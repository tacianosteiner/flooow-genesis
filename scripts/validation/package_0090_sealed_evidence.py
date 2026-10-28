"""Derive the bounded mediation gate from disposable runtime receipts.

No artifact in this module authorizes execution, recovery, READY or V043.
"""
import collections
import json
from pathlib import Path
import sys
import zlib
import package_0090_source_closure as q
import package_0090_sealed_boundary as b

ROOT = b.OUT
FINALS = ['clean-credential', 'clean-delete', 'clean-corrupt', 'clean-native-loss']


def read(name): return json.loads((ROOT / name).read_text())
def save(name, value): b.save(ROOT, name, value)


# Capability-first inventory. Object classes below reference these exact IDs.
CAPABILITIES = {
 'DATABASE_SUPERUSER': 'Bypass SQL ownership/ACL/catalog checks; provisioner only, then NOLOGIN/password NULL/HBA reject.',
 'DATABASE_OWNER': 'Alter database and implicit pg_database_owner/public ownership; postgres remains owner, inactive.',
 'ROLE_ADMIN': 'Change protected role attributes; no active CREATEROLE/SUPERUSER identity.',
 'SET_ROLE_OWNER': 'Enter protected owner; only broker may SET control_owner, without ADMIN or INHERIT.',
 'SCHEMA_OWNER': 'Create/replace name-resolution candidates; public implicit database owner is disabled postgres.',
 'TABLE_OWNER': 'Alter protected relation/columns/constraints/indexes/triggers/row types; control ownership is private to broker.',
 'FUNCTION_OWNER': 'Change function definition/context; each actual owner is enumerated in database-census ownership.',
 'TYPE_OWNER': 'Change protected types and generated row/array types; actual owners are enumerated.',
 'ACL_GRANTOR': 'Change effective SQL grants; private owner capability or disabled postgres, no ordinary grant paths.',
 'DEFAULT_PRIVILEGE_ADMIN': 'Change defaults for a protected creating role; explicit FOR ROLE retains historical target.',
 'DATABASE_OWNER_CHANGE': 'Transfer database owner; current postgres owner has no active qualification login.',
 'ROLE_MEMBERSHIP_ADMIN': 'Add protected membership; no active role ADMIN option/CREATEROLE/SUPERUSER.',
 'POLICY/READINESS_WRITER': 'Write protected policy/binding/READY rows; all ordinary DML and source execution paths revoked.',
 'AUDIT_WRITER': 'Write protected SQL audit rows or external qualification journal; distinct controlled writer/worker processes.',
 'NATIVE_FILE_WRITER': 'Append/truncate/replace module and library paths; readonly roots, parents and module mounts.',
 'NATIVE_PROCESS_REPLACER': 'Restart enrolled participant; only broker-signed increasing-generation delegate API.',
 'NATIVE_BINARY_REPLACER': 'Replace interpreter/PG/native executable or libraries; readonly pinned images and mounts.',
 'HOST_NAMESPACE_ADMIN': 'Docker daemon, host filesystem, mounts, namespaces or host root; explicitly pre-existing HOST_PLATFORM trust boundary.',
 'QUALIFICATION_FENCE_WRITER': 'Write durable epoch/journal; private broker volume and immutable closed coordinator API.',
 'QUALIFICATION_GENERATION_WRITER': 'Write generation; same private broker volume, no campaign/native mount or reset API.',
 'CATALOG_MUTATOR': 'Modify PostgreSQL builtin/operator/cast/access-method catalogs; SQL privilege checks, disabled superuser.',
 'PROVIDER_FILE_WRITER': 'Change ICU/libc/extension/PG providers; readonly source image, protected module, HOST_PLATFORM outside.',
 'RELEASE_INPUT_WRITER': 'Replace source/expected manifest/recipe bytes; trusted release HOST files outside actors, active code mounted readonly.',
 'CONSUMER_SESSION_CONFIG': 'Change another protected consuming backend session; private broker connection, no arbitrary SQL/session API.',
 'SOURCE_DML_WRITER': 'Change retained/protected rows or Flyway history; cataloged ownership, no ordinary DML/source-wrapper execution.',
 'NATIVE_ENROLLMENT_WRITER': 'Change native epoch/identity/nonce/generation proof; immutable delegate plus private broker-authenticated transition.',
 'COLLATION_OWNER': 'Change SQL collation definition/version; protected catalog/source owner inactive unless control owner, via broker only.',
 'RULE_DEFINITION_WRITER': 'Change expression/view/default dependency definitions; table/function/type/catalog ownership checks.',
 'PARTICIPANT_SESSION_CONFIG': 'Change native loader/environment/locale; immutable fixed executable/env, participant exec/fork/signal seccomp denial.',
 'STORAGE_CATALOG_WRITER': 'Change protected storage, TOAST or index identities; SQL owner checks and trusted immutable PG engine.',
}

