"""Read-only fail-closed diagnostic validation; never proves or executes a witness."""
import collections,hashlib,json,pathlib
P=pathlib.Path(__file__).resolve().parent;ROOT=P.parents[2]
def read(n):return json.loads((P/(n+'.json')).read_text(encoding='utf-8'))
def original(g,n):return json.loads((P.parent/('package-0090-B01-v2-native-static-closure-'+g)/(n+'.json')).read_text(encoding='utf-8'))
def run():
    pre=read('preflight');assert pre['status']=='PASS' and len(pre['exact_blocker_ids'])==3 and pre['exhausted_17_mapping_preserved']
    resolution=read('source-admission-artifact-resolution');assert resolution['ALLOWED_STATUS'] is None and not resolution['ALLOWED_STATUS_SELECTION_COMPLETE']
    assert resolution['requirements_well_specified'] and resolution['FACTUAL_STATE']=='ABSENT_NOT_ESTABLISHED_UNDER_EXISTING_FROZEN_AUTHORITY'
    assert len(resolution['status_tests'])==6 and all(not x['predicate_established'] for x in resolution['status_tests'])
    proof=read('artifact-authenticity-proof');assert proof['ARTIFACT_ID'] is None and proof['ARTIFACT_HASH'] is None and not proof['self_authentication_performed'] and proof['AUTHENTICITY_RESULT']=='NOT_ESTABLISHED_NO_ARTIFACT_ASSERTED'
    pnote=original('r5n2a5-3c5p','canonical-rule-analysis')['source_admission_note'];assert 'acceptance rules/schemas are frozen' in pnote
    for kind in ['binding','composition']:
        branch=read('canonical-'+kind+'-rule-analysis');assert branch['AUTHORITY_ALLOWED_STATUS'] is None and not branch['EXACT_RULE_AUTHORITY_ESTABLISHED'] and not branch['MATERIALIZATION_PERMITTED'] and not branch['MATERIALIZED']
        assert branch['META_ACCEPTANCE_CONSTRAINT_STATUS']=='RULE_ALREADY_ENTAILED' and branch['EXACT_RULE_FACTUAL_STATE']=='EXACT_CARRIER_OR_ADAPTER_DERIVATION_NOT_ESTABLISHED'
        assert not (P/('canonical-'+kind+'-rule.json')).exists()
    assert not read('binding-recomputation')['performed'] and not read('binding-recomputation')['trigger_satisfied']
    cert=read('all-49-recertification');assert not cert['performed'] and cert['required']==49 and cert['strict_certified']==39 and cert['not_certified']==10 and cert['algorithm_disproven']==0
    current=read('composition-recomputation');old=original('r5n2a5-3c5o','composition-recomputation')
    assert len(current['edges'])==714 and [(e['EDGE_ID'],e['STATUS']) for e in current['edges']]==[(e['EDGE_ID'],e['STATUS']) for e in old['edges']]
    assert collections.Counter(e['STATUS'] for e in current['edges'])=={'COMPLETE':294,'MISSING':420}
    assert len({e['EDGE_ID'] for e in current['edges']})==714 and all(e['C5Q_NEW_EDGE_PROOF'] is False and e['C5Q_EVIDENCE_BASIS'] and e['C5Q_PROVENANCE'] for e in current['edges'])
    order={node:i for i,node in enumerate(current['topological_order'])};assert len(order)==763
    for e in current['edges']:assert order[e['SOURCE_FUNCTION']]<order[e['TARGET_FUNCTION']]
    dag=read('canonical-dag-recomputation');assert [dag[k] for k in ['CANONICAL_DECISION_NODES','CANONICAL_DECISION_EDGES','UNBOUND_DECISION_INPUTS','UNBOUND_DECISION_OUTPUTS','AMBIGUOUS_DECISION_RELATIONS','CYCLES_DETECTED']]==[763,714,210,350,84,0]
    assert read('canonical-evaluator-analysis')['complete']==0 and not read('canonical-evaluator-analysis')['assembly_attempted']
    residual=read('residual-blocker-recomputation');assert residual['BLOCKERS_RESOLVED']==0 and residual['BLOCKERS_REMAINING']==residual['RESIDUAL_MINIMUM_BLOCKER_FRONTIER_TOTAL']==3 and residual['NEW_BLOCKERS_DISCOVERED']==0
    assert {b['BLOCKER_ID'] for b in residual['residual']}==set(pre['exact_blocker_ids'])
    failure=read('gate-classification-coverage-failure');assert not failure['domain_contradiction'] and not failure['historical_C5P_contradicted'] and not failure['original_frontier_incomplete']
    outcome=read('outcome-eligibility-analysis');assert len(outcome['tests'])==10 and [r['outcome'] for r in outcome['tests'] if r['eligible']]==['I']
    coverage=read('coverage-accounting')['preserved'];assert [coverage[k] for k in ['STATICALLY_PROVEN','STATICALLY_DISPROVEN','UNKNOWN','CONTRADICTED']]==[0,0,350,0]
    summary=read('final-summary');assert summary['SELECTED_OUTCOME']=='I_CONTRADICTION_OR_FRONTIER_FAILURE' and summary['NEXT_GATE']=='STOP_FAIL_CLOSED' and summary['NEXT_EXECUTED'] is False
    assert [summary[k] for k in ['LOCAL_FUNCTIONS_STRICT_CERTIFIED','CANONICAL_INPUT_BINDINGS_COMPLETE','CANONICAL_OUTPUT_BINDINGS_COMPLETE','COMPOSITION_EDGES_COMPLETE']]==[39,1316,280,294]
    handoff=read('minimum-gate-contract-repair-handoff');assert not handoff['applied'] and not handoff['automatic_next_gate_authorized']
    return dict(status='PASS_FAIL_CLOSED_DIAGNOSTIC',preflight='PASS',source_artifact_authenticated=False,exact_rules_materialized=0,original_blockers_resolved=0,original_blockers_preserved=3,new_domain_blockers=0,edges_audited=714,old_edge_state_drift=0,topological_nodes=763,cycles=0,full_binding_recomputation=False,witness_executions=0,domain_contradiction=False,gate_status_coverage='FAIL',selected_stop='I',scope='Evidence integrity and truthful stop; not successful blocker resolution')
if __name__=='__main__':print(json.dumps(run()))
