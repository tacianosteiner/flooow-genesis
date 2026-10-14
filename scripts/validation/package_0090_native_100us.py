"""Bounded TEST freshness measurement. No timing change or READY publication."""
import json
from pathlib import Path
import package_0090_source_closure as q
import package_0090_authorized_s04 as a

OUT = q.ROOT / 'docs/evidence/package-0090-native-health-100us-feasibility'
BASELINE = '701b595511dc70f50a38f128b1c6aa411d3259a1'


def instrument(source):
    def replace(old, new):
        nonlocal source
        q.require(source.count(old) == 1, 'Unique instrumentation boundary: ' + old[:60])
        source = source.replace(old, new)
    extra = r'''
static uint64_t runq(void){char s[256];file("/proc/self/schedstat",s,sizeof s);unsigned long long cpu,queue,count;if(sscanf(s,"%llu %llu %llu",&cpu,&queue,&count)!=3)exit(110);return queue;}
'''
    replace('typedef struct {int index;', extra + '\ntypedef struct {int index;uint64_t t[11],credential_start,credential_end,pidfd_start,pidfd_end;')
    replace('o.request_time=now();', 'uint64_t sched_before=runq();o.request_time=now();o.t[0]=o.request_time;')
    replace('o.work_kind=index+1;', 'o.work_kind=index+1;o.t[1]=now();')
    replace('o.emitted=now();sendobs(fd,&o);', 'o.t[2]=now();o.emitted=now();o.t[3]=o.emitted;sendobs(fd,&o);')
    replace('if(sendmsg(fd,&m,0)!=sizeof *o)', 'o->t[4]=now();if(sendmsg(fd,&m,0)!=sizeof *o)')
    replace('exit(98);int anchor=-1,cred=0;', 'exit(98);o->t[5]=now();o->credential_start=now();int anchor=-1,cred=0;')
    replace('if(anchor<0)exit(99);struct pollfd', 'o->credential_end=now();o->pidfd_start=now();if(anchor<0)exit(99);struct pollfd')
    replace('close(anchor);return cred&&live', 'close(anchor);o->pidfd_end=now();o->t[6]=now();return cred&&live')
    replace('probe(independently_observed);uint64_t observed=now();', 'uint64_t catalog_start=now();probe(independently_observed);uint64_t catalog_finish=now();uint64_t observed=now();')
    replace('int identity=authenticated[i]', 'o->t[7]=now();o->t[8]=catalog_finish;int identity=authenticated[i]')
    replace('printf("],\\"identity_and_work_complete', 'uint64_t decision_complete=now();for(int i=0;i<7;i++)obs[i].t[9]=decision_complete;printf("],\\"identity_and_work_complete')
    replace('fflush(stdout);\n for(int i=0;i<7;i++)', r'''fflush(stdout);
 printf("{\"kind\":\"timeline\",\"catalog_start_ns\":%llu,\"catalog_finish_ns\":%llu,\"qualified_decision_ns\":%llu,\"participants\":[",(unsigned long long)catalog_start,(unsigned long long)catalog_finish,(unsigned long long)decision_complete);
 for(int i=0;i<7;i++){observation*o=&obs[i];printf("%s{\"index\":%d,\"t\":[",i?",":"",i);for(int j=0;j<10;j++)printf("%s%llu",j?",":"",(unsigned long long)o->t[j]);printf(",null],\"credential_ns\":%llu,\"pidfd_ns\":%llu}",(unsigned long long)(o->credential_end-o->credential_start),(unsigned long long)(o->pidfd_end-o->pidfd_start));}printf("]}\n");fflush(stdout);
 for(int i=0;i<7;i++)''')
    replace('if(read(fd,&ack,1)!=1)exit(97);', 'if(read(fd,&ack,1)!=1)exit(97);uint64_t sched_after=runq();dprintf(1,"{\\"kind\\":\\"scheduler\\",\\"index\\":%d,\\"runqueue_wait_ns\\":%llu,\\"interval_end_ns\\":%llu}\\n",index,(unsigned long long)(sched_after-sched_before),(unsigned long long)now());')
    replace('int ledger=open("/run/test-only-0090-health/generation-ledger.jsonl",', 'char ledger_path[256];snprintf(ledger_path,sizeof ledger_path,"/run/test-only-0090-health/generation-%d.jsonl",getpid());int ledger=open(ledger_path,')
    return source.replace('/run/test-only-0090-health', '/run/test-only-0090-cold')


