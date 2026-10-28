"""Offline R2 derivation. Reads Git/local JSON only; never imports runtime harnesses.

This is deliberately a blocked partial closure, not a synthetic PASS. Execute
only at the frozen baseline to regenerate; verify_evidence.py is post-commit safe.
"""
import collections
import hashlib
import itertools
import json
from pathlib import Path
import subprocess
import zlib

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
PREV = ROOT / 'docs/evidence/package-0090-B01-v2-expanded-capability-mediation'
SRC = ROOT / 'docs/evidence/package-0090-full-reachable-expectation-closure-v2'
BASE = '5aa9e92f902d0af59abbbf67eb9a9b8f527b6368'
BRANCH = 'checkpoint/package-0090-cloud-handoff'
VHASH = '007ab786c417c41e2b1702ebf3852cb70ff5c142fa3fde195385e04c6dde8b4a'


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT)


def sha(b):
    return hashlib.sha256(b).hexdigest()


def read(folder, name):
    return json.loads((folder / name).read_text(encoding='utf-8-sig'))


def digest(value):
    return sha(json.dumps(value, sort_keys=True, separators=(',', ':')).encode())


def save(name, value):
    (OUT / name).write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')


def binding(path, pointer):
    return {'path': path.relative_to(ROOT).as_posix(), 'pointer': pointer,
            'git_lf_sha256': sha(git('show', BASE + ':' + path.relative_to(ROOT).as_posix()))}


assert git('rev-parse', 'HEAD').decode().strip() == BASE
assert git('branch', '--show-current').decode().strip() == BRANCH
assert git('rev-parse', 'origin/' + BRANCH).decode().strip() == BASE
# Worktree was clean before this evidence directory was created. Reject all other changes.
for line in git('status', '--porcelain', '--untracked-files=all').decode().splitlines():
    changed = line[3:].replace('\\', '/')
    assert changed.startswith(OUT.relative_to(ROOT).as_posix() + '/') or changed == 'docs/evidence/PACKAGE-0090-B01-v2-static-closure-revision-2.md', line

migrations = sorted(ROOT.glob('applications/**/db/migration/V*.sql'))
v043 = next(p for p in migrations if p.name.startswith('V043__'))
vb = git('show', BASE + ':' + v043.relative_to(ROOT).as_posix())
assert sha(vb) == VHASH
crc = zlib.crc32(''.join(vb.decode('utf-8-sig').splitlines()).encode())
crc = crc if crc < 2**31 else crc - 2**32
assert crc == 1279591798
fence = vb.index(b"RAISE EXCEPTION USING ERRCODE = '55000'") < vb.index(b'SET LOCAL search_path')
assert fence
old = {p.name: read(PREV, p.name) for p in PREV.glob('*.json')}
classes = read(SRC, 'mutation-class-denominator-v3.json')['classes']
graph = read(SRC, 's04-reachability-graph-v3.json')
nodes = {n['id']: n for n in graph['nodes']}
inputs = sorted(set([*PREV.glob('*.json'), ROOT / 'docs/evidence/PACKAGE-0090-B01-v2-expanded-capability-mediation.md',
                    *SRC.glob('*.json'), ROOT / 'scripts/validation/package_0090_b01_v2/design.py',
                    ROOT / 'scripts/validation/package_0090_s04_native_health.c',
                    ROOT / 'docs/specifications/SPEC-0090-governed-offline-field-proof-exclusive-capability-composition.md',
                    ROOT / 'docs/adr/ADR-0090-governed-offline-field-proof-exclusive-capability-composition.md']))
frozen = {p.relative_to(ROOT).as_posix(): sha(git('show', BASE + ':' + p.relative_to(ROOT).as_posix())) for p in inputs}
for p in inputs:
    assert sha(p.read_bytes().replace(b'\r\n', b'\n')) == sha(git('show', BASE + ':' + p.relative_to(ROOT).as_posix()).replace(b'\r\n', b'\n'))
protected = {}
for r in old['source-integrity.json']['protected_refs']:
    probe = subprocess.run(['git','rev-parse','--verify',r], cwd=ROOT, capture_output=True)
    protected[r] = probe.stdout.decode().strip() if probe.returncode == 0 else 'REF_ABSENT_AT_BASELINE'
save('baseline-freeze.json', {'branch': BRANCH, 'baseline_head': BASE, 'origin_head_after_fetch': BASE,
    'local_equals_remote': True, 'worktree_clean_before_evidence_creation': True,
    'fetch_performed': True, 'expected_V043_sha256': VHASH, 'Flyway_signed_CRC32': crc,
    'V043_fence_present': fence, 'input_git_hashes': frozen, 'protected_refs': protected})

# Distinct mechanisms are NOT represented by one generic ACL/constraint mutation.
# These are source-indexed exact constraint removals, not a completeness argument.
constraints = read(SRC, 'constraint-v2.json')['constraints']
mechanisms = []
contracts = []
templates = []
principals = []
outcomes = []
names = {'CONSTR_NOTNULL': 'NOT_NULL', 'CONSTR_CHECK': 'CHECK', 'CONSTR_FOREIGN': 'FOREIGN_KEY',
         'CONSTR_PRIMARY': 'PRIMARY_KEY', 'CONSTR_UNIQUE': 'UNIQUE'}


def qi(s):
    return '"' + s.replace('"', '""') + '"'