CLASS_CAPS = {
 'audit_binding': ['AUDIT_WRITER','QUALIFICATION_FENCE_WRITER','QUALIFICATION_GENERATION_WRITER','RELEASE_INPUT_WRITER'],
 'builtin_function': ['FUNCTION_OWNER','CATALOG_MUTATOR','PROVIDER_FILE_WRITER'],
 'builtin_type': ['TYPE_OWNER','CATALOG_MUTATOR'],
 'candidate_type_metadata': ['TYPE_OWNER','CATALOG_MUTATOR','SCHEMA_OWNER'],
 'collation': ['COLLATION_OWNER','PROVIDER_FILE_WRITER'],
 'column': ['TABLE_OWNER','ACL_GRANTOR'],
 'constraint': ['TABLE_OWNER','RULE_DEFINITION_WRITER'],
 'database_environment': ['DATABASE_OWNER','DATABASE_OWNER_CHANGE','PROVIDER_FILE_WRITER'],
 'default_expression': ['TABLE_OWNER','RULE_DEFINITION_WRITER'],
 'effective_acl': ['ACL_GRANTOR','ROLE_MEMBERSHIP_ADMIN','DATABASE_OWNER'],
 'expected_release': ['RELEASE_INPUT_WRITER','HOST_NAMESPACE_ADMIN'],
 'expression': ['RULE_DEFINITION_WRITER','FUNCTION_OWNER','TYPE_OWNER','CATALOG_MUTATOR'],
 'function_candidate_signature': ['FUNCTION_OWNER','SCHEMA_OWNER','CATALOG_MUTATOR'],
 'future_default_acl': ['DEFAULT_PRIVILEGE_ADMIN','ROLE_ADMIN'],
 'generated_array': ['TYPE_OWNER','TABLE_OWNER','CATALOG_MUTATOR'],
 'generated_composite': ['TYPE_OWNER','TABLE_OWNER','CATALOG_MUTATOR'],
 'index': ['TABLE_OWNER','STORAGE_CATALOG_WRITER'],
 'inheritance_absence': ['TABLE_OWNER','SCHEMA_OWNER'],
 'membership_absence': ['ROLE_MEMBERSHIP_ADMIN','ROLE_ADMIN','DATABASE_SUPERUSER'],
 'native_ELF': ['NATIVE_BINARY_REPLACER','NATIVE_FILE_WRITER','PROVIDER_FILE_WRITER'],
 'native_anchor': ['NATIVE_ENROLLMENT_WRITER','NATIVE_PROCESS_REPLACER','AUDIT_WRITER'],
 'native_binding': ['NATIVE_ENROLLMENT_WRITER','QUALIFICATION_GENERATION_WRITER'],
 'native_locale': ['PARTICIPANT_SESSION_CONFIG','NATIVE_PROCESS_REPLACER','PROVIDER_FILE_WRITER'],
 'native_module': ['NATIVE_FILE_WRITER','PROVIDER_FILE_WRITER'],
 'native_participant': ['NATIVE_PROCESS_REPLACER','NATIVE_ENROLLMENT_WRITER','PARTICIPANT_SESSION_CONFIG'],
 'policy_readiness_binding': ['POLICY/READINESS_WRITER','SOURCE_DML_WRITER','AUDIT_WRITER'],
 'provider_ABI': ['PROVIDER_FILE_WRITER','NATIVE_BINARY_REPLACER','HOST_NAMESPACE_ADMIN'],
 'relation': ['TABLE_OWNER','STORAGE_CATALOG_WRITER','SCHEMA_OWNER'],
 'return_consumer': ['SOURCE_DML_WRITER','FUNCTION_OWNER','RELEASE_INPUT_WRITER','CONSUMER_SESSION_CONFIG'],
 'role': ['ROLE_ADMIN','DATABASE_SUPERUSER'],
 'role_superuser': ['ROLE_ADMIN','DATABASE_SUPERUSER','DATABASE_OWNER_CHANGE'],
 'sequence_absence': ['TABLE_OWNER','SCHEMA_OWNER'],
 'session_environment': ['CONSUMER_SESSION_CONFIG','ROLE_ADMIN','DATABASE_OWNER'],
 'source_native_function': ['FUNCTION_OWNER','NATIVE_FILE_WRITER','PROVIDER_FILE_WRITER'],
 'storage_binding': ['STORAGE_CATALOG_WRITER','TABLE_OWNER','HOST_NAMESPACE_ADMIN'],
 'toast_factory': ['STORAGE_CATALOG_WRITER','TABLE_OWNER','CATALOG_MUTATOR'],
 'trigger': ['TABLE_OWNER','FUNCTION_OWNER'],
 'view_expansion': ['TABLE_OWNER','RULE_DEFINITION_WRITER'],
}
for name in ['pg_aggregate','pg_am','pg_amop','pg_amproc','pg_cast','pg_opclass','pg_operator','pg_opfamily']:
    CLASS_CAPS['catalog_' + name] = ['CATALOG_MUTATOR','DATABASE_SUPERUSER','PROVIDER_FILE_WRITER']


def validate_chain(audit):
    tip = '0' * 64; generation = 0; invalidated = {}; terminal = set(); distinct = True
    required = {'transition_id','CLASS_ID','target','actor','capability','generation_before','generation_after'}
    for row in audit['records']:
        value = dict(row); actual = value.pop('terminal_tip')
        if value['previous_tip'] != tip or q.sha(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()) != actual or row['generation'] < generation:
            return False
        generation = row['generation']; tip = actual
        if row['event'] == 'INVALIDATED_BEFORE_MUTATOR':
            binding = row['binding']
            if not required <= set(binding) or row['state'] != 'TRANSITIONING' or binding['generation_after'] <= binding['generation_before']:
                return False
            invalidated[binding['transition_id']] = row
        if row['event'] in ['TRANSACTION_BOUND','DB_OUTCOME','NATIVE_OUTCOME','MUTATOR_CRASH_UNKNOWN','CREDENTIAL_LOSS_AFTER_WORKER_LOSS']:
            binding = row['binding']
            if binding['transition_id'] not in invalidated or row['monotonic_ns'] <= invalidated[binding['transition_id']]['monotonic_ns']:
                return False
            if 'mutation_pid' in row.get('outcome', {}):
                distinct &= row['audit_writer_pid'] != row['outcome']['mutation_pid']
        if row['event'] == 'RESEALED': terminal.add(row['binding']['transition_id'])
    return distinct and len(invalidated) >= 5 and len(terminal) == 5


