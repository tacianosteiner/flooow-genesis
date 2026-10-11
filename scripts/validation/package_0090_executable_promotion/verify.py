"""Independent verifier: no generator imports and no trust in its PASS fields."""
from pathlib import Path
import hashlib,json,subprocess,sys
ROOT=Path(__file__).resolve().parents[3]
PIN_HEAD='0db4b7bed49ca76ca879875057d75bc2e68b0296'
PIN_SOURCE='b0ea86b6ba355fdf25fe09836bd4b75e4a4a2ad88ab7ef0e4724ca0d5a013e7d'
PATH='applications/marketplace-operations-persistence-postgres/src/main/resources/db/migration/V043__create_governed_offline_field_proof_capability_composition.sql'
def digest(b):return hashlib.sha256(b).hexdigest()
def verify(folder):
    folder=Path(folder);m=json.loads((folder/'PROMOTION-MANIFEST.json').read_text())
    current=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT).decode().strip();assert current==PIN_HEAD==m['input_commit']
    assert m['branch']==subprocess.check_output(['git','branch','--show-current'],cwd=ROOT).decode().strip()=='checkpoint/package-0090-cloud-handoff'
    assert m['repository_identity']==subprocess.check_output(['git','remote','get-url','origin'],cwd=ROOT).decode().strip()
    original=subprocess.check_output(['git','show',PIN_HEAD+':'+PATH],cwd=ROOT)
    assert digest(original)==PIN_SOURCE==m['frozen_source_sha256'] and m['frozen_source_path']==PATH
    assert digest((ROOT/PATH).read_bytes())==m['frozen_worktree_byte_sha256']
    # Independently recognize the first executable statement, including its end.
    lines=original.splitlines(keepends=True);start=sum(len(x) for x in lines[:next(i for i,x in enumerate(lines) if x.strip() and not x.lstrip().startswith(b'--'))])
    end=original.index(b'\n$$;',start)+len(b'\n$$;');removed=original[start:end]
    expected=b"DO $$\nBEGIN\n    RAISE EXCEPTION USING ERRCODE = '55000',\n        MESSAGE = 'Package 0090 V043 implementation closure is incomplete; execution denied';\nEND;\n$$;"
    assert removed==expected
    successor=(folder/m['successor_filename']).read_bytes();assert successor==original[:start]+original[end:]
    assert successor[:start]+removed+successor[start:]==original
    assert digest(successor)==m['successor_sha256']
    t=m['transformation'];assert t['offset']==start and t['length']==end-start and bytes.fromhex(t['removed_hex'])==removed
    assert digest(json.dumps(t,sort_keys=True,separators=(',',':')).encode())==m['transformation_digest']
    review=json.loads((ROOT/m['security_review_path']).read_text(encoding='utf-8-sig'))
    assert digest((ROOT/m['security_review_path']).read_bytes())==m['security_review_sha256'] and review['sql_source_sha256']==PIN_SOURCE and review['G3F_3B_IMPLEMENTATION_SECURITY_REVIEW']=='PASS'
    assert digest((ROOT/m['generation_tool']).read_bytes())==m['generation_tool_sha256']
    authorization=Path('C:/Users/xmz_r/.codex/attachments/7d018ca6-e53e-4b95-8b19-7c7a76b73d60/Pasted text.txt')
    assert digest(authorization.read_bytes())==m['explicit_authorization_sha256']
    assert digest((Path(__file__).parent/'CurrentPromotionFlyway.java').read_bytes())==m['runtime_consumer_source_sha256']
    assert m['marker']=='TEST_ONLY_NONCANONICAL' and m['rehearsal_execution_identity'].startswith('TEST_ONLY_NONCANONICAL-')
    assert all(m[k] is False for k in ['FROZEN_REFERENCE_MUTABLE','SUCCESSOR_CANONICAL','SUCCESSOR_PRODUCTION_ELIGIBLE','SUCCESSOR_NUMERIC_AUTHORITY'])
    assert m['SUCCESSOR_PROMOTION_SCOPE']=='DISPOSABLE_REHEARSAL_ONLY'
    required={'CANONICAL_V6_ACCESS','CANONICAL_V6_MUTATION','CANONICAL_DATABASE_MUTATION','CANONICAL_IDS','CANONICAL_KEYS','T0','CANONICAL_SIGN','CANONICAL_ADMIN','TREG','FINAL_RUNNER','PRODUCTION_DEPLOYMENT','PRODUCTION_SECRETS','NUMERIC_POLICY_ADOPTION','SERVICE_PRIVILEGE_EXPANSION','DOMAIN_SEMANTIC_CHANGE','FROZEN_SOURCE_MUTATION','NATIVE_PROTOCOL_CHANGE'}
    assert required==set(m['prohibitions'])
    return {'PROMOTION_MANIFEST_VERIFY':'PASS','SUCCESSOR_PROVENANCE_VERIFY':'PASS','SUCCESSOR_SEMANTIC_EQUIVALENCE':'PASS_ENVELOPE_ONLY_BODY_BYTES_EXACT','NONCANONICAL_MANIFEST_VERIFY':'PASS','manifest_sha256':digest((folder/'PROMOTION-MANIFEST.json').read_bytes()),'successor_sha256':digest(successor),'independence':'NO_GENERATOR_IMPORT; pinned user input hash/head; first statement recognized separately','semantic_statements_changed_N':0,'security_reviewed_domain_statements_changed_N':0}
if __name__=='__main__':
    folder=Path(sys.argv[1]);r=verify(folder);target=folder/'INDEPENDENT-VERIFICATION.json';assert not target.exists();target.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r))