def add_cap(cid, cls, mech, target, sql, principal, pre, post, source):
    contract = {'CAPABILITY_ID': cid, 'ALLOWED_CLASS': cls, 'ALLOWED_MECHANISM': mech,
        'EXACT_TARGET': target, 'FIXED_OPERATION_TEMPLATE': cid, 'EXACT_PRINCIPAL': principal,
        'PRECONDITION_DIGEST': digest({'source': source, 'target': target, 'pre': pre}),
        'EXPECTED_PRE_STATE': pre, 'EXPECTED_POST_STATE': post,
        'OUTCOME_PROOF': cid, 'AUDIT_EVENT': 'R2_MUTATION_OUTCOME',
        'UNKNOWN_OUTCOME_RULE': 'MUTATION_UNKNOWN -> RECONCILING; never replay blindly or reseal',
        'REVOCATION_RULE': 'Revoke endpoint, credential, backend and process tree; independent extinction receipt before reseal',
        'status': 'DESIGNED', 'executable_installation_authorized': False,
        'source': source, 'runtime_qualified': False}
    contracts.append(contract)
    templates.append({'CAPABILITY_ID': cid, 'language': 'SQL', 'literal': sql,
        'caller_parameters': [], 'identifier_interpolation_at_runtime': False,
        'execution_phase': 'UNSEALED_ONLY', 'status': 'DESIGNED',
        'transport_and_executor_binding': 'NOT_PROVEN'})
    principals.append({'CAPABILITY_ID': cid, 'principal': principal, 'status': 'DESIGNED',
        'OS_process_identity': 'NOT_PROVEN', 'credential_delivery': 'one epoch/one operation only after durable invalidation',
        'no_qualification_actor_receives_credential': True, 'authority_containment': 'NOT_PROVEN'})
    outcomes.append({'CAPABILITY_ID': cid, 'expected_delta': {'before': pre, 'after': post},
        'observer': 'V2_OUTCOME_VERIFIER', 'proof': 'Independent protected catalog projection + durable operation/transaction outcome + full unrelated-state comparison',
        'observer_exact_read_entitlement': 'NOT_PROVEN', 'ACK_is_sufficient': False,
        'durable_audit_required': ['operation_id', 'capability_id', 'template_digest', 'target_digest',
            'epoch', 'generation', 'actor_anchor', 'pre_digest', 'post_digest', 'transaction_identity', 'outcome', 'audit_tip'],
        'status': 'DESIGNED'})


for i, c in enumerate(constraints):
    typ = names[c['source']['contype']]
    target = {'database': 'g3f4', 'relation': c['relation'], 'constraint': c['source'].get('conname'),
              'column': None}
    rel = '.'.join(qi(s) for s in c['relation'].split('.'))
    if typ == 'NOT_NULL':
        target['column'] = c['source']['keys'][0]['String']['sval']
        sql = f"ALTER TABLE {rel} ALTER COLUMN {qi(target['column'])} DROP NOT NULL;"
    else:
        assert target['constraint']
        sql = f"ALTER TABLE {rel} DROP CONSTRAINT {qi(target['constraint'])};"
    source = binding(SRC / 'constraint-v2.json', '/constraints/' + str(i))
    mid = 'R2/CONSTRAINT/' + str(i)
    mechanisms.append({'CLASS': '0090/CURRENTNESS/constraint', 'MECHANISM_ID': mid,
        'mechanism_kind': typ, 'SOURCE_AUTHORITY': source, 'PHYSICAL_TARGET': target,
        'MUTATION_PRIMITIVE': sql, 'REQUIRED_PRIVILEGE': 'exact relation owner or closed-epoch deployment superuser; catalog relations need privileged bootstrap',
        'CURRENT_ACTOR_PATH': 'Existing deployment bootstrap outside active qualification; no new installed actor',
        'SEALED_MUTABILITY': 'FORBIDDEN_BY_DESIGN_NOT_PROVEN',
        'QUALIFICATION_MUTABILITY': 'CLOSED_EPOCH_REPLACEMENT_ONLY',
        'EXPECTED_OBSERVER': 'Independent constraint + dependent index/trigger/column projection',
        'REPRESENTATIVE_OPERATION': 'R2/C/' + str(i),
        'REPRESENTATIVE_ADEQUACY_REASON': 'Only this exact removal; no equivalence to add/validate/replace/rename/dependency change is asserted',
        'status': 'DESIGNED', 'complete': False})
    add_cap('R2/C/' + str(i), '0090/CURRENTNESS/constraint', mid, target, sql,
            {'SQL_session_user': 'postgres', 'OS_uid': 999, 'phase': 'OUT_OF_EPOCH_BOOTSTRAP'},
            {'exact_source_constraint': c['source'], 'relation': c['relation']},
            {'constraint_removed': target, 'required_dependent_catalog_delta': 'NOT_PROVEN',
             'SQL_applicability_to_exact_relation': 'NOT_PROVEN',
             'unrelated_changes': 'DENY', 'semantically_complete': False}, source)

# Literal, same authenticated final consumer operations. These prove no executor.
for i, zone in enumerate(['UTC', 'Etc/UTC']):
    add_cap('R2/SESSION/TIMEZONE/' + str(i), '0090/CURRENTNESS/session_environment', 'SESSION_TIMEZONE',
            {'authenticated_role': 'test_0090_audit', 'connection': 'SAME_FINAL_CONSUMER'},
            "SET TIME ZONE '" + zone + "';", {'SQL_session_user': 'test_0090_audit', 'OS_uid': 10004},
            {'zone': ['UTC', 'Etc/UTC'][1-i], 'PID_and_handle': 'continuous exact enrolled session'},
            {'zone': zone, 'session_user': 'test_0090_audit', 'PID_and_handle': 'unchanged'},
            binding(PREV / 'consumer-session-capability.json', '/fixed_same_connection_settings'))

# Only exact NOLOGIN / LOGIN targets in the frozen ordinary TEST role set.
role_targets = [r['name'] for r in read(SRC, 'role-graph-v2.json')['roles'] if r['name'].startswith('test_0090_')]
assert len(role_targets) == 4
for role in role_targets:
    for setting in ['NOLOGIN', 'LOGIN']:
        add_cap('R2/ROLE/' + role + '/' + setting, '0090/CURRENTNESS/role', 'ROLE_LOGIN',
                {'role': role}, 'ALTER ROLE ' + qi(role) + ' ' + setting + ';',
                {'SQL_session_user': 'postgres', 'OS_uid': 999, 'phase': 'OUT_OF_EPOCH_BOOTSTRAP'},
                {'role': role, 'login': setting == 'NOLOGIN', 'all_other_attributes': 'frozen role-graph-v2.json'},
                {'role': role, 'login': setting == 'LOGIN', 'memberships': [], 'owner_memberships': []},
                binding(SRC / 'role-graph-v2.json', '/roles'))

