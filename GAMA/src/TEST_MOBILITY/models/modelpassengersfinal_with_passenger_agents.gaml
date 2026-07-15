/**
* Name: modelpassengersfinal_with_passenger_agents
* Bus route simulation with explicit FIPA-communicating passenger agents.
* Adds a transit-time STOP_APPROACH/LAST_STOP broadcast and an "invisible-hand"
* cooperative dropoff selection. Boarding is now passenger-initiated through
* the bus, which receives FIPA-requests with each passenger frozen time_in_stop.
* Author: hectoralv22
*/




model modelpassengersfinal_with_passenger_agents




//Unnecesary import since the routes_loader.gaml is fully implemented in this code
//import "routes_loader.gaml"




//--------------------------------------------------------------------------------------------------------------------------------
//-----------------------------------------------------GLOBAL_STATEMENT-----------------------------------------------------------
//--------------------------------------------------------------------------------------------------------------------------------



global 
{


//--------------------------------------------------------------------------------------------------------------------------------
//--------------------------------------------------------------------------------------------------------------------------------
//----------------------------------------------------GLOBAL FROM ROUTES----------------------------------------------------------
//--------------------------------------------------------------------------------------------------------------------------------
//--------------------------------------------------------------------------------------------------------------------------------


	

	//CREATE GLOBAL VARIABLES TO SAVE GLOBAL SCOPE OF THE AGENTS CREATED
	list <stop> stops_list_toA;
	
	list <stop> stops_list_toB;
	

    map<string, list<stop>> stops_list;
	
	list<stop> all_unique_stops;
	
	
	//CREATE GLOBAL VARIABLE MAP FOR DISTRIBUTIONS TO SAVE GLOBAL SCOPE OF THE VALS. FOR BOARD DROPOFFS
	map<int, map<int,map<string,list>>> global_distribution_values;
	
	
	//CREAYE GLOBAL VARIABLE MAP FOR DISTRIBUTIONS TO SAVE GLOBAL SCOPE OF THE VALS. FOR TBS(TIME BETWEEN STOPS)
	map<string, map<int,list<float>>> global_time_stops_values;
	
	
	
	//INPUT FILES
    file file_401_toA_route <- file("../includes/ROUTE/E01/E01_toA.shp");
    file file_401_toA_stops <- file("../includes/STOPS/E01/E01_stops_toA.shp");
    
    file file_401_toB_route <- file("../includes/ROUTE/E01/E01_toB.shp");
    file file_401_toB_stops <- file("../includes/STOPS/E01/E01_stops_toB.shp");
    
    
    //ADAPT THE SCALE TO MATCH THE 401 RESOLUTION
    geometry shape <- envelope(file_401_toA_route);

    
    
	//---------------------------------------------------------------------------------
	//------------------PROBABILITY DISTRIBUTIONS FUNCTIONS----------------------------
	//---------------------------------------------------------------------------------
    
    
    //NORMAL IS ALREADY IMPLEMENTED AS GAUSS()
    
    
    
  //NEGATIVE BINOMIAL

	/*
	* As the negative binomial distribution is not implemented in GAMA,
	* sampling is performed via the Gamma-Poisson mixture:
	*   lambda ~ Gamma(r, (1-p)/p),  X | lambda ~ Poisson(lambda)
	* Shape-scale parameterization, consistent with scipy.stats.nbinom
	* (support {0,1,2,...}, number of failures).
	*/
	int sample_negative_binomial(float r, float p) {

		// Degenerate cases: non-positive shape or p >= 1 imply X = 0
		if (r <= 0.0 or p >= 1.0) {
			return 0;
		}

		float gamma_val <- gamma_rnd(r, (1 - p) / p);

		// Defensive guard only: poisson() is non-negative by definition
		return max(0, poisson(gamma_val));

	} //End function sample_negative_binomial



	//GEOMETRIC

	/*
	* As the geometric distribution is not implemented in GAMA,
	* sampling is performed via the inverse transform method:
	*   X = floor( ln(U) / ln(1-p) ),  U ~ Uniform(0,1)
	* Support {0,1,2,...} (number of failures), consistent with the
	* fitting pipeline (p_hat = 1/(1 + mean), pmf (1-p)^k * p).
	* ln(U) is used instead of ln(1-U): both are identically distributed.
	*/
	int sample_geometric(float p) {

		// Degenerate cases
		if (p >= 1.0) { return 0; }     // success guaranteed -> 0 failures
		if (p <= 0.0) { return 0; }     // invalid parameter; should not occur post-fitting

		float u <- rnd(0.0, 1.0);
		if (u = 0.0) { u <- 1e-12; }    // avoid ln(0); negligible bias
		if (u = 1.0) { u <- 1.0 - 1e-12; }

		return int(floor(ln(u) / ln(1 - p)));

	} //End function sample_geometric
	
	
	
	//DROPOFF COUNT SAMPLER (FOR THE INVISIBLE HAND)
	
	/*
	 * Sample one realization of the dropoff count for the given stop and timeslot.
	 * Used by the invisible-hand selector instead of by the stop. The bus must NOT
	 * call this directly because, by design, the bus does not know N upfront.
	 */
	int sample_dropoff_count(int stop_num, int ts) {
		
		int safe_ts <- min(ts, 23);
		
		list distrib <- global_distribution_values[stop_num][safe_ts]["DropOffs"];
		
		if (distrib = nil){
			return 0;
		}
		
		string dtype <- string(distrib[0]);
		
		if (dtype = "NORMAL"){
			return max(int(floor(gauss(float(distrib[1]), float(distrib[2])))), 0);
		}
		if (dtype = "NEGATIVE BINOMIAL"){
			return max(sample_negative_binomial(float(distrib[1]), float(distrib[2])), 0);
		}
		if (dtype = "GEOMETRICAL"){
			return max(int(floor(sample_geometric(float(distrib[1])))), 0);
		}
		
		//NO DATA case (or anything else unrecognised). Default to 0
		return 0;
		
	}//End function sample_dropoff_count
	
	
	
	
	//---------------------------------------------------------------------------------
	//------------------------INVISIBLE HAND ACTION------------------------------------
	//---------------------------------------------------------------------------------
	
	/*
	 * The "invisible hand" mark passenger agents currently riding the bus b with
	 * a wants_to_drop = true flag. The amount of marked passengers (N) is sampled from
	 * the upcoming stop distribution at the current TimeSlot.
	 * 
	 * Important note about the bus knowledge: The bus DOES NOT see N from this action. 
	 * It only triggers it. The set of droppers will eventually be known by the bus 
	 * when the I_WILL_DROP informs come back from the passengers themselves at handle_stop.
	 *
	 * Selection criterion: top-N passengers by frozen time_in_stop. This way, those who
	 * have been waiting longer are the first ones marked to drop. The exact criterion is not
	 * very important rn, just any way of picking N passengers from the bus would work.
	 *
	 * Last stop case: all passengers on bus are marked, no sampling done.
	 */
	action select_droppers(bus b, int upcoming_stop_code, bool is_last_stop) {
		
		list<passenger> on_board <- list<passenger>(b.passengers_on_bus) where (!dead(each));		
		if (length(on_board) = 0){
			return;
		}
		
		
		//Reset flags before marking, so a fresh segment doesnt inherit the marks of the previous one
		loop p over: on_board {
			p.wants_to_drop <- false;
		}
		
		
		int N;
		
		if (is_last_stop){
			N <- length(on_board);
		}else{
			N <- sample_dropoff_count(upcoming_stop_code, TimeSlot);
		}
		
		if (N <= 0){
			return;
		}
		
		
		//Sort descending by frozen time_in_stop, mark the first min(N, |on_board|) ones
		list<passenger> sorted_pass <- on_board sort_by (-each.time_in_stop);
		
		int actual_N <- min(N, length(sorted_pass));
		
		loop i from: 0 to: actual_N - 1 {
			sorted_pass[i].wants_to_drop <- true;
		}
		
	}//End action select_droppers
	
	

    
    /*
     * Action module to be invoiced from other models .gaml
     *
     * This simply reads the files stops and routes (Both with .shp[shapefile] extension) and process all the agents
     * required to satisfy the content of the file
     */
    action load_401 {
        
      	
      	
      	//write "LOADING THE MAP WITH ROUTES AND STOPS";
      	
      	
      	
      	//Read input for normal days distributions
      	file input_data_e01_toA <- csv_file("../includes/INPUTS/input_data_E01_toA.csv");
      	file input_data_e01_toB <- csv_file("../includes/INPUTS/input_data_E01_toB.csv");
      	
      	//Convert it as matrix
      	matrix input_as_matrix_toA <- matrix(input_data_e01_toA);
      	
		matrix input_as_matrix_toB <- matrix(input_data_e01_toB);
		
		
      	//All stops willbe using the same Timeslots. Starting at 5 ending at 23
      	list<int> timeslots <- [5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23];
		
		
		//Hardcodded stopNums in both directions
		list<int> stopNums_toA <- [2646, 562, 4090, 4188, 5939, 3995, 3991, 3903, 2539, 2535, 1929, 4032, 5360, 82, 5727];
		
		list<int> stopNums_toB <- [5727, 81, 1167, 2538, 3929, 3990, 3994, 5938, 4187, 2964, 649, 2646];
		
		
		
		
		
		
		
		
		//Declaration of the dictionary	
		map<int, map<int,map<string,list>>> distribution_values;
		
		
		/*
		 * Loop to obtain all the stopNums and store the data from the stops related to that num
		 * The skeleton of the distribution map will be the following:
		 * Dictionary distribution_values: {Key(StopNum): Value: Dict}
		 * Secondary Dict: {Key(TimeSlot): Value: Dict}
		 * Third Dict: {Key(Board): Value: ["DistrType", Param1, Param2], Key(DropOff): Value: ["DistrType", Param1, Param2]}
	     */
		loop stops_iter over: file_401_toA_stops {
			
			/*
			 * Map the file stops iteration element to a point. 
			 * Required to extract the attrs and obtain the stopNum
			 */
				geometry point_iter <- stops_iter;
			
				map attr <- point_iter.attributes;
			
    			int stop_code <-int(attr["stopNum"]);
    		
    		
    		/*
    		 * Now, obtain from the input_as_matrix, all the rows referencing that stop code
    		 * From this, it will order the daata as specified in the loop definition above
    		 */
    			list<list> elements_from_stop <- [];
    			
    			
    			/*
    			 * Secondary loop itering the matrix. It obtain all the row content, and if row[0] == stop_code then save it. ¡
    			 * Once thellop is over, use the list to store the data 
    			 */
    			loop i from: 0 to: input_as_matrix_toA.rows {
    				
    				list row <- row_at(input_as_matrix_toA, i);					
					
					//This is put because matrix saves an empty list out of the EOF line in csv
					if (row != []){
					
						if (int(row[0]) = stop_code){
							elements_from_stop << row;
						}	
					}
    			}//End loop mat_row
    		    	
    		    
    		    
    		    	
    		    	
    		    //Secondary dictionary for each 
				map<int,map<string,list>> map_per_stop;		
				
				
				/*
    			 * Case first stop. Different because only have boards, no dropoffs, so the third dict will contain only Board
    			 */
    			if (stop_code = 2646){
    				
    				
    				loop timeslot over: timeslots {
    					
    					/*
	    				 * The structure for each stop iteration, is, the element 0 for TS 5, 1 for TS 6,....
	    				 * For each timeslot, it will take the i and i elements where i == (TS -5)
	    				 * The i, will be BOARDS, as is the first stop, there will be no DropOffs
	       				 */
    					
    					
    					//Third dictionary
    					map<string, list> boards_dropoffs_per_timeslot;
						
						//Boards
	    				list element_boards <-  elements_from_stop[(timeslot - 5)];	
						
						//Dropoffs
						list element_dropoffs <- ["NO DATA", 0, 0];
						
						
						//Save in the third dictionary 
						boards_dropoffs_per_timeslot << "Boards"::[element_boards[3], element_boards[4], element_boards[5]];
						
						boards_dropoffs_per_timeslot << "DropOffs"::element_dropoffs;
						
						//Limit case for those buses finishing later than24:00
						if (timeslot = 23){
							//Save in the third dictionary 
							boards_dropoffs_per_timeslot << "Boards"::[element_boards[3], element_boards[4], element_boards[5]];
							
							boards_dropoffs_per_timeslot << "DropOffs"::element_dropoffs;
						}
							
						//Save the third dictionary in the second dictionary				
						map_per_stop << timeslot::boards_dropoffs_per_timeslot;
						
						//Limit case for those buses finishing later than24:00
						if (timeslot = 23){
							map_per_stop << (timeslot +1) ::boards_dropoffs_per_timeslot;
							map_per_stop << (timeslot +2) ::boards_dropoffs_per_timeslot;
						}
						
    				}//End loop Timeslots

    				//Save the second dictionary in the first dictionary
    				distribution_values << stop_code::map_per_stop;

    				
    				
    			}//End if First Stop
				
				
    			
    			/*
    			 * Rest of the cases
    			 */
    			if (stop_code != 2646 and stop_code != 5727){
    				
    				
    				loop timeslot over: timeslots {
    					
    					/*
	    				 * The structure for each stop iteration, is, the elements 0 and 1 for TS 5, the 2 and 3 for 6,......
	    				 * For each timeslot, it will take the i and i + 1 elements where i == (TS -5)*2
	    				 * The i, will be BOARDS, and i + 1 DROPOFFS
	       				 */

    					//Third dictionary
    					map<string, list> boards_dropoffs_per_timeslot;
						
						//Boards
	    				list element_boards <-  elements_from_stop[(timeslot - 5)*2];	
						
						//Dropoffs
						list element_dropoffs <- elements_from_stop[(timeslot - 5)*2 + 1];
						
						
						//Save in the third dictionary 
						boards_dropoffs_per_timeslot << "Boards"::[element_boards[3], element_boards[4], element_boards[5]];
						
						boards_dropoffs_per_timeslot << "DropOffs"::[element_dropoffs[3], element_dropoffs[4], element_dropoffs[5]];
							
							
						//Save the third dictionary in the second dictionary				
						map_per_stop << timeslot::boards_dropoffs_per_timeslot;
						
						//Limit case for those buses finishing later than24:00
						if (timeslot = 23){
							map_per_stop << (timeslot +1) ::boards_dropoffs_per_timeslot;
							map_per_stop << (timeslot +2) ::boards_dropoffs_per_timeslot;
						}
						
    				}//End loop Timeslots

    				//Save the second dictionary in the first dictionary
    				distribution_values << stop_code::map_per_stop;
    				
    			}//End if general case
    			
		}//End loop stops_iter
		
		
		
		//---------------------------------------------
		//-----Loop again for the Inverse route--------
		//---------------------------------------------		
		
		/*
		 * Loop to obtain all the stopNums and store the data from the stops related to that num
		 * The skeleton of the distribution map will be the following:
		 * Dictionary distribution_values: {Key(StopNum): Value: Dict}
		 * Secondary Dict: {Key(TimeSlot: Value: Dict}
		 * Third Dict: {Key(Board): Value: ["DistrType", Param1, Param2], Key(DropOff): Value: ["DistrType", Param1, Param2]}
	     */
		loop stops_iter over: file_401_toB_stops {
			
			/*
			 * Map the file stops iteration element to a point. 
			 * Required to extract the attrs and obtain the stopNum
			 */
				geometry point_iter <- stops_iter;
			
				map attr <- point_iter.attributes;
			
    			int stop_code <-int(attr["stopNum"]);
    		
    		
    		/*
    		 * Now, obtain from the input_as_matrix, all the rows referencing that stop code
    		 * From this, it will order the daata as specified in the loop definition above
    		 */
    		 
    		     		
    			list<list> elements_from_stop <- [];
    			
    			
    			/*
    			 * Secondary loop itering the matrix. It obtain all the row content, and if row[0] == stop_code then save it. ¡
    			 * Once thellop is over, use the list to store the data 
    			 */
    			loop i from: 0 to: input_as_matrix_toB.rows {
    				
    				list row <- row_at(input_as_matrix_toB, i);					
					
					//This is put because matrix saves an empty list out of the EOF line in csv
					if (row != []){
					
						if (int(row[0]) = stop_code){
							elements_from_stop << row;
						}	
					}
    			}//End loop mat_row
    		    	
    		    	
    		    	
    		    	
    		    //Secondary dictionary for each 
				map<int,map<string,list>> map_per_stop;		
    			
    			
    			
    			/*
    			 * Case last stop. Different because only have dropoffs and the dropoffs are all the passengers. The dropoffs here
    			 * Can serve as a metric to identify normal cases and extreme cases.
    			 */
    			if (stop_code = 5727){
    				
    				
    				loop timeslot over: timeslots {
    					
    					/*
	    				 * The structure for each stop iteration, is, the element 0 for TS 5, 1 for TS 6,....
	    				 * For each timeslot, it will take the i and i elements where i == (TS -5)
	    				 * The i, will be DropOffs, as is the last stop, there will be no Boards
	       				 */
    					
    					
    					//Third dictionary
    					map<string, list> boards_dropoffs_per_timeslot;
    					
    					//Boards
    					list element_boards <- elements_from_stop[(timeslot - 5)];
						
						//DropOffs
	    				list element_dropoffs <-  ["NO DATA", 0, 0];	
						

						//Save in the third dictionary 
						boards_dropoffs_per_timeslot << "Boards"::[element_boards[3], element_boards[4], element_boards[5]];
						
						
						boards_dropoffs_per_timeslot << "DropOffs"::[element_dropoffs[0], element_dropoffs[1], element_dropoffs[2]];
							

						
						
						//Save the third dictionary in the second dictionary				
						map_per_stop << timeslot::boards_dropoffs_per_timeslot;
						
						//Limit case for those buses finishing later than24:00
						if (timeslot = 23){
							map_per_stop << (timeslot +1) ::boards_dropoffs_per_timeslot;
							map_per_stop << (timeslot +2) ::boards_dropoffs_per_timeslot;
						}
						
    				}//End loop Timeslots


    				//Save the second dictionary in the first dictionary
    				distribution_values << stop_code::map_per_stop;
    				
		
    				
    			}//End If Last Stop
    			
    			
    			
    			/*
    			 * Rest of the cases
    			 */
    			if (stop_code != 2646 and stop_code != 5727){
    				
    				
    				loop timeslot over: timeslots {
    					
    					/*
	    				 * The structure for each stop iteration, is, the elements 0 and 1 for TS 5, the 2 and 3 for 6,......
	    				 * For each timeslot, it will take the i and i + 1 elements where i == (TS -5)*2
	    				 * The i, will be BOARDS, and i + 1 DROPOFFS
	       				 */

    					//Third dictionary
    					map<string, list> boards_dropoffs_per_timeslot;
						
						//Boards
	    				list element_boards <-  elements_from_stop[(timeslot - 5)*2];	
						
						//Dropoffs
						list element_dropoffs <- elements_from_stop[(timeslot - 5)*2 + 1];
						
						
						//Save in the third dictionary 
						boards_dropoffs_per_timeslot << "Boards"::[element_boards[3], element_boards[4], element_boards[5]];
						
						boards_dropoffs_per_timeslot << "DropOffs"::[element_dropoffs[3], element_dropoffs[4], element_dropoffs[5]];

						
						
						//Save the third dictionary in the second dictionary				
						map_per_stop << timeslot::boards_dropoffs_per_timeslot;
						
						//Limit case for those buses finishing later than24:00
						if (timeslot = 23){
							map_per_stop << (timeslot +1) ::boards_dropoffs_per_timeslot;
							map_per_stop << (timeslot +2) ::boards_dropoffs_per_timeslot;
						}
						
    				}//End loop Timeslots

    				//Save the second dictionary in the first dictionary
    				distribution_values << stop_code::map_per_stop;
    				
    			}//End if general case
    			
		}//End loop stops_iter
		
		
		//Update the global variable so every agent can access this data.
		global_distribution_values <- distribution_values;
		
		
		
		
		//treat the time-between stops distributions.
		file time_between_stops_toA <- csv_file("../includes/INPUTS/input_times_stops_toA.csv");
		file time_between_stops_toB <- csv_file("../includes/INPUTS/input_times_stops_toB.csv");
		
		
		
		/* 
		 * Loop to create the map for the time between stops. The structure of the map wil be the following:
		 * A first map<string, map> containing a map for each Direction of the route, so keys 'toA' and 'toB'
		 * A second map(One for each direction) containing as keys the stopNums and values the mean and std for the tbs between
		 * Them and its following. For the last stop for no error in the agents will be mean 0 and std 0.
		 */
		 
		 //local action variable to save the data. Then change the reference to the global variable scope
		 
		 map<string, map<int,list<float>>> local_time_stops_values;
		 
		 matrix matrix_time_stops_toA <- matrix(time_between_stops_toA);
 		 matrix matrix_time_stops_toB <- matrix(time_between_stops_toB);
		 
		 map<int,list<float>> local_toA_times;
		 
		 list<float> mean_std_values;
		 
		 //Do case toA
		 loop iter from: 0 to: (length(stopNums_toA) -1){
		 	
		 	mean_std_values <- [];
		 	
		 	if (iter < (length(stopNums_toA) -1)){
			 	//locate first stopNum
			 	int stop_code <- stopNums_toA[iter];
			 	
			 	
			 	//loop every timeslot for saving its mean and std
			 	loop timeslot over: timeslots{
			 		
				 	float mean_val <- float(matrix_time_stops_toA[(timeslot-5)*2 + 1, iter]);
				 	
					float std_val <- float(matrix_time_stops_toA[(timeslot-5)*2 + 2, iter]);
					
					mean_std_values << mean_val;
					mean_std_values << std_val;
					
					
					if (timeslot = 23){
						mean_std_values << mean_val;
						mean_std_values << std_val;
					}
					
				}
				
				local_toA_times << stop_code::mean_std_values;	
				
			} else{
				
				//Case last stop. No conections with stops in this direction so 0.0 all the time
				int stop_code <- stopNums_toA[iter];
				
				loop timeslot over: timeslots{
					mean_std_values << 0.0;
					mean_std_values << 0.0;
					
					if (timeslot = 23){
						mean_std_values << 0.0;
						mean_std_values << 0.0;
					}
				}
				
				local_toA_times << stop_code::mean_std_values;					
			}//End ifs
			
			
		 }//End case toA for time between stops data.
		 
		 //Save to the local map
		 local_time_stops_values << "toA"::local_toA_times;
		 
		 
		 
		 //do case toB
		 map<int,list<float>> local_toB_times;
		 
		 
		 loop iter from: 0 to: (length(stopNums_toB) -1){
		 	
		 	mean_std_values <- [];
		 	
		 	if (iter < (length(stopNums_toB) -1)){
			 	//locate first stopNum
			 	int stop_code <- stopNums_toB[iter];
			 	
			 	//pick up the values and store
			 	
			 	//List to store all the data
			 	
			 	loop timeslot over: timeslots{
			 		
				 	float mean_val <- float(matrix_time_stops_toB[(timeslot-5)*2 + 1, iter]);
				 	
					float std_val <- float(matrix_time_stops_toB[(timeslot-5)*2 + 2, iter]);
					
					mean_std_values << mean_val;
					mean_std_values << std_val;
					
					if (timeslot = 23){
						mean_std_values << mean_val;
						mean_std_values << std_val;
					}
					
				}//End loop timeslot
				
				
				local_toB_times << stop_code::mean_std_values;	
				
			} else{
				//Case last stop. No conections with stops in this direction so 0.0 all the time
				int stop_code <- stopNums_toB[iter];
				
				loop timeslot over: timeslots{
					mean_std_values << 0.0;
					mean_std_values << 0.0;
					
					if (timeslot = 23){
						mean_std_values << 0.0;
						mean_std_values << 0.0;
					}
				}
				
				
				local_toB_times << stop_code::mean_std_values;	
				
			}//End ifs
		
		}//End case toB for time between stops data.
		
		
		//update the local value map
	    local_time_stops_values << "toB"::local_toB_times;
		
		//Save it to the global scope
		global_time_stops_values <- local_time_stops_values;


		//----------------------------------------------------------------------------
		//Now create both the route and the stop, for the agent representation of them.
		//----------------------------------------------------------------------------

        // CREATE ROUTE FROM .SHP FILE
        create route from: file_401_toA_route with: [
            routename :: read("name"),
            distance :: int(read("distance")),
            id :: int(read("id"))	
        ];
        
        create route from: file_401_toB_route with: [
            routename :: read("name"),
            distance :: int(read("distance")),
            id :: int(read("id"))	
        ];
        
        // CREATE EACH STOP FROM .SHP FILE
        create stop from: file_401_toA_stops returns: created_stops_toA with: [
            stopName :: string(read("stopName")),
            stopNum :: int(read("stopNum")),
            distance :: int(read("distance")),
            name :: string(read("stopName")),
            stop_distributions:: distribution_values[int(read("stopNum"))]
        ];
        
        
        //Remove 2646 and 5727. When creating them in toB
        stop stop_to_remove <- first(created_stops_toA);
        
        //pop it from the stop list
        created_stops_toA >> first(created_stops_toA);
        //Kill it
        ask stop_to_remove {do die;}
        
        //Same with the last
        stop_to_remove <- last(created_stops_toA);
        
        //pop it from the stop list
        created_stops_toA >> last(created_stops_toA);
        //Kill it
        ask stop_to_remove {do die;}
        
        
        //SAVE TO GLOBAL LIST
        stops_list_toA <- list<stop>(created_stops_toA);
        
        
        // CREATE EACH STOP FROM .SHP FILE
        create stop from: file_401_toB_stops returns: created_stops_toB with: [
            stopName :: string(read("stopName")),
            stopNum :: int(read("stopNum")),
            distance :: int(read("distance")),
            name :: string(read("stopName")),
            stop_distributions:: distribution_values[int(read("stopNum"))]
        ];
        
        //Add the last element of toB (2646) to the first spot of toA list
        stops_list_toA <- [last(created_stops_toB)] + stops_list_toA;
        
        //Append the first of toB to toA
        stops_list_toA << first(created_stops_toB);


        //SAVE TO GLOBAL LIST
        stops_list_toB <- list<stop>(created_stops_toB);
        
        
        stops_list <<  "toA"::stops_list_toA;
        stops_list << "toB"::stops_list_toB;
		all_unique_stops <- remove_duplicates(stops_list.values accumulate each);

    }//END ACTION STATEMENT

		
//--------------------------------------------------------------------------------------------------------------------------------
//--------------------------------------------------------------------------------------------------------------------------------
//----------------------------------------------GLOBAL STATEMENTS-MOBILITY--------------------------------------------------------
//--------------------------------------------------------------------------------------------------------------------------------
//--------------------------------------------------------------------------------------------------------------------------------



//------------------------------------------------------------------
//-----------------TIME REFLEXES AND VARIABLES----------------------
//------------------------------------------------------------------
	
	
	//#DEFINE. CHANGE THIS IN CASE THE SIMULATION HAS TO RUN ON LOWER/HIGHER ITERATIONS
	float step <- 2 #seconds;
	

	float time <- cycle * step;
	
	
	//Initialize minutes
	int minutes <- 0;

	
	//Initialize sim TimeSlot
	int TimeSlot <- 5;
	
	int seconds <- 0;

	/*
	 * Global reflex to handle each iteration the time that has passed. It will save
	 */
	reflex update_time {
		
        // Convert total simulated time to minutes
        int total_minutes <- int(time / 60);  // time is in seconds
        
        int total_seconds <- int(time);
        
        // Calculate hours and minutes from simulation start (5:00)
        TimeSlot <- 5 + int(total_minutes / 60);
       
        //Calculate minutes passed in the hour by dividing by 60
        minutes <- mod(total_minutes, 60);
		
		// Seconds within the minute
    	seconds <- int(mod(total_seconds, 60));
    
	}//End reflex update_time



	
	//Value to know how many time per passenger the bus must wait in the stop
	float elapsed_time_per_passenger <- 5.0;



	//Map the TimeSlot + minutes into a string, to compare with the input
	string current_time -> 
    string(TimeSlot) + ":" +
    (minutes < 10 ? "0" + string(minutes) : string(minutes)) + ":" +
    (seconds < 10 ? "0" + string(seconds) : string(seconds));
	
	
	
//------------------------------------------------------------------
//----------------------DISTRIBUTION VARIABLES----------------------
//------------------------------------------------------------------
	
	
	//Variable to hold the info about each stop and its distribution values
	map<int, list<float>> stops_distribution_values;
	
	
	
	
	/*
	 * Reflex function to update the new distrinutions values to add every step of the simulation
	 */
	 reflex update_distributions when: (mod(minutes, 60) = 0 and mod(time, 60)= 0 ){
	 	
	 	
	 	
	 	loop stop_iter over: all_unique_stops{
	 		
	 		list distribution_per_timeslot_boards;
		 	list next_distribution_per_timeslot_boards;
		 	float board_generation_ratio;
		 	float next_board_generation_ratio;

	 		if (TimeSlot < 23){
			
			//Loading the distros
			distribution_per_timeslot_boards <- global_distribution_values[stop_iter.stopNum][TimeSlot]["Boards"];
			
			
			//Loading the following distros
			next_distribution_per_timeslot_boards <- global_distribution_values[stop_iter.stopNum][TimeSlot + 1]["Boards"];
			
			
			//Infer the new and the following exact random values based on the distribution.

			//Actual VAL
			if(distribution_per_timeslot_boards[0] = "NORMAL"){
				board_generation_ratio <- gauss(float(distribution_per_timeslot_boards[1]), float(distribution_per_timeslot_boards[2]));
			}
			if(distribution_per_timeslot_boards[0] = "NEGATIVE BINOMIAL"){
				board_generation_ratio <- float(sample_negative_binomial(float(distribution_per_timeslot_boards[1]),
					float(distribution_per_timeslot_boards[2])));			
			}
			if (distribution_per_timeslot_boards[0] = "GEOMETRICAL"){
				board_generation_ratio <- sample_geometric(float(distribution_per_timeslot_boards[1]));
			}
			if (distribution_per_timeslot_boards[0] = "NO DATA"){
				board_generation_ratio <- 0.0;
			}

		
			//Following VAL
			if(next_distribution_per_timeslot_boards[0] = "NORMAL"){
				next_board_generation_ratio <- gauss(float(next_distribution_per_timeslot_boards[1]), float(next_distribution_per_timeslot_boards[2]));
			}
			if(next_distribution_per_timeslot_boards[0] = "NEGATIVE BINOMIAL"){
				next_board_generation_ratio <- float(sample_negative_binomial(float(next_distribution_per_timeslot_boards[1]),
					float(next_distribution_per_timeslot_boards[2])));			
			}
			if (next_distribution_per_timeslot_boards[0] = "GEOMETRICAL"){
				next_board_generation_ratio <- sample_geometric(float(next_distribution_per_timeslot_boards[1]));
			}
			if (next_distribution_per_timeslot_boards[0] = "NO DATA"){
				next_board_generation_ratio <- 0.0;
			}

		}
		else if (TimeSlot = 23){
			
			//Last TimeSlot, no next, but for no error will be 0.0
			distribution_per_timeslot_boards <- global_distribution_values[stop_iter.stopNum][TimeSlot]["Boards"];
			
			//Actual VAL
			if(distribution_per_timeslot_boards[0] = "NORMAL"){
				board_generation_ratio <- gauss(float(distribution_per_timeslot_boards[1]), float(distribution_per_timeslot_boards[2]));
			}
			if(distribution_per_timeslot_boards[0] = "NEGATIVE BINOMIAL"){
				board_generation_ratio <- float(sample_negative_binomial(float(distribution_per_timeslot_boards[1]),
					float(distribution_per_timeslot_boards[2])));			
			}
			if (distribution_per_timeslot_boards[0] = "GEOMETRICAL"){
				board_generation_ratio <- sample_geometric(float(distribution_per_timeslot_boards[1]));
			}
			if (distribution_per_timeslot_boards[0] = "NO DATA"){
				board_generation_ratio <- 0.0;
			}
			
			//The next 0.0 as no TimeSlot 24
			next_board_generation_ratio <- 0.0;

		}
		else{
			//For timeslots bigger than 24 in case a bus still gets running
			board_generation_ratio <- 0.0;
			next_board_generation_ratio <- 0.0;
		}//End Ifs Cases Timeslot
		
		
		/*
		 * After this loop, board will contain the value of the random choice selected and next too.
		 * Now apply trigonometric formulas to be able to smooth down the transitions
		 */
	
		//obtain the value in wich you will generate passengers
		stops_distribution_values[stop_iter.stopNum] <- smooth_data_function(board_generation_ratio, next_board_generation_ratio);
		
		
	 	}//End loop
	 	
	 	
	 }//End reflex update distributions
	
	

	/*
	 * Reflex function to handle the update of the generation of passengers for every stop.
	 * Now spawns proper passenger AGENTS at the stop location, with a back-reference to the
	 * stop and time_in_stop = 0.0. The wait_at_stop reflex of the passenger will grow that
	 * value once per cycle, and it will be frozen the moment the passenger boards a bus.
	 */
	reflex generate_passengers_from_distributions {
		
		loop stop_iter over: all_unique_stops{
			stop_iter.passengers_to_be_generated <- stop_iter.passengers_to_be_generated + 
						stops_distribution_values[stop_iter.stopNum][int(mod(time, 3600) / step)];
						
			
			int passengers_generated_new <- int(stop_iter.passengers_to_be_generated);
			
			if (passengers_generated_new > 0){

				stop_iter.passengers_to_be_generated <- stop_iter.passengers_to_be_generated - passengers_generated_new;
				
				//Spawn passenger agents at this stop. Each one starts at the stop's location, with
				//a back-reference to the stop and a time_in_stop counter starting at 0.
				create passenger number: passengers_generated_new returns: new_pax with: [
					location          :: stop_iter.location,
					current_stop_ref  :: stop_iter,
					on_bus            :: false,
					time_in_stop      :: 0.0
				];
				
				//Append them to the stop's waiting list
				stop_iter.passengers_at_stop <- stop_iter.passengers_at_stop + new_pax;
				
				stop_iter.passengers_generated <- stop_iter.passengers_generated + passengers_generated_new;		
			}
		}//End loop

	}//End reflex generate passengers from distributions


	
	/*
	 * Reflex to handle the END of the sim once no bus is kept alive
	 */ 
	reflex end_real_simulation when: empty(bus){
        do die;  //CHAO CHAO CHAO CHAO
	}

	
	
//--------------------------------------------
//-------------GLOBAL FUNCTIONS---------------
//--------------------------------------------
	

	/*
	 * Global function to transform the number of Boards and Dropoffs given a stop data and return the number of cycles
	 * of waiting the bus must take based on that number and the step value of the sim.
	 */
	 int await_time_per_bus(int boards, int dropoffs){
	 	
	 	//Taking max of boards anddropoffs because in real time te bus parallelizes the board/dropoff one per door.
	 	float time_to_wait <- max(boards, dropoffs) * elapsed_time_per_passenger;
		
		//Once known the val, convert it to cycle sims
		int cycles_to_wait <- int(time_to_wait/step);
	 	
	 	//The system must return the max between 0 or the number calc - 2, as 2 are the cycles that the bus is already
	 	//taking for processing the passengers. This is extra time only of wait
	 	return max(0, (cycles_to_wait-2));
	 }
	
	
    
    /*
     * Global function to pass to minutes the time in hh:mm
     */
	int time_to_minutes(string t) {
		
	    list<string> parts <- t split_with ":";
	    
	    return int(parts[0]) * 60 + int(parts[1]);
	}

	
	
	float time_to_seconds(string t) {

		list<string> parts <- t split_with ":";

		float func_hours <- float(parts[0]);
		float func_minutes <- float(parts[1]);
		float func_seconds <- float(parts[2]);

		return func_hours * 3600.0 + func_minutes * 60.0 + func_seconds;
	}


	/*
	 * Global function to handle the smoothness of the change between distribution.
	 * Returns a list of float values, one per simulation step within the timeslot.
	 * The sum of all values in the list equals first_value.
	 * The line tilts to connect smoothly toward second_value's rate.
	 */
	list<float> smooth_data_function(float first_value, float second_value) {
	
	    // Number of simulation steps in one timeslot (3600 seconds)
	    float simple_step <- 3600 / step;
	
	    // The average per-step rate that the next timeslot would have
	    float rate_end <- second_value / simple_step;
	
	    // y_intercept is solved so that the sum across all steps = first_value
	    // From: sum = y_intercept * N + slope * N*(N-1)/2 = first_value
	    // And:  f(N-1) = slope*(N-1) + y_intercept = rate_end
	    float y_intercept <- (2 * first_value / simple_step) - rate_end;
	    float slope <- (rate_end - y_intercept) / (simple_step - 1);
	
	    list<float> return_statement;
	
	    loop i from: 0 to: (simple_step - 1) {
	
	        float new_val <- slope * i + y_intercept;
	        return_statement << new_val;
	    }
	
	    return return_statement;
	}
	
	
	
	
	float estimate_time_between_stops(int stopNum, string direction){
		
		//Define a special case. If timeslot 5 and directions are toB. All the distros are 0.0 because no bus recorded left in ts5 and arrive in ts5to any stops
		//Just for precaution, in that case, load the TS 6 distributions.
		if (TimeSlot = 5 and direction = "toB"){
			float mean <- global_time_stops_values[direction][stopNum][((TimeSlot+1)-5)*2];
			float std <- global_time_stops_values[direction][stopNum][((TimeSlot+1)-5)*2 + 1];
			return max(gauss(mean, std), 4*step);
		}
		if (TimeSlot >= 24){
			float mean <- global_time_stops_values[direction][stopNum][((23)-5)*2];
			float std <- global_time_stops_values[direction][stopNum][((23)-5)*2 + 1];
			return max(gauss(mean, std), 4*step);
		}
		
		float mean <- global_time_stops_values[direction][stopNum][((TimeSlot)-5)*2];
		float std <- global_time_stops_values[direction][stopNum][((TimeSlot)-5)*2 + 1];
		return max(gauss(mean, std), 4*step);

	}//end function stimate times betwween stops
	
	
		
//--------------------------------------------------------------------------------------------------------------------------------
//--------------------------------------------------------------------------------------------------------------------------------
//------------------------------------------------------INIT MODULE---------------------------------------------------------------
//--------------------------------------------------------------------------------------------------------------------------------
//--------------------------------------------------------------------------------------------------------------------------------


    
    
    /*
     * Init function for main test. This firstly initialize the routes_loader model init, to read the geojson info in .shp 
     * format and generate the routes and the bus_stop agents. It saves the ordered bus info in a global list 
     * variable called stops_list_toA
     * 
     * Then it creates a bus specie starting in the initial stop of the route and saving the goal destination, 
     * which hard codded rn is the final stop.
     */
    init 
    {
    	
    	//LOAD THE 401 ROUTE
    	do load_401;
			
		//Load the input bus departure scheduled times		
		file input_json <- json_file("../includes/INPUTS/input_data_buses.json");
		map json_map <- input_json.contents;
		
		loop bus_key over: json_map.keys {
		    
		    list logical_bus <- json_map[bus_key];
		    
		    //Map the bus id code
		    string bus_id <- string(bus_key);
		    
		    string departure_direction;
		    if (list(list(logical_bus)[0])[0] = '2646'){
		        departure_direction <- "toA";
		    } else {
		        departure_direction <- "toB";
		    }
		
		    list<string> departure_times;
		    loop departures over: list(logical_bus){
		        departure_times << list(departures)[1];
		    }
		
		    create bus with: [
		        id:: bus_id,
		        departure_time:: first(departure_times),
		        direction:: departure_direction,
		        initial_stop:: first(stops_list[departure_direction]).stopName,
		        departure_times:: departure_times
		    ];
		}
		

    }//END INIT
    
}// END GLOBAL




