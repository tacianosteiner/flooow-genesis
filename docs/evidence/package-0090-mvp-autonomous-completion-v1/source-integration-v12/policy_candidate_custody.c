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
#include <stdlib.h>
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
    uint32_t version,source_acceptance_state,activation_state,decision_state;
    uint64_t proposed_max_age_us,proposed_lease_us,max_rows,max_frame_bytes;
    uint64_t held_started_us,held_finished_us;
    S03RawBootstrap raw_context;
    char policy_version[64],proposal_sha256[65];
    unsigned char host_decision_request[208];
} PolicyCandidate;
static unsigned hex_value(char c){if(c>='0'&&c<='9')return (unsigned)(c-'0');if(c>='a'&&c<='f')return (unsigned)(c-'a'+10);assert(0);return 0;}
static uint64_t be_integer(const unsigned char *p,unsigned n){uint64_t value=0;for(unsigned i=0;i<n;++i)value=(value<<8)|p[i];return value;}
static uint64_t process_start_ticks(void){
    FILE *file=fopen("/proc/self/stat","r");assert(file);char line[2048];assert(fgets(line,sizeof(line),file));fclose(file);
    char *end=strrchr(line,')');assert(end&&end[1]==' ');char *save=NULL;char *part=strtok_r(end+2," ",&save);
    for(unsigned field=3;field<22;++field){assert(part);part=strtok_r(NULL," ",&save);}assert(part);
    errno=0;char *tail;unsigned long long value=strtoull(part,&tail,10);assert(!errno&&*tail==0&&value);return value;
}
static void validate_request_hashes(const unsigned char *request){
    for(unsigned i=0;i<32;++i){assert(request[i]==(hex_value(S03_MVP_PARENT_RECEIPT_SHA256[i*2])<<4|hex_value(S03_MVP_PARENT_RECEIPT_SHA256[i*2+1])));assert(request[32+i]==(hex_value(S03_POLICY_PROPOSAL_SHA256[i*2])<<4|hex_value(S03_POLICY_PROPOSAL_SHA256[i*2+1])));}
    assert(be_integer(request+172,4)==1); /* Explicit bound parameter approval action, not mere ISSUE/PUBLISH. */
    assert(be_integer(request+176,8)==S03_PROPOSED_MAX_AGE_US&&be_integer(request+184,8)==S03_PROPOSED_LEASE_US&&be_integer(request+192,8)==S03_PROPOSED_MAX_ROWS&&be_integer(request+200,8)==S03_PROPOSED_MAX_BYTES);
}
static void validate_own_request(const unsigned char *request){
    validate_request_hashes(request);assert(be_integer(request+144,4)==(uint64_t)getpid()&&be_integer(request+148,8)==process_start_ticks());
    struct stat pidns,timens;assert(stat("/proc/self/ns/pid",&pidns)==0&&stat("/proc/self/ns/time",&timens)==0);
    assert(be_integer(request+156,8)==pidns.st_ino&&be_integer(request+164,8)==timens.st_ino);
    /* External manager/daemon/image/container identity is retained as actual
     * control-origin input and independently verified outside this process.
     * These bytes/hashes alone neither authenticate delegation nor approve. */
}
/* Structural intake guard only, never source/policy acceptance. All explicit
 * parameters and complete original raw context must match held expectations. */
