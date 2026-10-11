/* Private TEST_ONLY_NONCANONICAL progress-channel adversarial vectors. */
#include "protocol.h"
#include "heartbeat.h"
static unsigned passed=0,failed=0;
static void check(const char *name,int condition){printf("%s=%s\n",name,condition?"PASS":"FAIL");if(condition)passed++;else failed++;}
static void raw(int fd,unsigned char marker,uint64_t stamp,size_t length){unsigned char b[9]={marker};for(unsigned i=0;i<8;i++)b[i+1]=(unsigned char)(stamp>>(56-i*8));send(fd,b,length,MSG_NOSIGNAL);}
int main(void){
    int pair[2],one=0;uint64_t last=0;if(socketpair(AF_UNIX,SOCK_SEQPACKET|SOCK_NONBLOCK,0,pair))return 70;
    int self=syscall(SYS_pidfd_open,getpid(),0);if(self<0||!progress_enable(pair[1]))return 77;
    check("empty_queue_no_progress",progress_receive(pair[1],self,0xb1,&last)==0);
    check("fresh_send",progress_send(pair[0],0xb1));check("fresh_kernel_bound_progress",progress_receive(pair[1],self,0xb1,&last)==1);
    raw(pair[0],0xb1,last,9);check("replay_denied",progress_receive(pair[1],self,0xb1,&last)==-1);
    raw(pair[0],0xb1,tick_us()+1000000,9);check("future_stamp_denied",progress_receive(pair[1],self,0xb1,&last)==-1);
    uint64_t saved=last;
    raw(pair[0],0xb1,tick_us()-10000001,9);check("expired_stamp_denied",progress_receive(pair[1],self,0xb1,&last)==-1);
    check("stale_queued_message_never_renews_liveness",last==saved);
    last=0;uint64_t emitted=tick_us();raw(pair[0],0xb1,emitted,9);
    struct timespec queued={11,0};nanosleep(&queued,NULL);
    check("fresh_at_emission_stale_at_consumption_denied",progress_receive(pair[1],self,0xb1,&last)==-1&&last==0);
    raw(pair[0],0xb2,tick_us(),9);check("wrong_marker_denied",progress_receive(pair[1],self,0xb1,&last)==-1);
    raw(pair[0],0xb1,tick_us(),1);check("short_frame_denied",progress_receive(pair[1],self,0xb1,&last)==-1);
    setsockopt(pair[1],SOL_SOCKET,SO_PASSPIDFD,&one,sizeof(one));raw(pair[0],0xb1,tick_us(),9);check("missing_kernel_sender_denied",progress_receive(pair[1],self,0xb1,&last)==-1);
    close(pair[0]);check("channel_loss_denied",progress_receive(pair[1],self,0xb1,&last)==-1);
    close(pair[1]);close(self);printf("N=%u FAILURES=%u\n",passed+failed,failed);return failed?1:0;
}