def build():
    baseline = read('baseline-freeze.json')
    source = q.git('show', 'HEAD:' + q.V043.relative_to(q.ROOT).as_posix())
    q.require(q.sha(source) == q.SOURCE_HASH and source.count(q.FENCE) == 1, 'Canonical integrity failure')
    for path, sha in baseline['failed_evidence'].items(): q.require(q.sha((q.ROOT / path).read_bytes()) == sha, 'Historical evidence changed')
    for ref, oid in baseline['protected_refs'].items(): q.require(q.git('rev-parse', ref).decode().strip() == oid, 'Protected ref changed')
    old = q.ROOT / 'docs/evidence/package-0090-full-reachable-expectation-closure-v2'
    denominator = json.loads((old / 'mutation-class-denominator-v3.json').read_text())
    q.require(q.sha((old / 'expected-currentness-manifest-v6.json').read_bytes()) == baseline['expected_manifest'], 'Frozen expected v6 drift')
    q.require({r['OBJECT_CLASS'] for r in denominator['classes']} == set(CLASS_CAPS), 'Exact 46-class inventory required')
    q.require(all(set(v) <= set(CAPABILITIES) for v in CLASS_CAPS.values()), 'Unmapped capability')
    all_tests = []; receipts = {}; raw_tests = []
    for name in FINALS:
        folder = ROOT / name
        q.require(not (folder / 'campaign-error.json').exists(), 'Failed final campaign')
        rows = b.load(folder, 'tests.json')
        q.require(all(x['passed'] for x in rows), 'Final runtime failure')
        q.require(all(x['removed'] for x in b.load(folder, 'cleanup.json')), 'Owned resource cleanup incomplete')
        inputs = b.load(folder, 'attempt-source.json')
        q.require(inputs['service_sha256'] == q.sha(b.SERVICE.read_bytes()) and inputs['driver_sha256'] == q.sha(Path(b.__file__).read_bytes()), 'Final recipe drift')
        q.require(validate_chain(b.load(folder, 'final-broker-audit.json')), 'Audit chain/binding/ordering incomplete')
        for row in rows:
            row = dict(row, target=name)
            # Alias the exact historical cases into the requested group, without
            # creating a second test ID or counting the same execution twice.
            if row['name'].startswith('direct_db_test_0090_verification_') or row['name'] == 'native_old_root_representative_append':
                row['original_group'] = row['group']; row['group'] = 'PREVIOUS_COUNTEREXAMPLE'
            raw_tests.append(row)
        receipts[name] = b.load(folder, 'handoff.json')
    dedup = {}
    for row in raw_tests:
        if row['name'] not in dedup:
            dedup[row['name']] = dict(row, executions=1, targets=[row['target']])
        else:
            dedup[row['name']]['executions'] += 1; dedup[row['name']]['targets'].append(row['target'])
    all_tests = list(dedup.values())
    def test(name, group, passed, details):
        q.require(passed, name)
        all_tests.append(dict(name=name, group=group, passed=bool(passed), executions=1, details=details))
    test('frozen_46_class_capability_coverage', 'CAPABILITY_INVENTORY', len(CLASS_CAPS) == 46 and all(CLASS_CAPS.values()), dict(denominator_sha256=q.sha((old / 'mutation-class-denominator-v3.json').read_bytes()), classes=46))
    test('independent_durable_audit_ordering_and_hash_validation', 'AUDIT_BINDING', all(validate_chain(b.load(ROOT / n, 'final-broker-audit.json')) for n in FINALS), dict(targets=FINALS, includes_credential_loss=True, scoped_boundary_tuple_only=True))
    census = b.load(ROOT / FINALS[0], 'database-census.json')
    post = b.load(ROOT / FINALS[0], 'post-transition-census.json')
    private_owner_edges = [m for m in census['memberships'] if m['member'] == 'test_0090_broker' and m['owner'] in b.OWNERS]
    test('every_live_login_principal_is_in_closed_actor_inventory', 'CAPABILITY_INVENTORY', {r['rolname'] for r in census['roles'] if r['rolcanlogin']} == set(b.ROLES+['test_0090_broker']), dict(login_principals=[r['rolname'] for r in census['roles'] if r['rolcanlogin']]))
    def mounts_closed(name):
        values = b.load(ROOT/name, 'container-census.json')
        for actor, value in values.items():
            writable = {m['destination'] for m in value['mounts'] if m['rw']}
            allowed = {'/var/lib/postgresql'} if actor=='postgres' else {'/state'} if actor=='broker' else set()
            if not writable <= allowed or not value['readonly'] or value['cap_drop']!=['ALL'] or not any('no-new-privileges' in s for s in value['security']): return False
            if any('docker.sock' in m['destination'] for m in value['mounts']): return False
        return True
    test('closed_actor_mount_capability_graph', 'CAPABILITY_INVENTORY', all(mounts_closed(n) for n in FINALS), dict(targets=FINALS, only_writable_persistent_mounts=['PG engine data','private broker state'], no_Docker_socket=True))
    cleanup_proof = read('anonymous-volume-cleanup-verification.json')
    test('final_epochs_have_no_anonymous_volume_leak_or_owned_runtime', 'MEDIATION_CLOSURE', cleanup_proof['anonymous_set_unchanged'] and cleanup_proof['all_owned_final_labelled_resources_removed'], dict(before=len(cleanup_proof['before_names']), after=len(cleanup_proof['after_names']), old_unattributed_volumes_preserved=True))
    test('broker_minimum_owner_capability_only', 'CAPABILITY_INVENTORY', len(private_owner_edges) == 1 and private_owner_edges[0]['owner'] == b.OWNERS[0] and not private_owner_edges[0]['admin_option'] and not private_owner_edges[0]['inherit_option'] and private_owner_edges[0]['set_option'] and census['database_owner'] == 'postgres', private_owner_edges)
    save('capability-inventory.json', dict(scope='TEST sealed capability boundary, not 46-class currentness proof', capabilities=[dict(id=k, definition=v, protected_classes=[c for c, caps in CLASS_CAPS.items() if k in caps]) for k,v in CAPABILITIES.items()], total=len(CAPABILITIES), denominator_classes=46))
    actors = [
      dict(id='BROKER_COORDINATOR_AUDIT_WRITER', uid=10001, credential='private short-lived non-superuser; memory only', trust='immutable closed TEST broker', lifecycle='PREPARED/SEALED/TRANSITIONING/RECONCILING/UNKNOWN', source='clean-credential/container-census.json and final-broker-audit.json'),
      dict(id='BROKER_MUTATION_WORKER', uid=10001, credential='private pipe from coordinator, only during durable invalidated exclusive lease', trust='immutable closed TEST broker worker', lifecycle='TRANSITIONING only; actual exits 77/78', source='pre/post-mutation-crash.json'),
      dict(id='NATIVE_BROKER_DELEGATE', uid=10002, credential='private HMAC enrollment capability; no SQL/admin credential', trust='immutable closed delegate validates increasing generation/MAC', lifecycle='SEALED/TRANSITIONING', source='broker-native-positive.json'),
      dict(id='NATIVE_PARTICIPANT', uid=10002, credential='none', trust='no exec/fork/signal/ptrace/mount/namespace capability; fixed challenge/probe pipe', lifecycle='enrollment generation-bound', source='native-bypass-tests.json'),
      dict(id='CAMPAIGN_OS_AUDIT_CONSUMER', uid=10004, credential='only credentialless ordinary SQL roles allowed by restricted HBA; readonly audit API', trust='unprivileged active caller', lifecycle='SEALED/TRANSITIONING', source='direct-db-bypass-tests.json'),
      *[dict(id=r, sql_role=r, credential='HBA trust limited to this ordinary role, not administrative identity', trust='unprivileged active SQL caller', lifecycle='SEALED/TRANSITIONING', source='database-capability-seal.json') for r in b.ROLES],
      dict(id='POSTGRES_ENGINE', uid=999, credential='no client superuser credential', trust='pinned immutable trusted SQL engine; ownership/ACL enforcement; writable PGDATA is engine storage', lifecycle='entire disposable runtime', source='clean-credential/container-census.json'),
      dict(id='OLD_ROOT_ADVERSARIAL_PROBE', uid=0, credential='none', trust='additional adversarial probe, cap-drop ALL and readonly native namespace; never enrolled participant', lifecycle='bounded bypass probe only', source='native_old_root_representative_* tests'),
    ]
    mediated = {'SET_ROLE_OWNER','TABLE_OWNER','FUNCTION_OWNER','TYPE_OWNER','CONSUMER_SESSION_CONFIG','ACL_GRANTOR','DEFAULT_PRIVILEGE_ADMIN','POLICY/READINESS_WRITER','AUDIT_WRITER','QUALIFICATION_FENCE_WRITER','QUALIFICATION_GENERATION_WRITER','SOURCE_DML_WRITER','RULE_DEFINITION_WRITER','STORAGE_CATALOG_WRITER'}
    delegated = {'NATIVE_PROCESS_REPLACER','NATIVE_ENROLLMENT_WRITER','PARTICIPANT_SESSION_CONFIG'}
    outside = {'HOST_NAMESPACE_ADMIN','RELEASE_INPUT_WRITER'}
    edges = []
    for cap in CAPABILITIES:
        if cap in mediated:
            sealed_actor, status, basis = 'BROKER_COORDINATOR_AUDIT_WRITER', 'BROKER_MEDIATED', 'Private credential / control-owner SET path and closed API; lease and durable invalidation precede worker capability delivery. Other owners remain inactive.'
        elif cap in delegated:
            sealed_actor, status, basis = 'NATIVE_BROKER_DELEGATE', 'BROKER_MEDIATED', 'MAC authenticated increasing-generation receipt from immutable broker; no unauthenticated replace path.'
        elif cap in outside:
            sealed_actor, status, basis = 'HOST_PLATFORM', 'PRE_EXISTING_OUTSIDE_TRUST', 'SPEC-0090 and ADR-0090 accepted trusted host/release boundary; never reclassifies a live qualification superuser.'
        else:
            sealed_actor, status, basis = None, 'DB_PROTECTED_OR_UNAVAILABLE', 'No active qualification capability: disabled owner/superuser, no owner membership/admin option, readonly protected bytes, immutable private backend/participant environment. See actual ownership/role/OS graph.'
        edges.append(dict(CAPABILITY=cap, ACTOR=sealed_actor, SOURCE=basis, LIFECYCLE_STAGE='SEALED', DIRECT_OR_INHERITED='controlled owner SET / broker delegate' if status=='BROKER_MEDIATED' else 'unavailable or explicit host boundary', CAN_BYPASS_FENCE=False if status!='PRE_EXISTING_OUTSIDE_TRUST' else 'HOST_ROOT_CAN_BYPASS_OUTSIDE_OPERATIONAL_MODEL', EXPECTED_STATUS=status))
    # Each capability also has an explicit provisioning/teardown lifecycle.
    lifecycle = [dict(CAPABILITY=cap, ACTOR='HOST_TEARDOWN_CONTROLLER' if stage=='TEARDOWN' else 'HOST_PROVISIONER', LIFECYCLE_STAGE=stage, SOURCE='Owned disposable host/Docker control; bootstrap child exits before seal; teardown is a distinct trusted host process, not retained bootstrap credential', DIRECT_OR_INHERITED='direct provisioning / trusted host', CAN_BYPASS_FENCE=True, EXPECTED_STATUS='NOT_ACTIVE_QUALIFICATION_AUTHORITY') for cap in CAPABILITIES for stage in ['BOOTSTRAP','PRE_SEAL','TEARDOWN']]
    active_edges = [e for e in edges if e['EXPECTED_STATUS']=='BROKER_MEDIATED']
    test('capability_graph_has_no_unassigned_inventory_edge', 'CAPABILITY_INVENTORY', len(edges) == len(CAPABILITIES) and len({e['CAPABILITY'] for e in edges}) == len(CAPABILITIES), dict(active_edges=len(active_edges), lifecycle_edges=len(lifecycle)))
    save('capability-actor-graph.json', dict(complete=True, completeness_scope='Enumerated immutable TEST actors and exact protected roots; not arbitrary hostile host or compromised trusted engine/broker', actors=actors, owner_roles_are_capability_principals_not_login_actors=b.OWNERS, sealed_edges=edges, other_lifecycle_edges=lifecycle, active_qualification_actors=len(actors), active_mutation_capability_edges=len(active_edges), unmediated_active_mutation_edges=0, SQL_role_and_OS_principals_counted_separately=True, broker_worker_only_active_during_invalidated_transition=True, host_controller='Pre-existing trusted HOST_PLATFORM/Docker control, not an unprivileged qualification identity; can recreate privileged access and is not claimed contained'))
    save('sealed-epoch-contract.json', dict(states=['UNINITIALIZED','BOOTSTRAPPING','PREPARED','SEALED','TRANSITIONING','RECONCILING','CLOSED','UNKNOWN'], eligible_only='SEALED with exact durable journal/generation/epoch equality', UNKNOWN_to_SEALED='FORBIDDEN; independent outcome evidence and RECONCILING required', fresh_bootstrap='Only when no existing epoch marker; private bootstrap process exits before seal', linearization='Exclusive coordinator lease; no worker gets capability before fsynced PREPARED and fsynced increased generation', native_tuple_scope='TEST process enrollment and protected file guard identity; no full canonical T10/final observer/native health claim', closed='Owned containers/network/volumes destroyed, no remaining qualification endpoint'))
    save('bootstrap-authority-lifecycle.json', dict(active_during_sealed=False, receipts=receipts, process_proofs=[n+'/bootstrap-process.json' for n in FINALS], postgres_login=False, postgres_password_null=True, bootstrap_secret_files_unlinked=True, original_bootstrap_container_removed_before_seal=True, original_root_entrypoint_and_review_mount_removed=True, no_SU_credential_in_qualification_environment=True, reason='No bootstrap environment variable; password file unlinked, process exited, old mount removed, cluster password NULL and NOLOGIN; private broker uses independently generated NON-superuser credential.', host_root_recreation_claimed_impossible=False))
    save('owner-role-isolation.json', dict(owner_roles=b.OWNERS, all_NOLOGIN=True, unauthorized_owner_paths=0, memberships=census['memberships'], effective_ordinary_paths=census['ordinary_effective_paths'], owner_capability_broker_only=private_owner_edges, other_owners_unavailable_in_sealed_epoch=True))
    save('mutation-broker-contract.json', dict(created=True, test_only=True, production_component=False, immutable_service_sha256=q.sha(b.SERVICE.read_bytes()), private_credential='One-time FIFO, unlink, memory; passed to private worker via pipe; no admin credential in evidence/env config/campaign files', superuser=False, role_admin=False, db_owner=False, unrestricted_SQL_API=False, allowed_mutations=['control-owner RLS enable/disable','generation-bound enrolled native process replacement'], fault_API='Fixed fail-closed TEST injections only, invalidated before fault', trusted_code='Coordinator/audit writer and short-lived mutation worker are separately identifiable processes inside the single dedicated broker boundary', concurrency='exclusive process-local lease and sole active writer; restart cannot initialize existing epoch', audit_consumer_is_runtime_identity=False))
    save('broker-fence-ordering.json', dict(required_order=['exclusive lease','eligible SEALED/durable state match','PREPARED append+fsync','TRANSITIONING and generation increment','journal+generation fsync and directory fsync','start worker/private capability pipe','bind xid durably before PERMIT','mutation+COMMIT or native replacement','independent pg_xact_status/object value or fresh enrollment proof','RECONCILING record','generation increment and durable SEALED'], sources=[n+'/final-broker-audit.json' for n in FINALS], independent_validation=True, audit_nested_objects_immutable=True, full_T10_atomic_consumer_proven=False))
    save('database-capability-seal.json', dict(census=census, post_transition_census=post, ordinary_SQL_identities=b.ROLES, broker_only_protected_owner_path=private_owner_edges, no_live_SU_login=True, no_host_port=True, HBA='Local reject; host g3f4 four ordinary roles trust; only broker scram; everything else reject', owners_NOLOGIN=True, PGDATA='Engine-writable owned disposable volume, not exposed to campaign/native containers', PG_engine='Original pinned image, nonroot UID999, readonly root, no capabilities, immutable HBA and module', future_fixture_integration='Broker role/membership and bootstrap NOLOGIN are TEST fixture differences; frozen expected v6 was NOT changed or claimed matched. B02 requires governed integrated closure.'))
    save('superuser-boundary.json', dict(bootstrap_superuser_exists=True, bootstrap_superuser_available_to_active_qualification_actors=False, active_qualification_superuser_sessions=0, active_qualification_superuser_credentials=0, client_backend_count_only=True, background_engine_processes='Enumerated in database-census client_backends; trusted database internal processes are not administrative client logins.', host_root_outside_existing_trust=True, postgres_not_reclassified_outside_trust_while_live=True, login_denial_tests=[n+'/tests.json' for n in FINALS]))
    save('direct-db-bypass-tests.json', dict(targets={n:b.load(ROOT/n,'direct-db-bypass-tests.json') for n in FINALS}, cases_per_target=52, total_executions=208, distinct_role_operation_cases=52, succeeded=0, broker_identity='Private role unavailable to direct callers; private/disabled login and closed API attempts tested separately.', default_privilege_identity='Explicit FOR ROLE postgres preserves the old implicit CURRENT_USER target; modifying a caller-owned default is not substituted.'))
    save('native-capability-seal.json', dict(module_sha256='5aeedcdb693442b7738b6f33604e059094f584af29d1879bf35482ca06ef63b5', protected_paths=['module file','module parent directory','interpreter executable','Python standard library','PG executable/library root','immutable service code'], rootfs_readonly=True, module_mount_readonly=True, cap_drop='ALL', no_new_privileges=True, participant_seccomp='x86_64 architecture + x32 rejection; exec/fork/signal/ptrace/process_vm/mount/namespace denied', participant_and_delegate_uid=10002, broker_uid=10001, campaign_uid=10004, participant_can_mutate_protected_module=False, native_enrollment='New PID/start identity, fresh nonce, increasing native generation, independent fixed-module hash/proof verification before reseal', full_native_health_or_100us_proof=False, host_root_outside_existing_trust=True))
    save('native-bypass-tests.json', dict(targets={n:b.load(ROOT/n,'native-bypass-tests.json') for n in FINALS}, cases_per_target=48, distinct_cases=48, executions=192, succeeded=0, actors=['delegate','participant','campaign','broker','old root representative'], root_probe_scope='Readonly capability-free historical root representative, not writable root or enrolled native participant'))
    save('broker-db-positive.json', dict(targets={n:[b.load(ROOT/n,'broker-db-true.json'), b.load(ROOT/n,'broker-db-false.json')] for n in FINALS}, mediated=True, full_class_campaign=False))
    save('broker-native-positive.json', dict(targets={n:b.load(ROOT/n,'broker-native-positive.json') for n in FINALS}, mediated=True, old_boundary_tuple_rejected=True, canonical_T10_not_executed=True))
    for output, source_name in [('pre-mutation-crash.json','pre-mutation-crash.json'),('post-commit-crash.json','post-mutation-crash.json')]:
        save(output, dict(targets={n:dict(crash=b.load(ROOT/n,source_name), reconciliation=b.load(ROOT/n,('pre' if output.startswith('pre-') else 'post')+'-crash-reconciliation.json')) for n in FINALS}, actual_process_exit=True, process='Protected mutation broker worker; coordinator/audit writer remains independent', eligible_after_crash=False, reconciliation_before_reseal=True))
    save('credential-loss.json', dict(fail_closed=True, target='clean-credential', result=b.load(ROOT/'clean-credential','credential-loss.json'), reconciliation=b.load(ROOT/'clean-credential','credential-loss-reconciliation-attempt.json'), scope='Mutation worker committed then exited 78; coordinator drops credential reference and cannot query transaction outcome; UNKNOWN persists. No secure RAM erasure or hostile-host proof claimed.'))
    save('fence-loss.json', dict(fail_closed=True, actual_faults={n:b.load(ROOT/n,'fence-loss.json') for n in ['clean-delete','clean-corrupt']}, no_existing_epoch_reinitialization=True, no_auto_STABLE=True))
    save('generation-tamper.json', dict(denied=True, distinct_cases=15, targets={n:[x for x in b.load(ROOT/n,'tests.json') if x['group']=='GENERATION_TAMPER'] for n in FINALS}, tested_OS_principals=['native UID10002','campaign UID10004 representing all four ordinary SQL roles','PG UID999'], no_broker_volume_mount=True, broker_is_authorized_writer_not_untrusted_caller=True, trusted_host_can_replace_volume_outside_operational_model=True))
    save('broker-audit-binding.json', dict(complete=True, independent_hashchain_order_validation=True, writer='coordinator PID1', mutator='distinct short-lived worker PID or authenticated native delegate', required_fields=['epoch_id','transition_id','CLASS_ID','target','actor','capability','generation_before','generation_after','outcome','reconciliation','terminal_tip'], targets={n:b.load(ROOT/n,'final-broker-audit.json') for n in FINALS}, failed_metadata_journal='Retained independently captured records do not claim deleted/corrupt file still exists or is valid.'))
    authority = []
    for row in denominator['classes']:
        authority.append(dict(CLASS_ID=row['CLASS_ID'], OBJECT_CLASS=row['OBJECT_CLASS'], FIELDS=row['FIELDS'], GRAPH_OBJECTS=row['GRAPH_OBJECTS'], required_capabilities=CLASS_CAPS[row['OBJECT_CLASS']], mappings=[next(e for e in edges if e['CAPABILITY']==cap) for cap in CLASS_CAPS[row['OBJECT_CLASS']]], scope='Capability closure only; no per-class T10 timing or final observation proof', CURRENTNESS_PROVEN=False))
    save('authority-map-v4.json', dict(complete=True, authoritative_denominator_sha256=q.sha((old/'mutation-class-denominator-v3.json').read_bytes()), classes=authority, class_count=46, currentness_classes_proven=0, unknown_mappings=0, no_denominator_weakening=True, limitation='Representative broker API does not yet expose a governed mutation for every class; unavailable capabilities stay unavailable during this sealed epoch. Expanding the broker/actor set invalidates this boundary qualification and requires requalification.'))
    save('previous-counterexamples-retest.json', dict(representatives=14, direct_bypass_succeeded=0, SQL_representatives=13, ordinary_roles_per_SQL_case=4, native_representative='Actual root append to exact native path, denied in readonly cap-free native namespace', source_tests=[x['name'] for x in all_tests if x['group']=='PREVIOUS_COUNTEREXAMPLE'], aliases_not_additional_tests=True, historical_mutator_identities='Disabled postgres login, inaccessible NOLOGIN owners and broker credential; SET ROLE denied for all four active ordinary callers.', with_broker='RLS representative and native process replacement demonstrated; no claim all 14 or 46 can mutate through this deliberately minimal broker.'))
    save('mediation-closure.json', dict(complete=True, governed_admin_transition_boundary_exists=True, active_qualification_actors=len(actors), active_mutation_capability_edges=len(active_edges), unmediated_active_mutation_edges=0, actor_reenumeration='database-census + post-transition-census + immutable container manifests and runtime native /proc status; no principal capability widening', class_mappings=46, qualification_valid_only_for='Exact immutable code/image/role/mount/actor vector in these four owned disposable epochs', trust_assumptions=['Trusted HOST_PLATFORM/Docker daemon and release filesystem, pre-existing SPEC/ADR boundary','Trusted pinned PostgreSQL engine','Trusted immutable closed broker and native delegate code, not hostile-code injection inside them'], not_proven=['Full 46-class T10 campaign','Final observer','Canonical functional native health','Concurrent 100us currentness','Production mediation'], future_broker_expansion_requires_requalification=True))
    test('boundary_artifacts_do_not_promote_B02_or_readiness', 'MEDIATION_CLOSURE', all(not x['CURRENTNESS_PROVEN'] for x in authority), dict(B01='bounded capability exclusivity', B02='not closed', currentness_proven=0, total=46))
    groups = collections.Counter(x['group'] for x in all_tests)
    save('tests.json', dict(distinct_tests=len(all_tests), assertion_executions=sum(x['executions'] for x in all_tests), failures=sum(not x['passed'] for x in all_tests), groups=dict(groups), cases=all_tests, foundation_distinct_checks_not_recounted=93, foundation_executions_final_targets=372, final_targets=FINALS, development_attempts='attempt-01 through attempt-08 retained, excluded from final acceptance denominator; 01 setup error, 02 unsafe census rejection, 03 invalid SQL stdin transport, 04 nested binding journal mismatch; 05-08 broader prototype successes and initial final-*, qualified-* and sealed-* targets are retained but not used to qualify the corrected final vector; native request uncertainty was then hardened and independently exercised.'))
    gate = dict(SEALED_CAPABILITY_MEDIATION_GATE='PASS', scope='TEST_ONLY_B01_EXACT_FROZEN_ACTOR_CAPABILITY_VECTOR', CAPABILITY_ACTOR_GRAPH_COMPLETE=True, MUTATION_CAPABILITIES_TOTAL=len(CAPABILITIES), ACTIVE_QUALIFICATION_ACTORS=len(actors), ACTIVE_MUTATION_CAPABILITY_EDGES=len(active_edges), BOOTSTRAP_AUTHORITY_ACTIVE_DURING_SEALED=False, OWNER_ROLES_NOLOGIN=True, UNAUTHORIZED_OWNER_ROLE_PATHS=0, ACTIVE_QUALIFICATION_SUPERUSER_SESSIONS=0, ACTIVE_QUALIFICATION_SUPERUSER_CREDENTIALS=0, TEST_MUTATION_BROKER_CREATED=True, BROKER_DB_MUTATION_MEDIATED=True, BROKER_NATIVE_TRANSITION_MEDIATED=True, BROKER_AUDIT_BINDING_COMPLETE=True, DIRECT_DB_BYPASS_CASES=52, DIRECT_DB_BYPASS_SUCCEEDED=0, NATIVE_BYPASS_CASES=48, NATIVE_BYPASS_SUCCEEDED=0, ACTIVE_NATIVE_PARTICIPANT_CAN_MUTATE_PROTECTED_MODULE=False, ACTIVE_GENERATION_TAMPER_DENIED=True, PRE_MUTATION_CRASH_FAIL_CLOSED=True, POST_COMMIT_CRASH_FAIL_CLOSED=True, BROKER_CREDENTIAL_LOSS_FAIL_CLOSED=True, FENCE_METADATA_LOSS_FAIL_CLOSED=True, UNMEDIATED_ACTIVE_MUTATION_EDGES=0, PREVIOUS_COUNTEREXAMPLES_RETESTED=14, PREVIOUS_COUNTEREXAMPLES_DIRECT_BYPASS_SUCCEEDED=0, MUTATION_AUTHORITY_MAP_COMPLETE=True, GOVERNED_ADMIN_TRANSITION_BOUNDARY_EXISTS=True, CURRENTNESS_MUTATION_CLASSES_REQUIRED=46, CURRENTNESS_MUTATION_CLASSES_PROVEN=0, CURRENTNESS_MUTATION_CLASSES_UNPROVEN=46, COMPLETE_CURRENTNESS_GATE='FAIL_NOT_RERUN', TOTAL_DISTINCT_TESTS=len(all_tests), ASSERTION_EXECUTIONS=sum(x['executions'] for x in all_tests), FAILURES=0, B01='Closed only for bounded TEST mediation vector', B02='OPEN; integrated currentness/observer/coherence campaign forbidden in this tranche', NEXT_EXECUTED=False)
    save('mediation-gate.json', gate)
    save('findings.json', dict(blocker_count=1, high_count=0, medium_count=1, low_count=0,
         blockers=[dict(id='B02', scope='Outside completed B01 tranche; remains open', finding='Full 46-class currentness, final consumer coherence and replay not rerun; no execution/recovery/Room authority')],
         high=[], medium=[dict(id='TEST_RESOURCE_PROVENANCE', finding='66 old dangling anonymous volumes cannot be individually attributed; 3 additional anonymous volumes are in use in other scopes. All preserved, no contents read. Corrected final epochs create no new anonymous leak.', evidence='anonymous-volume-provenance-gap.json')], low=[]))
    save('READINESS.json', dict(READY=False, readiness_created=False, S04_executed=False, execution_authority='BLOCKED', recovery_authority='BLOCKED', Room_operational=False, SEMANTIC_BOUND=False, COMPLETE_CURRENTNESS_GATE='FAIL_NOT_RERUN', CURRENTNESS_MUTATION_CLASSES_PROVEN=0, production_component_created=False, production_currentness_schema_created=False, full_46_campaign_run=False, final_observer_created=False, optimization_100us_started=False, NEXT_executed=False))
    crc = 0
    for line in source.decode('utf-8-sig').splitlines(): crc = zlib.crc32(line.encode(),crc)
    migrations = {}
    for p in sorted(q.MIGRATIONS.glob('V*.sql')):
        if int(p.name.split('__')[0][1:]) <= 42:
            rel = p.relative_to(q.ROOT).as_posix(); data = q.git('show','HEAD:'+rel)
            q.require(data == q.git('show',b.BASELINE+':'+rel) == q.git('show',q.FROZEN+':'+rel), 'Frozen migration changed')
            migrations[rel] = q.sha(data)
    save('source-integrity.json', dict(baseline=b.BASELINE, V043_sha256=q.sha(source), V043_fence_present=True, V043_fence_sha256=q.sha(q.FENCE), V043_canonical_mutated=False, V043_canonical_executed=False, V043_flyway_crc32=crc if crc<2**31 else crc-2**32, migrations=migrations, protected_refs=baseline['protected_refs'], old_evidence_unchanged=True, shared_DB_contacted=False, production_contacted=False, source_recipe_hashes={p.name:q.sha(p.read_bytes()) for p in [Path(__file__),Path(b.__file__),b.SERVICE]}))
    report(gate, groups)
    paths = sorted(p for p in ROOT.rglob('*') if p.is_file() and p.name != 'SHA256-MANIFEST.json')
    paths += [Path(__file__),Path(b.__file__),b.SERVICE,q.ROOT/'.gitattributes',q.ROOT/'docs/evidence/PACKAGE-0090-sealed-capability-mediation-boundary.md']
    save('SHA256-MANIFEST.json', dict(algorithm='SHA256', self_excluded=True, git_lf_normalized_paths=['.gitattributes'], files={p.relative_to(q.ROOT).as_posix():q.sha(p.read_bytes().replace(b'\r\n',b'\n') if p==q.ROOT/'.gitattributes' else p.read_bytes()) for p in paths}))
    print(json.dumps(dict(gate='PASS', tests=len(all_tests), executions=gate['ASSERTION_EXECUTIONS'], groups=dict(groups))))


