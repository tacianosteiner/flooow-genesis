"""Current public fixture through exact frozen JVM codecs and verifier boundary."""
from pathlib import Path
import subprocess,os,hashlib,json
def run(q):
    dest=q.OUT/'public-reference';dest.mkdir(exist_ok=False);classes=dest/'classes';classes.mkdir()
    bundle=q.expected_bundle
    values={'manifest':bundle['manifest_hex'],'preimage':q.ex('base64','-w','0','/run/flooow-external/preimage.bin',user='0').stdout,'spki':bundle['spki_hex'],'signature':bundle['signature_hex']}
    import base64
    for name,value in values.items():(dest/(name+'.bin')).write_bytes(base64.b64decode(value) if name=='preimage' else bytes.fromhex(value))
    jdk=Path('C:/Program Files/Microsoft/jdk-21.0.12.8-hotspot/bin')
    stdlib=list((Path.home()/'.gradle/caches/modules-2/files-2.1/org.jetbrains.kotlin/kotlin-stdlib/2.3.21').glob('**/*.jar'));assert len(stdlib)==1
    cp=os.pathsep.join(map(str,[classes,*q.ROOT.glob('**/build/classes/kotlin/main'),*stdlib]))
    operations=[]
    def execute(args):
        r=subprocess.run(args,capture_output=True,text=True,encoding='utf-8',timeout=90);operations.append({'command':args,'exit':r.returncode,'stdout':r.stdout,'stderr':r.stderr});return r
    compiled=execute([str(jdk/'javac.exe'),'-d',str(classes),str(q.HERE/'FrozenPublicParity.java'),str(q.HERE/'FrozenSnapshotParity.java')]);q.case('reference_verifier','public_helpers_compile',compiled.returncode==0,'No signing/private material or database access in these host helpers')
    common=[str(dest/(name+'.bin')) for name in ['manifest','preimage','spki','signature']]+[bundle['key_id']]
    for helper,args in [('FrozenPublicParity',common),('FrozenSnapshotParity',common+[bundle['authority']['id'],q.expected_header['issued_at'].replace('+00:00','Z')])]:
        r=execute([str(jdk/'java.exe'),'-cp',cp,helper,*args])
        for line in r.stdout.splitlines():
            if line.endswith('=PASS'):q.case('reference_verifier',line[:-5],True,{'actual_frozen_implementation':True,'input_scope':'PUBLIC_TEST_ONLY_NONCANONICAL','helper':helper})
        q.case('reference_verifier',helper+'_complete',r.returncode==0,{'stdout':r.stdout,'stderr':r.stderr,'scope':'Immutable artifact/JCA boundary only. Actual SQL authority/source/consumption joins remain unexecuted.'})
    hashes={str(p.relative_to(q.ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in q.ROOT.glob('applications/*/build/classes/kotlin/main/io/flooow/**/**Attestation*.class')}
    q.save('FROZEN-JVM-REFERENCE.json',{'operations':operations,'class_sha256':hashes,'host_signing':False,'full_SQL_semantic_verifier_parity':'HOLD','source':'Exact repository compiled Kotlin implementation; synthetic public snapshot input'})
