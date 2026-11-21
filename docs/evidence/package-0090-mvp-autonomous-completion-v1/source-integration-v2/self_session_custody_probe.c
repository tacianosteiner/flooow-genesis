#define _GNU_SOURCE
#include <assert.h>
#include <dirent.h>
#include <errno.h>
#include <fcntl.h>
#include <grp.h>
#include <libpq-fe.h>
#include <linux/audit.h>
#include <linux/capability.h>
#include <linux/filter.h>
#include <linux/seccomp.h>
#include <openssl/sha.h>
#include <stddef.h>
#include <poll.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/prctl.h>
#include <sys/resource.h>
#include <sys/socket.h>
#include <sys/stat.h>
#include <sys/syscall.h>
#include <sys/wait.h>
#include <time.h>
#include <unistd.h>
int s03_publish_immutable(const void *, size_t);
static void no_capabilities(void) {
    struct __user_cap_header_struct header={.version=_LINUX_CAPABILITY_VERSION_3,.pid=0};
    struct __user_cap_data_struct data[2]={{0},{0}};
    assert(syscall(SYS_capget,&header,data)==0);
    for(unsigned i=0;i<2;++i)assert(!(data[i].effective|data[i].permitted|data[i].inheritable));
}
static uint64_t boottime_us(void) {
    struct timespec value;assert(clock_gettime(CLOCK_BOOTTIME,&value)==0);
    return (uint64_t)value.tv_sec*1000000+(uint64_t)value.tv_nsec/1000;
}
static void print_observation(const char *scope,const unsigned char *bytes,size_t count,uint64_t start,uint64_t finish) {
    unsigned char digest[SHA256_DIGEST_LENGTH];assert(SHA256(bytes,count,digest));
    /* Only the fixed four public self-row values. Never credentials or bridge facts. */
    char line[1600];const char *hex="0123456789abcdef";
    int prefix=snprintf(line,sizeof(line),"{\"kind\":\"%s\",\"pid\":%ld,\"start_boottime_us\":%llu,\"finish_boottime_us\":%llu,\"payload_hex\":\"",scope,(long)getpid(),(unsigned long long)start,(unsigned long long)finish);
    assert(prefix>0&&(size_t)prefix+count*2+160<sizeof(line));size_t offset=(size_t)prefix;
    for(size_t i=0;i<count;++i){line[offset++]=hex[bytes[i]>>4];line[offset++]=hex[bytes[i]&15];}
    const char middle[]="\",\"sha256\":\"";memcpy(line+offset,middle,sizeof(middle)-1);offset+=sizeof(middle)-1;
    for(size_t i=0;i<sizeof(digest);++i){line[offset++]=hex[digest[i]>>4];line[offset++]=hex[digest[i]&15];}
    const char suffix[]="\",\"source_acceptance\":\"NOT_ESTABLISHED\"}\n";memcpy(line+offset,suffix,sizeof(suffix)-1);offset+=sizeof(suffix)-1;
    /* One bounded pipe write preserves a complete line across the two children. */
    assert(write(STDOUT_FILENO,line,offset)==(ssize_t)offset);
}

/* Engineering probe only. No accepted issuer, target bridge, S02 roster,
 * authenticated observer role, source admission, or canonical input output.
 * Spawn/exec readers BEFORE acquiring SQL connection; never pass SQL socket.
 * Public synthetic test password is not a production credential/custody proof. */
