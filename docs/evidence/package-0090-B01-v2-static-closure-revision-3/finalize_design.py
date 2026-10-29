"""Finish static-only R3 design after source investigation, before independent review."""
import sys
sys.dont_write_bytecode=True
import collections
import hashlib
import itertools
import json
import subprocess
from pathlib import Path
import derive as d

OUT=d.OUT


def read(name):
    return json.loads((OUT/name).read_text(encoding='utf-8-sig'))


def freeze_native_inputs():
    freeze=read('baseline-freeze.json');native=read('native-source-investigation.json')
    additions={p:h for p,h in native['source_git_lf_sha256'].items() if p not in freeze['input_git_sha256']}
    oids=list(dict.fromkeys(d.tree()[p] for p in additions))
    data=subprocess.check_output(['git','cat-file','--batch'],input=('\n'.join(oids)+'\n').encode(),cwd=d.ROOT)
    pos=0;hashes={}
    for oid in oids:
        end=data.index(b'\n',pos);head=data[pos:end].decode().split();size=int(head[2]);pos=end+1
        assert head[0]==oid
        hashes[oid]=d.sha(data[pos:pos+size]);pos+=size+1
    for p,h in native['source_git_lf_sha256'].items():
        assert h==(freeze['input_git_sha256'].get(p) or hashes[d.tree()[p]]),p
        freeze['input_git_sha256'][p]=h
    freeze['input_git_sha256']=dict(sorted(freeze['input_git_sha256'].items()))
    freeze['input_count']=len(freeze['input_git_sha256'])
    initial=set(d.initial_input_paths())
    freeze['initial_input_count']=len(initial)
    freeze['native_snapshot_additions']=len(set(native['source_git_lf_sha256'])-initial)
    d.save('baseline-freeze.json',freeze)


