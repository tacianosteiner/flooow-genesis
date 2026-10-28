"""Offline integrity verification, safe before and after evidence-only commit."""
import hashlib
import json
from pathlib import Path
import subprocess
import zlib

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT)


def load(name):
    return json.loads((OUT / name).read_text(encoding='utf-8'))


def sha(b):
    return hashlib.sha256(b).hexdigest()


freeze = load('baseline-freeze.json')
integrity = load('source-integrity.json')
gate = load('STATIC-GATE.json')
assert git('branch', '--show-current').decode().strip() == freeze['branch']
assert subprocess.run(['git','merge-base','--is-ancestor',freeze['baseline_head'],'HEAD'],cwd=ROOT).returncode == 0
for path, expected in integrity['input_git_hashes'].items():
    current = git('show', 'HEAD:' + path)
    assert sha(current) == expected, path
    assert sha((ROOT/path).read_bytes().replace(b'\r\n',b'\n')) == sha(current.replace(b'\r\n',b'\n')), path
for path, expected in integrity['migrations'].items():
    current = git('show', 'HEAD:' + path)
    assert sha(current) == expected, path
    assert (ROOT/path).read_bytes().replace(b'\r\n',b'\n') == current.replace(b'\r\n',b'\n'), path
    if Path(path).name.startswith('V043__'):
        crc = zlib.crc32(''.join(current.decode('utf-8-sig').splitlines()).encode())
        assert (crc if crc < 2**31 else crc-2**32) == 1279591798
        assert current.index(b"RAISE EXCEPTION USING ERRCODE = '55000'") < current.index(b'SET LOCAL search_path')
for ref, expected in integrity['protected_refs'].items():
    p = subprocess.run(['git','rev-parse','--verify',ref],cwd=ROOT,capture_output=True)
    actual = p.stdout.decode().strip() if p.returncode == 0 else 'REF_ABSENT_AT_BASELINE'
    assert actual == expected, ref
assert gate['STATIC_GATE'] == 'BLOCKED'
assert gate['CURRENTNESS_MUTATION_CLASSES_PROVEN'] == 0
assert gate['CURRENTNESS_MUTATION_CLASSES_UNPROVEN'] == 46
assert gate['COMPLETE_CURRENTNESS_GATE'] == 'FAIL_NOT_RERUN'
assert gate['B02_CURRENTNESS_INTEGRATION_GATE'] == 'NOT_RERUN'
assert gate['NEXT_EXECUTED'] is False
assert gate['RAW_AUTHORITY_SURFACE'] == 'NOT_PROVEN'
assert gate['UNCLASSIFIED_MUTATION_EDGES'] is None
assert gate['UNMEDIATED_ACTIVE_MUTATION_EDGES'] is None
assert gate['MANIFEST_COMPATIBILITY_DECISION'] == 'C. B01_FIXTURE_MUST_CHANGE'
assert gate['BLOCKER_COUNT'] == len(load('findings.json')['blockers']) == 4
assert load('tests.json')['test_failures'] == 0
assert gate['TESTS_DISTINCT'] == load('tests.json')['tests_distinct']
catalog = load('typed-capability-catalog-v2.json')
ids = {c['CAPABILITY_ID'] for c in catalog['capabilities']}
assert len(ids) == catalog['partial_contracts_total'] == 243
for name, key in [('fixed-operation-templates.json','templates'), ('capability-principal-bindings.json','bindings'), ('capability-outcome-bindings.json','bindings')]:
    rows=load(name)[key]
    assert {r['CAPABILITY_ID'] for r in rows} == ids
    assert len(rows) == len(ids)
model=load('closed-epoch-state-machine.json')
required=load('closed-epoch-reseal-invariants.json')['required']
assert len(required)==7
assert [t['from'] for t in model['transitions'] if t['to']=='SEALED_NEW_EPOCH']==['RESEAL_PENDING']
assert set(next(t['precondition'] for t in model['transitions'] if t['to']=='SEALED_NEW_EPOCH'))==set(required)
for name in ['least-privilege-review-v2-r2.json','static-adversarial-review-v2-r2.json']:
    review=load(name)
    assert review['result'] in ['FAIL','BLOCKED']
    for path, expected in review['reviewed_files_sha256'].items():
        assert sha((ROOT/path).read_bytes())==expected, path
manifest=load('SHA256-MANIFEST.json')
assert manifest['self_excluded'] is True
for path, expected in manifest['files'].items():
    payload=(ROOT/path).read_bytes()
    if path==manifest['report_git_lf_path']:
        payload=payload.replace(b'\r\n',b'\n')
    assert sha(payload)==expected, path
actual_files={p.relative_to(ROOT).as_posix() for p in OUT.iterdir() if p.is_file() and p.name!='SHA256-MANIFEST.json'}
actual_files.add('docs/evidence/PACKAGE-0090-B01-v2-static-closure-revision-2.md')
assert actual_files==set(manifest['files'])
allowed=[OUT.relative_to(ROOT).as_posix()+'/', 'docs/evidence/PACKAGE-0090-B01-v2-static-closure-revision-2.md']
for path in git('diff','--name-only',freeze['baseline_head'],'HEAD').decode().splitlines():
    assert any(path.startswith(a) if a.endswith('/') else path==a for a in allowed), path
print(json.dumps({'verified':True,'STATIC_GATE':gate['STATIC_GATE'],'contracts_partial':len(ids),
    'source_files':len(integrity['input_git_hashes']), 'migrations':len(integrity['migrations']),
    'evidence_files_hashed':len(manifest['files']), 'model_tests_distinct':gate['TESTS_DISTINCT'],
    'failures':0,'canonical_unchanged':True}))
