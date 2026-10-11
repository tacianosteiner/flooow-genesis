/* Disposable atomic generation bootstrap. No external PID acquisition fallback. */
#include "protocol.h"
#include <linux/sched.h>
#include <signal.h>
#include <sys/random.h>
#include <sys/wait.h>
#include "heartbeat.h"
#include "quarantine.h"
static int child_anchor=-1;
static pid_t spawn(char *const args[],int close_fd){
    struct clone_args c={.flags=CLONE_PIDFD,.pidfd=(unsigned long)&child_anchor,.exit_signal=SIGCHLD};
    long p=syscall(SYS_clone3,&c,sizeof(c));if(p<0){perror("clone3 required");exit(77);}if(!p){if(close_fd>=0)close(close_fd);execv(args[0],args);perror("execv");_exit(70);}return (pid_t)p;
}
int main(void){
    test_context ctx;int in=open("/usr/local/fixture-context.bin",O_RDONLY);if(in<0||read(in,&ctx,sizeof(ctx))!=(ssize_t)sizeof(ctx))return 70;close(in);
    if(getrandom(ctx.epoch,32,0)!=32)return 70;
    int statefd=syscall(SYS_memfd_create,"flooow-test-observation",0);if(statefd<0||ftruncate(statefd,sizeof(observation_state)))return 70;
    observation_state *observed=observation_map(statefd,1);if(!observed)return 70;memset(observed,0,sizeof(*observed));char state_text[24];snprintf(state_text,sizeof(state_text),"%d",statefd);
    int mem=syscall(SYS_memfd_create,"flooow-test-boot",MFD_ALLOW_SEALING);if(mem<0||write(mem,&ctx,sizeof(ctx))!=(ssize_t)sizeof(ctx)||fcntl(mem,F_ADD_SEALS,F_SEAL_WRITE|F_SEAL_GROW|F_SEAL_SHRINK|F_SEAL_SEAL))return 70;
    int channel[2];if(socketpair(AF_UNIX,SOCK_SEQPACKET,0,channel))return 70;
    char fdtext[24],ctext[24];snprintf(fdtext,sizeof(fdtext),"%d",mem);snprintf(ctext,sizeof(ctext),"%d",channel[1]);
    int supervisor_anchor=syscall(SYS_pidfd_open,getpid(),0);if(supervisor_anchor<0||fcntl(supervisor_anchor,F_SETFD,0))return 70;char stext[24];snprintf(stext,sizeof(stext),"%d",supervisor_anchor);
    char *receiver_args[]={"/usr/local/bin/flooow-test-receiver",ctext,fdtext,stext,state_text,"-1",NULL};pid_t receiver=spawn(receiver_args,channel[0]);int receiver_fd=child_anchor;
    fcntl(receiver_fd,F_SETFD,0);close(channel[1]);
    char rtext[24];snprintf(rtext,sizeof(rtext),"%d",receiver_fd);setenv("FLOOOW_TEST_BOOT_FD",fdtext,1);setenv("FLOOOW_TEST_RECEIVER_FD",rtext,1);
    int observer_channel[2];if(socketpair(AF_UNIX,SOCK_SEQPACKET,0,observer_channel))return 70;char octext[24];snprintf(octext,sizeof(octext),"%d",observer_channel[1]);
    char *observer_args[]={"/usr/local/bin/flooow-test-observer",octext,fdtext,stext,rtext,state_text,"-1",NULL};pid_t observer=spawn(observer_args,observer_channel[0]);int observer_fd=child_anchor;fcntl(observer_fd,F_SETFD,0);close(observer_channel[1]);
    char otext[24];snprintf(otext,sizeof(otext),"%d",observer_fd);setenv("FLOOOW_TEST_OBSERVER_FD",otext,1);setenv("FLOOOW_TEST_OBSERVATION_FD",state_text,1);
    setenv("FLOOOW_TEST_SUPERVISOR_FD",stext,1);
    char *pg_args[]={"/usr/lib/postgresql/18/bin/postgres","-D","/tmp/pgdata","-c","shared_preload_libraries=/usr/local/lib/flooow_test_login","-c","unix_socket_directories=/tmp/pgsock","-c","listen_addresses=","-c","log_min_messages=log",NULL};
    pid_t pg=spawn(pg_args,channel[0]);int pgfd=child_anchor;
    unsigned char marker=0xa1;if(!send_anchor(channel[0],&marker,1,pgfd))return 70;
    if(!send_anchor(observer_channel[0],&marker,1,pgfd))return 70;marker=0xa2;if(!send_anchor(channel[0],&marker,1,observer_fd))return 70;
    setvbuf(stdout,NULL,_IOLBF,0);printf("{\"event\":\"supervisor_started\",\"receiver_child\":%d,\"postmaster_child\":%d,\"generation_source\":\"atomic_pidfd_children\"}\n",receiver,pg);
    if(!progress_enable(channel[0]))return 70;
    uint64_t last_progress=0,first_progress_deadline=tick_us()+10000000;
    struct pollfd p[2]={{receiver_fd,POLLIN,0},{pgfd,POLLIN,0}};
    while(poll(p,2,20)==0){
        atomic_store(&observed->supervisor_progress,tick_us());
        uint64_t observer_stamp=atomic_load(&observed->observer_progress);
        if(!alive(observer_fd)||(observer_stamp?tick_us()-observer_stamp>10000000:tick_us()>first_progress_deadline)){
            atomic_store(&observed->quarantined,1);printf("{\"event\":\"observer_progress_lost\"}\n");break;}
        if(access(TEST_DIR "/stall-receiver",F_OK)==0){unlink(TEST_DIR "/stall-receiver");syscall(SYS_pidfd_send_signal,receiver_fd,SIGSTOP,NULL,0);}
        if(progress_send(channel[0],0xb1)<0){printf("{\"event\":\"receiver_progress_lost\",\"reason\":\"communication_lost\",\"at_us\":%llu}\n",(unsigned long long)tick_us());break;}
        int progress;while((progress=progress_receive(channel[0],receiver_fd,0xb2,&last_progress))==1){}
        if(progress<0||(!last_progress?tick_us()>first_progress_deadline:tick_us()-last_progress>10000000)){printf("{\"event\":\"receiver_progress_lost\",\"at_us\":%llu}\n",(unsigned long long)tick_us());break;}
        if(access(TEST_DIR "/crash-supervisor",F_OK)==0)_exit(86);
        if(access(TEST_DIR "/kill-receiver",F_OK)==0){syscall(SYS_pidfd_send_signal,receiver_fd,SIGTERM,NULL,0);break;}
    }
    /* Only retained kernel objects select test targets. SIGTERM no numeric kill. */
    printf("{\"event\":\"supervisor_generation_loss\",\"receiver_dead\":%s,\"postmaster_dead\":%s}\n",alive(receiver_fd)?"false":"true",alive(pgfd)?"false":"true");
    atomic_store(&observed->quarantined,1);
    /* Independent observer owns backend anchors and survives receiver loss.
     * Experimental collection wait is not an authorized drain policy bound. */
    uint64_t witness_until=tick_us()+15000000;
    while(alive(pgfd)&&alive(observer_fd)&&!atomic_load(&observed->outcome_confirmed)&&tick_us()<witness_until){
        if(tick_us()-atomic_load(&observed->observer_progress)>10000000)break;
        struct timespec pause={0,20000000};nanosleep(&pause,NULL);
    }
    printf("{\"event\":\"supervisor_independent_outcome\",\"confirmed\":%s}\n",atomic_load(&observed->outcome_confirmed)?"true":"false");
    /* Fast PG stop is a coarse disposable drain, NOT full watchdog qualification. */
    if(alive(pgfd))syscall(SYS_pidfd_send_signal,pgfd,SIGINT,NULL,0);
    if(alive(receiver_fd)){syscall(SYS_pidfd_send_signal,receiver_fd,SIGCONT,NULL,0);syscall(SYS_pidfd_send_signal,receiver_fd,SIGTERM,NULL,0);}
    if(alive(observer_fd)){syscall(SYS_pidfd_send_signal,observer_fd,SIGCONT,NULL,0);syscall(SYS_pidfd_send_signal,observer_fd,SIGTERM,NULL,0);}
    close(channel[0]);close(observer_channel[0]);int s;waitpid(pg,&s,0);waitpid(receiver,&s,0);waitpid(observer,&s,0);close(pgfd);close(receiver_fd);close(observer_fd);close(mem);close(statefd);
    printf("{\"event\":\"supervisor_verified_child_drain\"}\n");return 0;
}