def native_contracts():
    inv=read('native-source-investigation.json');req=d.js(d.SRC+'native-proof-v6.json')['participants']
    result=[]
    for n in inv['independent_source_findings']:
        name=n['PARTICIPANT_ID'];r=next(x for x in req if x['PARTICIPANT_NAME']==name)
        result.append({'PARTICIPANT_ID':name,'EXACT_BINARY_OR_MODULE':None,
            'SOURCE_POINTER':{'investigation':'native-source-investigation.json#/independent_source_findings/'+str(inv['independent_source_findings'].index(n)),
                'existing_candidates':n['existing_source_anchors']},
            'FUNCTION_ENTRYPOINT':None,'FUNCTIONAL_WORK_ANCHOR':None,
            'work_anchor_candidate_meaning':'Existing code anchors are real candidates, not an approved complete B01 participant witness.',
            'PARENT_IDENTITY':None,'DEPENDENCY_SET':None,'CATALOG_OR_REGISTRY_BINDING':None,
            'GENERATION_BINDING':r['GENERATION_BINDING'],'FRESHNESS_SOURCE':r['LIVENESS_SOURCE'],
            'CHALLENGE_BINDING':'Fresh independent original challenge + exact participant slot/epoch/generation/work context required; physical source mapping NOT_PROVEN',
            'FUNCTIONAL_RESULT':r['COMPLETED_WORK_WITNESS'],'INDEPENDENT_OBSERVER':r['INDEPENDENT_OBSERVER'],
            'RESTART_IDENTITY_RULE':r['RESTART_BEHAVIOR'],'REPLACEMENT_IDENTITY_RULE':r['GENERATION_INVALIDATED_WHEN'],
            'FAIL_CLOSED_RULE':r['FAIL_CLOSED_ACTION'],'STATIC_STATUS':'NOT_PROVEN',
            'unmet_bindings':n['unmet_required_bindings'],'closure_classification':n['closure_classification'],
            'minimum_next_design_action':n['minimum_next_design_action']})
    d.save('native-seven-participant-contract-v3.json',{'status':'BLOCKED_SOURCE_GAP','participants':result,
        'NATIVE_PARTICIPANTS_REQUIRED':7,'NATIVE_PARTICIPANTS_FULLY_BOUND':0,'UNRESOLVED_NATIVE_WORK_ANCHORS':7,
        'NATIVE_STATIC_SOURCE_GAP':inv['NATIVE_STATIC_SOURCE_GAP'],'gap_semantics':inv['gap_semantics'],
        'GENERIC_PROCESS_SUBSTITUTIONS':0,'approved_alternates':[],
        'minimum_design_change':inv['minimum_design_change'],'canonical_amendment_required':'NOT_ESTABLISHED',
        'alternate_rule':'DENY unless exact independently approved functional equivalence and no broader authority/supply-chain boundary are proven; no such alternate is adopted in R3'})
    d.save('native-work-anchor-map-v3.json',{'status':'NOT_PROVEN',
        'source_inventory':'native-source-investigation.json',
        'participant_candidate_anchor_references':[{'PARTICIPANT_ID':r['PARTICIPANT_ID'],
            'candidate_anchors':r['SOURCE_POINTER']['existing_candidates'],'approved_B01_anchor':None} for r in result],
        'new_module_design_requirements':[
            {'participant':'APPROVAL_PRODUCER','boundary':'New separate TEST-only producer identity/process, never a signing loop relabelled as original authority',
             'work':'Publish immutable exact original signature/full context/committed digest; independent consumer verifies; per-slot generation/current epoch registry binds publication',
             'authority':'No DB owner/superuser or arbitrary filesystem/command/module inputs; exact original material custody and immutable publication path still require approved design'},
            {'participant':'APPROVAL_CONSUMER','boundary':'New separate TEST-only consumer work/result slot anchored and observed by independent guard',
             'work':'Verify exact immutable original publication, full-context signature and current registry decision; retain verification result/publication digest/epoch/generation/decision revision',
             'authority':'Read-only exact publication/catalog entitlements; no mutation or producer-key custody'},
            {'participant':'ENFORCEMENT_WORKER','boundary':'Separate retained target-anchor worker and independent external outcome guard',
             'work':'Outcome proof requires target anchor and independently observed actual effect; signal ACK is insufficient; unknown retains ownership and reconciliation',
             'authority':'Only separately authorized existing TEST target actions; no arbitrary PID/signal/shell path and no new execution/recovery authority'}],
        'requirements_are_not_approved_modules_or_runtime_implementation':True,
        'what_alternates_do_not_prove':['production participant identity','currentness qualification','100us','S04','READY']})


