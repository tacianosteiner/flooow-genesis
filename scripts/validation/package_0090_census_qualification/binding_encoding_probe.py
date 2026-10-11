"""Independent native encoding of frozen JVM headers and actual stored header."""
import json,base64,hashlib
from pathlib import Path
import codec
def run(q):
    q.ex('gcc','-D_GNU_SOURCE','-std=c11','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','/usr/local/src-full/heartbeat_tests.c','-o','/usr/local/bin/heartbeat-tests','-lcrypto','-ldl',user='0')
    heartbeat=q.ex('/usr/local/bin/heartbeat-tests',user='0',ok=False)
    q.case('heartbeat_protocol','timestamp_replay_sender_adversarial_vectors',heartbeat.returncode==0,{'stdout':heartbeat.stdout,'stderr':heartbeat.stderr,'binary_sha256':q.ex('sha256sum','/usr/local/bin/heartbeat-tests',user='0').stdout})
    source='/usr/local/src-full/binding_encode.c';target='/usr/local/bin/binding-encode'
    q.ex('gcc','-D_GNU_SOURCE','-std=c11','-Wall','-Wextra','-Werror','-Wno-misleading-indentation',source,'-o',target,'-lcrypto','-ldl',user='0')
    reference=json.loads((q.ROOT/'docs/evidence/package-0090-g3f4-census-heartbeat-domain-parity/BINDING-REFERENCE-PARITY.json').read_text(encoding='utf-8'))
    results=[]
    for name,h,expected in [(str(v['vector']),v['header'],bytes.fromhex((q.ROOT/'docs/evidence/package-0090-g3f4-census-heartbeat-domain-parity/binding-parity/FROZEN-JVM-OUTPUT.txt').read_text().split('VECTOR_'+str(v['vector'])+'_BINDING_HEX=',1)[1].splitlines()[0])) for v in reference['vectors']]+[('stored_header',q.getheader(),None)]:
        text=''.join(str(i)+'\t'+str(h[field])+'\n' for i,field in enumerate(codec.FIELDS,1))
        q.rootfile('/usr/local/native-header.txt',text);r=q.ex(target,'/usr/local/native-header.txt','/usr/local/native-encoded.bin',user='0',ok=False)
        actual=base64.b64decode(q.ex('base64','-w','0','/usr/local/native-encoded.bin',user='0').stdout) if r.returncode==0 else b''
        digest=hashlib.sha256(actual).hexdigest()
        passed=r.returncode==0 and digest==codec.fingerprint(h) and (expected is None or actual==expected)
        result={'vector':name,'native_hex':actual.hex(),'native_digest':digest,'python_digest':codec.fingerprint(h),'byte_parity_with_frozen_jvm':actual==expected if expected else 'STORED_HEADER_NO_JVM_TYPED_ENCODER','exit':r.returncode,'stderr':r.stderr}
        results.append(result);q.case('encoding','independent_native_'+name,passed,result)
    q.save('NATIVE-ENCODING-PARITY.json',{'scope':'TEST_ONLY_NONCANONICAL','results':results,'binary_sha256':q.ex('sha256sum',target,user='0').stdout,'native_source_sha256':q.ex('sha256sum',source,user='0').stdout,'full_domain_authority_parity':'NOT_CLAIMED'})
