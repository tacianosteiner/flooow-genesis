"""Independent offline R3 integrity/reproducibility checks; no runtime imports.

Run with -B. Sources are Git bytes at the exact baseline; the report alone is
LF-normalized so Windows checkout settings cannot change its content identity.
"""
import sys
sys.dont_write_bytecode=True
import hashlib
import json
from pathlib import Path
import subprocess
import zlib
import derive as d

OUT=d.OUT
ROOT=d.ROOT


def read(name):
    return json.loads((OUT/name).read_text(encoding='utf-8-sig'))


def git(*args):
    return subprocess.check_output(['git',*args],cwd=ROOT)


def sha(b):
    return hashlib.sha256(b).hexdigest()


freeze=read('baseline-freeze.json');gate=read('STATIC-GATE.json');tests=read('tests.json')
assert git('branch','--show-current').decode().strip()==freeze['branch']==d.BRANCH
assert subprocess.run(['git','merge-base','--is-ancestor',d.BASE,'HEAD'],cwd=ROOT).returncode==0
assert freeze['baseline_head']==d.BASE and freeze['origin_head_after_fetch']==d.BASE
assert freeze['worktree_clean_before_evidence'] and freeze['staged_changes_before_evidence']==0
baseline=d.tree();now={}
for row in git('ls-tree','-r','-z','HEAD').split(b'\0'):
    if row:
        meta,path=row.split(b'\t',1);now[path.decode()]=meta.decode().split()[2]
for p in freeze['input_git_sha256']:
    assert now.get(p)==baseline[p],p
oids=list(dict.fromkeys(baseline[p] for p in freeze['input_git_sha256']))
data=subprocess.check_output(['git','cat-file','--batch'],input=('\n'.join(oids)+'\n').encode(),cwd=ROOT)
hashes={};raw={};pos=0
for oid in oids:
    end=data.index(b'\n',pos);hdr=data[pos:end].decode().split();size=int(hdr[2]);pos=end+1
    assert hdr[0]==oid and hdr[1]=='blob'
    hashes[oid]=sha(data[pos:pos+size]);raw[oid]=data[pos:pos+size];pos+=size+1
for p,expected in freeze['input_git_sha256'].items():
    assert hashes[baseline[p]]==expected,p
    assert (ROOT/p).read_bytes().replace(b'\r\n',b'\n')==raw[baseline[p]].replace(b'\r\n',b'\n'),p
v=raw[baseline[d.V043]];assert sha(v)==d.VHASH
crc=zlib.crc32(''.join(v.decode('utf-8-sig').splitlines()).encode());crc=crc if crc<2**31 else crc-2**32
assert crc==1279591798
assert v.index(b"RAISE EXCEPTION USING ERRCODE = '55000'")<v.index(b'SET LOCAL search_path')
for ref,expected in freeze['protected_refs'].items():
    r=subprocess.run(['git','rev-parse','--verify',ref],cwd=ROOT,capture_output=True)
    actual=r.stdout.decode().strip() if r.returncode==0 else 'REF_ABSENT_AT_BASELINE'
    assert actual==expected,ref
allowed_prefix=OUT.relative_to(ROOT).as_posix()+'/'
report='docs/evidence/PACKAGE-0090-B01-v2-static-closure-revision-3.md'
for p in git('diff','--name-only',d.BASE,'HEAD').decode().splitlines():
    assert p.startswith(allowed_prefix) or p==report,p
for line in git('status','--porcelain','--untracked-files=all').decode().splitlines():
    p=line[3:].replace('\\','/')
    assert p.startswith(allowed_prefix) or p==report,p

