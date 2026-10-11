"""Hash exact uncommitted review bytes. This is not approval/provisioning authority."""
from pathlib import Path
import json,hashlib
ROOT=Path(__file__).resolve().parents[3];OUT=ROOT/'docs/evidence/package-0090-g3f4-census-heartbeat-domain-parity'
manifest=OUT/'SHA256-WORKTREE.json'
paths=[ROOT/'scripts/validation/package_0090_census_qualification',OUT]
files={str(p.relative_to(ROOT)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest() for folder in paths for p in sorted(folder.rglob('*')) if p.is_file() and p!=manifest and '__pycache__' not in str(p)}
manifest.write_bytes((json.dumps({'scope':'TEST_ONLY_NONCANONICAL','authority':'NONE_REVIEW_SNAPSHOT_ONLY','hash_domain':'Exact uncommitted worktree bytes; not canonical Git LF or signed approval','input_head':'0078290f79c8e6bcdc7b124ca0ae24963a915e2d','N':len(files),'files':files},indent=2)+'\n').encode('utf-8'))
print('REVIEW_HASHED_FILES',len(files))
