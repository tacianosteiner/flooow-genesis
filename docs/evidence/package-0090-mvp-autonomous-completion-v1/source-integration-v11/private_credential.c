#define _GNU_SOURCE
#include "private_credential.h"
#include <assert.h>
#include <errno.h>
#include <fcntl.h>
#include <grp.h>
#include <linux/capability.h>
#include <poll.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/prctl.h>
#include <sys/random.h>
#include <sys/socket.h>
#include <sys/stat.h>
#include <sys/syscall.h>
#include <sys/wait.h>
#include <unistd.h>
int s03_publish_immutable(const void *,size_t);
static void erase(void *p,size_t count){volatile unsigned char *bytes=p;while(count--)*bytes++=0;}
static void zero_caps(void){struct __user_cap_header_struct h={.version=_LINUX_CAPABILITY_VERSION_3,.pid=0};struct __user_cap_data_struct d[2]={{0},{0}};assert(syscall(SYS_capget,&h,d)==0);for(unsigned i=0;i<2;++i)assert(!(d[i].effective|d[i].permitted|d[i].inheritable));}
static void readable(int fd){struct pollfd p={.fd=fd,.events=POLLIN};assert(poll(&p,1,10000)==1&&(p.revents&POLLIN));}
static void alive(int fd){struct pollfd p={.fd=fd,.events=POLLIN};assert(poll(&p,1,0)==0);}
static void private_environ(void){assert(clearenv()==0&&setenv("PATH","/usr/bin:/bin",1)==0&&setenv("LC_ALL","C",1)==0);}
static void send_fd(int channel,int fd){
    char byte='S';struct iovec iov={.iov_base=&byte,.iov_len=1};union{struct cmsghdr align;char bytes[CMSG_SPACE(sizeof(int))];} control={0};
    struct msghdr msg={.msg_iov=&iov,.msg_iovlen=1,.msg_control=control.bytes,.msg_controllen=sizeof(control.bytes)};struct cmsghdr *c=CMSG_FIRSTHDR(&msg);c->cmsg_level=SOL_SOCKET;c->cmsg_type=SCM_RIGHTS;c->cmsg_len=CMSG_LEN(sizeof(int));memcpy(CMSG_DATA(c),&fd,sizeof(fd));assert(sendmsg(channel,&msg,MSG_NOSIGNAL)==1);
}
S03PendingCredential s03_prepare_private_test_credential(void){
    assert(getuid()==0);pid_t owner=getpid();int channels[2];assert(socketpair(AF_UNIX,SOCK_SEQPACKET|SOCK_CLOEXEC,0,channels)==0);
    int yes=1;assert(setsockopt(channels[0],SOL_SOCKET,SO_PASSCRED,&yes,sizeof(yes))==0&&setsockopt(channels[1],SOL_SOCKET,SO_PASSCRED,&yes,sizeof(yes))==0);
    pid_t child=fork();assert(child>=0);
    if(!child){
        close(channels[0]);assert(dup2(channels[1],3)==3&&fcntl(3,F_SETFD,FD_CLOEXEC)==0);assert(syscall(SYS_close_range,4u,~0u,0u)==0);close(0);
        assert(setgroups(0,NULL)==0&&setgid(10000)==0&&setuid(999)==0&&prctl(PR_SET_DUMPABLE,0)==0);zero_caps();
        int birth=(int)syscall(SYS_pidfd_open,owner,0);assert(birth>=0);readable(3);
        char command;struct iovec iov={.iov_base=&command,.iov_len=1};union{struct cmsghdr align;char bytes[CMSG_SPACE(sizeof(struct ucred))];} control={0};
        struct msghdr msg={.msg_iov=&iov,.msg_iovlen=1,.msg_control=control.bytes,.msg_controllen=sizeof(control.bytes)};
        assert(recvmsg(3,&msg,0)==1&&command=='G'&&!(msg.msg_flags&(MSG_CTRUNC|MSG_TRUNC)));struct cmsghdr *c=CMSG_FIRSTHDR(&msg);
        assert(c&&c->cmsg_level==SOL_SOCKET&&c->cmsg_type==SCM_CREDENTIALS&&c->cmsg_len==CMSG_LEN(sizeof(struct ucred))&&!CMSG_NXTHDR(&msg,c));struct ucred peer;memcpy(&peer,CMSG_DATA(c),sizeof(peer));assert(peer.pid==owner&&peer.uid==10000&&peer.gid==10000);alive(birth);
        /* No secret exists before the owner's post-fork request. Observers
         * have already execed and closed all unrelated source channels. */
        unsigned char random[32];size_t got=0;while(got<sizeof(random)){ssize_t n=getrandom(random+got,sizeof(random)-got,0);if(n<0&&errno==EINTR)continue;assert(n>0);got+=(size_t)n;}
        char password[65];const char *hex="0123456789abcdef";for(unsigned i=0;i<32;++i){password[i*2]=hex[random[i]>>4];password[i*2+1]=hex[random[i]&15];}password[64]=0;erase(random,sizeof(random));
        private_environ();PGconn *admin=PQconnectdb("host=/tmp/s03-socket port=5432 dbname=postgres user=postgres passfile=/nonexistent/s03-unused-passfile sslmode=disable gssencmode=disable require_auth=none options='' connect_timeout=5 application_name=s03_private_credential_issuer");assert(PQstatus(admin)==CONNECTION_OK);
        char *literal=PQescapeLiteral(admin,password,64);assert(literal);char sql[256];int length=snprintf(sql,sizeof(sql),"ALTER ROLE flooow_reader PASSWORD %s",literal);assert(length>0&&(size_t)length<sizeof(sql));PQfreemem(literal);
        PGresult *changed=PQexec(admin,sql);erase(sql,sizeof(sql));assert(PQresultStatus(changed)==PGRES_COMMAND_OK);PQclear(changed);PQfinish(admin);
        int secret=s03_publish_immutable(password,64);erase(password,sizeof(password));assert(secret>=0);alive(birth);send_fd(3,secret);
        readable(3);assert(recv(3,&command,1,0)==1&&command=='A');close(secret);close(birth);close(3);_exit(0);
    }
    close(channels[1]);int birth=(int)syscall(SYS_pidfd_open,child,0);assert(birth>=0);
    return (S03PendingCredential){channels[0],birth,child};
}
PGconn *s03_connect_private_test_reader(S03PendingCredential *pending){
    assert(getuid()==10000&&getgid()==10000);zero_caps();alive(pending->birth);assert(send(pending->channel,"G",1,MSG_NOSIGNAL)==1);readable(pending->channel);
    char byte;struct iovec iov={.iov_base=&byte,.iov_len=1};union{struct cmsghdr align;char bytes[CMSG_SPACE(sizeof(int))+CMSG_SPACE(sizeof(struct ucred))];} control={0};
    struct msghdr msg={.msg_iov=&iov,.msg_iovlen=1,.msg_control=control.bytes,.msg_controllen=sizeof(control.bytes)};
    assert(recvmsg(pending->channel,&msg,MSG_CMSG_CLOEXEC)==1&&byte=='S'&&!(msg.msg_flags&(MSG_CTRUNC|MSG_TRUNC)));int fd=-1,credentials=0;
    for(struct cmsghdr *c=CMSG_FIRSTHDR(&msg);c;c=CMSG_NXTHDR(&msg,c)){assert(c->cmsg_level==SOL_SOCKET);if(c->cmsg_type==SCM_RIGHTS){assert(fd<0&&c->cmsg_len==CMSG_LEN(sizeof(int)));memcpy(&fd,CMSG_DATA(c),sizeof(fd));}else{assert(c->cmsg_type==SCM_CREDENTIALS&&!credentials&&c->cmsg_len==CMSG_LEN(sizeof(struct ucred)));struct ucred peer;memcpy(&peer,CMSG_DATA(c),sizeof(peer));assert(peer.pid==pending->issuer&&peer.uid==999&&peer.gid==10000);credentials=1;}}
    assert(fd>=0&&credentials);alive(pending->birth);struct stat st;assert(fstat(fd,&st)==0&&S_ISREG(st.st_mode)&&st.st_uid==999&&st.st_size==64);
    assert((fcntl(fd,F_GETFL)&O_ACCMODE)==O_RDONLY&&(fcntl(fd,F_GETFD)&FD_CLOEXEC)&&fcntl(fd,F_GET_SEALS)==(F_SEAL_WRITE|F_SEAL_GROW|F_SEAL_SHRINK|F_SEAL_SEAL));
    char password[65]={0};assert(pread(fd,password,64,0)==64);close(fd);for(unsigned i=0;i<64;++i)assert((password[i]>='0'&&password[i]<='9')||(password[i]>='a'&&password[i]<='f'));
    private_environ();const char *keywords[]={"host","port","dbname","user","password","passfile","sslmode","gssencmode","require_auth","options","connect_timeout","application_name",NULL};
    const char *values[]={"/tmp/s03-socket","5432","postgres","flooow_reader",password,"/nonexistent/s03-unused-passfile","disable","disable","scram-sha-256","","5","s03_private_owner",NULL};
    PGconn *reader=PQconnectdbParams(keywords,values,0);erase(password,sizeof(password));assert(PQstatus(reader)==CONNECTION_OK&&PQconnectionUsedPassword(reader));
    assert(send(pending->channel,"A",1,MSG_NOSIGNAL)==1);close(pending->channel);int status;assert(waitpid(pending->issuer,&status,0)==pending->issuer&&WIFEXITED(status)&&WEXITSTATUS(status)==0);close(pending->birth);
    puts("PASS PRIVATE_EPHEMERAL_READER_CREDENTIAL_MECHANICS: generated after observer exec-ready, sender/receiver kernel credentials+pidfds, ROsealedsecret only to owner10000, SCRAM required; no credential bytes in image/argv/environment/observer export");fflush(stdout);
    return reader;
}
