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


	//CREATE GLOBAL VARIABLES TO SAVE GLOBAL SCOPE OF THE AGENTS CREATED
	list <stop> stops_list;
	
	
	
	//CREATE GLOBAL VARIABLE MAP FOR DISTRIBUTIONS TO SAVE GLOBAL SCOPE OF THE VALS
	map<int, map<int,map<string,list>>> global_distribution_values;
	
	
	
	
	//INPUT FILES
    file file_401route <- file("../includes/ROUTE/E01/E01_toA.shp");
    file file_401stops <- file("../includes/STOPS/E01/E01_stops_toA.shp");
    
    
    
    
    //ADAPT THE SCALE TO MATCH THE 401 RESOLUTION
    geometry shape <- envelope(file_401route);

    
    
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
        
      	
      	
      	write "LOADING THE MAP WITH ROUTES AND STOPS";
      	
      	
      	
      	//Read input for normal days distributions
      	file input_data_e01 <- csv_file("../includes/INPUTS/input_data_E01_toA.csv");
      	
      	
      	//Convert it as matrix
      	matrix input_as_matrix <- matrix(input_data_e01);
      	
		
		
		
      	//All stops willbe using the same Timeslots. Starting at 5 ending at 23
      	list<int> timeslots <- [5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23];
		
		
		
		
		//Declaration of the dictionary	
		map<int, map<int,map<string,list>>> distribution_values;
		
		
		/*
		 * Loop to obtain all the stopNums and store the data from the stops related to that num
		 * The skeleton of the distribution map will be the following:
		 * Dictionary distribution_values: {Key(StopNum): Value: Dict}
		 * Secondary Dict: {Key(TimeSlot: Value: Dict}
		 * Third Dict: {Key(Board): Value: ["DistrType", Param1, Param2], Key(DropOff): Value: ["DistrType", Param1, Param2]}
	     */
		loop stops_iter over: file_401stops {
			
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
    			loop i from: 0 to: input_as_matrix.rows {
    				
    				list row <- row_at(input_as_matrix, i);					
					
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
							
						//Save the third dictionary in the second dictionary				
						map_per_stop << timeslot::boards_dropoffs_per_timeslot;
						
    				}//End loop Timeslots

    				//Save the second dictionary in the first dictionary
    				distribution_values << stop_code::map_per_stop;

    				
    				
    			}//End if First Stop
    			
    			
    			
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
						
						//DropOffs
	    				list element_dropoffs <-  elements_from_stop[(timeslot - 5)];	
						
						//Boards
						list element_boards <- ["NO DATA", 0, 0];
						
						
						//Save in the third dictionary 
						boards_dropoffs_per_timeslot << "Boards"::element_boards;
						
						
						boards_dropoffs_per_timeslot << "DropOffs"::[element_dropoffs[3], element_dropoffs[4], element_dropoffs[5]];
							
						//Save the third dictionary in the second dictionary				
						map_per_stop << timeslot::boards_dropoffs_per_timeslot;
						
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
						
    				}//End loop Timeslots

    				//Save the second dictionary in the first dictionary
    				distribution_values << stop_code::map_per_stop;
    				
    			}//End if general case
    			
			
				
    		
		}//End loop stops_iter


		global_distribution_values <- distribution_values;




		//----------------------------------------------------------------------------
		//Now create both the route and the stop, for the agent representation of them.
		//----------------------------------------------------------------------------


        // CREATE ROUTE FROM .SHP FILE
        create route from: file_401route with: [
            routename :: read("name"),
            distance :: int(read("distance")),
            id :: int(read("id"))	
        ];
        
        
        
        
        // CREATE EACH STOP FROM .SHP FILE
        create stop from: file_401stops with: [
            stopName :: string(read("stopName")),
            stopNum :: int(read("stopNum")),
            distance :: int(read("distance")),
            name :: string(read("stopName")),
            stop_distributions:: distribution_values[int(read("stopNum"))],
            distribution_per_timeslot_boards::distribution_values[int(read("stopNum"))][5]["Boards"],
            distribution_per_timeslot_dropoffs::distribution_values[int(read("stopNum"))][5]["DropOffs"]
        ];
        
        
        
        //SAVE TO GLOBAL LIST
        stops_list <- list(stop);
        
        

    }//END ACTION STATEMENT



		
		