//--------------------------------------------------------------------------------------------------------------------------------
//--------------------------------------------------------------------------------------------------------------------------------
//-----------------------------------------------------SPECIES_DEFINITION---------------------------------------------------------
//--------------------------------------------------------------------------------------------------------------------------------
//--------------------------------------------------------------------------------------------------------------------------------




/*
 *Definition of the type specie BUS.  
 * Skills fipa means that this agent inherit the FIPA communication protocol. Used to communicate between bus agents 
 * and stops agents and now also passenger agents
 * 
 */
species bus skills: [fipa] {
	
	
	//INITIAL_POS
    string initial_stop;
	
	string id;
	
    //Which direction hes managing(either 'toA' or 'toB')
    string direction;
    
    //DEPRECATED
//    //COORDINATES GOAL
//    point location_goal;
    
    
    //DEPARTURE TIME
    string departure_time;
    
    
    //Initially not allowed to leave until current_time == departure_time
    bool allowed_to_leave <- false;
     
    
    //INITIALLY NOT IN GOAL DESTINATION
    bool arrived_to_end <- false;
    
    
    //INITIALLY IN A BUS STOP
    bool stopped <- false;
    
    
    
    //NUMBER OF STOPS REACHED, FOR THE INDEX. INITIALLY 0, to board the first passengers from the stop
    int stops_reached <- 0;
    
    
    //LIST OF PASSENGERS CURRENTLY ON THE BUS. Replaces the int passengers <- 0 of the older model.
    //The size of this list is the bus occupation
    list<passenger> passengers_on_bus <- [];
    
    
    //Number of passengers, computed as the size of the on-bus list. Kept for compatibility with the aspect and the logging
    int passengers -> length(passengers_on_bus);
    
    
    //Variables to hold the species scope of the boards, dropoffs and residual_boards in order to have them in other reflexes
    int boards;
    int dropoffs;
    int residual_boards;
    
    
    
    
    //List container of the departure times for the bus
    list<string> departure_times;
    
    
    //Number of travels completed
    int travels_completed <- 0;
    
    //BOOL VARIABLE TO DEFINE WHETHER OR NOT THE AGENT IS MOUNTING PASSENGERS
    bool processing_passengers <- false;
    
    
    //to know the time between stops. Once reaches 0, it is "considered in the next stop"
    float time_between_stops;
    
    //Variable which acts as an accumulator for the bus distance time between stops. Once its >= self.time_between_stops, is in the next stop.
    float time_travelled <- 0.0;
    
    //AUXILIAR VARIABLE TO PROCESS THE PASSENGERS
    int passengers_to_process;
    
    
    //All buses have the same maximum capacity 
    int max_passengers <- 80;
    
    //To handle the comms in the next iteration, not in the same
    int comms_cycle;
    
    //Bool variable to handle the extra time await at the stop
    bool extra_waiting_time <- false;
    
    //Variable to hold the number of cycles left of waiting
    int cycles_to_wait;
    
    
    //To wait for the acceptance of the proposals
    bool waiting <- false;
    
    //Bool variable to know wether the bus has finished a shift(Arrive to its destintation, or not). It will trigger a reflextu change the direction or die.
    bool finished_shift <- false;
    
    //variable to hold the timeslot in which the bus left a header stop. useful to save the scope of when the bus left for each trip in order to match 
    //with the analysis scope
    int departure_timeslot <- 5;
    
    
    //BOOL FLAG to know if the in-transit STOP_APPROACH/LAST_STOP broadcast has already fired for the current segment
    bool approach_broadcast_done <- false;
    
    //Cycle in which the broadcast was fired. Useful for debugging.
    int approach_broadcast_cycle <- -1;
    
    //List of passengers who replied I_WILL_DROP to the last STOP_APPROACH broadcast. The bus learns this set HERE,
    //not from the invisible-hand action, so the bus does not see N upfront, only when the responses come back
    list<passenger> confirmed_droppers <- [];
    
    //List of frozen time_in_stop values picked up by the bus when boarding. Sent to the stop in the 'Update count' message,
    //so the stop can save the PASSENGERS log row.
    list<float> boarded_time_in_stops <- [];
    
    
    //List container to act as a buffer for the disk writings(logs) at its end of execution
    list<list> buffer_results;
    
    list<list> buffer_events;
    
        
    //DEFAULT ASPECT FOR THE GUI EXPERIMENT
    aspect default {
        if (self.stopped) 
        {
        	//SI ESTA PARADO, SE COLOREA EN naranja
        	draw square(100) color: #orange;
        	
        }//END IF ASPECT DEF
        else
        {
        	//SI ESTA EN MOVIMIENTO SE COLOREA EN VERDE
        	draw square(100) color: #green;
        	
        	
        }//END ELSE ASPECT DEF
        
    }//END ASPECT DEF
    
    
    /*
	 * Reflex to cleanup dead passengers from lists and stale FIPA messages from all inboxes.
	 * Runs every cycle unconditionally to prevent dead-agent references from accumulating.
	 */
	reflex dead_cleanup {
	    
	    //---- Remove dead passengers from the on-bus list ----
	    passengers_on_bus <- passengers_on_bus where (!dead(each));
	    
	    //---- Remove dead passengers from confirmed_droppers ----
	    confirmed_droppers <- confirmed_droppers where (!dead(each));
	    
	}//End reflex dead_cleanup


	/*
     * Reflex function to handle the abstraction not allowing the bus to leave
     * Until the departure_time is set.
     */
   
    reflex start_movements when: (allowed_to_leave = false)
    { 
	    
		//Check and compare if the bus can leave
    	if (world.time_to_minutes(world.current_time) >= world.time_to_minutes(departure_time))
    	{
    		allowed_to_leave <- true;
    		
    		self.departure_timeslot <- TimeSlot;
    		
    		//as it is the first stop, no need to trigger the time between stops. Just starts the comms with the bus
    		//time_between_stops <- world.estimate_time_between_stops(stops_list[direction][stops_reached].stopNum, direction);
    		//Set stopped as true so comm with the first stop
    		self.stopped <- true;
    	}//End IF
    	
    }//END reflex start_movements
    

	/*
     * Reflex function to handle the abstraction of moving the bus between stops.
     * 
     * It invoices auxiliary global functions to handle the movement and verify if the agent is in the area of acceptance
     * The area of acceptance is necesarry because the code is using float coordinates with very exact precision, 
     * so with module 5 vector speed,not always(mainly never) the coordinates will be the same, so a logical function 
     * to stablish certain minimum range is necesarry
     *
     * In this version, when reaching the LAST stop, finished_shift is NO LONGER set directly. Instead, arrived_to_end and stopped
     * are set so that handle_last_stop can run the dropoff phase first, and finished_shift will be triggered by 
     * finalize_last_stop_dropoffs once all on-board passengers have died.
     */
    reflex move_to_destination when: (arrived_to_end = false and stopped = false and allowed_to_leave = true)
    {
    	
     	self.time_travelled <- self.time_travelled + step;
    	
    	if (self.time_travelled >=  self.time_between_stops){
    		
    		
    		//Check if its last stop
    		if (stops_list[direction][self.stops_reached].stopNum = last(stops_list[direction]).stopNum){
    			
    			self.arrived_to_end <- true;
    			
    			//"move" to the last stop
    			//self.stops_reached <- self.stops_reached + 1;
    				
				//No longer trigger finished_shift here. handle_last_stop will run the dropoff first, then finalize_last_stop_dropoffs will trigger it
				self.stopped <- true;
				
    		}else{
    			//If it enters here, a sop has been reached, but no end destination, so simply stopped = true so it starts handling the board/dropoff
    			
    			self.stopped <- true;

    		}//End if else last direction

    	}//End if in new stop
    	
    	
    }//end reflex move_to_destination
    
    
    
    /*
     * Reflex function to fire the in-transit STOP_APPROACH or LAST_STOP broadcast to all
     * the passengers currently on board. The trigger is 3*step + time_travelled >= time_between_stops,
     * which means it fires when there are <=3 cycles left until arrival.
     * 
     * After sending the broadcast, the invisible-hand action select_droppers is called to mark the
     * top-N passengers (by frozen time_in_stop) with wants_to_drop = true. The bus does not see N here.
     * 
     * It only fires ONCE per segment thanks to the approach_broadcast_done flag, that gets reseted on
     * verify_stop_and_restart_way.
     */
    reflex broadcast_approach when: (allowed_to_leave = true and stopped = false and arrived_to_end = false 
    								and approach_broadcast_done = false and time_between_stops > 0
    								and (3 * step + time_travelled) >= time_between_stops)
    {
    	
    	approach_broadcast_done <- true;
    	approach_broadcast_cycle <- cycle;
    	
    	//If no passengers on board, no need to broadcast nor select droppers
    	if (length(passengers_on_bus) = 0){
    		return;
    	}
    	
    	//In case the full passengers are dead and there is an behind the scenes cleanup
    	list<passenger> alive_pass <- passengers_on_bus where (!dead(each));
    	if (length(alive_pass) = 0){ return; }
    	
    	int upcoming <- stops_list[direction][stops_reached].stopNum;
    	bool is_last <- (upcoming = last(stops_list[direction]).stopNum);
    	string msg_type <- is_last ? 'LAST_STOP' : 'STOP_APPROACH';
    	
    	
    	//Send the broadcast inform to all passengers
    	do start_conversation to: alive_pass protocol: 'fipa-query' performative: 'query' contents: [msg_type, upcoming];
    	
    	
    	//Trigger the invisible hand. Global action -- must be invoked through ask world. Inside the ask block, myself is this bus,
    	//and the local vars upcoming/is_last from the enclosing reflex scope are visible. Named-arg syntax is mandatory for action calls
    	ask world {
    		do select_droppers(b: myself, upcoming_stop_code: upcoming, is_last_stop: is_last);
    	}
    	
    }//End reflex broadcast_approach
    

    /*
     * 
     * Reflex function to handle the abstraction of communicating with the agent stop in the new boarding flow.
     *
     * Cycle A (= comms_cycle): bus arrived at non-terminal stop.
     *   - Defensive collection: scan informs for I_WILL_DROP responses still in flight from the broadcast. Removes them
     *     from the inbox so they are not re-read at the next stop. Also drops I_WILL_STAY messages.
     *   - Send 'Drop off' FIPA-request to confirmed_droppers (parallel to the boarding request).
     *   - Send 'Bus arrived' FIPA-request to the current stop.
     *   - dropoffs is recorded here as the response count: this is the FIRST time the bus learns N.
     *
     */
    reflex handle_stop when: (self.stopped = true and self.processing_passengers = false and self.arrived_to_end = false)
    {
    	
    	/*LOGIC TO COMMUNICATE WITH THE AGENT STOP WHICH IS IN
    	 * 
    	 * (1) Collect any I_WILL_DROP responses currently in the informs inbox. 
    	 * (2) Send 'Drop off' to confirmed droppers (parallel with the boarding request)
    	 * (3) Tell the stop the bus has arrived
    	 * 
    	 */
    	 
    	 
    	//(1)Cleaning up agrees
    	loop msg over: agrees {
			list c <- list(msg.contents);
			if (length(c) < 1 and string(c[0]) != 'Ok'){
				write "Error message unknown";
			}
		}
    	 
    	 
		
		//(2) collect I_WILL_DROP responses
		confirmed_droppers <- [];
		loop msg over: informs {
			list c <- list(msg.contents);
			if (length(c) >= 1){
				string ctype <- string(c[0]);
				if (ctype = 'I_WILL_DROP'){
					passenger p <- passenger(msg.sender);
				    if (!dead(p)){
				        confirmed_droppers << p;
				    }
				}
				else if (ctype = 'I_WILL_STAY'){
				}
			}
		}//End loop on informs
		
		self.dropoffs <- length(confirmed_droppers);
		
		
		//(3) ask all droppers to drop off (parallel with the boarding request)
		if (length(confirmed_droppers) > 0){
			do start_conversation to: confirmed_droppers protocol: 'fipa-request' performative: 'request' contents: ['Drop off'];
		}
		//(4) tell the stop the bus has arrived
    	do start_conversation to: [stops_list[self.direction][self.stops_reached]] protocol: 'fipa-request' performative: 'request' contents: ['Bus arrived'];
		
		
		//THIS LINE IS JUST FOR THE BUS IN THE NEXT CYCLE NOT REPEATING THE SENDING MESSAGE
		self.processing_passengers <- true;
		
		//To not trigger handle_stop_response_and_boards till next cycle
		self.comms_cycle <- cycle;
		
		
		//Reset the per-stop counters
		self.boarded_time_in_stops <- [];
		self.boards <- 0;
		self.residual_boards <- 0;

    }//END REFLEX handle stop
    
    
    
    /*
     * Reflex function to handle the boarding part 3 cycles after handle_stop. By then, all the responses are in:
     *   - stop has agreed to 'Bus arrived'
     *   - droppers have agreed to 'Drop off' (will die in their own reflex)
     *   - waiting passengers have sent 'Board me' FIPA-requests with their frozen time_in_stop
     * 
     * The bus agrees/informs up to capacity, refuses the rest, and accumulates boarded_time_in_stops for the PASSENGERS log.
     * After processing, it computes the extra waiting time and either waits or finalizes immediately by sending the 'Update count'
     * message to the stop.
     */
    reflex handle_stop_response_and_boards when: (self.processing_passengers = true and self.waiting = false 
    											and self.extra_waiting_time = false and self.arrived_to_end = false
    											and cycle > self.comms_cycle + 2)
	{
		
		//---- consume the stop's agree to 'Bus arrived' ----
		loop msg over: agrees {
			list c <- list(msg.contents);
			if (length(c) < 1 and string(c[0]) != 'Ok telling passengers'){
				write "Error, unknown message";
			}
			else if (length(c) < 1 and string(c[0]) != 'Ok dropping'){
				//dropper agree -- counted only via confirmed_droppers length; consume
				write "Error, unknown message";
			}
		}
		
		
		//--cleanup de Done Telling Passengers.
		message m <- informs at 0;
		list m_cont <- list(m.contents);
		if (length(m_cont) < 1 and string(m_cont[0]) != 'Done telling passengers'){
			write "Error, unknown message that should be done telling passengers" + m_cont;
		}
		
		
		//---- consume the stop's inform to dropoff ----
		loop msg over: informs {
			list b <- list(msg.contents);
			if (length(b) < 1 and string(b[0]) != 'Dropped'){
				write "Error, unknown message " + b;
			}
			else{
				passengers_on_bus >> msg.sender;
			}
		}


		
		
		//---- process board requests from passengers ----
		loop board_msg over: requests {
			list c <- list(board_msg.contents);
			if (length(c) >= 2 and string(c[0]) = 'Board me'){
				
				passenger pax <- passenger(board_msg.sender);
				float pax_time_in_stop <- float(c[1]);
				
				if (length(passengers_on_bus) < max_passengers){
					
					//Capacity left -> board
					passengers_on_bus << pax;
					boarded_time_in_stops << pax_time_in_stop;
					self.boards <- self.boards + 1;
					
					do agree message: board_msg contents: ['Boarded'];
					do inform message: board_msg contents: ['Welcome', self.id];
				}
				else{
					//Bus full -> refuse
					self.residual_boards <- self.residual_boards + 1;
					do refuse message: board_msg contents: ['Bus full'];
				}
			}
		}//End loop board requests
		
		
		//Estimate the time needed for boarding and discharging the passengers.
		self.cycles_to_wait <- world.await_time_per_bus(self.boards, self.dropoffs);
		
		
		if (self.cycles_to_wait > 0){
			self.extra_waiting_time <- true;
		}
		else {
			
			//Copy the configuration from the spend_extra_time_in_stop where the bus comms with the stop to request it to update its vales
			self.waiting <- true;
			self.comms_cycle <- cycle;
			
			do start_conversation to: [stops_list[self.direction][self.stops_reached]] protocol: 'fipa-request' performative: 'request' 
							contents: ['Update count', self.boards, self.boarded_time_in_stops];
		
		
			/*
			 * Write in the .log the result of the stop procedure. IN this log, it will be saved (Simulation ID, Bus realizing it, StopCode, Time
			 * Board, total boards expected(or residual_boards) and dropoffs. Also the ocupation valueç
			 */
			buffer_results << [world.name, self.id, self.travels_completed, stops_list[self.direction][self.stops_reached].stopNum, self.direction,
					current_time, TimeSlot, self.departure_timeslot, self.boards, self.residual_boards, self.dropoffs, length(passengers_on_bus), self.time_travelled] ;
		}
		
	}//end reflex handle_stop_response_and_boards
    
    
    /*
     * Reflex function to handle the extra time in stop boarding or discharging passengers.
     */
    reflex spend_extra_time_in_stop when: self.extra_waiting_time {
    	
    	self.cycles_to_wait <- self.cycles_to_wait -1;
    	
    	if (self.cycles_to_wait = 0){
    		
    		
    		self.extra_waiting_time <- false;
    		
			do start_conversation to: [stops_list[self.direction][self.stops_reached]] protocol: 'fipa-request' performative: 'request' 
							contents: ['Update count', self.boards, self.boarded_time_in_stops];
		
		
			/*
			 * Write in the .log the result of the stop procedure. IN this log, it will be saved (Simulation ID, Bus realizing it, StopCode, Time
			 * Board, total boards expected(or residual_boards) and dropoffs. Also the ocupation valueç
			 */
			buffer_results << [world.name, self.id, self.travels_completed, stops_list[self.direction][self.stops_reached].stopNum, self.direction,
					current_time, TimeSlot,self.departure_timeslot, self.boards, self.residual_boards, self.dropoffs, length(passengers_on_bus), self.time_travelled] ;    		
    		
			self.waiting <- true;
			self.comms_cycle <- cycle;
    	}
    	
    }//End reflex spend_extra_time_in_stop
    
    
    
    
    
    
    /*
     * Reflex function to verify that the stop updated its value of passengers based on the new boards.
     * Resets per-segment state (time_travelled, processing_passengers, waiting, approach_broadcast_done,
     * confirmed_droppers, boarded_time_in_stops) and advances to the next stop.
     */
    reflex verify_stop_and_restart_way when: (self.waiting = true and self.extra_waiting_time = false 
    										and cycle > self.comms_cycle and self.arrived_to_end = false){
    	
    	
    	//Consume stop's agree+inform of the count update
    	loop msg over: agrees {
			list c <- list(msg.contents);
			if (length(c) < 1 and string(c[0]) != 'Ok updating count'){
				write "ERror message unknown";
			}
		}
		loop msg over: informs {
			list c <- list(msg.contents);
			if (length(c) < 1 and string(c[0]) != 'Done updating count'){
				write "Error message unknown";
			}
		}
    	
    	
    	self.time_travelled <- 0.0;
    	self.processing_passengers <- false;
    	self.waiting <- false;
    	self.stops_reached <- self.stops_reached + 1;
    	self.stopped <- false;
    	self.approach_broadcast_done <- false;
    	self.confirmed_droppers <- [];
    	self.boarded_time_in_stops <- [];
    	
		time_between_stops <- world.estimate_time_between_stops(stops_list[direction][stops_reached - 1].stopNum, direction);
		
    }//End reflex verify stop and restart way
    
    
    
    
    /*
     * Reflex to handle the LAST stop of the route. At the terminal stop, all on-board passengers
     * drop off unconditionally. No 'Bus arrived' / boarding / count-update flow is run. We send
     * 'Drop off' FIPA-requests to every passenger currently on board (regardless of the
     * confirmed_droppers list -- this is robust to short last-segments where the broadcast didnt
     * have time to fully cycle).
     */
    reflex handle_last_stop when: (self.arrived_to_end = true and self.stopped = true and self.processing_passengers = false){
    	
    	list<passenger> alive_pass <- passengers_on_bus where (!dead(each));
    	if (length(alive_pass) = 0){
    		//No one to drop -> directly transition to handle_shifts
    		self.dropoffs <- 0;
    		self.finished_shift <- true;
    		self.stopped <- false;
    		return;
    	}
    	
    	self.dropoffs <- length(alive_pass);
    	
    	do start_conversation to: alive_pass protocol: 'fipa-request' performative: 'request' contents: ['Drop off'];
    	
    	self.processing_passengers <- true;
    	self.comms_cycle <- cycle;
    	
    }//End reflex handle_last_stop
    
    
    
    /*
     * Reflex to wait until all passengers have removed themselves from passengers_on_bus
     * (they do so in their die_after_drop reflex). Then transition to handle_shifts via finished_shift = true.
     */
    reflex finalize_last_stop_dropoffs when: (self.arrived_to_end = true and self.processing_passengers = true 
    											 and cycle > self.comms_cycle){
    	
    	//Consume any dropper agrees still hanging in the inbox
    	loop msg over: agrees {
			list c <- list(msg.contents);
			if (length(c) >= 1 and string(c[0]) = 'Ok dropping'){
				agrees >> msg;
			}
		}
		
		
    	loop msg over: informs {
	    	list c <- list(msg.contents);
		    if (length(c) >= 1){
		        string ctype <- string(c[0]);
		        if (ctype != 'I_WILL_DROP' and ctype != 'I_WILL_STAY' and ctype != 'Dropped'){
		        	write "Error unknown message" + ctype;
	        	}
	        	else if (ctype = 'Dropped'){
	        		passengers_on_bus >> msg.sender;
	        	}
	    	}
		}
    	
    	
    	self.processing_passengers <- false;
    	self.stopped <- false;
    	self.finished_shift <- true;
    	
    }//End reflex finalize_last_stop_dropoffs
    
    
	
	/*
	 * Reflex used to handle the shifting process.
	 * Same logic as the original. The terminal-stop log row records self.dropoffs (set in handle_last_stop)
	 * instead of the stale self.passengers from the original (which was always 0 right before reset).
	 */
	reflex handle_shifts when: (self.finished_shift = true){
		
		//it needs to write the last stop information.
		buffer_results << [world.name, self.id, self.travels_completed, stops_list[self.direction][self.stops_reached].stopNum, self.direction,
		current_time, TimeSlot, self.departure_timeslot, 0, 0, self.dropoffs, 0, self.time_travelled];
    	
    	
    	
		self.finished_shift <- false;
		
		
		if (departure_times[travels_completed] = last(departure_times)){
			//Save all the rows accumulated in the buffer in its files
			loop row over: buffer_results {
				save row to: '../logs/RESULTS/log_' + world.name + '.csv' format: 'csv' rewrite: false;
			}
			
			loop row over: buffer_events {
				save row to: '../logs/EVENTS/log_' + world.name + '.csv' format: 'csv' rewrite: false;
			}
		
			do die;
		}
		
		travels_completed <- travels_completed + 1;
		departure_time <- departure_times[travels_completed];
		if (direction = "toA"){
			direction <- "toB";
		}else{
			direction <- "toA";
		}
		
		if (world.time_to_minutes(self.departure_time) < world.time_to_minutes(current_time)){
			//Delayed, but allowed to leave
			allowed_to_leave <- true;
			stops_reached <- 0;
			self.departure_timeslot <- TimeSlot;
			self.stopped <- true;
			
			//If it enters here, it means a delay is produced,so there will be a writing inside a EVENTS.log
			//The order of the variables will be world.name, id of the bus, StopCode, EVENTCODE, Current Time, Departure Time
			//And Current time - departure time
			buffer_events << [world.name, self.id, self.travels_completed, stops_list[self.direction][self.stops_reached].stopNum, self.direction,
				TimeSlot, "DELAY", current_time, self.departure_time, world.time_to_minutes(current_time) - world.time_to_minutes(self.departure_time)] ;		
		}
		else{
			allowed_to_leave <- false;
		}//End case if the bus is arriving late to its next departure
		
		//reset the variables
		stops_reached <- 0;
	    arrived_to_end <- false;
	    self.passengers_on_bus <- [];
	    self.confirmed_droppers <- [];
	    self.boarded_time_in_stops <- [];
	    self.approach_broadcast_done <- false;
	    self.time_travelled <- 0.0;
	}//End reflex handle_shifts
    
    
    
}//End specie bus






