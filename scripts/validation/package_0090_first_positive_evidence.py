"""Collect two fresh preparation runs. Never certify an unexecuted positive."""
import argparse
import collections
import json
from pathlib import Path
import package_0090_source_closure as q

ap = argparse.ArgumentParser(); ap.add_argument('--directory', required=True)
ap.add_argument('--runs', nargs=2, default=['run-7','run-8'])
args = ap.parse_args(); root = Path(args.directory).resolve()
unit = json.loads((root / 'unit-tests.json').read_text(encoding='utf-8'))
q.require(unit['tests_run'] == 6 and unit['failures'] == 0 and unit['errors'] == 0 and unit['skipped'] == 0, 'Executed six-test unit proof required')


def read(p):
    return json.loads(p.read_text(encoding='utf-8'))


def write(name, value):
    (root / name).write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')


runs = []
for name in args.runs:
    folder = root / name; r = read(folder / 'foundation-runtime.json')
    q.require(not r['errors'] and len(r['cases']) == 102 and all(c['passed'] for c in r['cases']) and r['owned_runtime_destroyed'], 'Exact passing preparation required')
    q.require(all(q.sha((folder / p).read_bytes()) == h for p,h in r['input_hashes'].items()), 'Preparation input drift')
    q.require(all(q.sha((q.ROOT / 'scripts/validation' / p).read_bytes()) == h for p,h in r['recipe_hashes'].items()), 'Executed recipe drift')
    custody = read(folder / 'key-custody.json'); observation = read(folder / 'first-positive-observation.json')
    q.require(custody['erasure_verified'] and not custody['private_material_exported'], 'Private key cleanup proof required')
    q.require(observation['precheck']['status'] == 'FAIL' and not observation['executed'], 'No positive without governed precheck')
    runs.append(r)
q.require([(c['name'],c['passed']) for c in runs[0]['cases']] == [(c['name'],c['passed']) for c in runs[1]['cases']], 'Preparation semantic results differ')
fixture = read(root / args.runs[0] / 'registered-fixture-manifest.json')
policy = read(q.ROOT / 'docs/evidence/PACKAGE-0090-G3F-3B-FIXTURE-001.json')
write('fixture-approval-provenance.json', {'scope': 'TEST_ONLY', 'production_authority': False, 'nodes': [
    {'id': 'policy', 'classification': 'APPROVED_TEST_ONLY', 'source': 'SPEC-0090 Independent technical test-fixture approval; section21.2', 'value': policy, 'sha256': q.sha(bytes.fromhex(policy['canonical_policy_hex'])), 'consumer': 'offline_deadline_policy and auditor R'},
    {'id': 'activation', 'classification': 'UNAPPROVED', 'source': 'SPEC-0090 sections25.2/25.3/25.4', 'missing': ['Independently approved exact effective_from or explicitly approved relative clock recipe', 'approval/change identity and durable ADMIN provisioning audit'], 'production_authority_required': False},
    {'id': 'retained_header_manifest', 'classification': 'APPROVED_TEST_ONLY', 'source': 'SPEC-0090 retained TEST evidence fixture / VECTOR_1', 'consumer': 'immutable header, original signature preimage', 'original_window_preserved': True},
    {'id': 'live_slots', 'classification': 'DERIVED_FROM_APPROVED_INPUT', 'source': 'SPEC-0090 section3/full-domain fixture actual-OID rule', 'value': runs[0]['service_identities'], 'consumer': 'header.identity_slots'},
    {'id': 'original_test_signature', 'classification': 'DERIVED_FROM_APPROVED_INPUT', 'source': 'Current user tranche phase7; SPEC original signed-attestation commitment amendment', 'public_material': fixture, 'consumer': 'header + expected original tuple; no current field authority'},
    {'id': 'native_health', 'classification': 'UNAPPROVED', 'source': 'NATIVE-HEALTH-CONTRACT.md / NATIVE-HEALTH-DESIGN.json', 'missing': ['Independent enrollment/generation/identity and completed functional work for required participants', 'Applicable implementation authority; existing design generation_implementation=NOT_AUTHORIZED'], 'production_authority_required': False}],
    'edges': [['policy','activation'], ['retained_header_manifest','live_slots'], ['live_slots','original_test_signature'], ['activation','native_health']]})
