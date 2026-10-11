/* TEST_ONLY_NONCANONICAL experimental progress protocol; no policy authority. */
#include <sys/socket.h>
static int progress_enable(int fd) {
    int one=1; return setsockopt(fd,SOL_SOCKET,SO_PASSPIDFD,&one,sizeof(one))==0;
}
static int progress_receive(int fd,int expected,unsigned char marker) {
    unsigned char b=0; union {struct cmsghdr align; char bytes[128];} control={0};
    struct iovec i={&b,1}; struct msghdr m={.msg_iov=&i,.msg_iovlen=1,.msg_control=control.bytes,.msg_controllen=sizeof(control.bytes)};
    int count=0,valid=0; ssize_t n=recvmsg(fd,&m,MSG_DONTWAIT|MSG_CMSG_CLOEXEC);
    if(n<0)return errno==EAGAIN?0:-1;
    for(struct cmsghdr *c=CMSG_FIRSTHDR(&m);c;c=CMSG_NXTHDR(&m,c)) {
        if(c->cmsg_level==SOL_SOCKET && c->cmsg_type==SCM_PIDFD && c->cmsg_len==CMSG_LEN(sizeof(int))) {
            int anchor;memcpy(&anchor,CMSG_DATA(c),sizeof(anchor)); count++;valid=anchor_equal(anchor,expected)&&alive(anchor);close(anchor);
        } else valid=0;
    }
    return n==1 && b==marker && !(m.msg_flags&(MSG_TRUNC|MSG_CTRUNC)) && count==1 && valid?1:-1;
}
static int progress_send(int fd,unsigned char marker) {
    return send(fd,&marker,1,MSG_DONTWAIT|MSG_NOSIGNAL)==1;
}