//--------------------------------------------------------------------------------------------------------------------------------
//--------------------------------------------------------------------------------------------------------------------------------
//----------------------------------------------GLOBAL STATEMENTS-MOBILITY--------------------------------------------------------
//--------------------------------------------------------------------------------------------------------------------------------
//--------------------------------------------------------------------------------------------------------------------------------

		
		
		
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
       
       
       
        //DEBUG
        if (minutes = 0) {
            write "[DEBUG]: Now: " + current_time;
        }//End If
    
	}//End reflex update_time


	//Map the TimeSlot + minutes into a string, to compare with the input
	string current_time -> string(TimeSlot) + ":" + (minutes < 10 ? "0" + string(minutes) : string(minutes));	
	
	
	
	
	/*
	 * Reflex to handle the END of the sim once no bus is kept alive
	 */ 
	reflex end_real_simulation when: empty(bus){
		write "BUSES FINIQUITEN " + current_time;
        do pause;  //CHAO CHAO CHAO CHAO
	}



	
	/*
	 * Auxiliar global function to calculate the distance vector between the actual bus position and the next stop scheduled.
	 * It has for parameters the initial position of the bus, the goal destination and the speed module of the bus
	 * It first calulates the difference for each coordinate
	 * Then calculates the module of that resultant distance vector
	 * Consecuently, it refresh the value of the return_vector by multiplying the result calculated before with the relation
	 * between SPEED_MODULE/DISTANCE_MODULE
	 * Returns the 2 elem float vector to update the position of the bus
	 */
	list <float> vector_distance_calc(point bus_actual_position, point stop_reference, float speed_module) {
		
		
		//RESRVING THE VECTOR COMPONENT DECOMPOSITION TO THE RETURN TYPE
		list<float> return_vector <- [0.0,0.0];
		
		
		
		//CALC NEW DISTAMCE VECTOR
		return_vector[0] <- stop_reference.x - bus_actual_position.x;
		return_vector[1] <- stop_reference.y - bus_actual_position.y;
		
		//write "[DEBUG]: The resultant vector of distances is " + return_vector;
		
		
		
		//CALC THE MOD OF THE RESULTANT VECTOR
		float new_mod <- sqrt(return_vector[0]* return_vector[0] + return_vector[1] * return_vector[1]);
		
		
		/*READJUST TO MATCH MOD speed_module FOR THE BUS SPEED
		*
		* 
		*/
		
		if (new_mod = 0.0){
			return return_vector;
		}
		
		
			//CALC OF THE RELATION BETWEEN THE DISTANCE MOD AND THE SPEED MOD
		float relation <- speed_module / new_mod;
		
			//READJUST THE ELEMENTS OF THE VECTOR TO MATCH THE SCALE
		return_vector[0] <- return_vector[0] * relation;
		return_vector[1] <- return_vector[1] * relation;
		
		
		//RETURN
		return return_vector;
		
	}//END FUNCTION CALL vdc
	


	/* Auxiliar global function to verify if a bus is inside the "stop catching area". It establish the criteria that the 
	 * coordinates of the bus must be inside the +- 5 meters range from the stop coordinates
	 * 
	 * As parameters, the function takes the bus location and the reference stop coordinates.
	 * 
	 */
	bool is_inside_stop_range(point bus_actual_position, point stop_reference, float speed_module) {
		
		//CASE 1. THE COORDINATES MATCHES EXACTY
		if (bus_actual_position = stop_reference)
		{
			return true;
			
		}//END IF EQUAL MATCH
		
			
		//CASE INSIDE RANGE 5 MTRS ++
		list<float> distance_vector <- [0.0,0.0];
		
		
		
		//CALC DISTAMCE VECTOR
		distance_vector[0] <- stop_reference.x - bus_actual_position.x;
		distance_vector[1] <- stop_reference.y - bus_actual_position.y;
		

		//CALC THE MOD OF THE RESULTANT VECTOR
		float new_mod <- sqrt(distance_vector[0]* distance_vector[0] + distance_vector[1] * distance_vector[1]);
		
		
		//RN HARCODED, IF THE MODULE OF THE DISTANCE IS < 5. THE FUNCTION WOULD RETURN TRUE
		if (new_mod < speed_module)
		{
			return true;
		}
		
		return false;
		
	}//END FUNCTION CALL iisr
    





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
	
	
		
