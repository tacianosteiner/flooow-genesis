#define _GNU_SOURCE
#include <sys/ptrace.h>
#include <sys/user.h>
#include <sys/wait.h>
#include <sys/types.h>
#include <signal.h>
#include <unistd.h>
#include <stdio.h>
#include <stdlib.h>
#include <errno.h>
#include <stdint.h>
#include <fcntl.h>
struct syscall_info {uint8_t op,pad[3];uint32_t arch;uint64_t instruction_pointer,stack_pointer;union {struct {uint64_t nr,args[6];} entry;struct {int64_t rval;uint8_t is_error;} exit;} u;};
struct thread {pid_t tid;int live,in;long nr;};static struct thread threads[16];
static struct thread *get(pid_t tid){for(int i=0;i<16;i++)if(threads[i].live&&threads[i].tid==tid)return &threads[i];for(int i=0;i<16;i++)if(!threads[i].live){threads[i]=(struct thread){tid,1,0,0};return &threads[i];}exit(90);}
static void resume(pid_t tid,int sig){if(ptrace(PTRACE_SYSCALL,tid,0,(void*)(long)sig)<0&&errno!=ESRCH){perror("resume");exit(91);}}
int main(void){
 setvbuf(stdout,0,_IONBF,0);pid_t child=fork();if(child<0)return 92;
 if(!child){int capture=open("/tmp/observer-fixture.stdout",O_WRONLY|O_CREAT|O_TRUNC,0600);if(capture<0||dup2(capture,STDOUT_FILENO)<0)_exit(89);close(capture);if(ptrace(PTRACE_TRACEME,0,0,0)<0)_exit(93);char *args[]={"/out/observer-fixture-tests",0};char *env[]={"PATH=/usr/bin:/bin","LC_ALL=C","LD_BIND_NOW=1","LD_DEBUG=libs,bindings",0};execve(args[0],args,env);_exit(94);}
 int status,main_result=-1;unsigned stops=0;waitpid(child,&status,0);get(child);
 long opts=PTRACE_O_TRACESYSGOOD|PTRACE_O_TRACECLONE|PTRACE_O_TRACEEXIT|PTRACE_O_EXITKILL;
 if(ptrace(PTRACE_SETOPTIONS,child,0,(void*)opts)<0)return 95;resume(child,0);
 for(;;){pid_t tid=waitpid(-1,&status,__WALL);if(tid<0){if(errno==ECHILD)break;perror("wait");return 96;}struct thread *t=get(tid);
  if(WIFEXITED(status)||WIFSIGNALED(status)){int result=WIFEXITED(status)?WEXITSTATUS(status):128+WTERMSIG(status);printf("THREAD_EXIT\tTID=%d\tSTATUS=%d\n",tid,result);if(tid==child)main_result=result;t->live=0;continue;}
  if(!WIFSTOPPED(status))return 97;if(++stops>50000){kill(child,SIGKILL);return 98;}
  int sig=WSTOPSIG(status);unsigned event=(unsigned)status>>16;
  if(sig==SIGTRAP&&event==PTRACE_EVENT_CLONE){unsigned long newtid=0;ptrace(PTRACE_GETEVENTMSG,tid,0,&newtid);get((pid_t)newtid)->in=1;printf("CLONE\tPARENT=%d\tTID=%lu\n",tid,newtid);resume(tid,0);continue;}
  if(sig==SIGTRAP&&event==PTRACE_EVENT_EXIT){resume(tid,0);continue;}
  if(sig==(SIGTRAP|0x80)){struct syscall_info info={0};long got=ptrace(PTRACE_GET_SYSCALL_INFO,tid,(void*)sizeof(info),&info);if(got<0){perror("syscall-info");return 99;}
   if(info.op==1){t->nr=(long)info.u.entry.nr;if(1)printf("SYSCALL_ENTER\tTID=%d\tNR=%ld\tRIP=0x%llx\tARG0=0x%llx\tARG1=0x%llx\tARG2=0x%llx\tARG3=0x%llx\tKERNEL_STOP=ENTRY\n",tid,t->nr,(unsigned long long)info.instruction_pointer,(unsigned long long)info.u.entry.args[0],(unsigned long long)info.u.entry.args[1],(unsigned long long)info.u.entry.args[2],(unsigned long long)info.u.entry.args[3]);t->in=1;}
   else if(info.op==2){if(t->in&&(1))printf("SYSCALL_EXIT\tTID=%d\tNR=%ld\tRETURN=%lld\tKERNEL_STOP=EXIT\n",tid,t->nr,(long long)info.u.exit.rval);t->in=0;}
   resume(tid,0);continue;
  }
  if(sig==SIGSTOP){resume(tid,0);continue;}
  printf("SIGNAL_DELIVERED\tTID=%d\tSIGNAL=%d\n",tid,sig);resume(tid,sig);
 }
 FILE *capture=fopen("/tmp/observer-fixture.stdout","rb");if(!capture)return 88;printf("HARNESS_CAPTURE_BEGIN\n");char bytes[4096];size_t count;while((count=fread(bytes,1,sizeof bytes,capture)))fwrite(bytes,1,count,stdout);fclose(capture);printf("HARNESS_CAPTURE_END\n");
 printf("TRACE_DONE\tMAIN_STATUS=%d\tSTOPS=%u\n",main_result,stops);return main_result;
}