write('active-fixture-manifest.json', {'scope': 'TEST_ONLY_PREPARATION_NOT_ACTIVE', 'production_authority': False,
    'prepared_public_inputs': [str(Path(n) / 'registered-fixture-manifest.json') for n in args.runs],
    'runtime_hash_rule': 'Recipe hashes and generated public inputs are separate; random private keys never published',
    'active': False, 'gaps': {'G1': 'PARTIAL', 'G2': 'PARTIAL', 'G3': 'OPEN', 'G4': 'OPEN', 'G5': 'PARTIAL', 'G6': 'PARTIAL', 'G7': 'OPEN', 'G8': 'PARTIAL'}})
gap_rows = [
 ('G1','PARTIAL','SPEC-0090 sections4/5 and original signed-input registration amendment','VECTOR_1 header values; actual OIDs/names','offline_readiness FK parent and committed header/original/lifecycle','No new header authority gap beyond prerequisite approvals',False),
 ('G2','PARTIAL','SPEC-0090 sections14/16/21.2/22.1/25','Exact42 source/script/CRC expectation;1040 column ACL equality;70 context properties','Complete independently expected effective ACL/readiness manifests; approved policy metadata','Governed ADMIN provisioning after activation and health prerequisites',False),
 ('G3','OPEN','SPEC-0090 sections9/18; NATIVE-HEALTH-CONTRACT.md and NATIVE-HEALTH-DESIGN.json','Pinned library, actual generated signature vectors; not participant health','Independent enrollment/generation/identity/functional-progress observations for required participants','Existing design generation_implementation=NOT_AUTHORIZED; applicable implementation/proof authority must be established',False),
 ('G4','OPEN','SPEC-0090 sections25.2/25.3/25.4; user phase5/10','fixture-1 numeric values; original golden windows; observed finite DB clock','Approved exact activation instant or explicit relative DB-clock recipe plus approval/change identity and durable ADMIN audit','Independent TEST activation/administrative fixture approval, not production policy',True),
 ('G5','PARTIAL','SPEC-0090 original signed-attestation commitment amendment; current user phase7','Actual new TEST Ed25519 original, SPKI, signature/preimage, exact commitment; no window extension','Committed independently supplied original tuple with header; activation/lineage where applicable','TEST signing allowed by this tranche; no production signer authority inferred',False),
 ('G6','PARTIAL','Current user phase7/8; full-domain fixture custody contract','Root0700/0600, private never exported, backend OS read denial, verified erasure','Preflight MAC key lifecycle/lineage for later S01; not a direct S04 crypto dependency','No production custody authority needed; no HSM claim',False),
 ('G7','OPEN','SPEC-0090 sections3/16/21.4/25','Authentic direct logins; prepared original data','First R chain policy→readiness→header→slot; later intent/admission is not needed for S04','Approved activation and real health, not ownership-derived authority',False),
 ('G8','PARTIAL','SPEC-0090 sections8/14/21.1 and thirteen-case contract','First S04 expectation frozen independently:42 rows,no writes/audit/consumption','Observed first success; remaining eighteen-wrapper/thirteen-trajectory outcomes','No production authority required for expected outcomes',False)]
write('fixture-gap-matrix.json', {'scope':'FIRST_READER_FOUNDATION_VS_FULL_PACKAGE_DISTINGUISHED','rows':[
    {'gap_id':id_,'status':status,'exact_contract_source':source,'already_approved_test_material':material,
     'missing_values':missing,'missing_authority':authority,'can_be_closed_with_test_only_technical_fixture':True,
     'requires_new_design_decision':decision,'requires_production_authority':False}
    for id_,status,source,material,missing,authority,decision in gap_rows]})
write('active-fixture-runtime.json', {'runs': [n + '/active-fixture-runtime.json' for n in args.runs],
    'preparation_reproduced': True, 'ACTIVE_LOADER_REPRODUCIBLE': False, 'registration_committed': False,
    'actual_policy_rows': 0, 'actual_ready_rows': 0, 'actual_header_rows': 0, 'actual_expected_tuple_rows': 0})
write('first-positive-expectation.json', read(root / args.runs[0] / 'first-positive-expectation.json'))
write('first-positive-observation.json', {'runs': [n + '/first-positive-observation.json' for n in args.runs],
    'precheck': 'FAIL', 'executed': False, 'pass': False, 'active_sibling_attacks_executed': False, 'active_search_path_attacks_executed': False})
