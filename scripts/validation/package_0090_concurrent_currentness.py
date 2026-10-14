"""TEST_ONLY currentness counterexamples. Never grants readiness or invokes S04.

Each mutation is limited to the labelled disposable foundation and reversed.
Successful counterexamples are tests of insufficiency, not health positives.
"""
import json
import sys
from pathlib import Path
import package_0090_source_closure as q

OUT = q.ROOT / 'docs/evidence/package-0090-native-health-concurrent-100us'
BASELINE = '6eff07161cdf3a295a1e0c713f68963a626eff11'
LEGACY_QUERY = """SELECT encode(sha256(convert_to(string_agg(v,E'\n' ORDER BY k),'UTF8')),'hex') FROM (
SELECT 0 AS k,pg_postmaster_start_time()::text||version() AS v
UNION ALL SELECT installed_rank,installed_rank::text||version||type||script||checksum::text||success::text FROM public.flyway_schema_history
UNION ALL SELECT 100000+oid::int,oid::text||rolname||rolsuper::text||rolinherit::text||rolcreaterole::text||rolcreatedb::text||rolcanlogin::text||rolreplication::text||rolbypassrls::text FROM pg_roles WHERE rolname LIKE 'test_0090_%') q"""


def qualify(sql, run, container, folder, record, fixture, runtime_work):
    sys.path.insert(0, str(Path.home() / 'AppData/Local/Temp/flooow-0090-authorized-psycopg'))
    import psycopg
    details = json.loads(run(['docker', 'inspect', container]))[0]
    q.require(details['Image'] == q.IMAGE and details['Config']['Labels']['com.docker.compose.project'] == record['isolation']['project'], 'Foreign target')
    binding = details['NetworkSettings']['Ports']['5432/tcp']
    q.require(len(binding) == 1 and binding[0]['HostIp'] == '127.0.0.1', 'Nonloopback target')
    password = (Path(runtime_work) / 'postgres-password').read_text()
    kwargs = dict(host='127.0.0.1', port=int(binding[0]['HostPort']), dbname='g3f4', user='postgres', password=password, autocommit=True)
    cases = []

    def case(name, passed, evidence):
        item = dict(name=name, passed=bool(passed), evidence=evidence, group='CURRENTNESS')
        cases.append(item); record['cases'].append(item)
        q.require(passed, 'Currentness counterexample assertion: ' + name)

    with psycopg.connect(**kwargs) as observer, psycopg.connect(**kwargs) as writer:
        def digest(): return observer.execute(LEGACY_QUERY).fetchone()[0]
        initial = digest()
        role = 'test_0090_audit'
        writer.execute('ALTER ROLE test_0090_audit INHERIT')
        try:
            case('fresh_query_detects_role_attribute_change', digest() != initial, 'Current broad query sees committed INHERIT change in fresh statement')
        finally: writer.execute('ALTER ROLE test_0090_audit NOINHERIT')
        case('role_attribute_restored', digest() == initial, 'Restricted original attributes restored')
        original = observer.execute("SELECT has_table_privilege(%s,'public.flyway_schema_history','UPDATE')", (role,)).fetchone()[0]
        q.require(not original, 'Unexpected initial history writer')
        writer.execute('GRANT UPDATE ON public.flyway_schema_history TO test_0090_audit')
        try:
            changed = observer.execute("SELECT has_table_privilege(%s,'public.flyway_schema_history','UPDATE')", (role,)).fetchone()[0]
            case('legacy_digest_misses_history_write_ACL', changed and digest() == initial, 'Granted UPDATE creates actual migration-history writer; broad query digest unchanged')
        finally: writer.execute('REVOKE UPDATE ON public.flyway_schema_history FROM test_0090_audit')
        writer.execute('GRANT flooow_offline_control_owner TO test_0090_audit')
        try:
            count = observer.execute("SELECT count(*) FROM pg_auth_members WHERE member=(SELECT oid FROM pg_roles WHERE rolname=%s)", (role,)).fetchone()[0]
            case('legacy_digest_misses_role_membership', count == 1 and digest() == initial, 'Membership violates zero-membership requirement without changing role attributes/OID')
        finally: writer.execute('REVOKE flooow_offline_control_owner FROM test_0090_audit')
        owner_before = observer.execute("SELECT proowner FROM pg_proc WHERE oid='public.offline_read_history(uuid,bytea,uuid,text)'::regprocedure").fetchone()[0]
        writer.execute('ALTER FUNCTION public.offline_read_history(uuid,bytea,uuid,text) OWNER TO postgres')
        try:
            owner_after = observer.execute("SELECT proowner FROM pg_proc WHERE oid='public.offline_read_history(uuid,bytea,uuid,text)'::regprocedure").fetchone()[0]
            case('legacy_digest_misses_function_owner', owner_before != owner_after and digest() == initial, 'S04 SECURITY DEFINER owner changed, broad digest unchanged')
        finally: writer.execute('ALTER FUNCTION public.offline_read_history(uuid,bytea,uuid,text) OWNER TO flooow_offline_audit_owner')
        # Data snapshot coherence does not establish currentness at final join.
        observer.execute('BEGIN ISOLATION LEVEL REPEATABLE READ READ ONLY')
        before = digest()
        old_checksum = observer.execute('SELECT checksum FROM public.flyway_schema_history WHERE installed_rank=1').fetchone()[0]
        writer.execute('UPDATE public.flyway_schema_history SET checksum=checksum+1 WHERE installed_rank=1')
        try:
            stale = digest()
            current = writer.execute(LEGACY_QUERY).fetchone()[0]
            case('repeatable_read_coherent_but_stale_history', stale == before and current != before, 'Committed history mutation invisible to retained RR snapshot but visible to independent fresh session')
        finally:
            observer.execute('ROLLBACK')
            writer.execute('UPDATE public.flyway_schema_history SET checksum=%s WHERE installed_rank=1', (old_checksum,))
        case('history_restored_exactly', digest() == initial, 'Original checksum and complete legacy digest restored')
        # Even a fresh query leaves an unguarded observation-to-consumer gap.
        observed = digest()
        writer.execute('ALTER ROLE test_0090_audit INHERIT')
        try:
            case('fresh_observation_not_valid_through_T10', observed == initial and digest() != observed, 'Admin commits after guard query; retained query hash alone has no final-consumer invalidation')
        finally: writer.execute('ALTER ROLE test_0090_audit NOINHERIT')
        # A real SHARE lock blocks data updates until release, not arbitrary catalog changes.
        observer.execute('BEGIN')
        observer.execute('LOCK TABLE public.flyway_schema_history IN SHARE MODE')
        writer.execute("SET lock_timeout='50ms'")
        denied = False
        try: writer.execute('UPDATE public.flyway_schema_history SET checksum=checksum WHERE installed_rank=1')
        except psycopg.errors.LockNotAvailable: denied = True
        case('history_SHARE_lock_blocks_concurrent_DML', denied, '55P03 under actual lock_timeout; no checksum changed')
        writer.execute('ALTER ROLE test_0090_audit INHERIT')
        try:
            case('history_lock_does_not_guard_role_catalog', digest() != initial, 'ALTER ROLE commits while history SHARE lock retained')
        finally:
            writer.execute('ALTER ROLE test_0090_audit NOINHERIT')
            observer.execute('ROLLBACK')
        writer.execute("SET lock_timeout='0'")
        case('all_mutations_reversed', digest() == initial and not observer.execute("SELECT has_table_privilege(%s,'public.flyway_schema_history','UPDATE')", (role,)).fetchone()[0] and observer.execute("SELECT count(*) FROM pg_auth_members WHERE member=(SELECT oid FROM pg_roles WHERE rolname=%s)", (role,)).fetchone()[0] == 0, 'Original role/ACL/membership/history restored; owned target then destroyed')
        case('no_readiness_header_original', all(observer.execute('SELECT count(*) FROM public.' + table).fetchone()[0] == 0 for table in ['offline_readiness', 'offline_binding_header', 'offline_expected_signed_attestation']), 'No eligibility material fabricated')
    (folder / 'currentness-runtime.json').write_text(json.dumps(dict(cases=cases, query=LEGACY_QUERY, query_sha256=q.sha(LEGACY_QUERY.encode()), target=record['isolation'], currentness_prebinding_proven=False, snapshot_current_through_T10=False, canonical_submitted=False), indent=2) + '\n')