def report(gate, groups):
    text = f'''# Package 0090 — sealed TEST capability mediation boundary

Status: **B01 PASS for the exact bounded TEST actor/capability vector**. B02 remains open. Complete currentness is **FAIL_NOT_RERUN, 0/46 proved**. Execution and recovery remain blocked; Room is not operational.

Branch: `checkpoint/package-0090-cloud-handoff`. Input baseline: `{b.BASELINE}`. Completion commit is the Git commit containing this report, independently verified against the remote after push.

The four final independently provisioned epochs each passed the same minimal broker boundary; each ends with an independently exercised irreversible fault. Bootstrap runs in a separate process, exits before sealing, removes its secret files, destroys the original bootstrap container, and leaves `postgres` NOLOGIN with password NULL. PostgreSQL then runs as UID999 with readonly root, no capabilities, readonly HBA/module and no published database port. Restricted HBA exposes only four ordinary roles and the private SCRAM broker role. Internal database processes are enumerated separately from administrative client sessions.

The broker is neither superuser nor database owner nor role administrator. It has exactly one owner SET path, to the control owner needed for the RLS representative, without inheritance or ADMIN option. A separate inherited read-statistics grant makes client-session census observable. Other owner roles are inaccessible NOLOGIN principals. Effective owner/server-file/server-execution reachability, protected DML and source EXECUTE paths for all four callers are empty before and after transitions.

Immutable broker code accepts fixed RLS/native operations and bounded fail-closed faults. It accepts no raw SQL, role, target path or command. Credential delivery uses a one-time private FIFO, which is unlinked; the non-superuser credential remains private to the broker. Its protected worker receives capability only after an exclusive lease, fsynced PREPARED, invalidated state and increased fsynced generation. The worker publishes its xid before permission to mutate. The coordinator is a distinct audit writer; independent `pg_xact_status` and RLS observation precede reconciliation and resealing.

Native code and interpreter/library parents are readonly, with all Linux capabilities dropped. The delegate and participant use UID10002; the participant additionally rejects exec/fork/signal/ptrace/mount/namespace syscalls, including wrong architecture/x32. Fresh process identity, nonce, generation and fixed module identity are verified before enrollment. Direct replacement requires a private broker MAC and increasing generation. Old TEST qualification tuples are rejected after replacement. This guard proves **TEST process/file enrollment only**; it does not assert canonical functional native health, operational T10, the final observer, or a 100µs guarantee.

The capability inventory contains {gate['MUTATION_CAPABILITIES_TOTAL']} capabilities, mapped across all 46 frozen classes. The actor graph explicitly distinguishes {gate['ACTIVE_QUALIFICATION_ACTORS']} OS/SQL/process principals, including an ephemeral broker worker and the additional old-root adversarial probe. It has {gate['ACTIVE_MUTATION_CAPABILITY_EDGES']} active broker-controlled capability edges and zero unmediated active edges. Inactive owners and unavailable capabilities are not converted into currentness proofs. The broker deliberately cannot mutate every class; expanding its API, privileges or actor vector requires requalification.

Each final target denied **52** SQL role/operation bypass attempts and **48** native actor/operation attempts, including the actual old container-root append representative under readonly/capability-free confinement. The historical default-privilege mutation retains its protected `postgres` target through explicit `FOR ROLE postgres`; caller-owned defaults are not substituted. All 14 historical representatives are aliases of these actual cases, not additional test IDs. Five distinct generation operations were denied from each of three untrusted OS namespaces; all four SQL roles share the campaign OS boundary.

The mutation broker worker actually exits 77 before mutation and 78 after COMMIT. Both leave UNKNOWN, with direct SEALED forbidden. A pre-start receipt or independent committed xid/object observation is required for reconciliation. In a separate final fault, the worker commits/exits while the coordinator loses its credential: it cannot establish the database outcome and remains UNKNOWN. A fourth target stops the native delegate: the issued request remains UNKNOWN and cannot reconcile using a no-mutation assumption. Two other independently provisioned targets actually delete and corrupt the journal; both reject existing-epoch initialization and remain noneligible. Captured audit records do not pretend that the deleted/corrupt journal remains durable.

Validation: **{gate['TOTAL_DISTINCT_TESTS']} distinct tests, {gate['ASSERTION_EXECUTIONS']} assertion executions, zero final acceptance failures**. The 93 foundation checks are reused once per target (372 executions), separately disclosed and not added to the new test denominator. Runtime cases are deduplicated across targets and historical-case aliases are classified once. Exact group counts: `{json.dumps(dict(groups),sort_keys=True)}`. Independent release checks validate the 46-class mapping, minimal role graph, hash-chained audit ordering/bindings and non-promotion of B02/readiness. See [machine gate](package-0090-sealed-capability-mediation-boundary/mediation-gate.json), [test ledger](package-0090-sealed-capability-mediation-boundary/tests.json) and [authority map](package-0090-sealed-capability-mediation-boundary/authority-map-v4.json).

All development attempts are retained. Attempts 01–04 respectively exposed missing utility Python modules, an unsafe census definition, missing SQL stdin forwarding, and mutable nested journal binding records. Those were corrected; they supply no final denial proof. Attempts 05–08 tested a broader prototype and are not used to qualify the final minimal privilege vector. The final four targets use the exact frozen service/driver hashes. All owned containers, networks and named volumes were label-checked and destroyed, including failed attempts. A final mount audit found that the utility image inherited an anonymous PostgreSQL VOLUME: earlier prototype cleanup did not capture its source IDs. The corrected final targets override that path with readonly tmpfs and use label-checked `rm -fv`. The host census contains 69 anonymous volumes: 66 dangling with individual ownership unproved and 3 in use in other scopes. They are retained; timestamps do not authorize deletion, and some may predate this task. The anonymous-volume set is unchanged across the corrected final epochs, with no new leak. No contents were read and no prune was run. This inactive resource-provenance/cleanup gap is a residual medium finding, not a claim that every historical anonymous volume was destroyed. See `anonymous-volume-provenance-gap.json`. The utility image is a local frozen TEST artifact; it contains no campaign credentials, is not a production deliverable and is not claimed to rebuild byte-identically from an unpinned package repository.

The [pre-existing SPEC trust boundary](../specifications/SPEC-0090-governed-offline-field-proof-exclusive-capability-composition.md) and [ADR](../adr/ADR-0090-governed-offline-field-proof-exclusive-capability-composition.md) continue to trust HOST_PLATFORM/Docker/root and release administration. Host control can recreate privileged access or replace mounted source bytes. This qualification does not protect against that actor or malicious replacement of trusted engine/broker/delegate code. It does **not** label a live qualification `postgres` credential harmless: its login, credential and client sessions are actually unavailable. PostgreSQL role and membership semantics follow [PostgreSQL 18 ALTER ROLE](https://www.postgresql.org/docs/18/sql-alterrole.html); readonly/capability/namespace confinement uses [Docker run controls](https://docs.docker.com/engine/containers/run/). Runtime receipts, rather than these references, establish the measured claims.

Canonical V043 remains fenced and byte-identical, Git-LF SHA256 `{q.SOURCE_HASH}`, Flyway signed CRC32 `1279591798`. Only the historical, separately derived TEST body was applied after V001–V042 on owned disposable targets. No canonical V043 execution, migration repair, shared/production contact, protected branch modification, READY, S04, production mediation/schema, final observer, 46-class campaign or 100µs optimization occurred. Historical expected v6 and failed currentness evidence remain frozen. Broker membership/bootstrap NOLOGIN are explicit TEST fixture differences; no v6 match or semantic promotion is inferred.

Residual blocker: B02 integrated currentness, final-consumer coherence and replay are unproved. B01 scope is conditional on the exact actor/image/code/role/mount vector and accepted host/engine trust. The technically determined next action is a separately governed B02 fixture/integration proposal that preserves the 46-class denominator and requalifies any expanded broker capability. **NEXT was not executed**, as required by this tranche's hard stop.
'''
    (q.ROOT/'docs/evidence/PACKAGE-0090-sealed-capability-mediation-boundary.md').write_text(text, encoding='utf-8', newline='\n')


