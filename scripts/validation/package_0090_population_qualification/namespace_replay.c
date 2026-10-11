/* TEST_ONLY_NONCANONICAL: unmodified valid foreign bootstrap bytes, own self anchor. */
#include "protocol.h"
int main(void){
    unsigned char frame[FRAME_MAX],reply[80];request_fields request={0};
    int source=open(TEST_DIR "/TEST_ONLY_NONCANONICAL-foreign-frame.bin",O_RDONLY|O_NOFOLLOW|O_CLOEXEC);
    if(source<0)return 70;ssize_t size=read(source,frame,sizeof(frame));close(source);
    if(size<=0||!decode_request(frame,(size_t)size,&request))return 70;
    int self=(int)syscall(SYS_pidfd_open,getpid(),0),fd=socket(AF_UNIX,SOCK_SEQPACKET|SOCK_CLOEXEC|SOCK_NONBLOCK,0);
    struct sockaddr_un address={.sun_family=AF_UNIX};strcpy(address.sun_path,TEST_SOCKET);
    uint64_t deadline=tick_us()+5000000;
    if(self<0||fd<0||connect(fd,(struct sockaddr *)&address,sizeof(address))||!wait_fd(fd,POLLOUT,deadline)||!send_anchor(fd,frame,(size_t)size,self)||!wait_fd(fd,POLLIN,deadline))return 70;
    ssize_t got=recv(fd,reply,sizeof(reply),MSG_DONTWAIT);
    int denied=got==78&&!memcmp(reply,"G3F4",4)&&reply[5]==1&&reply[6]==3&&reply[76]==0&&reply[77]==3;
    printf("{\"event\":\"actual_valid_foreign_namespace_frame\",\"self_anchor_alive\":%s,\"deny_reason\":%d,\"context_denied\":%s}\n",alive(self)?"true":"false",got==78?reply[77]:-1,denied?"true":"false");
    close(self);close(fd);return denied?0:1;
}
