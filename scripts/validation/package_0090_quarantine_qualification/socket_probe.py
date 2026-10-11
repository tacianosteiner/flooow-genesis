"""Real owned socket path/peer faults under the final full synthetic context."""
import subprocess,time
def run(q):
    path='/run/flooow-watchdog/enrollment-v1.sock';saved=path+'.TEST_ONLY_NONCANONICAL-held'
    q.ex('mv',path,saved)
    try:q.denial('socket','socket_removed')
    finally:q.ex('mv',saved,path)
    q.case('socket','removed_path_restored',q.sql('SELECT 1;','test_verifier',ok=False).returncode==0,'Same retained receiver; original inode restored')
    for mode in ['0640','0666','0000']:
        q.ex('chmod',mode,path)
        try:q.denial('socket','wrong_mode_'+mode)
        finally:q.ex('chmod','0600',path)
        q.case('socket','mode_restored_'+mode,q.sql('SELECT 1;','test_verifier',ok=False).returncode==0,'Mandatory path validation remains active')
    q.ex('chown','0:0',path,user='0')
    try:q.denial('socket','wrong_owner')
    finally:q.ex('chown','999:999',path,user='0')
    q.case('socket','owner_restored',q.sql('SELECT 1;','test_verifier',ok=False).returncode==0,'Only disposable socket ownership changed')
    q.ex('gcc','-D_GNU_SOURCE','-std=c11','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','/usr/local/src-full/fake_receiver.c','-o','/usr/local/bin/fake-receiver','-lcrypto','-ldl',user='0')
    q.ex('mv',path,saved)
    fake=None
    try:
        fake=subprocess.Popen(['docker','exec','--user','postgres',q.NAME,'/usr/local/bin/fake-receiver'],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        deadline=time.monotonic()+5
        while q.ex('test','-S',path,ok=False).returncode and time.monotonic()<deadline:time.sleep(.05)
        result=q.sql('SELECT 1;','test_verifier',ok=False)
        q.case('socket','replacement_fake_receiver_wrong_kernel_peer',result.returncode!=0 and 'receiver identity mismatch' in result.stderr,{'stderr':result.stderr,'exit':result.returncode,'namespace_mode':'0600','same_uid_fixture':True})
        fake.communicate(timeout=5)
        q.case('socket','fake_receiver_exits',fake.returncode==0,{'meaning':'Connect rejected before trusting foreign receiver; no process signaling','binary_sha256':q.ex('sha256sum','/usr/local/bin/fake-receiver',user='0').stdout,'source_sha256':q.ex('sha256sum','/usr/local/src-full/fake_receiver.c',user='0').stdout})
    finally:
        if fake and fake.poll() is None:fake.kill();fake.wait()
        q.ex('rm','-f',path);q.ex('mv',saved,path)
    q.case('socket','exact_receiver_restored',q.sql('SELECT 1;','test_verifier',ok=False).returncode==0,'Retained receiver anchor unchanged')
    for name in ['stale_enrollment_frame','old_receiver_generation_frame','old_supervisor_generation_frame','old_postmaster_generation_frame','old_approval_generation_frame','old_attestation_bundle_frame','replayed_ACCEPT','replayed_SCM_RIGHTS','valid_protocol_wrong_namespace']:
        q.record['cases'].append({'group':'replay','name':name,'result':'NOT_RUN_THIS_COHORT','detail':'Explicit cross-cohort reconciliation required: only same-final-source replay_probe and schedule_probe may resolve selected generation/ACCEPT/actual SCM cases. Revision tampering does not prove replay of a previously valid older authority ceremony. A second concurrently valid isolated namespace is not qualified. No earlier PASS inherited.'})
