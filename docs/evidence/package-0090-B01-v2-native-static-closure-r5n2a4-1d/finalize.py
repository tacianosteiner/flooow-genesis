"""Design-only validation and sealing. Does not run predecessor graph closure suite."""
import ast,hashlib,json,subprocess
from pathlib import Path
O=Path(__file__).resolve().parent;R=O.parents[2];REPORT=R/'docs/evidence/PACKAGE-0090-B01-v2-native-static-closure-r5n2a4-1d.md'
def rd(n):return json.loads((O/n).read_text(encoding='utf-8-sig'))
def put(n,v):(O/n).write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def git(*a):return subprocess.check_output(['git',*a],cwd=R).decode().strip()
def validate():
    checks=[]
    def ck(n,v):checks.append(dict(name=n,passed=bool(v)))
    f=rd('baseline-freeze.json');steps=rd('G1-producer-execution-plan.json')['steps'];calls=rd('G2-callable-effect-universe.json')['callables'];mapping=rd('16-gap-design-resolution.json')['mapping'];cap=rd('source-capability-contract.json')
    ck('branch',git('branch','--show-current')==f['branch']);ck('HEAD',git('rev-parse','HEAD')==f['head']);ck('tracking_ref',git('rev-parse','origin/checkpoint/package-0090-cloud-handoff')==f['remote_tracking_ref_head']);ck('tracked_clean',not git('diff','--name-only'));ck('staged_empty',not git('diff','--cached','--name-only'))
    for p,h in f['source_sha256'].items():ck('preserved:'+p,(R/p).is_file() and sha(R/p)==h)
    before=set(f['untracked_before_paths']);now=set(git('ls-files','--others','--exclude-standard').splitlines());prefix=O.relative_to(R).as_posix()+'/'
    ck('old228_preserved',len(before)==228 and before<=now);ck('scope_only',all(p in before or p.startswith(prefix) or p==REPORT.relative_to(R).as_posix() for p in now))
    ck('eight_unique_steps',len(steps)==len({s['PRODUCER_STEP_ID'] for s in steps})==8);ck('eight_unique_fixed_callables',len(calls)==len({c['CALLABLE_ID'] for c in calls})==8 and all(c['FIXED_OR_DYNAMIC']=='FIXED' for c in calls))
    stepkeys={'PRODUCER_STEP_ID','PLAN_ID','PLAN_VERSION','STEP_ORDER','STEP_PURPOSE','SOURCE_RELATION_SET','SOURCE_FIELD_SET','TRANSFORMER_ID','TRANSFORMER_TYPE','CALLER_PRINCIPAL','SESSION_PRINCIPAL','EFFECTIVE_PRINCIPAL','AUTHORITY_SOURCE','AUTHORITY_SCOPE','AUTHENTICATION_CONTEXT','INPUT_CREDENTIAL_CLASS','SECRET_MATERIAL_REQUIRED','SECURITY_PREDICATES_EVALUATED','TRANSFORMATION_SET','OUTPUT_FIELD_SET','OUTPUT_CONTRACT','MUTATION_ALLOWED','ROLE_ESCALATION_ALLOWED','GENERIC_SQL_ALLOWED','ARBITRARY_OBJECT_SELECTION_ALLOWED','SECRET_ACCESS_ALLOWED','FAIL_CLOSED_BEHAVIOR','UNKNOWN_BEHAVIOR','FUTURE_IMPLEMENTATION_BOUNDARY'}
    callkeys={'CALLABLE_ID','CALLABLE_TYPE','PRODUCER_STEP_ID','FIXED_OR_DYNAMIC','OBJECT_SELECTION_MODE','QUERY_SURFACE_MODE','INPUT_SCHEMA','OUTPUT_SCHEMA','SOURCE_RELATIONS','SOURCE_FIELDS','PREDICATES_EVALUATED','TRANSFORMATIONS_PERFORMED','CALLER_PRINCIPAL','EFFECTIVE_PRINCIPAL','AUTHORITY_SOURCE','EXECUTE_AUTHORITY','MUTATION_CAPABILITY','ROLE_ESCALATION_CAPABILITY','GENERIC_SQL_CAPABILITY','ARBITRARY_OBJECT_CAPABILITY','SECRET_ACCESS_CAPABILITY','PARAMETER_CLASSES','IDENTIFIER_PARAMETERS_ALLOWED','SQL_TEXT_PARAMETERS_ALLOWED','OBJECT_NAME_PARAMETERS_ALLOWED','FAIL_CLOSED_CONDITIONS','FUTURE_PHYSICAL_IMPLEMENTATION_OPTIONS','STATIC_ACCEPTANCE_CRITERIA'}
    for s,c in zip(steps,calls):
        sid=s['PRODUCER_STEP_ID'];ck('step_fields:'+sid,stepkeys<=s.keys());ck('call_fields:'+sid,callkeys<=c.keys());ck('binding:'+sid,c['PRODUCER_STEP_ID']==sid and c['CALLABLE_ID']==s['TRANSFORMER_ID'])
        ck('step_no_authority_widening:'+sid,all(s[k] is False for k in ['SECRET_MATERIAL_REQUIRED','MUTATION_ALLOWED','ROLE_ESCALATION_ALLOWED','GENERIC_SQL_ALLOWED','ARBITRARY_OBJECT_SELECTION_ALLOWED','SECRET_ACCESS_ALLOWED']))
        ck('call_no_authority_widening:'+sid,all(c[k] is False for k in ['MUTATION_CAPABILITY','ROLE_ESCALATION_CAPABILITY','GENERIC_SQL_CAPABILITY','ARBITRARY_OBJECT_CAPABILITY','SECRET_ACCESS_CAPABILITY','IDENTIFIER_PARAMETERS_ALLOWED','SQL_TEXT_PARAMETERS_ALLOWED','OBJECT_NAME_PARAMETERS_ALLOWED']))
    ck('stats_four_source_fields',{p.rsplit('.',1)[1] for p in steps[1]['SOURCE_FIELD_SET']}=={'datid','pid','usesysid','usename'})
    ck('stats_six_slots_separate_bridge',len(steps[1]['OUTPUT_FIELD_SET'])==6 and steps[2]['EFFECTIVE_PRINCIPAL']=='EXISTING_AUTHENTICATED_LOGIN_BRIDGE_SELF_SESSION')
    ck('config_all_conjuncts',all(p in steps[6]['TRANSFORMATION_SET'][0] for p in ['EXACT_APPROVED_PROCONFIG','QUALIFIED_STATIC_DEPENDENCIES_ONLY','NO_UNAPPROVED_SD_OR_OWNER_PATH']))
    ck('config_manifest_explicit',bool(steps[6]['INPUT_AUTHENTICATED_MANIFESTS']))
    ck('pure_no_source',all(not steps[i]['TRANSFORM_REQUIRES_SOURCE_AUTHORITY'] and steps[i]['SESSION_PRINCIPAL']=='NONE_NO_DATABASE_SESSION' and steps[i]['INPUT_CREDENTIAL_CLASS']=='NONE' for i in [5,6,7]))
    ck('source_membrane_no_SQL_magic','ordinary INVOKER SQL' in cap['implementation_constraint'] and cap['security_definer_required'] is False)
    ck('transport_custody_and_PUBLIC_audit',bool(cap['session_transport_confinement']) and 'PUBLIC' in cap['transport_acceptance'])
    ck('19_relations',len(rd('fixed-surface-proof.json')['closed_relation_set'])==19);ck('146_fields',len(set(rd('fixed-surface-proof.json')['closed_field_set']))==146);ck('26_predicates',len(set(rd('fixed-surface-proof.json')['predicate_ids']))==26)
    ck('10_field_design_paths',sum(bool(m['FIELD_ID']) and m['DESIGN_RESOLUTION_AVAILABLE'] for m in mapping)==10);ck('6_predicate_design_paths',sum(bool(m['PREDICATE_ID']) and m['DESIGN_RESOLUTION_AVAILABLE'] for m in mapping)==6)
    ck('unique_resolution_16',len(mapping)==len({m['GAP_ID'] for m in mapping})==16 and all(m['GAP_STATUS']=='OPEN_NOT_BOUND' for m in mapping))
    ck('design_path_ids',all(m['DESIGN_CALLABLE_ID'] in {c['CALLABLE_ID'] for c in calls} and m['DESIGN_PRODUCER_STEP_ID'] in {s['PRODUCER_STEP_ID'] for s in steps} for m in mapping))
    threats=rd('adversarial-threat-model.json');ck('19_threats',len(threats['threats'])==19);ck('no_open_design_threats',threats['BLOCKER_THREATS_OPEN']==0)
    review=rd('independent-design-review.json');ck('independent_review_PASS',review.get('INDEPENDENT_DESIGN_REVIEW')=='PASS')
    for p,h in review.get('source_sha256',{}).items():ck('reviewed_hash:'+p,sha(R/p)==h)
    for p in O.glob('*.py'):ast.parse(p.read_text());ck('syntax:'+p.name,True)
    manifest=rd('SHA256-MANIFEST.json')
    for p,h in manifest['files'].items():ck('sealed:'+p,sha(R/p)==h)
    actual={p.relative_to(R).as_posix() for p in O.rglob('*') if p.is_file() and p.name!='SHA256-MANIFEST.json'}|{REPORT.relative_to(R).as_posix()}
    ck('manifest_exact',set(manifest['files'])==actual);ck('names_distinct',len(checks)==len({c['name'] for c in checks}))
    return dict(scope='DESIGN_CONTRACT_VALIDATION_ONLY_NOT_GRAPH_CLOSURE',checks_distinct=len(checks),failures=sum(not c['passed'] for c in checks),checks=checks,predecessor_graph_closure_suite_executed=False,previous_test_failures=17,test_failures_expected_to_remain=17)
