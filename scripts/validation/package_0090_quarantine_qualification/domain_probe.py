"""Exact frozen row shapes and controlled query-first boundaries.
These ADMIN-shaped fixtures do not impersonate the complete frozen wrappers.
"""
import uuid,subprocess,time,hashlib
def run(q):
    source=q.V043.read_text(encoding='utf-8-sig')
    for table in ['offline_attempt','offline_execution','offline_reconciliation']:
        ddl=source.split('CREATE TABLE public.'+table+' (',1)[1].split('\n);',1)[0]
        q.sql('CREATE TABLE public.'+table+' ('+ddl+'\n); REVOKE ALL ON public.'+table+' FROM PUBLIC;')
    binding=q.expected_header['binding_id'];attempt=str(uuid.uuid4());execution=str(uuid.uuid4());instance=str(uuid.uuid4());receipt=str(uuid.uuid4())
    executor=int(q.sql("SELECT oid FROM pg_roles WHERE rolname='test_executor';").stdout)
    q.ex('openssl','rand','-out','/run/test-only-private/TEST_ONLY_NONCANONICAL-execution-secret','32',user='0')
    private_digest=q.ex('sha256sum','/run/test-only-private/TEST_ONLY_NONCANONICAL-execution-secret',user='0').stdout.split()[0]
    try:
        q.sql(f"INSERT INTO offline_attempt VALUES('{binding}','{attempt}',1,'CLAIMED',clock_timestamp(),clock_timestamp()+interval '10 minutes',0); INSERT INTO offline_execution VALUES('{binding}','{attempt}',1,'{execution}','{instance}',{executor},'OWNED',decode('{private_digest}','hex'),clock_timestamp(),clock_timestamp()+interval '10 minutes','{receipt}',0); INSERT INTO offline_reconciliation VALUES('{binding}','NOT_STARTED',NULL,NULL);")
        q.sql('CREATE TABLE test_domain_effect(operation_id uuid PRIMARY KEY,value int NOT NULL); GRANT INSERT,SELECT ON test_domain_effect TO test_executor;')
        for state in ['CLAIMED','EFFECTS_IN_PROGRESS','RECOVERY_REQUIRED','EFFECTS_COMPLETE','ABORTED']:
            q.sql("UPDATE offline_attempt SET state='"+state+"';")
            q.case('ownership_row_contract','attempt_state_'+state,q.sql('SELECT state FROM offline_attempt;').stdout.strip()==state,'Exact V043 DDL; ADMIN fixture transition, not wrapper parity')
        for state in ['OWNED','STALE','RELEASED']:
            q.sql("UPDATE offline_execution SET state='"+state+"';")
            q.case('ownership_row_contract','execution_state_'+state,q.sql('SELECT state FROM offline_execution;').stdout.strip()==state,'Exact V043 DDL; no transport event authorizes this ADMIN write')
        q.sql("UPDATE offline_execution SET state='OWNED'; UPDATE offline_attempt SET state='CLAIMED';")
        for name,sql,expected in [('no_write_issued','SELECT 1;',0),('write_rollback',None,0),('commit_definitely_failed',None,0),('commit_definitely_succeeded',None,1)]:
            operation=str(uuid.uuid4())
            statement=sql or (f"BEGIN; INSERT INTO test_domain_effect VALUES('{operation}',1); "+('COMMIT;' if expected else 'SELECT 1/0; COMMIT;' if name=='commit_definitely_failed' else 'ROLLBACK;'))
            result=q.sql(statement,'test_executor',ok=False)
            # Query only after the synchronous writer process is quiescent.
            count=int(q.sql("SELECT count(*) FROM test_domain_effect WHERE operation_id='"+operation+"';").stdout)
            q.case('domain_query_first',name,count==expected and (result.returncode!=0 if name=='commit_definitely_failed' else result.returncode==0),{'writer_quiescent':True,'authoritative_count':count,'classification':'KNOWN_COMMITTED' if count else 'KNOWN_NO_EFFECT','ownership_retained':q.sql('SELECT state FROM offline_execution;').stdout.strip()=='OWNED'})
        # Committed response deliberately discarded. This is a lost response
        # witness, not a synchronized transport kill during the COMMIT syscall.
        operation=str(uuid.uuid4());q.sql(f"INSERT INTO test_domain_effect VALUES('{operation}',1);",'test_executor')
        q.sql("UPDATE offline_reconciliation SET state='REQUIRED'; UPDATE offline_attempt SET state='RECOVERY_REQUIRED';")
        q.case('domain_query_first','lost_response_unknown_retains_ownership',q.sql('SELECT state FROM offline_execution;').stdout.strip()=='OWNED',{'classification':'UNKNOWN_REQUIRES_RECONCILIATION','automatic_replay':False,'response_discarded':True,'precise_commit_transport_fault':False})
        count=int(q.sql("SELECT count(*) FROM test_domain_effect WHERE operation_id='"+operation+"';").stdout)
        q.case('domain_query_first','lost_response_authoritative_committed',count==1,{'writer_quiescent':True,'classification':'KNOWN_COMMITTED','automatic_replay':False})
        denied=q.sql("UPDATE offline_reconciliation SET state='RECONCILED';",ok=False)
        q.case('ownership_row_contract','reconciliation_without_evidence_denied',denied.returncode!=0,'Exact frozen check constraint requires evidence digest and time')
        q.case('ownership_row_contract','reconciliation_does_not_release_ownership',q.sql('SELECT state FROM offline_execution;').stdout.strip()=='OWNED','No reconciliation observation or drain event rewrites ownership')
        q.record['cases'].append({'group':'full_normative_parity','name':'frozen_wrappers_authority_consumption_terminal_retry_release','result':'NOT_RUN','detail':'DDL row and ADMIN transition fixtures are not complete V043 wrapper/state-machine execution; frozen migration safety interlock preserved'})
    finally:
        private_digest=None
        q.ex('rm','-f','/run/test-only-private/TEST_ONLY_NONCANONICAL-execution-secret',user='0')
        q.case('cleanup','execution_secret_erased',q.ex('test','!','-e','/run/test-only-private/TEST_ONLY_NONCANONICAL-execution-secret',user='0',ok=False).returncode==0,'No possession material preserved in evidence')
