"""Evidence-first S02 expected signed-input boundary; no DB or runtime proof."""
import base64
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import uuid
import package_0090_source_gate as gate

PRODUCER=gate.ROOT/'applications/command-authority-ceremony/src/main/kotlin/io/flooow/ceremony/PostgresOfflineFieldProofSupport.kt'
CODEC=gate.ROOT/'applications/marketplace-operations/src/main/kotlin/io/flooow/marketplace/operations/authorization/ApprovalAttestationCanonicalCodec.kt'


def fixture_input():
    path=gate.ROOT/'applications/command-authority-ceremony/src/test/kotlin/io/flooow/ceremony/OfflineFieldProofInputLoaderTest.kt'
    template=path.read_text(encoding='utf-8-sig').split('private fun validArtifact(): String = listOf(',1)[1].split(').joinToString',1)[0]
    lines=[]
    for line in template.splitlines():
        line=line.strip().rstrip(',')
        if not line:continue
        if not line.startswith('"') or not line.endswith('"'):raise ValueError('Fixture template changed')
        line=line[1:-1]
        line=re.sub(r'\$\{uuid\((\d+)\)\}',lambda m:str(uuid.UUID(int=int(m[1]))),line)
        line=re.sub(r'\$\{"([ab])"\.repeat\(64\)\}',lambda m:m[1]*64,line)
        if line.startswith('attestation.signatureBase64Url='):
            line='attestation.signatureBase64Url='+base64.urlsafe_b64encode(bytes([1])*64).decode().rstrip('=')
        if '${' in line:raise ValueError('Unresolved fixture expression')
        lines.append(line)
    return '\n'.join(lines)+'\n'


def audit():
    source=(gate.ROOT/gate.V043).read_text(encoding='utf-8-sig')
    statements,_=gate.parse(source)
    header=next(s['CreateStmt'] for s in statements if 'CreateStmt' in s and s['CreateStmt']['relation']['relname']=='offline_binding_header')
    columns=[elt['ColumnDef']['colname'] for elt in header['tableElts'] if 'ColumnDef' in elt]
    expected={'algorithm_id','signer_key_id','signer_key_fingerprint','signature_bytes'}
    if expected.intersection(columns):raise ValueError('Binding source changed; reevaluate boundary')
    spec=(gate.ROOT/gate.SPEC).read_text(encoding='utf-8-sig')
    s02=spec.split('**S02**',1)[1].split('**S03**',1)[0]
    signature=s02.split('`public.offline_inspect(',1)[1].split(')`',1)[0]
    if [part.strip().split()[1] for part in signature.split(',')]!=['pg_catalog.uuid','pg_catalog.bytea','pg_catalog.uuid','pg_catalog.text']:
        raise ValueError('S02 signature changed')
    binding=spec.split('## 4. Immutable binding and fingerprint',1)[1].split('## 5.',1)[0]
    tag_rows=[line for line in binding.splitlines() if re.match(r'\| \d+-\d+ \|',line)]
    if len(tag_rows)!=7 or 'V1 count=38.' not in binding or any(field in '\n'.join(tag_rows) for field in expected):
        raise ValueError('38-tag signed-input exclusion changed')
    codec=CODEC.read_text(encoding='utf-8-sig').split('fun canonicalManifestBytes',1)[1].split('fun manifestDigest',1)[0]
    if any(field in codec for field in ('signerKey','signatureBytes','algorithmId')):raise ValueError('Manifest contains signing identity now')
    producer=PRODUCER.read_text(encoding='utf-8-sig').split('private fun acceptedArtifact',1)[1].split('private fun consumption',1)[0]
    comparisons=['proof.algorithmId == signed.algorithmId','proof.signerKeyId == signed.signerKeyId',
                 'proof.signerKeyFingerprint == signed.signerKeyFingerprint',
                 'publicKey.fingerprint() == signed.signerKeyFingerprint',
                 'proof.signatureBytes().contentEquals(signed.signatureBytes())']
    if not all(c in producer for c in comparisons):raise ValueError('Frozen expected comparisons changed')
    stdlib=list((Path.home()/'.gradle/caches/modules-2/files-2.1/org.jetbrains.kotlin/kotlin-stdlib/2.3.21').glob('*/*.jar'))
    if len(stdlib)!=1:raise ValueError('Pinned stdlib missing')
    classes=[p for p in gate.ROOT.glob('applications/*/build/classes/kotlin/main')]
    classes+=list(gate.ROOT.glob('platform/foundation/*/build/classes/kotlin/main'))
    cp=os.pathsep.join(map(str,[*classes,stdlib[0]]))
    def run(args):
        result=subprocess.run(args,capture_output=True,text=True)
        if result.returncode:raise RuntimeError(result.stderr)
        return result.stdout
    with tempfile.TemporaryDirectory(prefix='flooow-0090-s02-input-') as scratch:
        fixture=Path(scratch)/'test.input';fixture.write_text(fixture_input(),encoding='utf-8',newline='\n')
        run(['javac','-cp',cp,'-d',scratch,str(gate.ROOT/'scripts/validation/Package0090S02ExpectedAttestationWitness.java')])
        output=run(['java','-cp',scratch+os.pathsep+cp,'Package0090S02ExpectedAttestationWitness',str(fixture)])
    witness=dict(line.split('=',1) for line in output.splitlines())
    wanted={'CANONICAL_MANIFEST_EQUAL':'true','PLAN_EQUAL':'true','STORED_A_EXPECTED_A':'true',
            'STORED_A_EXPECTED_B':'false','STORED_B_EXPECTED_A':'false','STORED_B_EXPECTED_B':'true'}
    if any(witness.get(k)!=v for k,v in wanted.items()):raise ValueError('Witness did not establish expected-input distinction')
    return dict(gate='G3F.3B_S02_EXPECTED_SIGNED_ATTESTATION_BINDING',status='HOLD_MISSING_INDEPENDENT_EXPECTED_INPUT',
                reference='ACTUAL_FROZEN_ACCEPTED_METHOD_WITH_MOCK_JDBC_NO_DATABASE',
                witness=witness,s02_signature=signature,binding_columns=columns,
                binding_tag_rows=tag_rows,missing_expected_signed_fields=sorted(expected-{'algorithm_id'}),
                algorithm_constraint='STATIC_ED25519_SUFFICIENT_NOT_A_MISSING_EXPECTATION',
                frozen_comparisons=comparisons,producer_sha256=hashlib.sha256(PRODUCER.read_bytes()).hexdigest(),
                codec_sha256=hashlib.sha256(CODEC.read_bytes()).hexdigest(),
                physical_column_grants=len(gate.expected_column_grants(spec)),
                conclusion='Same manifest/plan and all binding fields cannot distinguish two valid original signed inputs whose frozen accepted decisions differ for the same stored artifact.',
                s02_implemented=False,unresolved_authority_blocker_count=1,
                database_connection_attempted=False,protected_database_mutation=False)


if __name__=='__main__':
    report=audit()
    target=gate.ROOT/'docs/evidence/PACKAGE-0090-S02-EXPECTED-ATTESTATION-AUTHORITY.json'
    target.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k in ('gate','status','witness','missing_expected_signed_fields','physical_column_grants')},indent=2))
