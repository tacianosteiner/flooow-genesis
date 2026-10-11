"""Evolve successor only. Predecessor bytes are never written."""
from pathlib import Path
HERE=Path(__file__).parent
def replace(name, old, new):
    p=HERE/name;s=p.read_text();assert old in s,(name,old);p.write_text(s.replace(old,new),encoding='utf-8',newline='\n')
replace('supervisor.c','#include <sys/wait.h>','#include <sys/wait.h>\n#include "heartbeat.h"')
replace('supervisor.c','static pid_t spawn(char *const args[]){','static pid_t spawn(char *const args[],int close_fd){')
replace('supervisor.c','if(!p){execv','if(!p){if(close_fd>=0)close(close_fd);execv')
replace('supervisor.c','spawn(receiver_args)','spawn(receiver_args,channel[0])')
replace('supervisor.c','spawn(pg_args)','spawn(pg_args,channel[0])')
replace('supervisor.c','struct pollfd p[2]={{receiver_fd,POLLIN,0},{pgfd,POLLIN,0}};\n    while(poll(p,2,20)==0){', '''if(!progress_enable(channel[0]))return 70;
    uint64_t last_progress=tick_us();
    struct pollfd p[2]={{receiver_fd,POLLIN,0},{pgfd,POLLIN,0}};
    while(poll(p,2,20)==0){
        if(!progress_send(channel[0],0xb1))break;
        int progress;while((progress=progress_receive(channel[0],receiver_fd,0xb2))==1)last_progress=tick_us();
        if(progress<0||tick_us()-last_progress>10000000){printf("{\\"event\\":\\"receiver_progress_lost\\",\\"at_us\\":%llu}\\n",(unsigned long long)tick_us());break;}''')
replace('receiver.c','int main(int argc,char **argv){','#include "heartbeat.h"\nint main(int argc,char **argv){')
replace('receiver.c','if(!alive(postmaster))return 70;','if(!alive(postmaster)||!progress_enable(ctl))return 70;\n    uint64_t parent_progress=tick_us();')
replace('receiver.c','health_gate health;int eligible=alive(supervisor)&&alive(postmaster)&&read_gate(&ctx,&health);','''int progress;while((progress=progress_receive(ctl,supervisor,0xb1))==1)parent_progress=tick_us();
        if(progress<0||tick_us()-parent_progress>10000000){printf("{\\"event\\":\\"supervisor_progress_lost\\",\\"at_us\\":%llu}\\n",(unsigned long long)tick_us());syscall(SYS_pidfd_send_signal,postmaster,SIGINT,NULL,0);break;}
        if(!progress_send(ctl,0xb2)){syscall(SYS_pidfd_send_signal,postmaster,SIGINT,NULL,0);break;}
        health_gate health;int eligible=alive(supervisor)&&alive(postmaster)&&read_gate(&ctx,&health);''')
replace('receiver.c','if(ps[1].revents||ps[2].revents)','if(ps[1].revents||(ps[2].revents&(POLLHUP|POLLERR|POLLNVAL)))')
# Builder must compile exact committed sources, not regenerate/overwrite them.
replace('build.py','prepare();started=False','started=False')
