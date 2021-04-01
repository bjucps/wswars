#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdbool.h>

#include <unistd.h>
#include <sys/types.h>
#include <sys/file.h>
#include <pwd.h>

const char USERS_DB[] = "/home/cps250/wswars/users.txt";

char *getuname(uid_t userid) {
    struct passwd *pp = NULL;
    if ((pp = getpwuid(userid)) == NULL) {
        perror("unable to look up user");
        return NULL;
    }
    return strdup(pp->pw_name);
}

int main(int argc, char **argv) {
    int ret = 1;
    char *run_uname = NULL;
    char *ssh_ip = NULL;
    char hostname[256] = { 0 };
    FILE *db = NULL;
    bool locked = false;

    if (argc != 2) {
        fprintf(stderr, "Usage: register <handle>\n");
        goto cleanup;
    }

    char *handle = argv[1];

    if (gethostname(hostname, sizeof(hostname))) {
        perror("unable to see hostname");
        goto cleanup;
    }

    if (strcmp(hostname, "csunix.bju.edu") != 0) {
        fprintf(stderr, "Dude, you have to run this on CSUNIX...\n");
        goto cleanup;
    }

    if ((run_uname = getuname(getuid())) == NULL) {
        goto cleanup;
    }

    char *SSH_CLIENT = getenv("SSH_CLIENT");
    if (SSH_CLIENT == NULL) {
        fprintf(stderr, "You must run this program on CSUNIX via SSH.\n");
        goto cleanup;
    }
    char *ip_end = strchr(SSH_CLIENT, ' ');
    if (ip_end == NULL) {
        fprintf(stderr, "Whoa...  Trippy $SSH_CLIENT, bro!  But no cigar...\n");
        goto cleanup;
    }
    ssh_ip = strndup(SSH_CLIENT, ip_end - SSH_CLIENT);

    if ((db = fopen(USERS_DB, "r+")) == NULL) {
        perror("unable to open DB for reading/writing");
        goto cleanup;
    }

    if (flock(fileno(db), LOCK_EX)) {
        perror("unable to lock database file");
        goto cleanup;
    }
    locked = true;

    char db_user[32], db_ip[32], db_handle[32];
    bool found = false;
    while (fscanf(db, "%31s %31s %31s ", db_user, db_ip, db_handle) == 3) {
        if (strcmp(db_user, run_uname) == 0) {
            found = true;
            if (strcmp(db_ip, ssh_ip) != 0) {
                fprintf(stderr, "Already registered at IP %s; go ask the instructor for help...\n", db_ip);
            } else {
                fprintf(stderr, "You're already registered at this IP.  Have a nice day!\n");
            }
            goto cleanup;
        }
        if (strcmp(db_user, run_uname) != 0 && strcmp(db_ip, ssh_ip) == 0) {
            fprintf(stderr, "Someone else is already registered at IP %s; go ask the instructor for help...\n", db_ip);
            goto cleanup;
        } 
        if (strcmp(db_handle, handle) == 0) {
            fprintf(stderr, "Someone else already has that handle. Pick another one.\n");
            goto cleanup;
        }
    }

    fprintf(db, "%s %s %s\n", run_uname, ssh_ip, handle);

    puts(ssh_ip);

    ret = 0;
cleanup:
    if (db) { 
        fflush(db);
        if (locked) { flock(fileno(db), LOCK_UN); }
        fclose(db); 
    }
    free(ssh_ip);
    free(run_uname);
    return ret;
}