static void ready(int fd, short events) {
    struct pollfd p = {.fd=fd,.events=events};
    assert(poll(&p, 1, 10000) == 1 && (p.revents & events));
}
static void inventory(int export) {
    DIR *dir = opendir("/proc/self/fd"); assert(dir);
    struct dirent *entry;
    while ((entry = readdir(dir))) {
        if (entry->d_name[0] == '.') continue;
        int fd = atoi(entry->d_name);
        assert(fd <= 3 || fd == export || fd == dirfd(dir));
    }
    closedir(dir);
}
static void restrict_probe(void) {
#define ALLOW_NR(n) BPF_JUMP(BPF_JMP|BPF_JEQ|BPF_K, (n), 0, 1), BPF_STMT(BPF_RET|BPF_K, SECCOMP_RET_ALLOW)
    struct sock_filter filter[] = {
        BPF_STMT(BPF_LD|BPF_W|BPF_ABS, offsetof(struct seccomp_data,arch)),
        BPF_JUMP(BPF_JMP|BPF_JEQ|BPF_K, AUDIT_ARCH_X86_64, 1, 0),
        BPF_STMT(BPF_RET|BPF_K, SECCOMP_RET_KILL_PROCESS),
        BPF_STMT(BPF_LD|BPF_W|BPF_ABS, offsetof(struct seccomp_data,nr)),
        ALLOW_NR(SYS_read), ALLOW_NR(SYS_write), ALLOW_NR(SYS_close),
        ALLOW_NR(SYS_pread64), ALLOW_NR(SYS_fcntl), ALLOW_NR(SYS_fstat),
        ALLOW_NR(SYS_newfstatat), ALLOW_NR(SYS_poll), ALLOW_NR(SYS_ppoll),
        ALLOW_NR(SYS_recvmsg), ALLOW_NR(SYS_sendmsg), ALLOW_NR(SYS_sendto),
        ALLOW_NR(SYS_exit), ALLOW_NR(SYS_exit_group), ALLOW_NR(SYS_rt_sigreturn),
        ALLOW_NR(SYS_brk), ALLOW_NR(SYS_mmap), ALLOW_NR(SYS_mprotect),
        ALLOW_NR(SYS_munmap), ALLOW_NR(SYS_futex), ALLOW_NR(SYS_clock_gettime),
        ALLOW_NR(SYS_getpid),
        BPF_STMT(BPF_RET|BPF_K, SECCOMP_RET_ERRNO | EPERM)
    };
    struct sock_fprog program = {.len=(unsigned short)(sizeof(filter)/sizeof(filter[0])), .filter=filter};
    assert(prctl(PR_SET_NO_NEW_PRIVS,1,0,0,0)==0);
    assert(prctl(PR_SET_SECCOMP,SECCOMP_MODE_FILTER,&program)==0);
#undef ALLOW_NR
}
static int probe(unsigned role) {
    assert((role==1||role==2)&&getuid()==10000+role&&getgid()==10000+role);
    no_capabilities();
    assert(prctl(PR_SET_DUMPABLE, 0) == 0);
    struct rlimit limit={64,64};assert(setrlimit(RLIMIT_NOFILE,&limit)==0);
    inventory(-1);
    for(int i=0;i<3;++i){struct stat st;assert(fstat(i,&st)==0&&!S_ISSOCK(st.st_mode));}
    char parentfds[80]; snprintf(parentfds,sizeof(parentfds),"/proc/%ld/fd",(long)getppid());
    DIR *parent = opendir(parentfds); assert(!parent && errno == EACCES);
    /* Separate OS principal cannot reach the Reader socket even before seccomp. */
    int protected_directory=open("/tmp/s03-socket",O_RDONLY|O_DIRECTORY);
    assert(protected_directory==-1&&errno==EACCES);
    restrict_probe();
    /* Negative capability proof occurs before ready/SQL acquisition. Default
     * deny includes new paths, sockets, exec, process-memory and descriptor theft. */
    assert(socket(AF_UNIX,SOCK_STREAM,0)==-1&&errno==EPERM);
    assert(syscall(SYS_connect,-1,NULL,0)==-1&&errno==EPERM);
    assert(syscall(SYS_openat2,-1,NULL,NULL,0)==-1&&errno==EPERM);
    assert(open("/tmp/s03-socket",O_RDONLY)==-1&&errno==EPERM);
    assert(syscall(SYS_execveat,-1,NULL,NULL,NULL,0)==-1&&errno==EPERM);
    assert(syscall(SYS_ptrace,0,0,0,0)==-1&&errno==EPERM);
    assert(syscall(SYS_process_vm_readv,0,NULL,0,NULL,0,0)==-1&&errno==EPERM);
    assert(syscall(SYS_pidfd_getfd,-1,0,0)==-1&&errno==EPERM);
    assert(send(3, "R", 1, MSG_NOSIGNAL) == 1);
    char byte;
    union { struct cmsghdr align; char bytes[CMSG_SPACE(sizeof(int))]; } control = {0};
    struct iovec iov = {.iov_base=&byte,.iov_len=1};
    struct msghdr msg = {.msg_iov=&iov,.msg_iovlen=1,.msg_control=control.bytes,.msg_controllen=sizeof(control.bytes)};
    ready(3, POLLIN);
    assert(recvmsg(3, &msg, MSG_CMSG_CLOEXEC) == 1 && byte == 'E');
    assert(!(msg.msg_flags & (MSG_CTRUNC | MSG_TRUNC)));
    struct cmsghdr *c = CMSG_FIRSTHDR(&msg);
    assert(c && c->cmsg_level == SOL_SOCKET && c->cmsg_type == SCM_RIGHTS &&
           c->cmsg_len == CMSG_LEN(sizeof(int)) && !CMSG_NXTHDR(&msg,c));
    int fd; memcpy(&fd, CMSG_DATA(c), sizeof(fd));
    uint64_t started=boottime_us();
    assert((fcntl(fd, F_GETFL) & O_ACCMODE) == O_RDONLY);
    assert(fcntl(fd, F_GETFD) & FD_CLOEXEC);
    assert(fcntl(fd, F_GET_SEALS) == (F_SEAL_WRITE | F_SEAL_GROW | F_SEAL_SHRINK | F_SEAL_SEAL));
    for(int i=4;i<64;++i)if(i!=fd)assert(fcntl(i,F_GETFD)==-1&&errno==EBADF);
    unsigned char bytes[512]; ssize_t n = pread(fd, bytes, sizeof(bytes), 0);
    assert(n > 4 && n < (ssize_t)sizeof(bytes) && bytes[0] == 4);
    size_t offset = 1;
    for (unsigned i=0; i<4; ++i) {
        assert(offset < (size_t)n);
        unsigned len = bytes[offset++]; assert(len && len <= 63 && offset+len <= (size_t)n);
        for (unsigned j=0;j<len;++j) assert(bytes[offset+j] >= 32 && bytes[offset+j] < 127);
        offset += len;
    }
    assert(offset == (size_t)n);
    uint64_t finished=boottime_us();
    print_observation("RAW_PUBLIC4_EXPORT_CHILD_PROBE",bytes,(size_t)n,started,finished);
    close(fd);
    assert(send(3, "V", 1, MSG_NOSIGNAL) == 1);
    close(3); return 0;
}
static pid_t launch(const char *self, int *channel, unsigned role) {
    int pair[2]; assert(socketpair(AF_UNIX, SOCK_SEQPACKET | SOCK_CLOEXEC,0,pair)==0);
    pid_t child=fork(); assert(child>=0);
    if (!child) {
        close(pair[0]); assert(dup2(pair[1],3)==3);
        assert(fcntl(3,F_SETFD,0)==0);
        assert(syscall(SYS_close_range,4u,~0u,0u)==0);
        assert(setgroups(0,NULL)==0&&setgid(10000+role)==0&&setuid(10000+role)==0);
        char *const args[]={(char *)self,"--probe",role==1?"1":"2",NULL};
        char *const env[]={"PATH=/usr/bin:/bin","LC_ALL=C",NULL};
        execve(self,args,env); _exit(127);
    }
    close(pair[1]); *channel=pair[0];
    ready(*channel,POLLIN); char byte;
    assert(recv(*channel,&byte,1,0)==1 && byte=='R');
    return child;
}
static void send_export(int channel,int fd) {
    char byte='E';
    union {struct cmsghdr align; char bytes[CMSG_SPACE(sizeof(int))];} control={0};
    struct iovec iov={.iov_base=&byte,.iov_len=1};
    struct msghdr msg={.msg_iov=&iov,.msg_iovlen=1,.msg_control=control.bytes,.msg_controllen=sizeof(control.bytes)};
    struct cmsghdr *c=CMSG_FIRSTHDR(&msg);
    c->cmsg_level=SOL_SOCKET;c->cmsg_type=SCM_RIGHTS;c->cmsg_len=CMSG_LEN(sizeof(int));
    memcpy(CMSG_DATA(c),&fd,sizeof(fd));
    assert(sendmsg(channel,&msg,MSG_NOSIGNAL)==1);
}
int main(int argc,char **argv) {
    if (argc==3 && !strcmp(argv[1],"--probe")) return probe((unsigned)atoi(argv[2]));
    assert(argc==1&&getuid()==0&&prctl(PR_SET_DUMPABLE,0)==0);
    int channels[2]; pid_t children[2];
    children[0]=launch(argv[0],&channels[0],1);
    children[1]=launch(argv[0],&channels[1],2);
    assert(setgroups(0,NULL)==0&&setgid(10000)==0&&setuid(10000)==0);
    no_capabilities();
    assert(prctl(PR_SET_DUMPABLE,0)==0);
    assert(clearenv()==0&&setenv("PATH","/usr/bin:/bin",1)==0&&setenv("LC_ALL","C",1)==0);
    /* Exact local test endpoint, cleared environment, no arbitrary SQL/selectors. */
    PGconn *connection=PQconnectdb("host=/tmp/s03-socket port=5432 dbname=postgres user=flooow_reader password=PUBLIC_SYNTHETIC_PROBE_ONLY passfile=/dev/null sslmode=disable gssencmode=disable require_auth=scram-sha-256 options='' connect_timeout=5 application_name=s03_custody_probe");
    assert(PQstatus(connection)==CONNECTION_OK && PQconnectionUsedPassword(connection));
    assert(fcntl(PQsocket(connection),F_GETFD)&FD_CLOEXEC);
    PGresult *role=PQexec(connection,"SELECT rolcanlogin AND NOT rolsuper AND NOT rolinherit AND NOT rolcreaterole AND NOT rolcreatedb AND NOT rolreplication AND NOT rolbypassrls AND NOT EXISTS (SELECT 1 FROM pg_auth_members WHERE member=(SELECT oid FROM pg_roles WHERE rolname=current_user)) FROM pg_roles WHERE rolname=current_user");
    assert(PQresultStatus(role)==PGRES_TUPLES_OK && PQntuples(role)==1 && !strcmp(PQgetvalue(role,0,0),"t"));PQclear(role);
    PGresult *begin=PQexec(connection,"BEGIN READ ONLY");assert(PQresultStatus(begin)==PGRES_COMMAND_OK);PQclear(begin);
    uint64_t started=boottime_us();
    PGresult *facts=PQexec(connection,"SELECT datid::text,usesysid::text,pid::text,usename FROM pg_catalog.pg_stat_activity WHERE pid=pg_catalog.pg_backend_pid()");
    assert(PQresultStatus(facts)==PGRES_TUPLES_OK && PQntuples(facts)==1 && PQnfields(facts)==4);
    assert(!strcmp(PQgetvalue(facts,0,3),"flooow_reader"));
    unsigned char bytes[512];size_t offset=0;bytes[offset++]=4;
    for(int i=0;i<4;++i){assert(!PQgetisnull(facts,0,i));int n=PQgetlength(facts,0,i);assert(n>0&&n<=63);bytes[offset++]=(unsigned char)n;memcpy(bytes+offset,PQgetvalue(facts,0,i),(size_t)n);offset+=(size_t)n;}
    int backend=PQbackendPID(connection);PQclear(facts);
    uint64_t finished=boottime_us();
    print_observation("RAW_PUBLIC4_SELF_SESSION_ACQUISITION",bytes,offset,started,finished);
    /* Local bytes have one writer; export helper seals only after this copy. */
    int exported=s03_publish_immutable(bytes,offset);assert(exported>=0);
    for(int i=0;i<2;++i)send_export(channels[i],exported);
    for(int i=0;i<2;++i){ready(channels[i],POLLIN);char byte;assert(recv(channels[i],&byte,1,0)==1&&byte=='V');close(channels[i]);int status;assert(waitpid(children[i],&status,0)==children[i]&&WIFEXITED(status)&&WEXITSTATUS(status)==0);}
    PGresult *retained=PQexec(connection,"SELECT pg_catalog.pg_backend_pid()");
    assert(PQresultStatus(retained)==PGRES_TUPLES_OK&&atoi(PQgetvalue(retained,0,0))==backend);PQclear(retained);
    close(exported);PQfinish(connection);
    puts("PASS SELF_SESSION_PGSTAT_CUSTODY_PROBE: distinct OS principals10000/10001/10002, Reader socket DAC rejects children before seccomp, required SCRAM, nonprivileged/zero memberships, children exec-ready and seccomp before SQL, sealed public4 self-row export only, child fd inventory, parent fd access denied, same retained backend; each child denies8 reacquisition syscalls");
    puts("NOT_ESTABLISHED: S02 roster, S03 bridge/MyStartTimestamp/B_BACKEND, issuer, source acceptance, role enrollment, credential custody, generation, canonical admission");
    return 0;
}
