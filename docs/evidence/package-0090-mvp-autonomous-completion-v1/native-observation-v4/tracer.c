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
#include <string.h>
struct syscall_info {uint8_t op,pad[3];uint32_t arch;uint64_t instruction_pointer,stack_pointer;union {struct {uint64_t nr,args[6];} entry;struct {int64_t rval;uint8_t is_error;} exit;} u;};
struct thread {pid_t tid;int live,in;long nr;};static struct thread threads[16];
static struct thread *get(pid_t tid){for(int i=0;i<16;i++)if(threads[i].live&&threads[i].tid==tid)return &threads[i];for(int i=0;i<16;i++)if(!threads[i].live){threads[i]=(struct thread){tid,1,0,0};return &threads[i];}exit(90);}
static void resume(pid_t tid,int sig){if(ptrace(PTRACE_SYSCALL,tid,0,(void*)(long)sig)<0&&errno!=ESRCH){perror("resume");exit(91);}}

static void path_at(pid_t tid,unsigned long address){printf("OPEN_PATH\tTID=%d\tPATH=",tid);for(unsigned i=0;i<256;i+=sizeof(long)){errno=0;long word=ptrace(PTRACE_PEEKDATA,tid,(void*)(address+i),0);if(word==-1&&errno){printf("NOT_ESTABLISHED");break;}for(unsigned j=0;j<sizeof(long);j++){unsigned char c=((unsigned char*)&word)[j];if(!c){putchar('\n');return;}putchar(c>=32&&c<127?c:'?');}}putchar('\n');}
static void dump_vdso(pid_t tid,unsigned long start,unsigned long end){
 if(!start||end<=start||end-start>65536||(end-start)%sizeof(long)){puts("VDSO_DUMP_NOT_ESTABLISHED");exit(87);}
 printf("VDSO_HEX\tSTART=0x%lx\tEND=0x%lx\tBYTES=",start,end);
 for(unsigned long address=start;address<end;address+=sizeof(long)){errno=0;long word=ptrace(PTRACE_PEEKDATA,tid,(void*)address,0);if(word==-1&&errno)exit(86);for(unsigned i=0;i<sizeof(word);++i)printf("%02x",((unsigned char*)&word)[i]);}putchar('\n');
}
static void bindings_at(pid_t tid){char path[64],line[1024];snprintf(path,sizeof path,"/proc/%d/maps",tid);FILE *maps=fopen(path,"r");if(!maps)return;unsigned long libc=0,crypto=0,vdso0=0,vdso1=0;while(fgets(line,sizeof line,maps)){printf("MAP\t%s",line);unsigned long begin,end,offset;char mode[8];if(sscanf(line,"%lx-%lx %7s %lx",&begin,&end,mode,&offset)!=4)continue;if(offset==0&&strstr(line,"libc.so.6"))libc=begin;if(offset==0&&strstr(line,"libcrypto.so.3"))crypto=begin;if(strstr(line,"[vdso]")){vdso0=begin;vdso1=end;}}fclose(maps);errno=0;unsigned long global=libc?(unsigned long)ptrace(PTRACE_PEEKDATA,tid,(void*)(libc+0x1e4ec0),0):0;unsigned long clock=global?(unsigned long)ptrace(PTRACE_PEEKDATA,tid,(void*)(global+0x300),0):0;unsigned long copy=crypto?(unsigned long)ptrace(PTRACE_PEEKDATA,tid,(void*)(crypto+0x6335f0),0):0;unsigned long cleanse=crypto?(unsigned long)ptrace(PTRACE_PEEKDATA,tid,(void*)(crypto+0x62ea50),0):0;printf("BOUND_POINTERS\tLIBC=0x%lx\tCRYPTO=0x%lx\tRTLD_GLOBAL=0x%lx\tCLOCK=0x%lx\tMEMCPY=0x%lx\tCLEANSE=0x%lx\tVDSO_START=0x%lx\tVDSO_END=0x%lx\tERRNO=%d\n",libc,crypto,global,clock,copy,cleanse,vdso0,vdso1,errno);dump_vdso(tid,vdso0,vdso1);}

int main(void){static int captured=0;
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
   if(info.op==1){t->nr=(long)info.u.entry.nr;if(t->nr==257)path_at(tid,(unsigned long)info.u.entry.args[1]);if(t->nr==2)path_at(tid,(unsigned long)info.u.entry.args[0]);if(t->nr==293&&!captured){captured=1;bindings_at(tid);}if(1)printf("SYSCALL_ENTER\tTID=%d\tNR=%ld\tRIP=0x%llx\tARG0=0x%llx\tARG1=0x%llx\tARG2=0x%llx\tARG3=0x%llx\tKERNEL_STOP=ENTRY\n",tid,t->nr,(unsigned long long)info.instruction_pointer,(unsigned long long)info.u.entry.args[0],(unsigned long long)info.u.entry.args[1],(unsigned long long)info.u.entry.args[2],(unsigned long long)info.u.entry.args[3]);t->in=1;}
   else if(info.op==2){if(t->in&&(1))printf("SYSCALL_EXIT\tTID=%d\tNR=%ld\tRETURN=%lld\tKERNEL_STOP=EXIT\n",tid,t->nr,(long long)info.u.exit.rval);t->in=0;}
   resume(tid,0);continue;
  }
  if(sig==SIGSTOP){resume(tid,0);continue;}
  printf("SIGNAL_DELIVERED\tTID=%d\tSIGNAL=%d\n",tid,sig);resume(tid,sig);
 }
 FILE *capture=fopen("/tmp/observer-fixture.stdout","rb");if(!capture)return 88;printf("HARNESS_CAPTURE_BEGIN\n");char bytes[4096];size_t count;while((count=fread(bytes,1,sizeof bytes,capture)))fwrite(bytes,1,count,stdout);fclose(capture);printf("HARNESS_CAPTURE_END\n");
 printf("TRACE_DONE\tMAIN_STATUS=%d\tSTOPS=%u\n",main_result,stops);return main_result;
}