//--------------------------------------------------------------------------------------------------------------------------------
//--------------------------------------------------------------------------------------------------------------------------------
//------------------------------------------------------INIT MODULE---------------------------------------------------------------
//--------------------------------------------------------------------------------------------------------------------------------
//--------------------------------------------------------------------------------------------------------------------------------


    
    
    /*
     * Init function for main test. This firstly initialize the routes_loader model init, to read the geojson info in .shp 
     * format and generate the routes and the bus_stop agents. It saves the ordered bus info in a global list 
     * variable called stops_list
     * 
     * Then it creates a bus specie starting in the initial stop of the route and saving the goal destination, 
     * which hard codded rn is the final stop.
     */
    init 
    {
    	
    	//LOAD THE 401 ROUTE
    	do load_401;
			
		//Load the input bus departure scheduled times
		file input_bus_departures <- file("../includes/INPUTS/input_data_buses.txt");
		
		
		//Create one bus for each input departure parameter
		loop dep_time over: input_bus_departures {
			
						
			//CREATE THE BUS SPECIE WITH THE REQUIRED NECESSARY INFO
			create bus with:[
			departure_time :: dep_time,
    		initial_stop :: first(stops_list).stopName,
    		destination_stopname :: last(stops_list).stopName,
    		location :: first(stops_list).location,
    		makespan :: first(stop).distance,
    		location_goal :: last(stops_list).location
    		]; //END WITH
			
			
    	}//End loop input_buses_gateaways
    	

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
    
    
    //GOAL
    string destination_stopname;
    
    
    //COORDINATES GOAL
    point location_goal;
    
    
    //DEPARTURE TIME
    string departure_time;
    
    
    //Initially not allowed to leave until current_time == departure_time
    bool allowed_to_leave <- false;
     
    //DISTANCE MOVED
    int makespan;
    
    
    //INITIALLY NOT IN GOAL DESTINATION
    bool arrived <- false;
    
    
    //INITIALLY IN A BUS STOP
    bool stopped <- false;
    

    //MAX SPEED
    float speed_module_vector <- 60.00;
    
    
    //NUMBER OF STOPS REACHED, FOR THE INDEX. INITIALLY 0, to board the first passengers from the stop
    int stops_reached <- 0;
    
    
    
    //LIST OF PASSENGERS LOADED
    list<passenger> passengers;
    
    //NUMBER OF PASSENGERS LOADED.
    int passengers_length <- length(self.passengers);
    
    //BOOL VARIABLE TO DEFINE WHETHER OR NOT THE AGENT IS MOUNTING PASSENGERS
    bool processing_passengers <- false;
    
    
    //AUXILIAR VARIABLE TO PROCESS THE PASSENGERS
    int passengers_to_process;
    
    
    //All buses have the same maximum capacity 
    int max_passengers <- 80;
    
    
    //Seatable capacity
    int seatable_capacity <- 28;
    
    
    //To wait for the acceptance of the proposals
    bool waiting <- false;
    
    
    
    //DEFAULT ASPECT FOR THE GUI EXPERIMENT
    aspect default {
        if (self.stopped) 
        {
        	//SI ESTA PARADO, SE COLOREA EN ROJO
        	draw square(100) color: #orange;	
        	
        }//END IF ASPECT DEF
        else
        {
        	//SI ESTA EN MOVIMIENTO SE COLOREA EN VERDE
        	draw square(100) color: #green;
	        draw string(passengers_length) color: #black size: 1 at: location + {0, -80};
        	
        	
        }//END ELSE ASPECT DEF
        
    }//END ASPECT DEF
    
   
	/*
     * Reflex function to handle the abstraction not allowing the bus to leave
     * Until the departure_time is set.
     */
   
    reflex start_movements when: (allowed_to_leave = false)
    { 
	    
		//Check and compare if the bus can leave
    	if (departure_time = world.current_time)
    	{
    		allowed_to_leave <- true;
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
    reflex move_to_destination when: (arrived = false and stopped = false and allowed_to_leave = true) 
    {
    

	    //INVOICE THE CALCULATION OF THE MOVEMENT OF THE BUS
		list<float> new_point <- world.vector_distance_calc(self.location,
										stops_list[self.stops_reached].location, self.speed_module_vector);
	
		
		//UPDATE THE MOVEMENT
		self.location <- self.location + {new_point[0], new_point[1]};
		
		
		//CHECK ARRIVAL TO STOP
		
		if (world.is_inside_stop_range(self.location, stops_list[self.stops_reached].location, self.speed_module_vector) = true)
		{
			//IF THE FUNCTION ENTERS HERE, IT MEANS A STOP HAS BEEN REACHED
			
			
			//FIRST, CHECK IF ITS THE GOAL DESTINATION
			if (world.is_inside_stop_range(self.location, self.location_goal, self.speed_module_vector) = true)
			{
				
			//THIS MEANS THE TARGET HAS BEEN REACHED
			self.arrived <- true;
			
			
			
			loop passenger_to_dropoff over: self.passengers{
				do start_conversation to: [passenger_to_dropoff] protocol: 'fipa-request' performative: 'request' contents: ['Drop Off'];
			}
			
			
			do die;//NOW THE AGENT DIES, LATER TODO THE BUS WILL BE LOGICAL BUS AND WILL START ITS RETURN AS TIME SCHEDULED.
			
			
			}//END IF GOAL DESTINATION
			
			
			//IF IT REACES HERE, NO GOAL DESTINATION YET, BUT STILL IN A STOP, SO IT COMUNICATES 
			//WITH THE STOP AGENT WITH THE ACTION HANDLE_STOP
						
			//BOOL VARIABLE TO TRUE
			self.stopped <- true;
			

		}//END IF STOP REACHED


    }//END REFLEX mtd




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
    	do start_conversation to: [stops_list[self.stops_reached]] protocol: 'fipa-query' performative: 'query' contents: ['Bus arrived to stop'];
		
		
		//THIS LINE IS JUST FOR THE BUS IN THE NEXT CYCLE NOT REPEATING THE SENDING MESSAGE
		self.processing_passengers <- true;
		

    }//END REFLEX hs
    
    
    
    
    
    /*
     * Reflex function to handle the abstraction of charging/discharging passengers in the bus.
     * First, it discharges the number of passengers that the stop tells the bus to dischargeº
     * Process of mounting passengers has begun,it will comunicate with the passengers in the bus via FIPA protocol
     * Once every passenger has been processed, the self. variables to move to the next stop reactivates.
     */
	reflex handle_answer when: !(empty(informs))
	{
	    message answer <- informs at 0;
	    	    
	    
	    list<passenger> received_passengers <- list(answer.contents)[0];
		
		int passengers_to_pop <- int(list(answer.contents)[1]);
		
		
		//If the number to drop is lower than the number of passengers on the bus and that number is not 0, drop those passengers
		if (passengers_to_pop <= self.passengers_length and self.passengers_length != 0 and passengers_to_pop != 0){
			
			loop i from: 0 to: (passengers_to_pop -1){
				
				do start_conversation to: [self.passengers[0]] protocol: 'fipa-request' performative: 'request' contents: ['Drop Off'];
				
				remove index: 0 from: self.passengers;
			}
			
			self.passengers_length <- length(self.passengers);
		}
		
		/*
		 * Local variable to know how many passengers from the stop the bus can process. Later on, the bus will inform the stop the value of
		 * number_of_boards, so the stop removes those passengers from its queue
		 */
		int number_of_boards <- 0;
		
		
	    loop one_passenger over: received_passengers {
	        if (self.passengers_length < max_passengers) {
                do start_conversation to: [one_passenger] protocol: 'fipa-request' performative: 'request' contents: ['Mount'];
	            self.passengers << one_passenger;
	            self.passengers_length <- length(self.passengers);
	            number_of_boards +<- 1;
			}
	        else {
                do start_conversation to: [one_passenger] protocol: 'fipa-request' performative: 'request' contents: ['Bus full'];
	        }//End if bus full
	    }
	    
	    //Answer back to the stop the number of passengers picked up by the bus agent
	    do start_conversation to: [stops_list[self.stops_reached]] protocol: 'fipa-inform' performative: 'inform' contents: [number_of_boards];
		
		//self variable to handle the acceptance of the messages from the passengers.
	    self.waiting <- true;
	    
	    
	}//END REFLEX handle answer
  
  	/*
  	 * Reflex function to, in the saame loop the passengers are processing the information 
  	 * from the bus, change the variables that control the movement
  	 */
  	reflex wait_for_acceptance when: (self.waiting = true and empty(accept_proposals)) {
	    self.waiting <- false;
	    self.processing_passengers <- false;
	    self.stopped <- false;
	    self.stops_reached <- self.stops_reached + 1;
	}
  
    
}//END SPECIE BUS





/*
 *Definition of the type specie PASSENGER 
 * 
 * 
 * 
 * Skills fipa means that this agent inherit the FIPA communication protocol. Used to communicate between bus agents,
 * stops agents and this passengers agent
 * 
 */
species passenger skills: [fipa]
{
	
	//Stop code in which this passenger is generated
	int stop_origin;
	
	
	//Boolean to know when it is stopped or when it is on a bus. On starting it is False
	bool on_bus <- false;
	
	
	
	//Boolean to knwo wheter it is seated or no(Estimation based on the total number of seats in the bus). To measure KPIs of seatability
	bool seated;
	
	
	
	//Agent bus variable
	bus mounted_bus;
	
	
	
	//To measure KPIs of wait time
	float wait_time;

	
	//variable to know the mood of the passenger depending on the time waiting, if he can seat on the bus or if the bus its full
	string mood;
	
	
	//For drawing
	aspect default {
		
		if (self.on_bus = false){
			
			draw circle(50) color: #red;
		}
		else {
			
			draw circle(50) color: #yellow;
		}
		
		
	}//End aspcet DEF
	


	/*
	 * Reflex to handle the movement of the passenger. Initially will be in the stop, buth when the bus arrives, using FIPA it will pass the
	 * reference to the bus specie instance, so the passenger wont be calling global function vec_dist_calc which willbe a redundant call
	 */
	reflex update_movement when: self.on_bus = true {
		
		self.location <- mounted_bus.location;

	}//End reflex update_movement
	
	
	
	/*
	 * Reflex to handle the wait of the passenger in the stop. Every cicle the self.on_bus = false, it will add 10 seconds out of variable wait_time
	 * 
	 */
	reflex wait_on_stop when: self.on_bus = false {
		
		//Advance the wait time counter. This will not stop until a bus picks this passenger up
		wait_time <- wait_time + world.step;
		/*
		 * Each instance of passenger will be on a Specie Stop list variable. Once the bus reaches the stop, it will fetch the list via FIPA request
		 * And communicate with each passenger to offer board. So now, what the code does is, once the proposals is not empty, stablish comm with bus
		 */ 
		
	}//End reflex wait_on_stop
	
	
	reflex comm_with_bus when: (!(empty(requests)) and self.seated = false){
		
		message answer <- requests at 0;

		if (answer.contents = 'Mount'){
			self.seated <- true;
			self.mounted_bus <- answer.sender;
			self.on_bus <- true;
		}
	}
	
	
	reflex comm_to_dropoff when: (!(empty(requests)) and self.seated = true) {
		do die;	
	}
	
}//End Species Passenger






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
    
    
    //Variable which will contain the passengers that are waiting in the stop.
    list<passenger> passengers_list;
    
    
    //MAP CONTAINING THE DISTRIBUTIONS FOR THE DAY
    map<int, map<string,list>> stop_distributions;
    
    //VALUE FOR PASSENGER GENERATION RATIO
    float board_generation_ratio;
    
    //VAUE FOR THE NEXT GENERATIO RATIO
    float next_board_generation_ratio;
    
    
    //Value that serve as an accumulator for the passengers that are generated over the course of an hour.
    float passengers_to_be_generated <- 0.0;
    
    
    /*
     * List variables containing the info about the behaviour of boards and dropoffs for the stop.
     * Each TimeSlot, will be updated acording to the behaviour of that TS
     * The list params are always the same [ "DistrType", param1, param2]
     * Where DistrType RN is NORMAL, NEGATIVE BINOMIAL, GEOMETRIC
     */  	
    list distribution_per_timeslot_boards <- [];
    
    list distribution_per_timeslot_dropoffs <- [];
    
    list next_distribution_per_timeslot_boards <- [];
    
    list next_distribution_per_timeslot_dropoffs <- [];
    
    
    
    /*
     * List variable containing, for each iteration of the timeslot, the ratio of generation of passengers that has to be added
     * to fulfill the needs of the variable selected.
     */
    list<float> smooth_generated_data;
    
    //Pair of floats wich holds the parameters of the distributions
    pair<float, float> board_generator_variables;
    
    
    
    
    aspect default {
    	
        draw circle(50) color: #purple border: #black;
        draw stopName + " " + length(passengers_list) color: #black size: 1 at: location + {0, -80};
       	
    }
    
    
    
    aspect simple {
        draw shape color: #red;
    }
    
    
    
    
    /*
     * Reflex function to handle the change of the boards and dropoffs distribution every hour. So this will happen when mod(minutes, 60) == 0
     * Apart from that. Every distribution change, the sim will load the next params(distribution of TS +1) Unless last TS.
     * Then, it will recalculate, to smooth the transition between distributions. With the calculations done, instead of being the same value for
     * every iteration of the TS, it will create a function y = mx + n, which will have the same under the curve area. This, will imply that
     * in the course of a full TimeSlot, the result of the passengers created will be the same under the curve area as it would be with a constant
     * function, but smoothing the transition to the following value.
     * 
     * This behaviour is only for boards, for dropoffs, it will pick up a random value everytime a bus arrives.
     */
    reflex update_distributions when: (mod(world.minutes, 60) = 0 and mod(world.time, 60)= 0 ) {
		

		if (TimeSlot = 5){
			
			//Loading the distros
			distribution_per_timeslot_boards <- world.global_distribution_values[stopNum][TimeSlot]["Boards"];
			distribution_per_timeslot_dropoffs <- world.global_distribution_values[stopNum][TimeSlot]["DropOffs"];
			
			
			//Loading the following distros
			next_distribution_per_timeslot_boards <- world.global_distribution_values[stopNum][TimeSlot + 1]["Boards"];
			next_distribution_per_timeslot_dropoffs <- world.global_distribution_values[stopNum][TimeSlot + 1]["DropOffs"];
			
			
			
			//Infer the new and the following exact random values based on the distribution. JUST FOR BOARDS
			
			
			//Actual VAL
			if(distribution_per_timeslot_boards[0] = "NORMAL"){
				board_generation_ratio <- gauss(float(distribution_per_timeslot_boards[1]), float(distribution_per_timeslot_boards[2]));
			}
			if(distribution_per_timeslot_boards[0] = "NEGATIVE BINOMIAL"){
				board_generation_ratio <- float(world.sample_negative_binomial(float(distribution_per_timeslot_boards[1]),
					float(distribution_per_timeslot_boards[2])));			
			}
			if (distribution_per_timeslot_boards[0] = "GEOMETRICAL"){
				board_generation_ratio <- world.sample_geometric(float(distribution_per_timeslot_boards[1]));
			}
			if (distribution_per_timeslot_boards[0] = "NO DATA"){
				board_generation_ratio <- 0.0;
			}

		
			//Following VAL
			if(next_distribution_per_timeslot_boards[0] = "NORMAL"){
				next_board_generation_ratio <- gauss(float(next_distribution_per_timeslot_boards[1]), float(next_distribution_per_timeslot_boards[2]));
			}
			if(next_distribution_per_timeslot_boards[0] = "NEGATIVE BINOMIAL"){
				next_board_generation_ratio <- float(world.sample_negative_binomial(float(next_distribution_per_timeslot_boards[1]),
					float(next_distribution_per_timeslot_boards[2])));			
			}
			if (next_distribution_per_timeslot_boards[0] = "GEOMETRICAL"){
				next_board_generation_ratio <- world.sample_geometric(float(next_distribution_per_timeslot_boards[1]));
			}
			if (next_distribution_per_timeslot_boards[0] = "NO DATA"){
				next_board_generation_ratio <- 0.0;
			}

			
		}
		else if (TimeSlot < 23){
			
			//For Boards, the random value is actually infer already, because it was calc in the iteration before
			board_generation_ratio <- next_board_generation_ratio;
			
			
			//Loading the following distros
			next_distribution_per_timeslot_boards <- world.global_distribution_values[stopNum][TimeSlot + 1]["Boards"];
			next_distribution_per_timeslot_dropoffs <- world.global_distribution_values[stopNum][TimeSlot + 1]["DropOffs"];
			
			//Following VAL
			if(next_distribution_per_timeslot_boards[0] = "NORMAL"){
				next_board_generation_ratio <- gauss(float(next_distribution_per_timeslot_boards[1]), float(next_distribution_per_timeslot_boards[2]));
			}
			if(next_distribution_per_timeslot_boards[0] = "NEGATIVE BINOMIAL"){
				next_board_generation_ratio <- float(world.sample_negative_binomial(float(next_distribution_per_timeslot_boards[1]),
					float(next_distribution_per_timeslot_boards[2])));			
			}
			if (next_distribution_per_timeslot_boards[0] = "GEOMETRICAL"){
				next_board_generation_ratio <- world.sample_geometric(float(next_distribution_per_timeslot_boards[1]));
			}
			if (next_distribution_per_timeslot_boards[0] = "NO DATA"){
				next_board_generation_ratio <- 0.0;
			}
			
		}
		else{
			
			//Last TimeSlot, no next, but for no error will be 0.0
			board_generation_ratio <- next_board_generation_ratio;
			next_board_generation_ratio <- 0.0;
		}//End Ifs Cases Timeslot
		
	/*
	 * After this loop, board will contain the value of the random choice selected and next too.
	 * Now apply trigonometric formulas to be able to smooth down the transitions
	 */
	
	//obtain the value in wich you will generate passengers
	smooth_generated_data <- world.smooth_data_function(board_generation_ratio, next_board_generation_ratio);


    }//End reflex Update Distributions
    
    
    /*
     * Reflex to handle the abstraction of generating passengers Each iteration, the needed value has to be added.
     * When a truncate to int generates a positive result, generate that number of passengers and
     * substract the number generated
     */
     reflex generate_passengers {
     	//add the value for this iteration			
		passengers_to_be_generated <- passengers_to_be_generated + smooth_generated_data[int(mod(world.time, 3600) / step)];
		
		
		int to_generate <- int(passengers_to_be_generated);
		
		
	    if (to_generate > 0) {
	        // Generate that number of passengers
	        create passenger number: to_generate with: [
	            stop_origin :: self.stopNum,
	            location :: self.location
	        ] returns: new_passengers;

    		passengers_list <- passengers_list + new_passengers;
	
	        // Subtract only the integer part, keep the fractional remainder
	        passengers_to_be_generated <- passengers_to_be_generated - to_generate;
	    	}//End if to_generate
	    	
    	}//End reflex generate passengers
    
     
    

    
    
    /*
     * Reflex function to handle the comms between this agent and the requesting agents
     * 
     * It simply reads the message metadata and answer back with the number of passengers rn in the stop
     * 
     */
    reflex communicate_with_bus when: !(empty(queries)) 
    {
    	
    	//CHECK OUT THE RECEIVING MESSAGE
		message queryFromInitiator <- queries at 0;
		
		
		//Infer the number of passengers that are gonna drop off 
		int dropoff_passengers;
		
		if (distribution_per_timeslot_dropoffs[0] = "NORMAL"){
			
			dropoff_passengers <- max(floor(gauss(float(distribution_per_timeslot_dropoffs[1]),
												float(distribution_per_timeslot_dropoffs[2]))), 0);
			
		}
		if (distribution_per_timeslot_dropoffs[0] = "NEGATIVE BINOMIAL"){
			
			dropoff_passengers <- max(floor(world.sample_negative_binomial(float(distribution_per_timeslot_dropoffs[1]),
												float(distribution_per_timeslot_dropoffs[2]))), 0);
			
		}
		if (distribution_per_timeslot_dropoffs[0] = "GEOMETRICAL"){
			
			dropoff_passengers <- max(floor(world.sample_geometric(float(distribution_per_timeslot_dropoffs[1]))), 0);
			
		}
		
		if (distribution_per_timeslot_dropoffs[0] = "NO DATA"){
			
			dropoff_passengers <- 0;
		}
		
		
		//ANSWER BACK WITH FIPA PROTOCOL QUERY
		do agree message: queryFromInitiator contents: ["Ok copy"];
		do inform message: queryFromInitiator contents: [self.passengers_list, dropoff_passengers];		
		
		self.passengers_list <- [];
		
    }//END REFLEX cwb
    
    
    
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
          	species passenger aspect: default;
          
          	//RENDER THE BUS SPECIE
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
            }
            
        }//END DISPLAY

    }//END OUTPUT
    

}//END EXPERIMENT
