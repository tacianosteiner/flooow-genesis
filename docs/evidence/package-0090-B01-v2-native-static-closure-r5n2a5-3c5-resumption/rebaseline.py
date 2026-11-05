"""Authorized C5 resumption preflight. Parallel files are hashed, never semantic inputs."""
import hashlib,json,subprocess
from pathlib import Path
O=Path(__file__).resolve().parent;R=O.parents[2];E=O.parent;P='package-0090-B01-v2-native-static-closure-'
HEAD='cbc284f62d9bd09b7169b55c8d66a3c51a68c6cb'
PARALLEL=['docs/post-mvp/FLOOOW-REA-X-ECONOMIC-EPISTEMIC-CONTROL-PLANE.md','docs/post-mvp/README.md']
def rd(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def git(*a):return subprocess.check_output(['git',*a],cwd=R).decode().strip()
def put(n,v):(O/n).write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def main():
    prior=E/(P+'r5n2a5-3c4b');stop=E/(P+'r5n2a5-3c5');pb=rd(prior/'baseline-freeze.json');ps=rd(prior/'scope-receipt.json');ss=rd(stop/'scope-receipt.json')
    original=set(pb['untracked_before_paths'])|set(ps['new_paths']);stopped=set(ss['new_gate_owned_paths']);assert len(original)==578 and len(stopped)==7
    before=[p for p in git('ls-files','--others','--exclude-standard').splitlines() if not p.startswith(O.relative_to(R).as_posix()+'/') and p!='docs/evidence/PACKAGE-0090-B01-v2-native-static-closure-r5n2a5-3c5-resumption.md']
    expected=original|set(PARALLEL)|stopped
    assert set(before)==expected and len(before)==587,dict(extra=sorted(set(before)-expected),missing=sorted(expected-set(before)))
    assert git('branch','--show-current')=='checkpoint/package-0090-cloud-handoff' and git('rev-parse','HEAD')==HEAD
    assert subprocess.run(['git','merge-base','--is-ancestor',HEAD,'HEAD'],cwd=R).returncode==0
    assert not git('diff','--name-only') and not git('diff','--cached','--name-only')
    original_hashes=pb['source_sha256'].copy()
    for p,h in rd(prior/'SHA256-MANIFEST.json')['files'].items():original_hashes[p]=h
    original_hashes[(prior/'SHA256-MANIFEST.json').relative_to(R).as_posix()]=sha(prior/'SHA256-MANIFEST.json')
    for p,h in original_hashes.items():assert sha(R/p)==h,p
    for p,h in rd(stop/'SHA256-MANIFEST.json')['files'].items():assert sha(R/p)==h,p
    # Hash-only reads of parallel artifacts are integrity observations, never authority/content analysis.
    hashes={p:sha(R/p) for p in sorted(set(git('ls-files').splitlines()+before))}
    pg=rd(prior/'gate.json');assert pg['OBJECT']=='INHERITED_CREDENTIAL_STATE' and pg['OBJECT_RESOLVED']=='YES' and pg['OBJECT_AGGREGATION_BY_FIAT']=='FORBIDDEN'
    assert pg['I13_PRESERVED_IN_FULL']=='YES' and pg['I13_INTERNAL_FAMILY_MEMBER']=='NO'
    assert pg['ATOMIC_NORMATIVE_CANDIDATES_TOTAL']==108 and pg['AMBIGUOUS_CANDIDATES_PRESERVED']==105
    assert pg['THREE_DIMENSION_DECOMPOSITION_VALIDATED']=='NO' and pg['CANONICAL_INTERNAL_OBLIGATION_UNIVERSE_ESTABLISHED']=='NO' and pg['CANONICAL_INTERNAL_OBLIGATIONS_TOTAL']=='NOT_ESTABLISHED'
    assert pg['N1_DECISIONS_CLOSED']==11 and pg['N1_DECISIONS_OPEN']==1 and pg['V2_NATIVE_STATUS']=='BLOCKED'
    v043={p:h for p,h in original_hashes.items() if Path(p).name.startswith('V043')}
    assert v043,'Expected V043 files in frozen set'
    put('parallel-authorization.json',dict(source='Explicit user resumption instruction in this conversation after C5 preflight STOP',authorized_paths=PARALLEL,classification='AUTHORIZED_PARALLEL_POST_MVP_RESEARCH_ONLY',part_of_C5_semantic_scope=False,Package0090_implementation=False,semantic_authority_for_C5=False,MVP_authority=False,implementation_authority=False,may_be_modified_by_C5=False,content_used_as_decision_authority=False,integrity_hashes={p:hashes[p] for p in PARALLEL}))
    put('resumption-baseline.json',dict(branch=git('branch','--show-current'),head=HEAD,untracked_before_paths=sorted(before),source_sha256=hashes,UNTRACKED_BEFORE=587,original_Package0090_source_sha256=original_hashes,original_C5_STOP_paths=sorted(stopped),authorized_parallel_paths=PARALLEL,parallel_files_are_not_semantic_sources=True))
    put('resumption-preflight.json',dict(STATUS='PASS_CURRENT_STATE_REBASELINE',BRANCH=git('branch','--show-current'),BASELINE_HEAD=HEAD,CURRENT_HEAD=git('rev-parse','HEAD'),FROZEN_BASELINE_ANCESTRY_VALID=True,TRACKED_DIRTY_COUNT=0,STAGED_COUNT=0,UNTRACKED_BEFORE=587,UNAUTHORIZED_UNTRACKED_COUNT=0,accounting=dict(original_authorized=578,authorized_parallel=2,preserved_C5_STOP=7,total=587),unexplained_delta=[],missing_paths=[],original_frozen_files_hash_verified=len(original_hashes),all_current_preexisting_files_hash_recorded=len(hashes),V043_UNTOUCHED=True,V043_verified_hashes=v043,STOP_manifest_verified=True,historical_STOP_files_preserved=True,PARALLEL_CONTENT_USED_AS_AUTHORITY=False,PARALLEL_FILES_MODIFIED=False,C5_SOURCE_SET_CHANGED=False,O8_CHANGED=False,ANTI_AGGREGATION_CHANGED=False,I13_CHANGED=False,DECOMPOSITION_VALIDATED=False,CANDIDATE_108_105_CHANGED=False,INTERNAL_UNIVERSE_ESTABLISHED=False,DENOMINATOR_ESTABLISHED=False,N1_CHANGED=False,TRANSITION_RESOLVED_BY_REBASELINE=False,DOWNSTREAM_DECISIONS_RESOLVED=False,EXECUTION_BOUNDARY='Tool history: only filesystem/git read checks and static evidence Python; no project build/native runtime/SQL/database execution by C5',INDEPENDENT_PREFLIGHT_REVIEW='PENDING',semantic_resumption_authorized_only_after_independent_pass=True))
    print(json.dumps(dict(preflight='PASS',untracked_before=587,explained_delta='578+2+7',frozen_original_files=len(original_hashes),current_files=len(hashes),V043_paths=len(v043),semantic_authority_of_parallel=False)))
if __name__=='__main__':main()