# Explicit remaining mechanism obligations by class, not a claimed exhaustive list.
refinements = {
 'constraint': ['NOT_NULL', 'CHECK', 'FOREIGN_KEY', 'PRIMARY_KEY', 'UNIQUE', 'ADD', 'DROP', 'VALIDATE', 'REPLACE', 'DEFERRABILITY', 'DEPENDENT_INDEX_TRIGGER'],
 'effective_acl': ['TABLE_ACL', 'COLUMN_ACL', 'FUNCTION_ACL', 'SCHEMA_ACL', 'DATABASE_ACL', 'SEQUENCE_ACL_PRESENCE_ABSENCE', 'GRANT_OPTION', 'OWNER_IMPLICIT_AUTHORITY', 'ROLE_INHERITANCE', 'PUBLIC_ACL'],
 'future_default_acl': ['GLOBAL_DEFAULT_PRIVILEGES', 'SCHEMA_DEFAULT_PRIVILEGES', 'CREATOR', 'GRANTEE', 'OBJECT_KIND', 'GRANT_OPTION'],
 'membership_absence': ['ADMIN_OPTION', 'INHERIT_OPTION', 'SET_OPTION', 'INCOMING_OWNER_EDGE', 'OUTGOING_OWNER_EDGE', 'IMPLICIT_PG_DATABASE_OWNER'],
 'role': ['LOGIN', 'INHERIT', 'SUPERUSER', 'CREATEROLE', 'CREATEDB', 'REPLICATION', 'BYPASSRLS', 'IDENTITY_RENAME'],
 'relation': ['IDENTITY', 'OWNERSHIP', 'RLS_ENABLE_DISABLE', 'RLS_FORCE', 'RLS_POLICY', 'VIEW_EXPANSION', 'VIEW_SECURITY_MODE', 'PERSISTENCE'],
 'session_environment': ['AUTHENTICATED_IDENTITY', 'EFFECTIVE_ROLE', 'SEARCH_PATH', 'ENCODING', 'TIMEZONE', 'STANDARD_CONFORMING_STRINGS', 'TRANSACTION_ISOLATION', 'RECONNECT'],
 'native_participant': ['BINARY_MODULE_BINDING', 'PROCESS_IDENTITY', 'PARENT_CHILD', 'FUNCTIONAL_WORK', 'WORK_ANCHOR', 'DEPENDENCY', 'CATALOG', 'GENERATION', 'FRESHNESS', 'REPLACEMENT'],
 'native_binding': ['ENROLLMENT', 'CHANNEL', 'NONCE', 'PIDFD', 'WORK_COUNTER', 'GUARD', 'EPOCH', 'GENERATION'],
 'sequence_absence': ['SEQUENCE_CREATE_DROP', 'IDENTITY_ADD_DROP', 'DEFAULT_NEXTVAL', 'OWNED_DEPENDENCY', 'SEQUENCE_ACL'],
 'return_consumer': ['RETURN_TUPLE', 'HISTORY_ORDER', 'HISTORY_CONTENT', 'WRAPPER_ENTITLEMENT', 'RAW_HISTORY_DENIAL'],
 'expression': ['FUNCTION_RESOLUTION', 'OPERATOR_RESOLUTION', 'CAST_RESOLUTION', 'SEARCH_PATH', 'COLLATION', 'ERROR_NULL_SEMANTICS'],
 'storage_binding': ['STORAGE_OWNERSHIP', 'PARENT', 'PROVIDER_BINDING', 'REQUIRED_PRESENCE'],
 'audit_binding': ['AUDIT_IDENTITY', 'CONTEXT', 'TRANSACTION', 'PREPARED', 'TERMINAL_OUTCOME', 'HASH_CHAIN', 'TRUSTED_TIP'],
 'policy_readiness_binding': ['POLICY_DIGEST', 'POLICY_ACTIVATION', 'BINDING_HEADER', 'LIFECYCLE', 'READINESS', 'GUARD', 'GENERATION_VECTOR'],
}
for kind in ['builtin_function', 'source_native_function', 'function_candidate_signature']:
    refinements[kind] = ['FUNCTION_BODY', 'FUNCTION_OWNER', 'FUNCTION_ACL', 'FUNCTION_SECURITY_MODE', 'FUNCTION_SEARCH_PATH',
                         'FUNCTION_SIGNATURE', 'FUNCTION_DEFAULTS', 'EXTENSION_PROVIDER_BINDING', 'REPLACE_DROP_RENAME']
class_ledger = []
for row in classes:
    kind = row['OBJECT_CLASS']
    prior = [p for p in old['class-mechanism-partitions.json']['partitions'] if p['CLASS_ID'] == row['CLASS_ID']]
    obligations = refinements.get(kind, [p['MECHANISM_ID'] for p in prior])
    class_ledger.append({'CLASS': row['CLASS_ID'], 'source': binding(SRC / 'mutation-class-denominator-v3.json', '/classes/' + str(classes.index(row))),
        'frozen_graph_objects': row['GRAPH_OBJECTS'], 'distinct_mechanism_obligations': obligations,
        'physical_target_resolution': [{'component': nodes[g]['component'], 'pointer': nodes[g]['pointer']} for g in row['GRAPH_OBJECTS']],
        'mechanism_closure': 'NOT_PROVEN', 'representative_adequacy': 'NOT_PROVEN',
        'gap': 'Source pointers identify expected records; do not prove all physical mutation paths, executable templates or actor containment.'})
save('class-mechanism-partitions-v2.json', {'status': 'DESIGNED', 'classes_required': 46,
    'classes_fully_partitioned': 0, 'fully_partitioned_count_semantics': 'No class has a complete reachable-mechanism proof; not zero reachable mechanisms.',
    'mechanisms_total': None, 'known_exact_constraint_removal_records': len(mechanisms),
    'compound_constraint_counts': dict(collections.Counter(names[c['source']['contype']] for c in constraints)),
    'effective_acl_records': len(read(SRC, 'effective-acl-v6.json')['entries']),
    'all_reachable_mechanisms_partitioned': 'NOT_PROVEN', 'compound_mechanisms_refined': 'PARTIAL',
    'null_physical_targets_in_exact_constraint_subset': 0, 'null_physical_targets_total': None,
    'unjustified_representative_collapses': None, 'classes': class_ledger, 'exact_mechanisms': mechanisms})
