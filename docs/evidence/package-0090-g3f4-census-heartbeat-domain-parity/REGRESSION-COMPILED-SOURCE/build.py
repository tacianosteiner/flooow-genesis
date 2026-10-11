"""Reproducible successor builder; no installation or canonical access."""
import pathlib,subprocess,json,sys,hashlib,urllib.request
import qualification as q
from prepare_sources import prepare
HERE=pathlib.Path(__file__).parent
OUT=pathlib.Path(sys.argv[sys.argv.index('--output')+1]).resolve()
attempt=[]
def call(a):
    r=subprocess.run(a,capture_output=True,text=True,timeout=45);attempt.append({'command':a,'exit':r.returncode,'stdout':r.stdout,'stderr':r.stderr})
    if r.returncode:raise RuntimeError(r.stderr)
def main():
    if OUT.exists():raise RuntimeError('Refuse existing output')
    if subprocess.run(['docker','inspect',q.NAME],capture_output=True).returncode==0:raise RuntimeError('Refuse existing owned container name')
    profile=q.ROOT/'docs/evidence/package-0090-g3f4-disposable-native-qualification/SECCOMP-TEST.json'
    header=urllib.request.urlopen('https://raw.githubusercontent.com/postgres/postgres/REL_18_4/src/interfaces/libpq/libpq-fe.h',timeout=30).read()
    assert hashlib.sha256(header).hexdigest()=='499d984421f5490be016f7d49a8599e7f8be120f0cf80c200e872265064be7c0'
    private=pathlib.Path.home()/'AppData/Local/Temp/flooow-native-qualification/libpq-fe.h';private.write_bytes(header)
    prepare();started=False
    try:
        call(['docker','run','--detach','--name',q.NAME,'--label','flooow.scope='+q.SCOPE,'--network','none','--cpus','1','--memory','768m','--security-opt','seccomp='+str(profile),'--tmpfs','/tmp','--tmpfs','/run','--tmpfs','/var/lib/postgresql','--entrypoint','sleep',q.IMAGE,'infinity']);started=True
        call(['docker','cp',str(HERE),q.NAME+':/usr/local/src-full']);call(['docker','cp',str(private),q.NAME+':/usr/local/src-full/libpq-fe.h'])
        flags=['gcc','-D_GNU_SOURCE','-std=c11','-Wall','-Wextra','-Werror','-Wno-misleading-indentation']
        for name,target,extra in [('login.c','/usr/local/lib/flooow_test_login.so',['-Wno-unused-parameter','-fPIC','-shared','-I/usr/include/postgresql/18/server','-I/usr/include/postgresql/internal']),('receiver.c','/usr/local/bin/flooow-test-receiver',['-I/usr/include/postgresql/18/server','-I/usr/local/src-full','-l:libpq.so.5']),('supervisor.c','/usr/local/bin/flooow-test-supervisor',[]),('frame_tests.c','/usr/local/bin/flooow-test-frame',[]),('boottime.c','/usr/local/bin/boottime',[])]:
            call(['docker','exec',q.NAME,*flags,'/usr/local/src-full/'+name,'-o',target,*extra,'-lcrypto','-ldl'])
        call(['docker','exec',q.NAME,'/usr/local/bin/flooow-test-frame'])
        args=[sys.executable,str(HERE/'qualification.py'),'--output',str(OUT)]
        if '--scenario-module' in sys.argv:args+=['--scenario-module',sys.argv[sys.argv.index('--scenario-module')+1]]
        r=subprocess.run(args)
        if r.returncode:raise RuntimeError('Qualification recorded failure/HOLD; inspect raw evidence')
    finally:
        if started:
            r=subprocess.run(['docker','inspect',q.NAME],capture_output=True,text=True)
            if r.returncode==0:
                i=json.loads(r.stdout)[0];assert i['Image']==q.IMAGE and i['Config']['Labels'].get('flooow.scope')==q.SCOPE
                subprocess.run(['docker','rm','-f',i['Id']],check=True,capture_output=True)
        OUT.mkdir(parents=True,exist_ok=True);(OUT/'BUILD.json').write_bytes((json.dumps(attempt,indent=2)+'\n').encode())
if __name__=='__main__':main()
