"""Freeze successor evidence bytes; no approval or runtime authority."""
from pathlib import Path
import json,hashlib
ROOT=Path(__file__).resolve().parents[3];OUT=Path(__file__).parent
PREFIXES=['docs/evidence/package-0090-g3f4-fc01-fc02-closure','scripts/validation/package_0090_population_qualification','docs/evidence/package-0090-g3f4-census-heartbeat-domain-parity','docs/evidence/package-0090-g3f4-quarantine-closure','scripts/validation/package_0090_census_qualification','scripts/validation/package_0090_quarantine_qualification']
manifest=OUT/'SHA256-FINAL-PUBLICATION.json'
assert not manifest.exists(),'Refuse replacing immutable evidence'
files={str(p.relative_to(ROOT)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest() for prefix in PREFIXES for p in sorted((ROOT/prefix).rglob('*')) if p.is_file() and p!=manifest and '__pycache__' not in p.parts}
aggregate=hashlib.sha256(json.dumps(files,sort_keys=True,separators=(',',':')).encode()).hexdigest()
manifest.write_bytes((json.dumps({'scope':'TEST_ONLY_NONCANONICAL','authority':'NONE_EVIDENCE_PRESERVATION_ONLY','domain':'Exact worktree bytes; compact sorted JSON path/SHA256 aggregate; excludes this self manifest and ignored pycache','N':len(files),'aggregate_sha256':aggregate,'files':files},indent=2)+'\n').encode())
print(json.dumps({'evidence_file_N':len(files),'aggregate_sha256':aggregate,'manifest_sha256':hashlib.sha256(manifest.read_bytes()).hexdigest()}))