ledger = read(q.ROOT / 'docs/evidence/package-0090-semantic-ledger-active-fixture-final/semantic-ledger.json')['records']
reader_in_corpus = any('public.offline_read_history(uuid,bytea,uuid,text)' in r['source_functions'] for r in ledger)
write('first-positive-semantic-bindings.json', {'global_candidate_shapes': len(ledger), 'global_bound': 0, 'global_unbound': len(ledger),
    'selected_reader_in_existing_call_corpus': reader_in_corpus, 'path_candidate_shapes': None, 'path_bound_shapes': 0, 'path_unbound_shapes': None,
    'reason': 'No runtime wrapper traversal because precheck fails. Existing 68-function call corpus omits selected read_history; future actual path needs an explicit source addendum.', 'bindings': [], 'global_ledger_mutated': False})
write('first-positive-null-matrix.json', {'first_path_complete': False, 'cases': [], 'reason': 'No otherwise valid ACTIVE wrapper context; native signature NULL vector remains crypto-only evidence'})
write('first-positive-acl.json', {'first_path_complete': False, 'known_subproofs': ['1040 exact source/SPEC column ACLs', '70 installed function context attributes', 'four direct LOGIN/SET ROLE/raw-read boundaries'],
    'positive_context_required': True, 'missing': ['Complete independently expected first-reader effective privilege chain', 'Authenticated immutable-slot successful operation and positive-context attacks']})
write('native-health-evidence.json', {'binary_sha256': runs[0]['binary_sha256'], 'versions': runs[0]['build_versions'],
    'actual_generated_signature_vectors_pass': True, 'private_backend_read_denied': True, 'participant_functional_health_proven': False,
    'boundary': 'Installed crypto and signature behavior do not establish enrollment/generation/functional watchdog health'})
order = [
 ('S04','offline_read_history','AUDITOR',[],False,'complete ordered history; no writes'),
 ('S01','offline_preflight','AUDITOR',[],False,'authenticated scope receipt; no writes'),
 ('S02','offline_inspect','AUDITOR',[],False,'bounded domain/control inspection; no writes'),
 ('S03','offline_reconcile','AUDITOR',[],False,'bounded reconciliation snapshot; no result recording'),
 ('S13','offline_claim_attempt','EXECUTOR',['S01'],True,'CLAIMED/OWNED, original possession/deadlines'),
 ('S05','offline_begin_verification','VERIFIER',['S13'],True,'frozen verification begin/replay projection'),
 ('S06','offline_persist_verification','VERIFIER',['S05'],True,'verified original evidence/receipt, effects progress'),
 ('S07','offline_begin_principal','ISSUER',['S06'],True,'principal verification projection'),
 ('S08','offline_apply_principal','ISSUER',['S07'],True,'exact principal/operation receipt'),
 ('S09','offline_begin_initial_credential','ISSUER',['S08'],True,'fresh credential-origin verification'),
 ('S10','offline_apply_initial_credential','ISSUER',['S09'],True,'credential receipt and CREATED_NOT_DELIVERABLE'),
 ('S14','offline_claim_attempt','EXECUTOR',['S10'],True,'one delivery consumption, DELIVERY_ATTEMPTED'),
 ('S15','offline_claim_attempt','EXECUTOR',['S14'],True,'bounded original delivery outcome report'),
 ('S11','offline_begin_grant','ISSUER',['S15'],True,'requires exact DELIVERY_ACKNOWLEDGED'),
 ('S12','offline_apply_grant','ISSUER',['S11'],True,'original grant/operation receipt'),
 ('S16','offline_authenticate_command','EXECUTOR',['S12'],True,'bound admission, current authority and possession'),
 ('S17','offline_prepare_attested_decision','EXECUTOR',['S16'],True,'bounded decision/JCA projection'),
 ('S18','offline_apply_attested_decision','EXECUTOR',['S17'],True,'decision/head + consumed admission + completion/reconciliation required')]
signatures = read(q.ROOT / 'docs/evidence/package-0090-semantic-ledger-active-fixture-final/positive-wrapper-results.json')['expected_signatures']
claim_counts = {'S13': 9, 'S14': 12, 'S15': 13}
dag_nodes = []
for id_,name,caller,parents,mutating,output in order:
    matches = [s for s in signatures if s.startswith('public.' + name + '(')]
    if id_ in claim_counts:
        matches = [s for s in matches if len(s.split('(',1)[1].removesuffix(')').split(',')) == claim_counts[id_]]
    q.require(len(matches) == 1, 'Exact wrapper signature required for DAG: ' + id_)
    dag_nodes.append({'id': id_, 'wrapper_signature': matches[0], 'caller': caller, 'predecessors': parents,
        'authority_guard_class': 'M' if mutating else 'R',
        'mutating': 'M_GUARDED_POTENTIALLY_WRITING_OR_LOCKING' if mutating else False,
        'physical_write_effects': 'SOURCE_TRAJECTORY_QUALIFICATION_PENDING' if mutating else 'NONE',
        'expected_logical_output': output, 'new_semantic_groups': 'UNPROVEN_RUNTIME_DEPENDENT',
        'fixture_dependencies': ['governed ACTIVE foundation', 'exact original stage/possession/authority inputs where M applies']})
