"""Exact managed live-record capture. No policy/source verdict."""
import argparse,pathlib,json,subprocess,hashlib,re,uuid,shlex
HERE=pathlib.Path(__file__).resolve().parent
IMAGE='sha256:07fc165de5bb569d822460e2df645c5489f99220fc2cb16c86596d39db394561'
DOCKER=['docker','--context','desktop-linux']
def call(args,**kw):return subprocess.run(DOCKER+args,capture_output=True,timeout=45,**kw)
def inspect(cid):
 q=call(['inspect',cid]);q.check_returncode();return json.loads(q.stdout)[0]
def validate(x,a):
 assert x['Id']==a.container and x['Image']==a.image and x['State']['Running']
 assert x['Config']['Labels'].get(a.label_key)==a.label_value
 assert x['HostConfig']['NetworkMode']=='none' and x['HostConfig']['ReadonlyRootfs']
 assert not x.get('Mounts') or all(m['Type'] in ['tmpfs','volume'] for m in x['Mounts'])
 assert x['HostConfig']['PidMode'] not in ['host']
def main():
 p=argparse.ArgumentParser();p.add_argument('--container',required=True);p.add_argument('--image',required=True);p.add_argument('--label-key',required=True);p.add_argument('--label-value',required=True);p.add_argument('--daemon',required=True)
 for name in ['pid','fd','start-ticks','device','inode','size']:p.add_argument('--'+name,required=True,type=int)
 p.add_argument('--sha256',required=True);a=p.parse_args()
 assert re.fullmatch('[0-9a-f]{64}',a.container) and re.fullmatch('sha256:[0-9a-f]{64}',a.image)
 assert re.fullmatch('[0-9a-f]{64}',a.sha256) and 0<a.pid<=2147483647 and 0<=a.fd<=63 and a.start_ticks>0 and 0<a.size<=4096
 info=call(['info','--format','{{.ID}}']);info.check_returncode();assert info.stdout.decode().strip()==a.daemon
 original=inspect(a.container);validate(original,a)
 source=(HERE/'capture.c').read_bytes();bindings=json.loads((HERE/'input-bindings.json').read_text());assert hashlib.sha256(source).hexdigest()==bindings['capture.c']
 args=[str(a.pid),str(a.fd),str(a.start_ticks),str(a.device),str(a.inode),str(a.size),a.sha256]
 command='gcc -std=c11 -O2 -Wall -Wextra -Werror -x c - -lcrypto -o /tmp/capture && exec /tmp/capture '+' '.join(shlex.quote(x) for x in args)
 name='independent-policy-read-'+uuid.uuid4().hex
 create=call(['create','-i','--pull','never','--name',name,'--label','flooow.independent.policy.capture='+name,'--network','none','--read-only','--user','0:0','--cap-drop','ALL','--cap-add','SYS_PTRACE','--security-opt','no-new-privileges','--pid','container:'+a.container,'--tmpfs','/tmp:rw,nosuid,nodev,size=16m','--entrypoint','/bin/sh',IMAGE,'-eu','-c',command]);create.check_returncode();cid=create.stdout.decode().strip();assert re.fullmatch('[0-9a-f]{64}',cid)
 result={'request':vars(a),'helper_id':cid,'helper_image':IMAGE,'source_sha256':hashlib.sha256(source).hexdigest(),'before':original}
 try:
  q=call(['start','--attach','--interactive',cid],input=source);result.update(returncode=q.returncode,stdout=q.stdout.decode(errors='replace'),stderr=q.stderr.decode(errors='replace'))
  after=inspect(a.container);validate(after,a);result['after']=after
  info=call(['info','--format','{{.ID}}']);info.check_returncode();assert info.stdout.decode().strip()==a.daemon
  assert q.returncode==0
  record=json.loads(q.stdout);assert record['sha256']==a.sha256 and len(bytes.fromhex(record['hex']))==a.size
  assert hashlib.sha256(bytes.fromhex(record['hex'])).hexdigest()==a.sha256
 finally:
  own=inspect(cid);assert own['Config']['Labels'].get('flooow.independent.policy.capture')==name and own['Id']==cid
  removal=call(['rm','--force','--volumes',cid]);result['cleanup_returncode']=removal.returncode
  (HERE/('capture-'+name+'.json')).write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':main()