static int exact_unaccepted_projection(const PolicyCandidate *p,const S03RawBootstrap *expected){
    if(p->version!=3||p->source_acceptance_state!=1||p->activation_state!=1||p->decision_state!=2||
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
    struct stat st;assert(fstat(fd,&st)==0);char line[1100];
    int n=snprintf(line,sizeof(line),"{\"kind\":\"%s\",\"pid\":%ld,\"sender_pid\":%ld,\"record_fd\":%d,\"private_record_size\":%zu,\"device\":%llu,\"inode\":%llu,\"private_record_sha256\":\"%s\",\"proposal_sha256\":\"%s\",\"proposed_max_age_us\":%llu,\"proposed_lease_us\":%llu,\"start_boottime_us\":%llu,\"finish_boottime_us\":%llu,\"issuer_decision_claim\":\"APPROVE_BOUND_PARAMETER_VALUES_PENDING_INDEPENDENT_CHECK\",\"qualified_policy_approval\":\"NOT_ESTABLISHED\",\"source_acceptance\":\"NOT_ESTABLISHED\",\"activation\":\"NOT_ESTABLISHED\",\"activated_by_this_run\":false}\n",kind,(long)getpid(),(long)sender,fd,sizeof(*p),(unsigned long long)st.st_dev,(unsigned long long)st.st_ino,hash,p->proposal_sha256,(unsigned long long)p->proposed_max_age_us,(unsigned long long)p->proposed_lease_us,(unsigned long long)p->held_started_us,(unsigned long long)p->held_finished_us);
    assert(n>0&&(size_t)n<sizeof(line)&&write(1,line,(size_t)n)==n);
}
static void send_candidate(int channel,int fd){
    unsigned char bytes[5]={'C',(unsigned char)((unsigned)fd>>24),(unsigned char)((unsigned)fd>>16),(unsigned char)((unsigned)fd>>8),(unsigned char)fd};struct iovec iov={.iov_base=bytes,.iov_len=sizeof(bytes)};
    union{struct cmsghdr align;char bytes[CMSG_SPACE(sizeof(int))];} control={0};
    struct msghdr msg={.msg_iov=&iov,.msg_iovlen=1,.msg_control=control.bytes,.msg_controllen=sizeof(control.bytes)};
    struct cmsghdr *c=CMSG_FIRSTHDR(&msg);c->cmsg_level=SOL_SOCKET;c->cmsg_type=SCM_RIGHTS;c->cmsg_len=CMSG_LEN(sizeof(int));memcpy(CMSG_DATA(c),&fd,sizeof(fd));
    assert(sendmsg(channel,&msg,MSG_NOSIGNAL)==sizeof(bytes));
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
        wait_readable(3);unsigned char request[208];assert(recv(3,request,sizeof(request),0)==sizeof(request));validate_own_request(request);
        assert(prctl(PR_SET_DUMPABLE,0)==0&&prctl(PR_SET_NO_NEW_PRIVS,1,0,0,0)==0);
        PolicyCandidate p={0};p.version=3;p.source_acceptance_state=1;p.activation_state=1;p.decision_state=2; /* Issuer parameter approval claim, NOT qualified/source accepted/active. */
        memcpy(p.host_decision_request,request,sizeof(request));
        p.held_started_us=tick();s03_read_raw_bootstrap(4,&p.raw_context);close(4);
        p.proposed_max_age_us=S03_PROPOSED_MAX_AGE_US;p.proposed_lease_us=S03_PROPOSED_LEASE_US;p.max_rows=S03_PROPOSED_MAX_ROWS;p.max_frame_bytes=S03_PROPOSED_MAX_BYTES;
        assert(p.proposed_max_age_us&&p.proposed_lease_us&&p.max_rows&&p.max_frame_bytes);
        assert(sizeof(S03_PROPOSED_POLICY_VERSION)<=sizeof(p.policy_version)&&sizeof(S03_POLICY_PROPOSAL_SHA256)==65);
        memcpy(p.policy_version,S03_PROPOSED_POLICY_VERSION,sizeof(S03_PROPOSED_POLICY_VERSION));memcpy(p.proposal_sha256,S03_POLICY_PROPOSAL_SHA256,65);p.held_finished_us=tick();
        /* Actual distinct explicit parameter disposition through HOST role.
         * Authority/qualification/source acceptance are independently checked;
         * this record cannot activate a policy or use numbers as a lease. */
        int fd=s03_publish_immutable(&p,sizeof(p));assert(fd>=0);print_record("POLICY_ISSUER_PARAMETER_APPROVAL_CLAIM_NOT_ACCEPTED",fd,&p,getpid());
        send_candidate(3,fd);
        /* Qualification handoff wait is HOST test control, NOT source TTL. */
        struct pollfd pending={.fd=3,.events=POLLIN};assert(poll(&pending,1,180000)==1&&(pending.revents&POLLIN));
        char action;assert(recv(3,&action,1,0)==1&&action=='A');close(fd);close(3);_exit(0);
    }
    close(copied);close(channels[1]);int birth=(int)syscall(SYS_pidfd_open,child,0);assert(birth>=0);
    wait_readable(channels[0]);char ready;assert(recv(channels[0],&ready,1,0)==1&&ready=='R');
    char command[512];const char prefix[]="APPROVE_BOUND_POLICY_VALUES_PENDING_SOURCE_ACCEPTANCE ";assert(fgets(command,sizeof(command),stdin));
    size_t begin=sizeof(prefix)-1;assert(!memcmp(command,prefix,begin)&&strlen(command)==begin+416+1&&command[begin+416]=='\n');
    unsigned char request[208];for(unsigned i=0;i<208;++i)request[i]=(uint8_t)((hex_value(command[begin+i*2])<<4)|hex_value(command[begin+i*2+1]));
    validate_request_hashes(request);assert(be_integer(request+144,4)==(uint64_t)child);
    live(birth);assert(send(channels[0],request,sizeof(request),MSG_NOSIGNAL)==sizeof(request));wait_readable(channels[0]);
    unsigned char payload[5];struct iovec iov={.iov_base=payload,.iov_len=sizeof(payload)};
    union{struct cmsghdr align;char bytes[CMSG_SPACE(sizeof(int))+CMSG_SPACE(sizeof(struct ucred))];} control={0};
    struct msghdr msg={.msg_iov=&iov,.msg_iovlen=1,.msg_control=control.bytes,.msg_controllen=sizeof(control.bytes)};
    assert(recvmsg(channels[0],&msg,MSG_CMSG_CLOEXEC)==sizeof(payload)&&payload[0]=='C'&&!(msg.msg_flags&(MSG_CTRUNC|MSG_TRUNC)));
    unsigned sender_fd=(unsigned)be_integer(payload+1,4);assert(sender_fd<64);
    int fd=-1,credentials=0;for(struct cmsghdr *c=CMSG_FIRSTHDR(&msg);c;c=CMSG_NXTHDR(&msg,c)){
        assert(c->cmsg_level==SOL_SOCKET);
        if(c->cmsg_type==SCM_RIGHTS){assert(fd==-1&&c->cmsg_len==CMSG_LEN(sizeof(int)));memcpy(&fd,CMSG_DATA(c),sizeof(fd));}
        else{assert(c->cmsg_type==SCM_CREDENTIALS&&!credentials&&c->cmsg_len==CMSG_LEN(sizeof(struct ucred)));struct ucred u;memcpy(&u,CMSG_DATA(c),sizeof(u));assert(u.pid==child&&u.uid==10003&&u.gid==10003);credentials=1;}
    }
    assert(fd>=0&&credentials);live(birth);
    assert((fcntl(fd,F_GETFL)&O_ACCMODE)==O_RDONLY&&fcntl(fd,F_GET_SEALS)==(F_SEAL_WRITE|F_SEAL_GROW|F_SEAL_SHRINK|F_SEAL_SEAL));
    PolicyCandidate p;struct stat st;assert(fstat(fd,&st)==0&&st.st_size==(off_t)sizeof(p)&&pread(fd,&p,sizeof(p),0)==sizeof(p));
    S03RawBootstrap expected;s03_read_raw_bootstrap(raw_bootstrap_fd,&expected);assert(exact_unaccepted_projection(&p,&expected)&&!memcmp(p.host_decision_request,request,sizeof(request)));
    print_record("POLICY_ISSUER_APPROVAL_CLAIM_RECEIVED_KERNEL_ORIGIN_VERIFIED",fd,&p,child);live(birth);
    char handoff[160];int count=snprintf(handoff,sizeof(handoff),"HOST_POLICY_INPUT_REVIEW_READY PID=%ld FD=%u SIZE=%zu\n",(long)child,sender_fd,sizeof(p));assert(count>0&&(size_t)count<sizeof(handoff)&&write(1,handoff,(size_t)count)==count);
    assert(fgets(command,sizeof(command),stdin)&&!strcmp(command,"CONTINUE_WITHOUT_POLICY_ACCEPTANCE\n"));live(birth);
    assert(send(channels[0],"A",1,MSG_NOSIGNAL)==1);close(channels[0]);int status;assert(waitpid(child,&status,0)==child&&WIFEXITED(status)&&WEXITSTATUS(status)==0);close(birth);
    return fd;
}
