"""Preserve rejected primary evidence before correcting witness/evaluator artifacts."""
import hashlib,json,shutil
from pathlib import Path
O=Path(__file__).resolve().parent;R=O.parents[2];ARCHIVE=O/'primary-rejected';REPORT=R/'docs/evidence/PACKAGE-0090-B01-v2-native-static-closure-r5n2a5-3.md'
def main():
    if (ARCHIVE/'archive-manifest.json').exists():return
    ARCHIVE.mkdir(exist_ok=True)
    files=[p for p in O.iterdir() if p.is_file() and p.name not in ['preserve_primary.py']]+[REPORT]
    hashes={}
    for p in files:
        target=ARCHIVE/p.name;shutil.copyfile(p,target);hashes[target.relative_to(R).as_posix()]=hashlib.sha256(target.read_bytes()).hexdigest()
    record=dict(status='PRIMARY_HYPOTHESIS_REJECTED_BY_INDEPENDENT_FALSIFICATION_NOT_CANONICAL_RESULTS',files=hashes,reason='Incomplete source/effect mapping, aggregate tuples, unsupported POSTMASTER inheritance substitution, and underconstrained schema/equality evaluator.350rejected/133valid/217materialized claims are withdrawn pending correction.',runtime_evidence=False)
    (ARCHIVE/'archive-manifest.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
if __name__=='__main__':main()
