/**
* Name: mobilitymodel
* Bus route simulation to try out GAMA species and agents implementation
* Author: hectoralv22
*/




model mobility_model





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
		
	    float gamma_val <- gamma_rnd(r, (1-p)/p);
	    
	    int result <- poisson(gamma_val);
	    
	    return max(0, result);
	    
	}//End function sample_negative_binomial
    
    
    
    
    //GEOMETRICAL
    
    /*
     * As geometrical distribution is not implemented, using the inverse transform method, taking ln's
     */
	int sample_geometric(float p) {
		
    	float u <- rnd(0.0001, 0.9999);
    	
    	return int(floor(ln(u) / ln(1 - p)));
    	
	}//End function sample_geometric
     
     

    
    /*
     * Action module to be invoiced from other models .gaml
     *
     * 
     * This simply reads the files stops and routes (Both with .shp[shapefile] extension) and process all the agents
     * required to satisfy the content of the file
     * 
     */
    action load_401 {
        
      	
      	
      	write "LOADING THE MAP WITH ROUTES AND STOPS";
      	
      	
      	
      	//Read input for normal days distributions
      	file input_data_e01 <- csv_file("../includes/INPUTS/input_data_E01_toA.csv");
      	
      	//Convert it as matrix
      	matrix input_as_matrix <- matrix(input_data_e01);
      	
      	
      	
      	loop i from: 0 to: input_as_matrix.rows - 1 {
      		write "ROW  "+  " " + input_as_matrix[0, i]+  " " + input_as_matrix[1, i] +  " "+ input_as_matrix[2, i]+  " " + 
      		input_as_matrix[3, i]+  " " + input_as_matrix[4, i]+  " " + input_as_matrix[5, i];
      		
      	}
      	
		
		/*
		 * Loop to obtain all the stopNums and store the data from the stops related to that num
		 * The skeleton of the distribution map will be the following:
		 * Dictionary "VARNAME": {Key(StopNum): Value: Dict}
		 * Secondary Dict: {Key(TimeSlot: Value: Dict}
		 * Third Dict: {Key(Board): Value: ["DistrType", Param1, Param2], Key(DropOff): Value: ["DistrType", Param1, Param2]}
		 */
		loop stops_iter over: file_401stops {
			geometry point_iter <- stops_iter;
			map attr <- point_iter.attributes;
    		int stop_code <-int(attr["stopNum"]);
		}//TODO ACABAR TODO ESTOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOooo
		
      	
      	
      	
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
            passengers ::  one_of([5,14,19,26,41])//THIS WILL GET DELETED
        ];
        
        
        
        //SAVE TO GLOBAL LIST
        stops_list <- list(stop);
        
        

    }//END ACTION STATEMENT



		
		
