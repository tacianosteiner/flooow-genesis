"""Execute frozen codecs on public disposable material. Never generates keys."""
from pathlib import Path
import json,subprocess,hashlib,os,sys
ROOT=Path(__file__).resolve().parents[3];HERE=Path(__file__).parent
OUT=ROOT/'docs/evidence/package-0090-g3f4-census-heartbeat-domain-parity'
final='--final' in sys.argv;hup='--hup-final' in sys.argv
source=OUT/('hup-final-28-binding_encoding_probe/SYNTHETIC-PUBLIC-CONTEXT.json' if hup else 'corrected-16-binding_encoding_probe/SYNTHETIC-PUBLIC-CONTEXT.json' if final else 'regression-main/SYNTHETIC-PUBLIC-CONTEXT.json')
q=json.loads(source.read_text())
b=q['original_attestation'];dest=OUT/('hup-final-public-parity' if hup else 'final-public-parity' if final else 'public-parity');dest.mkdir(exist_ok=False)
for name,value in [('manifest',b['manifest_hex']),('preimage',q['preimage_hex']),('spki',b['spki_hex']),('signature',b['signature_hex'])]:(dest/(name+'.bin')).write_bytes(bytes.fromhex(value))
jdk=Path('C:/Program Files/Microsoft/jdk-21.0.12.8-hotspot/bin')
classes=Path(os.environ['LOCALAPPDATA'])/'Temp/flooow-public-parity-classes';classes.mkdir(exist_ok=True)
cp=[ROOT/p for p in ['applications/marketplace-operations/build/classes/kotlin/main','libraries/organization/build/classes/kotlin/main']]
# Include current repository's compiled domain value classes, never canonical data.
cp=list(ROOT.glob('**/build/classes/kotlin/main'))
stdlib=list((Path.home()/'.gradle/caches/modules-2/files-2.1/org.jetbrains.kotlin/kotlin-stdlib/2.3.21').glob('**/*.jar'));assert len(stdlib)==1
classpath=os.pathsep.join(map(str,[classes,*cp,*stdlib]))
runs=[]
def run(args):
    r=subprocess.run(args,capture_output=True,text=True,encoding='utf-8',timeout=90);runs.append({'command':args,'exit':r.returncode,'stdout':r.stdout,'stderr':r.stderr});return r
r=run([str(jdk/'javac.exe'),'-d',str(classes),str(HERE/'FrozenPublicParity.java')]);assert r.returncode==0
r=run([str(jdk/'java.exe'),'-cp',classpath,'FrozenPublicParity',*[str(dest/(n+'.bin')) for n in ['manifest','preimage','spki','signature']],b['key_id']])
result={'scope':'PUBLIC_TEST_ONLY_NONCANONICAL_MATERIAL','signing_executed':False,'runs':runs,'result':'PASS_PRIMITIVES_ONLY' if r.returncode==0 else 'FAIL','full_domain_authority_parity':'HOLD_NOT_EXECUTED','class_hashes':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'applications/marketplace-operations/build/classes/kotlin/main/io/flooow/marketplace/operations/authorization').glob('*.class')}}
result['public_material_source']=str(source.relative_to(ROOT))
(OUT/('HUP-FINAL-PUBLIC-JVM-PARITY.json' if hup else 'FINAL-PUBLIC-JVM-PARITY.json' if final else 'PUBLIC-JVM-PARITY.json')).write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(result['result'])
