#include "config.h"

#include <errno.h>
#include <stdio.h>
#include <string.h>
#include <sys/stat.h>
#include <sys/types.h>

/* mkdir -p, in-place on a mutable copy of the path */
int mkdir_p(const char *path) {
    char tmp[512];
    size_t len = strlen(path);
    if (len == 0 || len >= sizeof tmp) { errno = ENAMETOOLONG; return -1; }
    memcpy(tmp, path, len + 1);

    if (tmp[len - 1] == '/') tmp[len - 1] = '\0';

    for (char *p = tmp + 1; *p; p++) {
        if (*p != '/') continue;
        *p = '\0';
        if (mkdir(tmp, 0755) != 0 && errno != EEXIST) return -1;
        *p = '/';
    }
    if (mkdir(tmp, 0755) != 0 && errno != EEXIST) return -1;
    return 0;
}

int config_ensure_outdir(const char *path) {
    if (mkdir_p(path) != 0) {
        fprintf(stderr, "cannot create output dir '%s': %s\n",
                path, strerror(errno));
        return -1;
    }
    return 0;
}