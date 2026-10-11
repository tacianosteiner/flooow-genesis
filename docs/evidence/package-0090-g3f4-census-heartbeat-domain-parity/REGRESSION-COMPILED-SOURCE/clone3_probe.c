/* Disposable qualification prerequisite. No externally observed PID fallback. */
#ifndef _GNU_SOURCE
#define _GNU_SOURCE
#endif
#include <errno.h>
#include <linux/sched.h>
#include <signal.h>
#include <stdio.h>
#include <sys/syscall.h>
#include <sys/wait.h>
#include <unistd.h>
int main(void) {
    int anchor=-1, status=0;
    struct clone_args args={.flags=CLONE_PIDFD,.pidfd=(unsigned long)&anchor,.exit_signal=SIGCHLD};
    long child=syscall(SYS_clone3,&args,sizeof(args));
    if(child<0){printf("{\"clone3\":\"DENIED\",\"errno\":%d,\"fallback\":false}\n",errno);return 77;}
    if(!child)_exit(0);
    if(anchor<0 || waitpid((pid_t)child,&status,0)<0)return 70;
    printf("{\"clone3\":\"PASS\",\"atomic_child_pidfd\":true,\"child_exit\":%d}\n",WEXITSTATUS(status));
    close(anchor);return 0;
}