def qualify(sql, run, container, folder, record, fixture, runtime_work):
    # Reproduce approved activation/audit and original mechanism gate independently.
    a.qualify(sql, run, container, folder, record, fixture, runtime_work)
    if folder.name.startswith('warm'):
        q.require((OUT/'cold-decomposition.json').exists(), 'No optimization before measured decomposition')
        warm(sql, run, container, folder, record)
        return
    source_path = q.ROOT / 'scripts/validation/package_0090_s04_native_health.c'
    original = q.git('show', BASELINE + ':' + source_path.relative_to(q.ROOT).as_posix()).decode()
    measured = instrument(original)
    (folder / 'instrumented-cold.c').write_text(measured, encoding='utf-8', newline='\n')
    private = '/run/test-only-0090-cold'
    run(['docker','exec',container,'mkdir','-m','0700',private])
    run(['docker','cp',str(folder/'native-context.json'),container+':'+private+'/context.json'])
    run(['docker','cp',str(folder/'instrumented-cold.c'),container+':'+private+'/cold.c'])
    result=q.command(['docker','exec',container,'cc','-O2','-Wall','-Wextra',private+'/cold.c','-o',private+'/cold','-lcrypto'],check=False)
    a.save(folder,'cold-build.json',{'exit':result.returncode,'stderr':result.stderr.decode(),'source_sha256':q.sha(measured.encode())})
    q.require(result.returncode==0,'Instrumented build failed')
    samples=[]
    for index in range(20):
        result=q.command(['docker','exec',container,private+'/cold'],check=False)
        (folder/f'cold-{index:02}.jsonl').write_bytes(result.stdout)
        q.require(result.returncode==0,'Instrumented work failed: '+result.stderr.decode())
        rows=[json.loads(line) for line in result.stdout.decode().splitlines() if line.strip()]
        timeline=next(row for row in rows if row.get('kind')=='timeline')
        scheduler=[row for row in rows if row.get('kind')=='scheduler']
        q.require(len(scheduler)==7,'Scheduler samples missing')
        samples.append({'timeline':timeline,'scheduler':scheduler,'native':rows[0]})
    a.save(folder,'cold-samples.json',{'samples':samples,'epochs':20,'clock':'CLOCK_BOOTTIME',
          'T10':'NOT_REACHED_READINESS_CONSUMER', 'scheduler_interval':'Before trigger through post-decision ACK; exact runqueue counter but wider than freshness window',
          'kernel_delivery_event':'recvmsg return observed in BOOTTIME; actual kernel enqueue timestamp unavailable in this compatible clock',
          'IPC_queue_scheduler_separation':'Transport plus receive queue latency cannot be uniquely decomposed without compatible kernel tracing; recorded explicitly, not hidden in other',
          'baseline_hot_path_evidence_IO':'PRESENT_BEFORE_COMPLETE_VALIDATION',
          'original_source_sha256':q.sha(original.encode()),'instrumented_source_sha256':q.sha(measured.encode())})
    record['native_100us_cold_measurements']={'epochs':20,'participant_samples':140,'readiness_written':False}


def warm(sql,run,container,folder,record):
    private='/run/test-only-0090-warm'
    run(['docker','exec',container,'mkdir','-m','0700',private])
    run(['docker','cp',str(folder/'native-context.json'),container+':'+private+'/context.json'])
    for name in ['package_0090_native_100us_warm.c','package_0090_s04_native_health.c']:
        run(['docker','cp',str(q.ROOT/'scripts/validation'/name),container+':'+private+'/'+name])
    compile_result=q.command(['docker','exec',container,'cc','-O2','-Wall','-Wextra',private+'/package_0090_native_100us_warm.c','-o',private+'/warm','-lcrypto','/usr/lib/x86_64-linux-gnu/libpq.so.5'],check=False)
    a.save(folder,'warm-build.json',{'exit':compile_result.returncode,'stderr':compile_result.stderr.decode(),
        'source_sha256':q.sha((q.ROOT/'scripts/validation/package_0090_native_100us_warm.c').read_bytes())})
    q.require(compile_result.returncode==0,'Warm build failed')
    environment=run(['docker','exec',container,'sh','-c','getconf _NPROCESSORS_ONLN; cat /sys/fs/cgroup/cpu.max; cat /proc/loadavg; cat /proc/sys/kernel/perf_event_paranoid; uname -a']).decode()
    a.save(folder,'environment.json',{'observed':environment,'image':q.IMAGE,'container':record['isolation'],
        'realtime_scheduling_requested':False,'kernel_queue_trace_available':False,
        'measurement_limit':'recvmsg-return BOOTTIME observes delivery; transport/queue/guard descheduling cannot be uniquely attributed without compatible kernel tracing'})
    for mode in ['unpinned','pin']:
        result=q.command(['docker','exec',container,private+'/warm',mode],check=False)
        (folder/('warm-'+mode+'.json')).write_bytes(result.stdout)
        (folder/('warm-'+mode+'-stderr.txt')).write_bytes(result.stderr)
        a.save(folder, 'exit-'+mode+'.json', {'exit':result.returncode})
        q.require(result.returncode==0,'Warm work assertions failed: '+str(result.returncode)+' '+result.stderr.decode())
        data=json.loads(result.stdout)
        q.require(len(data['samples'])==500 and all(row['work_valid'] for row in data['samples']),'Complete measured mechanism cohort missing')
        q.require(data['hot_path_evidence_IO']=='NONE' and data['scheduler_policy']==0,'Hot path/scheduler drift')
    q.require(sql('SELECT count(*) FROM offline_readiness;').stdout.strip()==b'0','Benchmark must not publish readiness')
    record['native_100us_warm_measurements']={'epochs':1000,'participant_samples':7000,'warmup_epochs_per_mode':50,'readiness_written':False}