# Reproduce every normalized per-target/per-operation record without storing
# hundreds of thousands of duplicated source objects in the repository.
count=0;nulls=0;digest=hashlib.sha256();ids=set()
for record in d.expand_mechanisms():
    assert record['MECHANISM_ID'] not in ids
    ids.add(record['MECHANISM_ID']);count+=1
    nulls+=record['PHYSICAL_TARGET'] is None
    assert record['REPRESENTATIVE_ALLOWED']=='NO' and record['STATIC_STATUS']=='NOT_PROVEN'
    digest.update(d.canon(record)+b'\n')
md=read('mechanism-denominator.json')
assert count==md['enumerated_form_obligations']
assert nulls==md['enumerated_form_obligations_with_null_target']
assert digest.hexdigest()==md['expanded_records_sha256']
assert md['MECHANISMS_TOTAL'] is None and md['capability_derivation_allowed'] is False
assert len(read('class-mechanism-partitions-v3.json')['classes'])==46
assert read('typed-capability-catalog-v3.json')['required_typed_capabilities'] is None
assert gate['STATIC_GATE']=='BLOCKED_SOURCE_GAP'
assert gate['CURRENTNESS_MUTATION_CLASSES_PROVEN']==0
assert gate['CURRENTNESS_MUTATION_CLASSES_UNPROVEN']==46
assert gate['B02_CURRENTNESS_INTEGRATION_GATE']=='NOT_RERUN'
assert gate['COMPLETE_CURRENTNESS_GATE']=='FAIL_NOT_RERUN' and not gate['NEXT_EXECUTED']
assert gate['TESTS_DISTINCT']==tests['TESTS_DISTINCT'] and tests['TEST_FAILURES']==gate['TEST_FAILURES']==0
assert all(c['passed'] for c in tests['checks'])
assert len(read('findings.json')['blockers'])==gate['BLOCKER_COUNT']==4
native=read('native-source-investigation.json')
assert gate['NATIVE_STATIC_SOURCE_GAP']==native['NATIVE_STATIC_SOURCE_GAP']
assert native['NATIVE_PARTICIPANTS_FULLY_BOUND']==0
assert gate['FIXTURE_CORRECTION_PLAN_COMPLETE'].startswith('NOT_PROVEN')
assert gate['RAW_AUTHORITY_SURFACES'] is None
for file,field in [('least-privilege-review-v3.json','LEAST_PRIVILEGE_REVIEW'),('static-adversarial-review-v3.json','STATIC_ADVERSARIAL_REVIEW')]:
    r=read(file)
    assert r['result']=='FAIL' and gate[field]=='FAIL'
    assert r['independent_review'] is True
    for p,expected in r['reviewed_files_sha256'].items():
        assert sha((ROOT/p).read_bytes())==expected,p
    for p,expected in r['inspected_source_git_sha256'].items():
        assert freeze['input_git_sha256'][p]==expected,p
    assert r['all_frozen_source_hash_verification']['input_count']==freeze['input_count']
    assert r['all_frozen_source_hash_verification']['hash_map_artifact_sha256']==sha((OUT/'baseline-freeze.json').read_bytes())
    assert r['STATIC_ASSERTION_FAILURES']==0
manifest=read('SHA256-MANIFEST.json')
assert manifest['self_excluded'] is True
actual_files={p.relative_to(ROOT).as_posix() for p in OUT.iterdir() if p.is_file() and p.name!='SHA256-MANIFEST.json'}|{report}
assert actual_files==set(manifest['files'])
for p,expected in manifest['files'].items():
    b=(ROOT/p).read_bytes()
    if p==report:b=b.replace(b'\r\n',b'\n')
    assert sha(b)==expected,p
print(json.dumps({'verified':True,'STATIC_GATE':gate['STATIC_GATE'],'frozen_inputs':len(freeze['input_git_sha256']),
    'classes':46,'normalized_expansion_records':count,'known_null_target_obligations':nulls,
    'tests_distinct':tests['TESTS_DISTINCT'],'test_failures':0,'evidence_files_hashed':len(manifest['files']),
    'V043_fence':True,'canonical_and_R2_unchanged':True,'runtime_executed':False}))
