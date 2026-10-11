"""Freeze non-secret successor evidence after cleanup/scope audit; no Git mutation."""
from pathlib import Path
import hashlib,json,sys
OUT=Path(__file__).parent;ROOT=OUT.parents[2]
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    audit=json.loads((OUT/(sys.argv[1]+'-SCOPE-AUDIT.json')).read_text())
    assert audit['scope_PASS'] and not audit['owned_runtime_containers_remaining'] and not audit['owned_unit_containers_remaining']
    target=OUT/'SHA256-FINAL-SUCCESSOR-EVIDENCE.json';assert not target.exists()
    directories=[OUT,ROOT/'scripts/validation/package_0090_quarantine_qualification']
    files={str(p.relative_to(ROOT)).replace('\\','/'):digest(p) for directory in directories for p in directory.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p!=target}
    aggregate=hashlib.sha256(json.dumps(files,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    record={'scope':'TEST_ONLY_NONCANONICAL_NON_SECRET_SUCCESSOR_EVIDENCE','aggregate_domain':'SHA256 sorted compact JSON relative path/exact byte SHA256 map','sha256':aggregate,'files':files,'excluded':'self manifest and interpreter __pycache__; historical predecessor hashes separately checked 885 times','commit_created':False,'push_performed':False}
    target.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
    assert all(digest(ROOT/name)==value for name,value in files.items())
    print(json.dumps({'successor_non_secret_file_N':len(files),'evidence_sha256':aggregate,'manifest_sha256':digest(target),'all_frozen_evidence_hashes_verified':True}))
if __name__=='__main__':main()
