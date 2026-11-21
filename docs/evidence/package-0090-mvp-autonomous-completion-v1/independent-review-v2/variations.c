#define _GNU_SOURCE
#include "observer.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <sys/socket.h>
#include <sys/stat.h>
#include <fcntl.h>
static unsigned id=1;
static S03Ref ref(void){S03Ref r={.kind=1,.size=4}; unsigned v=id++;memcpy(r.bytes,&v,4);return r;}
static S03Observer obs(unsigned role){S03Observer o={.role=role};o.principal=ref();o.birth=ref();o.session=ref();o.channel=ref();o.context=ref();return o;}
static unsigned long long now(void){struct timespec t;clock_gettime(CLOCK_BOOTTIME,&t);return (unsigned long long)t.tv_sec*1000000+t.tv_nsec/1000;}
int main(void){for(int k=0;k<13;k++){
S03ProtectedContext *r=calloc(1,sizeof(*r)); S03Observation *i=calloc(1,sizeof(*i));S03Terminal *t=calloc(1,sizeof(*t));unsigned char *frame=calloc(1,S03_FRAME_LIMIT);S03Evidence e;
r->version=1;r->max_rows=64;r->max_bytes=S03_FRAME_LIMIT;r->max_age_us=100000000;r->not_before_us=now()-1000000;r->expires_us=now()+100000000;r->observer=obs(1);r->other_observer=obs(2);
S03Target *a=&r->target;a->context=ref();a->server_generation=ref();a->birth=ref();a->session=ref();a->registry_revision=ref();a->participant=ref();a->principal=ref();a->generation=1;a->database_oid=1;a->role_oid=2;a->pid=123;a->server_start_pg_us=1234;a->backend_start_pg_us=2345;a->role_name.size=6;memcpy(a->role_name.bytes,"reader",6);
for(int s=0;s<8;s++){r->source[s].source_id=ref();r->source[s].source_authority=ref();r->source[s].source_provenance=ref();r->source[s].source_acceptance=ref();memset(r->source[s].integrity,1,32);i->source[s]=r->source[s];i->source_state[s]=1;}
r->origin_channel_binding=ref();r->creator_principal=ref();r->verifier_principal=ref();r->population_scope=ref();S03Window *w=&r->window;w->boot=ref();w->time_namespace=ref();w->barrier=ref();w->acquisition=ref();w->snapshot=ref();w->custody=ref();w->authentication=ref();w->policy=ref();w->challenge=ref();w->started_us=now()-1000;w->finished_us=now()-100;w->barrier_valid_until_us=now()+100000000;r->expected_count=1;r->expected[0]=*a;r->terminal=t;
int fd[2];socketpair(AF_UNIX,SOCK_DGRAM|SOCK_NONBLOCK,0,fd);struct stat st;fstat(fd[0],&st);r->evidence_fd=fd[0];r->evidence_device=st.st_dev;r->evidence_inode=st.st_ino;
i->observer=r->observer;i->target=*a;i->window=*w;i->population_scope=r->population_scope;i->consumer_kind=1;i->requested_output_kind=1;i->coverage=1;i->count=1;i->members[0].bridge=*a;i->members[0].native_birth=a->birth;i->members[0].bridge_presence=1;i->members[0].liveness_before=1;i->members[0].liveness_after=1;i->members[0].public_row.database_oid=a->database_oid;i->members[0].public_row.role_oid=a->role_oid;i->members[0].public_row.pid=a->pid;i->members[0].public_row.role_name=a->role_name;i->members[0].public_row.source_row=ref();i->members[0].backend_type.size=14;memcpy(i->members[0].backend_type.bytes,"client backend",14);
if(k==1){i->window.started_us=r->not_before_us-1000000;i->window.finished_us=r->not_before_us-500000;}
if(k==2){i->source_state[1]=S03_SOURCE_MISSING;i->target.principal=ref();i->window.finished_us=i->window.started_us-1;}
if(k==3){i->observer.principal=ref();i->source[1].integrity[0]=2;}
if(k==4){i->members[0].native_birth=ref();i->members[0].public_row.pid++;}
if(k==5){i->window.started_us=now()+1000000;i->window.finished_us=now()+2000000;}
if(k==6){i->window.finished_us=i->window.started_us-1;}
if(k==7){i->window.started_us=now()-r->max_age_us-1000000;}
if(k==8){r->window.started_us=r->not_before_us-10000000;r->window.finished_us=r->not_before_us-9000000;}
if(k==9){i->source_state[3]=S03_SOURCE_MISSING;i->target.principal=ref();i->window.finished_us=i->window.started_us-1;}
if(k==10){i->source_state[1]=S03_SOURCE_MISSING;i->members[0].native_birth=ref();}
if(k==11){i->source[1].integrity[0]=2;i->target.principal=ref();i->window.finished_us=i->window.started_us-1;}
if(k==12){i->window.started_us=r->not_before_us;i->window.finished_us=r->not_before_us;}
int rc=s03_health_guard_observe(r,i,&e,frame,S03_FRAME_LIMIT);if(k==0){S03Evidence first=e;unsigned char saved[32];memcpy(saved,e.content_digest,32);int repeat=s03_health_guard_observe(r,i,&e,frame,S03_FRAME_LIMIT);printf("{\"replay\":%d,\"immutable\":%d}\n",repeat,memcmp(saved,e.content_digest,32)==0 && first.observed_started_us==e.observed_started_us);i->coverage=2;int conflict=s03_health_guard_observe(r,i,&e,frame,S03_FRAME_LIMIT);printf("{\"conflict\":%d}\n",conflict);e=first;}printf("{\"case\":%d,\"rc\":%d,\"status\":%u,\"diagnostics\":%llu,\"size\":%u}\n",k,rc,e.status,(unsigned long long)e.diagnostics,e.frame_size);
}return 0;}