positions = {n['id']: i for i,n in enumerate(dag_nodes)}
q.require(len(positions) == 18 and all(p in positions and positions[p] < positions[n['id']] for n in dag_nodes for p in n['predecessors']), 'Exact acyclic eighteen-wrapper plan required')
write('wrapper-expansion-dag.json', {'status': 'SOURCE_DERIVED_PLAN_NOT_EXECUTED', 'provenance': 'SPEC-0090 sections8/10/11/21.1; all nodes additionally require exact R/M/READY/policy/current original authority guards',
    'nodes': dag_nodes,
    'count': 18, 'execution_authority': 'BLOCKED', 'terminal_or_expired_readers': 'R ignores mutation expiry but still requires authentic slot/current READY/effective read policy'})
write('READINESS.json', {'baseline': 'a82bb8ccf352ba89510f52b3d9c3f1ecc3dee7d8', 'source_hash': q.SOURCE_HASH,
    'canonical_v043_mutated': False, 'canonical_v043_executed': False, 'active_fixture_foundation_ready': False, 'full_fixture_ready': False,
    'first_positive_wrapper': 'public.offline_read_history(uuid,bytea,uuid,text)', 'first_positive_caller': 'test_0090_audit',
    'expectation_frozen': True, 'active_fixture_precheck': 'FAIL', 'first_authentic_positive_executed': False, 'first_authentic_positive_pass': False,
    'test_Ed25519_key_custody_ready': True, 'full_key_custody_ready': False, 'native_functional_health_ready': False,
    'global_candidate_shapes': 818, 'global_bound': 0, 'global_unbound': 818, 'global_ledger_changed': False,
    'active_loader_reproducible': False, 'bounded_preparation_reproduced_twice': True, 'B06_STATUS': 'OPEN',
    'B01_STATUS': 'OPEN', 'B02_STATUS': 'OPEN', 'B03_STATUS': 'OPEN', 'scoped_blockers': 2,
    'scoped_high_count': 'UNKNOWN_REVIEW_NOT_COMPLETE', 'scoped_medium_count': 'UNKNOWN', 'scoped_low_count': 'UNKNOWN',
    'distinct_native_tests': 102, 'unit_tests': 6, 'total_distinct_tests': 108, 'final_failures': 0,
    'shared_database_contacted': False, 'production_contacted': False, 'execution_authority': 'BLOCKED', 'recovery_authority': 'BLOCKED', 'ROOM_OPERATIONAL': False, 'NEXT_EXECUTED': False})
files = list(root.rglob('*')) + [q.ROOT / 'docs/evidence/PACKAGE-0090-ACTIVE-fixture-first-positive.md']
files += [q.ROOT / 'scripts/validation' / n for n in ['package_0090_active_foundation.py','package_0090_first_positive.py',
    'package_0090_first_positive_evidence.py','test_package_0090_first_positive.py','package_0090_source_closure.py','Package0090SourceClosureFlyway.java']]
files += list((q.ROOT / 'applications/marketplace-operations-persistence-postgres/native/flooow_offline_mac32').iterdir())
files += [q.ROOT / 'scripts/validation/package_0090_full_qualification/codec.py']
entries = {p.relative_to(q.ROOT).as_posix(): {'sha256':q.sha(p.read_bytes()),'bytes':p.stat().st_size}
           for p in sorted(files) if p.is_file() and p.name != 'SHA256-MANIFEST.json'}
write('SHA256-MANIFEST.json', {'scope':'SIGNED_INPUT_PREPARATION_AND_FAILED_FIRST_POSITIVE_PRECHECK_NOT_ACTIVE_PROOF','entries':entries})
print(json.dumps({'preparation_tests': 102, 'distinct_tests': 108, 'first_positive_executed': False, 'scoped_blockers': 2}))
