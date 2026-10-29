"""Offline publication packaging only, after actual independent reviews exist.

Does not install an executor, mutate SQL/native state, or grant authority. It
binds reviewed design bytes, mirrors FAIL results and hashes the evidence set.
"""
import sys
sys.dont_write_bytecode=True
import hashlib
import json
from pathlib import Path
import derive as d


def read(name):
    return json.loads((d.OUT/name).read_text(encoding='utf-8-sig'))


gate=read('STATIC-GATE.json');tests=read('tests.json')
reviews=[]
for name,key in [('least-privilege-review-v3.json','LEAST_PRIVILEGE_REVIEW'),('static-adversarial-review-v3.json','STATIC_ADVERSARIAL_REVIEW')]:
    review=read(name)
    assert review['independent_review'] is True
    assert review['result']=='FAIL'  # This packager cannot manufacture PASS.
    for p,expected in review['reviewed_files_sha256'].items():
        assert hashlib.sha256((d.ROOT/p).read_bytes()).hexdigest()==expected,p
    assert review['BLOCKER_COUNT']==gate['BLOCKER_COUNT']==4
    assert review['HIGH_COUNT']==gate['HIGH_COUNT']==0
    gate[key]=review['result'];reviews.append(review)
assert gate['STATIC_GATE']=='BLOCKED_SOURCE_GAP'
assert gate['NATIVE_STATIC_SOURCE_GAP']==reviews[0]['NATIVE_STATIC_SOURCE_GAP']
assert not gate['PRIVILEGED_IMPLEMENTATION_AUTHORITY_GRANTED']
tests['independent_review_assertions_distinct']=reviews[0]['STATIC_ASSERTIONS_DISTINCT']
tests['independent_review_assertion_failures']=reviews[0]['STATIC_ASSERTION_FAILURES']
tests['independent_review_dimensions']=len(reviews[0]['review_dimensions'])
tests['independent_adversarial_categories_reviewed']=reviews[1]['attacks_reviewed']
tests['independent_assertions_or_repeats_added_to_TESTS_DISTINCT']=False
tests['full_design_finalization_byte_reproducible']=True
d.save('STATIC-GATE.json',gate);d.save('tests.json',tests)
report=d.ROOT/'docs/evidence/PACKAGE-0090-B01-v2-static-closure-revision-3.md'
files=sorted([p for p in d.OUT.iterdir() if p.is_file() and p.name!='SHA256-MANIFEST.json']+[report])
manifest={'algorithm':'SHA256','byte_rule':'Exact bytes except report Git LF normalization',
    'report_git_lf_path':report.relative_to(d.ROOT).as_posix(),'self_excluded':True,'files':{}}
for p in files:
    b=p.read_bytes()
    if p==report:b=b.replace(b'\r\n',b'\n')
    manifest['files'][p.relative_to(d.ROOT).as_posix()]=hashlib.sha256(b).hexdigest()
d.save('SHA256-MANIFEST.json',manifest)
print(json.dumps({'packaged_files':len(files),'STATIC_GATE':gate['STATIC_GATE'],
    'reviews':[r['result'] for r in reviews],'tests_distinct':tests['TESTS_DISTINCT']}))