def session_and_fixture():
    r2=d.js(d.R2+'consumer-session-contract-v2.json')
    d.save('consumer-session-contract-v3.json',{'status':'DESIGNED_NOT_PHYSICALLY_BOUND',
        'database':'g3f4','authenticated_SQL_identity':'test_0090_audit',
        'connection_identity':None,'backend_PID':None,'backend_start_identity':None,
        'deployment_incarnation':'Trusted owned TEST bootstrap identity, never adopted from another session/backup',
        'epoch_generation':'Exact enrolled connection tuple; any mismatch/death/reconnect invalidates old eligibility',
        'parameter_contracts':r2['allowed_settings'],
        'mutation':'Only exact frozen literal typed setting on the original authenticated final-consumer connection handle; no helper cursor/backend substitute',
        'before_after':'Read exact typed setting immediately before and after on SAME handle, server PID/start identity and authenticated identity; bind independent observer receipt to that tuple',
        'observer':None,'observer_entitlement':None,
        'continuity_rule':'Exact same live handle + backend PID/start + session incarnation + session_user + database + deployment + epoch + generation',
        'reconnect_rule':'Old connection revoked/drained, new identity/epoch/generation enrollment only after old UNKNOWN outcome reconciled; never transfer old capability',
        'UNKNOWN_rule':'Durable pending operation survives reconnect/process loss; do not infer successful SET, failed SET or rollback; independent reconciliation required',
        'durable_pending_survives_reconnect':True,'new_enrollment_requires_reconciled_prior_outcome':True,
        'isolation_rule':'Transaction isolation change only before first transaction query; otherwise deny, preserving durable UNKNOWN if transport outcome is ambiguous',
        'forbidden':['SET SESSION AUTHORIZATION','SET ROLE to another role','owner/admin membership','helper session equivalence','reconnect erases pending state'],
        'source':d.pointer(d.R2+'consumer-session-contract-v2.json'),
        'binding_gap':'Frozen same-connection experiment establishes possibility on an ordinary historical auditor session. It does not bind the actual future final-consumer observer/driver/session-creation authority.',
        'FINAL_CONSUMER_SESSION_CONTRACT_COMPLETE':'NOT_PROVEN','new_session_opened':False})
    plan=d.js(d.R2+'b01-fixture-correction-plan.json')
    d.save('fixture-correction-revalidation-v3.json',{'status':'PARTIAL_PLAN_REVALIDATED_MODEL_NOT_CLOSED',
        'MANIFEST_COMPATIBILITY_DECISION':'C. B01_FIXTURE_MUST_CHANGE','v6_byte_preserved':True,
        'v6_source':d.pointer(d.SRC+'expected-currentness-manifest-v6.json'),
        'exact_wrapper':'public.offline_read_history(uuid,bytea,uuid,text)',
        'auditor':'test_0090_audit','wrapper_entitlement':'EXECUTE only on exact intended wrapper slot, no additional family grants',
        'raw_history':'public.flyway_schema_history SELECT remains denied for ordinary auditor',
        'zero_incoming_outgoing_ADMIN_owner_memberships':True,'private_control_owner_SET_path':'REMOVE, never substitute inheritance/SECURITY DEFINER or overlay waiver',
        'original_plan':d.pointer(d.R2+'b01-fixture-correction-plan.json'),
        'source_fixture_wrapper_rule':d.lineptr('scripts/validation/package_0090_reachable_v2_privileges.py',"source_acls['public.offline_read_history']['test_0090_audit']"),
        'source_private_owner_path_to_remove':d.lineptr('scripts/validation/package_0090_sealed_boundary.py','GRANT flooow_offline_control_owner TO test_0090_broker'),
        'source_plan_steps_preserved':len(plan['steps']),
        'no_expected_truth_from_observation':True,'canonical_overlay_waivers':False,'production_carryover':'FORBIDDEN',
        'FIXTURE_CORRECTION_PLAN_COMPLETE':'NOT_PROVEN_AGAINST_UNCLOSED_R3_AUTHORITY_MODEL',
        'reason':'Canonical correction intent/source bindings preserved, but complete capability/authority/observer model still absent; do not carry R2 plan-complete YES into stronger R3 revalidation.',
        'corrected_fixture_installed':False})


def authority_graph():
    model=read('class-mechanism-partitions-v3.json')
    proposals=[]
    for c in model['classes']:
        kind=c['CLASS_ID'].split('/')[-1]
        label='TRUST_BOUNDARY_ONLY' if kind in ['native_ELF','native_locale','native_module','provider_ABI','expected_release','role_superuser'] else 'EPOCH_REPLACEMENT_ONLY'
        if kind in ['session_environment','native_binding','audit_binding','policy_readiness_binding']:label='BROKER_MEDIATED_TYPED'
        proposals.append({'CLASS_ID':c['CLASS_ID'],'candidate_label':label,'classification_proven':False,
            'exact_source_target_form_expansion':'class-mechanism-partitions-v3.json',
            'boundary':'HOST_PLATFORM/root/release/deployment authority independent of qualification broker' if label=='TRUST_BOUNDARY_ONLY' else None,
            'boundary_limit':'Host/root/release compromise excluded only if broker cannot invoke arbitrary privileged commands/credentials; no such invocation is waived. Physical custody and independent observation still required.' if label=='TRUST_BOUNDARY_ONLY' else None,
            'complete_actor_and_edge_set':'NOT_PROVEN'})
    d.save('authority-graph-v3.json',{'status':'NOT_PROVEN','mechanism_model':'class-mechanism-partitions-v3.json',
        'class_route_candidates':proposals,'complete_authority_edges':None,
        'rejected_raw_paths':'executor-confinement-v3.json#/rejected_raw_candidate_paths',
        'allowed_edge_classes':['BROKER_MEDIATED_TYPED','CLOSED_EPOCH_TRANSITION_ONLY','EPOCH_REPLACEMENT_ONLY','IMMUTABLE_DURING_SEALED','TRUST_BOUNDARY_ONLY'],
        'AUTHORITY_EDGES_TOTAL':None,'AUTHORITY_EDGES_CLASSIFIED':0,'UNCLASSIFIED_MUTATION_EDGES':None,
        'UNMEDIATED_ACTIVE_MUTATION_EDGES':None,'TRUST_BOUNDARY_ONLY_EDGES':None,'AUTHORITY_GRAPH_COMPLETE':'NOT_PROVEN',
        'classified_count_semantics':'Zero edges certified, not zero reachable edges or raw authority.',
        'trust_boundary_never_hides_broker_invocable_superuser':True})


