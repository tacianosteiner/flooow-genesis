"""Independent repair/phase sequencing and preserved-state consistency audit."""
import hashlib,importlib.util,itertools,json,pathlib,sys
sys.dont_write_bytecode=True
P=pathlib.Path(__file__).resolve().parent;ROOT=P.parents[2]
def read(n):return json.loads((P/(n+'.json')).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def pinpath(n):return ROOT/n if n.replace('\\','/').startswith('docs/') else P/n
s=importlib.util.spec_from_file_location('r_validate_classifier',P/'repair_contract.py');rc=importlib.util.module_from_spec(s);s.loader.exec_module(rc)
def run():
    pre=read('preflight');assert pre['status']=='PASS' and len(pre['historical_sha256'])==9588
    assert read('repair-handoff-interpretation')['HANDOFF_INTERPRETATION_COMPLETE']=='YES' and not read('repair-handoff-interpretation')['NONDOMINATED_ALTERNATIVES']
    contract=read('minimum-contract-repair');assert contract['ABSENT_STATUS']=='ABSENT_NOT_ESTABLISHED_UNDER_EXISTING_AUTHORITY' and not contract['PREEXISTING_SEMANTICS_CHANGED'] and len(contract['ARTIFACT_STATE_FIELDS'])==7
    assert not any(contract[k] for k in ['CREATION_IMPLIES_AUTHORITY','CREATION_IMPLIES_AUTHENTICATION','CREATION_IMPLIES_ADMISSION'])
    tests=read('repair-six-state-tests');assert tests['REPAIR_TESTS_PASSING']==6 and tests['REPAIR_TESTS_FAILING']==0 and tests['validation_revision']==2 and all(x['passed'] for x in tests['additional_controls'])
    actual=rc.six_state_tests();assert len(actual)==6 and all(x['PASS'] for x in actual) and len({x['ACTUAL_STATUS'] for x in actual})==6
    # All2187 state valuations, three bookkeeping origins: only allsevenYES
    # with independent proofs and no inconsistent escalation flags may close.
    trials=0
    for values in itertools.product(('YES','NO','NOT_ESTABLISHED'),repeat=7):
        state=dict(zip(rc.FIELDS,values))
        for origin in [None,'PRE_EXISTING','DETERMINISTIC_ASSEMBLY']:
            facts=dict(independent_authentication_proved=True,independent_admission_proved=True,origin=origin,all_assembly_inputs_established=True)
            assert rc.closure_eligible(state,facts)==all(v=='YES' for v in values);trials+=1
    for flag in ['frozen_authority_contradiction_proved','new_normative_authority_required_proved','inherently_observational_runtime_required_proved','requirement_underspecified_proved']:
        assert not rc.closure_eligible({k:'YES' for k in rc.FIELDS},dict(independent_authentication_proved=True,independent_admission_proved=True,**{flag:True}))
    receipt=read('phase2-resumption-authorization');assert receipt['PHASE1_REVIEW_1']==receipt['PHASE1_REVIEW_2']=='PASS' and receipt['phase2_begins_only_after_checks']
    for i in [1,2]:
        r=read('phase1-independent-review-'+str(i));assert r['status']=='PASS' and r['PHASE1_REVIEW_'+str(i)]=='PASS'
        for n,h in r['reviewed_sha256'].items():assert sha(pinpath(n))==h
        reference=receipt['reviews'][i-1];assert sha(ROOT/reference['path'])==reference['sha256']
    assert receipt['classifier_sha256']==sha(P/'repair_contract.py')
    assert sha(ROOT/receipt['phase1_tests']['path'])==receipt['phase1_tests']['sha256']
    archive=read('superseded-draft-v1/archive-record')
    for original,record in archive['files'].items():assert sha(ROOT/record['archived_path'])==record['sha256']
    assert not read('phase1-correction')['accepted_normative_predicate_changed'] and read('phase1-correction')['actual_domain_closures']==0
    state=read('source-admission-reevaluation');assert all(state[k]=='YES' for k in rc.FIELDS[:4]) and state['ARTIFACT_EXISTS']=='NO' and state['ARTIFACT_AUTHENTICATED']==state['ARTIFACT_ADMITTED']=='NOT_ESTABLISHED'
    assert state['ARTIFACT_STATUS']==rc.ABSENT and rc.classify({k:state[k] for k in rc.FIELDS},{})==rc.ABSENT and not state['closure_eligible'] and not state['source_blocker_closed']
    construction=read('artifact-construction-analysis');assert not construction['ALL_CONSTRUCTION_PREREQUISITES_ESTABLISHED'] and not construction['CONSTRUCTION_PERFORMED'] and construction['ACTUAL_ARTIFACT_ID'] is None and len(construction['REQUIRED_INPUTS'])==4
    assert all(not x['ESTABLISHED'] and x['WHY_MISSING'] for x in construction['REQUIRED_INPUTS'])
    assert read('artifact-authenticity-analysis')['ARTIFACT_AUTHENTICATED']=='NOT_ESTABLISHED' and not read('artifact-authenticity-analysis')['ACTUAL_AUTHENTICATION_ATTEMPTED']
    assert read('artifact-admission-analysis')['ARTIFACT_ADMITTED']=='NOT_ESTABLISHED' and not read('artifact-admission-analysis')['ACTUAL_ADMISSION_ATTEMPTED']
    for kind in ['binding','composition']:
        rule=read(kind+'-rule-analysis');assert rule['RULE_AUTHORITY_STATUS'] is None and rule['EXACT_RULE_DERIVATION_STATE']=='NOT_ESTABLISHED' and not rule['RULE_MATERIALIZED'] and not rule['INVENTED_RULE']
    for name in ['binding-recomputation-if-applicable','all-49-recertification-if-applicable','composition-recomputation-if-applicable','canonical-dag-if-applicable']:assert not read(name)['performed']
    assert read('canonical-evaluator-analysis')['COMPLETE_CANONICAL_DECISION_EVALUATORS']==0 and not read('canonical-evaluator-analysis')['assembly_attempted']
    residual=read('residual-frontier');assert [residual[k] for k in ['ORIGINAL_BLOCKERS','BLOCKERS_RESOLVED','BLOCKERS_REMAINING','NEW_BLOCKERS_DISCOVERED','RESIDUAL_MINIMUM_BLOCKER_FRONTIER_TOTAL']]==[3,0,3,0,3]
    assert {b['BLOCKER_ID'] for b in residual['blockers']}==set(pre['exact_blocker_ids'])
    eligibility=read('outcome-eligibility');assert len(eligibility['tests'])==13 and [x['outcome'] for x in eligibility['tests'] if x['eligible']]==['D']
    summary=read('final-summary');assert summary['SELECTED_OUTCOME']=='D_CONTRACT_REPAIRED_ARTIFACT_CONSTRUCTION_INPUT_MISSING' and summary['NEXT_GATE']=='BOUNDED_AUTHENTICATED_ARTIFACT_INPUT_CLOSURE' and summary['NEXT_EXECUTED'] is False
    assert [summary[k] for k in ['LOCAL_FUNCTIONS_STRICT_CERTIFIED','CANONICAL_INPUT_BINDINGS_COMPLETE','CANONICAL_OUTPUT_BINDINGS_COMPLETE','COMPOSITION_EDGES_COMPLETE','COMPLETE_CANONICAL_DECISION_EVALUATORS','STATICALLY_PROVEN','STATICALLY_DISPROVEN','UNKNOWN','CONTRADICTED']]==[39,1316,280,294,0,0,0,350,0]
    return dict(status='PASS',phase1_tests='6/6',tri_state_origin_neutrality_trials=trials,phase1_review_pins_and_resumption_receipt='PASS',superseded_draft_preserved=True,normative_semantics_changed=False,actual_artifact_constructed=False,actual_authentication_or_admission=False,original_blockers_resolved=0,original_blockers_remaining=3,actual_binding_changes=0,witness_executions=0,outcome='D')
if __name__=='__main__':print(json.dumps(run()))
