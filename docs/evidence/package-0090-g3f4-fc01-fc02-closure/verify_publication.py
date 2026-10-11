"""Verify staged exact bytes and immutable evidence without writing receipts."""
from pathlib import Path
import json,hashlib,subprocess
ROOT=Path(__file__).resolve().parents[3];OUT=Path(__file__).parent
manifest=OUT/'SHA256-FINAL-PUBLICATION.json';record=json.loads(manifest.read_text())
def sha(data):return hashlib.sha256(data).hexdigest()
expected=record['files']|{str(manifest.relative_to(ROOT)).replace('\\','/'):sha(manifest.read_bytes())}
staged=subprocess.run(['git','diff','--cached','--name-only','-z'],cwd=ROOT,capture_output=True,check=True).stdout.decode().split('\0')[:-1]
assert set(staged)==set(expected),'Staged scope must exactly equal six successor inventories plus manifest'
for name,digest in expected.items():
    assert sha((ROOT/name).read_bytes())==digest,('worktree changed',name)
    blob=subprocess.run(['git','show',':'+name],cwd=ROOT,capture_output=True,check=True).stdout
    assert sha(blob)==digest,('index normalization or mutation',name)
check=subprocess.run(['git','-c','core.whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol','diff','--cached','--check'],cwd=ROOT,capture_output=True,text=True)
assert check.returncode==0,(check.stdout,check.stderr)
print(json.dumps({'STAGED_EXACT_SCOPE':True,'STAGED_BLOB_WORKTREE_SHA256_EQUAL':True,'IMMUTABLE_EVIDENCE_INTACT':True,'DIFF_CHECK':True,'N':len(expected)}))