def checks():
    checks=[]
    def check(name,ok,evidence):
        assert ok,name
        checks.append({'name':name,'passed':bool(ok),'evidence':evidence})
    # Parser adversarial cases are source-analysis checks, not SQL runtime attacks.
    check('SQL_lexer_dollar_body_semicolons',len(list(d.sql_statements("CREATE FUNCTION f() RETURNS void AS $$ BEGIN PERFORM 1; END $$ LANGUAGE plpgsql; GRANT EXECUTE ON FUNCTION f() TO x;")))==2,'dollar-quoted body does not create fake top-level grants')
    check('SQL_lexer_quoted_literal_semicolons',len(list(d.sql_statements("SELECT 'x;''y'; SELECT 2;")))==2,'escaped single quote and embedded semicolon')
    check('SQL_lexer_nested_comments',len(list(d.sql_statements('/* a /* b; */ c */ SELECT 1;')))==1,'nested comments ignored')
    cs=d.js(d.SRC+'mutation-class-denominator-v3.json')['classes'];graph=d.js(d.SRC+'s04-reachability-graph-v3.json')
    expected={n['id'] for n in graph['nodes'] if n['mutable_currentness']}
    assigned=[n for c in cs for n in c['GRAPH_OBJECTS']]
    check('frozen_46_classes_independently_recounted',len(cs)==46,'input source classes, not R2 counts')
    check('all_mutable_graph_objects_once',len(assigned)==len(set(assigned)) and set(assigned)==expected,{'mutable_nodes':len(expected)})
    check('all_source_pointers_resolve',all(d.resolve(d.js(d.SRC+n['component']),n['pointer']) is not None for n in graph['nodes'] if n['mutable_currentness']),'every mutable node independently dereferenced')
    constraints=read('constraint-applicability-v3.json');source=d.js(d.SRC+'constraint-v2.json')['constraints']
    check('constraint_subtypes_recounted',constraints['source_counts']==dict(collections.Counter(c['source']['contype'] for c in source)),constraints['source_counts'])
    check('constraint_all_exact_targets_retained',len(constraints['records'])==len(source)==233 and all(r['PHYSICAL_TARGET']['name'] for r in constraints['records']),'no generic constraint representative')
    deny=[r for r in constraints['records'] if r['drop_restrict_applicability']=='STRUCTURALLY_DENIED_UNDER_FROZEN_PK']
    check('NOTNULL_primary_key_denials_source_bound',len(deny)>0 and all(r['subtype']=='CONSTR_NOTNULL' and r['denial_reasons'] for r in deny),{'denials':len(deny),'source':'tablecmds.c dropconstraint_internal'})
    denyfk=[r for r in constraints['records'] if r['drop_restrict_applicability']=='RESTRICT_DENIED_WITH_FROZEN_EXTERNAL_FK']
    check('key_external_FK_denials_source_bound',len(denyfk)>0 and all(r['external_fk_dependencies'] for r in denyfk),{'denials':len(denyfk)})
    check('validate_excludes_PK_UNIQUE',all(r['validate_applicability']=='NOT_APPLICABLE_PK_UNIQUE' for r in constraints['records'] if r['subtype'] in ['CONSTR_PRIMARY','CONSTR_UNIQUE']),'PG18 exact type guard')
    acl=read('acl-origin-ledger-v3.json')
    check('ACL_six_physical_kinds_recounted',sum(acl['effective_row_kinds'].values())==25466 and len(acl['effective_row_kinds'])==6,'effective values never promoted into direct grant provenance')
    check('raw_canonical_DDL_tables_recounted',acl['canonical_create_table_count']==15,'independent lexical top-level source scan')
    check('ACL_default_global_schema_distinction',acl['schema_scoped_defaults_not_supported_for']==['SCHEMAS','LARGE OBJECTS'],'pinned SetDefaultACL error branches')
    caps=read('typed-capability-catalog-v3.json')
    check('capabilities_not_derived_before_mechanism_closure',caps['required_typed_capabilities'] is None and caps['capabilities']==[] and not read('mechanism-denominator.json')['capability_derivation_allowed'],'empty set is NOT zero required')
    model=read('closed-epoch-state-machine-v3.json');trans=model['transitions'];guards=model['reseal_invariants']
    check('14_state_labels_independently_reproduced',len(model['states'])==14 and model['R2_state_labels_independently_reproduced'],'independent transition table compared with frozen R2 labels')
    incoming=[t for t in trans if t['to']=='SEALED_NEW_EPOCH']
    check('reseal_only_from_pending',len(incoming)==1 and incoming[0]['from']=='RESEAL_PENDING','all generated legal transitions examined')
    vals=[]
    for bits in itertools.product([False,True],repeat=len(guards)):
        values=dict(zip(guards,bits));vals.append(all(values[g] is True for g in incoming[0]['required_known_true']))
    check('all_128_reseal_guard_valuations',len(vals)==128 and sum(vals)==1,'seven conjunctive required independent evidence flags; abstract only')
    unknown=[]
    for g in guards:
        obs=dict.fromkeys(guards,True);obs[g]=None;unknown.append(all(obs[f] is True for f in guards))
    check('each_unknown_reseal_guard_denies',not any(unknown),'seven unknown substitutions')
    check('UNKNOWN_no_direct_reseal',not any(t['from']=='MUTATION_UNKNOWN' and t['to'] in ['RESEAL_PENDING','SEALED_NEW_EPOCH'] for t in trans),'actual generated transition relation')
    identities=read('closed-epoch-physical-bindings-v3.json')['durable_identities']
    hashes={d.sha(d.canon({'domain':'FLOOOW/B01V2/R3','identity_kind':v['identity_kind'],'frozen_tuple':'same-test-tuple'})) for v in identities.values()}
    check('durable_identity_kind_domain_separation',len(hashes)==len(identities)==9 and all(v['identity_kind']==k and v['kind_specific_fields'] for k,v in identities.items()),'distinct typed identity domains; physical custody and attestations still unbound')
    ep=read('endpoint-inventory-v3.json')
    check('concrete_endpoint_source_anchors_exist',len(ep['endpoints'])==21 and len({e['ENDPOINT_ID'] for e in ep['endpoints']})==21 and all(e['SOURCE_POINTER']['anchor'] for e in ep['endpoints']),'21 concrete V1 source handles/records, not an exhaustive R3 inventory')
    n=read('native-source-investigation.json')
    check('seven_native_semantic_roles_preserved',len(n['independent_source_findings'])==7 and n['NATIVE_PARTICIPANTS_REQUIRED']==7,'required semantic roles, no relabelled generic process')
    check('native_source_gap_bounded',n['NATIVE_STATIC_SOURCE_GAP']==['APPROVAL_PRODUCER','APPROVAL_CONSUMER','ENFORCEMENT_WORKER'] and all(r['functional_source_exists'] for r in n['independent_source_findings']),'missing independent witness paths, reusable functional code explicitly exists')
    check('native_full_binding_not_inferred',n['NATIVE_PARTICIPANTS_FULLY_BOUND']==0 and n['GENERIC_PROCESS_SUBSTITUTIONS']==0 and n['UNRESOLVED_NATIVE_WORK_ANCHORS']==7,'new mapping never promotes candidates to proof')
    sess=read('consumer-session-contract-v3.json')
    check('session_reconnect_preserves_UNKNOWN',sess['durable_pending_survives_reconnect'] and sess['new_enrollment_requires_reconciled_prior_outcome'],'explicit durable pending/reconciliation conditions; no helper session equivalence')
    fixture=read('fixture-correction-revalidation-v3.json')
    check('manifest_decision_and_overlay_rules',fixture['MANIFEST_COMPATIBILITY_DECISION']=='C. B01_FIXTURE_MUST_CHANGE' and not fixture['canonical_overlay_waivers'] and not fixture['corrected_fixture_installed'],'source-expectation decision preserved without stronger model-completeness claim')
    check('no_authority_graph_completeness_inference',read('authority-graph-v3.json')['AUTHORITY_EDGES_TOTAL'] is None,'partial routing proposals do not certify edges')
    d.save('tests.json',{'scope':'Offline source/model/consistency assertions; no live qualification or attack execution',
        'TESTS_DISTINCT':len(checks),'TEST_FAILURES':0,'checks':checks,'model_valuations':135,
        'adversarial_runtime_cases':0,'independent_review_cases_counted_as_tests':False,
        'verify_command':'python -B docs/evidence/package-0090-B01-v2-static-closure-revision-3/verify_evidence.py'})