save('typed-capability-catalog-v2.json', {'status': 'DESIGNED', 'total_required_capabilities': None,
    'partial_contracts_total': len(contracts), 'capabilities': contracts,
    'previous_74_disposition': [{'CAPABILITY_ID': c['CAPABILITY_ID'],
        'decision': 'MUST_SPLIT_FURTHER' if c['CAPABILITY_CLASS'] == 'BOOTSTRAP_ONLY_CAPABILITY' else 'NOT_PROVEN',
        'reason': 'Candidate enum over multiple targets is not one executable authority; exact source-target-operation-principal/outcome derivation required.',
        'covered_by_R2': [x['CAPABILITY_ID'] for x in contracts if x['ALLOWED_CLASS'] in c['AUTHORIZED_CLASS_IDS'] and
                          (x['ALLOWED_CLASS'].endswith('/constraint') or x['ALLOWED_CLASS'].endswith('/session_environment') or x['ALLOWED_CLASS'].endswith('/role'))],
        'safe_coalescence_proven': False, 'retained_as_executable': False} for c in old['typed-capability-catalog.json']['capabilities']],
    'minimum_authority_complete': False, 'raw_authority_surface': 'NOT_PROVEN'})
save('fixed-operation-templates.json', {'status': 'DESIGNED', 'templates': templates,
    'literal_templates_total': len(templates), 'raw_sql_caller_capabilities_in_this_subset': 0,
    'raw_command_caller_capabilities_in_this_subset': 0, 'arbitrary_targets_in_this_subset': 0,
    'complete_required_set': False, 'parse_execute_or_install_performed': False})
save('capability-principal-bindings.json', {'status': 'DESIGNED', 'bindings': principals,
    'exact_static_SQL_principal_subset_count': len(principals), 'fully_bound_OS_SQL_containment_count': 0})
save('capability-outcome-bindings.json', {'status': 'DESIGNED', 'bindings': outcomes,
    'independent_physical_observer_bindings_complete': False})

# A finite closed-world abstract protocol. No operation availability is claimed.
states = ['SEALED', 'UNSEAL_REQUESTED', 'UNSEALED', 'CAPABILITY_ACTIVATING', 'ACTIVE',
          'MUTATION_IN_FLIGHT', 'MUTATION_COMMITTED', 'MUTATION_UNKNOWN', 'RECONCILING',
          'CAPABILITY_REVOKING', 'WORKER_EXTINCTION_PENDING', 'RESEAL_PENDING', 'SEALED_NEW_EPOCH', 'BLOCKED']
invariants = ['old_capability_revoked', 'old_worker_extinct', 'mutation_outcome_known', 'audit_durable',
              'generation_advanced', 'new_expected_state_bound', 'new_observer_contract_bound']
edges = [
 ('SEALED', 'UNSEAL_REQUESTED', 'V2_COORDINATOR', ['exclusive_lease', 'authorized_contract', 'prepared_durable']),
 ('UNSEAL_REQUESTED', 'UNSEALED', 'V2_COORDINATOR', ['invalidation_durable', 'all_old_endpoints_fenced', 'old_consumers_drained']),
 ('UNSEALED', 'CAPABILITY_ACTIVATING', 'TRUSTED_BOOTSTRAP', ['generation_advanced', 'operation_identity_reserved', 'exact_target_precondition']),
 ('CAPABILITY_ACTIVATING', 'ACTIVE', 'TRUSTED_BOOTSTRAP', ['fixed_worker_anchored', 'credential_scoped', 'authority_attested']),
 ('ACTIVE', 'MUTATION_IN_FLIGHT', 'FIXED_WORKER', ['prepared_durable', 'exact_pre_state', 'lease_current']),
 ('MUTATION_IN_FLIGHT', 'MUTATION_COMMITTED', 'V2_OUTCOME_VERIFIER', ['commit_receipt', 'exact_post_state', 'audit_durable']),
 ('MUTATION_IN_FLIGHT', 'MUTATION_UNKNOWN', 'V2_COORDINATOR', ['timeout_or_lost_ack_or_crash']),
 ('MUTATION_UNKNOWN', 'RECONCILING', 'V2_OUTCOME_VERIFIER', ['independent_transaction_and_state_probe']),
 ('RECONCILING', 'MUTATION_COMMITTED', 'V2_OUTCOME_VERIFIER', ['commit_receipt', 'exact_post_state', 'audit_durable']),
 ('RECONCILING', 'CAPABILITY_REVOKING', 'V2_OUTCOME_VERIFIER', ['known_no_commit', 'exact_pre_state', 'audit_durable']),
 ('MUTATION_COMMITTED', 'CAPABILITY_REVOKING', 'TRUSTED_BOOTSTRAP', ['mutation_outcome_known', 'audit_durable']),
 ('CAPABILITY_REVOKING', 'WORKER_EXTINCTION_PENDING', 'TRUSTED_BOOTSTRAP', ['old_capability_revoked', 'credential_revoked', 'backend_terminated', 'audit_durable']),
 ('WORKER_EXTINCTION_PENDING', 'RESEAL_PENDING', 'V2_OUTCOME_VERIFIER', ['old_worker_extinct', 'no_descendants', 'no_sessions', 'no_prepared_transactions', 'mutation_outcome_known', 'audit_durable']),
 ('RESEAL_PENDING', 'SEALED_NEW_EPOCH', 'V2_COORDINATOR', invariants),
 ('SEALED_NEW_EPOCH', 'UNSEAL_REQUESTED', 'V2_COORDINATOR', ['exclusive_lease', 'authorized_contract', 'prepared_durable']),
 ('BLOCKED', 'RECONCILING', 'V2_OUTCOME_VERIFIER', ['exclusive_recovery_lease', 'durable_lineage_available', 'all_eligibility_denied']),
]
for state in states:
    if state != 'BLOCKED':
        edges.append((state, 'BLOCKED', 'V2_COORDINATOR', ['any_missing_evidence_or_guard_failure']))
