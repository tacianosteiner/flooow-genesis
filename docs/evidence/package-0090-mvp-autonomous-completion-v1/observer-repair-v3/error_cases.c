#define _GNU_SOURCE
#define main original_fixture_main
#include "observer_fixture_tests.c"
#undef main
#include <assert.h>
#include <linux/audit.h>
#include <linux/filter.h>
#include <linux/seccomp.h>
#include <stddef.h>
#include <sys/prctl.h>
#include <sys/syscall.h>
#include <sys/wait.h>
static void deny_effect(unsigned number,int fd) {
    struct sock_filter code[]={
        BPF_STMT(BPF_LD|BPF_W|BPF_ABS,offsetof(struct seccomp_data,arch)),
        BPF_JUMP(BPF_JMP|BPF_JEQ|BPF_K,AUDIT_ARCH_X86_64,1,0),
        BPF_STMT(BPF_RET|BPF_K,SECCOMP_RET_KILL_PROCESS),
        BPF_STMT(BPF_LD|BPF_W|BPF_ABS,offsetof(struct seccomp_data,nr)),
        BPF_JUMP(BPF_JMP|BPF_JEQ|BPF_K,number,0,3),
        BPF_STMT(BPF_LD|BPF_W|BPF_ABS,offsetof(struct seccomp_data,args[0])),
        BPF_JUMP(BPF_JMP|BPF_JEQ|BPF_K,(unsigned)fd,0,1),
        BPF_STMT(BPF_RET|BPF_K,SECCOMP_RET_ERRNO|EIO),
        BPF_STMT(BPF_RET|BPF_K,SECCOMP_RET_ALLOW)
    };
    /* Clock's first argument is fixed CLOCK_BOOTTIME; others are fixed sink. */
    struct sock_fprog program={.len=sizeof(code)/sizeof(code[0]),.filter=code};
    assert(prctl(PR_SET_NO_NEW_PRIVS,1,0,0,0)==0);
    assert(prctl(PR_SET_SECCOMP,SECCOMP_MODE_FILTER,&program)==0);
}
int main(void) {
    const unsigned effects[]={SYS_clock_gettime,SYS_fcntl,SYS_fstat,SYS_write};
    for(unsigned role=1;role<=2;++role)for(unsigned test=0;test<4;++test){
        pid_t child=fork();assert(child>=0);
        if(!child){int pipes[2];assert(setup(role,pipes));
            deny_effect(effects[test],test==0?CLOCK_BOOTTIME:r.evidence_fd);
            S03Evidence result;int rc=call(role,&result);assert(rc==-2);
            if(test==0){assert(result.status==S03_UNKNOWN&&result.frame_size==0&&atomic_load(&terminal.state)==0);}
            else{assert(result.delivery_state==2&&atomic_load(&terminal.state)==2);}
            uint8_t byte;assert(read(pipes[0],&byte,1)==-1&&errno==EAGAIN);
            S03Evidence replay;assert(call(role,&replay)==-2);
            assert(read(pipes[0],&byte,1)==-1&&errno==EAGAIN);
            printf("{\"role\":%u,\"denied_syscall\":%u,\"pass\":true,\"public_rc\":%d,\"source_acceptance\":\"NOT_ESTABLISHED\"}\n",role,effects[test],rc);
            fflush(stdout);_exit(0);
        }
        int status;assert(waitpid(child,&status,0)==child&&WIFEXITED(status)&&WEXITSTATUS(status)==0);
    }
    return 0;
}
