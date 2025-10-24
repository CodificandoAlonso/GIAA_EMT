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
	
	
	
    file file_402route <- file("../includes/ROUTE/402route_toA.shp");
    file file_402stops <- file("../includes/STOPS/402stopsclean_toA.shp");
    
    
    //ADAPT THE SCALE TO MATCH THE 402 RESOLUTION
    geometry shape <- envelope(file_402route);

    
    
    
    
    
    /*
     * 
     * 
     * 
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
            name :: string(read("stopName"))
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
 * 
 * 
 * 
 * 
 * 
 * 
 * 
 * 
 */
species stop {
	
	//NAME OF THE STOP
    string stopName;
    
    //STOP CODE
    int stopNum;
    
    //DISTANCE FROM ORIGIN
    int distance;
    
    
    
    aspect default {
        draw circle(50) color: #purple border: #black;
        draw stopName color: #black size: 1 at: location + {0, -80};
    }
    
    
    
    aspect simple {
        draw shape color: #red;
    }
}




/*
 * 
 * 
 * 
 * 
 * 
 * 
 * 
 */
species route {
    string routename;
    int distance;
    int id;
    
    aspect default {
        draw shape color: #blue width: 3;
    }
}