transitions = []
for i, (a, b, actor, guards) in enumerate(edges):
    transitions.append({'id': 'R2/T/' + str(i), 'from': a, 'to': b, 'authority': actor,
        'precondition': guards, 'durable_evidence': ['compare_and_swap_prior_state_revision', 'transition_record', 'independent_audit_tip'] + guards,
        'audit_event': 'R2_' + a + '_TO_' + b, 'generation': 'Monotonic reservation before activation; never decrement/reuse; old tuple always denied after invalidation',
        'epoch': 'Exact transition/lease tuple; replacement creates new epoch, never reactivates old endpoints',
        'expected_currentness_invalidation': 'DENY after UNSEAL_REQUESTED -> UNSEALED; BLOCKED always denies; SEALED states still confer no operational readiness in this tranche',
        'recovery_behavior': 'Restart at last independently durable state; ambiguity -> MUTATION_UNKNOWN or BLOCKED, never assume abort/commit; reconcile before retry'})
legal = {(t['from'], t['to']) for t in transitions}
save('closed-epoch-state-machine.json', {'status': 'DESIGNED', 'states': states, 'initial': 'SEALED',
    'transitions': transitions, 'impossible_transitions': [[a,b] for a in states for b in states if (a,b) not in legal],
    'guard_evaluation': 'All guards must be independently known TRUE. Missing/null/unknown/stale is FALSE.',
    'revision_serialization': 'Durable CAS under exclusive lease; no worker gets mutation credential until invalidation/drain acknowledgements complete.',
    'no_implicit_resume': True, 'runtime_implemented': False})
save('closed-epoch-transition-authority.json', {'status': 'DESIGNED',
    'actors': {'V2_COORDINATOR': {'uid': 10001, 'SQL': 'none', 'cannot_attest_own_outcome': True},
        'TRUSTED_BOOTSTRAP': {'uid': 999, 'SQL': 'postgres only outside SEALED', 'qualification_credentials': 'none'},
        'FIXED_WORKER': {'identity': 'per-capability exact binding; OS anchor unresolved', 'arbitrary_input': 'deny'},
        'V2_OUTCOME_VERIFIER': {'uid': 10006, 'SQL': 'read only; exact entitlement NOT_PROVEN', 'independent_from_mutator': True}},
    'transitions': [{'id':t['id'], 'authority':t['authority'], 'precondition':t['precondition']} for t in transitions],
    'authority_is_design_not_installed_permission': True, 'complete': False})
crashes = []
for state in states:
    crashes.append({'crash_at': state, 'eligibility_after_restart': 'DENY',
        'recovery_state': 'MUTATION_UNKNOWN' if state in ['MUTATION_IN_FLIGHT','MUTATION_COMMITTED'] else 'BLOCKED',
        'required_proof': 'Recover durable lease/state/operation tuple and independently reconcile outcome, revocation, descendants, backends, prepared xacts, audit and generation. Never infer rollback from process death.',
        'resend_policy': 'No blind replay; exact same operation tuple yields retained receipt only. Same id/different digest denied. Unknown stays denied.',
        'before_mutation': 'Known no-commit only after independent pre-state and transaction-absence proof',
        'after_commit_before_ack': 'Retained transaction outcome plus exact post-state -> MUTATION_COMMITTED; otherwise UNKNOWN'})
save('closed-epoch-crash-matrix.json', {'status':'DESIGNED', 'cases':crashes})
save('closed-epoch-reseal-invariants.json', {'status':'DESIGNED', 'required':invariants,
    'known_true_required':True, 'all_old_endpoints_scope':['broker','worker channel','database backend','consumer session','native enrollment','guard cache','external event writer'],
    'extinction_scope':['process pidfd','descendant cgroup','backend PID/start identity','open inherited descriptors','credential','socket','prepared transaction'],
    'non_operational_reseal':'SEALED_NEW_EPOCH describes a TEST contract state; does not declare READY or currentness qualified.',
    'physical_evidence_bindings_complete':False})
save('closed-epoch-role-admin-contract.json', {'status':'DESIGNED', 'selected_path':'CLOSED_EPOCH_BOOTSTRAP_ONLY',
    'persistent_live_CREATEROLE_actor':'FORBIDDEN', 'available_while_SEALED':False,
    'exact_target_roles':role_targets, 'exact_allowed_operations':[t['CAPABILITY_ID'] for t in templates if t['CAPABILITY_ID'].startswith('R2/ROLE/')],
    'postgres_administration':False, 'unrelated_role_administration':False, 'create_roles':False,
    'arbitrary_membership_creation':False, 'SET_ROLE':False, 'inherited_owner_escape':False,
    'credential_policy':'Trusted deployment postgres authority cannot be made SQL-target-scoped by assertion. Its process/input/transport confinement is an explicit unproved bootstrap trust-boundary obligation; never deliver it to qualification actors.',
    'activation':'Only after UNSEALED invalidation/drain receipts, operation reservation and exact precondition digest',
    'revocation':'Before reseal: revoke authority, close sockets and descriptors, terminate backend, verify no prepared xact, independently prove process/descendant extinction',
    'exact_executor_containment':'NOT_PROVEN', 'prior_broad_CREATEROLE_counterexample_preserved':True})
save('role-admin-lifecycle-proof.json', {'status':'DESIGNED', 'model':'closed-epoch-state-machine.json',
    'required_path':['UNSEALED','CAPABILITY_ACTIVATING','ACTIVE','MUTATION_IN_FLIGHT','MUTATION_COMMITTED','CAPABILITY_REVOKING','WORKER_EXTINCTION_PENDING','RESEAL_PENDING','SEALED_NEW_EPOCH'],
    'proof_scope':'Abstract transition/guard safety only; neither physical extinction nor scoped bootstrap authority is statically established.',
    'old_endpoint_survival':'Every endpoint must check exact epoch/generation and independent current ledger; enumeration and transport implementation unresolved',
    'proof_status':'NOT_PROVEN'})
save('role-admin-unknown-outcome-contract.json', {'status':'DESIGNED',
    'operation_identity':['epoch','generation','operation_id','capability_id','template_digest','target_digest','precondition_digest'],
    'reservation':'Durable unique operation tuple before worker authority; conflicting digest always deny',
    'replay':'Known terminal exact tuple returns immutable receipt, never re-executes. No terminal proof -> reconcile; no new id to bypass UNKNOWN.',
    'crash_before_mutation':'Deny until independent no-commit + exact pre-state proof; then revoke and extinguish',
    'commit_before_ack':'Independent transaction identity + exact post-state + durable audit reconcile committed; ACK loss never implies rollback',
    'partial_delta':'BLOCKED; no reversal or reseal without separately exact governed operation',
    'audit_loss':'BLOCKED even if SQL state appears correct', 'UNKNOWN_can_reseal':False,
    'physical_outcome_reader':'NOT_PROVEN'})

