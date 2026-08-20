#include <stdio.h>
#include <stdlib.h>

#include "io/txt_parser.h"

int main(void)
{
    const stops_list *stops = load_stops("data/input_stops.txt");

    if (!stops) {
        fprintf(stderr, "Failed to load stops\n");
        return EXIT_FAILURE;
    }

    printf("Direction A:\n");

    for (size_t i = 0; i < MAX_DIRECTION_LEN; i++) {
        if (stops->stopcode[0][i] == 0)
            break;

        printf("%hu", stops->stopcode[0][i]);

        if (i + 1 < MAX_DIRECTION_LEN &&
            stops->stopcode[0][i + 1] != 0)
            printf(",");
    }

    printf("\n\nDirection B:\n");

    for (size_t i = 0; i < MAX_DIRECTION_LEN; i++) {
        if (stops->stopcode[1][i] == 0)
            break;

        printf("%hu", stops->stopcode[1][i]);

        if (i + 1 < MAX_DIRECTION_LEN &&
            stops->stopcode[1][i + 1] != 0)
            printf(",");
    }

    printf("\n");

    free((void *)stops);

    return EXIT_SUCCESS;
}