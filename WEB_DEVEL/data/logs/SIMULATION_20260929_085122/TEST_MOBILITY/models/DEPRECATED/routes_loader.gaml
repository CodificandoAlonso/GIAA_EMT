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
    file file_401route <- file("../includes/ROUTE/E01/E01_toA.shp");
    file file_401stops <- file("../includes/STOPS/E01/E01_stops_toA.shp");
    
    file input_data_e01 <- csv_file("../includes/INPUTS/input_data_E01_toA.csv");
    
    
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
      	
      	
      	
      	matrix input_as_matrix <- matrix(input_data_e01);
      	
      	
      	
      	loop i from: 0 to: input_as_matrix.rows - 1 {
      		write "ROW  "+  " " + input_as_matrix[0, i]+  " " + input_as_matrix[1, i] +  " "+ input_as_matrix[2, i]+  " " + 
      		input_as_matrix[3, i]+  " " + input_as_matrix[4, i]+  " " + input_as_matrix[5, i];
      		
      	}
      	
      	
      	
      	
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
            passengers ::  one_of([5,14,19,26,41])
        ];
        
        
        
        //SAVE TO GLOBAL LIST
        stops_list <- list(stop);
        
        

    }//END ACTION STATEMENT
    
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
