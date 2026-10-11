"""Historical reproduction of unanchored parallel execution; no production claim."""
def run(q):
    q.sql('CREATE TABLE test_parallel AS SELECT generate_series(1,200000) id; ANALYZE test_parallel; GRANT SELECT ON test_parallel TO test_executor;')
    query="SET max_parallel_workers_per_gather=2; SET min_parallel_table_scan_size=0; SET parallel_setup_cost=0; SET parallel_tuple_cost=0; EXPLAIN (ANALYZE,FORMAT JSON) SELECT sum(id) FROM test_parallel;"
    result=q.sql(query,'test_executor',ok=False)
    (q.OUT/'PARALLEL-RAW.txt').write_text(result.stdout+result.stderr)
    import re
    launched=[int(n) for n in re.findall(r'"Workers Launched": (\d+)',result.stdout)]
    q.case('process_population','unsupported_governed_parallel_worker_must_not_execute',result.returncode!=0,{'exit':result.returncode,'actual_workers_launched':launched,'stderr':result.stderr,'experimental_query_settings':'planner exercise only, no numeric policy','expected_pre_fix_FAILURE':True})
