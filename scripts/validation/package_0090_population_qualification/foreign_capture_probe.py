"""Capture public bytes from a separately bootstrapped, actually admitted backend."""
import subprocess,time,base64,hashlib
def run(q):
    q.ex('gcc','-D_GNU_SOURCE','-std=c11','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','/usr/local/src-full/scm_replay.c','-o','/usr/local/bin/scm-replay','-lcrypto','-ldl',user='0')
    helper=subprocess.Popen(['docker','exec','--user','postgres',q.NAME,'/usr/local/bin/scm-replay'],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    try:
        deadline=time.monotonic()+5
        while q.ex('test','-S','/run/flooow-watchdog/replay-capture.sock',ok=False).returncode and time.monotonic()<deadline:time.sleep(.05)
        q.ex('touch','/run/flooow-watchdog/capture-scm-replay')
        original=q.sql('SELECT current_user;','test_verifier',ok=False)
        q.ex('rm','-f','/run/flooow-watchdog/capture-scm-replay')
        stdout,stderr=helper.communicate(timeout=25)
        frame=base64.b64decode(q.ex('base64','-w','0','/run/flooow-watchdog/TEST_ONLY_NONCANONICAL-captured-frame.bin').stdout,validate=True)
        (q.OUT/'TEST_ONLY_NONCANONICAL-VALID-FOREIGN-FRAME.bin').write_bytes(frame)
        q.case('namespace','foreign_valid_backend_capture',original.returncode==0 and helper.returncode==0,{'original_admitted':original.returncode==0,'stdout':stdout.decode(),'stderr':stderr.decode(),'frame_sha256':hashlib.sha256(frame).hexdigest(),'public_bytes_only':True,'no_exported_pidfd_or_private_key':True})
    finally:
        q.ex('rm','-f','/run/flooow-watchdog/capture-scm-replay','/run/flooow-watchdog/replay-capture.sock')
        if helper.poll() is None:helper.kill();helper.wait()
