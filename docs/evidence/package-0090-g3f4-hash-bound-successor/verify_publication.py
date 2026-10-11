"""Verify every published Git blob against the exact preserved worktree bytes."""
from pathlib import Path
import subprocess,json,hashlib,sys
ROOT=Path(__file__).resolve().parents[3];HERE=Path(__file__).parent
p=HERE/'final-02/SHA256-PUBLICATION.json';r=json.loads(p.read_text());files=dict(r['files']);files[p.relative_to(ROOT).as_posix()]=hashlib.sha256(p.read_bytes()).hexdigest()
prefix=':' if sys.argv[1]=='index' else sys.argv[1]+':'
batch=subprocess.run(['git','cat-file','--batch'],input=''.join(prefix+n+'\n' for n in files).encode(),stdout=subprocess.PIPE,check=True,cwd=ROOT).stdout
cursor=0
for name,expected in files.items():
    end=batch.index(b'\n',cursor);header=batch[cursor:end].split();assert len(header)==3 and header[1]==b'blob',(name,header)
    size=int(header[2]);blob=batch[end+1:end+1+size];assert hashlib.sha256(blob).hexdigest()==expected,name
    assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==expected,name
    cursor=end+size+2
assert cursor==len(batch)
print(json.dumps({'domain':sys.argv[1],'exact_blobs_verified':len(files),'mismatch':0}))
