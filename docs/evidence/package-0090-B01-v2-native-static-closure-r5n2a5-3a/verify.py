"""Read-only verification of this provenance gate; not an attack evaluator."""
import hashlib,json,subprocess
from pathlib import Path
O=Path(__file__).resolve().parent;R=O.parents[2]
def rd(n):return json.loads((O/n).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def git(*a):return subprocess.check_output(['git',*a],cwd=R).decode().strip()
def main():
    b=rd('baseline-freeze.json');g=rd('gate.json');m=rd('SHA256-MANIFEST.json');scope=rd('scope-receipt.json')
    assert git('branch','--show-current')==g['BRANCH'] and git('rev-parse','HEAD')==g['CURRENT_HEAD']==g['BASELINE_HEAD']
    assert not git('diff','--name-only') and not git('diff','--cached','--name-only')
    for p,h in b['source_sha256'].items():assert sha(R/p)==h,p
    for p,h in m['files'].items():assert sha(R/p)==h,p
    current=set(git('ls-files','--others','--exclude-standard').splitlines());before=set(b['untracked_before_paths'])
    assert len(before)==401 and len(current)==g['UNTRACKED_AFTER'] and before<=current
    assert current-before==set(scope['new_paths']) and not scope['unauthorized']
    matrix=rd('object-transition-matrix.json');assert len(matrix['cells'])==7*21 and matrix['canonically_valid_pairs']==0
    assert g['SELECTED_OUTCOME']=='C' and g['INAPPLICABILITY_PROVEN']=='NO' and g['CANONICAL_PAIR_VALID']=='NOT_ESTABLISHED'
    assert g['N1_SUBSTITUTION_STATIC_WITNESSES']=='OPEN' and g['V2_NATIVE_STATUS']=='BLOCKED'
    a=rd('attack-accounting.json');assert len(a['ids'])==len(set(a['ids']))==350 and a['EVALUATOR_CHECKS']==398
    assert a['MATERIALIZED_ATTACKS']==a['ATTACK_REJECTED_AS_DESIGNED']==a['ATTACK_ACCEPTED_DESIGN_FAILURE']==0
    assert all(g[k]=='PASS' for k in ['INDEPENDENT_PROVENANCE_REVIEW','INDEPENDENT_SEMANTIC_REVIEW','INDEPENDENT_ACCOUNTING_REVIEW'])
    inv=rd('search-inventory.json');assert len(inv['terms'])==32 and len(inv['files'])==len(b['source_sha256'])
    print(json.dumps(dict(PROVENANCE_GATE_INTEGRITY='PASS',frozen_files_verified=len(b['source_sha256']),matrix_cells=147,denominator=350,evaluator_checks_distinct=398,outcome='C',tracked_dirty=0,staged=0,untracked_after=len(current))))
if __name__=='__main__':main()
