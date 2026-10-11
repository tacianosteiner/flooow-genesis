/* TEST_ONLY_NONCANONICAL experimental progress protocol; no policy authority. */
#include <sys/socket.h>
static unsigned char progress_first_emitted[9];
static int progress_enable(int fd) {
    int one=1; return setsockopt(fd,SOL_SOCKET,SO_PASSPIDFD,&one,sizeof(one))==0;
}
static int progress_receive(int fd,int expected,unsigned char marker,uint64_t *last_stamp) {
    unsigned char b[9]={0}; union {struct cmsghdr align; char bytes[128];} control={0};
    struct iovec i={b,sizeof(b)}; struct msghdr m={.msg_iov=&i,.msg_iovlen=1,.msg_control=control.bytes,.msg_controllen=sizeof(control.bytes)};
    int count=0,valid=0,extra=0; ssize_t n=recvmsg(fd,&m,MSG_DONTWAIT|MSG_CMSG_CLOEXEC);
    if(n<0)return errno==EAGAIN?0:-1;
    for(struct cmsghdr *c=CMSG_FIRSTHDR(&m);c;c=CMSG_NXTHDR(&m,c)) {
        if(c->cmsg_level==SOL_SOCKET && c->cmsg_type==SCM_PIDFD && c->cmsg_len==CMSG_LEN(sizeof(int))) {
            int anchor;memcpy(&anchor,CMSG_DATA(c),sizeof(anchor)); count++;valid=anchor_equal(anchor,expected)&&alive(anchor);close(anchor);
        } else {extra++;
            if(c->cmsg_level==SOL_SOCKET&&c->cmsg_type==SCM_RIGHTS){size_t nf=(c->cmsg_len-CMSG_LEN(0))/sizeof(int);int *fds=(int *)CMSG_DATA(c);for(size_t j=0;j<nf;j++)close(fds[j]);}}
    }
    uint64_t stamp=0;for(unsigned j=1;j<9;j++)stamp=(stamp<<8)|b[j];uint64_t now=tick_us();
    if(n!=9||b[0]!=marker||(m.msg_flags&(MSG_TRUNC|MSG_CTRUNC))||extra||count!=1||!valid||stamp>now||stamp<=*last_stamp||now-stamp>10000000)return -1;
    *last_stamp=stamp;return 1;
}
static int progress_send(int fd,unsigned char marker) {
    unsigned char b[9];b[0]=marker;uint64_t stamp=tick_us();for(unsigned j=0;j<8;j++)b[j+1]=(unsigned char)(stamp>>(56-j*8));
    ssize_t sent=send(fd,b,sizeof(b),MSG_DONTWAIT|MSG_NOSIGNAL);
    if(sent==(ssize_t)sizeof(b)&&!progress_first_emitted[0])memcpy(progress_first_emitted,b,sizeof(b));
    return sent==(ssize_t)sizeof(b)?1:sent<0&&(errno==EAGAIN||errno==EWOULDBLOCK)?0:-1;
}
