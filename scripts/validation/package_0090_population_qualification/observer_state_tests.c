/* Test-only unit fixture: fabricated catalog rows, no process signaling. */
#define main observer_program_main
#include "observer.c"
#undef main
#include <assert.h>
int main(void){
    shared=calloc(1,sizeof(*shared));assert(shared);
    sup=syscall(SYS_pidfd_open,getpid(),0);receiver=dup(sup);pm=dup(sup);assert(sup>=0&&receiver>=0&&pm>=0);capture_census_context();
    PGresult *rows=PQmakeEmptyPGresult(NULL,PGRES_TUPLES_OK);assert(rows);
    PGresAttDesc fields[8]={0};
    for(int i=0;i<8;i++){fields[i].name="fixture";fields[i].typid=25;fields[i].typlen=-1;}
    assert(PQsetResultAttrs(rows,8,fields));
    for(int i=0;i<129;i++){
        char pid[24];snprintf(pid,sizeof(pid),"%d",1000+i);
        const char *values[8]={pid,"100","200","300","400","test_fixture","client backend","t"};
        for(int j=0;j<8;j++)assert(PQsetvalue(rows,i,j,(char *)values[j],strlen(values[j])));
    }
    assert(!observe(rows));assert(unknown_n==128&&unknown_overflow);
    PQclear(rows);rows=PQmakeEmptyPGresult(NULL,PGRES_TUPLES_OK);assert(rows);
    capture_census_context();assert(observe(rows)==1);assert(unknown_overflow&&atomic_load(&shared->quarantined));
    assert(!atomic_load(&shared->outcome_confirmed));
    PQclear(rows);close(sup);close(receiver);close(pm);free(shared);
    puts("OBSERVER_CAPACITY_OVERFLOW_LATCH_PERSISTS=PASS");return 0;
}
