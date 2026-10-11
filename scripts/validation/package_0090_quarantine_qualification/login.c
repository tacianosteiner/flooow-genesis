/* Disposable native lifecycle prototype. Synthetic fixture storage, not V043 parity. */
#include "postgres.h"
#include "fmgr.h"
#include "commands/event_trigger.h"
#include "commands/dbcommands.h"
/* No GSS API is used. PG18 Port deliberately preserves the pointer ABI with
 * ENABLE_GSS unset (libpq-be.h); avoid adding unavailable development deps. */
#undef ENABLE_GSS
#include "libpq/auth.h"
#include "libpq/libpq-be.h"
#include "utils/acl.h"
#include "executor/spi.h"
#include "executor/executor.h"
#include "tcop/utility.h"
#include "catalog/pg_type_d.h"
#include "miscadmin.h"
#include "utils/builtins.h"
#include "utils/timestamp.h"
#include "utils/timeout.h"
#include "storage/proc.h"
#include <sys/time.h>
#include "protocol.h"
#include "quarantine.h"
static observation_state *observed;static int expected_observer=-1;
static int expected_supervisor=-1,expected_postmaster=-1;
PG_MODULE_MAGIC;
PG_FUNCTION_INFO_V1(flooow_test_login);
void _PG_init(void);
Datum flooow_test_login(PG_FUNCTION_ARGS);
static test_context ctx;
static int expected_receiver=-1;
static int prepared=0;
static ClientAuthentication_hook_type previous_auth_hook;
static int pending_anchor=-1;
static request_fields pending_identity;
static int enrollment_in_progress;
static ExecutorStart_hook_type previous_executor_hook;
static ProcessUtility_hook_type previous_utility_hook;
static TimeoutId enrollment_timer=MAX_TIMEOUTS;
static void enrollment_interrupt(void){InterruptPending=true;QueryCancelPending=true;}
static void enrollment_deny(const char *reason){ereport(FATAL,(errmsg("FLOOOW_TEST_ENROLLMENT_DENIED: %s",reason)));}
static void require_enrolled_execution(void){
    if(enrollment_in_progress||!prepared||!IsUnderPostmaster||MyBackendType!=B_BACKEND)return;
    Oid auth=GetAuthenticatedUserId();if(!OidIsValid(auth))return;char *name=GetUserNameFromId(auth,false);int governed=0;
    for(unsigned i=0;i<4;i++)if(auth==ctx.role_oid[i]||!strcmp(name,ctx.role_name[i]))governed=1;
    if(!governed)return;
    int self=syscall(SYS_pidfd_open,getpid(),0);health_gate gate;
    int ok=self>=0&&observation_enrolled(observed,self,&pending_identity)&&alive(expected_receiver)&&alive(expected_observer)&&alive(expected_supervisor)&&alive(expected_postmaster)&&!atomic_load(&observed->quarantined)&&tick_us()-atomic_load(&observed->observer_progress)<=10000000&&tick_us()-atomic_load(&observed->receiver_progress)<=10000000&&tick_us()-atomic_load(&observed->supervisor_progress)<=10000000&&read_gate(&ctx,&gate);
    if(self>=0)close(self);if(!ok)enrollment_deny("mandatory enrolled execution guard denied");
}
static void guarded_executor_start(QueryDesc *query,int flags){require_enrolled_execution();if(previous_executor_hook)previous_executor_hook(query,flags);else standard_ExecutorStart(query,flags);}
static void guarded_utility(PlannedStmt *p,const char *text,bool read_only,ProcessUtilityContext context,ParamListInfo parameters,QueryEnvironment *environment,DestReceiver *destination,QueryCompletion *completion){
    require_enrolled_execution();if(previous_utility_hook)previous_utility_hook(p,text,read_only,context,parameters,environment,destination,completion);else standard_ProcessUtility(p,text,read_only,context,parameters,environment,destination,completion);
}
static void observe_authenticated_birth(Port *port,int status){
    if(previous_auth_hook)previous_auth_hook(port,status);if(status!=STATUS_OK)return;
    Oid role_oid=get_role_oid(port->user_name,true);int slot=-1;
    for(int j=0;j<4;j++)if(role_oid==ctx.role_oid[j]||!strcmp(port->user_name,ctx.role_name[j])){if(slot!=-1)enrollment_deny("ambiguous authenticated roster");slot=j;}
    if(slot<0)return;
    request_fields *r=&pending_identity;memset(r,0,sizeof(*r));r->slot=slot+1;r->role=role_oid;r->db=get_database_oid(port->database_name,true);
    if(!OidIsValid(role_oid)||!OidIsValid(r->db))enrollment_deny("authenticated catalog identity absent");
    strlcpy(r->role_name,GetUserNameFromId(role_oid,false),64);strlcpy(r->db_name,get_database_name(r->db),64);r->backend_start=MyStartTimestamp;r->postmaster_start=PgStartTime;
    memcpy(r->binding,ctx.binding,16);memcpy(r->deployment,ctx.deployment,16);memcpy(r->incarnation,ctx.incarnation,16);memcpy(r->epoch,ctx.epoch,32);memcpy(r->fingerprint,ctx.fingerprint,32);memcpy(r->policy,ctx.policy,32);
    if(!context_matches(&ctx,r))enrollment_deny("allocated identity mismatch");
    health_gate gate;if(!read_gate(&ctx,&gate))enrollment_deny("authenticated pending context denied");
    if(access(TEST_DIR "/skip-auth-observation",F_OK)==0)return; /* root fixture only */
    pending_anchor=syscall(SYS_pidfd_open,getpid(),0);
    if(pending_anchor<0||!observation_pending(&ctx,observed,expected_observer,pending_anchor,r,tick_us()+ctx.experimental_abort_us))enrollment_deny("authenticated birth observation denied");
    if(access(TEST_DIR "/auth-observation-completion-pause",F_OK)==0){struct timespec pause={0,200000000};nanosleep(&pause,NULL);} /* experimental schedule only */
    ereport(LOG,(errmsg("FLOOOW_TEST_PENDING_AUTH_ANCHOR_ONLY role=%u",role_oid)));
}
void _PG_init(void){
    const char *s,*r;int fd,seals;
    if(!process_shared_preload_libraries_in_progress)enrollment_deny("mandatory shared preload absent");
    s=getenv("FLOOOW_TEST_BOOT_FD");r=getenv("FLOOOW_TEST_RECEIVER_FD");
    if(!s||!r)enrollment_deny("inherited context absent");fd=atoi(s);expected_receiver=atoi(r);
    seals=fcntl(fd,F_GET_SEALS);
    if(seals<0 || (seals&(F_SEAL_WRITE|F_SEAL_GROW|F_SEAL_SHRINK|F_SEAL_SEAL))!=(F_SEAL_WRITE|F_SEAL_GROW|F_SEAL_SHRINK|F_SEAL_SEAL))enrollment_deny("unsealed context");
    if(pread(fd,&ctx,sizeof(ctx),0)!=(ssize_t)sizeof(ctx)||ctx.magic!=0x00900001||!ctx.experimental_abort_us||ctx.experimental_abort_us>60000000||!alive(expected_receiver))enrollment_deny("invalid bootstrap");
    const char *obs=getenv("FLOOOW_TEST_OBSERVER_FD"),*state=getenv("FLOOOW_TEST_OBSERVATION_FD");
    if(!obs||!state)enrollment_deny("independent observation absent");expected_observer=atoi(obs);int statefd=atoi(state);observed=observation_map(statefd,0);close(statefd);if(!observed||!alive(expected_observer))enrollment_deny("invalid independent observer");
    const char *supervisor=getenv("FLOOOW_TEST_SUPERVISOR_FD");if(!supervisor)enrollment_deny("retained supervisor absent");expected_supervisor=atoi(supervisor);
    expected_postmaster=syscall(SYS_pidfd_open,getpid(),0);if(!alive(expected_supervisor)||!alive(expected_postmaster))enrollment_deny("retained generation invalid");
    prepared=1;
    previous_auth_hook=ClientAuthentication_hook;ClientAuthentication_hook=observe_authenticated_birth;
    previous_executor_hook=ExecutorStart_hook;ExecutorStart_hook=guarded_executor_start;
    previous_utility_hook=ProcessUtility_hook;ProcessUtility_hook=guarded_utility;
}
Datum flooow_test_login(PG_FUNCTION_ARGS){
    uint64_t started=tick_us(),deadline;
    Oid auth;char *role,*db;int slot=-1,fd=-1,self=-1,peer=-1,one=1;
    request_fields r={0};unsigned char wire[FRAME_MAX],reply[80],digest[32];size_t n;
    struct sockaddr_un address={.sun_family=AF_UNIX};struct ucred cred;socklen_t clen=sizeof(cred),plen=sizeof(peer);int repeated=0;
    if(!CALLED_AS_EVENT_TRIGGER(fcinfo)||strcmp(((EventTriggerData *)fcinfo->context)->event,"login"))enrollment_deny("private login context required");
    auth=GetAuthenticatedUserId();role=GetUserNameFromId(auth,false);db=get_database_name(MyDatabaseId);
    for(int i=0;i<4;i++)if(auth==ctx.role_oid[i]||!strcmp(role,ctx.role_name[i])){if(slot!=-1)enrollment_deny("ambiguous roster");slot=i;}
    if(slot<0)PG_RETURN_POINTER(NULL); /* Unmanaged test ADMIN, no expansion. */
    enrollment_in_progress=1;
    if(!prepared||!MyProc||MyBackendType!=B_BACKEND||getpid()!=MyProcPid||GetSessionUserId()!=auth||!alive(expected_receiver))enrollment_deny("invalid native process");
    deadline=started+ctx.experimental_abort_us;
    r.slot=(uint8_t)(slot+1);r.role=auth;r.db=MyDatabaseId;
    strlcpy(r.role_name,role,sizeof(r.role_name));strlcpy(r.db_name,db,sizeof(r.db_name));
    r.backend_start=MyStartTimestamp;r.postmaster_start=PgStartTime;
    memcpy(r.binding,ctx.binding,16);memcpy(r.deployment,ctx.deployment,16);memcpy(r.incarnation,ctx.incarnation,16);memcpy(r.epoch,ctx.epoch,32);memcpy(r.fingerprint,ctx.fingerprint,32);memcpy(r.policy,ctx.policy,32);
    if(!context_matches(&ctx,&r))enrollment_deny("allocated identity mismatch");
    health_gate gate;if(!read_gate(&ctx,&gate))enrollment_deny("independent eligibility absent");
    self=pending_anchor>=0?pending_anchor:syscall(SYS_pidfd_open,getpid(),0);
    if(access(TEST_DIR "/pre-observer-pause",F_OK)==0){struct timespec pause={2,0};nanosleep(&pause,NULL);}
    if(self<0||(pending_anchor>=0?memcmp(&pending_identity,&r,sizeof(r))||!observation_registered(observed,self,&r,0):!observation_pending(&ctx,observed,expected_observer,self,&r,deadline)))enrollment_deny("pending census enrollment denied");
    /* Current server catalog + protected synthetic header, no raw service access. */
    struct sigaction signal_before,signal_after;struct itimerval alarm_before,alarm_after;
    bool statement_active=get_timeout_active(STATEMENT_TIMEOUT);TimestampTz statement_finish=statement_active?get_timeout_finish_time(STATEMENT_TIMEOUT):0;
    sigaction(SIGALRM,NULL,&signal_before);getitimer(ITIMER_REAL,&alarm_before);
    /* Bound SPI lock waits too; this test control is not a numeric policy grant. */
    {uint64_t current=tick_us();if(current>=deadline)enrollment_deny("experimental abort elapsed before SPI");if(enrollment_timer==MAX_TIMEOUTS)enrollment_timer=RegisterTimeout(USER_TIMEOUT,enrollment_interrupt);enable_timeout_after(enrollment_timer,(int)((deadline-current+999)/1000));}
    PG_TRY();
    {
    if(SPI_connect()!=SPI_OK_CONNECT)enrollment_deny("SPI unavailable");
    {
        Oid types[3]={OIDOID,TEXTOID,INT4OID};Datum vals[3]={ObjectIdGetDatum(auth),CStringGetTextDatum(role),Int32GetDatum(slot+1)};
        int rc=SPI_execute_with_args("SELECT 1 FROM public.flooow_test_binding h JOIN pg_catalog.pg_roles r ON r.oid=h.role_oid WHERE h.role_oid=$1 AND h.role_name=$2 AND h.slot=$3 AND r.rolname=h.role_name AND r.rolcanlogin AND NOT r.rolinherit AND NOT r.rolsuper AND NOT r.rolcreaterole AND NOT r.rolcreatedb AND NOT r.rolreplication AND NOT r.rolbypassrls AND NOT EXISTS(SELECT 1 FROM pg_catalog.pg_auth_members m WHERE m.member=r.oid OR m.roleid=r.oid)",3,types,vals,NULL,true,2);
        if(rc!=SPI_OK_SELECT||SPI_processed!=1)enrollment_deny("header absent or role invalid");
    }
    SPI_finish();disable_timeout(enrollment_timer,false);
    }
    PG_CATCH();{disable_timeout(enrollment_timer,false);PG_RE_THROW();}
    PG_END_TRY();if(tick_us()>=deadline)enrollment_deny("experimental abort elapsed");
    if(!alive(self))enrollment_deny("self anchor failure");
retry_fixture_anchor:
    {
        struct stat directory,endpoint;
        if(lstat(TEST_DIR,&directory)||!S_ISDIR(directory.st_mode)||directory.st_uid!=getuid()||(directory.st_mode&0777)!=0700||lstat(TEST_SOCKET,&endpoint)||!S_ISSOCK(endpoint.st_mode)||endpoint.st_uid!=getuid()||(endpoint.st_mode&0777)!=0600)enrollment_deny("unsafe or absent namespace");
    }
    if(access(TEST_DIR "/pre-transfer-pause",F_OK)==0){struct timespec pause={6,0};nanosleep(&pause,NULL);}
    fd=socket(AF_UNIX,SOCK_SEQPACKET|SOCK_CLOEXEC|SOCK_NONBLOCK,0);if(fd<0)enrollment_deny("socket failure");
    strcpy(address.sun_path,TEST_SOCKET);
    if(connect(fd,(struct sockaddr *)&address,sizeof(address))<0)enrollment_deny("receiver absent");
    if(getsockopt(fd,SOL_SOCKET,SO_PEERCRED,&cred,&clen)||cred.uid!=getuid()||cred.gid!=getgid()||getsockopt(fd,SOL_SOCKET,SO_PEERPIDFD,&peer,&plen)||!anchor_equal(peer,expected_receiver)||!alive(peer))enrollment_deny("receiver identity mismatch");
    if(setsockopt(fd,SOL_SOCKET,SO_PASSPIDFD,&one,sizeof(one))||setsockopt(fd,SOL_SOCKET,SO_PASSCRED,&one,sizeof(one)))enrollment_deny("strong ancillary unavailable");
    /* ADMIN-owned fixture faults; never SQL identity arguments or service GUCs. */
    if(access(TEST_DIR "/wrong-deployment",F_OK)==0)r.deployment[0]^=1;
    if(access(TEST_DIR "/wrong-incarnation",F_OK)==0)r.incarnation[0]^=1;
    if(access(TEST_DIR "/stale-epoch",F_OK)==0)r.epoch[0]^=1;
    {int old=open(TEST_DIR "/old-epoch.bin",O_RDONLY|O_NOFOLLOW);if(old>=0){if(read(old,r.epoch,32)!=32)enrollment_deny("malformed replay fixture");close(old);}}
    if(access(TEST_DIR "/wrong-database",F_OK)==0)r.db++;
    if(access(TEST_DIR "/wrong-slot",F_OK)==0)r.slot=r.slot==4?1:r.slot+1;
    if(access(TEST_DIR "/old-postmaster-frame",F_OK)==0)r.postmaster_start--;
    n=encode_request(wire,&r);if(access(TEST_DIR "/bad-version",F_OK)==0)wire[5]=2;
    if(access(TEST_DIR "/partial-frame",F_OK)==0)n--;
    SHA256(wire,n,digest);
    /* Test-only copy of this actual self anchor, never a foreign PID lookup. */
    if(access(TEST_DIR "/capture-scm-replay",F_OK)==0){
        int capture=socket(AF_UNIX,SOCK_SEQPACKET|SOCK_CLOEXEC|SOCK_NONBLOCK,0);
        struct sockaddr_un destination={.sun_family=AF_UNIX};strcpy(destination.sun_path,TEST_DIR "/replay-capture.sock");
        unsigned char receipt=0;
        if(capture<0||connect(capture,(struct sockaddr *)&destination,sizeof(destination))||!wait_fd(capture,POLLOUT,deadline)||!send_anchor(capture,wire,n,self)||!wait_fd(capture,POLLIN,deadline)||recv(capture,&receipt,1,MSG_DONTWAIT)!=1||receipt!=0xd1)enrollment_deny("test-only anchor capture failed");
        close(capture);
    }
    if(!wait_fd(fd,POLLOUT,deadline)||!send_anchor(fd,wire,n,self)||!wait_fd(fd,POLLIN,deadline))enrollment_deny("no finite ACCEPT");
    {
        union{struct cmsghdr align;char bytes[256];} c={0};struct iovec i={.iov_base=reply,.iov_len=sizeof(reply)};
        struct msghdr m={.msg_iov=&i,.msg_iovlen=1,.msg_control=c.bytes,.msg_controllen=sizeof(c.bytes)};
        ssize_t got=recvmsg(fd,&m,MSG_CMSG_CLOEXEC|MSG_DONTWAIT);int sender=-1,cc=0,pc=0,extra=0;struct ucred mc={0};
        for(struct cmsghdr *x=CMSG_FIRSTHDR(&m);x;x=CMSG_NXTHDR(&m,x)){
            if(x->cmsg_level==SOL_SOCKET && x->cmsg_type==SCM_PIDFD && x->cmsg_len==CMSG_LEN(sizeof(int))){memcpy(&sender,CMSG_DATA(x),sizeof(int));pc++;}
            else if(x->cmsg_level==SOL_SOCKET && x->cmsg_type==SCM_CREDENTIALS && x->cmsg_len==CMSG_LEN(sizeof(mc))){memcpy(&mc,CMSG_DATA(x),sizeof(mc));cc++;}
            else extra++;
        }
        if(got!=76||m.msg_flags&(MSG_TRUNC|MSG_CTRUNC)||extra||pc!=1||cc!=1||mc.uid!=cred.uid||mc.gid!=cred.gid||!anchor_equal(sender,peer)||!alive(sender)||memcmp(reply,"G3F4\0\1\2\0\0\0\0\100",12)||memcmp(reply+12,ctx.epoch,32)||memcmp(reply+44,digest,32)||tick_us()>=deadline||!alive(self)||atomic_load(&observed->quarantined)||!alive(expected_observer)||tick_us()-atomic_load(&observed->observer_progress)>10000000)enrollment_deny("invalid or denied ACK");
        close(sender);
    }
    close(peer);close(fd);
    if(!repeated && access(TEST_DIR "/repeat-anchor",F_OK)==0){repeated=1;goto retry_fixture_anchor;}
    close(self);sigaction(SIGALRM,NULL,&signal_after);getitimer(ITIMER_REAL,&alarm_after);
    bool preserved=statement_active==get_timeout_active(STATEMENT_TIMEOUT)&&(!statement_active||statement_finish==get_timeout_finish_time(STATEMENT_TIMEOUT))&&signal_before.sa_handler==signal_after.sa_handler&&signal_before.sa_flags==signal_after.sa_flags&&!get_timeout_active(enrollment_timer);
    for(int sig=1;sig<NSIG;sig++)if(sigismember(&signal_before.sa_mask,sig)!=sigismember(&signal_after.sa_mask,sig))preserved=false;
    if(!statement_active&&!alarm_before.it_value.tv_sec&&!alarm_before.it_value.tv_usec&&(alarm_after.it_value.tv_sec||alarm_after.it_value.tv_usec))preserved=false;
    ereport(LOG,(errmsg("FLOOOW_TEST_TIMEOUT_RESTORATION preserved=%s custom_active=%s",preserved?"YES":"NO",get_timeout_active(enrollment_timer)?"YES":"NO")));
    if(!preserved)enrollment_deny("timeout restoration invariant failed");
    enrollment_in_progress=0;
    require_enrolled_execution();
    ereport(LOG,(errmsg("FLOOOW_TEST_ENROLLMENT_ACCEPT role=%u database=%u total_us=%llu",auth,MyDatabaseId,(unsigned long long)(tick_us()-started))));
    PG_RETURN_POINTER(NULL);
}
