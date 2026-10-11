/* TEST_ONLY_NONCANONICAL. Observation is never an eligibility publisher. */
#ifndef FLOOOW_QUARANTINE_H
#define FLOOOW_QUARANTINE_H
#include <stdatomic.h>
#include <sys/mman.h>
#define OBS_SOCKET TEST_DIR "/census-v1.sock"
typedef struct {
    _Atomic unsigned phase; /* 0 gone, 1 pending anchor, 2 receiver enrolled, 3 quarantined */
    _Atomic uint64_t enrolled_us,enrollment_revision;
    uint64_t inode; pid_t pid; request_fields request;
} observation_entry;
typedef struct {
    _Atomic unsigned quarantined;
    _Atomic unsigned armed;
    _Atomic unsigned outcome_confirmed;
    _Atomic uint64_t registry_revision;
    _Atomic uint64_t receiver_progress,observer_progress,supervisor_progress;
    observation_entry entries[128];
} observation_state;
static inline observation_state *observation_map(int fd,int writable){
    void *p=mmap(NULL,sizeof(observation_state),PROT_READ|(writable?PROT_WRITE:0),MAP_SHARED,fd,0);
    return p==MAP_FAILED?NULL:p;
}
static inline int observation_registered(observation_state *s,int anchor,const request_fields *r,int promote){
    struct stat st;if(!s||fstat(anchor,&st)||!atomic_load(&s->armed)||atomic_load(&s->quarantined))return 0;
    for(unsigned i=0;i<128;i++){unsigned phase=atomic_load_explicit(&s->entries[i].phase,memory_order_acquire);
        if((phase==1||phase==2)&&s->entries[i].inode==(uint64_t)st.st_ino&&!memcmp(&s->entries[i].request,r,sizeof(*r))){
            if(promote&&phase==1){
                uint64_t revision=atomic_fetch_add_explicit(&s->registry_revision,1,memory_order_acq_rel)+1;
                atomic_store_explicit(&s->entries[i].enrollment_revision,revision,memory_order_relaxed);
                atomic_store_explicit(&s->entries[i].enrolled_us,tick_us(),memory_order_relaxed);
                if(!atomic_compare_exchange_strong(&s->entries[i].phase,&phase,2))return 0;
            }
            return !atomic_load(&s->quarantined)&&atomic_load(&s->entries[i].phase)==(promote?2:phase);}}
    return 0;
}
static inline void observation_quarantine_anchor(observation_state *s,int anchor){
    struct stat st;if(!s||fstat(anchor,&st))return;
    for(unsigned i=0;i<128;i++)if(s->entries[i].inode==(uint64_t)st.st_ino){
        unsigned phase=atomic_load_explicit(&s->entries[i].phase,memory_order_acquire);
        while(phase&&phase!=3)if(atomic_compare_exchange_weak(&s->entries[i].phase,&phase,3)){atomic_fetch_add(&s->registry_revision,1);break;}
    }
}
static inline int observation_enrolled(observation_state *s,int anchor,const request_fields *r){
    struct stat st;if(!s||fstat(anchor,&st)||atomic_load(&s->quarantined))return 0;
    for(unsigned i=0;i<128;i++)if(atomic_load_explicit(&s->entries[i].phase,memory_order_acquire)==2&&s->entries[i].inode==(uint64_t)st.st_ino&&!memcmp(&s->entries[i].request,r,sizeof(*r)))return atomic_load(&s->entries[i].phase)==2&&!atomic_load(&s->quarantined);
    return 0;
}
static inline int observation_pending(const test_context *ctx,observation_state *s,int expected,int self,const request_fields *r,uint64_t until){
    if(!s||!alive(expected))return 0;
    int fd=socket(AF_UNIX,SOCK_SEQPACKET|SOCK_CLOEXEC|SOCK_NONBLOCK,0),peer=-1;unsigned char b[FRAME_MAX],reply=0;struct sockaddr_un a={.sun_family=AF_UNIX};strcpy(a.sun_path,OBS_SOCKET);
    socklen_t n=sizeof(peer);int ok=fd>=0&&!connect(fd,(struct sockaddr *)&a,sizeof(a))&&!getsockopt(fd,SOL_SOCKET,SO_PEERPIDFD,&peer,&n)&&anchor_equal(peer,expected)&&alive(peer);
    size_t size=encode_request(b,r);if(ok)ok=wait_fd(fd,POLLOUT,until)&&send_anchor(fd,b,size,self)&&wait_fd(fd,POLLIN,until)&&recv(fd,&reply,1,0)==1&&reply==0xc1;
    if(peer>=0)close(peer);if(fd>=0)close(fd);
    return ok&&context_matches(ctx,r)&&observation_registered(s,self,r,0)&&!atomic_load(&s->quarantined);
}
#endif
