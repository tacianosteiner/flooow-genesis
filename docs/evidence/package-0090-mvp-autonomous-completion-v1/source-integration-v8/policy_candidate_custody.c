#define _GNU_SOURCE
#include "bootstrap_expectation.h"
#include "policy_candidate_custody.h"
#include "policy_proposal_values.h"
#include <assert.h>
#include <errno.h>
#include <fcntl.h>
#include <grp.h>
#include <linux/capability.h>
#include <openssl/sha.h>
#include <poll.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <sys/prctl.h>
#include <sys/socket.h>
#include <sys/stat.h>
#include <sys/syscall.h>
#include <sys/wait.h>
#include <time.h>
#include <unistd.h>
int s03_publish_immutable(const void *,size_t);
typedef struct {
    uint32_t version,source_acceptance_state,activation_state;
    uint64_t proposed_max_age_us,proposed_lease_us,max_rows,max_frame_bytes;
    uint64_t held_started_us,held_finished_us;
    S03RawBootstrap raw_context;
    char policy_version[64],proposal_sha256[65];
} PolicyCandidate;
/* Structural intake guard only, never source/policy acceptance. All explicit
 * parameters and complete original raw context must match held expectations. */
static int exact_unaccepted_projection(const PolicyCandidate *p,const S03RawBootstrap *expected){
    if(p->version!=1||p->source_acceptance_state!=1||p->activation_state!=1||
       p->proposed_max_age_us!=S03_PROPOSED_MAX_AGE_US||p->proposed_lease_us!=S03_PROPOSED_LEASE_US||
       p->max_rows!=S03_PROPOSED_MAX_ROWS||p->max_frame_bytes!=S03_PROPOSED_MAX_BYTES||
       memcmp(p->proposal_sha256,S03_POLICY_PROPOSAL_SHA256,65)||
       memcmp(p->policy_version,S03_PROPOSED_POLICY_VERSION,sizeof(S03_PROPOSED_POLICY_VERSION))||
       memcmp(expected,&p->raw_context,sizeof(*expected))||
       p->held_started_us<expected->finished_us||p->held_finished_us<p->held_started_us)return 0;
    for(size_t i=sizeof(S03_PROPOSED_POLICY_VERSION);i<sizeof(p->policy_version);++i)if(p->policy_version[i])return 0;
    return 1;
}
static uint64_t tick(void){struct timespec t;assert(clock_gettime(CLOCK_BOOTTIME,&t)==0);return (uint64_t)t.tv_sec*1000000+(uint64_t)t.tv_nsec/1000;}
static void wait_readable(int fd){struct pollfd p={.fd=fd,.events=POLLIN};assert(poll(&p,1,10000)==1&&(p.revents&POLLIN));}
static void live(int fd){struct pollfd p={.fd=fd,.events=POLLIN};assert(poll(&p,1,0)==0);}
static void print_record(const char *kind,int fd,const PolicyCandidate *p,pid_t sender){
    unsigned char digest[32];assert(SHA256((const unsigned char *)p,sizeof(*p),digest));
    char hash[65];for(unsigned i=0;i<32;++i)snprintf(hash+i*2,3,"%02x",digest[i]);
    struct stat st;assert(fstat(fd,&st)==0);char line[900];
    int n=snprintf(line,sizeof(line),"{\"kind\":\"%s\",\"pid\":%ld,\"sender_pid\":%ld,\"device\":%llu,\"inode\":%llu,\"private_record_sha256\":\"%s\",\"proposal_sha256\":\"%s\",\"proposed_max_age_us\":%llu,\"proposed_lease_us\":%llu,\"start_boottime_us\":%llu,\"finish_boottime_us\":%llu,\"policy_approval\":\"NOT_ESTABLISHED\",\"source_acceptance\":\"NOT_ESTABLISHED\",\"activation\":\"NOT_ESTABLISHED\",\"activated_by_this_run\":false}\n",kind,(long)getpid(),(long)sender,(unsigned long long)st.st_dev,(unsigned long long)st.st_ino,hash,p->proposal_sha256,(unsigned long long)p->proposed_max_age_us,(unsigned long long)p->proposed_lease_us,(unsigned long long)p->held_started_us,(unsigned long long)p->held_finished_us);
    assert(n>0&&(size_t)n<sizeof(line)&&write(1,line,(size_t)n)==n);
}
static void send_candidate(int channel,int fd){
    char byte='C';struct iovec iov={.iov_base=&byte,.iov_len=1};
    union{struct cmsghdr align;char bytes[CMSG_SPACE(sizeof(int))];} control={0};
    struct msghdr msg={.msg_iov=&iov,.msg_iovlen=1,.msg_control=control.bytes,.msg_controllen=sizeof(control.bytes)};
    struct cmsghdr *c=CMSG_FIRSTHDR(&msg);c->cmsg_level=SOL_SOCKET;c->cmsg_type=SCM_RIGHTS;c->cmsg_len=CMSG_LEN(sizeof(int));memcpy(CMSG_DATA(c),&fd,sizeof(fd));
    assert(sendmsg(channel,&msg,MSG_NOSIGNAL)==1);
}
int s03_hold_policy_provisioning_candidate(int raw_bootstrap_fd){
    assert(getuid()==0);int channels[2];assert(socketpair(AF_UNIX,SOCK_SEQPACKET|SOCK_CLOEXEC,0,channels)==0);
    int passcred=1;assert(setsockopt(channels[0],SOL_SOCKET,SO_PASSCRED,&passcred,sizeof(passcred))==0);
    int copied=fcntl(raw_bootstrap_fd,F_DUPFD_CLOEXEC,10);assert(copied>=10);
    pid_t child=fork();assert(child>=0);
    if(!child){
        close(channels[0]);assert(dup2(channels[1],3)==3&&dup2(copied,4)==4);
        assert(fcntl(3,F_SETFD,FD_CLOEXEC)==0&&fcntl(4,F_SETFD,FD_CLOEXEC)==0);
        assert(syscall(SYS_close_range,5u,~0u,0u)==0);close(0);
        assert(setgroups(0,NULL)==0&&setgid(10003)==0&&setuid(10003)==0);
        struct __user_cap_header_struct header={.version=_LINUX_CAPABILITY_VERSION_3,.pid=0};struct __user_cap_data_struct caps[2]={{0},{0}};
        assert(syscall(SYS_capget,&header,caps)==0);for(unsigned i=0;i<2;++i)assert(!(caps[i].effective|caps[i].permitted|caps[i].inheritable));
        /* Public preparation code/context only; no SQL/private credentials.
         * Permit the external HOST manager's same-UID metadata read at gate. */
        assert(prctl(PR_SET_DUMPABLE,1)==0);
        assert(send(3,"R",1,MSG_NOSIGNAL)==1);
        char ready[120];int size=snprintf(ready,sizeof(ready),"HOST_POLICY_CANDIDATE_CUSTODIAN_BIRTH_READY PID=%ld UID=10003\n",(long)getpid());assert(size>0&&(size_t)size<sizeof(ready)&&write(1,ready,(size_t)size)==size);
        wait_readable(3);char action;assert(recv(3,&action,1,0)==1&&action=='P');
        assert(prctl(PR_SET_DUMPABLE,0)==0&&prctl(PR_SET_NO_NEW_PRIVS,1,0,0,0)==0);
        PolicyCandidate p={0};p.version=1;p.source_acceptance_state=1;p.activation_state=1; /* Explicit NOT_ESTABLISHED tags. */
        p.held_started_us=tick();s03_read_raw_bootstrap(4,&p.raw_context);close(4);
        p.proposed_max_age_us=S03_PROPOSED_MAX_AGE_US;p.proposed_lease_us=S03_PROPOSED_LEASE_US;p.max_rows=S03_PROPOSED_MAX_ROWS;p.max_frame_bytes=S03_PROPOSED_MAX_BYTES;
        assert(p.proposed_max_age_us&&p.proposed_lease_us&&p.max_rows&&p.max_frame_bytes);
        assert(sizeof(S03_PROPOSED_POLICY_VERSION)<=sizeof(p.policy_version)&&sizeof(S03_POLICY_PROPOSAL_SHA256)==65);
        memcpy(p.policy_version,S03_PROPOSED_POLICY_VERSION,sizeof(S03_PROPOSED_POLICY_VERSION));memcpy(p.proposal_sha256,S03_POLICY_PROPOSAL_SHA256,65);p.held_finished_us=tick();
        /* Actual immutable custody of proposed provisioning data. No field is
         * set to accepted/approved/active; numbers are never used as a lease. */
        int fd=s03_publish_immutable(&p,sizeof(p));assert(fd>=0);print_record("POLICY_PROVISIONING_CANDIDATE_HELD_NOT_APPROVED",fd,&p,getpid());
        send_candidate(3,fd);wait_readable(3);assert(recv(3,&action,1,0)==1&&action=='A');close(fd);close(3);_exit(0);
    }
    close(copied);close(channels[1]);int birth=(int)syscall(SYS_pidfd_open,child,0);assert(birth>=0);
    wait_readable(channels[0]);char ready;assert(recv(channels[0],&ready,1,0)==1&&ready=='R');
    char command[80];assert(fgets(command,sizeof(command),stdin)&&!strcmp(command,"PUBLISH_UNACCEPTED_POLICY_CANDIDATE\n"));
    live(birth);assert(send(channels[0],"P",1,MSG_NOSIGNAL)==1);wait_readable(channels[0]);
    char byte;struct iovec iov={.iov_base=&byte,.iov_len=1};
    union{struct cmsghdr align;char bytes[CMSG_SPACE(sizeof(int))+CMSG_SPACE(sizeof(struct ucred))];} control={0};
    struct msghdr msg={.msg_iov=&iov,.msg_iovlen=1,.msg_control=control.bytes,.msg_controllen=sizeof(control.bytes)};
    assert(recvmsg(channels[0],&msg,MSG_CMSG_CLOEXEC)==1&&byte=='C'&&!(msg.msg_flags&(MSG_CTRUNC|MSG_TRUNC)));
    int fd=-1,credentials=0;for(struct cmsghdr *c=CMSG_FIRSTHDR(&msg);c;c=CMSG_NXTHDR(&msg,c)){
        assert(c->cmsg_level==SOL_SOCKET);
        if(c->cmsg_type==SCM_RIGHTS){assert(fd==-1&&c->cmsg_len==CMSG_LEN(sizeof(int)));memcpy(&fd,CMSG_DATA(c),sizeof(fd));}
        else{assert(c->cmsg_type==SCM_CREDENTIALS&&!credentials&&c->cmsg_len==CMSG_LEN(sizeof(struct ucred)));struct ucred u;memcpy(&u,CMSG_DATA(c),sizeof(u));assert(u.pid==child&&u.uid==10003&&u.gid==10003);credentials=1;}
    }
    assert(fd>=0&&credentials);live(birth);
    assert((fcntl(fd,F_GETFL)&O_ACCMODE)==O_RDONLY&&fcntl(fd,F_GET_SEALS)==(F_SEAL_WRITE|F_SEAL_GROW|F_SEAL_SHRINK|F_SEAL_SEAL));
    PolicyCandidate p;struct stat st;assert(fstat(fd,&st)==0&&st.st_size==(off_t)sizeof(p)&&pread(fd,&p,sizeof(p),0)==sizeof(p));
    S03RawBootstrap expected;s03_read_raw_bootstrap(raw_bootstrap_fd,&expected);assert(exact_unaccepted_projection(&p,&expected));
    print_record("POLICY_PROVISIONING_CANDIDATE_RECEIVED_KERNEL_ORIGIN_VERIFIED",fd,&p,child);live(birth);
    assert(send(channels[0],"A",1,MSG_NOSIGNAL)==1);close(channels[0]);int status;assert(waitpid(child,&status,0)==child&&WIFEXITED(status)&&WEXITSTATUS(status)==0);close(birth);
    return fd;
}
