/* TEST_ONLY independent Linux guard. No PostgreSQL writes or READY publication.
 * Actual SCM_CREDENTIALS + SCM_RIGHTS pidfds, fresh generations and work.
 * A completed campaign can still deny eligibility at the immutable 100us gate.
 */
#define _GNU_SOURCE
#include <sys/socket.h>
#include <sys/syscall.h>
#include <sys/wait.h>
#include <sys/stat.h>
#include <sys/random.h>
#include <fcntl.h>
#include <poll.h>
#include <unistd.h>
#include <signal.h>
#include <errno.h>
#include <time.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <openssl/evp.h>
#include <openssl/sha.h>

static const char *names[]={"POSTMASTER","SUPERVISOR","RECEIVER","CENSUS_OBSERVER","APPROVAL_PRODUCER","APPROVAL_CONSUMER","ENFORCEMENT_WORKER"};
static uint64_t now(void){struct timespec t;if(clock_gettime(CLOCK_BOOTTIME,&t))exit(90);return (uint64_t)t.tv_sec*1000000000+t.tv_nsec;}
static void die(const char *s){perror(s);exit(91);}
static void randombytes(void *p,size_t n){if(getrandom(p,n,0)!=(ssize_t)n)die("getrandom");}
static void hex(const unsigned char *p,size_t n,char *out){for(size_t i=0;i<n;i++)sprintf(out+2*i,"%02x",p[i]);out[2*n]=0;}
static void file(const char *path,char *out,size_t n){FILE*f=fopen(path,"r");if(!f)die(path);size_t k=fread(out,1,n-1,f);out[k]=0;fclose(f);}
static void proc(pid_t pid,char *out,size_t n){char path[80],raw[4096];snprintf(path,sizeof path,"/proc/%d/stat",pid);file(path,raw,sizeof raw);char*tail=strrchr(raw,')');if(!tail)exit(105);char *save,*token=strtok_r(tail+2," ",&save);unsigned long long start=0;long parent=0;for(int field=3;token;field++,token=strtok_r(NULL," ",&save)){if(field==4)parent=strtol(token,NULL,10);if(field==22){start=strtoull(token,NULL,10);break;}}if(!start)exit(106);snprintf(out,n,"pid=%d;parent=%ld;start_ticks=%llu",pid,parent,start);}
static int stopped(pid_t pid){char path[80],raw[4096];snprintf(path,sizeof path,"/proc/%d/stat",pid);file(path,raw,sizeof raw);char*tail=strrchr(raw,')');return tail&&tail[2]=='T';}
static void probe(unsigned char out[32]){
 FILE*f=popen("psql -X -qAt -w -U postgres -d g3f4 -v ON_ERROR_STOP=1 -c \"SELECT pg_postmaster_start_time(),version(); SELECT installed_rank,version,type,script,checksum,success FROM public.flyway_schema_history ORDER BY installed_rank; SELECT oid,rolname,rolsuper,rolinherit,rolcreaterole,rolcreatedb,rolcanlogin,rolreplication,rolbypassrls FROM pg_catalog.pg_roles WHERE rolname LIKE 'test_0090_%' ORDER BY rolname;\"","r");
 if(!f){die("catalog probe");}unsigned char b[32768];size_t n=fread(b,1,sizeof b,f);int rc=pclose(f);if(rc||!n||n==sizeof b)exit(92);SHA256(b,n,out);
}

static uint64_t runq(void){char s[256];file("/proc/self/schedstat",s,sizeof s);unsigned long long cpu,queue,count;if(sscanf(s,"%llu %llu %llu",&cpu,&queue,&count)!=3)exit(110);return queue;}

