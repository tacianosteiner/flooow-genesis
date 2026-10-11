/* Independent disposable census/enforcer. Retained anchors only select signals. */
#include "protocol.h"
#include "quarantine.h"
#include "process_class.h"
#include <libpq-fe.h>
typedef struct {int fd;pid_t pid;request_fields r;} retained;
static retained anchors[128];static unsigned count;static observation_state *shared;
static request_fields unknown_identity[128];static pid_t unknown_pid[128];static unsigned unknown_n;static unsigned char unknown_anchored[128];static int unknown_overflow;
static test_context ctx;static int pm=-1,sup=-1,receiver=-1,frozen=0;
static int enforced;
typedef struct {
    uint64_t started_us,revision,parent_inode[3],inode[128],enrollment_revision[128];
    unsigned phase[128];int live[128],parent_live[3],valid;unsigned char epoch[32];
} census_observation;
static census_observation snapshot;
static int generation_matches_snapshot(void){
    int anchors_by_generation[3]={sup,receiver,pm};struct stat st;
    if(memcmp(snapshot.epoch,ctx.epoch,32))return 0;
    for(unsigned i=0;i<3;i++)if(fstat(anchors_by_generation[i],&st)||(uint64_t)st.st_ino!=snapshot.parent_inode[i])return 0;
    return 1;
}
static void capture_census_context(void){
    memset(&snapshot,0,sizeof(snapshot));snapshot.started_us=tick_us();snapshot.revision=atomic_load_explicit(&shared->registry_revision,memory_order_acquire);memcpy(snapshot.epoch,ctx.epoch,32);
    int parents[3]={sup,receiver,pm};struct stat st;int valid=1;
    for(unsigned i=0;i<3;i++){if(fstat(parents[i],&st))valid=0;else snapshot.parent_inode[i]=st.st_ino;snapshot.parent_live[i]=alive(parents[i]);}
    for(unsigned i=0;i<count;i++){
        snapshot.phase[i]=atomic_load_explicit(&shared->entries[i].phase,memory_order_acquire);
        snapshot.inode[i]=shared->entries[i].inode;snapshot.enrollment_revision[i]=atomic_load(&shared->entries[i].enrollment_revision);snapshot.live[i]=alive(anchors[i].fd);
    }
    snapshot.valid=valid&&snapshot.revision==atomic_load_explicit(&shared->registry_revision,memory_order_acquire);
}
/* 0 lost generation, 1 current, 2 stale: stale is never absence or eligibility. */
static int census_applicability(void){
    if(!generation_matches_snapshot())return 0;
    int parents[3]={sup,receiver,pm};for(unsigned i=0;i<3;i++)if(alive(parents[i])!=snapshot.parent_live[i])return 2;
    if(!snapshot.valid||snapshot.revision!=atomic_load_explicit(&shared->registry_revision,memory_order_acquire))return 2;
    for(unsigned i=0;i<count;i++){
        unsigned phase=atomic_load_explicit(&shared->entries[i].phase,memory_order_acquire);struct stat st;
        if(phase!=snapshot.phase[i]||shared->entries[i].inode!=snapshot.inode[i]||fstat(anchors[i].fd,&st)||(uint64_t)st.st_ino!=snapshot.inode[i]||alive(anchors[i].fd)!=snapshot.live[i]||atomic_load(&shared->entries[i].enrollment_revision)!=snapshot.enrollment_revision[i]||(phase==2&&atomic_load(&shared->entries[i].enrolled_us)>=snapshot.started_us))return 2;
    }
    return snapshot.revision==atomic_load_explicit(&shared->registry_revision,memory_order_acquire)?1:2;
}
static void event(const char *classification,pid_t pid){
    printf("{\"event\":\"independent_observer\",\"classification\":\"%s\",\"pid\":%d,\"at_us\":%llu}\n",classification,pid,(unsigned long long)tick_us());
    if(!strcmp(classification,"STALE_CENSUS_OBSERVATION_IGNORED"))printf("{\"event\":\"census_snapshot_ignored\",\"snapshot_started_us\":%llu,\"snapshot_revision\":%llu,\"current_revision\":%llu,\"supervisor_inode\":%llu,\"receiver_inode\":%llu,\"postmaster_inode\":%llu}\n",(unsigned long long)snapshot.started_us,(unsigned long long)snapshot.revision,(unsigned long long)atomic_load(&shared->registry_revision),(unsigned long long)snapshot.parent_inode[0],(unsigned long long)snapshot.parent_inode[1],(unsigned long long)snapshot.parent_inode[2]);
}
static void quarantine(const char *reason){
    atomic_store(&shared->quarantined,1);
    if(!frozen){frozen=1;
        event("QUARANTINED_PENDING_RECONCILIATION",0);printf("{\"event\":\"quarantine_frozen_anchor_set\",\"reason\":\"%s\",\"N\":%u,\"at_us\":%llu}\n",reason,count,(unsigned long long)tick_us());
        /* Stop every known participant before the potentially blocking witness.
         * Pending unknown sessions cannot receive ACCEPT after the atomic latch. */
        for(unsigned i=0;i<count;i++)if(alive(anchors[i].fd))syscall(SYS_pidfd_send_signal,anchors[i].fd,SIGSTOP,NULL,0);
        for(unsigned i=0;i<count;i++){struct stat st;fstat(anchors[i].fd,&st);printf("{\"event\":\"frozen_retained_anchor\",\"inode\":%llu,\"pid\":%d,\"role_oid\":%u,\"database_oid\":%u,\"backend_start\":%lld,\"postmaster_start\":%lld,\"phase\":%u}\n",(unsigned long long)st.st_ino,anchors[i].pid,anchors[i].r.role,anchors[i].r.db,(long long)anchors[i].r.backend_start,(long long)anchors[i].r.postmaster_start,atomic_load(&shared->entries[i].phase));}
    }
}
static PGresult *census(uint64_t until){
    memset(&snapshot,0,sizeof(snapshot));PGconn *db=PQconnectStart("host=/tmp/pgsock dbname=native_fixture user=postgres");if(!db)return NULL;
    for(;;){PostgresPollingStatusType s=PQconnectPoll(db);if(s==PGRES_POLLING_OK)break;if((s!=PGRES_POLLING_READING&&s!=PGRES_POLLING_WRITING)||!wait_fd(PQsocket(db),s==PGRES_POLLING_READING?POLLIN:POLLOUT,until)){PQfinish(db);return NULL;}}
    if(PQsetnonblocking(db,1)){PQfinish(db);return NULL;}char oid[4][24];const char *v[8];for(unsigned i=0;i<4;i++){snprintf(oid[i],sizeof(oid[i]),"%u",ctx.role_oid[i]);v[i]=oid[i];v[i+4]=ctx.role_name[i];}capture_census_context();
    if(!PQsendQueryParams(db,"SELECT pid,usesysid,datid,(extract(epoch from backend_start)*1000000-946684800000000)::bigint,(extract(epoch from pg_postmaster_start_time())*1000000-946684800000000)::bigint,usename,backend_type,(usesysid IN ($1::oid,$2::oid,$3::oid,$4::oid) OR usename IN ($5,$6,$7,$8)) FROM pg_stat_activity",8,NULL,v,NULL,NULL,0)){PQfinish(db);return NULL;}
    while(PQisBusy(db)){if(!wait_fd(PQsocket(db),POLLIN,until)||!PQconsumeInput(db)){PQfinish(db);return NULL;}}
    PGresult *r=PQgetResult(db);if(!r||PQresultStatus(r)!=PGRES_TUPLES_OK){if(r)PQclear(r);r=NULL;}PQfinish(db);
    if(access(TEST_DIR "/census-response-pause",F_OK)==0){struct timespec pause={0,500000000};nanosleep(&pause,NULL);}return r;
}
static int census_has_relevant_rows(PGresult *r){
    if(!r)return 1;
    for(int row=0;row<PQntuples(r);row++)if(PQnfields(r)!=8||process_class(PQgetvalue(r,row,6),!strcmp(PQgetvalue(r,row,7),"t"))!=2)return 1;
    return 0;
}
static int observe(PGresult *r){
    unsigned char seen[128]={0};int good=r!=NULL;if(!r){event("AMBIGUOUS",0);return 0;}
    int applicable=census_applicability();if(applicable!=1){event(applicable==2?"STALE_CENSUS_OBSERVATION_IGNORED":"GENERATION_MISMATCH",0);return applicable;}
    for(int row=0;row<PQntuples(r);row++){
        if(PQnfields(r)!=8){quarantine("UNKNOWN_CENSUS_SHAPE");unknown_overflow=1;return 0;}
        int classification=process_class(PQgetvalue(r,row,6),!strcmp(PQgetvalue(r,row,7),"t"));
        printf("{\"event\":\"census_process_class\",\"pid\":%s,\"type\":\"%s\",\"class\":%d}\n",PQgetvalue(r,row,0),PQgetvalue(r,row,6),classification);
        if(classification==2)continue;
        if(classification==0){quarantine("UNKNOWN_PROCESS_TYPE");unknown_overflow=1;good=0;continue;}
        pid_t pid=atoi(PQgetvalue(r,row,0));int matches=0;const char *c="BACKEND_NOT_REGISTERED";
        for(unsigned i=0;i<count;i++)if(anchors[i].pid==pid){
            matches+=seen[i]?2:1;seen[i]=1;request_fields *e=&anchors[i].r;
            c=e->postmaster_start!=strtoll(PQgetvalue(r,row,4),NULL,10)?"GENERATION_MISMATCH":
              e->role!=strtoul(PQgetvalue(r,row,1),NULL,10)||e->db!=strtoul(PQgetvalue(r,row,2),NULL,10)||e->backend_start!=strtoll(PQgetvalue(r,row,3),NULL,10)||strcmp(e->role_name,PQgetvalue(r,row,5))?"IDENTITY_MISMATCH":"MATCHED";
        }
        applicable=census_applicability();if(applicable!=1){event(applicable==2?"STALE_CENSUS_OBSERVATION_IGNORED":"GENERATION_MISMATCH",pid);return applicable;}
        if(matches>1)c="AMBIGUOUS";event(c,pid);if(strcmp(c,"MATCHED")){good=0;quarantine("CENSUS_INCONSISTENCY");}
        printf("{\"event\":\"independent_census_identity\",\"pid\":%d,\"role_oid\":%s,\"database_oid\":%s,\"backend_start\":%s,\"postmaster_start\":%s,\"classification\":\"%s\"}\n",pid,PQgetvalue(r,row,1),PQgetvalue(r,row,2),PQgetvalue(r,row,3),PQgetvalue(r,row,4),c);
        if(!matches){unsigned j=0;for(;j<unknown_n;j++)if(unknown_pid[j]==pid&&unknown_identity[j].backend_start==strtoll(PQgetvalue(r,row,3),NULL,10))break;
            if(j==unknown_n&&j<128){unknown_pid[j]=pid;unknown_identity[j].role=strtoul(PQgetvalue(r,row,1),NULL,10);unknown_identity[j].db=strtoul(PQgetvalue(r,row,2),NULL,10);unknown_identity[j].backend_start=strtoll(PQgetvalue(r,row,3),NULL,10);unknown_identity[j].postmaster_start=strtoll(PQgetvalue(r,row,4),NULL,10);snprintf(unknown_identity[j].role_name,64,"%s",PQgetvalue(r,row,5));unknown_n++;}
            else if(j==unknown_n){unknown_overflow=1;event("AMBIGUOUS_OBSERVATION_CAPACITY_EXCEEDED",pid);}}
    }
    for(unsigned i=0;i<count;i++)if(!seen[i]){
        applicable=census_applicability();if(applicable!=1){event(applicable==2?"STALE_CENSUS_OBSERVATION_IGNORED":"GENERATION_MISMATCH",anchors[i].pid);return applicable;}
        if(alive(anchors[i].fd)&&snapshot.phase[i]>=2){
            if(atomic_load(&shared->quarantined)){event("QUARANTINED_PENDING_RECONCILIATION",anchors[i].pid);continue;}
            unsigned phase=snapshot.phase[i];if(!atomic_compare_exchange_strong(&shared->entries[i].phase,&phase,3))return 2;if(phase!=3)atomic_fetch_add(&shared->registry_revision,1);event("REGISTRY_ENTRY_NO_BACKEND",anchors[i].pid);syscall(SYS_pidfd_send_signal,anchors[i].fd,SIGSTOP,NULL,0);
            event("QUARANTINED_PENDING_RECONCILIATION",anchors[i].pid);
            syscall(SYS_pidfd_send_signal,anchors[i].fd,SIGTERM,NULL,0);syscall(SYS_pidfd_send_signal,anchors[i].fd,SIGCONT,NULL,0);return 2;}
        else if(!alive(anchors[i].fd)&&atomic_load(&shared->entries[i].phase)){event("CONFIRMED_GONE",anchors[i].pid);atomic_store_explicit(&shared->entries[i].phase,0,memory_order_release);atomic_fetch_add(&shared->registry_revision,1);return 2;}
        else if(alive(anchors[i].fd))event("PENDING_AUTH_NOT_YET_VISIBLE",anchors[i].pid);
    }
    applicable=census_applicability();if(good&&applicable!=1){event(applicable==2?"STALE_CENSUS_OBSERVATION_IGNORED":"GENERATION_MISMATCH",0);return applicable;}return good;
}
static int apply_census(PGresult *r){
    int result=observe(r);
    if(result==1){int current=census_applicability();if(current!=1)return current;
        if(!atomic_load(&shared->quarantined)&&alive(sup)&&alive(receiver)&&alive(pm))atomic_store(&shared->armed,1);
    }else if(!result)quarantine("CENSUS_INCONSISTENCY");
    return result;
}
static void pending(int listener){
    int fd=accept4(listener,NULL,NULL,SOCK_CLOEXEC|SOCK_NONBLOCK);if(fd<0)return;
    uint64_t until=tick_us()+ctx.experimental_abort_us;int peer=-1,self=-1,sender=-1;struct ucred cred,mc={0};socklen_t n=sizeof(peer),cn=sizeof(cred);request_fields r={0};unsigned char b[FRAME_MAX];
    union {struct cmsghdr align;char bytes[256];} ancillary={0};struct iovec i={b,sizeof(b)};struct msghdr m={.msg_iov=&i,.msg_iovlen=1,.msg_control=ancillary.bytes,.msg_controllen=sizeof(ancillary.bytes)};
    int ok=!getsockopt(fd,SOL_SOCKET,SO_PEERPIDFD,&peer,&n)&&!getsockopt(fd,SOL_SOCKET,SO_PEERCRED,&cred,&cn)&&cred.uid==getuid()&&cred.gid==getgid()&&wait_fd(fd,POLLIN,until);
    ssize_t got=ok?recvmsg(fd,&m,MSG_CMSG_CLOEXEC|MSG_DONTWAIT):-1;unsigned rights=0,extra=0,pidfds=0,credentials=0;
    for(struct cmsghdr *c=CMSG_FIRSTHDR(&m);c;c=CMSG_NXTHDR(&m,c)){
        if(c->cmsg_level==SOL_SOCKET&&c->cmsg_type==SCM_RIGHTS){size_t total=(c->cmsg_len-CMSG_LEN(0))/sizeof(int);int *p=(int *)CMSG_DATA(c);for(size_t j=0;j<total;j++){if(!rights)self=p[j];else close(p[j]);rights++;}}
        else if(c->cmsg_level==SOL_SOCKET&&c->cmsg_type==SCM_PIDFD&&c->cmsg_len==CMSG_LEN(sizeof(int))){int value;memcpy(&value,CMSG_DATA(c),sizeof(value));if(pidfds)close(value);else sender=value;pidfds++;}
        else if(c->cmsg_level==SOL_SOCKET&&c->cmsg_type==SCM_CREDENTIALS&&c->cmsg_len==CMSG_LEN(sizeof(mc))){memcpy(&mc,CMSG_DATA(c),sizeof(mc));credentials++;}
        else extra++;
    }
    ok=ok&&got>0&&!(m.msg_flags&(MSG_TRUNC|MSG_CTRUNC))&&rights==1&&pidfds==1&&credentials==1&&!extra&&decode_request(b,(size_t)got,&r)&&context_matches(&ctx,&r)&&anchor_equal(peer,self)&&anchor_equal(sender,self)&&mc.uid==cred.uid&&mc.gid==cred.gid&&alive(self);
    int duplicate=0;for(unsigned j=0;j<count;j++)if(anchor_equal(anchors[j].fd,self)){duplicate=1;ok=ok&&!memcmp(&anchors[j].r,&r,sizeof(r));}
    if(ok&&!duplicate){unsigned j=count;if(j==128)ok=0;
        else {if(j<count)close(anchors[j].fd);anchors[j]=(retained){.fd=self,.pid=cred.pid,.r=r};struct stat st;fstat(self,&st);shared->entries[j].inode=st.st_ino;shared->entries[j].pid=cred.pid;shared->entries[j].request=r;atomic_store_explicit(&shared->entries[j].phase,1,memory_order_release);atomic_fetch_add(&shared->registry_revision,1);self=-1;if(j==count)count++;event("PENDING_RETAINED_ANCHOR",cred.pid);
            if(atomic_load(&shared->quarantined)){atomic_store(&shared->outcome_confirmed,0);enforced=0;syscall(SYS_pidfd_send_signal,anchors[j].fd,SIGSTOP,NULL,0);event("LATE_QUARANTINE_ANCHOR_FROZEN",cred.pid);
                printf("{\"event\":\"late_frozen_retained_anchor\",\"inode\":%llu,\"pid\":%d,\"role_oid\":%u,\"database_oid\":%u,\"backend_start\":%lld,\"postmaster_start\":%lld,\"phase\":1}\n",(unsigned long long)st.st_ino,cred.pid,r.role,r.db,(long long)r.backend_start,(long long)r.postmaster_start);
            }
        }}
    if(ok)for(unsigned j=0;j<unknown_n;j++)if(unknown_pid[j]==cred.pid&&unknown_identity[j].role==r.role&&unknown_identity[j].db==r.db&&unknown_identity[j].backend_start==r.backend_start&&unknown_identity[j].postmaster_start==r.postmaster_start&&!strcmp(unknown_identity[j].role_name,r.role_name)){unknown_anchored[j]=1;event("LATE_ANCHOR_EVIDENCE_ONLY",cred.pid);}
    unsigned char reply=ok&&!atomic_load(&shared->quarantined)?0xc1:0xc0;if(wait_fd(fd,POLLOUT,until))send(fd,&reply,1,MSG_NOSIGNAL);if(self>=0)close(self);if(sender>=0)close(sender);if(peer>=0)close(peer);close(fd);
}
int main(int argc,char **argv){
    if(argc!=7)return 64;int ctl=atoi(argv[1]),ctxfd=atoi(argv[2]);sup=atoi(argv[3]);receiver=atoi(argv[4]);shared=observation_map(atoi(argv[5]),1);int receiver_ctl=atoi(argv[6]);(void)receiver_ctl;
    if(!shared||pread(ctxfd,&ctx,sizeof(ctx),0)!=(ssize_t)sizeof(ctx)||!alive(sup)||!alive(receiver))return 70;setvbuf(stdout,NULL,_IOLBF,0);
    int parent=-1;socklen_t parent_length=sizeof(parent);if(getsockopt(ctl,SOL_SOCKET,SO_PEERPIDFD,&parent,&parent_length)||!anchor_equal(parent,sup)||!alive(parent))return 70;close(parent);
    unsigned char marker;char cb[CMSG_SPACE(sizeof(int))]={0};struct iovec iv={&marker,1};struct msghdr msg={.msg_iov=&iv,.msg_iovlen=1,.msg_control=cb,.msg_controllen=sizeof(cb)};
    if(recvmsg(ctl,&msg,MSG_CMSG_CLOEXEC)!=1||marker!=0xa1)return 70;struct cmsghdr *c=CMSG_FIRSTHDR(&msg);if(!c||c->cmsg_type!=SCM_RIGHTS||c->cmsg_len!=CMSG_LEN(sizeof(int)))return 70;memcpy(&pm,CMSG_DATA(c),sizeof(pm));
    int listener=socket(AF_UNIX,SOCK_SEQPACKET|SOCK_CLOEXEC|SOCK_NONBLOCK,0),one=1;struct sockaddr_un a={.sun_family=AF_UNIX};strcpy(a.sun_path,OBS_SOCKET);umask(0077);if(setsockopt(listener,SOL_SOCKET,SO_PASSPIDFD,&one,sizeof(one))||setsockopt(listener,SOL_SOCKET,SO_PASSCRED,&one,sizeof(one))||bind(listener,(struct sockaddr *)&a,sizeof(a))||chmod(OBS_SOCKET,0600)||listen(listener,32))return 70;
    int own=syscall(SYS_pidfd_open,getpid(),0);struct stat ss,rs,ps,os;fstat(sup,&ss);fstat(receiver,&rs);fstat(pm,&ps);fstat(own,&os);close(own);
    char epoch[65];for(unsigned j=0;j<32;j++)sprintf(epoch+j*2,"%02x",ctx.epoch[j]);
    printf("{\"event\":\"independent_observer_armed\",\"epoch\":\"%s\",\"supervisor_inode\":%llu,\"receiver_inode\":%llu,\"postmaster_inode\":%llu,\"observer_inode\":%llu,\"at_us\":%llu}\n",epoch,(unsigned long long)ss.st_ino,(unsigned long long)rs.st_ino,(unsigned long long)ps.st_ino,(unsigned long long)os.st_ino,(unsigned long long)tick_us());
    uint64_t start=tick_us(),next=start;
    for(;;){
        atomic_store(&shared->observer_progress,tick_us());
        if(access(TEST_DIR "/force-quarantine",F_OK)==0){unlink(TEST_DIR "/force-quarantine");quarantine("TEST_ONLY_CONTROLLED_QUARANTINE");}
        if(access(TEST_DIR "/stall-observer",F_OK)==0){unlink(TEST_DIR "/stall-observer");raise(SIGSTOP);}
        struct pollfd p={listener,POLLIN,0};if(poll(&p,1,20)>0)pending(listener);
        if(enforced==2&&!atomic_load(&shared->outcome_confirmed))enforced=0;
        uint64_t stamp=atomic_load(&shared->receiver_progress),parent_stamp=atomic_load(&shared->supervisor_progress);if(!alive(sup)||!alive(receiver)||(stamp?tick_us()-stamp>10000000:tick_us()-start>10000000)||(parent_stamp?tick_us()-parent_stamp>10000000:tick_us()-start>10000000))quarantine("PARTICIPANT_PROGRESS_LOST");
        if(atomic_load(&shared->quarantined))quarantine("EXTERNAL_QUARANTINE_LATCH");
        if(!alive(pm)){quarantine("POSTMASTER_GONE");event("AMBIGUOUS",0);break;}
        if(tick_us()<next)continue;next=tick_us()+100000;
        PGresult *r=census(tick_us()+ctx.experimental_abort_us);
        if(!atomic_load(&shared->armed)&&!r){if(tick_us()-start>10000000)quarantine("STARTUP_OBSERVATION_UNAVAILABLE");continue;}
        int observation_result=apply_census(r);
        if(atomic_load(&shared->quarantined)&&!enforced&&r&&observation_result!=2&&census_applicability()==1){
            /* Complete catalog classification while postmaster remains available.
             * The stop latch already prohibits admission; all known anchors stopped. */
            event(r?"QUARANTINE_CATALOG_CAPTURE_COMPLETE":"QUARANTINE_CATALOG_CAPTURE_UNKNOWN",0);
            if(access(TEST_DIR "/quarantine-enforcement-pause",F_OK)==0){struct timespec pause={0,500000000};nanosleep(&pause,NULL);}
            if(census_applicability()==1){for(unsigned j=0;j<count;j++)if(alive(anchors[j].fd)){syscall(SYS_pidfd_send_signal,anchors[j].fd,SIGTERM,NULL,0);syscall(SYS_pidfd_send_signal,anchors[j].fd,SIGCONT,NULL,0);}enforced=1;}
            else event("STALE_CENSUS_OBSERVATION_IGNORED",0);
        }else if(atomic_load(&shared->quarantined)&&!enforced)event("QUARANTINE_CATALOG_CAPTURE_UNKNOWN",0);
        if(r)PQclear(r);
        if(enforced==2&&(!alive(sup)||!alive(receiver))){event("CONFIRMED_OUTCOME_GENERATION_TEARDOWN",0);syscall(SYS_pidfd_send_signal,pm,SIGINT,NULL,0);break;}
        if(enforced==1){int dead=!unknown_overflow;for(unsigned j=0;j<count;j++)if(alive(anchors[j].fd))dead=0;for(unsigned j=0;j<unknown_n;j++)if(!unknown_anchored[j])dead=0;
            PGresult *after=census(tick_us()+ctx.experimental_abort_us);int absent=after&&!census_has_relevant_rows(after)&&census_applicability()==1;if(after)PQclear(after);
            for(unsigned j=0;j<count;j++)if(alive(anchors[j].fd))dead=0;
            if(dead&&absent&&census_applicability()==1){event("CONFIRMED_GONE",0);event("QUARANTINE_KERNEL_CATALOG_OUTCOME_CONFIRMED",0);
                /* Keep ADMIN observability and the monotonic quarantine latch.
                 * Fixture controller rotates only after effect reconciliation. */
                enforced=2;
                atomic_store(&shared->outcome_confirmed,1);
                if(!alive(sup)||!alive(receiver)){event("CONFIRMED_OUTCOME_GENERATION_TEARDOWN",0);syscall(SYS_pidfd_send_signal,pm,SIGINT,NULL,0);break;}
            }else event("QUARANTINED_PENDING_RECONCILIATION",0);
        }
    }
    for(unsigned i=0;i<count;i++)close(anchors[i].fd);close(listener);close(pm);return 0;
}
