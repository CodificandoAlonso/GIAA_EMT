#include <iostream>
#include <fstream>
#include <cstring>
using namespace std;

int main(int argc, char **argv) {

    if( argc != 3) {
        cerr << "INCORRECT INPUT FORMAT. SHOULD BE ./EXECUTABLE INPUT OUTPUT\n";
        return -1;
    }

    char *input;
    char *output;

    auto counter_input = static_cast<int>(strlen(argv[1]));
    auto counter_output = static_cast<int>(strlen(argv[2]));

    input = static_cast<char *>(malloc(sizeof(char) * counter_input));
    output = static_cast< char *>(malloc(sizeof(char) * counter_output));


    memcpy(input, argv[1], sizeof(char) *  counter_input);
    memcpy(output, argv[2], sizeof(char) * counter_output);



    //Archivo entrada y comprobacion
    ifstream input_file(input,
                  ios::binary);
    if (!input_file)
    {
        cerr << "Falló apertura input file\n";
        free(input);
        free(output);
        return -1;
    }

    //Archivo salida y comprobacion
    ofstream output_file(output, ios::binary);
    if (!output_file)
    {
        cerr << "Fallo apertura output file\n";
        free(input);
        free(output);
        return -1;
    }



    const size_t maxBuf = 35 * 1024 * 1024;
    char* content = new char[maxBuf];
    input_file.read(content, maxBuf);
    const size_t bytesRead = input_file.gcount();
    input_file.close();





    //READ CONTENT. SKIP THE FIRST LINE, THEN EXCHANGE THE TABS WITH ;, TO MAKE IT A REAL CSV
    int first_line_skipped = 0;


    for (size_t iter = 0; iter < bytesRead; iter ++)
    {


        //Solo quiero procesar a partir de la segunda línea, asi que hasta no encontrar un \n no haré nada.

        if (first_line_skipped == 0)
        {
            if (content[iter] == '\n' )
            {
                first_line_skipped = 1;
            }
            else
            {
                continue;
            }
        }
        else
        {
            if (content[iter] == ' ' || content[iter] == '\t' )
            {
                content[iter] = ',';
            }
        }
    }
    output_file.write(content, static_cast<int>(bytesRead));

    delete[] content;
    free(input);
    free(output);
    return 0;
}
