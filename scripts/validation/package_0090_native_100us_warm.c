/* TEST_ONLY bounded mechanism benchmark. No SQL writes, no READY publication.
 * Includes pinned earlier primitives but does not invoke its cold main.
 * libpq's stable opaque C ABI is declared because builder has runtime library.
 */
#define main cold_legacy_main
#include "package_0090_s04_native_health.c"
#undef main
#include <sys/mman.h>
#include <sched.h>
typedef struct pg_conn PGconn;
typedef struct pg_result PGresult;
extern PGconn *PQconnectdb(const char *);
extern int PQstatus(const PGconn *);
extern PGresult *PQexec(PGconn *,const char *);
extern PGresult *PQprepare(PGconn *,const char *,const char *,int,const unsigned int *);
extern PGresult *PQexecPrepared(PGconn *,const char *,int,const char *const *,const int *,const int *,int);
extern int PQresultStatus(const PGresult *);
extern char *PQgetvalue(const PGresult *,int,int);
extern void PQclear(PGresult *);
extern void PQfinish(PGconn *);
#define N 7
#ifndef MAXE
#define MAXE 500
#endif
typedef struct {uint64_t t[11],queue_before,queue_after,queue_end_ns;} trace;
typedef struct {trace actor[N],guard;unsigned char sig[64];volatile int publication,release_epoch;} shared;
typedef struct {int index,pid;uint64_t epoch,generation,emitted;unsigned char nonce[32],work[32],pub[32],sig[64];} msg;
typedef struct {uint64_t epoch;unsigned char nonce[32];} request;
typedef struct {trace actor[N];uint64_t guard_db_start,guard_db_end,decision,consumer,guard_runqueue_ns;int all_work,all_fresh,consumer_fresh;uint64_t ages[N],decision_ages[N];} sample;
static const char *query="SELECT encode(sha256(convert_to(string_agg(v,E'\\n' ORDER BY k),'UTF8')),'hex') FROM (SELECT 0 AS k,pg_postmaster_start_time()::text||version() AS v UNION ALL SELECT installed_rank,installed_rank::text||version||type||script||checksum::text||success::text FROM public.flyway_schema_history UNION ALL SELECT 100000+oid::int,oid::text||rolname||rolsuper::text||rolinherit::text||rolcreaterole::text||rolcreatedb::text||rolcanlogin::text||rolreplication::text||rolbypassrls::text FROM pg_roles WHERE rolname LIKE 'test_0090_%') q";
static uint64_t rq(void){char s[256];file("/proc/self/schedstat",s,sizeof s);unsigned long long a,b,c;if(sscanf(s,"%llu %llu %llu",&a,&b,&c)!=3)exit(120);return b;}
static PGconn *connection(void){PGconn*c=PQconnectdb("dbname=g3f4 user=postgres host=/var/run/postgresql");if(!c||PQstatus(c))exit(121);PGresult*r=PQprepare(c,"epoch",query,0,NULL);if(!r||PQresultStatus(r)!=1)exit(122);PQclear(r);return c;}
static void db(PGconn*c,unsigned char out[32]){PGresult*r=PQexecPrepared(c,"epoch",0,NULL,NULL,NULL,0);if(!r||PQresultStatus(r)!=2)exit(123);char*p=PQgetvalue(r,0,0);if(strlen(p)!=64)exit(124);for(int i=0;i<32;i++){unsigned int b;if(sscanf(p+2*i,"%2x",&b)!=1)exit(125);out[i]=b;}PQclear(r);}
static int pidlive(int fd){struct pollfd p={fd,POLLIN,0};return poll(&p,1,0)==0;}
static int target_match(int fd,pid_t pid){char path[80],s[2048],*p;snprintf(path,sizeof path,"/proc/self/fdinfo/%d",fd);file(path,s,sizeof s);p=strstr(s,"Pid:");return p&&atoi(p+4)==pid;}
static void packet(int fd,msg*m){struct iovec io={m,sizeof *m};struct msghdr h={0};h.msg_iov=&io;h.msg_iovlen=1;if(sendmsg(fd,&h,0)!=sizeof *m)exit(126);}
static int receive(int fd,msg*m,pid_t expected,trace*t){char control[CMSG_SPACE(sizeof(struct ucred))];struct iovec io={m,sizeof *m};struct msghdr h={0};h.msg_iov=&io;h.msg_iovlen=1;h.msg_control=control;h.msg_controllen=sizeof control;memset(control,0,sizeof control);if(recvmsg(fd,&h,0)!=sizeof *m||h.msg_flags&(MSG_TRUNC|MSG_CTRUNC))exit(127);t->t[5]=now();int valid=0;for(struct cmsghdr*c=CMSG_FIRSTHDR(&h);c;c=CMSG_NXTHDR(&h,c)){if(c->cmsg_level==SOL_SOCKET&&c->cmsg_type==SCM_CREDENTIALS){struct ucred u;memcpy(&u,CMSG_DATA(c),sizeof u);valid=u.pid==expected&&u.uid==getuid();}}t->t[6]=now();return valid;}
static void send_anchor(int fd,int anchor){char ctrl[CMSG_SPACE(sizeof(int))];char x='p';struct iovec io={&x,1};struct msghdr h={0};h.msg_iov=&io;h.msg_iovlen=1;h.msg_control=ctrl;h.msg_controllen=sizeof ctrl;memset(ctrl,0,sizeof ctrl);struct cmsghdr*c=CMSG_FIRSTHDR(&h);c->cmsg_level=SOL_SOCKET;c->cmsg_type=SCM_RIGHTS;c->cmsg_len=CMSG_LEN(sizeof(int));memcpy(CMSG_DATA(c),&anchor,sizeof anchor);if(sendmsg(fd,&h,0)!=1)exit(128);}
static int receive_anchor(int fd,pid_t expected){char ctrl[CMSG_SPACE(sizeof(int))+CMSG_SPACE(sizeof(struct ucred))],x;struct iovec io={&x,1};struct msghdr h={0};h.msg_iov=&io;h.msg_iovlen=1;h.msg_control=ctrl;h.msg_controllen=sizeof ctrl;if(recvmsg(fd,&h,0)!=1)exit(129);int anchor=-1,cred=0;for(struct cmsghdr*c=CMSG_FIRSTHDR(&h);c;c=CMSG_NXTHDR(&h,c)){if(c->cmsg_level!=SOL_SOCKET)continue;if(c->cmsg_type==SCM_RIGHTS)memcpy(&anchor,CMSG_DATA(c),sizeof anchor);if(c->cmsg_type==SCM_CREDENTIALS){struct ucred u;memcpy(&u,CMSG_DATA(c),sizeof u);cred=u.pid==expected&&u.uid==getuid();}}if(!cred||anchor<0||!target_match(anchor,expected)||!pidlive(anchor))exit(130);return anchor;}
static int evp_verify(EVP_MD_CTX*c,EVP_PKEY*k,const unsigned char*sig,const unsigned char*nonce){return EVP_DigestVerifyInit(c,NULL,NULL,NULL,k)==1&&EVP_DigestVerify(c,sig,64,nonce,32)==1;}
static void actor(int i,int fd,uint64_t gen,shared*s,int targetfd,EVP_PKEY*signkey,unsigned char pub[32]){
 if(i==4){signkey=generate();size_t size=32;if(EVP_PKEY_get_raw_public_key(signkey,pub,&size)!=1)exit(164);}
 PGconn*c=(i==0||i==3)?connection():NULL;EVP_MD_CTX*crypto=EVP_MD_CTX_new();EVP_PKEY*verifykey=EVP_PKEY_new_raw_public_key(EVP_PKEY_ED25519,NULL,pub,32);unsigned char warm[32];SHA256((unsigned char*)"warm",4,warm);int anchor=syscall(SYS_pidfd_open,getpid(),0);if(anchor<0)exit(131);send_anchor(fd,anchor);close(anchor);
 if(i==4){msg registration={0};registration.index=i;registration.pid=getpid();registration.generation=gen;memcpy(registration.pub,pub,32);packet(fd,&registration);}
 uint64_t queue_before=rq();for(int e=0;e<MAXE;e++){trace*t=&s->actor[i];request r;if(read(fd,&r,sizeof r)!=sizeof r)exit(132);memset(t,0,sizeof *t);t->queue_before=queue_before;t->t[0]=now();while(__atomic_load_n(&s->release_epoch,__ATOMIC_ACQUIRE)!=e+1){sched_yield();}t->t[1]=now();msg m={0};m.index=i;m.pid=getpid();m.epoch=r.epoch;m.generation=gen;memcpy(m.nonce,r.nonce,32);memcpy(m.pub,pub,32);
  if(i==0||i==3)db(c,m.work);
  else if(i==1||i==2){unsigned char pre[48];memcpy(pre,r.nonce,32);memcpy(pre+32,&gen,8);memcpy(pre+40,&r.epoch,8);if(!pidlive(targetfd))exit(133);SHA256(pre,sizeof pre,m.work);}
  else if(i==4){size_t n=64;if(EVP_DigestSignInit(crypto,NULL,NULL,NULL,signkey)!=1||EVP_DigestSign(crypto,m.sig,&n,r.nonce,32)!=1||n!=64)exit(134);memcpy(s->sig,m.sig,64);__atomic_store_n(&s->publication,e+1,__ATOMIC_RELEASE);SHA256(m.sig,64,m.work);}
  else if(i==5){while(__atomic_load_n(&s->publication,__ATOMIC_ACQUIRE)!=e+1){sched_yield();}memcpy(m.sig,s->sig,64);if(!evp_verify(crypto,verifykey,m.sig,r.nonce))exit(135);SHA256(m.sig,64,m.work);}
  else{if(syscall(SYS_pidfd_send_signal,targetfd,SIGSTOP,NULL,0))exit(136);char completed;if(read(fd,&completed,1)!=1||completed!='s')exit(159);SHA256(r.nonce,32,m.work);}
  t->t[2]=now();m.emitted=now();t->t[3]=m.emitted;t->t[4]=now();packet(fd,&m);char ack;if(read(fd,&ack,1)!=1)exit(137);t->queue_after=rq();t->queue_end_ns=now();queue_before=rq();if(write(fd,"d",1)!=1)exit(138);
 }
 if(c){PQfinish(c);}if(i==4)EVP_PKEY_free(signkey);EVP_MD_CTX_free(crypto);EVP_PKEY_free(verifykey);_exit(0);
}
static void benchmark(pid_t hostroot,int pin){
 shared*s=mmap(NULL,sizeof *s,PROT_READ|PROT_WRITE,MAP_SHARED|MAP_ANONYMOUS,-1,0);if(s==MAP_FAILED)exit(139);memset(s,0,sizeof *s);sample*results=calloc(MAXE,sizeof *results);if(!results)exit(140);
 int hostfd=syscall(SYS_pidfd_open,hostroot,0);if(hostfd<0||!target_match(hostfd,hostroot))exit(141);
 char context[65536];unsigned char context_digest[32];file("/run/test-only-0090-warm/context.json",context,sizeof context);SHA256((unsigned char*)context,strlen(context),context_digest);
 char pgpath[512],pgpidtext[1024];const char*data=getenv("PGDATA");if(!data)data="/var/lib/postgresql/18/docker";snprintf(pgpath,sizeof pgpath,"%s/postmaster.pid",data);file(pgpath,pgpidtext,sizeof pgpidtext);pid_t pgpid=atoi(pgpidtext);int pganchor=syscall(SYS_pidfd_open,pgpid,0);if(pgpid<=0||pganchor<0||!target_match(pganchor,pgpid)||!pidlive(pganchor))exit(158);
 pid_t target=fork();if(target<0)exit(142);if(!target){for(;;)pause();}int targetfd=syscall(SYS_pidfd_open,target,0);if(targetfd<0||!target_match(targetfd,target))exit(143);
 PGconn*guarddb=connection();unsigned char expected[32];db(guarddb,expected);PQfinish(guarddb);guarddb=NULL;
 EVP_PKEY*key=NULL;unsigned char pub[32]={0};
 int pair[N][2],anchors[N];pid_t pid[N];uint64_t gen[N];cpu_set_t available;sched_getaffinity(0,sizeof available,&available);int cpus[N+1],ncpus=0;for(int c=0;c<CPU_SETSIZE&&ncpus<N+1;c++)if(CPU_ISSET(c,&available))cpus[ncpus++]=c;
 int order[]={4,0,1,2,3,5,6};for(int j=0;j<N;j++){int i=order[j];randombytes(&gen[i],8);if(socketpair(AF_UNIX,SOCK_SEQPACKET,0,pair[i]))exit(145);int yes=1;setsockopt(pair[i][0],SOL_SOCKET,SO_PASSCRED,&yes,sizeof yes);pid[i]=fork();if(pid[i]<0)exit(146);if(!pid[i]){close(pair[i][0]);if(pin&&ncpus>N){cpu_set_t a;CPU_ZERO(&a);CPU_SET(cpus[i+1],&a);if(sched_setaffinity(0,sizeof a,&a))exit(147);}actor(i,pair[i][1],gen[i],s,targetfd,key,pub);}close(pair[i][1]);anchors[i]=receive_anchor(pair[i][0],pid[i]);if(i==4){msg registration;trace setup_trace={0};if(!receive(pair[i][0],&registration,pid[i],&setup_trace)||registration.generation!=gen[i]||registration.index!=i||registration.epoch!=0)exit(165);memcpy(pub,registration.pub,32);}}
 if(pin&&ncpus>N){cpu_set_t a;CPU_ZERO(&a);CPU_SET(cpus[0],&a);if(sched_setaffinity(0,sizeof a,&a))exit(148);}
 guarddb=connection();EVP_MD_CTX*crypto=EVP_MD_CTX_new();EVP_PKEY*verifykey=EVP_PKEY_new_raw_public_key(EVP_PKEY_ED25519,NULL,pub,32);unsigned char dummy[32]={0},sig[64]={0};evp_verify(crypto,verifykey,sig,dummy);
 /* Fixed generation/process/channel/dependency expectations pre-established.
  * No earlier result is reused: every epoch invokes work and a fresh guard DB query.
  */
 for(int e=0;e<MAXE;e++){sample*out=&results[e];uint64_t guardq=rq();request r;unsigned char challenge[64];r.epoch=e+1;randombytes(challenge,32);memcpy(challenge+32,context_digest,32);SHA256(challenge,sizeof challenge,r.nonce);for(int i=0;i<N;i++){if(write(pair[i][0],&r,sizeof r)!=sizeof r)exit(149);}__atomic_store_n(&s->release_epoch,e+1,__ATOMIC_RELEASE);msg m[N];int auth[N],work[N];
  for(int i=0;i<N;i++){if(i==6){siginfo_t actual_stop={0};if(waitid(P_PIDFD,targetfd,&actual_stop,WSTOPPED|WNOWAIT)||actual_stop.si_pid!=target||actual_stop.si_code!=CLD_STOPPED)exit(160);if(write(pair[i][0],"s",1)!=1)exit(161);}auth[i]=receive(pair[i][0],&m[i],pid[i],&out->actor[i]);uint64_t identity_start=now();auth[i]=auth[i]&&pidlive(anchors[i])&&pidlive(hostfd)&&pidlive(pganchor)&&m[i].index==i&&m[i].pid==pid[i]&&m[i].generation==gen[i]&&m[i].epoch==r.epoch&&!memcmp(m[i].nonce,r.nonce,32);out->actor[i].t[6]=now();(void)identity_start;}
  out->guard_db_start=now();unsigned char current[32];db(guarddb,current);out->guard_db_end=now();int verified=evp_verify(crypto,verifykey,m[4].sig,r.nonce);
  for(int i=0;i<N;i++){unsigned char check[32];if(i==0||i==3){work[i]=!memcmp(m[i].work,current,32)&&!memcmp(current,expected,32);}else if(i==1||i==2){unsigned char pre[48];memcpy(pre,r.nonce,32);memcpy(pre+32,&gen[i],8);memcpy(pre+40,&r.epoch,8);SHA256(pre,sizeof pre,check);work[i]=pidlive(targetfd)&&!memcmp(check,m[i].work,32);}else if(i==4||i==5){SHA256(m[i].sig,64,check);work[i]=verified&&!memcmp(check,m[i].work,32)&&!memcmp(m[i].pub,pub,32)&&!memcmp(m[i].sig,m[4].sig,64);}else{siginfo_t si={0};if(waitid(P_PIDFD,targetfd,&si,WSTOPPED|WNOHANG|WNOWAIT))exit(150);SHA256(r.nonce,32,check);work[i]=si.si_pid==target&&si.si_code==CLD_STOPPED&&!memcmp(check,m[i].work,32);}out->actor[i].t[7]=now();out->actor[i].t[8]=out->guard_db_end;}
  out->decision=now();out->all_work=1;out->all_fresh=1;for(int i=0;i<N;i++){out->decision_ages[i]=out->decision-m[i].emitted;out->all_work=out->all_work&&auth[i]&&work[i];out->all_fresh=out->all_fresh&&auth[i]&&work[i]&&out->decision>=m[i].emitted&&out->decision_ages[i]<=100000;out->actor[i].t[9]=out->decision;}
  /* In-memory qualification consumer, not canonical readiness publication. */
  out->consumer=now();out->consumer_fresh=out->all_fresh;for(int i=0;i<N;i++){out->ages[i]=out->consumer-m[i].emitted;out->consumer_fresh=out->consumer_fresh&&out->consumer>=m[i].emitted&&out->ages[i]<=100000;out->actor[i].t[10]=out->consumer;}
  out->guard_runqueue_ns=rq()-guardq; // AFTER decision and consumer; no hot-path evidence IO.
  siginfo_t consumed_stop={0};if(waitid(P_PIDFD,targetfd,&consumed_stop,WSTOPPED|WNOHANG)||consumed_stop.si_pid!=target)exit(162);if(syscall(SYS_pidfd_send_signal,targetfd,SIGCONT,NULL,0)){exit(151);}siginfo_t resumed={0};if(waitid(P_PIDFD,targetfd,&resumed,WCONTINUED)||resumed.si_pid!=target)exit(163);
  for(int i=0;i<N;i++){if(write(pair[i][0],"a",1)!=1)exit(152);}for(int i=0;i<N;i++){char done;if(read(pair[i][0],&done,1)!=1)exit(153);trace*t=&s->actor[i];for(int j=0;j<5;j++)out->actor[i].t[j]=t->t[j];out->actor[i].queue_before=t->queue_before;out->actor[i].queue_after=t->queue_after;out->actor[i].queue_end_ns=t->queue_end_ns;}
  if(!out->all_work)exit(154);
 }
 /* Persist only after every sample's decision, entirely outside fresh sections. */
 printf("{\"mode\":\"%s\",\"clock\":\"CLOCK_BOOTTIME\",\"scheduler_policy\":%d,\"available_cpu_count\":%d,\"affinity_pinned\":%s,\"hot_path_evidence_IO\":\"NONE\",\"setup_pidfd_target_match\":true,\"samples\":[",pin?"warm_pinned":"warm_unpinned",sched_getscheduler(0),CPU_COUNT(&available),pin?"true":"false");
 for(int e=0;e<MAXE;e++){sample*out=&results[e];printf("%s{\"epoch\":%d,\"work_valid\":%s,\"all_under_100us\":%s,\"consumer_under_100us\":%s,\"guard_db_ns\":%llu,\"guard_scheduler_queue_ns\":%llu,\"participants\":[",e?",":"",e+1,out->all_work?"true":"false",out->all_fresh?"true":"false",out->consumer_fresh?"true":"false",(unsigned long long)(out->guard_db_end-out->guard_db_start),(unsigned long long)out->guard_runqueue_ns);
  for(int i=0;i<N;i++){trace*t=&out->actor[i];printf("%s{\"index\":%d,\"generation\":%llu,\"age_ns\":%llu,\"decision_age_ns\":%llu,\"scheduler_queue_ns\":%llu,\"scheduler_interval_end_ns\":%llu,\"t\":[",i?",":"",i,(unsigned long long)gen[i],(unsigned long long)out->ages[i],(unsigned long long)out->decision_ages[i],(unsigned long long)(t->queue_after-t->queue_before),(unsigned long long)t->queue_end_ns);for(int j=0;j<11;j++)printf("%s%llu",j?",":"",(unsigned long long)t->t[j]);printf("]}");}printf("]}");}
 printf("],\"full_original_approval_lineage_proven\":false,\"readiness_written\":false,\"native_health_ready\":false}\n");fflush(stdout);
 for(int i=0;i<N;i++){waitpid(pid[i],NULL,0);close(anchors[i]);close(pair[i][0]);}kill(target,SIGTERM);waitpid(target,NULL,0);close(targetfd);close(hostfd);close(pganchor);PQfinish(guarddb);EVP_MD_CTX_free(crypto);EVP_PKEY_free(verifykey);free(results);exit(0);
}
int main(int argc,char**argv){int pin=argc>1&&!strcmp(argv[1],"pin");pid_t root=getpid(),guard=fork();if(guard<0)return 155;if(!guard)benchmark(root,pin);int status;if(waitpid(guard,&status,0)!=guard)return 156;return WIFEXITED(status)?WEXITSTATUS(status):157;}
