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
	 * Returns the 2 float vector to update the position of the bus
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
	 * To verify the catching aceptation area, the function must convert the EPGS type coordinates to meters or vice versa
	 * 
	 * Theoretically, 
	 * 
	 * 
	 */
	bool is_inside_stop_range(point bus_actual_position, point stop_reference) {
		
		//CASE 1. THE COORDINATES MATCHES EXACTY
		if (bus_actual_position = stop_reference){
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
		
		
		if (new_mod < 2.00)
		{
			return true;
		}
		
		return false;
		
	}//END FUNCTION CALL iisr
    
    
    
    
    
    /*
     * Init function for main test. This firstly initialize the routes_loader model init, to read the geojson info in .shp format
     * and generate the routes and the bus_stop agents. It saves the ordered bus info in a global list variable called stops_list
     * 
     * Then it creates a bus specie starting in the initial stop of the route and saving the goal destination, which hard codded rn
     * is the final stop.
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
    		location_goal :: last(stops_list).location
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
 * 
 */
species bus {
	
	
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
     * 
     * 
     *
     * 
     * 
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
			
			
			//IF IT REACES HERE, NO GOAL DESTINATION YET, BUT STILL IN A STOP, SO IT COMUNICATES WITH THE STOP AGENT WITH THE
			//ACTION HANDLE_STOP
			
			write "[DEBUG]: " + "THE BUS ARRIVED TO THE STOP";
			
			//BOOL VARIABLE TO TRUE
			self.stopped <- true;
			
			
			
			
		}//END IF STOP REACHED


    }//END REFLEX mtd




    /*
     * 
     *
     *
     *
     *
     *
     */
    reflex handle_stop when: (stopped = true)
    {
    	
    	//LOGIC TO COMMUNICATE WITH THE AGENT STOP WHICH IS IN
    	
    	
    	
    	
    	
    	//CHANGE TO FALSE SO THE BUS MOVES IN THE NEXT CYCLE
    	self.stopped <- false;
    	
    	
		//UPDATE FOR THE INDEX OF THE NEXT STOP.
    	self.stops_reached <- self.stops_reached +1;
    	
    	
    }//END REFLEX hs
    
  
    
    
}//END SPECIE BUS






/*
 * 
 * 
 * 
 * 
 * 
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





