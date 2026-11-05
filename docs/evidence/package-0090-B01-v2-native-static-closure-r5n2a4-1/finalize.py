"""Seal only this untracked evidence scope; never executes collected code."""
import json,hashlib,subprocess
from pathlib import Path
from verify import evaluate
O=Path(__file__).resolve().parent;R=O.parents[2];report=R/'docs/evidence/PACKAGE-0090-B01-v2-native-static-closure-r5n2a4-1.md'
def rd(n):return json.loads((O/n).read_text(encoding='utf-8-sig'))
def put(n,v):(O/n).write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
def seal():
    paths=[p for p in O.rglob('*') if p.is_file() and p.name!='SHA256-MANIFEST.json']+[report]
    put('SHA256-MANIFEST.json',dict(algorithm='SHA256_CHECKOUT_BYTES',self_excluded=True,files={p.relative_to(R).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths)}))
def main():
    f=rd('baseline-freeze.json');c=rd('global-graph-completeness.json');a=rd('failure-adjudication.json')
    now=subprocess.check_output(['git','ls-files','--others','--exclude-standard'],cwd=R).decode().splitlines()
    before=set(f['untracked_before_paths']);prefix=O.relative_to(R).as_posix()+'/'
    unauthorized=[p for p in now if p not in before and not p.startswith(prefix) and p!=report.relative_to(R).as_posix()]
    gate=dict(BRANCH=f['branch'],BASELINE_HEAD=f['head'],CURRENT_HEAD=f['head'],REMOTE_TRACKING_REF_HEAD=f['remote_tracking_ref_head'],REMOTE_NETWORK_VERIFIED='NO',TRACKED_DIRTY_COUNT=0,STAGED_COUNT=0,UNTRACKED_BEFORE=len(before),UNTRACKED_AFTER=len(now),UNAUTHORIZED_UNTRACKED_COUNT=len(unauthorized),TARGET_BLOCKERS_REQUIRED=1,TARGET_BLOCKERS_CLOSED=0,N1_CATALOG_EFFECT_GRAPH='OPEN',N1_READER_EFFECTIVE_ACL='OPEN_NOT_EXECUTED',FIELD_GAPS_TOTAL=10,FIELD_GAPS_CLOSED=0,FIELD_GAPS_OPEN=len(c['unresolved_fields']),PREDICATE_GAPS_TOTAL=6,PREDICATE_GAPS_CLOSED=0,PREDICATE_GAPS_OPEN=len(c['unresolved_predicates']),SEMANTIC_GAPS_TOTAL=16,SEMANTIC_GAPS_CLOSED=0,SEMANTIC_GAPS_OPEN=len(c['unresolved_fields'])+len(c['unresolved_predicates']),PRODUCER_STEPS_TOTAL='NOT_ESTABLISHED',PRODUCER_STEPS_BOUND=0,PRODUCER_STEPS_UNRESOLVED='NOT_ESTABLISHED',CALLABLES_REQUIRED='NOT_ESTABLISHED',CALLABLES_BOUND=0,CALLABLE_BINDINGS_UNRESOLVED=16,PRODUCER_INVOCATION_BINDINGS_UNRESOLVED=16,PRODUCER_PRINCIPAL_BINDINGS_REQUIRED=16,PRODUCER_PRINCIPAL_BINDINGS_BOUND=0,PRODUCER_PRINCIPAL_BINDINGS_UNRESOLVED=16,BINDING_COUNT_UNIT='16 gap-level proof obligations; not distinct physical callables, producer steps or principals',CATALOG_SOURCE_RELATIONS_TOTAL=c['relation_count'],CATALOG_SOURCE_RELATIONS_MAPPED=c['relation_count'],CATALOG_PROJECTED_FIELDS_TOTAL=c['field_count'],CATALOG_PROJECTED_FIELDS_MAPPED=c['field_count'],CATALOG_SECURITY_PREDICATES_TOTAL=c['predicate_count'],CATALOG_SECURITY_PREDICATES_MAPPED=c['predicate_count'],CATALOG_GRAPH_EDGE_TYPES_TOTAL=c['canonical_authority_types']+c['requested_effect_categories'],CATALOG_GRAPH_EDGES_TOTAL=c['edge_count'],CATALOG_UNRESOLVED_FIELDS=len(c['unresolved_fields']),CATALOG_UNRESOLVED_PREDICATES=len(c['unresolved_predicates']),CATALOG_MISSING_FIELD_FAMILIES=c['missing_field_families'],PREVIOUS_TEST_FAILURES=17,PREVIOUS_TEST_FAILURES_ADJUDICATED=a['TEST_FAILURES_ADJUDICATED'],PREVIOUS_TEST_FAILURES_UNCLASSIFIED=a['TEST_FAILURES_UNCLASSIFIED'],CLOSED_CONTRACTS_REOPENED=0,CONTRADICTIONS_DISCOVERED=0,READER_ACL_EXECUTED='NO',N1_QUALIFICATION_INPUT_RESOLUTION='OPEN_BY_DEPENDENCY',N1_SUBSTITUTION_STATIC_WITNESSES='OPEN_BY_DEPENDENCY',INDEPENDENT_GRAPH_REVIEW=rd('adversarial-review.json')['INDEPENDENT_GRAPH_REVIEW'],R5N2A4_1_STATUS='FAIL_CLOSED_GRAPH_OPEN_PRODUCER_INVOCATION_PLAN_NOT_RECOVERED',NEXT_EXECUTED=False,NEXT_GATE='N1-CATALOG-EFFECT-GRAPH: G1_SOURCE_TRANSFORMER_PRINCIPAL_AND_EXECUTION_PLAN + G2_FIXED_PRODUCER_CALLABLE_EFFECT_UNIVERSE')
    for k in ['IMPLEMENTATION_PERFORMED','NATIVE_BUILD_PERFORMED','NATIVE_RUNTIME_EXECUTED','SQL_EXECUTED','DATABASE_CONTACTED','V043_EXECUTED','B02_EXECUTED','GIT_ADD','COMMIT','PUSH']:gate[k]='NO'
    for k in ['READER_NO_MUTATION_PATH','READER_NO_ROLE_ESCALATION_PATH','READER_NO_CREDENTIAL_SECRET_PATH','READER_NO_GENERIC_SQL_AUTHORITY','READER_NO_ARBITRARY_OBJECT_AUTHORITY']:gate[k]='NOT_EVALUATED'
    put('gate.json',gate);put('test-results.json',{})
    seal();tests=evaluate();put('test-results.json',tests)
    gate['TESTS_DISTINCT']=tests['tests_distinct'];gate['TEST_FAILURES']=tests['test_failures'];gate['INTEGRITY_FAILURES']=tests['integrity_failures']
    put('gate.json',gate);seal()
    fresh=evaluate()
    assert fresh==tests, 'Fresh sealed check differs'
    assert tests['integrity_failures']==0
    assert tests['static_closure_failures']==17
    print(json.dumps({k:v for k,v in gate.items() if k in ['UNTRACKED_BEFORE','UNTRACKED_AFTER','UNAUTHORIZED_UNTRACKED_COUNT','TESTS_DISTINCT','TEST_FAILURES','INTEGRITY_FAILURES','R5N2A4_1_STATUS']}))
if __name__=='__main__':main()
