"""Read-only evidence verification, no attack evaluation."""
import collections,hashlib,json,subprocess
from pathlib import Path
O=Path(__file__).resolve().parent;R=O.parents[2]
def rd(n):return json.loads((O/n).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def git(*a):return subprocess.check_output(['git',*a],cwd=R).decode().strip()
def main():
    b=rd('baseline-freeze.json');g=rd('gate.json');m=rd('intent-matrix.json');t=rd('threat-intent-matrix.json');c=rd('architectural-consistency.json')
    assert git('branch','--show-current')==g['BRANCH'] and git('rev-parse','HEAD')==g['CURRENT_HEAD']==g['BASELINE_HEAD']
    assert not git('diff','--name-only') and not git('diff','--cached','--name-only')
    for p,h in b['source_sha256'].items():assert sha(R/p)==h,p
    for p,h in rd('SHA256-MANIFEST.json')['files'].items():assert sha(R/p)==h,p
    paths=set(git('ls-files','--others','--exclude-standard').splitlines());before=set(b['untracked_before_paths']);scope=rd('scope-receipt.json')
    assert len(before)==421 and len(paths)==g['UNTRACKED_AFTER'] and before<=paths and paths-before==set(scope['new_paths']) and not scope['unauthorized_paths']
    assert len(m['candidates'])==len({x['INTENT_ID'] for x in m['candidates']})==19
    assert dict(collections.Counter(x['CANONICAL_SUPPORT'] for x in m['candidates']))==m['counts']
    assert len(t['threats'])==len(c['candidates'])==19
    for row in t['threats']:
        for field in ['ATTACKER_OR_ACTOR','SOURCE_OBJECT_OR_SUBJECT','TARGET_OBJECT_OR_SUBJECT','ATTEMPTED_TRANSITION']:assert row[field]=='NOT_CANONICALLY_DETERMINED'
    assert g['SELECTED_OUTCOME']=='C' and g['UNIQUE_INTENT']==g['COMPOSITE_INTENT']=='NOT_ESTABLISHED'
    assert g['ATTACKS_MATERIALIZED_THIS_GATE']==g['ATTACKS_EVALUATED_THIS_GATE']==0
    assert g['CANONICAL_ATTACK_DENOMINATOR']==350 and g['EVALUATOR_CHECKS_PREVIOUS']==398
    assert g['N1_SUBSTITUTION_STATIC_WITNESSES']=='OPEN' and g['V2_NATIVE_STATUS']=='BLOCKED' and g['ROOT_CAUSE_RECOMPUTATION_PERFORMED']=='NO'
    for k in ['INDEPENDENT_INTENT_REVIEW','INDEPENDENT_CONSISTENCY_REVIEW','INDEPENDENT_SCOPE_REVIEW']:assert g[k]=='PASS'
    for k in ['CASE_SPECIFIC_OBJECT_CREATED','CASE_SPECIFIC_TRANSITION_CREATED','OBJECT_TRANSITION_BINDING_CREATED','POSTMASTER_CONTEXT_BINDING_CREATED']:assert g[k]=='NO'
    print(json.dumps(dict(INTENT_GATE_INTEGRITY='PASS',frozen_files=len(b['source_sha256']),intent_candidates=19,threats=19,consistency_rows=19,outcome='C',attacks_evaluated=0,tracked_dirty=0,staged=0,untracked_after=len(paths))))
if __name__=='__main__':main()