//--------------------------------------------------------------------------------------------------------------------------------
//--------------------------------------------------------------------------------------------------------------------------------
//----------------------------------------------GLOBAL STATEMENTS-MOBILITY--------------------------------------------------------
//--------------------------------------------------------------------------------------------------------------------------------
//--------------------------------------------------------------------------------------------------------------------------------

		
		
		
		
	float step <- 30 #seconds;
	

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
		
		write "[DEBUG]: The resultant vector of distances is " + return_vector;
		
		
		
		//CALC THE MOD OF THE RESULTANT VECTOR
		float new_mod <- sqrt(return_vector[0]* return_vector[0] + return_vector[1] * return_vector[1]);
		
		
		/*READJUST TO MATCH MOD 5 FOR THE BUS SPEED
		*
		* 
		*/
		
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
	bool is_inside_stop_range(point bus_actual_position, point stop_reference) {
		
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
		if (new_mod < 5.00)
		{
			return true;
		}
		
		return false;
		
	}//END FUNCTION CALL iisr
    

		
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
    		location_goal :: last(stops_list).location,
    		passengers :: first(stops_list).passengers
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
    float speed_module_vector <- 10.00;
    
    
    //NUMBER OF STOPS REACHED, FOR THE INDEX. INITIALLY 1, AS THE BUS STARTS IN A STOP
    int stops_reached <- 1;
    
    
    
    //NUMBER OF PASSENGERS LOADED.
    int passengers;
    
    //BOOL VARIABLE TO DEFINE WHETHER OR NOT THE AGENT IS MOUNTING PASSENGERS
    bool processing_passengers <- false;
    
    
    //AUXILIAR VARIABLE TO PROCESS THE PASSENGERS
    int passengers_to_process;
    
    
    //All buses have the same maximum capacity 
    int max_passengers <- 80;
    
    
    //Seatable capacity
    int seatable_capacity <- 28;
    
    
    
    
    
    
    //DEFAULT ASPECT FOR THE GUI EXPERIMENT
    aspect default {
        if (self.stopped) 
        {
        	//SI ESTA PARADO, SE COLOREA EN ROJO
        	draw square(100) color: #red;	
        	
        }//END IF ASPECT DEF
        else
        {
        	//SI ESTA EN MOVIMIENTO SE COLOREA EN VERDE
        	draw square(100) color: #green;
        	
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
		
		if (world.is_inside_stop_range(self.location, stops_list[self.stops_reached].location) = true)
		{
			//IF THE FUNCTION ENTERS HERE, IT MEANS A STOP HAS BEEN REACHED
			
			
			//FIRST, CHECK IF ITS THE GOAL DESTINATION
			if (world.is_inside_stop_range(self.location, self.location_goal) = true)
			{
				
			//THIS MEANS THE TARGET HAS BEEN REACHED
			self.arrived <- true;
			
			
			do die;//NOW THE AGENT DIES, LATER TODO THE BUS WILL BE LOGICAL BUS AND WILL START ITS RETURN AS TIME SCHEDULED.
			
			
			}//END IF GOAL DESTINATION
			
			
			//IF IT REACES HERE, NO GOAL DESTINATION YET, BUT STILL IN A STOP, SO IT COMUNICATES 
			//WITH THE STOP AGENT WITH THE ACTION HANDLE_STOP
			
			write "[DEBUG]: " + "THE BUS ARRIVED TO THE STOP";
			
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
    	do start_conversation to: [stops_list[self.stops_reached]] protocol: 'fipa-propose' performative: 'propose' contents: ['Bus arrived to stop'];
		
		
		//THIS LINE IS JUST FOR THE BUS IN THE NEXT CYCLE NOT REPEATING THE SENDING MESSAGE
		self.processing_passengers <- true;
		

    }//END REFLEX hs
    
    
    
    
    
    /*
     * Reflex function to handle the abstraction of charging passengers in the bus
     *
     *It has 2 main cases. First up, if the message received has not yet being read, it reads its content, 
     * extract the passengers in that stop and save into a self variable
     *
     *The other case, when the process of mounting passengers has begun, once per cycle, it process one passenger.
     * 
     *Once every passenger has been processed, the self. variables to move to the next stop reactivates.
     */
     reflex handle_answer when: (self.processing_passengers = true or !(empty(accept_proposals)))
     {
     	
     	//CASE_0. The message has just been received. needs to be processed
     	if (!(empty(accept_proposals)))
     	{
     		//SAVE IT INTO A VARIABLE
     		message answer <- accept_proposals at 0;
     		
     		//CAST THE CONTENT INTO A LIST AND PICK UP THE FIRST ELEM(THE PASSENGERS IN THAT STOP RECEIVED
     		self.passengers_to_process <- list(answer.contents)[0];
     		
     		//BOOL FLAG TO START PROCESSING
     		self.processing_passengers <- true;
     		
     		
     	}//END IF
     	
     	else
     	{
     		//PROCESS PASSENGERS, CASE_1. THE MESSAGE HAS ALREADY BEEN READ.
     		self.passengers <- self.passengers + 1;
     		self.passengers_to_process <- self.passengers_to_process - 1;
     		
     		//DEBUG
     		write "[DEBUG]: " + "A passenger is being processed up";
     		
     		
     	}//END ELSE
     	
     	
     	//FINAL CASE. PROCESSING HAS BEEN ENDED
     	if (self.passengers_to_process = 0)
     	{
     		
     		
     		//CHANGE TO FALSE SO THE BUS MOVES IN THE NEXT CYCLE
    		self.stopped <- false;
    	
    	
			//UPDATE FOR THE INDEX OF THE NEXT STOP.
	    	self.stops_reached <- self.stops_reached +1;
	    	
	    	//STOP PROCESSING PASSENGERS
	    	self.processing_passengers <- false;
	    	
     	}
     	
     	
     	
     }//END REFLEX handle answer
  
    
    
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
    
    
    //HARCODED INVENTED NUMBER OF PASSENGERS. THIS WILL BE DELETEED
    int passengers;
    

    //list<passengers> passengers_list;
    
    
    
    
    //Pair of floats wich holds the parameters of the distributions
    pair<float, float> board_generator_variables;
    
    
    
    
    aspect default {
    	
        draw circle(50) color: #purple border: #black;
        draw stopName + " " + passengers color: #black size: 1 at: location + {0, -80};
       	
    }
    
    
    
    aspect simple {
        draw shape color: #red;
    }
    
    
    
    
    /*
     * Reflex function to handle the change of the boards and dropoffs distribution every hour. So this will happen when mod(minutes, 60) == 0
     */
    reflex update_distributions when: mod(world.minutes, 60) = 0 {



    }
    

    
    
    /*
     * Reflex function to handle the comms between this agent and the requesting agents
     * 
     * It simply reads the message metadata and answer back with the number of passengers rn in the stop
     * 
     */
    reflex communicate_with_bus when: !(empty(proposes)) 
    {
    	
    	//CHECK OUT THE RECEIVING MESSAGE
		message proposalFromInitiator <- proposes at 0;
		
		
		//ANSWER BACK WITH FIPA PROTOCOL ACCEPT_PROPOSAL
		do accept_proposal message: proposalFromInitiator contents: [self.passengers] ;
		
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
