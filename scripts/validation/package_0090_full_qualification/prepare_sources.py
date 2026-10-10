"""Successor-only transforms; frozen predecessor files are never edited."""
from pathlib import Path
import re
ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).parent
OLD=ROOT/'scripts/validation/package_0090_native_qualification'
def prepare():
    for name in ['protocol.h','login.c','receiver.c','supervisor.c','frame_tests.c','fake_receiver.c','clone3_probe.c']:
        s=(OLD/name).read_text()
        if name=='protocol.h':
            s=s.replace('#include <openssl/sha.h>','#include <openssl/sha.h>\n#include <dlfcn.h>\n#include <signal.h>')
            start=s.index('    /* Conservative ASCII fixture subset:')
            end=s.index('    memcpy(out,*p,n)',start)
            s=s[:start]+'''    if(!text_nfc(*p,n))return 0;
'''+s[end:]
            pos=s.index('static inline int getstr(')
            s=s[:pos]+'''/* Qualified existing ICU76 runtime; strict UTF8->UTF16, exact NFC, no rewrite. */
static inline int text_nfc(const unsigned char *s,unsigned n){
    static void *lib;static const void *(*nfc)(int32_t *);
    static void (*convert)(uint16_t *,int32_t,int32_t *,const char *,int32_t,int32_t *);
    static int8_t (*normalized)(const void *,const uint16_t *,int32_t,int32_t *);
    if(!lib){lib=dlopen("libicuuc.so.76",RTLD_NOW|RTLD_LOCAL);if(!lib)return 0;
      *(void **)(&nfc)=dlsym(lib,"unorm2_getNFCInstance_76");
      *(void **)(&convert)=dlsym(lib,"u_strFromUTF8_76");
      *(void **)(&normalized)=dlsym(lib,"unorm2_isNormalized_76");}
    if(!nfc||!convert||!normalized||!n||n>63)return 0;
    uint16_t u[64];int32_t e=0,len=0;convert(u,64,&len,(const char *)s,(int32_t)n,&e);if(e>0)return 0;
    for(int32_t i=0;i<len;i++)if(u[i]<32||(u[i]>=0x7f&&u[i]<=0x9f))return 0;
    const void *norm=nfc(&e);if(e>0||!norm)return 0;return normalized(norm,u,len,&e)&&e<=0;
}
typedef struct{uint32_t magic,eligible;uint64_t expires;unsigned char context[32],header[32];} health_gate;
static inline int read_gate(const test_context *ctx,health_gate *g){
    struct stat st,dir;if(lstat("/run/flooow-external",&dir)||dir.st_uid||!S_ISDIR(dir.st_mode)||(dir.st_mode&0777)!=0755)return 0;
    int fd=open("/run/flooow-external/gate.bin",O_RDONLY|O_NOFOLLOW|O_CLOEXEC);
    if(fd<0)return 0;int ok=!fstat(fd,&st)&&st.st_uid==0&&(st.st_mode&0777)==0444&&S_ISREG(st.st_mode)&&read(fd,g,sizeof(*g))==(ssize_t)sizeof(*g);close(fd);
    test_context copy=*ctx;memset(copy.epoch,0,32);unsigned char digest[32];SHA256((unsigned char *)&copy,sizeof(copy),digest);
    return ok&&g->magic==0x00900002&&g->eligible==1&&g->expires>tick_us()&&!memcmp(g->context,digest,32)&&access(TEST_DIR "/drain-active",F_OK)!=0&&access(TEST_DIR "/quarantine-active",F_OK)!=0;
}
'''+s[pos:]
        elif name=='login.c':
            s=s.replace('#include "storage/proc.h"','#include "storage/proc.h"\n#include <sys/time.h>')
            s=s.replace('static int prepared=0;','static int prepared=0;\nstatic TimeoutId enrollment_timer=MAX_TIMEOUTS;\nstatic void enrollment_interrupt(void){InterruptPending=true;QueryCancelPending=true;}')
            s=s.replace('    /* Current server catalog', '    health_gate gate;if(!read_gate(&ctx,&gate))die("independent eligibility absent");\n    /* Current server catalog')
            s=s.replace('    /* Bound SPI lock waits too;', '''    struct sigaction signal_before,signal_after;struct itimerval alarm_before,alarm_after;
    bool statement_active=get_timeout_active(STATEMENT_TIMEOUT);TimestampTz statement_finish=statement_active?get_timeout_finish_time(STATEMENT_TIMEOUT):0;
    sigaction(SIGALRM,NULL,&signal_before);getitimer(ITIMER_REAL,&alarm_before);
    /* Bound SPI lock waits too;''')
            s=s.replace('    close(self);', '''    close(self);sigaction(SIGALRM,NULL,&signal_after);getitimer(ITIMER_REAL,&alarm_after);
    bool preserved=statement_active==get_timeout_active(STATEMENT_TIMEOUT)&&(!statement_active||statement_finish==get_timeout_finish_time(STATEMENT_TIMEOUT))&&signal_before.sa_handler==signal_after.sa_handler&&signal_before.sa_flags==signal_after.sa_flags&&!get_timeout_active(enrollment_timer);
    for(int sig=1;sig<NSIG;sig++)if(sigismember(&signal_before.sa_mask,sig)!=sigismember(&signal_after.sa_mask,sig))preserved=false;
    if(!statement_active&&!alarm_before.it_value.tv_sec&&!alarm_before.it_value.tv_usec&&(alarm_after.it_value.tv_sec||alarm_after.it_value.tv_usec))preserved=false;
    ereport(LOG,(errmsg("FLOOOW_TEST_TIMEOUT_RESTORATION preserved=%s custom_active=%s",preserved?"YES":"NO",get_timeout_active(enrollment_timer)?"YES":"NO")));
    if(!preserved)die("timeout restoration invariant failed");''')
            s=s.replace('enable_timeout_after(STATEMENT_TIMEOUT,','if(enrollment_timer==MAX_TIMEOUTS)enrollment_timer=RegisterTimeout(USER_TIMEOUT,enrollment_interrupt);enable_timeout_after(enrollment_timer,')
            s=s.replace('    if(SPI_connect()!=SPI_OK_CONNECT)', '    PG_TRY();\n    {\n    if(SPI_connect()!=SPI_OK_CONNECT)')
            s=s.replace('SPI_finish();disable_timeout(STATEMENT_TIMEOUT,false);','SPI_finish();disable_timeout(enrollment_timer,false);\n    }\n    PG_CATCH();{disable_timeout(enrollment_timer,false);PG_RE_THROW();}\n    PG_END_TRY();')
        elif name=='receiver.c':
            s=s.replace('unsigned char digest[32];} entry;','unsigned char digest[32];request_fields request;pid_t pid;int cancelling;uint64_t detected;} entry;')
            s=s.replace('static int catalog(const request_fields *r,pid_t sender_pid,uint64_t until){','static test_context current;\nstatic int catalog(const request_fields *r,pid_t sender_pid,uint64_t until){\n    health_gate gate;if(!read_gate(&current,&gate))return 0;')
            s=s.replace('SELECT 1 FROM public.flooow_test_binding h','SELECT to_jsonb(full_header)::text FROM public.flooow_test_binding h JOIN public.offline_binding_header full_header ON true JOIN public.offline_binding_lifecycle lifecycle ON lifecycle.binding_id=full_header.binding_id AND lifecycle.state=\'ACTIVE\'')
            s=s.replace('if(q)PQclear(q);PQfinish(db);return ok;', 'if(ok){unsigned char hash[32];SHA256((unsigned char *)PQgetvalue(q,0,0),strlen(PQgetvalue(q,0,0)),hash);ok=!memcmp(hash,gate.header,32);}\n    if(q)PQclear(q);PQfinish(db);return ok;')
            insert=s.index('int main(int argc,char **argv)')
            s=s[:insert]+'''/* Authoritative catalog disappearance is independent of eligibility predicates. */
static int session_present(const entry *e,uint64_t until){
    PGconn *db=PQconnectStart("host=/tmp/pgsock dbname=native_fixture user=postgres");if(!db)return -1;
    for(;;){PostgresPollingStatusType state=PQconnectPoll(db);if(state==PGRES_POLLING_OK)break;
      if((state!=PGRES_POLLING_READING&&state!=PGRES_POLLING_WRITING)||!wait_fd(PQsocket(db),state==PGRES_POLLING_READING?POLLIN:POLLOUT,until)){PQfinish(db);return -1;}}
    if(PQsetnonblocking(db,1)){PQfinish(db);return -1;}char pid[24],start[32];snprintf(pid,sizeof(pid),"%d",e->pid);snprintf(start,sizeof(start),"%lld",(long long)e->request.backend_start);const char *v[]={pid,start};
    if(!PQsendQueryParams(db,"SELECT 1 FROM pg_stat_activity WHERE pid=$1::int AND (extract(epoch from backend_start)*1000000-946684800000000)::bigint=$2::bigint",2,NULL,v,NULL,NULL,0)){PQfinish(db);return -1;}
    for(;;){int flushed=PQflush(db);if(!flushed)break;if(flushed<0||!wait_fd(PQsocket(db),POLLOUT,until)){PQfinish(db);return -1;}}
    while(PQisBusy(db)){if(!wait_fd(PQsocket(db),POLLIN,until)||!PQconsumeInput(db)){PQfinish(db);return -1;}}
    PGresult *r=PQgetResult(db);int result=r&&PQresultStatus(r)==PGRES_TUPLES_OK?PQntuples(r):-1;if(r)PQclear(r);PQfinish(db);return result;
}
'''+s[insert:]
            s=s.replace('if(argc!=3)return 64;', 'if(argc!=4)return 64;int supervisor=atoi(argv[3]);')
            s=s.replace('    current=ctx;', '    current=ctx;')
            s=s.replace('    /* Only the supervisor', '    current=ctx;\n    int parent_peer=-1;socklen_t parent_len=sizeof(parent_peer);if(getsockopt(ctl,SOL_SOCKET,SO_PEERPIDFD,&parent_peer,&parent_len)||!anchor_equal(parent_peer,supervisor)||!alive(supervisor))return 70;close(parent_peer);\n    /* Only the supervisor')
            start=s.index('        for(unsigned i=0;i<used;i++)if(registry[i].fd>=0&&!alive')
            end=s.index('        struct pollfd ps[3]',start)
            s=s[:start]+'''        health_gate health;int eligible=alive(supervisor)&&alive(postmaster)&&read_gate(&ctx,&health);
        for(unsigned i=0;i<used;i++)if(registry[i].fd>=0){entry *e=&registry[i];
          if(!alive(e->fd)){printf("{\\"event\\":\\"kernel_death\\",\\"pid\\":%d,\\"slot\\":%u,\\"at_us\\":%llu}\\n",e->pid,e->slot,(unsigned long long)tick_us());e->cancelling=1;
             int present=session_present(e,tick_us()+ctx.experimental_abort_us);
             if(present==0){printf("{\\"event\\":\\"DRAINED\\",\\"pid\\":%d,\\"catalog_disappeared\\":true,\\"effects\\":\\"RECONCILIATION_REQUIRED\\",\\"at_us\\":%llu}\\n",e->pid,(unsigned long long)tick_us());close(e->fd);e->fd=-1;}
             else printf("{\\"event\\":\\"RECONCILIATION_REQUIRED\\",\\"pid\\":%d,\\"catalog_presence\\":%d}\\n",e->pid,present);continue;}
          int valid=eligible&&catalog(&e->request,e->pid,tick_us()+ctx.experimental_abort_us);
          if(!valid&&!e->cancelling){e->detected=tick_us();e->cancelling=1;int rc=-1;if(access(TEST_DIR "/cancel-failure",F_OK)!=0)rc=syscall(SYS_pidfd_send_signal,e->fd,SIGINT,NULL,0);
             printf("{\\"event\\":\\"QUARANTINE\\",\\"pid\\":%d,\\"slot\\":%u,\\"signal_rc\\":%d,\\"at_us\\":%llu}\\n",e->pid,e->slot,rc,(unsigned long long)e->detected);}
          if(e->cancelling&&tick_us()-e->detected>=200000){int rc=-1;if(access(TEST_DIR "/terminate-failure",F_OK)!=0)rc=syscall(SYS_pidfd_send_signal,e->fd,SIGTERM,NULL,0);
             printf("{\\"event\\":\\"DRAINING\\",\\"pid\\":%d,\\"signal_rc\\":%d,\\"at_us\\":%llu}\\n",e->pid,rc,(unsigned long long)tick_us());e->detected=tick_us();}
        }
        if(!alive(supervisor)){printf("{\\"event\\":\\"supervisor_lost\\"}\\n");syscall(SYS_pidfd_send_signal,postmaster,SIGINT,NULL,0);break;}
'''+s[end:]
            s=s.replace('registry[index].slot=r.slot;','registry[index].slot=r.slot;registry[index].request=r;registry[index].pid=mc.pid;registry[index].cancelling=0;')
            s=s.replace('        if(!catalog(&r,mc.pid,begin+ctx.experimental_abort_us))','        for(unsigned j=0;j<used;j++)if(registry[j].fd>=0&&registry[j].cancelling){reason=11;goto answer;}\n        if(!catalog(&r,mc.pid,begin+ctx.experimental_abort_us))')
            s=s.replace('    printf("{\\"event\\":\\"receiver_armed\\",\\"atomic_postmaster_anchor\\":true}\\n");', '''    char epoch_hex[65];for(unsigned j=0;j<32;j++)sprintf(epoch_hex+j*2,"%02x",ctx.epoch[j]);struct stat supervisor_stat,postmaster_stat;fstat(supervisor,&supervisor_stat);fstat(postmaster,&postmaster_stat);
    printf("{\\"event\\":\\"receiver_armed\\",\\"epoch\\":\\"%s\\",\\"supervisor_inode\\":%llu,\\"postmaster_inode\\":%llu,\\"at_us\\":%llu}\\n",epoch_hex,(unsigned long long)supervisor_stat.st_ino,(unsigned long long)postmaster_stat.st_ino,(unsigned long long)tick_us());''')
            s=s.replace('if(!context_matches(&ctx,&r))','if(!text_nfc((unsigned char *)r.role_name,strlen(r.role_name))||!text_nfc((unsigned char *)r.db_name,strlen(r.db_name))||!context_matches(&ctx,&r))')
        elif name=='supervisor.c':
            s=s.replace('char *receiver_args[]={"/usr/local/bin/flooow-test-receiver",ctext,fdtext,NULL};','int supervisor_anchor=syscall(SYS_pidfd_open,getpid(),0);if(supervisor_anchor<0||fcntl(supervisor_anchor,F_SETFD,0))return 70;char stext[24];snprintf(stext,sizeof(stext),"%d",supervisor_anchor);\n    char *receiver_args[]={"/usr/local/bin/flooow-test-receiver",ctext,fdtext,stext,NULL};')
            s=s.replace('        if(access(TEST_DIR "/kill-receiver"', '        if(access(TEST_DIR "/crash-supervisor",F_OK)==0)_exit(86);\n        if(access(TEST_DIR "/kill-receiver"')
        elif name=='frame_tests.c':
            s=s.replace('    printf(', '''    const unsigned char *good=(const unsigned char *)"caf\\xc3\\xa9";
    if(!text_nfc(good,5))return 70;total++;
    const unsigned char invalid[][8]={{0xc0,0xaf},{0xed,0xa0,0x80},{0xf4,0x90,0x80,0x80},{0xc3,0},{'a',0,'b'},{'e',0xcc,0x81},{0x7f},{0xff}};
    unsigned lengths[]={2,3,4,2,3,3,1,1};for(unsigned i=0;i<8;i++){if(text_nfc(invalid[i],lengths[i]))return 70;total++;}
    printf(''').replace('ASCII_FIXTURE_SUBSET','UTF8_NFC_ICU76')
        (HERE/name).write_bytes(s.encode())
if __name__=='__main__':prepare()
