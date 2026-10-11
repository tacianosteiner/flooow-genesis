"""Bounded actual delay schedules; experimental controls confer no policy."""
def run(q):
    before=q.ex('cat','/tmp/full.log').stdout
    flags=['/run/flooow-watchdog/auth-observation-completion-pause','/run/flooow-watchdog/census-response-pause'];q.ex('touch',*flags)
    try:
        result=q.sql("SELECT pg_sleep(2), 'USABLE_SNAPSHOT_MARKER';",'test_verifier',ok=False)
        after=q.ex('cat','/tmp/full.log').stdout[len(before):]
        q.case('schedule','actual_pre_promotion_catalog_snapshot_arrives_after_promotion',result.returncode==0 and 'USABLE_SNAPSHOT_MARKER' in result.stdout and 'STALE_CENSUS_OBSERVATION_IGNORED' in after,{'exit':result.returncode,'stdout':result.stdout,'stderr':result.stderr,'new_events':after,'experimental_auth_pause_us':200000,'experimental_census_response_pause_us':500000,'numeric_policy_authority':'NONE'})
    finally:q.ex('rm','-f',*flags)
    q.case('schedule','current_snapshot_after_old_snapshot_recovers',q.sql('SELECT 1;','test_verifier',ok=False).returncode==0,'Current generation and enrollment remain valid; old snapshot grants no eligibility')
    q.sql('ALTER EVENT TRIGGER flooow_test_login_event DISABLE;')
    try:
        for command in ['SELECT 1;','BEGIN; SELECT 1; COMMIT;','SET application_name=\'cannot_be_authority\';']:
            r=q.sql(command,'test_verifier',ok=False);q.case('mandatory_guard',command,r.returncode!=0 and 'mandatory enrolled execution guard denied' in r.stderr,{'stderr':r.stderr,'trigger':'disabled TEST_ONLY_NONCANONICAL fixture','authority_granted':False})
    finally:q.sql('ALTER EVENT TRIGGER flooow_test_login_event ENABLE ALWAYS;')
    for name,flags,accept in [
        ('census_response_delayed',['census-response-pause'],True),
        ('registry_before_accept_delayed',['registry-insertion-pause'],True),
        ('census_and_registry_overlap',['census-response-pause','registry-insertion-pause'],True),
        ('receiver_response_after_deadline',['delay-ack'],False),
        ('catalog_response_after_deadline',['catalog-stall'],False),
        ('SCM_after_deadline',['pre-transfer-pause'],False),
        ('old_joint_receiver_supervisor_generation',['stale-epoch'],False),
        ('old_postmaster_identity',['old-postmaster-frame'],False),
        ('old_ACCEPT_epoch',['replay-accept-epoch'],False),
        ('old_ACCEPT_request_digest',['replay-accept-digest'],False),
    ]:
        paths=['/run/flooow-watchdog/'+f for f in flags];q.ex('touch',*paths)
        try:
            r=q.sql("SELECT 'USABLE_SCHEDULE_MARKER';",'test_verifier',ok=False)
            q.case('schedule',name,(r.returncode==0 and 'USABLE_SCHEDULE_MARKER' in r.stdout) if accept else (r.returncode!=0 and 'USABLE_SCHEDULE_MARKER' not in r.stdout),{'flags':flags,'exit':r.returncode,'stderr':r.stderr,'no_policy_authority':True})
        finally:q.ex('rm','-f',*paths)
        q.case('schedule',name+'_recovery',q.sql('SELECT 1;','test_verifier',ok=False).returncode==0,'Fresh exact-context admission, no lease extension from old messages')
    q.record['cases'].append({'group':'remaining','name':'exhaustive_all_interleavings','result':'NOT_RUN','detail':'Ten bounded real schedules are executed. Complete permutation coverage around backend birth, registry deletion and generation teardown is not established; this is not an exhaustive schedule model.'})