//--------------------------------------------------------------------------------------------------------------------------------
//--------------------------------------------------------------------------------------------------------------------------------
//-------------------------------------------SPECIES_DEFINITION-PASSENGER VERSION-------------------------------------------------
//--------------------------------------------------------------------------------------------------------------------------------
//--------------------------------------------------------------------------------------------------------------------------------



/*
 * Definition of the type specie PASSENGER.
 * Skills fipa, same as the bus and stop, to handle FIPA comms.
 *
 * Replaces the placeholder passenger of the older model. Real passengers spawn at stops, accumulate time_in_stop while waiting,
 * board buses on demand (passing their frozen time_in_stop in the FIPA-request) and respond to the in-transit STOP_APPROACH
 * broadcast or to the LAST_STOP broadcast indicating whether or not they will drop off at the next stop.
 */
species passenger skills: [fipa] {
	
	
	//Identifier
    int id;
    
    //Bool variable to know whether the passenger is on a bus or not
    bool on_bus <- false;
    
    //Reference to the stop where the passenger is currently waiting (only valid while on_bus = false)
    stop current_stop_ref <- nil;
    
    //To know which bus is the passenger mounted in
    bus mounted_bus <- nil;
    
    
    //Frozen on board: keeps the wait-at-stop value the bus uses for stats and the invisible-hand uses for ranking dropoff selection
    float time_in_stop <- 0.0;
    
    
    //Bool variable if he was marked by the invisible hand to drop off when a stop is approaching
    bool wants_to_drop <- false;
    
    //Bool flag to delay the do die one cycle so the agree FIPA message is actually transmitted
    bool die_flag <- false;
    
    
    //BOOL VARIABLE TO HOLD a pending board response state. While waiting for the bus's response to our 'Board me' request, we ignore further alerts
    bool pending_board_response <- false;
    
    //To know which bus we sent the 'Board me' request to
    bus pending_board_bus <- nil;
    
    
    
    //DEFAULT ASPECT FOR THE GUI EXPERIMENT
    aspect default {
    	if (on_bus){
    		//IF ON BUS, YELLOW CIRCLE
    		draw circle(15) color: #yellow border: #black;
    	}
    	else{
    		//IF AT STOP, RED CIRCLE WITH THE WAIT TIME UNDER IT
    		draw circle(15) color: #red border: #black;
    	}
    }//END ASPECT DEF
    
    
    
    /*
     * Reflex function to grow the time_in_stop counter every cycle while waiting at the stop.
     * Once on_bus = true, the guard becomes false and the counter is naturally frozen.
     */
    reflex wait_at_stop when: (on_bus = false and die_flag = false){
    	
    	time_in_stop <- time_in_stop + step;
    	
    }//End reflex wait_at_stop
    
    
    
    /*
     * Reflex to keep the visual location synced with the bus while on board. Just a cosmetic thing for the GUI.
     */
    reflex update_location_with_bus when: (on_bus = true and mounted_bus != nil){
    	
    	location <- mounted_bus.location;
    	
    }//End reflex update_location_with_bus
    
    
    
    /*
     * Reflex to respond to the in-transit broadcast (STOP_APPROACH or LAST_STOP). The response is set from tyhe query
     * Just inform
     *
     *   - LAST_STOP -> always I_WILL_DROP (per spec, all passengers drop)
     *   - STOP_APPROACH -> I_WILL_DROP iff wants_to_drop was set by the invisible hand, else I_WILL_STAY
     *
     * Each querie is dropped after so wont repeat the answer
     */
    reflex respond_to_approach when: (on_bus = true and not empty(queries)){
    	
    	loop msg over: queries{
    		list c <- list(msg.contents);
    		if (length(c) >= 1){
    			string ctype <- string(c[0]);
    			if (ctype = 'STOP_APPROACH' or ctype = 'LAST_STOP'){
					do agree message: msg contents: ["Ok"];
    				
    				string response;
    				if (ctype = 'LAST_STOP' or wants_to_drop = true){
    					response <- 'I_WILL_DROP';
    				}else{
    					response <- 'I_WILL_STAY';
    				}
    				
    				if (mounted_bus != nil){
    					do inform message: msg contents: [response];
    				}
    			}
    			else if (ctype = 'Welcome'){
    				//Belated welcome inform from boarding; just consume.
    			}
    		}
    	}//End loop
    	
    }//End reflex respond_to_approach
    
    
    
    /*
     * Reflex to handle the 'Board bus' FIPA-request from the stop. We agree (acknowledging the stop), then start a
     * new FIPA-request conversation to the bus with our frozen-by-the-instant time_in_stop, which the bus uses
     * both for capacity decisions and for the PASSENGERS log.
     *
     * If we are already pending a response from a previous bus, we ignore.
     */
    reflex handle_board_alert when: (on_bus = false and die_flag = false and pending_board_response = false and not empty(requests)){
    	
    	loop msg over: requests{
    		list c <- list(msg.contents);
    		if (length(c) >= 2 and string(c[0]) = 'Board bus'){
    			
    			bus target_bus <- bus(c[1]);
    			
    			//Acknowledge the stop
    			do agree message: msg contents: ['Ok'];
    			do inform message: msg contents: ['Done acknowledging'];
    			
    			
    			//Start a new conversation to the bus with the frozen time_in_stop
    			if (target_bus != nil){
    				pending_board_response <- true;
    				pending_board_bus <- target_bus;
    				do start_conversation to: [target_bus] protocol: 'fipa-request' performative: 'request' contents: ['Board me', time_in_stop];
    			}
    		}
    	}//End loop
    	
    }//End reflex handle_board_alert
    
    
    
    /*
     * Reflex to handle the bus's response to our 'Board me' request:
     *   - agree+inform 'Boarded'/'Welcome' -> we move onto the bus, remove ourselves from the stop's passengers_at_stop,
     *     and freeze time_in_stop (it stops growing because the wait_at_stop guard becomes false).
     *   - refuse 'Bus full' -> we stay at the stop and time_in_stop continues.
     */
    reflex handle_board_response when: (on_bus = false and pending_board_response = true){
    	
    	//Boarded path: we received an agree
    	if (not empty(agrees)){
    		loop msg over: agrees{
    			list c <- list(msg.contents);
    			if (length(c) >= 1 and string(c[0]) = 'Boarded'){
    				
    				on_bus <- true;
    				mounted_bus <- pending_board_bus;
    				
    				if (current_stop_ref != nil){
    					ask current_stop_ref { passengers_at_stop >> myself; }
    					current_stop_ref <- nil;
    				}
    				
    				pending_board_response <- false;
    				pending_board_bus <- nil;
    			}
    		}
    		return;
    	}
    	
    	//Refused path
    	if (not empty(refuses)){
    		loop msg over: refuses{
    			list c <- list(msg.contents);
    			if (length(c) >= 1 and string(c[0]) = 'Bus full'){
    				pending_board_response <- false;
    				pending_board_bus <- nil;
    			}
    		}
    	}
    	
    }//End reflex handle_board_response
    
    
    
    /*
     * Reflex to handle the 'Drop off' FIPA-request from the bus. We agree, set die_flag, and the
     * die_after_drop reflex will remove us from the bus's passengers_on_bus list and call do die in
     * a subsequent cycle.
     */
    reflex handle_dropoff_request when: (on_bus = true and die_flag = false and not empty(requests)){
    	
    	loop msg over: requests{
    		list c <- list(msg.contents);
    		if (length(c) >= 1 and string(c[0]) = 'Drop off'){
    			do agree message: msg contents: ['Ok dropping'];
				do inform message: msg contents: ['Dropped'];
    			die_flag <- true;
    		}
    	}//End loop
    	
    }//End reflex handle_dropoff_request
    
    
    
    /*
     * Reflex to self-remove from the bus's passenger list followed by death. Done in a separate reflex
     * (different cycle) from handle_dropoff_request so the agree FIPA message is actually transmitted before we die.
     */
    reflex die_after_drop when: die_flag = true {
    	
//    	if (mounted_bus != nil){
//    		ask mounted_bus { passengers_on_bus >> myself; }
//    	}
    	do die;
    	
    }//End reflex die_after_drop
    
    
}//End specie passenger