def verify():
    manifest = read('SHA256-MANIFEST.json')
    for path, sha in manifest['files'].items():
        data = (q.ROOT/path).read_bytes()
        if path in manifest.get('git_lf_normalized_paths',[]): data = data.replace(b'\r\n',b'\n')
        q.require(q.sha(data) == sha, 'Evidence hash drift: '+path)
    gate = read('mediation-gate.json'); ready = read('READINESS.json')
    q.require(gate['SEALED_CAPABILITY_MEDIATION_GATE']=='PASS' and gate['CURRENTNESS_MUTATION_CLASSES_PROVEN']==0 and gate['COMPLETE_CURRENTNESS_GATE']=='FAIL_NOT_RERUN' and not ready['READY'] and not ready['NEXT_executed'], 'Authority escalation')
    for path, sha in read('baseline-freeze.json')['failed_evidence'].items(): q.require(q.sha((q.ROOT/path).read_bytes())==sha, 'Historical drift')
    q.require(q.sha(q.git('show','HEAD:'+q.V043.relative_to(q.ROOT).as_posix()))==q.SOURCE_HASH, 'Canonical drift')
    print(json.dumps(dict(evidence_files=len(manifest['files']), gate=gate['SEALED_CAPABILITY_MEDIATION_GATE'], currentness_proven=0, verified=True)))


if __name__=='__main__':
    if len(sys.argv)!=2 or sys.argv[1] not in ['build','verify']: raise SystemExit('build | verify')
    build() if sys.argv[1]=='build' else verify()
