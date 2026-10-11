/* Actual observer code; fabricated old catalog snapshot; owned atomic child. */
#define main observer_program_main
#include "observer.c"
#undef main
#include <linux/sched.h>
#include <sys/wait.h>
#include <assert.h>
int main(void){
    shared=calloc(1,sizeof(*shared));assert(shared);atomic_store(&shared->armed,1);
    int childfd=-1;struct clone_args args={.flags=CLONE_PIDFD,.pidfd=(uint64_t)&childfd,.exit_signal=SIGCHLD};
    pid_t child=syscall(SYS_clone3,&args,sizeof(args));assert(child>=0);
    if(!child){for(;;)pause();}
    request_fields identity={0};struct stat st;assert(!fstat(childfd,&st));
    count=1;anchors[0]=(retained){.fd=childfd,.pid=child,.r=identity};
    shared->entries[0].inode=st.st_ino;shared->entries[0].pid=child;shared->entries[0].request=identity;atomic_store(&shared->entries[0].phase,1);
    uint64_t captured=tick_us();PGresult *empty=PQmakeEmptyPGresult(NULL,PGRES_TUPLES_OK);assert(empty);
    struct timespec pause_before_promotion={0,1000000};nanosleep(&pause_before_promotion,NULL);
    assert(observation_registered(shared,childfd,&identity,1));
#ifdef FLOOOW_SNAPSHOT_BOUND
    census_snapshot_started=captured;
#else
    (void)captured;
#endif
    assert(observe(empty));
    wait_fd(childfd,POLLIN,tick_us()+1000000);
    int safe=alive(childfd)&&atomic_load(&shared->entries[0].phase)==2;
    printf("STALE_CENSUS_MUST_NOT_QUARANTINE_NEW_PROMOTION=%s\n",safe?"PASS":"FAIL");
    syscall(SYS_pidfd_send_signal,childfd,SIGTERM,NULL,0);syscall(SYS_pidfd_send_signal,childfd,SIGCONT,NULL,0);
    waitpid(child,NULL,0);close(childfd);PQclear(empty);free(shared);return safe?0:1;
}
