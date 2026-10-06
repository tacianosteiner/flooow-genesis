"""Phase-A only: real pidfd signal-0 capability/lifetime probes, no signal primitive.

No SIGINT/SIGTERM, extension, SQL helper, grant, role change or policy change.
The five prior uncommitted artifacts are immutable inputs.
"""
import hashlib,json,secrets,subprocess,time
from pathlib import Path
import package_0090_timing_qualification2 as env
import package_0090_timing_forensics as forensic

ROOT=env.ROOT
BASELINE='401a5e313efbec9a4100af8b6b6e237fffb4ca38'
PROBE=r'''
#define _GNU_SOURCE
#include <errno.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <signal.h>
#include <sys/prctl.h>
#include <sys/syscall.h>
#include <sys/ioctl.h>
#include <sys/utsname.h>
#include <poll.h>
#include <unistd.h>
struct probe_pidfd_info {uint64_t mask,cgroupid;uint32_t pid,tgid,ppid,ruid,rgid,euid,egid,suid,sgid,fsuid,fsgid;int32_t exit_code;};
int main(int argc,char **argv){
 if(argc!=2)return 64;char *end;long pid=strtol(argv[1],&end,10);if(*end||pid<=1||pid>2147483647)return 64;
 struct utsname u;uname(&u);errno=0;int fd=syscall(SYS_pidfd_open,(int)pid,0);int oe=errno;
 errno=0;int s=fd<0?-1:syscall(SYS_pidfd_send_signal,fd,0,NULL,0);int se=errno;
 struct probe_pidfd_info info={.mask=1};errno=0;int iq=fd<0?-1:ioctl(fd,_IOWR(0xff,11,struct probe_pidfd_info),&info);int ie=errno;
 printf("{\"kernel\":\"%s\",\"uid\":%u,\"seccomp_mode\":%d,\"pid\":%ld,\"pidfd_open_result\":%d,\"pidfd_open_errno\":%d,\"signal_zero_result\":%d,\"signal_zero_errno\":%d,\"pidfd_get_info_result\":%d,\"pidfd_get_info_errno\":%d,\"pidfd_info_mask\":%llu,\"pidfd_info_ppid\":%u}\n",u.release,getuid(),prctl(PR_GET_SECCOMP),pid,fd,oe,s,se,iq,ie,(unsigned long long)info.mask,info.ppid);fflush(stdout);
 if(fd>=0){struct pollfd p={.fd=fd,.events=POLLIN};int rc=poll(&p,1,6000);errno=0;int after=syscall(SYS_pidfd_send_signal,fd,0,NULL,0);int ae=errno;printf("{\"poll_result\":%d,\"poll_revents\":%d,\"after_exit_signal_zero_result\":%d,\"after_exit_errno\":%d}\n",rc,p.revents,after,ae);close(fd);}
 return 0;
}
'''

def run(args,timeout=30):
 p=subprocess.run(args,capture_output=True,timeout=timeout)
 if p.returncode:raise RuntimeError('Tool failed: '+args[0])
 return p.stdout

