#define _GNU_SOURCE
#define main original_fixture_main
#include "observer_fixture_tests.c"
#undef main
#include <assert.h>
#include <pthread.h>
/* Deliberately exercises queued deferred cancellation BEFORE the fixed call or
 * AFTER its write/terminal publication. It does not test interruption during
 * the syscall, asynchronous cancellation, real owner custody or qualification. */
static atomic_uint ready_flag,go_flag,completed;
static unsigned selected_role,selected_mode;
static S03Evidence produced;
static void *worker(void *unused) {
    (void)unused;int old;
    assert(pthread_setcanceltype(PTHREAD_CANCEL_DEFERRED,&old)==0);
    if(selected_mode==0){atomic_store(&ready_flag,1);while(!atomic_load(&go_flag)){};}
    assert(call(selected_role,&produced)==0);
    atomic_store(&completed,1);
    if(selected_mode==1){atomic_store(&ready_flag,1);while(!atomic_load(&go_flag)){};}
    pthread_testcancel();
    return NULL;
}
int main(void) {
    for(unsigned role=1;role<=2;++role)for(unsigned mode=0;mode<2;++mode){
        int pipes[2];assert(setup(role,pipes));
        selected_role=role;selected_mode=mode;
        atomic_store(&ready_flag,0);atomic_store(&go_flag,0);atomic_store(&completed,0);
        pthread_t thread;assert(pthread_create(&thread,NULL,worker,NULL)==0);
        while(!atomic_load(&ready_flag)){};
        assert(pthread_cancel(thread)==0);atomic_store(&go_flag,1);
        void *result;assert(pthread_join(thread,&result)==0&&result==PTHREAD_CANCELED);
        assert(atomic_load(&completed)==1&&atomic_load(&terminal.state)==2);
        assert(produced.evidence_only==1&&produced.delivery_state==1&&produced.status==S03_OBSERVED_MATCH);
        uint8_t delivered[S03_FRAME_LIMIT];ssize_t count=read(pipes[0],delivered,sizeof(delivered));
        assert(count==(ssize_t)produced.frame_size&&!memcmp(delivered,terminal.frame,(size_t)count));
        S03Evidence replay;assert(call(role,&replay)==0);
        assert(replay.observed_finished_us==produced.observed_finished_us&&replay.frame_size==produced.frame_size&&!memcmp(frame,delivered,replay.frame_size));
        uint8_t byte;assert(read(pipes[0],&byte,1)==-1&&errno==EAGAIN);
        printf("{\"role\":%u,\"deferred_cancel_phase\":\"%s\",\"pass\":true,\"terminal_state\":2,\"replay_reemitted\":false,\"source_acceptance\":\"NOT_ESTABLISHED\"}\n",role,mode==0?"QUEUED_BEFORE_CALL":"QUEUED_AFTER_PUBLICATION");
        close(pipes[0]);close(pipes[1]);
    }
    return 0;
}