native = read(SRC, 'native-proof-v6.json')['participants']
native_contracts = []
for n in native:
    native_contracts.append({'PARTICIPANT_ID':n['PARTICIPANT_NAME'], 'EXPECTED_BINARY_OR_MODULE':None,
        'MODULE_DIGEST_OR_BINDING_RULE':None, 'PROCESS_IDENTITY_RULE':n['IDENTITY_BINDING'],
        'PARENT_CHILD_RELATIONSHIP':None, 'WORK_FUNCTION':None, 'WORK_ANCHOR':None,
        'FUNCTIONAL_WORK_WITNESS':n['COMPLETED_WORK_WITNESS'], 'DEPENDENCY_BINDING':None,
        'CATALOG_BINDING':None, 'GENERATION_BINDING':n['GENERATION_BINDING'],
        'FRESHNESS_BINDING':n['LIVENESS_SOURCE'], 'RESTART_RULE':n['RESTART_BEHAVIOR'],
        'REPLACEMENT_RULE':n['GENERATION_INVALIDATED_WHEN'],
        'ALTERNATE_MODULE_RULE':'DENY until independently approved exact equivalence contract',
        'FAIL_CLOSED_RULE':n['FAIL_CLOSED_ACTION'], 'status':'NOT_PROVEN',
        'source':binding(SRC/'native-proof-v6.json','/participants/'+str(native.index(n))),
        'gap':'Semantic expected witness is specified, but concrete seven functional module/work/dependency/parent bindings are not supplied by the frozen B01 candidate.'})
save('native-seven-participant-contract.json', {'status':'NOT_PROVEN', 'participants':native_contracts,
    'NATIVE_PARTICIPANTS_REQUIRED':7, 'NATIVE_PARTICIPANTS_FULLY_BOUND':0,
    'UNRESOLVED_NATIVE_WORK_ANCHORS':7, 'GENERIC_PROCESS_SUBSTITUTIONS':0,
    'single_historical_B01_participant_reused_as_proof':False})
save('native-work-anchor-map.json', {'status':'NOT_PROVEN', 'anchors':[{'PARTICIPANT_ID':n['PARTICIPANT_ID'],
    'WORK_ANCHOR':n['WORK_ANCHOR'], 'required_witness':n['FUNCTIONAL_WORK_WITNESS']} for n in native_contracts],
    'probe_source':binding(ROOT/'scripts/validation/package_0090_s04_native_health.c',''),
    'probe_is_not_full_mapping':True})
save('native-alternate-module-contract.json', {'status':'NOT_PROVEN', 'approved_alternates':[],
    'default_rule':'DENY', 'required_equivalence':['exact source and artifact digest','immutable exact staging location',
        'original work function and challenge context','independent witness','process ancestry and pidfd','dependency/catalog lineage',
        'same observer/freshness/epoch/generation invalidation semantics','no extra authority or alternate command/path interface'],
    'does_not_prove':['original production binary identity','seven real functional participant witnesses','currentness','100us timing'],
    'generic_TEST_process_acceptable':False})
save('consumer-session-contract-v2.json', {'status':'DESIGNED', 'authenticated_identity':'test_0090_audit',
    'continuity':['same connection object','same server PID and backend start identity','same session incarnation','same authenticated session_user'],
    'identity_source':'Authenticated handshake + independently observed server facts; never adopted helper session or caller-supplied PID',
    'allowed_settings':{'timezone':['UTC','Etc/UTC'], 'effective_role':['test_0090_audit'],
        'client_encoding':['UTF8'], 'standard_conforming_strings':['on'], 'search_path':['pg_catalog, pg_temp'], 'transaction_isolation':['read committed']},
    'literal_timezone_templates':['R2/SESSION/TIMEZONE/0','R2/SESSION/TIMEZONE/1'],
    'other_setting_executable_templates':'NOT_PROVEN', 'forbidden':['SET SESSION AUTHORIZATION','SET ROLE to any other identity','owner/admin membership','helper-session substitution'],
    'transaction_isolation_rule':'Only before first transactional query; otherwise deny',
    'reconnect':'Invalidate old session, epoch and generation; discard connection-local handles only, retain durable pending operation and UNKNOWN outcome for independent reconciliation; independently enroll new connection under new tuple only after old outcome reconciles. Never resume old capability.',
    'epoch_protocol':'Invalidate eligibility before exact session change; changes observed on same authenticated connection. Reconnect drains old backend before replacement admission.',
    'complete':False, 'no_new_live_proof':True})
save('b01-fixture-correction-plan.json', {'status':'DESIGNED',
    'MANIFEST_COMPATIBILITY_DECISION':'C. B01_FIXTURE_MUST_CHANGE', 'v6_remains_canonical':True,
    'steps':[{'order':1,'action':'Freeze v6, canonical source and exact original wrapper-slot recipe before building any future fixture'},
        {'order':2,'action':'Remove V1 private Package-owner membership path entirely; do not replace it with SET ROLE, inheritance, SECURITY DEFINER or overlay waiver'},
        {'order':3,'action':'Restore only intended auditor EXECUTE on exact source wrapper signature public.offline_read_history(uuid,bytea,uuid,text); preserve raw public.flyway_schema_history SELECT denial'},
        {'order':4,'action':'Independently derive complete ACL/ownership/default/membership expectations from v6 and source before observing fixture'},
        {'order':5,'action':'Validate zero incoming/outgoing ADMIN owner memberships, exact wrapper slots, raw-history denial, no unintended grants and no READY rows'},
        {'order':6,'action':'Any TEST-only ledger/principal overlay must be disjoint from canonical truth; reject collisions and canonical waivers'}],
    'correction_implemented':False, 'complete_static_plan':True,
    'authorization':'Future tranche only after full static PASS; current tranche installs nothing'})