def main():
 run(['git','fetch','origin'])
 if any(run(['git','rev-parse',r]).decode().strip()!=BASELINE for r in ['HEAD','origin/checkpoint/package-0090-cloud-handoff']):raise RuntimeError('Baseline mismatch')
 c,private,old=env.identity();work=private/'identity-signal-contract'
 inv=json.loads((work/'prior-inventory.json').read_text())
 if any(hashlib.sha256((ROOT/x['path']).read_bytes()).hexdigest()!=x['sha256'] for x in inv):raise RuntimeError('Prior uncommitted file changed')
 if c['State']['Running'] or (work/'platform-record.json').exists():raise RuntimeError('Refuse running/overwritten probe')
 tracked=run(['git','ls-files','-z']).decode().split('\0');hashes={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in tracked if p and (ROOT/p).is_file()}
 rec={'baseline':BASELINE,'prior_inventory':inv,'unrelated_count':0,'tracked_hashes_before':hashes,'destructive_signal_count':0,'signal_numbers_used':[0],'phase':'A_ONLY','tests':[]}
 def save():(work/'platform-record.json').write_text(json.dumps(rec,indent=2)+'\n',encoding='utf-8',newline='\n')
 def sql(statement):
  env.identity();p=subprocess.run(['docker','exec','-i',env.CONTAINER,'psql','-X','-U','postgres','-d','g3f4','-At','-v','ON_ERROR_STOP=1'],input=statement,text=True,capture_output=True,timeout=20)
  if p.returncode:raise RuntimeError('Read-only administrative SQL failed')
  return p.stdout.strip()
 roles=['postgres']+['g3f4_'+s+'_cc2941797db3' for s in ['auditor','verifier','issuer','executor']];query=forensic.authority_snapshot_sql(roles)
 marker_query="SELECT json_agg(row_to_json(r) ORDER BY incarnation_id) FROM (SELECT deployment_id,incarnation_id,state,policy_version,encode(policy_digest,'hex') AS policy_digest,watchdog_checked_at,watchdog_healthy FROM public.offline_readiness) r;"
 password=private/'postgres-password'
 if password.exists():raise RuntimeError('Unexpected startup file')
 password.write_text(secrets.token_hex(32),encoding='ascii');started=False;actors=[]
 try:
  env.identity();run(['docker','start',env.CONTAINER]);started=True
  deadline=time.monotonic()+40
  while time.monotonic()<deadline:
   if subprocess.run(['docker','exec',env.CONTAINER,'pg_isready','-U','postgres','-d','g3f4'],capture_output=True).returncode==0:break
   time.sleep(.1)
  else:raise RuntimeError('Startup timeout')
  rec['server']=json.loads(sql("SELECT json_build_object('version',version(),'version_num',current_setting('server_version_num'),'postmaster_start',pg_postmaster_start_time(),'database',current_database(),'clock',clock_timestamp());"))
  if rec['server']['version_num']!='180004':raise RuntimeError('PG18.4 required')
  rec['authority_pre']=json.loads(sql(query));rec['fingerprint_pre']=forensic.fingerprint(rec['authority_pre']);rec['marker_pre']=json.loads(sql(marker_query))
  rec['container_security']={k:c['HostConfig'][k] for k in ['Privileged','CapAdd','CapDrop','SecurityOpt','PidMode']}
  rec['compiler']=run(['docker','exec',env.CONTAINER,'gcc','--version']).decode().splitlines()[0]
  (work/'pidfd-platform-probe.c').write_text(PROBE,encoding='ascii')
  # Existing readonly /review bind; compile only to private /tmp in disposable.
  run(['docker','exec',env.CONTAINER,'gcc','-std=c11','-Wall','-Wextra','-O2','-o','/tmp/0090-pidfd-platform-probe','/review/identity-signal-contract/pidfd-platform-probe.c'])
  rec['binary_sha256']=run(['docker','exec',env.CONTAINER,'sha256sum','/tmp/0090-pidfd-platform-probe']).decode().split()[0]
  for index in range(3):
   label='0090-pidfd-phase-a-'+str(index)
   actor=subprocess.Popen(['docker','exec','-e','PGAPPNAME='+label,env.CONTAINER,'psql','-X','-U','g3f4_executor_cc2941797db3','-d','g3f4','-At','-v','ON_ERROR_STOP=1','-c','SELECT pg_sleep(3);'],stdout=subprocess.DEVNULL,stderr=subprocess.PIPE);actors.append(actor)
   deadline=time.monotonic()+5;target=None
   while time.monotonic()<deadline:
    raw=sql("SELECT row_to_json(x) FROM (SELECT pid,backend_start,datid,usesysid,backend_type,state,clock_timestamp() AS observed_db_clock FROM pg_stat_activity WHERE application_name='"+label+"' AND state='active') x;")
    if raw:target=json.loads(raw);break
    if actor.poll() is not None:raise RuntimeError('Subject did not authenticate')
    time.sleep(.01)
   if target is None:raise RuntimeError('Controlled subject not observed')
   result=run(['docker','exec','--user','postgres',env.CONTAINER,'/tmp/0090-pidfd-platform-probe',str(target['pid'])],10)
   actor.wait(timeout=10)
   if actor.returncode:raise RuntimeError('Controlled read-only subject failed')
   rows=[json.loads(l) for l in result.decode().splitlines()];rec['tests'].append({'target':target,'probe':rows,'destructive_signals':0});save()
  rec['authority_post']=json.loads(sql(query));rec['fingerprint_post']=forensic.fingerprint(rec['authority_post']);rec['marker_post']=json.loads(sql(marker_query));rec['authority_equal']=rec['authority_pre']==rec['authority_post'];rec['marker_unchanged']=rec['marker_pre']==rec['marker_post']
 finally:
  try:
   for actor in actors:
    if actor.poll() is None:actor.wait(timeout=10)
   if started:run(['docker','stop',env.CONTAINER],40)
  finally:
   if password.exists():password.unlink()
   rec['container_stopped']=not env.identity()[0]['State']['Running'];rec['plaintext_credential_files_erased']=not password.exists()
   rec['prior_files_unchanged']=all(hashlib.sha256((ROOT/x['path']).read_bytes()).hexdigest()==x['sha256'] for x in inv)
   rec['tracked_hashes_after']={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in hashes};rec['tracked_unchanged']=rec['tracked_hashes_before']==rec['tracked_hashes_after'];save()
 if not all(rec.get(k) for k in ['authority_equal','marker_unchanged','container_stopped','plaintext_credential_files_erased','prior_files_unchanged','tracked_unchanged']):raise RuntimeError('Integrity incomplete')
 print(json.dumps({'server':rec['server'],'tests':rec['tests'],'fingerprint_pre':rec['fingerprint_pre'],'fingerprint_post':rec['fingerprint_post']},indent=2))

if __name__=='__main__':main()