//--------------------------------------------------------------------------------------------------------------------------------
//--------------------------------------------------------------------------------------------------------------------------------
//-------------------------------------------SPECIES_DEFINITION-ROUTES VERSION----------------------------------------------------
//--------------------------------------------------------------------------------------------------------------------------------
//--------------------------------------------------------------------------------------------------------------------------------
		

/*
 * Specie stop definition
 * 
 * 
 * It includes the fipa skill, to handle the communications with other agents using a standar protocol.
 * Now it also stores REAL passenger agents waiting on it (passengers_at_stop) instead of the older list of [id, time] tuples
 * 
 */
species stop skills: [fipa]  {
	
	//NAME OF THE STOP
    string stopName;
    
    //STOP CODE
    int stopNum;
    
    //DISTANCE FROM ORIGIN
    int distance;
    
    
    //MAP CONTAINING THE DISTRIBUTIONS FOR THE DAY
    map<int, map<string,list>> stop_distributions;
    
    
    //VALUE FOR PASSENGER GENERATION RATIO
    float board_generation_ratio;
    
    //VAUE FOR THE NEXT GENERATIO RATIO
    float next_board_generation_ratio;
    
    
    //Value that serve as an accumulator for the passengers that are generated over the course of an hour.
    float passengers_to_be_generated <- 0.0;
    
    
    //Int value containing the passengers that are actually generated. In case the value sto add to the float self.passengers to be generated
    //is negative, that wont affect the passengers already created
    int passengers_generated;
    
    
    //REAL passenger agents currently waiting at this stop. Replaces the older passengers_with_time list of [id, time] tuples
    list<passenger> passengers_at_stop <- [];
    

    aspect default {
    	
        draw circle(50) color: #purple border: #black;
       	
    }

    aspect simple {
        draw shape color: #red;
    }
    
    
    
    /*
     * Reflex function to handle the comms between this agent and the requesting agents.
     * 
     * Now handles two kinds of FIPA-requests from the bus:
     *   - 'Bus arrived'  -> agree+inform, snapshot the waiting list, fan out 'Board bus' to every passenger
     *   - 'Update count' -> agree+inform, write the PASSENGERS log row from the time list passed in the contents
     * 
     * Both come from the same bus over the same FIPA inbox so they are handled in the same loop.
     */
    reflex handle_bus_arrived when: (not empty(requests))
    {
    	
    	loop msg over: requests{
    		list c <- list(msg.contents);
    		
    		//----- 'Bus arrived' case -----
    		if (length(c) >= 1 and string(c[0]) = 'Bus arrived'){
    			
    			bus arriving_bus <- bus(msg.sender);
    			
    			do agree message: msg contents: ['Ok telling passengers'];
    			do inform message: msg contents: ['Done telling passengers'];
    			
    			if (arriving_bus != nil and length(passengers_at_stop) > 0){
    				
    				//Snapshot: list at this exact moment. New arrivals after this point will miss this bus
    				list<passenger> waiting_snapshot <- copy(passengers_at_stop);
    				
    				do start_conversation to: waiting_snapshot protocol: 'fipa-request' performative: 'request' contents: ['Board bus', arriving_bus];
    			}
    			
    		}
    		
    		//----- 'Update count' case -----
    		else if (length(c) >= 2 and string(c[0]) = 'Update count'){
    			
    			int n_boarded <- int(c[1]);
    			list<float> time_from_passengers <- list<float>(c[2]);
    			
    			do agree message: msg contents: ['Ok updating count'];
    			do inform message: msg contents: ['Done updating count'];
    			
    			if (n_boarded > 0){
    				string attr_bus_id <- bus(msg.sender).id;
    				int attr_bus_travels_completed <- bus(msg.sender).travels_completed;
    				
    				save [world.name, attr_bus_id, attr_bus_travels_completed, self.stopNum, TimeSlot, current_time,
    						"\"" + replace(string(time_from_passengers), ",", ";") + "\""] 
    						to: '../logs/PASSENGERS/log_' + world.name + '.csv' format: 'csv' rewrite: false;
    			}
    			
    			self.passengers_generated <- self.passengers_generated - n_boarded;
    		}
    	}//End loop
    	
    }//END REFLEX handle_bus_arrived
    
    
    
    /*
     * Defensive cleanup reflex: passengers send agree+inform to us when they receive 'Board bus'.
     * We have no further action, so we just consume to keep the inboxes from growing unbounded.
     */
    reflex consume_passenger_acks when: (not empty(agrees) or not empty(informs)){
    	
    	loop msg over: agrees{
    		list c <- list(msg.contents);
    		if (length(c) < 1 and string(c[0]) != 'Ok'){
    			write "Error message unknown";
    		}
    	}
    	loop msg over: informs{
    		list c <- list(msg.contents);
    		if (length(c) < 1 and string(c[0]) != 'Done acknowledging'){
    			write "Error unknown message";
    		}
    	}
    	
    }//End reflex consume_passenger_acks
    

}//END SPECIE STOP




