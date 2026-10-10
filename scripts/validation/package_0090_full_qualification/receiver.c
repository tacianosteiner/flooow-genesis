/* Disposable receiver. Test fixtures + kernel anchors, no canonical connection. */
#include "protocol.h"
#include <libpq-fe.h>
typedef struct {int fd;uint8_t slot;unsigned char digest[32];request_fields request;pid_t pid;int cancelling;uint64_t detected;} entry;
static entry registry[128];static unsigned used;
static test_context current;
static int catalog(const request_fields *r,pid_t sender_pid,uint64_t until){
    health_gate gate;if(!read_gate(&current,&gate))return 0;
    PGconn *db=PQconnectStart("host=/tmp/pgsock dbname=native_fixture user=postgres");
    if(!db)return 0;
    for(;;){PostgresPollingStatusType state=PQconnectPoll(db);if(state==PGRES_POLLING_OK)break;
        if(state!=PGRES_POLLING_READING && state!=PGRES_POLLING_WRITING){PQfinish(db);return 0;}
        if(!wait_fd(PQsocket(db),state==PGRES_POLLING_READING?POLLIN:POLLOUT,until)){PQfinish(db);return 0;}}
    if(PQsetnonblocking(db,1)){PQfinish(db);return 0;}
    char roid[24],doid[24],slot[8],start[32];snprintf(roid,sizeof(roid),"%u",r->role);snprintf(doid,sizeof(doid),"%u",r->db);snprintf(slot,sizeof(slot),"%u",r->slot);snprintf(start,sizeof(start),"%lld",(long long)r->postmaster_start);
    char pid[24],backend[32];snprintf(pid,sizeof(pid),"%d",sender_pid);snprintf(backend,sizeof(backend),"%lld",(long long)r->backend_start);
    const char *v[]={roid,r->role_name,doid,r->db_name,slot,start,pid,backend};
    if(access(TEST_DIR "/catalog-stall",F_OK)==0){
        if(!PQsendQuery(db,"SELECT pg_sleep(7)")){PQfinish(db);return 0;}
        while(PQisBusy(db)){if(!wait_fd(PQsocket(db),POLLIN,until)||!PQconsumeInput(db)){PQfinish(db);return 0;}}
        PQfinish(db);return 0;
    }
    if(!PQsendQueryParams(db,"SELECT to_jsonb(full_header)::text FROM public.flooow_test_binding h JOIN public.offline_binding_header full_header ON true JOIN public.offline_binding_lifecycle lifecycle ON lifecycle.binding_id=full_header.binding_id AND lifecycle.state='ACTIVE' JOIN pg_catalog.pg_roles a ON a.oid=h.role_oid JOIN pg_catalog.pg_database d ON d.oid=$3::oid JOIN pg_catalog.pg_stat_activity s ON s.pid=$7::int WHERE h.role_oid=$1::oid AND h.role_name=$2 AND a.rolname=$2 AND d.datname=$4 AND h.slot=$5::int AND s.usesysid=a.oid AND s.datid=d.oid AND s.backend_type='client backend' AND (extract(epoch from s.backend_start)*1000000-946684800000000)::bigint=$8::bigint AND (extract(epoch from pg_postmaster_start_time())*1000000-946684800000000)::bigint=$6::bigint AND a.rolcanlogin AND NOT a.rolinherit AND NOT a.rolsuper AND NOT a.rolcreaterole AND NOT a.rolcreatedb AND NOT a.rolreplication AND NOT a.rolbypassrls AND NOT EXISTS(SELECT 1 FROM pg_catalog.pg_auth_members m WHERE m.member=a.oid OR m.roleid=a.oid)",8,NULL,v,NULL,NULL,0)){PQfinish(db);return 0;}
    for(;;){int flushed=PQflush(db);if(flushed==0)break;if(flushed<0||!wait_fd(PQsocket(db),POLLOUT,until)){PQfinish(db);return 0;}}
    while(PQisBusy(db)){if(!wait_fd(PQsocket(db),POLLIN,until)||!PQconsumeInput(db)){PQfinish(db);return 0;}}
    PGresult *q=PQgetResult(db);int ok=q && PQresultStatus(q)==PGRES_TUPLES_OK && PQntuples(q)==1;
    if(ok){unsigned char hash[32];SHA256((unsigned char *)PQgetvalue(q,0,0),strlen(PQgetvalue(q,0,0)),hash);ok=!memcmp(hash,gate.header,32);}
    if(q)PQclear(q);PQfinish(db);return ok;
}
/* Authoritative catalog disappearance is independent of eligibility predicates. */
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
int main(int argc,char **argv){
    if(argc!=4)return 64;int supervisor=atoi(argv[3]);int ctl=atoi(argv[1]),ctxfd=atoi(argv[2]),postmaster=-1,one=1;test_context ctx;
    setvbuf(stdout,NULL,_IOLBF,0);
    if(pread(ctxfd,&ctx,sizeof(ctx),0)!=(ssize_t)sizeof(ctx))return 70;
    current=ctx;
    int parent_peer=-1;socklen_t parent_len=sizeof(parent_peer);if(getsockopt(ctl,SOL_SOCKET,SO_PEERPIDFD,&parent_peer,&parent_len)||!anchor_equal(parent_peer,supervisor)||!alive(supervisor))return 70;close(parent_peer);
    /* Only the supervisor's inherited socketpair can arm this receiver. */
    {unsigned char marker;char ctrl[CMSG_SPACE(sizeof(int))]={0};struct iovec i={&marker,1};struct msghdr m={.msg_iov=&i,.msg_iovlen=1,.msg_control=ctrl,.msg_controllen=sizeof(ctrl)};
     if(recvmsg(ctl,&m,MSG_CMSG_CLOEXEC)!=1||marker!=0xa1)return 70;
     struct cmsghdr *x=CMSG_FIRSTHDR(&m);if(!x||x->cmsg_type!=SCM_RIGHTS||x->cmsg_len!=CMSG_LEN(sizeof(int)))return 70;memcpy(&postmaster,CMSG_DATA(x),sizeof(int));}
    if(!alive(postmaster))return 70;
    int listener=socket(AF_UNIX,SOCK_SEQPACKET|SOCK_CLOEXEC|SOCK_NONBLOCK,0);
    struct sockaddr_un addr={.sun_family=AF_UNIX};strcpy(addr.sun_path,TEST_SOCKET);
    struct stat st;if(lstat(TEST_DIR,&st)||!S_ISDIR(st.st_mode)||st.st_uid!=getuid()||(st.st_mode&0777)!=0700)return 70;
    if(!lstat(TEST_SOCKET,&st))return 70;
    if(setsockopt(listener,SOL_SOCKET,SO_PASSCRED,&one,sizeof(one))||setsockopt(listener,SOL_SOCKET,SO_PASSPIDFD,&one,sizeof(one)))return 70;
    umask(0077);if(bind(listener,(struct sockaddr *)&addr,sizeof(addr))||chmod(TEST_SOCKET,0600)||listen(listener,32))return 70;
    char epoch_hex[65];for(unsigned j=0;j<32;j++)sprintf(epoch_hex+j*2,"%02x",ctx.epoch[j]);struct stat supervisor_stat,postmaster_stat;fstat(supervisor,&supervisor_stat);fstat(postmaster,&postmaster_stat);
    printf("{\"event\":\"receiver_armed\",\"epoch\":\"%s\",\"supervisor_inode\":%llu,\"postmaster_inode\":%llu,\"at_us\":%llu}\n",epoch_hex,(unsigned long long)supervisor_stat.st_ino,(unsigned long long)postmaster_stat.st_ino,(unsigned long long)tick_us());
    for(;;){
        health_gate health;int eligible=alive(supervisor)&&alive(postmaster)&&read_gate(&ctx,&health);
        for(unsigned i=0;i<used;i++)if(registry[i].fd>=0){entry *e=&registry[i];
          if(!alive(e->fd)){printf("{\"event\":\"kernel_death\",\"pid\":%d,\"slot\":%u,\"at_us\":%llu}\n",e->pid,e->slot,(unsigned long long)tick_us());e->cancelling=1;
             int present=session_present(e,tick_us()+ctx.experimental_abort_us);
             if(present==0){printf("{\"event\":\"DRAINED\",\"pid\":%d,\"catalog_disappeared\":true,\"effects\":\"RECONCILIATION_REQUIRED\",\"at_us\":%llu}\n",e->pid,(unsigned long long)tick_us());close(e->fd);e->fd=-1;}
             else printf("{\"event\":\"RECONCILIATION_REQUIRED\",\"pid\":%d,\"catalog_presence\":%d}\n",e->pid,present);continue;}
          int valid=eligible&&catalog(&e->request,e->pid,tick_us()+ctx.experimental_abort_us);
          if(!valid&&!e->cancelling){e->detected=tick_us();e->cancelling=1;int rc=-1;if(access(TEST_DIR "/cancel-failure",F_OK)!=0)rc=syscall(SYS_pidfd_send_signal,e->fd,SIGINT,NULL,0);
             printf("{\"event\":\"QUARANTINE\",\"pid\":%d,\"slot\":%u,\"signal_rc\":%d,\"at_us\":%llu}\n",e->pid,e->slot,rc,(unsigned long long)e->detected);}
          if(e->cancelling&&tick_us()-e->detected>=200000){int rc=-1;if(access(TEST_DIR "/terminate-failure",F_OK)!=0)rc=syscall(SYS_pidfd_send_signal,e->fd,SIGTERM,NULL,0);
             printf("{\"event\":\"DRAINING\",\"pid\":%d,\"signal_rc\":%d,\"at_us\":%llu}\n",e->pid,rc,(unsigned long long)tick_us());e->detected=tick_us();}
        }
        if(!alive(supervisor)){printf("{\"event\":\"supervisor_lost\"}\n");syscall(SYS_pidfd_send_signal,postmaster,SIGINT,NULL,0);break;}
        struct pollfd ps[3]={{listener,POLLIN,0},{postmaster,POLLIN,0},{ctl,POLLIN,0}};
        if(poll(ps,3,20)<0){if(errno==EINTR)continue;break;}
        if(ps[1].revents||ps[2].revents){printf("{\"event\":\"control_generation_invalidated\"}\n");break;}
        if(!(ps[0].revents&POLLIN))continue;
        int fd=accept4(listener,NULL,NULL,SOCK_CLOEXEC|SOCK_NONBLOCK);if(fd<0)continue;
        uint64_t begin=tick_us(),received=0,validated=0;int peer=-1,sender=-1,supplied=-1,rcount=0,pcount=0,ccount=0,extra=0,reason=1,duplicate=0;struct ucred cred={0},mc={0};socklen_t len=sizeof(cred),plen=sizeof(peer);
        unsigned char b[FRAME_MAX],reply[80],digest[32]={0};request_fields r={0};ssize_t n=-1;
        if(getsockopt(fd,SOL_SOCKET,SO_PEERCRED,&cred,&len)||getsockopt(fd,SOL_SOCKET,SO_PEERPIDFD,&peer,&plen))goto answer;
        if(!wait_fd(fd,POLLIN,begin+ctx.experimental_abort_us)){reason=10;goto answer;}
        {union{struct cmsghdr a;char bytes[512];}control={0};struct iovec i={b,sizeof(b)};struct msghdr m={.msg_iov=&i,.msg_iovlen=1,.msg_control=control.bytes,.msg_controllen=sizeof(control.bytes)};
         n=recvmsg(fd,&m,MSG_CMSG_CLOEXEC|MSG_DONTWAIT);received=tick_us();
         for(struct cmsghdr *x=CMSG_FIRSTHDR(&m);x;x=CMSG_NXTHDR(&m,x)){
            if(x->cmsg_level!=SOL_SOCKET){extra++;continue;}
            if(x->cmsg_type==SCM_RIGHTS){size_t count=(x->cmsg_len-CMSG_LEN(0))/sizeof(int);int *fds=(int *)CMSG_DATA(x);for(size_t j=0;j<count;j++){if(!rcount)supplied=fds[j];else close(fds[j]);rcount++;}}
            else if(x->cmsg_type==SCM_PIDFD&&x->cmsg_len==CMSG_LEN(sizeof(int))){int v;memcpy(&v,CMSG_DATA(x),sizeof(v));if(pcount)close(v);else sender=v;pcount++;}
            else if(x->cmsg_type==SCM_CREDENTIALS&&x->cmsg_len==CMSG_LEN(sizeof(mc))){memcpy(&mc,CMSG_DATA(x),sizeof(mc));ccount++;}
            else extra++;
         }
         if(n<0||m.msg_flags&(MSG_TRUNC|MSG_CTRUNC)||extra||rcount!=1||pcount!=1||ccount!=1||!decode_request(b,(size_t)n,&r))goto answer;
        }
        SHA256(b,(size_t)n,digest);
        if(cred.uid!=getuid()||cred.gid!=getgid()||mc.uid!=cred.uid||mc.gid!=cred.gid||!anchor_equal(peer,sender)||!anchor_equal(sender,supplied)||!alive(peer)||!alive(sender)||!alive(supplied)){reason=6;goto answer;}
        if(!text_nfc((unsigned char *)r.role_name,strlen(r.role_name))||!text_nfc((unsigned char *)r.db_name,strlen(r.db_name))||!context_matches(&ctx,&r)){reason=3;goto answer;}
        for(unsigned j=0;j<used;j++)if(registry[j].fd>=0&&registry[j].cancelling){reason=11;goto answer;}
        if(!catalog(&r,mc.pid,begin+ctx.experimental_abort_us)){reason=tick_us()>=begin+ctx.experimental_abort_us?10:4;goto answer;}validated=tick_us();
        /* Fault injection is owned fixture configuration, never service input. */
        if(access(TEST_DIR "/drop-ack",F_OK)==0){reason=9;goto cleanup;}
        if(access(TEST_DIR "/delay-ack",F_OK)==0){struct timespec pause={6,0};nanosleep(&pause,NULL);reason=10;goto answer;}
        if(!alive(postmaster)||!alive(supplied)||tick_us()>=begin+ctx.experimental_abort_us){reason=7;goto answer;}
        for(unsigned i=0;i<used;i++)if(registry[i].fd>=0&&anchor_equal(registry[i].fd,supplied)){
            if(registry[i].slot!=r.slot||memcmp(registry[i].digest,digest,32)){reason=8;goto answer;}duplicate=1;
        }
        if(!duplicate){unsigned index=used;for(unsigned i=0;i<used;i++)if(registry[i].fd<0){index=i;break;}if(index==128){reason=8;goto answer;}registry[index].fd=supplied;registry[index].slot=r.slot;registry[index].request=r;registry[index].pid=mc.pid;registry[index].cancelling=0;memcpy(registry[index].digest,digest,32);if(index==used)used++;supplied=-1;}
        reason=0;
answer:
        header(reply,reason?3:2,reason?66:64);memcpy(reply+12,ctx.epoch,32);memcpy(reply+44,digest,32);if(reason){reply[76]=0;reply[77]=(unsigned char)reason;}
        if(wait_fd(fd,POLLOUT,begin+ctx.experimental_abort_us))send(fd,reply,reason?78:76,MSG_NOSIGNAL|MSG_DONTWAIT);
        printf("{\"event\":\"%s\",\"role_oid\":%u,\"slot\":%u,\"reason\":%d,\"duplicate\":%s,\"receive_us\":%llu,\"validation_us\":%llu,\"reply_us\":%llu}\n",reason?"DENY":"ACCEPT",r.role,r.slot,reason,duplicate?"true":"false",(unsigned long long)(received?received-begin:0),(unsigned long long)(validated&&received?validated-received:0),(unsigned long long)(tick_us()-begin));
cleanup:
        if(peer>=0)close(peer);if(sender>=0)close(sender);if(supplied>=0)close(supplied);close(fd);
    }
    for(unsigned i=0;i<used;i++)if(registry[i].fd>=0)close(registry[i].fd);
    close(postmaster);close(listener);close(ctl);return 0;
}
