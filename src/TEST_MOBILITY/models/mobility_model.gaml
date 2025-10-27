/**
* Name: mobilitymodel
* Bus route simulation to try out GAMA species and agents implementation
* Author: hectoralv22
*/




model mobility_model





import "routes_loader.gaml"



//--------------------------------------------------------------------------------------------------------------------------------
//--------------------------------------------------------------------------------------------------------------------------------
//-----------------------------------------------------GLOBAL_STATEMENT-----------------------------------------------------------
//--------------------------------------------------------------------------------------------------------------------------------
//--------------------------------------------------------------------------------------------------------------------------------



global 
{
	
	
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
		float relation <- 5.00 / new_mod;
		
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
		
		
		
		//RN HARCODED, IF THE MODULE OF THE DISTANCE IS < 2. THE FUNCTION WOULD RETURN TRUE
		list<float> distance_vector <- [0.0,0.0];
		
		
		
		//CALC DISTAMCE VECTOR
		distance_vector[0] <- stop_reference.x - bus_actual_position.x;
		distance_vector[1] <- stop_reference.y - bus_actual_position.y;
		
		
		
		
		//CALC THE MOD OF THE RESULTANT VECTOR
		float new_mod <- sqrt(distance_vector[0]* distance_vector[0] + distance_vector[1] * distance_vector[1]);
		
		
		if (new_mod < 5.00)
		{
			return true;
		}
		
		return false;
		
	}//END FUNCTION CALL iisr
    
    
    
    
    
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
    	
    	//LOAD THE 402 ROUTE
    	do load_402;

    	
    	
    	//CREATE THE BUS SPECIE WITH THE REQUIRED NECESSARY INFO
    	create bus with:[
    		initial_stop :: first(stops_list).stopName,
    		destination_stopname :: last(stops_list).stopName,
    		location :: first(stops_list).location,
    		makespan :: first(stop).distance,
    		location_goal :: last(stops_list).location,
    		passengers :: first(stops_list).passengers
    	]; //END WITH
        
        
        
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
    
     
    //DISTANCE MOVED
    int makespan;
    
    
    //INITIALLY NOT IN GOAL DESTINATION
    bool arrived <- false;
    
    
    //INITIALLY IN A BUS STOP
    bool stopped <- false;
    

    //MAX SPEED
    float speed_module_vector <- 5.00;
    
    
    //NUMBER OF STOPS REACHED, FOR THE INDEX. INITIALLY 1, AS THE BUS STARTS IN A STOP
    int stops_reached <- 1;
    
    
    
    //NUMBER OF PASSENGERS LOADED. INITIALLY ITS GONNA BE THE START STOP'S PASSENGERS
    int passengers;
    
    //BOOL VARIABLE TO DEFINE WHETHER OR NOT THE AGENT IS MOUNTING PASSENGERS
    bool processing_passengers <- false;
    
    
    //AUXILIAR VARIABLE TO PROCESS THE PASSENGERS
    int passengers_to_process;
    
    
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
     * Reflex function to handle the abstraction of moving the bus between stops.
     * 
     * It invoices auxiliary global functions to handle the movement and verify if the agent is in the area of acceptance
     * The area of acceptance is necesarry because the code is using float coordinates with very exact precision, 
     * so with module 5 vector speed,not always(mainly never) the coordinates will be the same, so a logical function 
     * to stablish certain minimum range is necesarry
     *
     * Once the agent has reached its destination, dies
     */
    reflex move_to_destination when: (arrived = false and stopped = false) 
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
			
			
			do die;
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
     	
     	
     	
     }//END REFLEX ha
  
    
    
}//END SPECIE BUS






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
            
        }//END DISPLAY

    }//END OUTPUT
    

}//END EXPERIMENT





