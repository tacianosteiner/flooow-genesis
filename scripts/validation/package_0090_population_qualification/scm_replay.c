/* TEST_ONLY_NONCANONICAL: retain an actual backend's transferred self anchor. */
#include "protocol.h"
int main(void){
    setvbuf(stdout,NULL,_IOLBF,0);uint64_t deadline=tick_us()+20000000;
    int listener=socket(AF_UNIX,SOCK_SEQPACKET|SOCK_CLOEXEC|SOCK_NONBLOCK,0),one=1;
    struct sockaddr_un address={.sun_family=AF_UNIX};strcpy(address.sun_path,TEST_DIR "/replay-capture.sock");umask(0077);
    if(listener<0||setsockopt(listener,SOL_SOCKET,SO_PASSPIDFD,&one,sizeof(one))||setsockopt(listener,SOL_SOCKET,SO_PASSCRED,&one,sizeof(one))||bind(listener,(struct sockaddr *)&address,sizeof(address))||listen(listener,1)||!wait_fd(listener,POLLIN,deadline))return 70;
    int fd=accept4(listener,NULL,NULL,SOCK_CLOEXEC|SOCK_NONBLOCK),peer=-1,retained=-1,sender=-1;struct ucred cred={0},message_cred={0};socklen_t peer_size=sizeof(peer),cred_size=sizeof(cred);
    if(fd<0||getsockopt(fd,SOL_SOCKET,SO_PEERPIDFD,&peer,&peer_size)||getsockopt(fd,SOL_SOCKET,SO_PEERCRED,&cred,&cred_size)||!wait_fd(fd,POLLIN,deadline))return 70;
    unsigned char frame[FRAME_MAX];union {struct cmsghdr a;char bytes[256];} control={0};struct iovec i={frame,sizeof(frame)};
    struct msghdr m={.msg_iov=&i,.msg_iovlen=1,.msg_control=control.bytes,.msg_controllen=sizeof(control.bytes)};
    ssize_t size=recvmsg(fd,&m,MSG_CMSG_CLOEXEC|MSG_DONTWAIT);unsigned rights=0,pidfds=0,credentials=0,extra=0;
    for(struct cmsghdr *c=CMSG_FIRSTHDR(&m);c;c=CMSG_NXTHDR(&m,c)){
        if(c->cmsg_level==SOL_SOCKET&&c->cmsg_type==SCM_RIGHTS){size_t n=(c->cmsg_len-CMSG_LEN(0))/sizeof(int);int *p=(int *)CMSG_DATA(c);for(size_t j=0;j<n;j++){if(rights++)close(p[j]);else retained=p[j];}}
        else if(c->cmsg_level==SOL_SOCKET&&c->cmsg_type==SCM_PIDFD&&c->cmsg_len==CMSG_LEN(sizeof(int))){int v;memcpy(&v,CMSG_DATA(c),sizeof(v));if(pidfds++)close(v);else sender=v;}
        else if(c->cmsg_level==SOL_SOCKET&&c->cmsg_type==SCM_CREDENTIALS&&c->cmsg_len==CMSG_LEN(sizeof(message_cred))){memcpy(&message_cred,CMSG_DATA(c),sizeof(message_cred));credentials++;}
        else extra++;
    }
    request_fields r={0};
    if(size<0||m.msg_flags&(MSG_TRUNC|MSG_CTRUNC)||rights!=1||pidfds!=1||credentials!=1||extra||!decode_request(frame,size,&r)||cred.uid!=getuid()||cred.gid!=getgid()||message_cred.pid!=cred.pid||message_cred.uid!=cred.uid||message_cred.gid!=cred.gid||!anchor_equal(peer,sender)||!anchor_equal(sender,retained)||!alive(retained))return 70;
    int saved=open(TEST_DIR "/TEST_ONLY_NONCANONICAL-captured-frame.bin",O_WRONLY|O_CREAT|O_EXCL|O_NOFOLLOW|O_CLOEXEC,0600);
    if(saved<0||write(saved,frame,(size_t)size)!=size)return 70;close(saved);
    struct stat st;fstat(retained,&st);unsigned char digest[32];SHA256(frame,size,digest);
    printf("{\"event\":\"actual_live_backend_anchor_captured\",\"pid\":%d,\"inode\":%llu,\"role_oid\":%u,\"frame_sha256\":\"",cred.pid,(unsigned long long)st.st_ino,r.role);for(unsigned j=0;j<32;j++)printf("%02x",digest[j]);puts("\"}");
    unsigned char receipt=0xd1;if(send(fd,&receipt,1,MSG_NOSIGNAL)!=1)return 70;close(fd);close(peer);close(sender);close(listener);
    while(alive(retained)&&tick_us()<deadline){struct timespec pause={0,20000000};nanosleep(&pause,NULL);}if(alive(retained))return 70;
    fd=socket(AF_UNIX,SOCK_SEQPACKET|SOCK_CLOEXEC|SOCK_NONBLOCK,0);strcpy(address.sun_path,TEST_SOCKET);
    if(fd<0||connect(fd,(struct sockaddr *)&address,sizeof(address))||!wait_fd(fd,POLLOUT,deadline)||!send_anchor(fd,frame,size,retained)||!wait_fd(fd,POLLIN,deadline))return 70;
    unsigned char reply[80];ssize_t got=recv(fd,reply,sizeof(reply),MSG_DONTWAIT);
    int denied=got==78&&!memcmp(reply,"G3F4",4)&&reply[5]==1&&reply[6]==3&&reply[76]==0&&reply[77]==6;
    printf("{\"event\":\"actual_dead_anchor_SCM_RIGHTS_replayed\",\"retained_inode\":%llu,\"kernel_dead\":true,\"deny_reason\":%d,\"denied\":%s}\n",(unsigned long long)st.st_ino,got==78?reply[77]:-1,denied?"true":"false");
    close(retained);close(fd);unlink(TEST_DIR "/replay-capture.sock");return denied?0:1;
}