def gate_and_findings():
    n=read('native-source-investigation.json');tests=read('tests.json')
    d.save('findings.json',{'BLOCKER_COUNT':4,'HIGH_COUNT':0,'MEDIUM_COUNT':0,'LOW_COUNT':0,
        'blockers':[
            {'ID':'V2-PARTITIONS','exact_missing_proof':'Complete physical reachability/applicability/actor universe and source-to-effect dependency proof, including ACL grantor/ownership/membership/default paths and semantic external ledgers/session handles',
             'sources_inspected':['mutation-class-denominator-v3.json','s04-reachability-graph-v3.json','canonical V043 top-level DDL/ACL','provider/tablecmds.c','provider/aclchk.c','provider/acl.c','provider/pg_constraint.c'],
             'why_insufficient':'46 classes and operation-form obligations are reconstructed; 422 enumerated obligations have unresolved physical targets, applicability is conditional, ACL effective values merge distinct origins. No representative proof justifies a complete denominator.',
             'minimum_next_action':'Freeze the exact qualification actor/environment boundary, physical audit/policy/native/session stores and observer reads; finish direct privilege/role-chain/default/schema and dependency closure against that boundary before minimal capability derivation.'},
            {'ID':'V2-TEMPLATES','exact_missing_proof':'Minimal required capability denominator plus immutable dispatcher/executor/credential/target/outcome/observer/revocation confinement',
             'sources_inspected':['scripts/validation/package_0090_sealed_service.py','scripts/validation/package_0090_sealed_boundary.py','R2 catalog/principal/outcome files','prior role-admin-special-case.json'],
             'why_insufficient':'Existing V1 broker holds private owner SET credential; R2 postgres labels lack process confinement; broad CREATEROLE counterexample persists. A literal operation does not narrow the credential. Required capability set is not derived before mechanism closure.',
             'minimum_next_action':'After mechanism closure, design exact immutable fixed-operation workers and private one-operation credential transport, independent observer entitlement and receipt path; no generic psql/superuser broker.'},
            {'ID':'V2-EPOCH','exact_missing_proof':'Exhaustive R3 physical endpoint inventory, independent durable reservation/outcome/audit identities, complete revocation/extinction attestors and receipts for all seven reseal invariants',
             'sources_inspected':['R2 14-state machine and crash/reseal contracts','scripts/validation/package_0090_sealed_service.py','scripts/validation/package_0090_sealed_boundary.py','actual native supervisor/receiver/observer sources'],
             'why_insufficient':'Abstract safety relation reproduced and 21 actual V1 source endpoints identified. Existing broker co-locates mutation credential, outcome query and audit writer; V1 private path is not adopted as R3. Exact independent R3 endpoints remain absent.',
             'minimum_next_action':'Define source-backed separate transition worker, audit/outcome/extinction actors and durable tuple stores; bind every handle/session/descendant/descriptor to revocation and independent proof before reseal.'},
            {'ID':'V2-NATIVE','exact_missing_proof':'Independent exact producer/consumer/enforcement witness paths plus complete B01 binary/parent/dependency/generation/challenge/catalog/observer bindings for all seven roles',
             'sources_inspected':['native-source-investigation.json:1175 source files and 524 embedded source snapshots','scripts/validation/package_0090_s04_native_health.c','scripts/validation/package_0090_native_health_qualification/*','HEALTH-CONTRACT.md'],
             'why_insufficient':'Richer spawn/enrollment/census/signature/enforcement logic exists. Required independent approval producer/consumer and enforcement worker paths are absent in inspected graph; co-location/harness threads and nonce benchmarks cannot substitute. Other four candidates still lack complete B01 work/generation/guard bindings.',
             'minimum_next_action':n['minimum_design_change']}],
        'prior_R2_negative_findings':d.pointer(d.R2+'findings.json'),
        'prior_anonymous_volume_provenance_MEDIUM':'Preserved unchanged outside four-blocker scope; no pruning or resource manipulation',
        'no_findings_suppressed':True})
    gate={'BRANCH':d.BRANCH,'BASELINE_HEAD':d.BASE,'CURRENT_V043_GIT_LF_SHA256':d.VHASH,'FLYWAY_SIGNED_CRC32':1279591798,
        'V043_FENCE_PRESENT':True,'CANONICAL_V043_MUTATED':False,'CANONICAL_V043_EXECUTED':False,'SHARED_DB_CONTACTED':False,'PRODUCTION_CONTACTED':False,
        'CLASSES_REQUIRED':46,'CLASSES_FULLY_PARTITIONED':0,'MECHANISMS_TOTAL':None,'NULL_PHYSICAL_TARGETS':None,
        'UNJUSTIFIED_REPRESENTATIVE_COLLAPSES':None,'UNCLASSIFIED_MECHANISMS':None,'REQUIRED_TYPED_CAPABILITIES':None,
        'CAPABILITIES_WITH_FIXED_TEMPLATE':None,'CAPABILITIES_WITH_EXACT_PRINCIPAL':None,'CAPABILITIES_WITH_OUTCOME_BINDING':None,
        'CAPABILITIES_WITH_OBSERVER_BINDING':None,'CAPABILITIES_WITH_CONFINED_EXECUTOR':None,'RAW_AUTHORITY_SURFACES':None,
        'ENDPOINTS_TOTAL':None,'ENDPOINTS_FULLY_BOUND':0,'UNBOUND_ENDPOINTS':None,
        'UNKNOWN_OUTCOME_PATHS_TOTAL':None,'UNKNOWN_OUTCOME_PATHS_BOUND':0,'RESEAL_INVARIANTS_TOTAL':7,'RESEAL_INVARIANTS_PHYSICALLY_BOUND':0,
        'ROLE_ADMIN_CLOSED_EPOCH_CONTRACT_COMPLETE':'NOT_PROVEN','CLOSED_EPOCH_STATE_MACHINE_COMPLETE':'NOT_PROVEN','UNKNOWN_OUTCOME_CONTRACT_COMPLETE':'NOT_PROVEN',
        'NATIVE_PARTICIPANTS_REQUIRED':7,'NATIVE_PARTICIPANTS_FULLY_BOUND':0,'UNRESOLVED_NATIVE_WORK_ANCHORS':7,'NATIVE_STATIC_SOURCE_GAP':n['NATIVE_STATIC_SOURCE_GAP'],
        'GENERIC_PROCESS_SUBSTITUTIONS':0,'FINAL_CONSUMER_SESSION_CONTRACT_COMPLETE':'NOT_PROVEN',
        'MANIFEST_COMPATIBILITY_DECISION':'C. B01_FIXTURE_MUST_CHANGE','FIXTURE_CORRECTION_PLAN_COMPLETE':'NOT_PROVEN_AGAINST_UNCLOSED_R3_MODEL',
        'AUTHORITY_GRAPH_COMPLETE':'NOT_PROVEN','AUTHORITY_EDGES_TOTAL':None,'AUTHORITY_EDGES_CLASSIFIED':0,
        'UNCLASSIFIED_MUTATION_EDGES':None,'UNMEDIATED_ACTIVE_MUTATION_EDGES':None,'TRUST_BOUNDARY_ONLY_EDGES':None,
        'STATIC_ADVERSARIAL_REVIEW':'PENDING','LEAST_PRIVILEGE_REVIEW':'PENDING','BLOCKER_COUNT':4,'HIGH_COUNT':0,'MEDIUM_COUNT':0,'LOW_COUNT':0,
        'STATIC_GATE':'BLOCKED_SOURCE_GAP','CURRENTNESS_MUTATION_CLASSES_PROVEN':0,'CURRENTNESS_MUTATION_CLASSES_UNPROVEN':46,
        'B02_CURRENTNESS_INTEGRATION_GATE':'NOT_RERUN','COMPLETE_CURRENTNESS_GATE':'FAIL_NOT_RERUN',
        'TESTS_DISTINCT':tests['TESTS_DISTINCT'],'TEST_FAILURES':tests['TEST_FAILURES'],'NEXT_EXECUTED':False,
        'B01_V2_STATIC_DESIGN_CLOSED':False,'PRIVILEGED_IMPLEMENTATION_AUTHORITY_GRANTED':False,
        'proof_levels':{'DESIGNED':'Specified requirement, no physical binding implied','STATICALLY_PROVEN':'Only named source/model/integrity assertion',
            'LIVE_PROVEN':'No new live evidence','NOT_PROVEN':'Missing or conditional proof; never zero/PASS'}}
    d.save('STATIC-GATE.json',gate)
    freeze=read('baseline-freeze.json')
    d.save('source-integrity.json',{'baseline_head':d.BASE,'baseline_tree':freeze['baseline_tree'],
        'input_hash_authority':'baseline-freeze.json#/input_git_sha256','source_inputs_frozen':freeze['input_count'],
        'CURRENT_V043_GIT_LF_SHA256':d.VHASH,'FLYWAY_SIGNED_CRC32':1279591798,'V043_FENCE_PRESENT':True,
        'CANONICAL_V043_MUTATED':False,'CANONICAL_V043_EXECUTED':False,'SHARED_DB_CONTACTED':False,'PRODUCTION_CONTACTED':False,
        'R2_unchanged':True,'V001_V042_unchanged':True,'Manifest_v6_unchanged':True,'protected_refs':'baseline-freeze.json#/protected_refs',
        'privileged_fixture_installed':False,'runtime_commands_executed':[],
        'external_documentation':'research-references.json; semantic corroboration only, not frozen implementation authority'})


if __name__=='__main__':
    freeze_native_inputs();native_contracts();session_and_fixture();authority_graph();checks();gate_and_findings()
    print(json.dumps({'STATIC_GATE':'BLOCKED_SOURCE_GAP','tests':read('tests.json')['TESTS_DISTINCT'],
        'source_inputs':read('baseline-freeze.json')['input_count']}))