save('manifest-compatibility-revalidation.json', {'status':'STATICALLY_PROVEN',
    'scope':'Preservation of committed compatibility decision and v6 bytes only; corrected fixture not installed or requalified',
    'MANIFEST_COMPATIBILITY_DECISION':old['manifest-compatibility-decision.json']['MANIFEST_COMPATIBILITY_DECISION'],
    'v6_git_sha256':frozen[(SRC/'expected-currentness-manifest-v6.json').relative_to(ROOT).as_posix()],
    'canonical_owner_membership_expectation':{'incoming':0,'outgoing':0},
    'observed_fixture_used_to_derive_expected_truth':False, 'overlay_can_waive_canonical_truth':False,
    'corrected_fixture_qualified':False, 'authority':old['manifest-compatibility-decision.json']['source_authority']})

# Graph edges deliberately expose proof holes. Proposed labels do not certify containment.
authority_edges = []
for row in class_ledger:
    kind = row['CLASS'].split('/')[-1]
    trust = kind in ['native_ELF','native_locale','native_module','provider_ABI','expected_release','native_anchor','role_superuser']
    authority_edges.append({'class':row['CLASS'], 'source_objects':row['frozen_graph_objects'],
        'proposed_classification':'TRUST_BOUNDARY_ONLY' if trust else ('BROKER_MEDIATED_TYPED' if kind == 'session_environment' else 'CLOSED_EPOCH_REPLACEMENT_ONLY'),
        'classification_proven':False, 'reachable_mutation_edges_exhaustive':False,
        'trusted_boundary':'HOST_PLATFORM/root/release/deployment postgres' if trust else None,
        'outside_protection_claim_reason':'Compromise of independently trusted host/release/bootstrap control is excluded; its availability, identity and lineage must still be witnessed; never granted to active qualification actors.' if trust else None})
save('authority-graph-v2-r2.json', {'status':'NOT_PROVEN', 'class_obligations':authority_edges,
    'exact_constraint_edges':[{'mechanism_id':m['MECHANISM_ID'],'capability':m['REPRESENTATIVE_OPERATION'],
        'proposed_classification':'CLOSED_EPOCH_REPLACEMENT_ONLY','containment_proven':False} for m in mechanisms],
    'all_reachable_mutation_edges':None, 'UNCLASSIFIED_MUTATION_EDGES':None,
    'UNMEDIATED_ACTIVE_MUTATION_EDGES':None, 'RAW_AUTHORITY_SURFACE':'NOT_PROVEN',
    'host_root_release_authority_hidden':False,
    'bootstrap_risk':'An exact SQL string does not narrow postgres authority. Immutable executor/credential/OS/descriptor containment and exhaustive actor paths are not proven.'})

# Static model checks: all invariant valuations, unknown evidence, all state pairs.
checks = []


def check(name, value, detail):
    checks.append({'name':name, 'passed':bool(value), 'evidence':detail})
    assert value, name


reseal = next(t for t in transitions if t['to'] == 'SEALED_NEW_EPOCH')
for bits in itertools.product([False, True], repeat=7):
    obs = dict(zip(invariants,bits))
    admitted = all(obs[g] is True for g in reseal['precondition'])
    assert admitted == all(bits)
check('reseal_requires_all_seven_invariants', True, '128 boolean valuations; exactly one admits reseal')
for field in invariants:
    obs = dict.fromkeys(invariants, True); obs[field] = None
    assert not all(obs[g] is True for g in reseal['precondition'])
check('unknown_invariant_never_reseals', True, 'Each invariant independently replaced by unknown/null')
check('no_unknown_direct_reseal', ('MUTATION_UNKNOWN','SEALED_NEW_EPOCH') not in legal and ('MUTATION_UNKNOWN','RESEAL_PENDING') not in legal, 'actual transition relation')
check('no_active_direct_reseal', all((s,'SEALED_NEW_EPOCH') not in legal for s in states if s != 'RESEAL_PENDING'), 'all 14 source states')
check('all_states_have_fail_closed_transition', all((s,'BLOCKED') in legal for s in states if s != 'BLOCKED'), 'actual transition relation')
check('fixed_templates_have_no_runtime_parameters', all(t['caller_parameters'] == [] for t in templates), 'partial generated literal template subset only')
check('no_role_target_substitution', all(t['literal'].startswith('ALTER ROLE "test_0090_') for t in templates if t['CAPABILITY_ID'].startswith('R2/ROLE/')), 'exact role templates')
check('no_postgres_role_administration', all('ALTER ROLE "postgres"' not in t['literal'] for t in templates), 'does not prove bootstrap credential containment')
check('constraint_subtypes_remain_distinct', set(names.values()) == {m['mechanism_kind'] for m in mechanisms}, 'five exact source subtypes; no mechanism equivalence asserted')
check('exact_constraint_targets_resolve', all(m['PHYSICAL_TARGET']['relation'] and (m['PHYSICAL_TARGET']['constraint'] or m['PHYSICAL_TARGET']['column']) for m in mechanisms), '233 source rows')
check('partial_template_principal_outcome_ids_bijective', len({c['CAPABILITY_ID'] for c in contracts}) == len(contracts) and all({r['CAPABILITY_ID'] for r in rows} == {c['CAPABILITY_ID'] for c in contracts} for rows in [templates,principals,outcomes]), 'partial set, not total required capability count')
check('all_46_class_obligations_retained', len(class_ledger)==46 and {c['CLASS'] for c in class_ledger}=={c['CLASS_ID'] for c in classes}, 'inventory retained, closure NOT_PROVEN')
check('native_unknowns_preserved', len(native_contracts)==7 and all(n['WORK_ANCHOR'] is None for n in native_contracts), 'zero generic-process substitutions')
check('manifest_decision_preserved', old['manifest-compatibility-decision.json']['MANIFEST_COMPATIBILITY_DECISION']=='C. B01_FIXTURE_MUST_CHANGE', 'committed decision')
check('canonical_V043_digest_crc_fence', sha(vb)==VHASH and crc==1279591798 and fence, 'Git source bytes only; never executed')
check('prior_four_negative_findings_preserved', {f['id'] for f in old['findings.json']['blockers']} == {'V2-PARTITIONS','V2-TEMPLATES','V2-EPOCH','V2-NATIVE'}, 'negative findings remain open')
save('tests.json', {'status':'STATICALLY_PROVEN','scope':'Offline contract consistency and abstract model checks; no SQL parsing/execution or privileged runtime qualification',
    'tests_distinct':len(checks),'test_failures':0,'checks':checks,
    'model_valuation_executions':135,'static_safety_checks_do_not_prove_physical_executor':True})
