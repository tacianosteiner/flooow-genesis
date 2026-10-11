/* Exact current observer; finite controlled catalog/registry schedules; owned children. */
#define main observer_program_main
#include "observer.c"
#undef main
#include <linux/sched.h>
#include <sys/wait.h>
#include <assert.h>
static pid_t child(int *fd){struct clone_args a={.flags=CLONE_PIDFD,.pidfd=(uint64_t)fd,.exit_signal=SIGCHLD};pid_t p=syscall(SYS_clone3,&a,sizeof(a));assert(p>=0);if(!p){for(;;)pause();}return p;}
static PGresult *catalog(pid_t pid,int n,int bad){
    PGresult *r=PQmakeEmptyPGresult(NULL,PGRES_TUPLES_OK);PGresAttDesc fields[8]={0};for(int j=0;j<8;j++){fields[j].name="fixture";fields[j].typid=25;fields[j].typlen=-1;}assert(PQsetResultAttrs(r,8,fields));
    char p[32];snprintf(p,sizeof(p),"%d",pid);const char *v[8]={p,bad==1?"101":"100","200",bad==2?"301":"300","400","test_fixture","client backend","t"};
    for(int i=0;i<n;i++)for(int j=0;j<8;j++)assert(PQsetvalue(r,i,j,(char *)v[j],strlen(v[j])));return r;
}
int main(void){
    const char *names[]={"appears_before_census","appears_during_census","disappears_during_census","dies_after_snapshot","restarts_new_pid","pid_tuple_reused","same_role_recreated","postmaster_generation_changes","receiver_generation_changes","supervisor_generation_changes","observer_generation_changes","promotion_during_census","quarantine_during_census","row_disappears_before_enforcement","row_appears_after_snapshot","duplicate_generation_observation","stale_snapshot_after_promotion"};
    for(unsigned k=0;k<17;k++){
        memset(&ctx,0,sizeof(ctx));shared=calloc(1,sizeof(*shared));assert(shared);count=1;frozen=enforced=unknown_overflow=unknown_n=0;
        int a=-1,b=-1;pid_t p=child(&a),p2=child(&b);sup=syscall(SYS_pidfd_open,getpid(),0);receiver=dup(sup);pm=dup(sup);
        request_fields id={.role=100,.db=200,.backend_start=300,.postmaster_start=400};strcpy(id.role_name,"test_fixture");struct stat st;assert(!fstat(a,&st));
        anchors[0]=(retained){.fd=a,.pid=p,.r=id};shared->entries[0].inode=st.st_ino;shared->entries[0].request=id;atomic_store(&shared->entries[0].phase,(k==11||k==16)?1:2);atomic_store(&shared->armed,1);
        capture_census_context();PGresult *r=catalog(p,(k==11||k==12||k==13||k==16)?0:(k==15?2:1),k==5?2:(k==6?1:0));int expected=1;
        if(k==1||k==14){atomic_fetch_add(&shared->registry_revision,1);expected=2;}
        if(k==2||k==3){syscall(SYS_pidfd_send_signal,a,SIGTERM,NULL,0);assert(wait_fd(a,POLLIN,tick_us()+1000000));expected=2;}
        if(k==4){anchors[0].fd=b;anchors[0].pid=p2;assert(!fstat(b,&st));shared->entries[0].inode=st.st_ino;atomic_fetch_add(&shared->registry_revision,1);expected=2;}
        if(k==7){close(pm);pm=dup(b);expected=0;}
        if(k==8){close(receiver);receiver=dup(b);expected=0;}
        if(k==9){close(sup);sup=dup(b);expected=0;}
        if(k==10){ctx.epoch[0]=1;expected=0;}
        if(k==11||k==16){assert(observation_registered(shared,a,&id,1));expected=2;}
        if(k==12)atomic_store(&shared->quarantined,1);
        if(k==5||k==6||k==15)expected=0;
        if(k==13)expected=2;
        int result=apply_census(r);assert(result==expected);
        if(k==5||k==6||k==7||k==8||k==9||k==10||k==12||k==15)assert(atomic_load(&shared->quarantined));
        if(k==11||k==16)assert(alive(a)&&atomic_load(&shared->entries[0].phase)==2&&!atomic_load(&shared->quarantined));
        if(k==13){assert(wait_fd(a,POLLIN,tick_us()+1000000));assert(!alive(a)&&atomic_load(&shared->entries[0].phase)==3);}
        printf("FINITE_OBSERVATION_SCHEDULE_%s=PASS\n",names[k]);
        syscall(SYS_pidfd_send_signal,a,SIGTERM,NULL,0);syscall(SYS_pidfd_send_signal,a,SIGCONT,NULL,0);syscall(SYS_pidfd_send_signal,b,SIGTERM,NULL,0);syscall(SYS_pidfd_send_signal,b,SIGCONT,NULL,0);waitpid(p,NULL,0);waitpid(p2,NULL,0);close(a);close(b);close(sup);close(receiver);close(pm);PQclear(r);free(shared);
    }
    assert(process_class("client backend",1)==1&&process_class("parallel worker",1)==3&&process_class("background worker",1)==3&&process_class("io worker",0)==2&&process_class("UNRECOGNIZED",0)==0);
    puts("UNKNOWN_PROCESS_CLASS_FAIL_CLOSED=PASS");return 0;
}