def seal():
    files=[p for p in O.rglob('*') if p.is_file() and p.name!='SHA256-MANIFEST.json']+[REPORT]
    put('SHA256-MANIFEST.json',dict(algorithm='SHA256_CHECKOUT_BYTES',self_excluded=True,files={p.relative_to(R).as_posix():sha(p) for p in sorted(files)}))
def main():
    f=rd('baseline-freeze.json');steps=rd('G1-producer-execution-plan.json')['steps'];calls=rd('G2-callable-effect-universe.json')['callables'];m=rd('16-gap-design-resolution.json')['mapping']
    for n in ['gate.json','design-validation.json']:
        if not (O/n).exists():put(n,{})
    if not (O/'SHA256-MANIFEST.json').exists():put('SHA256-MANIFEST.json',{})
    now=git('ls-files','--others','--exclude-standard').splitlines();before=set(f['untracked_before_paths']);prefix=O.relative_to(R).as_posix()+'/'
    gate=dict(BRANCH=f['branch'],BASELINE_HEAD=f['head'],CURRENT_HEAD=git('rev-parse','HEAD'),REMOTE_TRACKING_REF_HEAD=git('rev-parse','origin/checkpoint/package-0090-cloud-handoff'),REMOTE_NETWORK_VERIFIED='NO',TRACKED_DIRTY_COUNT=len(git('diff','--name-only').splitlines()),STAGED_COUNT=len(git('diff','--cached','--name-only').splitlines()),UNTRACKED_BEFORE=len(before),UNTRACKED_AFTER=len(now),UNAUTHORIZED_UNTRACKED_COUNT=sum(p not in before and not p.startswith(prefix) and p!=REPORT.relative_to(R).as_posix() for p in now),DESIGN_TARGETS_REQUIRED=2,G1_SOURCE_TRANSFORMER_PRINCIPAL_AND_EXECUTION_PLAN='APPROVED_DESIGN',G2_FIXED_PRODUCER_CALLABLE_EFFECT_UNIVERSE='APPROVED_DESIGN',PRODUCER_STEPS_TOTAL=len(steps),CALLABLES_TOTAL=len(calls),CALLABLES_FIXED_SURFACE=sum(c['FIXED_OR_DYNAMIC']=='FIXED' for c in calls),CALLABLES_DYNAMIC_SURFACE=sum(c['FIXED_OR_DYNAMIC']=='DYNAMIC' for c in calls),FIELD_GAPS_TOTAL=10,FIELD_GAPS_WITH_DESIGN_RESOLUTION=sum(bool(v['FIELD_ID']) and v['DESIGN_RESOLUTION_AVAILABLE'] for v in m),PREDICATE_GAPS_TOTAL=6,PREDICATE_GAPS_WITH_DESIGN_RESOLUTION=sum(bool(v['PREDICATE_ID']) and v['DESIGN_RESOLUTION_AVAILABLE'] for v in m),SEMANTIC_GAPS_TOTAL=16,SEMANTIC_GAPS_OPEN=16,BLOCKER_THREATS_OPEN=rd('adversarial-threat-model.json')['BLOCKER_THREATS_OPEN'],DESIGN_AUTHORITY_MODEL_SELECTED='D_EXISTING_AUTHENTICATED_LOGIN_BRIDGE_PLUS_FIXED_ACQUISITION_SURFACE',DESIGN_AUTHORITY_MODELS_REJECTED=['A','B','C_AS_STANDALONE','E_AS_INCOMPLETE'],CLOSED_CONTRACTS_REOPENED=0,CONTRADICTIONS_DISCOVERED=0,PREVIOUS_TEST_FAILURES=17,TEST_FAILURES_EXPECTED_TO_REMAIN=17,N1_CATALOG_EFFECT_GRAPH='OPEN_PENDING_DESIGN_BINDING',N1_READER_EFFECTIVE_ACL='OPEN_NOT_EXECUTED',INDEPENDENT_DESIGN_REVIEW=rd('independent-design-review.json')['INDEPENDENT_DESIGN_REVIEW'],R5N2A4_1D_STATUS='DESIGN_APPROVED_GRAPH_OPEN_PENDING_BINDING',NEXT_EXECUTED=False,NEXT_GATE='R5N.2A4.1B_BIND_APPROVED_PRODUCER_PLAN_TO_16_SEMANTIC_GAPS')
    for k in ['GENERIC_SQL_ALLOWED','SQL_TEXT_PARAMETERS_ALLOWED','ARBITRARY_OBJECT_SELECTION_ALLOWED','OBJECT_NAME_PARAMETERS_ALLOWED','SUPERUSER_REQUIRED','BYPASSRLS_REQUIRED','PG_READ_ALL_STATS_REQUIRED','SECURITY_DEFINER_REQUIRED','IMPLEMENTATION_PERFORMED','NATIVE_BUILD_PERFORMED','NATIVE_RUNTIME_EXECUTED','SQL_EXECUTED','DATABASE_CONTACTED','V043_EXECUTED','B02_EXECUTED','READER_ACL_EXECUTED','GIT_ADD','COMMIT','PUSH']:gate[k]='NO'
    seal();v=validate()
    if v['failures'] or gate['INDEPENDENT_DESIGN_REVIEW']!='PASS':
        gate.update(G1_SOURCE_TRANSFORMER_PRINCIPAL_AND_EXECUTION_PLAN='REJECTED',G2_FIXED_PRODUCER_CALLABLE_EFFECT_UNIVERSE='REJECTED',R5N2A4_1D_STATUS='FAIL_CLOSED_DESIGN_REJECTED',NEXT_GATE='RESOLVE_DESIGN_VALIDATION_OR_INDEPENDENT_REVIEW_FINDINGS')
    gate['DESIGN_VALIDATION_CHECKS']=v['checks_distinct'];gate['DESIGN_VALIDATION_FAILURES']=v['failures'];put('gate.json',gate);put('design-validation.json',v);seal()
    fresh=validate();assert fresh==v,'Fresh sealed verification differs'
    print(json.dumps({k:gate[k] for k in ['UNTRACKED_BEFORE','UNTRACKED_AFTER','UNAUTHORIZED_UNTRACKED_COUNT','DESIGN_VALIDATION_CHECKS','DESIGN_VALIDATION_FAILURES','INDEPENDENT_DESIGN_REVIEW','R5N2A4_1D_STATUS']}))
if __name__=='__main__':main()