save('source-integrity.json', {'status':'STATICALLY_PROVEN', 'input_git_hashes':frozen,
    'migrations':{p.relative_to(ROOT).as_posix():sha(git('show',BASE+':'+p.relative_to(ROOT).as_posix())) for p in migrations},
    'protected_refs':protected,'CURRENT_V043_GIT_LF_SHA256':VHASH,'Flyway_signed_CRC32':crc,
    'V043_FENCE_PRESENT':True,'CANONICAL_V043_MUTATED':False,'CANONICAL_V043_EXECUTED':False,
    'SHARED_DB_CONTACTED':False,'PRODUCTION_CONTACTED':False,'runtime_commands_executed':[],
    'previous_evidence_modified':False,'manifest_v6_modified':False,'privileged_fixture_installed':False})
save('findings.json', {'blocker_count':4,'high_count':0,'medium_count':0,'low_count':0,
    'blockers':[{'id':'V2-PARTITIONS','status':'OPEN','finding':'46 classes retained and 233 exact constraint removals separated, but complete source-to-physical-target reachable mutation coverage, ACL/ownership/default equivalence and representative adequacy remain unproved.'},
        {'id':'V2-TEMPLATES','status':'OPEN','finding':'243 literal partial contracts have static SQL principals; complete required capability denominator, physical observer entitlement and OS/credential authority containment remain unproved. No arbitrary-input API is authorized.'},
        {'id':'V2-EPOCH','status':'OPEN','finding':'14-state model, guards, crash matrix and seven reseal invariants specified and checked abstractly. Exhaustive physical endpoint fencing, bootstrap confinement, independent durable outcome authority and extinction bindings remain unproved; runtime evidence is not required for static design but cannot be replaced by logical labels.'},
        {'id':'V2-NATIVE','status':'OPEN','finding':'All seven semantic expectations retained. Exact participant binaries/functions/parents/dependencies/work anchors and approved alternate equivalence absent; historical probe processes are insufficient.'}],
    'prior_negative_findings':old['findings.json'],
    'residual_prior_hygiene':'Anonymous-volume provenance MEDIUM remains outside these four closure blockers, unchanged. No pruning or runtime action.'})
save('STATIC-GATE.json', {'STATIC_GATE':'BLOCKED', 'ALL_46_CLASSES_PARTITIONED':'NOT_PROVEN',
    'ALL_REACHABLE_MECHANISMS_PARTITIONED':'NOT_PROVEN','COMPOUND_MECHANISMS_REFINED':'PARTIAL',
    'CLASSES_REQUIRED':46,'CLASSES_FULLY_PARTITIONED':0,'MECHANISMS_TOTAL':None,'NULL_PHYSICAL_TARGETS':None,
    'UNJUSTIFIED_REPRESENTATIVE_COLLAPSES':None,'CAPABILITY_CONTRACT_COMPLETE':'NOT_PROVEN',
    'REQUIRED_TYPED_CAPABILITIES':None,'FIXED_OPERATION_TEMPLATES':len(templates),
    'EXACT_PRINCIPAL_BINDINGS':0,'PARTIAL_EXACT_SQL_PRINCIPAL_BINDINGS':len(principals),'OUTCOME_BINDINGS':0,
    'ALL_REQUIRED_CAPABILITIES_FIXED_TEMPLATE':'NOT_PROVEN','ALL_REQUIRED_CAPABILITIES_EXACT_PRINCIPAL':'NOT_PROVEN',
    'ALL_REQUIRED_CAPABILITIES_OUTCOME_BOUND':'NOT_PROVEN','RAW_AUTHORITY_SURFACE':'NOT_PROVEN',
    'ROLE_ADMIN_CLOSED_EPOCH_CONTRACT_COMPLETE':'NOT_PROVEN','CLOSED_EPOCH_STATE_MACHINE_COMPLETE':'NOT_PROVEN',
    'UNKNOWN_OUTCOME_CONTRACT_COMPLETE':'NOT_PROVEN','NATIVE_PARTICIPANTS_REQUIRED':7,
    'NATIVE_PARTICIPANTS_FULLY_BOUND':0,'UNRESOLVED_NATIVE_WORK_ANCHORS':7,'GENERIC_PROCESS_SUBSTITUTIONS':0,
    'FINAL_CONSUMER_SESSION_CONTRACT_COMPLETE':'NOT_PROVEN',
    'MANIFEST_COMPATIBILITY_DECISION':'C. B01_FIXTURE_MUST_CHANGE','FIXTURE_CORRECTION_PLAN_COMPLETE':'YES',
    'AUTHORITY_GRAPH_COMPLETE':'NOT_PROVEN','UNCLASSIFIED_MUTATION_EDGES':None,'UNMEDIATED_ACTIVE_MUTATION_EDGES':None,
    'STATIC_ADVERSARIAL_REVIEW':'PENDING_INDEPENDENT_REVIEW','LEAST_PRIVILEGE_REVIEW':'PENDING_INDEPENDENT_REVIEW',
    'BLOCKER_COUNT':4,'HIGH_COUNT':0,'MEDIUM_COUNT':0,'LOW_COUNT':0,
    'CURRENTNESS_MUTATION_CLASSES_PROVEN':0,'CURRENTNESS_MUTATION_CLASSES_UNPROVEN':46,
    'B02_CURRENTNESS_INTEGRATION_GATE':'NOT_RERUN','COMPLETE_CURRENTNESS_GATE':'FAIL_NOT_RERUN',
    'TESTS_DISTINCT':len(checks),'TEST_FAILURES':0,'NEXT_EXECUTED':False,
    'completion':'PARTIAL_STATIC_DESIGN_WITH_BLOCKED_GATE; requested static closure not achieved',
    'evidence_levels':{'DESIGNED':'Proposed contracts only','STATICALLY_PROVEN':'Only explicitly scoped source/model/consistency assertions',
        'LIVE_PROVEN':'No new live proof in this tranche','NOT_PROVEN':'Open or unknown; never PASS/zero'}})
print(json.dumps({'contracts':len(contracts),'mechanisms':len(mechanisms),'tests':len(checks),'STATIC_GATE':'BLOCKED'}))
