"""Read-only receipt verifier. No SQL, imports of experiment code, or network."""
import hashlib,json,subprocess
from pathlib import Path
O=Path(__file__).resolve().parent;R=O.parents[2]
def rd(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def git(*a):return subprocess.check_output(['git',*a],cwd=R).decode().strip()
def main():
    g=rd(O/'gate.json');baseline=rd(O/'baseline-freeze.json');manifest=rd(O/'SHA256-MANIFEST.json')
    assert git('rev-parse','HEAD')==g['CURRENT_HEAD']==g['BASELINE_HEAD']
    assert git('branch','--show-current')==g['BRANCH']
    assert not git('diff','--name-only') and not git('diff','--cached','--name-only')
    for p,h in baseline['source_sha256'].items():assert sha(R/p)==h,p
    for p,h in manifest['files'].items():assert sha(R/p)==h,p
    current=set(git('ls-files','--others','--exclude-standard').splitlines());before=set(baseline['untracked_before_paths'])
    scope=rd(O/'scope-receipt.json');assert len(current)==g['UNTRACKED_AFTER'] and before<=current
    assert current-before==set(scope['all_gate_created_or_modified_untracked_paths'])
    ledger=rd(O/'attack-evaluation-ledger.json')['cases']
    assert len(ledger)==len({c['attack_case_id'] for c in ledger})==350
    assert sum(c['structured_input'] for c in ledger)==133
    assert all(c['classification']=='UNRESOLVED_CANONICAL_GAP' and not c['evaluation_executed'] for c in ledger)
    assert g['CONFIRMED_MISSING_CANONICAL_WITNESS_COUNT']==1 and g['UNVALIDATED_REMAINING_AFTER_STOP']==349
    assert g['N1_SUBSTITUTION_STATIC_WITNESSES']=='OPEN' and g['V2_NATIVE_STATUS']=='BLOCKED'
    roots=rd(O/'root-cause-recomputation.json');assert len(roots['roots'])==3
    assert sum(r['closed'] for r in roots['roots'])==roots['closed']==g['NATIVE_ROOT_CAUSES_CLOSED']==1
    assert sum(not r['closed'] for r in roots['roots'])==roots['open']==g['NATIVE_ROOT_CAUSES_OPEN']==2
    assert g['CANONICAL_VALID_ATTACKS_EVALUATED']==g['ATTACK_REJECTED_AS_DESIGNED']==g['ATTACK_ACCEPTED_DESIGN_FAILURE']==0
    assert rd(O/'correction-check-results.json')['failures']==0
    print(json.dumps(dict(STOP_RECEIPT_INTEGRITY='PASS',canonical_cases=350,confirmed_witness_gap=1,remaining_unvalidated=349,untracked_after=len(current),tracked_dirty=0,staged=0)))
if __name__=='__main__':main()
