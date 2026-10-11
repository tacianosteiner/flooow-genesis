"""Actual previous joint epoch and original public-custody replay fixtures."""
import json,time,copy,subprocess,os,uuid,hashlib
def run(q):
    events=[json.loads(x) for x in q.ex('cat','/tmp/full.log').stdout.splitlines() if x.startswith('{')]
    old=next(e['epoch'] for e in reversed(events) if e.get('event')=='receiver_armed')
    q.ex('touch','/run/flooow-watchdog/capture-accept')
    try:assert q.sql('SELECT 1;','test_verifier',ok=False).returncode==0
    finally:q.ex('rm','-f','/run/flooow-watchdog/capture-accept')
    captured=q.ex('sha256sum','/run/flooow-watchdog/TEST_ONLY_NONCANONICAL-accept.bin').stdout.split()[0]
    q.ex('pg_ctl','-D','/tmp/pgdata','-m','fast','-w','stop');time.sleep(.3);q.boot()
    with q.health_lock:assert q.observer_once()
    events=[json.loads(x) for x in q.ex('cat','/tmp/full.log').stdout.splitlines() if x.startswith('{')]
    new=next(e['epoch'] for e in reversed(events) if e.get('event')=='receiver_armed')
    q.case('replay','actual_fresh_joint_generation',old!=new,{'old':old,'new':new,'context':'receiver/postmaster/supervisor/observer independently retained in one bootstrap'})
    q.ex('touch','/run/flooow-watchdog/replay-old-accept')
    try:
        result=q.sql('SELECT 1;','test_verifier',ok=False)
        q.case('replay','replayed_ACCEPT',result.returncode!=0 and 'FLOOOW_TEST_ENROLLMENT_DENIED' in result.stderr,{'stderr':result.stderr,'actual_previously_accepted_reply_sha256':captured,'old_epoch':old,'current_epoch':new,'reply_source':'exact prior 76 bytes, not flipped or fabricated bytes'})
    finally:q.ex('rm','-f','/run/flooow-watchdog/replay-old-accept')
    q.case('replay','current_ACCEPT_after_actual_replay_recovers',q.sql('SELECT 1;','test_verifier',ok=False).returncode==0,'No reuse of old reply or old backend request digest')
    q.rootfile('/run/flooow-watchdog/old-epoch.bin',bytes.fromhex(old))
    try:
        r=q.sql('SELECT 1;','test_verifier',ok=False)
        q.case('replay','actual_old_joint_generation_frame',r.returncode!=0,{'stderr':r.stderr,'old_epoch':old,'current_epoch':new,'new_live_self_anchor':True,'same_full_synthetic_binding':True})
    finally:q.ex('rm','-f','/run/flooow-watchdog/old-epoch.bin')
    q.case('replay','current_generation_frame_recovers',q.sql('SELECT 1;','test_verifier',ok=False).returncode==0,'Old bytes cannot rebuild current retained registry')
    approval=copy.deepcopy(q.expected_approval);approval['revision']=0;q.mutate_external('/run/flooow-external/approval.json',approval,'old_approval_generation_frame','replay')
    bundle=copy.deepcopy(q.expected_bundle);bundle['authority']['revision']=0;q.mutate_external('/run/flooow-external/attestation.json',bundle,'old_attestation_bundle_frame','replay')
    for flag in ['replay-accept-epoch','replay-accept-digest']:
        q.ex('touch','/run/flooow-watchdog/'+flag)
        try:q.denial('replay',flag)
        finally:q.ex('rm','-f','/run/flooow-watchdog/'+flag)
    q.ex('gcc','-D_GNU_SOURCE','-std=c11','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','/usr/local/src-full/scm_replay.c','-o','/usr/local/bin/scm-replay','-lcrypto','-ldl',user='0')
    helper=subprocess.Popen(['docker','exec','--user','postgres',q.NAME,'/usr/local/bin/scm-replay'],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    try:
        deadline=time.monotonic()+5
        while q.ex('test','-S','/run/flooow-watchdog/replay-capture.sock',ok=False).returncode and time.monotonic()<deadline:time.sleep(.05)
        q.ex('touch','/run/flooow-watchdog/capture-scm-replay')
        original=q.sql('SELECT 1;','test_verifier',ok=False)
        q.ex('rm','-f','/run/flooow-watchdog/capture-scm-replay')
        stdout,stderr=helper.communicate(timeout=25)
        q.case('replay','replayed_SCM_RIGHTS',original.returncode==0 and helper.returncode==0,{'actual_original_backend_admitted':original.returncode==0,'stdout':stdout.decode(),'stderr':stderr.decode(),'helper_exit':helper.returncode,'anchor_acquisition':'SCM_RIGHTS from actual self pidfd; no foreign PID lookup','experimental_helper_budget_s':20,'policy_authority':'NONE','binary_sha256':q.ex('sha256sum','/usr/local/bin/scm-replay',user='0').stdout})
    finally:
        q.ex('rm','-f','/run/flooow-watchdog/capture-scm-replay','/run/flooow-watchdog/replay-capture.sock')
        if helper.poll() is None:helper.kill();helper.wait()
    q.case('replay','native_admission_after_descriptor_replay_recovers',q.sql('SELECT 1;','test_verifier',ok=False).returncode==0,'Dead replay cannot promote the observation registry or reopen a prior anchor')
    foreign=q.OUT/'foreign-valid-namespace'
    env=os.environ.copy();env['FLOOOW_TEST_NAMESPACE_CONTAINER']='flooow-0090-quarantine-namespace-'+uuid.uuid4().hex[:12]
    with (q.OUT/'FOREIGN-NAMESPACE.console.log').open('w',encoding='utf-8') as stream:
        child=subprocess.run([q.sys.executable,str(q.HERE/'build.py'),'--output',str(foreign),'--scenario-module','foreign_capture_probe'],env=env,stdout=stream,stderr=subprocess.STDOUT,timeout=180)
    raw=json.loads((foreign/'RAW-QUALIFICATION.json').read_text())
    q.record['nested_namespace_evidence']={'directory':'foreign-valid-namespace','container_name':env['FLOOOW_TEST_NAMESPACE_CONTAINER'],'scope':'TEST_ONLY_NONCANONICAL','private_material_exported':False}
    for case in raw['cases']:
        q.record['cases'].append({**case,'group':'foreign_namespace/'+case['group'],'nested_raw_path':'foreign-valid-namespace/RAW-QUALIFICATION.json'})
    q.case('namespace','independent_valid_bootstrap_cleanup',child.returncode==0 and not raw['errors'] and raw['owned_container_removed'] and raw['private_key_erasure'] and raw['private_key_absent'],{'errors':raw['errors'],'container_removed':raw['owned_container_removed'],'private_key_absent':raw['private_key_absent'],'network':'none','mounts':[]})
    frame=(foreign/'TEST_ONLY_NONCANONICAL-VALID-FOREIGN-FRAME.bin').read_bytes()
    assert raw['isolation']['id']!=q.record['isolation']['id']
    assert json.loads((foreign/'SYNTHETIC-PUBLIC-CONTEXT.json').read_text())['approval']['binding_id']!=q.expected_approval['binding_id']
    q.rootfile('/run/flooow-watchdog/TEST_ONLY_NONCANONICAL-foreign-frame.bin',frame,mode='0600')
    q.ex('chown','999:999','/run/flooow-watchdog/TEST_ONLY_NONCANONICAL-foreign-frame.bin',user='0')
    q.ex('gcc','-D_GNU_SOURCE','-std=c11','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','/usr/local/src-full/namespace_replay.c','-o','/usr/local/bin/namespace-replay','-lcrypto','-ldl',user='0')
    result=q.ex('/usr/local/bin/namespace-replay',ok=False)
    q.case('replay','valid_protocol_wrong_namespace',result.returncode==0,{'stdout':result.stdout,'stderr':result.stderr,'exit':result.returncode,'foreign_frame_sha256':hashlib.sha256(frame).hexdigest(),'bytes_unmodified':True,'sender_self_anchor':'native helper own self pidfd; same UID/GID and kernel peer/sender identity','expected_denial_boundary':'full context reason 3 before catalog or registry promotion','descriptor_cross_namespace_transfer':False,'numeric_policy_authority':'NONE'})
    q.case('namespace','current_native_admission_after_foreign_context_recovers',q.sql('SELECT 1;','test_verifier',ok=False).returncode==0,'Foreign context cannot grant eligibility or erase current enrollment')
