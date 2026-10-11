"""Independent frozen JVM fixture/native framing/Python byte parity. Public only."""
from pathlib import Path
import subprocess,json,hashlib,os,sys,uuid,datetime,struct
import codec
ROOT=Path(__file__).resolve().parents[3];OUT=ROOT/'docs/evidence/package-0090-g3f4-census-heartbeat-domain-parity';HERE=Path(__file__).parent
dest=OUT/'binding-parity';dest.mkdir(exist_ok=False)
jdk=Path('C:/Program Files/Microsoft/jdk-21.0.12.8-hotspot/bin');classes=Path(os.environ['LOCALAPPDATA'])/'Temp/flooow-binding-parity-classes';classes.mkdir(exist_ok=True)
source=ROOT/'scripts/validation/Package0090EvidenceFixture.java'
subprocess.run([str(jdk/'javac.exe'),'-d',str(classes),str(source)],check=True,capture_output=True)
r=subprocess.run([str(jdk/'java.exe'),'-cp',str(classes),'Package0090EvidenceFixture'],capture_output=True,text=True,check=True)
(dest/'FROZEN-JVM-OUTPUT.txt').write_text(r.stdout,encoding='utf-8');values=dict(x.split('=',1) for x in r.stdout.splitlines())
result={'scope':'TEST_ONLY_NONCANONICAL','frozen_jvm_source':str(source.relative_to(ROOT)),'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'numeric_fixture_values':'ENCODING_REFERENCE_ONLY_NOT_AUTHORIZED','vectors':[]}
for v in range(1,4):
    src='café' if v==2 else 'order-1';uid=lambda n:str(uuid.UUID(int=n));cor=999 if v==3 else 15
    h={};ints=[1,1,1];id_tags={**dict(zip(range(2,7),range(1,6))),8:6,9:7,13:8,14:9,15:10,**dict(zip(range(21,29),[11,12,13,14,cor,16,17,18]))}
    for tag,name in enumerate(codec.FIELDS,1):
        if tag in id_tags:h[name]=uid(id_tags[tag])
        elif tag in [1,7,12]:h[name]=1
        elif tag in [10,11]:h[name]=values[f'VECTOR_{v}_MANIFEST_SHA256']
        elif tag==35:h[name]=values['POLICY_SHA256']
        elif tag in [29,30,31]:h[name]='1970-01-01T00:00:'+('01' if tag==31 else '00')+'.000001Z'
        elif tag==32:h[name]=values['SLOTS_HEX']
        else:h[name]={16:src,17:'integration-1',18:'TRANSACTION_IDENTITY_DECISION_WRITE',19:'reason',20:'fixture',33:'0090-v1',34:'fixture-1',36:'1',37:'1',38:'1'}[tag]
    raw=bytes.fromhex(values[f'VECTOR_{v}_BINDING_HEX']);p=dest/f'vector-{v}.bin';p.write_bytes(raw)
    result['vectors'].append({'vector':v,'jvm_digest':values[f'VECTOR_{v}_BINDING_SHA256'],'python_digest':codec.fingerprint(h),'parity':codec.fingerprint(h)==values[f'VECTOR_{v}_BINDING_SHA256'],'header':h})
(OUT/'BINDING-REFERENCE-PARITY.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf-8');print([v['parity'] for v in result['vectors']])
