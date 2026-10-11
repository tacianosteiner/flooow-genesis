"""Bounded owned overlay-storage I/O. No tmpfs/disk equivalence claim."""
import subprocess,time
def run(q):
    path='/usr/local/TEST_ONLY_NONCANONICAL-storage.bin';stop='/run/test-only-private/storage-stop'
    filesystem=q.ex('stat','-f','-c','%T','/usr/local',user='0').stdout.strip()
    q.case('storage','persistent_overlay_not_tmpfs',filesystem not in ['tmpfs','ramfs'],{'filesystem':filesystem,'underlying_host_device':'NOT_IDENTIFIED','size_cap_bytes':33554432})
    command='touch /run/test-only-private/storage-active; while test ! -e '+stop+'; do dd if=/dev/zero of='+path+' bs=4096 count=8192 conv=fdatasync 2>/dev/null || exit 91; done; rm -f /run/test-only-private/storage-active'
    generator=subprocess.Popen(['docker','exec','--user','0',q.NAME,'sh','-c',command],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    began=time.monotonic_ns();samples=[]
    try:
        ready=time.monotonic()+5
        while q.ex('test','-e','/run/test-only-private/storage-active',user='0',ok=False).returncode!=0 and time.monotonic()<ready:
            if generator.poll() is not None:break
            time.sleep(.05)
        for i,role in enumerate(['test_verifier','test_issuer','test_executor','test_auditor']):
            active_before=q.ex('test','-e','/run/test-only-private/storage-active',user='0',ok=False).returncode==0
            start=time.monotonic_ns();r=q.sql('SELECT 42;',role,ok=False);finish=time.monotonic_ns()
            active_after=q.ex('test','-e','/run/test-only-private/storage-active',user='0',ok=False).returncode==0
            sample={'role':role,'start_ns':start,'end_ns':finish,'elapsed_us':(finish-start)/1000,'generator_live_before_after':active_before and active_after and generator.poll() is None,'exit':r.returncode,'stderr':r.stderr}
            samples.append(sample);q.case('storage','overlap_'+role,r.returncode==0 and sample['generator_live_before_after'],sample)
    finally:
        q.ex('touch',stop,user='0');out,err=generator.communicate(timeout=30)
        q.case('storage','generator_completed',generator.returncode==0,{'exit':generator.returncode,'stderr':err.decode(errors='replace'),'begin_ns':began,'end_ns':time.monotonic_ns()})
        q.ex('rm','-f',path,stop,user='0')
        q.case('storage','owned_file_erased',q.ex('test','!','-e',path,user='0',ok=False).returncode==0,'Owned writable image overlay only; no Docker volume or host mount')
    q.save('STORAGE-COHORT.json',{'scope':'TEST_ONLY_NONCANONICAL','cohort':'container writable overlay with fdatasync','filesystem':filesystem,'samples':samples,'physical_storage_tail_claim':False,'numeric_policy_authority':'NONE'})