/*
 * Specie route definition
 * This specie is purely static
 * It does nothing more than being drawn in the experiment
 * 
 */
species route {
	
	
	//ATTRIBUTE ROUTENAME(E.G like a street name or an intersection)
    string routename;
    
    //DISTANCE IN METERS FROM THE ORIGIN
    int distance;
    
    //UNIQUE IDENTIFIER
    int id;
    
    aspect default {
        draw shape color: #blue width: 3;
    }
    
}//END SPECIE ROUTE



/*
 * Experiment to test out the result of the code
 * 
 *
 * It visualizes the agent bus as it navigates throughout the route.
 * 
 */
experiment test type: gui {
    output {
        display mapa type: opengl background: #white {
        	
        	//LOAD THE BACKGROUNDS GUI INFORMATION
            species route aspect: default;
            species stop aspect: default;
            species bus aspect: default;
            species passenger aspect: default;


            graphics "clock" {
                draw "Time: " + current_time 
                    at: {100, 100} 
                    color: #black 
                    font: font("TimesNewRoman", 20, #bold);
                draw "Timeslot: " + int(TimeSlot)
                    at: {100, 350} 
                    color: #gray 
                    font: font("TimesNewRoman", 14, #plain);
            }//End graphics

        }//END DISPLAY

    }//END OUTPUT
  
}//END EXPERIMENT



experiment batch_1000 type: batch repeat: 1000 parallel: 16 until: empty(bus) {
}
