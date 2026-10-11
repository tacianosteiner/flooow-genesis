"""Record native positive/negative byte vectors in the owned disposable runtime."""
import json,subprocess,hashlib
from pathlib import Path
import qualification as q
OUT=q.ROOT/'docs/evidence/package-0090-g3f4-census-heartbeat-domain-parity';HERE=Path(__file__).parent
info=json.loads(q.cmd(['docker','inspect',q.NAME]).stdout)[0]
assert info['Image']==q.IMAGE and info['Config']['Labels'].get('flooow.scope')==q.SCOPE and info['HostConfig']['NetworkMode']=='none' and not info['Mounts']
dest=OUT/'binding-parity';raw=(dest/'vector-1.bin').read_bytes();at=4+int.from_bytes(raw[:4],'big')+2
bad={};b=bytearray(raw);b[at+1]=2;bad['reordered_or_duplicate_tag']=bytes(b)
b=bytearray(raw);b[at+6]=0;bad['null_required_field']=bytes(b)
b=bytearray(raw);b[at+1]=39;bad['unknown_tag']=bytes(b)
bad['trailing_bytes']=raw+b'x';bad['truncated']=raw[:-1]
b=bytearray(raw);b[at+6:at+11]=b'\1\0\0\0\0';bad['zero_version']=bytes(b)
for name,value in bad.items():(dest/(name+'.bin')).write_bytes(value)
q.cmd(['docker','cp',str(dest),q.NAME+':/usr/local/native-parity'])
cases=[]
for name,expected in [(f'vector-{i}',True) for i in range(1,4)]+[(name,False) for name in bad]:
    r=q.ex('/usr/local/bin/binding-codec','/usr/local/native-parity/'+name+'.bin',user='0',ok=False)
    cases.append({'name':name,'expected_accept':expected,'exit':r.returncode,'stdout':r.stdout,'stderr':r.stderr,'pass':(r.returncode==0)==expected})
result={'scope':'TEST_ONLY_NONCANONICAL','cases':cases,'N':len(cases),'failures':sum(not c['pass'] for c in cases),'binary_sha256':q.ex('sha256sum','/usr/local/bin/binding-codec',user='0').stdout,'source_sha256':hashlib.sha256((HERE/'binding_codec.c').read_bytes()).hexdigest(),'claim_limit':'38-tag framing only; not semantic full binding authority'}
(OUT/'NATIVE-BINDING-PARITY.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(result['N'],result['failures'])
