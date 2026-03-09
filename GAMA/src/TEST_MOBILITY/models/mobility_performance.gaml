/**
* Name: mobilitymodel
* Bus route simulation to try out GAMA species and agents implementation
* Author: hectoralv22
*/




model mobility_model




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

	//FOR THE LOG
	int sim_id <- 0;
	

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
     * As negative binomial distribution is not implemented, using the Gamma-Poisson mixture gives the correct data
     */
	int sample_negative_binomial(float r, float p) {
		
		
		//Extreme case. If r detects a 0, value, just return, 0
		if (r = 0.0){
			return 0;
		}
		
	    float gamma_val <- gamma_rnd(r, (1-p)/p);
	    
	    int result <- poisson(gamma_val);
	    
	    return max(0, result);
	    
	}//End function sample_negative_binomial
    
    
    
    
    //GEOMETRICAL
    
    /*
     * As geometrical distribution is not implemented, using the inverse transform method, taking ln's
     */
	float sample_geometric(float p) {
		
		
		if (p >= 1.0) {
        return 0.0;
    	}
		
    	float u <- rnd(0.0001, 0.9999);
    	
    	return floor(ln(u) / ln(1 - p));
    	
	}//End function sample_geometric
     
     

    
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
		 * Secondary Dict: {Key(TimeSlot: Value: Dict}
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
	float step <- 10 #seconds;
	

	float time <- cycle * step;
	
	
	//Initialize minutes
	int minutes <- 0;

	
	//Initialize sim TimeSlot
	int TimeSlot;
	

	/*
	 * Global reflex to handle each iteration the time that has passed. It will save
	 */
	reflex update_time {
		
        // Convert total simulated time to minutes
        int total_minutes <- int(time / 60);  // time is in seconds
        
        
        // Calculate hours and minutes from simulation start (5:00)
        TimeSlot <- 5 + int(total_minutes / 60);
       
        //Calculate minutes passed in the hour by dividing by 60
        minutes <- mod(total_minutes, 60);
		
    
	}//End reflex update_time


	//Map the TimeSlot + minutes into a string, to compare with the input
	string current_time -> string(TimeSlot) + ":" + (minutes < 10 ? "0" + string(minutes) : string(minutes));	
	
	
	
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
	 * In this model, as its focused onperformance, it just represents int values.
	 */
	reflex generate_passengers_from_distributions {
		
		loop stop_iter over: all_unique_stops{
			stop_iter.passengers_to_be_generated <- stop_iter.passengers_to_be_generated + 
						stops_distribution_values[stop_iter.stopNum][int(mod(time, 3600) / step)];
						
			
			int passengers_generated_new <- int(stop_iter.passengers_to_be_generated);
			
			if (passengers_generated_new > 0){
				stop_iter.passengers_to_be_generated <- stop_iter.passengers_to_be_generated - passengers_generated_new;
				stop_iter.passengers_generated <- stop_iter.passengers_generated + passengers_generated_new;
			}
		}//End loop

	}//End reflex generate passengers from distributions


	
	/*
	 * Reflex to handle the END of the sim once no bus is kept alive
	 */ 
	reflex end_real_simulation when: empty(bus){
		write "Ending execution " + world.name;
        do die;  //CHAO CHAO CHAO CHAO
	}

	
    
    /*
     * Global function to pass to minutes the time in hh:mm
     */
	int time_to_minutes(string t) {
		
	    list<string> parts <- t split_with ":";
	    
	    return int(parts[0]) * 60 + int(parts[1]);
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
			return max(gauss(mean, std), step);
		}
		if (TimeSlot >= 24){
			float mean <- global_time_stops_values[direction][stopNum][((23)-5)*2];
			float std <- global_time_stops_values[direction][stopNum][((23)-5)*2 + 1];
			return max(gauss(mean, std), step);
		}
		
		float mean <- global_time_stops_values[direction][stopNum][((TimeSlot)-5)*2];
		float std <- global_time_stops_values[direction][stopNum][((TimeSlot)-5)*2 + 1];
		return max(gauss(mean, std), step);	

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
 * 
 * 
 * 
 * Skills fipa means that this agent inherit the FIPA communication protocol. Used to communicate between bus agents 
 * and stops agents
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
    
    
    //Number of passengers
    int passengers <- 0;
    
    
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
    
    
    //Deprecated, The EMT did not like this as KPI
    /* 
    //Seatable capacity
    int seatable_capacity <- 28;
    */
    
    //To wait for the acceptance of the proposals
    bool waiting <- false;
    
    //Bool variable to know wether the bus has finished a shift(Arrive to its destintation, or not). It will trigger a reflextu change the direction or die.
    bool finished_shift <- false;
    
        
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
	        draw string(passengers) color: #black size: 1 at: location + {0, -80};
        	
        	
        }//END ELSE ASPECT DEF
        
    }//END ASPECT DEF
    


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
     * Once the agent has reached its destination, dies todo THIS WILL CHANGE WHEN LOGICAL BUSES ARE INSERTED
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
    				
				self.finished_shift <- true;
				
    		}else{
    			//If it enters here, a sop has been reached, but no end destination, so simply stopped = true so it starts handling the board/dropoff
    			
    			self.stopped <- true;

    		}//End if else last direction

    	}//End if in new stop
    	
    	
    }//end reflex move_to_destination


	
	/*
	 * Reflex used to handle the shifting process.
	 */
	reflex handle_shifts when: (self.finished_shift = true){
		
		//it needs to write the last stop information.
		save [world.name, self.id, stops_list[self.direction][self.stops_reached].stopNum, self.direction,
		current_time, TimeSlot,0, 0,self.passengers,0,self.time_travelled]
    	to: '../logs/RESULTS/log_' + world.name + '.csv' format: "csv" rewrite: false;
    	
    	
		self.finished_shift <- false;
		
		
		if (departure_times[travels_completed] = last(departure_times)){
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
			//No need to  ths, as in the first sop no need of travelling. The bus is already there
			self.stopped <- true;
			//time_between_stops <- world.estimate_time_between_stops(stops_list[direction][stops_reached].stopNum, direction);
			
			//If it enters here, it means a delay is produced,so there will be a writing inside a EVENTS.log
			//The order of the variables will be world.name, id of the bus, StopCode, EVENTCODE, Current Time, Departure Time
			//And Current time - departure time
			save [world.name, self.id, stops_list[self.direction][self.stops_reached].stopNum, self.direction,
				"DELAY", current_time, self.departure_time, world.time_to_minutes(current_time) -world.time_to_minutes(self.departure_time)] 
    			to: '../logs/EVENTS/log_' + world.name + '.csv' format: "csv" rewrite: false;
		}
		else{
			allowed_to_leave <- false;
		}//End case if the bus is arriving late to its next departure
		
		//reset the variables
		stops_reached <- 0;
	    arrived_to_end <- false;
	    self.passengers <- 0;
	    self.time_travelled <- 0.0;
	}


    /*
     * 
     *Reflex function to handle the abstraction of communicating with the agent stop
     *
     *It simply stablish a conversation using FIPA protocol with the stop agent. The fipa protocol is a standar 
     * and mainly its being used for the propose/acceptance_propose  kinda type of communication
     * 
     *The last line, as specified in the comment below, its a particular case, because the next cycle 
     * after the message has been sent, the flag processing passengers will not have change, as this reflex is 
     * read before handle_answer.
     *
     */
    reflex handle_stop when: (self.stopped = true and self.processing_passengers = false)
    {
    	
    	/*LOGIC TO COMMUNICATE WITH THE AGENT STOP WHICH IS IN
    	 * 
    	 *This is gonna use FIPA protocol. It will launch a fipa propose to the agent stop which is in
    	 *The returning message will be processed in the handle_answer reflex
    	 * 
    	 */
		
		
		//INICIATE CONVERSATION
    	do start_conversation to: [stops_list[self.direction][self.stops_reached]] protocol: 'fipa-query' performative: 'query' contents: ['Bus arrived to stop'];
		
		
		//THIS LINE IS JUST FOR THE BUS IN THE NEXT CYCLE NOT REPEATING THE SENDING MESSAGE
		self.processing_passengers <- true;
		
		//To not trigger handle_stop_answer till next cycle
		self.comms_cycle <- cycle;

    }//END REFLEX handle stop
    
    
    
    /*
     * Reflex function to handle the board/Dropoff of passengers. It reads the content */
    reflex handle_stop_answer when: (self.processing_passengers = true and cycle > self.comms_cycle and self.waiting = false and !empty(agrees))
	{

		message agree_query <- agrees at 0;
		
		list content_agree <- agree_query.contents;

		if (content_agree != ["Here is the passenger list"]){
			write "RARUNO";
		}
		
		message inform_data_stop <- informs at 0;
		
		//First, handle dropoffs
		int dropoffs <- int(list(inform_data_stop.contents)[1]);
		
		if (dropoffs > self.passengers){
			self.passengers <- 0;
			dropoffs <- self.passengers;
		}
		else{
			self.passengers <- self.passengers - dropoffs;
		}
		
		//handle boards
		int boards <- int(list(inform_data_stop.contents)[0]);
		
		//to handle excess of boards
		int residual_boards <- 0;
		
		
		if (boards + self.passengers > self.max_passengers){
			//How many cannot board
			residual_boards <- (boards + self.passengers) -self.max_passengers;
			self.passengers <- self.max_passengers;
		}
		else {
			self.passengers <- self.passengers + boards;
		}
	
	
	self.waiting <- true;
	self.comms_cycle <- cycle;
	
	do start_conversation to: [stops_list[self.direction][self.stops_reached]] protocol: 'fipa-request' performative: 'request' 
								contents: ['Update passengers. I boarded',(boards-residual_boards)];
		
		
		
	/*
	 * Write in the .log the result of the stop procedure. IN this log, it will be saved (Simulation ID, Bus realizing it, StopCode, Time
	 * Board, total boards expected(or residual_boards) and dropoffs. Also the ocupation valueç
	 */
	save [world.name, self.id, stops_list[self.direction][self.stops_reached].stopNum, self.direction,
			current_time, TimeSlot, boards, residual_boards,dropoffs,self.passengers,self.time_travelled] 
    	to: '../logs/RESULTS/log_' + world.name + '.csv' format: "csv" rewrite: false;
    	
	
	}//end reflex handle stop answer
    
    
    /*
     * Reflex function to verify that the stop updated its value of passengers based on the new boards */
    reflex verify_stop_and_restart_way when: (self.waiting = true and cycle > self.comms_cycle){
    	
    	message agree_resp <- agrees at 0;
		message inform_resp <- informs at 0;
		
		if (agree_resp.contents != ["Ok"]){
			write "ERROR";
		}
		if (inform_resp.contents != ["Done"]){
			write "ERROR";
		}
    	
    	self.time_travelled <- 0.0;
    	self.processing_passengers <- false;
    	self.waiting <- false;
    	self.stops_reached <- self.stops_reached + 1;
    	self.stopped <- false;
		time_between_stops <- world.estimate_time_between_stops(stops_list[direction][stops_reached].stopNum, direction);
		
    }//End reflex verify stop and restart way
    
    
}//End specie bus






