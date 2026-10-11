"""Version 1: deterministic current-head executable envelope, never edits source."""
from pathlib import Path
import hashlib,json,subprocess,uuid,datetime,sys
ROOT=Path(__file__).resolve().parents[3]
HEAD='0db4b7bed49ca76ca879875057d75bc2e68b0296'
SOURCE='applications/marketplace-operations-persistence-postgres/src/main/resources/db/migration/V043__create_governed_offline_field_proof_capability_composition.sql'
EXPECTED='b0ea86b6ba355fdf25fe09836bd4b75e4a4a2ad88ab7ef0e4724ca0d5a013e7d'
REVIEW='docs/evidence/PACKAGE-0090-G3F-3B-POST-H02-SECURITY-REVIEW.json'
AUTH=Path('C:/Users/xmz_r/.codex/attachments/7d018ca6-e53e-4b95-8b19-7c7a76b73d60/Pasted text.txt')
FENCE=b"DO $$\nBEGIN\n    RAISE EXCEPTION USING ERRCODE = '55000',\n        MESSAGE = 'Package 0090 V043 implementation closure is incomplete; execution denied';\nEND;\n$$;"
FORBIDDEN=['CANONICAL_V6_ACCESS','CANONICAL_V6_MUTATION','CANONICAL_DATABASE_MUTATION','CANONICAL_IDS','CANONICAL_KEYS','T0','CANONICAL_SIGN','CANONICAL_ADMIN','TREG','FINAL_RUNNER','PRODUCTION_DEPLOYMENT','PRODUCTION_SECRETS','NUMERIC_POLICY_ADOPTION','SERVICE_PRIVILEGE_EXPANSION','DOMAIN_SEMANTIC_CHANGE','FROZEN_SOURCE_MUTATION','NATIVE_PROTOCOL_CHANGE']
def sha(b):return hashlib.sha256(b).hexdigest()
def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT)
def main():
    out=Path(sys.argv[1]).resolve();assert not out.exists();out.mkdir(parents=True)
    assert git('branch','--show-current').decode().strip()=='checkpoint/package-0090-cloud-handoff'
    assert git('rev-parse','HEAD').decode().strip()==HEAD
    assert not git('diff','--name-only','HEAD').strip() and not git('diff','--cached','--name-only').strip()
    original=git('show',HEAD+':'+SOURCE);assert sha(original)==EXPECTED and original.count(FENCE)==1
    workspace=(ROOT/SOURCE).read_bytes();assert workspace.replace(b'\r\n',b'\n')==original
    review=json.loads((ROOT/REVIEW).read_text(encoding='utf-8-sig'));assert review['sql_source_sha256']==EXPECTED and review['G3F_3B_IMPLEMENTATION_SECURITY_REVIEW']=='PASS'
    offset=original.index(FENCE);candidate=original[:offset]+original[offset+len(FENCE):]
    assert candidate[:offset]+FENCE+candidate[offset:]==original
    payload=out/'V043__TEST_ONLY_NONCANONICAL_executable_successor.sql';payload.write_bytes(candidate)
    transformation={'kind':'REMOVE_EXACT_FIRST_UNCONDITIONAL_DO_ENVELOPE_ONLY','source_byte_domain':'ACCEPTED_GIT_BLOB_LF','offset':offset,'length':len(FENCE),'removed_hex':FENCE.hex(),'source_sha256':EXPECTED,'successor_sha256':sha(candidate),'semantic_statements_changed_N':0,'security_reviewed_domain_statements_changed_N':0}
    identity='TEST_ONLY_NONCANONICAL-'+uuid.uuid4().hex
    manifest={'contract_version':1,'repository_identity':git('remote','get-url','origin').decode().strip(),'branch':'checkpoint/package-0090-cloud-handoff','input_commit':HEAD,'frozen_source_path':SOURCE,'frozen_source_sha256':EXPECTED,'frozen_worktree_byte_sha256':sha(workspace),'frozen_source_byte_domain':'ACCEPTED_GIT_BLOB_LF; worktree CRLF identity bound separately','security_review_path':REVIEW,'security_review_sha256':sha((ROOT/REVIEW).read_bytes()),'explicit_authorization_sha256':sha(AUTH.read_bytes()),'generation_tool':str(Path(__file__).relative_to(ROOT)).replace('\\','/'),'generation_tool_version':1,'generation_tool_sha256':sha(Path(__file__).read_bytes()),'transformation':transformation,'transformation_digest':sha(json.dumps(transformation,sort_keys=True,separators=(',',':')).encode()),'successor_filename':payload.name,'successor_sha256':sha(candidate),'marker':'TEST_ONLY_NONCANONICAL','rehearsal_execution_identity':identity,'permitted_runtime_consumer':'CurrentPromotionFlyway: exact artifact digest checked immediately before migrate; guarded fresh isolated endpoint','runtime_consumer_source_sha256':sha((Path(__file__).parent/'CurrentPromotionFlyway.java').read_bytes()),'creation_timestamp':datetime.datetime.now(datetime.timezone.utc).isoformat(),'FROZEN_REFERENCE_MUTABLE':False,'SUCCESSOR_CANONICAL':False,'SUCCESSOR_PRODUCTION_ELIGIBLE':False,'SUCCESSOR_NUMERIC_AUTHORITY':False,'SUCCESSOR_PROMOTION_SCOPE':'DISPOSABLE_REHEARSAL_ONLY','prohibitions':FORBIDDEN}
    (out/'PROMOTION-MANIFEST.json').write_bytes((json.dumps(manifest,indent=2)+'\n').encode())
    print(json.dumps({'successor_sha256':sha(candidate),'manifest_sha256':sha((out/'PROMOTION-MANIFEST.json').read_bytes()),'identity':identity}))
if __name__=='__main__':main()
