/* Disposable atomic generation bootstrap. No external PID acquisition fallback. */
#include "protocol.h"
#include <linux/sched.h>
#include <signal.h>
#include <sys/random.h>
#include <sys/wait.h>
static int child_anchor=-1;
static pid_t spawn(char *const args[]){
    struct clone_args c={.flags=CLONE_PIDFD,.pidfd=(unsigned long)&child_anchor,.exit_signal=SIGCHLD};
    long p=syscall(SYS_clone3,&c,sizeof(c));if(p<0){perror("clone3 required");exit(77);}if(!p){execv(args[0],args);perror("execv");_exit(70);}return (pid_t)p;
}
int main(void){
    test_context ctx;int in=open("/usr/local/fixture-context.bin",O_RDONLY);if(in<0||read(in,&ctx,sizeof(ctx))!=(ssize_t)sizeof(ctx))return 70;close(in);
    if(getrandom(ctx.epoch,32,0)!=32)return 70;
    int mem=syscall(SYS_memfd_create,"flooow-test-boot",MFD_ALLOW_SEALING);if(mem<0||write(mem,&ctx,sizeof(ctx))!=(ssize_t)sizeof(ctx)||fcntl(mem,F_ADD_SEALS,F_SEAL_WRITE|F_SEAL_GROW|F_SEAL_SHRINK|F_SEAL_SEAL))return 70;
    int channel[2];if(socketpair(AF_UNIX,SOCK_SEQPACKET,0,channel))return 70;
    char fdtext[24],ctext[24];snprintf(fdtext,sizeof(fdtext),"%d",mem);snprintf(ctext,sizeof(ctext),"%d",channel[1]);
    int supervisor_anchor=syscall(SYS_pidfd_open,getpid(),0);if(supervisor_anchor<0||fcntl(supervisor_anchor,F_SETFD,0))return 70;char stext[24];snprintf(stext,sizeof(stext),"%d",supervisor_anchor);
    char *receiver_args[]={"/usr/local/bin/flooow-test-receiver",ctext,fdtext,stext,NULL};pid_t receiver=spawn(receiver_args);int receiver_fd=child_anchor;
    fcntl(receiver_fd,F_SETFD,0);close(channel[1]);
    char rtext[24];snprintf(rtext,sizeof(rtext),"%d",receiver_fd);setenv("FLOOOW_TEST_BOOT_FD",fdtext,1);setenv("FLOOOW_TEST_RECEIVER_FD",rtext,1);
    char *pg_args[]={"/usr/lib/postgresql/18/bin/postgres","-D","/tmp/pgdata","-c","shared_preload_libraries=/usr/local/lib/flooow_test_login","-c","unix_socket_directories=/tmp/pgsock","-c","listen_addresses=","-c","log_min_messages=log",NULL};
    pid_t pg=spawn(pg_args);int pgfd=child_anchor;
    unsigned char marker=0xa1;if(!send_anchor(channel[0],&marker,1,pgfd))return 70;
    setvbuf(stdout,NULL,_IOLBF,0);printf("{\"event\":\"supervisor_started\",\"receiver_child\":%d,\"postmaster_child\":%d,\"generation_source\":\"atomic_pidfd_children\"}\n",receiver,pg);
    struct pollfd p[2]={{receiver_fd,POLLIN,0},{pgfd,POLLIN,0}};
    while(poll(p,2,20)==0){
        if(access(TEST_DIR "/crash-supervisor",F_OK)==0)_exit(86);
        if(access(TEST_DIR "/kill-receiver",F_OK)==0){syscall(SYS_pidfd_send_signal,receiver_fd,SIGTERM,NULL,0);break;}
    }
    /* Only retained kernel objects select test targets. SIGTERM no numeric kill. */
    printf("{\"event\":\"supervisor_generation_loss\",\"receiver_dead\":%s,\"postmaster_dead\":%s}\n",alive(receiver_fd)?"false":"true",alive(pgfd)?"false":"true");
    /* Fast PG stop is a coarse disposable drain, NOT full watchdog qualification. */
    if(alive(pgfd))syscall(SYS_pidfd_send_signal,pgfd,SIGINT,NULL,0);
    if(alive(receiver_fd))syscall(SYS_pidfd_send_signal,receiver_fd,SIGTERM,NULL,0);
    close(channel[0]);int s;waitpid(pg,&s,0);waitpid(receiver,&s,0);close(pgfd);close(receiver_fd);close(mem);
    printf("{\"event\":\"supervisor_verified_child_drain\"}\n");return 0;
}
