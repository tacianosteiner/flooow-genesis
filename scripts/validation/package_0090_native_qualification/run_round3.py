"""Reproducible disposable builder. Refuses existing names/evidence; always cleans.

Run only under the explicit disposable implementation authority. No canonical
mount/network. No package installation; exact PG18.4 header is fetched/pinned.
"""
from pathlib import Path
import subprocess,json,urllib.request,hashlib,sys
import qualify as q
ROOT=Path(__file__).resolve().parents[3]
NAME='flooow-0090-native-qual-bd84005-r3'
MEASURE='--measure' in sys.argv
if MEASURE:NAME='flooow-0090-native-qual-bd84005-measure'
IMAGE=q.IMAGE
BUILD=[]
def call(a):
    r=subprocess.run(a,text=True,capture_output=True,timeout=45)
    BUILD.append({'command':a,'exit':r.returncode,'stdout':r.stdout,'stderr':r.stderr})
    if r.returncode:raise RuntimeError(r.stderr[-2000:])
    return r.stdout
def main():
    if subprocess.run(['docker','inspect',NAME],capture_output=True).returncode==0:raise RuntimeError('Existing test container: refuse reuse')
    dest=q.PRIVATE;dest.mkdir(exist_ok=True)
    profile=ROOT/'docs/evidence/package-0090-g3f4-disposable-native-qualification/SECCOMP-TEST.json'
    assert profile.is_file(),'Pinned source profile missing'
    evidence_root=profile.parent
    metadata=json.loads((evidence_root/'measurement/QUALIFICATION.json').read_text())['seccomp']
    assert hashlib.sha256(profile.read_bytes()).hexdigest()==metadata['derived_sha256']
    (dest/'seccomp-evidence.json').write_bytes((json.dumps(metadata,indent=2)+'\n').encode())
    output=Path(sys.argv[sys.argv.index('--evidence-output')+1]).resolve() if '--evidence-output' in sys.argv else evidence_root/('measurement' if MEASURE else 'round3')
    if output.exists():raise RuntimeError('Refuse to overwrite existing evidence')
    header=urllib.request.urlopen('https://raw.githubusercontent.com/postgres/postgres/REL_18_4/src/interfaces/libpq/libpq-fe.h',timeout=30).read()
    assert hashlib.sha256(header).hexdigest()=='499d984421f5490be016f7d49a8599e7f8be120f0cf80c200e872265064be7c0'
    (dest/'libpq-fe.h').write_bytes(header)
    started=False
    try:
        call(['docker','run','--detach','--name',NAME,'--label','flooow.scope='+q.SCOPE,'--network','none','--security-opt','seccomp='+str(profile),'--tmpfs','/tmp','--tmpfs','/run','--tmpfs','/var/lib/postgresql','--entrypoint','sleep',IMAGE,'infinity']);started=True
        call(['docker','exec',NAME,'mkdir','-p','/usr/local/test-io'])
        call(['docker','exec',NAME,'chown','999:999','/usr/local/test-io'])
        call(['docker','cp',str(Path(__file__).parent),NAME+':/usr/local/src-native'])
        call(['docker','cp',str(dest/'libpq-fe.h'),NAME+':/usr/local/src-native/libpq-fe.h'])
        flags=['gcc','-D_GNU_SOURCE','-std=c11','-Wall','-Wextra','-Werror','-Wno-misleading-indentation']
        builds=[('login.c','/usr/local/lib/flooow_test_login.so',['-Wno-unused-parameter','-fPIC','-shared','-I/usr/include/postgresql/18/server','-I/usr/include/postgresql/internal','-lcrypto']),('receiver.c','/usr/local/bin/flooow-test-receiver',['-I/usr/include/postgresql/18/server','-I/usr/local/src-native','-l:libpq.so.5','-lcrypto']),('supervisor.c','/usr/local/bin/flooow-test-supervisor',['-lcrypto']),('frame_tests.c','/usr/local/bin/flooow-test-frame',['-lcrypto']),('fake_receiver.c','/usr/local/bin/flooow-test-fake-receiver',['-lcrypto']),('clone3_probe.c','/usr/local/bin/clone3-probe',[])]
        for source,target,extra in builds:call(['docker','exec',NAME,*flags,'/usr/local/src-native/'+source,'-o',target,*extra])
        r=subprocess.run([sys.executable,str(Path(__file__).with_name('qualify.py')),'--measure' if MEASURE else '--round3','--evidence-output',str(output)])
        if r.returncode:raise RuntimeError('Qualification harness failed')
    finally:
        if started:
            p=subprocess.run(['docker','inspect',NAME],capture_output=True,text=True)
            if not p.returncode:
                i=json.loads(p.stdout)[0];assert i['Image']==IMAGE and i['Config']['Labels'].get('flooow.scope')==q.SCOPE
                subprocess.run(['docker','rm','-f',i['Id']],capture_output=True,check=True)
        output.mkdir(parents=True,exist_ok=True)
        report=output/'BUILD-ATTEMPTS.json'
        prior=json.loads(report.read_text(encoding='utf-8')) if report.exists() else [{'historical_attempt':'First round3 builder failed clone3 probe -D_GNU_SOURCE duplicate macro under -Werror; owned container removed; no PG startup. Corrected with conditional macro guard.'}]
        prior.append({'round3_build_commands':BUILD})
        report.write_bytes((json.dumps(prior,indent=2)+'\n').encode())
if __name__=='__main__':main()