typedef struct {int index;uint64_t t[11],credential_start,credential_end,pidfd_start,pidfd_end;pid_t pid,target;uint64_t generation,counter,emitted,request_time;unsigned char nonce[32],catalog[32],work[32],pub[32],sig[64];int work_kind;char target_stat[512];} observation;
static void sendobs(int fd,observation *o){int anchor=syscall(SYS_pidfd_open,getpid(),0);if(anchor<0)die("pidfd_open");char control[CMSG_SPACE(sizeof(int))];struct iovec io={o,sizeof *o};struct msghdr m={0};m.msg_iov=&io;m.msg_iovlen=1;m.msg_control=control;m.msg_controllen=sizeof control;memset(control,0,sizeof control);struct cmsghdr*c=CMSG_FIRSTHDR(&m);c->cmsg_level=SOL_SOCKET;c->cmsg_type=SCM_RIGHTS;c->cmsg_len=CMSG_LEN(sizeof(int));memcpy(CMSG_DATA(c),&anchor,sizeof(int));o->t[4]=now();if(sendmsg(fd,&m,0)!=sizeof *o)die("sendmsg");close(anchor);}
static EVP_PKEY *generate(void){EVP_PKEY_CTX*c=EVP_PKEY_CTX_new_id(EVP_PKEY_ED25519,NULL);EVP_PKEY*k=NULL;if(!c||EVP_PKEY_keygen_init(c)!=1||EVP_PKEY_keygen(c,&k)!=1)exit(93);EVP_PKEY_CTX_free(c);return k;}
static int verify(observation *o){EVP_PKEY*k=EVP_PKEY_new_raw_public_key(EVP_PKEY_ED25519,NULL,o->pub,32);EVP_MD_CTX*c=EVP_MD_CTX_new();int r=k&&c&&EVP_DigestVerifyInit(c,NULL,NULL,NULL,k)==1&&EVP_DigestVerify(c,o->sig,64,o->nonce,32)==1;EVP_MD_CTX_free(c);EVP_PKEY_free(k);return r;}
static void worker(int index,int fd,uint64_t gen,const unsigned char nonce[32],const unsigned char catalog[32],pid_t postmaster,const observation *approval){
 observation o={0};o.index=index;o.pid=getpid();o.generation=gen;o.counter=1;uint64_t sched_before=runq();o.request_time=now();o.t[0]=o.request_time;memcpy(o.nonce,nonce,32);memcpy(o.catalog,catalog,32);o.work_kind=index+1;o.t[1]=now();
 if(index==0||index==3){probe(o.work);o.target=postmaster;proc(postmaster,o.target_stat,sizeof o.target_stat);}
 else if(index==1){pid_t child=fork();if(child<0)die("spawn witness");if(!child){for(;;)pause();}o.target=child;proc(child,o.target_stat,sizeof o.target_stat);SHA256((unsigned char*)o.target_stat,strlen(o.target_stat),o.work);}
 else if(index==2){/* actual generation-bound enrollment decision on authenticated request */
  unsigned char pre[72];memcpy(pre,nonce,32);memcpy(pre+32,catalog,32);memcpy(pre+64,&gen,8);SHA256(pre,sizeof pre,o.work);
 }else if(index==4){EVP_PKEY*k=generate();EVP_MD_CTX*c=EVP_MD_CTX_new();size_t n=32,z=64;if(EVP_PKEY_get_raw_public_key(k,o.pub,&n)!=1||EVP_DigestSignInit(c,NULL,NULL,NULL,k)!=1||EVP_DigestSign(c,o.sig,&z,nonce,32)!=1||z!=64)exit(94);EVP_MD_CTX_free(c);EVP_PKEY_free(k);SHA256(o.sig,64,o.work);}
 else if(index==5){memcpy(o.pub,approval->pub,32);memcpy(o.sig,approval->sig,64);if(!verify(&o))exit(95);SHA256(o.sig,64,o.work);}
 else{pid_t child=fork();if(child<0)die("enforcement target");if(!child){for(;;)pause();}if(kill(child,SIGSTOP))die("stop target");int status;if(waitpid(child,&status,WUNTRACED)!=child||!WIFSTOPPED(status))exit(96);o.target=child;proc(child,o.target_stat,sizeof o.target_stat);SHA256((unsigned char*)o.target_stat,strlen(o.target_stat),o.work);}
 o.t[2]=now();o.emitted=now();o.t[3]=o.emitted;sendobs(fd,&o);char ack;if(read(fd,&ack,1)!=1)exit(97);uint64_t sched_after=runq();dprintf(1,"{\"kind\":\"scheduler\",\"index\":%d,\"runqueue_wait_ns\":%llu,\"interval_end_ns\":%llu}\n",index,(unsigned long long)(sched_after-sched_before),(unsigned long long)now());if(o.target&&index!=0&&index!=3){kill(o.target,SIGCONT);kill(o.target,SIGTERM);waitpid(o.target,NULL,0);}close(fd);_exit(0);
}
static int recvobs(int fd,observation *o,pid_t expected){char control[CMSG_SPACE(sizeof(int))+CMSG_SPACE(sizeof(struct ucred))];struct iovec io={o,sizeof *o};struct msghdr m={0};m.msg_iov=&io;m.msg_iovlen=1;m.msg_control=control;m.msg_controllen=sizeof control;memset(control,0,sizeof control);if(recvmsg(fd,&m,0)!=sizeof *o||m.msg_flags&(MSG_TRUNC|MSG_CTRUNC))exit(98);o->t[5]=now();o->credential_start=now();int anchor=-1,cred=0;for(struct cmsghdr*c=CMSG_FIRSTHDR(&m);c;c=CMSG_NXTHDR(&m,c)){if(c->cmsg_level!=SOL_SOCKET)continue;if(c->cmsg_type==SCM_RIGHTS)memcpy(&anchor,CMSG_DATA(c),sizeof(int));if(c->cmsg_type==SCM_CREDENTIALS){struct ucred u;memcpy(&u,CMSG_DATA(c),sizeof u);cred=u.pid==expected&&u.uid==getuid();}}o->credential_end=now();o->pidfd_start=now();if(anchor<0)exit(99);struct pollfd p={anchor,POLLIN,0};int live=poll(&p,1,0)==0;close(anchor);o->pidfd_end=now();o->t[6]=now();return cred&&live&&o->pid==expected;}
static void guard(pid_t root,pid_t postmaster,const unsigned char expected_catalog[32]){
 char rootstat[512],boot[100],ns[128],binary[100],host[256];proc(root,rootstat,sizeof rootstat);file("/proc/sys/kernel/random/boot_id",boot,sizeof boot);file("/proc/1/cgroup",host,sizeof host);ssize_t n=readlink("/proc/self/ns/pid",ns,sizeof ns-1);if(n<0)die("namespace");ns[n]=0;snprintf(binary,sizeof binary,"/proc/%d/exe",postmaster);int rootfd=syscall(SYS_pidfd_open,root,0),pgfd=syscall(SYS_pidfd_open,postmaster,0);if(rootfd<0||pgfd<0)die("root/postmaster anchor");
 unsigned char nonce[32],context_digest[32],challenge[64];char context[65536];file("/run/test-only-0090-cold/context.json",context,sizeof context);SHA256((unsigned char*)context,strlen(context),context_digest);randombytes(challenge,32);memcpy(challenge+32,context_digest,32);SHA256(challenge,sizeof challenge,nonce);uint64_t gens[7];int sockets[7][2];pid_t pids[7];observation obs[7];int authenticated[7];unsigned char independently_observed[32];probe(independently_observed);if(memcmp(expected_catalog,independently_observed,32))exit(100);
 /* Producer precedes consumer; all actors remain independently observable. */
 int order[]={4,0,1,2,3,5,6};uint64_t campaign_start=now();
 char ledger_path[256];snprintf(ledger_path,sizeof ledger_path,"/run/test-only-0090-cold/generation-%d.jsonl",getpid());int ledger=open(ledger_path,O_CREAT|O_EXCL|O_WRONLY|O_APPEND,0600);if(ledger<0)die("fresh generation ledger");
 for(int j=0;j<7;j++){int i=order[j];randombytes(&gens[i],8);if(!gens[i])gens[i]=1;if(socketpair(AF_UNIX,SOCK_SEQPACKET,0,sockets[i]))die("socketpair");int yes=1;if(setsockopt(sockets[i][0],SOL_SOCKET,SO_PASSCRED,&yes,sizeof yes))die("passcred");pids[i]=fork();if(pids[i]<0)die("fork");if(!pids[i]){close(sockets[i][0]);char enrollment_ack;if(read(sockets[i][1],&enrollment_ack,1)!=1)exit(107);worker(i,sockets[i][1],gens[i],nonce,expected_catalog,postmaster,&obs[4]);}close(sockets[i][1]);char identity[512],generation[17];proc(pids[i],identity,sizeof identity);hex((unsigned char*)&gens[i],8,generation);if(dprintf(ledger,"{\"sequence\":%d,\"participant\":\"%s\",\"pid\":%d,\"generation\":\"%s\",\"identity\":\"%s\",\"enrolled_before_work\":true}\n",j+1,names[i],pids[i],generation,identity)<0||fsync(ledger))die("enrollment publication");if(write(sockets[i][0],"e",1)!=1)die("enrollment ack");if(i==4)authenticated[i]=recvobs(sockets[i][0],&obs[i],pids[i]);}
 for(int i=0;i<7;i++){if(i!=4)authenticated[i]=recvobs(sockets[i][0],&obs[i],pids[i]);}
 close(ledger);
 uint64_t catalog_start=now();probe(independently_observed);uint64_t catalog_finish=now();uint64_t observed=now();int all=1,fresh=1;
 char contexthex[65],cataloghex[65],noncehex[65],hosthex[65],pgidentity[512];unsigned char hostdigest[32];hex(context_digest,32,contexthex);hex(expected_catalog,32,cataloghex);hex(nonce,32,noncehex);SHA256((unsigned char*)host,strlen(host),hostdigest);hex(hostdigest,32,hosthex);boot[strcspn(boot,"\r\n")]=0;proc(postmaster,pgidentity,sizeof pgidentity);
 printf("{\"scope\":\"TEST_ONLY\",\"guard_pid\":%d,\"host_root_pid\":%d,\"postmaster_pid\":%d,\"host_root_pidfd\":true,\"postmaster_pidfd\":true,\"pid_namespace\":\"%s\",\"boot_id\":\"%s\",\"host_cgroup_sha256\":\"%s\",\"root_identity\":\"%s\",\"postmaster_identity\":\"%s\",\"context_sha256\":\"%s\",\"catalog_sha256\":\"%s\",\"challenge_hex\":\"%s\",\"campaign_elapsed_ns\":%llu,\"window_ns\":100000,\"participants\":[",getpid(),root,postmaster,ns,boot,hosthex,rootstat,pgidentity,contexthex,cataloghex,noncehex,(unsigned long long)(observed-campaign_start));
 for(int i=0;i<7;i++){observation*o=&obs[i];int work=0;unsigned char recomputed[32];char actual[512];if(i==0||i==3)work=!memcmp(o->work,independently_observed,32);else if(i==1||i==6){proc(o->target,actual,sizeof actual);SHA256((unsigned char*)actual,strlen(actual),recomputed);work=!memcmp(o->work,recomputed,32);if(i==6)work=work&&stopped(o->target);}else if(i==2){unsigned char pre[72];memcpy(pre,nonce,32);memcpy(pre+32,expected_catalog,32);memcpy(pre+64,&gens[i],8);SHA256(pre,sizeof pre,recomputed);work=!memcmp(o->work,recomputed,32);}else{SHA256(o->sig,64,recomputed);work=verify(o)&&!memcmp(o->work,recomputed,32);if(i==5)work=work&&!memcmp(o->sig,obs[4].sig,64)&&!memcmp(o->pub,obs[4].pub,32);}
  o->t[7]=now();o->t[8]=catalog_finish;int identity=authenticated[i]&&o->generation==gens[i]&&o->index==i&&o->counter==1&&!memcmp(o->nonce,nonce,32)&&!memcmp(o->catalog,expected_catalog,32)&&o->request_time<=o->emitted&&o->emitted<=observed;
  uint64_t age=observed-o->emitted;int eligible=identity&&work&&age<=100000;all=all&&identity&&work;fresh=fresh&&eligible;char generation[17],digest[65];hex((unsigned char*)&gens[i],8,generation);hex(o->work,32,digest);
  char actoridentity[512],pubhex[65],sighex[129];proc(o->pid,actoridentity,sizeof actoridentity);hex(o->pub,32,pubhex);hex(o->sig,64,sighex);
  printf("%s{\"participant\":\"%s\",\"pid\":%d,\"process_identity\":\"%s\",\"generation\":\"%s\",\"counter\":1,\"SCM_CREDENTIALS_verified\":%s,\"SCM_RIGHTS_pidfd_live\":%s,\"functional_work_independently_verified\":%s,\"request_boottime_ns\":%llu,\"emission_boottime_ns\":%llu,\"observation_boottime_ns\":%llu,\"age_ns\":%llu,\"fresh\":%s,\"work_sha256\":\"%s\",\"work_target_pid\":%d,\"public_key_hex\":\"%s\",\"signature_hex\":\"%s\"}",i?",":"",names[i],o->pid,actoridentity,generation,authenticated[i]?"true":"false",authenticated[i]?"true":"false",work?"true":"false",(unsigned long long)o->request_time,(unsigned long long)o->emitted,(unsigned long long)observed,(unsigned long long)age,eligible?"true":"false",digest,o->target,pubhex,sighex);
 }
 uint64_t decision_complete=now();for(int i=0;i<7;i++)obs[i].t[9]=decision_complete;printf("],\"identity_and_work_complete\":%s,\"native_health_ready\":%s,\"ready_written\":false,\"clock\":\"CLOCK_BOOTTIME\"}\n",all?"true":"false",fresh?"true":"false");fflush(stdout);
 printf("{\"kind\":\"timeline\",\"catalog_start_ns\":%llu,\"catalog_finish_ns\":%llu,\"qualified_decision_ns\":%llu,\"participants\":[",(unsigned long long)catalog_start,(unsigned long long)catalog_finish,(unsigned long long)decision_complete);
 for(int i=0;i<7;i++){observation*o=&obs[i];printf("%s{\"index\":%d,\"t\":[",i?",":"",i);for(int j=0;j<10;j++)printf("%s%llu",j?",":"",(unsigned long long)o->t[j]);printf(",null],\"credential_ns\":%llu,\"pidfd_ns\":%llu}",(unsigned long long)(o->credential_end-o->credential_start),(unsigned long long)(o->pidfd_end-o->pidfd_start));}printf("]}\n");fflush(stdout);
 for(int i=0;i<7;i++){if(write(sockets[i][0],"a",1)!=1)die("ack");close(sockets[i][0]);waitpid(pids[i],NULL,0);}close(rootfd);close(pgfd);exit(all?0:101);
}
int main(void){unsigned char catalog[32];probe(catalog);char pidpath[256];const char*pgdata=getenv("PGDATA");if(!pgdata)pgdata="/var/lib/postgresql/18/docker";snprintf(pidpath,sizeof pidpath,"%s/postmaster.pid",pgdata);char pidtext[1024];file(pidpath,pidtext,sizeof pidtext);pid_t postmaster=atoi(pidtext);if(postmaster<=0)exit(102);pid_t root=getpid(),child=fork();if(child<0)die("guard spawn");if(!child)guard(root,postmaster,catalog);int status;if(waitpid(child,&status,0)!=child)return 103;return WIFEXITED(status)?WEXITSTATUS(status):104;}
