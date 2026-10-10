/* Disposable native lifecycle prototype. Synthetic fixture storage, not V043 parity. */
#include "postgres.h"
#include "fmgr.h"
#include "commands/event_trigger.h"
#include "commands/dbcommands.h"
#include "executor/spi.h"
#include "catalog/pg_type_d.h"
#include "miscadmin.h"
#include "utils/builtins.h"
#include "utils/timestamp.h"
#include "utils/timeout.h"
#include "storage/proc.h"
#include <sys/time.h>
#include "protocol.h"
PG_MODULE_MAGIC;
PG_FUNCTION_INFO_V1(flooow_test_login);
void _PG_init(void);
Datum flooow_test_login(PG_FUNCTION_ARGS);
static test_context ctx;
static int expected_receiver=-1;
static int prepared=0;
static TimeoutId enrollment_timer=MAX_TIMEOUTS;
static void enrollment_interrupt(void){InterruptPending=true;QueryCancelPending=true;}
static void die(const char *reason){ereport(FATAL,(errmsg("FLOOOW_TEST_ENROLLMENT_DENIED: %s",reason)));}
void _PG_init(void){
    const char *s,*r;int fd,seals;
    if(!process_shared_preload_libraries_in_progress)die("mandatory shared preload absent");
    s=getenv("FLOOOW_TEST_BOOT_FD");r=getenv("FLOOOW_TEST_RECEIVER_FD");
    if(!s||!r)die("inherited context absent");fd=atoi(s);expected_receiver=atoi(r);
    seals=fcntl(fd,F_GET_SEALS);
    if(seals<0 || (seals&(F_SEAL_WRITE|F_SEAL_GROW|F_SEAL_SHRINK|F_SEAL_SEAL))!=(F_SEAL_WRITE|F_SEAL_GROW|F_SEAL_SHRINK|F_SEAL_SEAL))die("unsealed context");
    if(pread(fd,&ctx,sizeof(ctx),0)!=(ssize_t)sizeof(ctx)||ctx.magic!=0x00900001||!ctx.experimental_abort_us||ctx.experimental_abort_us>60000000||!alive(expected_receiver))die("invalid bootstrap");
    prepared=1;
}
Datum flooow_test_login(PG_FUNCTION_ARGS){
    uint64_t started=tick_us(),deadline;
    Oid auth;char *role,*db;int slot=-1,fd=-1,self=-1,peer=-1,one=1;
    request_fields r={0};unsigned char wire[FRAME_MAX],reply[80],digest[32];size_t n;
    struct sockaddr_un address={.sun_family=AF_UNIX};struct ucred cred;socklen_t clen=sizeof(cred),plen=sizeof(peer);int repeated=0;
    if(!CALLED_AS_EVENT_TRIGGER(fcinfo)||strcmp(((EventTriggerData *)fcinfo->context)->event,"login"))die("private login context required");
    auth=GetAuthenticatedUserId();role=GetUserNameFromId(auth,false);db=get_database_name(MyDatabaseId);
    for(int i=0;i<4;i++)if(auth==ctx.role_oid[i]||!strcmp(role,ctx.role_name[i])){if(slot!=-1)die("ambiguous roster");slot=i;}
    if(slot<0)PG_RETURN_POINTER(NULL); /* Unmanaged test ADMIN, no expansion. */
    if(!prepared||!MyProc||MyBackendType!=B_BACKEND||getpid()!=MyProcPid||GetSessionUserId()!=auth||!alive(expected_receiver))die("invalid native process");
    deadline=started+ctx.experimental_abort_us;
    r.slot=(uint8_t)(slot+1);r.role=auth;r.db=MyDatabaseId;
    strlcpy(r.role_name,role,sizeof(r.role_name));strlcpy(r.db_name,db,sizeof(r.db_name));
    r.backend_start=MyStartTimestamp;r.postmaster_start=PgStartTime;
    memcpy(r.binding,ctx.binding,16);memcpy(r.deployment,ctx.deployment,16);memcpy(r.incarnation,ctx.incarnation,16);memcpy(r.epoch,ctx.epoch,32);memcpy(r.fingerprint,ctx.fingerprint,32);memcpy(r.policy,ctx.policy,32);
    if(!context_matches(&ctx,&r))die("allocated identity mismatch");
    health_gate gate;if(!read_gate(&ctx,&gate))die("independent eligibility absent");
    /* Current server catalog + protected synthetic header, no raw service access. */
    struct sigaction signal_before,signal_after;struct itimerval alarm_before,alarm_after;
    bool statement_active=get_timeout_active(STATEMENT_TIMEOUT);TimestampTz statement_finish=statement_active?get_timeout_finish_time(STATEMENT_TIMEOUT):0;
    sigaction(SIGALRM,NULL,&signal_before);getitimer(ITIMER_REAL,&alarm_before);
    /* Bound SPI lock waits too; this test control is not a numeric policy grant. */
    {uint64_t current=tick_us();if(current>=deadline)die("experimental abort elapsed before SPI");if(enrollment_timer==MAX_TIMEOUTS)enrollment_timer=RegisterTimeout(USER_TIMEOUT,enrollment_interrupt);enable_timeout_after(enrollment_timer,(int)((deadline-current+999)/1000));}
    PG_TRY();
    {
    if(SPI_connect()!=SPI_OK_CONNECT)die("SPI unavailable");
    {
        Oid types[3]={OIDOID,TEXTOID,INT4OID};Datum vals[3]={ObjectIdGetDatum(auth),CStringGetTextDatum(role),Int32GetDatum(slot+1)};
        int rc=SPI_execute_with_args("SELECT 1 FROM public.flooow_test_binding h JOIN pg_catalog.pg_roles r ON r.oid=h.role_oid WHERE h.role_oid=$1 AND h.role_name=$2 AND h.slot=$3 AND r.rolname=h.role_name AND r.rolcanlogin AND NOT r.rolinherit AND NOT r.rolsuper AND NOT r.rolcreaterole AND NOT r.rolcreatedb AND NOT r.rolreplication AND NOT r.rolbypassrls AND NOT EXISTS(SELECT 1 FROM pg_catalog.pg_auth_members m WHERE m.member=r.oid OR m.roleid=r.oid)",3,types,vals,NULL,true,2);
        if(rc!=SPI_OK_SELECT||SPI_processed!=1)die("header absent or role invalid");
    }
    SPI_finish();disable_timeout(enrollment_timer,false);
    }
    PG_CATCH();{disable_timeout(enrollment_timer,false);PG_RE_THROW();}
    PG_END_TRY();if(tick_us()>=deadline)die("experimental abort elapsed");
    self=syscall(SYS_pidfd_open,getpid(),0);if(self<0||!alive(self))die("self anchor failure");
retry_fixture_anchor:
    {
        struct stat directory,endpoint;
        if(lstat(TEST_DIR,&directory)||!S_ISDIR(directory.st_mode)||directory.st_uid!=getuid()||(directory.st_mode&0777)!=0700||lstat(TEST_SOCKET,&endpoint)||!S_ISSOCK(endpoint.st_mode)||endpoint.st_uid!=getuid()||(endpoint.st_mode&0777)!=0600)die("unsafe or absent namespace");
    }
    fd=socket(AF_UNIX,SOCK_SEQPACKET|SOCK_CLOEXEC|SOCK_NONBLOCK,0);if(fd<0)die("socket failure");
    strcpy(address.sun_path,TEST_SOCKET);
    if(connect(fd,(struct sockaddr *)&address,sizeof(address))<0)die("receiver absent");
    if(getsockopt(fd,SOL_SOCKET,SO_PEERCRED,&cred,&clen)||cred.uid!=getuid()||cred.gid!=getgid()||getsockopt(fd,SOL_SOCKET,SO_PEERPIDFD,&peer,&plen)||!anchor_equal(peer,expected_receiver)||!alive(peer))die("receiver identity mismatch");
    if(setsockopt(fd,SOL_SOCKET,SO_PASSPIDFD,&one,sizeof(one))||setsockopt(fd,SOL_SOCKET,SO_PASSCRED,&one,sizeof(one)))die("strong ancillary unavailable");
    /* ADMIN-owned fixture faults; never SQL identity arguments or service GUCs. */
    if(access(TEST_DIR "/wrong-deployment",F_OK)==0)r.deployment[0]^=1;
    if(access(TEST_DIR "/wrong-incarnation",F_OK)==0)r.incarnation[0]^=1;
    if(access(TEST_DIR "/stale-epoch",F_OK)==0)r.epoch[0]^=1;
    if(access(TEST_DIR "/wrong-database",F_OK)==0)r.db++;
    if(access(TEST_DIR "/wrong-slot",F_OK)==0)r.slot=r.slot==4?1:r.slot+1;
    n=encode_request(wire,&r);if(access(TEST_DIR "/bad-version",F_OK)==0)wire[5]=2;
    if(access(TEST_DIR "/partial-frame",F_OK)==0)n--;
    SHA256(wire,n,digest);
    if(!wait_fd(fd,POLLOUT,deadline)||!send_anchor(fd,wire,n,self)||!wait_fd(fd,POLLIN,deadline))die("no finite ACCEPT");
    {
        union{struct cmsghdr align;char bytes[256];} c={0};struct iovec i={.iov_base=reply,.iov_len=sizeof(reply)};
        struct msghdr m={.msg_iov=&i,.msg_iovlen=1,.msg_control=c.bytes,.msg_controllen=sizeof(c.bytes)};
        ssize_t got=recvmsg(fd,&m,MSG_CMSG_CLOEXEC|MSG_DONTWAIT);int sender=-1,cc=0,pc=0,extra=0;struct ucred mc={0};
        for(struct cmsghdr *x=CMSG_FIRSTHDR(&m);x;x=CMSG_NXTHDR(&m,x)){
            if(x->cmsg_level==SOL_SOCKET && x->cmsg_type==SCM_PIDFD && x->cmsg_len==CMSG_LEN(sizeof(int))){memcpy(&sender,CMSG_DATA(x),sizeof(int));pc++;}
            else if(x->cmsg_level==SOL_SOCKET && x->cmsg_type==SCM_CREDENTIALS && x->cmsg_len==CMSG_LEN(sizeof(mc))){memcpy(&mc,CMSG_DATA(x),sizeof(mc));cc++;}
            else extra++;
        }
        if(got!=76||m.msg_flags&(MSG_TRUNC|MSG_CTRUNC)||extra||pc!=1||cc!=1||mc.uid!=cred.uid||mc.gid!=cred.gid||!anchor_equal(sender,peer)||!alive(sender)||memcmp(reply,"G3F4\0\1\2\0\0\0\0\100",12)||memcmp(reply+12,ctx.epoch,32)||memcmp(reply+44,digest,32)||tick_us()>=deadline||!alive(self))die("invalid or denied ACK");
        close(sender);
    }
    close(peer);close(fd);
    if(!repeated && access(TEST_DIR "/repeat-anchor",F_OK)==0){repeated=1;goto retry_fixture_anchor;}
    close(self);sigaction(SIGALRM,NULL,&signal_after);getitimer(ITIMER_REAL,&alarm_after);
    bool preserved=statement_active==get_timeout_active(STATEMENT_TIMEOUT)&&(!statement_active||statement_finish==get_timeout_finish_time(STATEMENT_TIMEOUT))&&signal_before.sa_handler==signal_after.sa_handler&&signal_before.sa_flags==signal_after.sa_flags&&!get_timeout_active(enrollment_timer);
    for(int sig=1;sig<NSIG;sig++)if(sigismember(&signal_before.sa_mask,sig)!=sigismember(&signal_after.sa_mask,sig))preserved=false;
    if(!statement_active&&!alarm_before.it_value.tv_sec&&!alarm_before.it_value.tv_usec&&(alarm_after.it_value.tv_sec||alarm_after.it_value.tv_usec))preserved=false;
    ereport(LOG,(errmsg("FLOOOW_TEST_TIMEOUT_RESTORATION preserved=%s custom_active=%s",preserved?"YES":"NO",get_timeout_active(enrollment_timer)?"YES":"NO")));
    if(!preserved)die("timeout restoration invariant failed");
    ereport(LOG,(errmsg("FLOOOW_TEST_ENROLLMENT_ACCEPT role=%u database=%u total_us=%llu",auth,MyDatabaseId,(unsigned long long)(tick_us()-started))));
    PG_RETURN_POINTER(NULL);
}
