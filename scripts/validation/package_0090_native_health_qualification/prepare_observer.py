"""Recorded one-time successor transformation; never run during compilation."""
from pathlib import Path
p=Path(__file__).parent
s=(p/'receiver.c').read_text()
s=s.replace('#include <libpq-fe.h>','#include <libpq-fe.h>\n#include "quarantine.h"\nstatic observation_state *observed;static int observer_anchor=-1;')
s=s.replace('if(argc!=4)return 64;','if(argc!=6)return 64;observed=observation_map(atoi(argv[4]),1);observer_anchor=atoi(argv[5]);if(!observed)return 70;')
s=s.replace('    for(;;){\n        if(access(TEST_DIR', '    for(;;){\n        atomic_store(&observed->receiver_progress,tick_us());\n        if(access(TEST_DIR',1)
start=s.index('        if(active_entries&&!independent_census');end=s.index('        for(unsigned i=0;i<used;i++)if(registry[i].fd>=0){',start)
s=s[:start]+s[end:]
s=s.replace('        int active_entries=0;for(unsigned i=0;i<used;i++)if(registry[i].fd>=0&&alive(registry[i].fd))active_entries++;\n','').replace('#include "census.h"','')
s=s.replace('int eligible=alive(supervisor)&&alive(postmaster)&&read_gate(&ctx,&health);','int eligible=alive(supervisor)&&alive(postmaster)&&alive(observer_anchor)&&!atomic_load(&observed->quarantined)&&tick_us()-atomic_load(&observed->observer_progress)<=10000000&&read_gate(&ctx,&health);')
s=s.replace('        if(!catalog(&r,mc.pid,begin+ctx.experimental_abort_us))','        if(!observation_registered(observed,supplied,&r,0)){reason=12;goto answer;}\n        if(!catalog(&r,mc.pid,begin+ctx.experimental_abort_us))')
start=s.index('        if(!independent_census(begin');end=s.index('        health_gate final_health;',start)
s=s[:start]+'        if(!observation_registered(observed,peer,&r,1)){reason=12;goto answer;}\n'+s[end:]
s=s.replace('!alive(supervisor)||!alive(postmaster)||!alive(peer)', '!alive(supervisor)||!alive(postmaster)||!alive(peer)||!alive(observer_anchor)||atomic_load(&observed->quarantined)||tick_us()-atomic_load(&observed->observer_progress)>10000000')
s=s.replace('reason=12;syscall(SYS_pidfd_send_signal,postmaster,SIGINT,NULL,0);goto answer;','reason=12;goto answer;')
(p/'receiver.c').write_text(s)
s=(p/'login.c').read_text().replace('#include "protocol.h"','#include "protocol.h"\n#include "quarantine.h"\nstatic observation_state *observed;static int expected_observer=-1;')
s=s.replace('    prepared=1;','    const char *obs=getenv("FLOOOW_TEST_OBSERVER_FD"),*state=getenv("FLOOOW_TEST_OBSERVATION_FD");\n    if(!obs||!state)die("independent observation absent");expected_observer=atoi(obs);int statefd=atoi(state);observed=observation_map(statefd,0);close(statefd);if(!observed||!alive(expected_observer))die("invalid independent observer");\n    prepared=1;')
marker='    health_gate gate;if(!read_gate(&ctx,&gate))die("independent eligibility absent");'
s=s.replace(marker,marker+'\n    self=syscall(SYS_pidfd_open,getpid(),0);if(self<0||!observation_pending(&ctx,observed,expected_observer,self,&r,deadline))die("pending census enrollment denied");')
s=s.replace('    self=syscall(SYS_pidfd_open,getpid(),0);if(self<0||!alive(self))die("self anchor failure");','    if(!alive(self))die("self anchor failure");')
s=s.replace('tick_us()>=deadline||!alive(self))die("invalid or denied ACK")','tick_us()>=deadline||!alive(self)||atomic_load(&observed->quarantined)||!alive(expected_observer)||tick_us()-atomic_load(&observed->observer_progress)>10000000)die("invalid or denied ACK")')
(p/'login.c').write_text(s)
s=(p/'build.py').read_text().replace("('receiver.c',","('observer.c','/usr/local/bin/flooow-test-observer',['-I/usr/include/postgresql/18/server','-I/usr/local/src-full','-l:libpq.so.5']),('receiver.c',")
(p/'build.py').write_text(s)
