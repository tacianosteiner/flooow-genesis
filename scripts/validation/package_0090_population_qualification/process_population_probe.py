"""Actual current population plus actual unsupported governed worker denial."""
import json,re,time
def run(q):
    rows=json.loads(q.sql("SELECT json_agg(json_build_object('pid',pid,'type',backend_type,'role',usename,'leader',leader_pid)) FROM pg_stat_activity;").stdout)
    known={'client backend','parallel worker','background worker','autovacuum worker','autovacuum launcher','checkpointer','background writer','walwriter','walreceiver','walsender','logical replication launcher','logical replication worker','startup','archiver','slotsync worker','walsummarizer','io worker'}
    q.case('process_population','all_current_pg_process_types_explicit',all(r['type'] in known for r in rows),rows)
    events=q.ex('cat','/tmp/full.log').stdout
    for kind in sorted({r['type'] for r in rows}):q.case('process_population','independent_census_observes_'+kind,'"type":"'+kind+'"' in events,{'classification':'OBSERVED_ONLY_INTERNAL_OR_UNMANAGED','never_grants_eligibility':True})
    settings=q.sql("SELECT json_object_agg(name,setting) FROM pg_settings WHERE name IN ('archive_mode','wal_level','hot_standby','shared_preload_libraries','max_parallel_workers');").stdout
    q.save('ACTUAL-PROCESS-CONFIGURATION.json',{'rows':rows,'settings':json.loads(settings),'scope':'fresh primary, network none, no replication slots/subscriptions/archive destination','excluded_features':'streaming receiver/sender, logical replication worker, recovery/startup after readiness, enabled archiver, third-party background worker; no such feature configured','numeric_authority':'NONE'})
    q.sql('CREATE TABLE test_parallel AS SELECT generate_series(1,200000) id; ANALYZE test_parallel; GRANT SELECT ON test_parallel TO test_executor;')
    q.sql("ALTER SYSTEM SET autovacuum_naptime='1s'; SELECT pg_reload_conf(); ALTER TABLE test_parallel SET (autovacuum_vacuum_threshold=0,autovacuum_vacuum_scale_factor=0,autovacuum_vacuum_cost_delay=20,autovacuum_vacuum_cost_limit=10); UPDATE test_parallel SET id=id+200000 WHERE id<=10000;")
    deadline=time.monotonic()+75;worker=''
    try:
        while time.monotonic()<deadline:
            worker=q.sql("SELECT coalesce(json_agg(json_build_object('pid',pid,'type',backend_type,'role',usename))::text,'') FROM pg_stat_activity WHERE backend_type='autovacuum worker';").stdout.strip()
            if worker:break
            time.sleep(.1)
        q.case('process_population','actual_autovacuum_worker_observed_no_authority',bool(worker),{'actual_worker':worker,'controls':'disposable autovacuum naptime/cost/table thresholds are fixture controls only','numeric_policy_authority':'NONE'})
    finally:q.sql('ALTER SYSTEM RESET autovacuum_naptime; SELECT pg_reload_conf();')
    query="SET max_parallel_workers_per_gather=2; SET min_parallel_table_scan_size=0; SET parallel_setup_cost=0; SET parallel_tuple_cost=0; EXPLAIN (ANALYZE,FORMAT JSON) SELECT sum(id) FROM test_parallel;"
    result=q.sql(query,'test_executor',ok=False)
    q.case('process_population','actual_parallel_execution_denied_at_native_worker',result.returncode!=0 and 'unsupported governed process class requires independent enrollment' in result.stderr,{'exit':result.returncode,'stderr':result.stderr,'stdout':result.stdout,'experimental_planner_controls_only':True})
    q.ex('pg_ctl','-D','/tmp/pgdata','-m','immediate','-w','stop',ok=False);q.boot()
    with q.health_lock:assert q.observer_once()
    q.case('process_population','supported_client_recovers_only_fresh_generation',q.sql('SELECT 42;','test_verifier',ok=False).returncode==0,'Unsupported parallel execution never becomes an enrolled client or restores a quarantined generation')
