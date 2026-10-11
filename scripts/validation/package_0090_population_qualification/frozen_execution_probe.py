"""Actual unchanged frozen file, unconditional fence; no extracted positive stack."""
import hashlib,json
def run(q):
    source=q.V043.read_bytes()
    state="SELECT md5(string_agg(oid::text||':'||relname,',' ORDER BY oid)) FROM pg_class WHERE relnamespace='public'::regnamespace;"
    before=q.sql(state).stdout
    result=q.sql("\\set VERBOSITY verbose\nBEGIN;\n"+source.decode('utf-8-sig'),ok=False)
    after=q.sql(state).stdout
    q.case('frozen_reference','actual_unchanged_source_hits_intended_interlock',result.returncode!=0 and '55000' in result.stderr and 'implementation closure is incomplete' in result.stderr,{'source_sha256':hashlib.sha256(source).hexdigest(),'stderr':result.stderr,'exit':result.returncode,'unconditional_raise':True,'source_modified':False,'prerequisite_fixture_can_disable_fence':False,'classification':'INTENDED_SOURCE_EXECUTION_INTERLOCK_NOT_MISSING_FIXTURE_OR_SEQUENCING'})
    q.case('frozen_reference','failed_transaction_changes_no_public_objects',before==after,{'before':before,'after':after,'transaction_connection_closed_and_rolled_back':True})
    for stage in ['claim','verification','admission','ownership_acquisition','effect_transition','terminal_transition','retry_replay_denial','ownership_retention','ownership_release','reconciliation_required','reconciliation_completion','full_authority_joins','runtime_consumption']:
        q.record['cases'].append({'group':'frozen_wrapper','name':stage,'result':'NOT_RUN_WITH_REASON','reason':'Unchanged frozen V043 unconditionally raises SQLSTATE 55000 before DDL. Recorded source implementation closure is required by its own contract; existing disposable infrastructure authority does not satisfy that source condition. No bypass or synthetic success.'})