//--------------------------------------------------------------------------------------------------------------------------------
//--------------------------------------------------------------------------------------------------------------------------------
//-------------------------------------------SPECIES_DEFINITION-ROUTES VERSION----------------------------------------------------
//--------------------------------------------------------------------------------------------------------------------------------
//--------------------------------------------------------------------------------------------------------------------------------
		

/*
 * Specie stop definition
 * 
 * 
 * It includes the fipa skill, to handle the communications with other agents using a standar protocol
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
    
    //Variable to wait for the answer back from the bus when its processing passengers
    bool waiting_for_bus_answer<- false;
    

    aspect default {
    	
        draw circle(50) color: #purple border: #black;
        draw stopName + " " + passengers_generated color: #black size: 1 at: location + {0, -80};
       	
    }

    aspect simple {
        draw shape color: #red;
    }
    
    /*
     * Reflex function to handle the comms between this agent and the requesting agents
     * 
     * It simply reads the message metadata and answer back with the number of passengers rn in the stop
     * 
     */
    reflex communicate_with_bus when: (!(empty(queries)) and waiting_for_bus_answer = false)
    {
    	
    	//CHECK OUT THE RECEIVING MESSAGE
		message queryFromInitiator <- queries at 0;
		
		if (list(queryFromInitiator.contents)[0] != 'Bus arrived to stop'){
			write "QUE PUÑETAAS";
		}
		
		//THIS IS WRONG. THIS SHOULD BE GENERATED FROM THE SIM. In this case of performance, DropOff is just the indicator of how many it
		//Decrease the occupation value.
		
		//Infer the number of passengers that are gonna drop off 
		int dropoff_passengers;
		
		if (global_distribution_values[stopNum][TimeSlot]["DropOffs"][0] = "NORMAL"){
			
			dropoff_passengers <- max(floor(gauss(float(global_distribution_values[stopNum][TimeSlot]["DropOffs"][1]),
												float(global_distribution_values[stopNum][TimeSlot]["DropOffs"][2]))), 0);
		}
		if (global_distribution_values[stopNum][TimeSlot]["DropOffs"][0] = "NEGATIVE BINOMIAL"){
			
			dropoff_passengers <- max(floor(world.sample_negative_binomial(float(global_distribution_values[stopNum][TimeSlot]["DropOffs"][1]),
												float(global_distribution_values[stopNum][TimeSlot]["DropOffs"][2]))), 0);
			
		}
		if (global_distribution_values[stopNum][TimeSlot]["DropOffs"][0] = "GEOMETRICAL"){
			
			dropoff_passengers <- max(floor(world.sample_geometric(float(global_distribution_values[stopNum][TimeSlot]["DropOffs"][1]))), 0);
			
		}
		
		if (global_distribution_values[stopNum][TimeSlot]["DropOffs"][0] = "NO DATA"){
			
			dropoff_passengers <- 0;
		}
		
		//ANSWER BACK WITH FIPA PROTOCOL QUERY
		do agree message: queryFromInitiator contents: ["Here is the passenger list"];
		do inform message: queryFromInitiator contents: [int(self.passengers_generated), dropoff_passengers];
		waiting_for_bus_answer <- true;
		
		
    }//END REFLEX cwb
    
    
    /*
     * Reflex process to handle the pick up of the message from the bus indicating how many passengers was able to pick up
     */
    reflex process_bus_answer when: (waiting_for_bus_answer = true and !(empty(requests))){
    	
		message inform_from_bus <- requests at 0;

		
		int number_of_boards <- int(list(inform_from_bus.contents)[1]);
		
		
		
		do agree message: inform_from_bus contents: ['Ok'];
		

		self.passengers_generated <- self.passengers_generated - number_of_boards;

		do inform message: inform_from_bus contents: ['Done'];
		
		
		waiting_for_bus_answer <- false;
		
    }//End reflex process_bus_answer

}//END SPECIE STOP




/*
 * Specie route definition
 * This specie is purely static
 * It does nothing more than being drawn in the experiment
 * 
 */
species route {
	
	
	//ATTRIBUTE ROUTENAME(E.G like a street name or an intersection
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



experiment batch_1000 type: batch repeat: 1000 parallel: 10 until: empty(bus) {
}

