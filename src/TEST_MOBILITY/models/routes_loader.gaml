/**
* Name: routes_loader
* Based on the internal skeleton template. 
* Author: hectoralv22
* Tags: 
*/

model routes_loader



//--------------------------------------------------------------------------------------------------------------------------------
//--------------------------------------------------------------------------------------------------------------------------------
//-----------------------------------------------------GLOBAL_STATEMENT-----------------------------------------------------------
//--------------------------------------------------------------------------------------------------------------------------------
//--------------------------------------------------------------------------------------------------------------------------------



global 
{
	
	//CREATE GLOBAL VARIABLES TO SAVE GLOBAL SCOPE OF THE AGENTS CREATED
	list <stop> stops_list;
	
	
	//INPUT FILES
    file file_402route <- file("../includes/ROUTE/402route_toA.shp");
    file file_402stops <- file("../includes/STOPS/402stopsclean_toA.shp");
    
    
    //ADAPT THE SCALE TO MATCH THE 402 RESOLUTION
    geometry shape <- envelope(file_402route);

    
    
    
    
    
    /*
     * Action module to be invoiced from other models .gaml
     *
     * 
     * This simply reads the files stops and routes (Both with .shp[shapefile] extension) and process all the agents
     * required to satisfy the content of the file
     * 
     */
    action load_402 {
        
      	
      	
      	write "LOADING THE MAP WITH ROUTES AND STOPS";
      	
      	
        // CREATE ROUTE FROM .SHP FILE
        create route from: file_402route with: [
            routename :: read("name"),
            distance :: int(read("distance")),
            id :: int(read("id"))	
        ];
        
        
        
        
        // CREATE EACH STOP FROM .SHP FILE
        create stop from: file_402stops with: [
            stopName :: string(read("stopName")),
            stopNum :: int(read("stopNum")),
            distance :: int(read("distance")),
            name :: string(read("stopName")),
            passengers ::  one_of([5,14,19,26,41])
        ];
        
        
        
        //SAVE TO GLOBAL LIST
        stops_list <- list(stop);
        
        

    }//END INIT STATEMENT
    
}//END GLOBAL_STATEMENT
		
		
		
//--------------------------------------------------------------------------------------------------------------------------------
//--------------------------------------------------------------------------------------------------------------------------------
//-----------------------------------------------------SPECIES_DEFINITION---------------------------------------------------------
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
    
    
    //HARCODED INVENTED NUMBER OF PASSENGERS
    int passengers;
    
    
    
    aspect default {
        draw circle(50) color: #purple border: #black;
        draw stopName + " " + passengers color: #black size: 1 at: location + {0, -80};
       	
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
		
		
		
		
		
		
		
