"""Read-only PG18.4 watchdog boundary review; never signals a backend.

An observation/action identity guard cannot remove the documented PID-reuse
window inside the allowed PostgreSQL native signaling primitive. This probe
records that implementation prerequisite without installing a partial watchdog.
"""
import datetime, hashlib, json, secrets, subprocess, sys, time, urllib.request
from pathlib import Path
import package_0090_timing_qualification2 as env
import package_0090_timing_forensics as authority

ROOT=env.ROOT
BASELINE='401a5e313efbec9a4100af8b6b6e237fffb4ca38'
SOURCE='https://raw.githubusercontent.com/postgres/postgres/REL_18_4/src/backend/storage/ipc/signalfuncs.c'
WORK='watchdog-deployment-boundary'

def run(args,timeout=30):
    p=subprocess.run(args,capture_output=True,timeout=timeout)
    if p.returncode:raise RuntimeError('Tool failed: '+args[0])
    return p.stdout

def measure():
    run(['git','fetch','origin'])
    if any(run(['git','rev-parse',r]).decode().strip()!=BASELINE for r in ['HEAD','origin/checkpoint/package-0090-cloud-handoff']):raise RuntimeError('Baseline mismatch')
    allowed={'scripts/validation/package_0090_watchdog_boundary_review.py'}
    if any(r[3:].replace('\\','/') not in allowed for r in run(['git','status','--porcelain']).decode().splitlines()):raise RuntimeError('Unexpected worktree changes')
    container,private,old=env.identity()
    if container['State']['Running']:raise RuntimeError('Expected stopped disposable')
    work=private/WORK;work.mkdir(exist_ok=True)
    if (work/'record.json').exists():raise RuntimeError('Do not overwrite diagnostic')
    paths=run(['git','ls-files','-z']).decode().split('\0')
    hashes={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths if p and (ROOT/p).is_file()}
    rec={'baseline':BASELINE,'historical_hashes_before':hashes,'protected_database_connection':'NO','protected_volume_mount':'NO','production_secret_use':'NO','signaling_call_count':0,'role_mutation_count':0,'password_rotation':'NOT_REQUIRED','read_only_catalog_probe':True}
    def save():(work/'record.json').write_text(json.dumps(rec,indent=2)+'\n',encoding='utf-8',newline='\n')
    def sql(statement,database='g3f4'):
        env.identity()
        p=subprocess.run(['docker','exec','-i',env.CONTAINER,'psql','-X','-U','postgres','-d',database,'-At','-v','ON_ERROR_STOP=1'],input=statement,text=True,capture_output=True,timeout=30)
        if p.returncode:raise RuntimeError('Read-only administrative SQL failed')
        return p.stdout.strip()
    roles=['postgres']+['g3f4_'+s+'_cc2941797db3' for s in ['auditor','verifier','issuer','executor']]
    query=authority.authority_snapshot_sql(roles)
    marker_query="SELECT json_agg(row_to_json(r) ORDER BY incarnation_id) FROM (SELECT deployment_id,incarnation_id,state,policy_version,encode(policy_digest,'hex') AS policy_digest,watchdog_checked_at,watchdog_healthy FROM public.offline_readiness) r;"
    password_file=private/'postgres-password'
    if password_file.exists():raise RuntimeError('Unexpected plaintext startup file')
    # Image entrypoint requires this file even for existing PGDATA. It is not
    # used for authentication, initialization or password rotation.
    password_file.write_text(secrets.token_hex(32),encoding='ascii')
    started=False;actors=[]
    try:
        env.identity();run(['docker','start',env.CONTAINER]);started=True
        deadline=time.monotonic()+40
        while time.monotonic()<deadline:
            if subprocess.run(['docker','exec',env.CONTAINER,'pg_isready','-U','postgres','-d','g3f4'],capture_output=True).returncode==0:break
            time.sleep(.1)
        else:raise RuntimeError('Startup timeout')
        rec['server']=json.loads(sql("SELECT json_build_object('version',version(),'version_num',current_setting('server_version_num'),'database_oid',(SELECT oid FROM pg_database WHERE datname=current_database()),'postmaster_start',pg_postmaster_start_time(),'clock',clock_timestamp());"))
        if rec['server']['version_num']!='180004':raise RuntimeError('PG18.4 required')
        rec['authority_pre']=json.loads(sql(query));rec['fingerprint_pre']=authority.fingerprint(rec['authority_pre'])
        rec['marker_pre']=json.loads(sql(marker_query))
        if len(rec['marker_pre'])!=1 or rec['marker_pre'][0]['incarnation_id']!=old['timing_fixture']['incarnation'] or rec['marker_pre'][0]['state']!='NOT_READY' or rec['marker_pre'][0]['watchdog_healthy']:raise RuntimeError('Unchanged NOT_READY fixture required')
        rec['native_signatures']=json.loads(sql("SELECT json_agg(json_build_object('oid',p.oid,'signature',p.oid::regprocedure::text,'arguments',pg_get_function_arguments(p.oid),'result',pg_get_function_result(p.oid),'language',l.lanname,'source_symbol',p.prosrc,'postgres_execute',has_function_privilege('postgres',p.oid,'EXECUTE')) ORDER BY p.oid) FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace JOIN pg_language l ON l.oid=p.prolang WHERE n.nspname='pg_catalog' AND p.proname IN ('pg_cancel_backend','pg_terminate_backend');"))
        data=urllib.request.urlopen(SOURCE,timeout=30).read();text=data.decode()
        if 'BackendPidGetProc(pid)' not in text or 'pid being' not in text or 'kill(-pid, sig)' not in text:raise RuntimeError('Pinned source does not match reviewed primitive')
        rec['primary_source']={'url':SOURCE,'sha256':hashlib.sha256(data).hexdigest(),'version_tag':'REL_18_4','reviewed_line_ranges':[[47,117],[125,149],[218,255]],'full_source_not_copied':True}
        rec['live_identity_guards']=[]
        # Existing logins, existing disposable databases, no CREATE/SET ROLE.
        # pg_sleep keeps read-only subjects observable; no signal is issued.
        for label,role,database in [('managed','g3f4_executor_cc2941797db3','g3f4'),('unmanaged','postgres','g3f4'),('foreign','postgres','postgres')]:
            name='0090-watchdog-boundary-'+label
            actor=subprocess.Popen(['docker','exec','-e','PGAPPNAME='+name,env.CONTAINER,'psql','-X','-U',role,'-d',database,'-At','-v','ON_ERROR_STOP=1','-c','SELECT pg_sleep(12);'],stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
            actors.append(actor)
            until=time.monotonic()+5;row=None
            while time.monotonic()<until:
                found=sql("SELECT row_to_json(x) FROM (SELECT pid,backend_start,datid,usesysid,usename,application_name,backend_type,state,clock_timestamp() AS observed_db_time FROM pg_stat_activity WHERE application_name='"+name+"' AND state='active') x;")
                if found:row=json.loads(found);break
                if actor.poll() is not None:raise RuntimeError('Read-only subject did not authenticate')
                time.sleep(.02)
            if row is None:raise RuntimeError('Subject not observed')
            expected_role=next(r['oid'] for r in rec['authority_pre']['roles'] if r['rolname']=='g3f4_executor_cc2941797db3')
            db_oid=rec['server']['database_oid'];incarnation=old['timing_fixture']['incarnation'];deployment=old['timing_fixture']['deployment']
            def guarded(start,inc=incarnation):
                # Predicate only: never add a native signal call to this SQL.
                return sql("SELECT EXISTS(SELECT 1 FROM pg_stat_activity a JOIN public.offline_readiness r ON r.incarnation_id='"+inc+"'::uuid AND r.deployment_id='"+deployment+"'::uuid WHERE a.pid="+str(row['pid'])+" AND a.backend_start='"+start+"'::timestamptz AND a.datid="+str(db_oid)+" AND a.usesysid="+str(expected_role)+" AND a.backend_type='client backend');")=='t'
            rec['live_identity_guards'].append({'case':label,'observed_subject':row,'guard_matches':guarded(row['backend_start']),'wrong_incarnation_matches':guarded(row['backend_start'],'00000000-0000-0000-0000-000000000001'),'changed_backend_start_matches':guarded('2000-01-01T00:00:00Z'),'destructive_action_executed':False,'application_name_usage':'Observation label only; never authority whitelist'})
        for p in actors:
            if p.wait(timeout=20)!=0:raise RuntimeError('Read-only subject failed')
        actual={r['case']:r for r in rec['live_identity_guards']}
        if not actual['managed']['guard_matches'] or actual['unmanaged']['guard_matches'] or actual['foreign']['guard_matches'] or any(r['wrong_incarnation_matches'] or r['changed_backend_start_matches'] for r in actual.values()):raise RuntimeError('Observed identity guard failed')
        rec['identity_guard_checks']='PASS_FOR_OBSERVED_IDENTITIES_ONLY_NOT_ATOMIC_SIGNALING'
        rec['authority_post']=json.loads(sql(query));rec['fingerprint_post']=authority.fingerprint(rec['authority_post'])
        rec['marker_post']=json.loads(sql(marker_query));rec['authority_equal']=rec['authority_pre']==rec['authority_post'];rec['marker_unchanged']=rec['marker_pre']==rec['marker_post'];save()
    finally:
        try:
            for p in actors:
                if p.poll() is None:
                    # These bounded subjects finish naturally; no PID-only action.
                    p.wait(timeout=20)
            if started:run(['docker','stop',env.CONTAINER],40)
        finally:
            if password_file.exists():password_file.unlink()
            rec['container_stopped']=not env.identity()[0]['State']['Running'];rec['plaintext_credential_files_erased']=not password_file.exists()
            rec['historical_hashes_after']={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in hashes};rec['historical_unchanged']=rec['historical_hashes_before']==rec['historical_hashes_after'];save()
    if not all(rec.get(k) for k in ['authority_equal','marker_unchanged','container_stopped','plaintext_credential_files_erased','historical_unchanged']):raise RuntimeError('Probe integrity failure')
    print('READ_ONLY_BOUNDARY_PROBE=PASS; IMPLEMENTATION_PREREQUISITE=UNRESOLVED')

def publish():
    if any(run(['git','rev-parse',r]).decode().strip()!=BASELINE for r in ['HEAD','origin/checkpoint/package-0090-cloud-handoff']):raise RuntimeError('Do not rewrite accepted evidence beyond baseline')
    container,private,_=env.identity();work=private/WORK;rec=json.loads((work/'record.json').read_text())
    if container['State']['Running'] or (private/'postgres-password').exists():raise RuntimeError('Cleanup incomplete')
    if not all(rec.get(k) for k in ['authority_equal','marker_unchanged','container_stopped','plaintext_credential_files_erased','historical_unchanged']):raise RuntimeError('Probe integrity incomplete')
    if any(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()!=h for p,h in rec['historical_hashes_before'].items()):raise RuntimeError('Historical drift')
    spec='docs/specifications/SPEC-0090-governed-offline-field-proof-exclusive-capability-composition.md'
    adr='docs/adr/ADR-0090-governed-offline-field-proof-exclusive-capability-composition.md'
    source_lines={spec:(ROOT/spec).read_text(encoding='utf-8-sig').splitlines(),adr:(ROOT/adr).read_text(encoding='utf-8-sig').splitlines()}
    matrix=[]
    def row(requirement,source,component,failure,persisted,required='Existing trusted deployment ADMIN',coverage='NOT_IMPLEMENTED'):
        refs=[{'path':path,'line':line,'text':source_lines[path][line-1]} for path,line in source]
        matrix.append({'REQUIREMENT':requirement,'SPEC_SOURCE':refs,'IMPLEMENTATION_COMPONENT':component,'FAILURE_ACTION':failure,'PERSISTED_STATE':persisted,'AUTHORITY_REQUIRED':required,'coverage':coverage})
    row('Monitor all exact governed service session OIDs/names; caller application_name is not authority',[(adr,27),(spec,88),(spec,245)],'Proposed external ADMIN catalog observer; no service process','Reject unmapped/recreated/renamed identities; no signal','Existing immutable slot/deployment configuration; no new SQL relation',coverage='READ_ONLY_OBSERVED_GUARDS_PASS')
    row('Exact approved endpoint, deployment and incarnation; clones stay ineligible',[(adr,35),(spec,96),(spec,220)],'Existing disposable endpoint guard plus proposed watcher incarnation validation','Reject wrong database/incarnation before write or signal','Existing incarnation/readiness; NOT_READY retained',coverage='READ_ONLY_OBSERVED_GUARDS_PASS')
    row('Protected marker relation, health/state, DB-clock heartbeat',[(spec,245),(spec,586),(spec,2210),(spec,2217)],'Proposed external ADMIN UPDATE public.offline_readiness.watchdog_checked_at/watchdog_healthy','Leave or mark NOT_READY/unhealthy on uncertainty; do not set READY by liveness','Existing offline_readiness; immutable policy binding preserved')
    row('Finite reviewed cadence and maximum tolerated transaction/idle duration',[(spec,239),(spec,243),(spec,245),(spec,586)],'Proposed canonical 29-field bound-policy decoder and enforcement loop','Reject absent/zero/overflow/above-max/unqualified values','Existing immutable offline_deadline_policy; no fixture/new numbers')
    row('Observe transaction wall-clock duration independently of session timeout settings',[(adr,81),(spec,245)],'Proposed catalog xact_start/database-clock observer','Cancel/terminate overdue exact governed backend; SET timeout=0 does not bypass','No automatic ownership release; administrative incident evidence')
    row('Observe idle-in-transaction duration',[(adr,81),(spec,245)],'Proposed state/state_change/database-clock observer','Cancel/terminate exact overdue idle transaction; cancel acknowledgment alone is not drain completion','Existing readiness and unchanged ownership')
    row('Native cancellation with target identity proved before action',[(spec,245)],'pg_cancel_backend; permitted by user request section7','No action if compound identity is unproved or changed','BACKEND_TIMEOUT/BACKEND_CANCELLED observations; no success inference',coverage='BLOCKED_STRICT_OBSERVATION_TO_SIGNAL_IDENTITY')
    row('Native termination when cancellation cannot enforce approved duration',[(spec,245)],'pg_terminate_backend; permitted by user request section7','No action against a replacement identity; verify actual target disappearance rather than boolean alone','BACKEND_TERMINATED observation; no completion/ownership inference',coverage='BLOCKED_STRICT_OBSERVATION_TO_SIGNAL_IDENTITY')
    row('Watchdog failure blocks new claim/effect admission and triggers drain',[(spec,245),(spec,610),(spec,612)],'Existing S01/Q/S13 and mutation guards plus proposed independent supervisor/drain controller','Make readiness ineligible; independently drain and reconcile uncertain work','offline_readiness NOT_READY/unhealthy; exact recovery evidence only')
    row('Stale ownership is never automatically released by crash, disconnect or timeout',[(adr,49),(spec,104)],'Governed ADMIN recovery under C locks after prior-session drain','Mark STALE/ABORTED and advance generation only under existing exact recovery conditions','Existing execution/attempt/generation lineage; watchdog does not fabricate domain outcomes')
    row('Recovery must distinguish early no-effects state from existing committed decision/head',[(spec,52),(spec,104),(spec,175)],'Governed independent administrative recovery/reconciliation recorder','Existing decision/head requires reconcile; uncertainty requires manual review','Existing evidence/result; no synthetic EFFECTS_COMPLETE/SUCCESS')
    row('Graceful shutdown cannot leave operational eligibility open',[(spec,245),(spec,104)],'Proposed stop controller: unhealthy/NOT_READY plus verified drain','No healthy heartbeat after shutdown; preserve uncertain ownership','Existing readiness; administrative drain/recovery obligation','Existing ADMIN; shutdown lifecycle is derived from fail-closed requirement, not a new SPEC signal API')
    row('Process crash/termination or inaccessible DB must fail closed',[(spec,245),(spec,104)],'Proposed independent supervisor plus DB-clock freshness checks','Lost heartbeat ages out; attempt unhealthy update/drain where reachable; on reconnect do not claim previous drain completion','Marker may stay physically unchanged while unreachable; derived freshness ineligible; recovery still required')
    row('Normal DB restart retains incarnation/ownership; restart alone is not recovery',[(spec,96),(spec,104),(spec,612)],'Proposed reconnect/startup exclusion and exact incarnation revalidation','No READY auto-promotion or receipt renewal; reconcile uncertain prior sessions/work','Retained incarnation, execution ownership, receipt scope and deadlines')
    row('No service privilege widening or domain effects from watchdog',[(spec,604),(spec,606),(spec,2210)],'External existing postgres ADMIN, isolated from four service credential sources','Reject new service grants/new helpers/domain writes','Exact non-secret authority state unchanged',coverage='PASS_NO_IMPLEMENTATION_MUTATIONS')
    row('Receipts/TTL/policy values remain immutable',[(spec,588),(spec,612),(spec,2234)],'Existing Q expiry rule and immutable policy storage','No heartbeat-based receipt renewal, fixture2 installation, fixture3 or numeric substitution','Existing policy and receipt bytes/deadlines unchanged',coverage='PASS_BYTE_AND_CATALOG_IDENTITY')
    row('Independent deployment packaging and secret-safe evidence',[(adr,133),(spec,249),(spec,2236)],'Proposed scripts/operations/rehearsal-watchdog; not enabled or created','No credential material in repository/logs; no declaration of COMPLETE without runtime proof','Existing trusted administrative evidence outside operational SQL surface')
    matrix.append({'REQUIREMENT':'PID replacement between observation and action must not receive a destructive signal','SPEC_SOURCE':[{'path':'USER_REQUEST','section':'5,7,13E,17','text':'Never cancel/terminate by PID alone; changed target identity must fail closed; no unsafe PID-only action.'}],
        'IMPLEMENTATION_COMPONENT':'Required generation-bound compare-and-signal execution primitive; absent from allowed native signatures',
        'FAILURE_ACTION':'STOP before enforcement implementation; no signaling calls; no unauthorized alternate mechanism',
        'PERSISTED_STATE':'Existing NOT_READY/unhealthy remains unchanged; deployment HIGH remains OPEN',
        'AUTHORITY_REQUIRED':'Explicit governance for a generation-bound signaling mechanism beyond section7 allowed native PID APIs; no new DB role/grant is required for existing APIs',
        'coverage':'UNRESOLVED_STRICT_GATE_REQUIREMENT; interpretation includes the final primitive execution window, not only a pre-call stale-token test'})
    result={'WATCHDOG_NEW_AUTHORITY_REQUIRED':'YES','WATCHDOG_NEW_DATABASE_PRIVILEGE_REQUIRED':'NO',
        'REQUIRED_NEW_AUTHORIZATION':'Generation-bound signaling mechanism outside the currently allowed pg_cancel_backend/pg_terminate_backend boundary',
        'WATCHDOG_COMPONENT':'NOT_IMPLEMENTED_AUTHORITY_AND_IDENTITY_BOUNDARY_STOP','WATCHDOG_DEPLOYMENT_LOCATION':'PROPOSED scripts/operations/rehearsal-watchdog; no deployment enabled',
        'WATCHDOG_TARGET_IDENTITY_MODEL':'Expected project/image/volume plus deployment/incarnation/database OID/service role OID/name/PID/backend_start/client-backend category; application_name is not authority',
        'WATCHDOG_PID_REUSE_PROTECTION':'Observed stale-token guards PASS; atomic observation-to-signal protection UNPROVEN with allowed native APIs',
        'HEARTBEAT_RUNTIME':'NOT_EXECUTED_BOUNDARY_STOP','DB_CLOCK_AUTHORITY':'CONFIRMED_EXISTING_CONTRACT_AND_REAL_CATALOG_CLOCK; writer not implemented',
        'TRANSACTION_TIMEOUT_ENFORCEMENT':'NOT_EXECUTED_BOUNDARY_STOP','IDLE_TIMEOUT_ENFORCEMENT':'NOT_EXECUTED_BOUNDARY_STOP',
        'CANCEL_RUNTIME':'NOT_EXECUTED_BOUNDARY_STOP','TERMINATE_RUNTIME':'NOT_EXECUTED_BOUNDARY_STOP',
        'WATCHDOG_STOP_FAIL_CLOSED':'NOT_EXECUTED_BOUNDARY_STOP','WATCHDOG_CRASH_FAIL_CLOSED':'NOT_EXECUTED_BOUNDARY_STOP','DB_DISCONNECT_FAIL_CLOSED':'NOT_EXECUTED_BOUNDARY_STOP',
        'DRAIN_RUNTIME':'NOT_EXECUTED_BOUNDARY_STOP','OWNERSHIP_AUTO_RELEASE':'NO','WATCHDOG_CONTRACT_COVERAGE':'INCOMPLETE',
        'WATCHDOG_AUTHORITY_DELTA':'NONE','WATCHDOG_DEPLOYMENT_IMPLEMENTATION':'MISSING','WATCHDOG_DEPLOYMENT_HIGH':'OPEN','G3F4_H01':'OPEN',
        'BLOCKER_COUNT':0,'HIGH_COUNT':2,'MEDIUM_COUNT':0,'LOW_COUNT':0,'FIXTURE_1_MUTATED':'NO','FIXTURE_2_INSTALLED':'NO','FIXTURE_3_CREATED':'NO',
        'PROTECTED_DATABASE_CONNECTION':'NO','PROTECTED_VOLUME_MOUNT':'NO','PRODUCTION_SECRET_USE':'NO',
        'PASSWORD_ROTATION':'NOT_REQUIRED','NON_SECRET_AUTHORITY_FINGERPRINT_PRE':rec['fingerprint_pre'],'NON_SECRET_AUTHORITY_FINGERPRINT_POST':rec['fingerprint_post'],
        'PLAINTEXT_CREDENTIAL_FILES_ERASED':'YES','DISPOSABLE_CONTAINER_STOPPED':'YES','NEXT_GATE':'G3F_4_WATCHDOG_DEPLOYMENT_CLOSURE',
        'CHECKPOINT':'NOT_EXECUTED_IMPLEMENTATION_VALIDATION_CONDITION_NOT_MET','LOCAL_HEAD':BASELINE,'REMOTE_HEAD':BASELINE,'LOCAL_EQUALS_REMOTE':'YES','WORKTREE':'DIRTY_NEW_AUTHORIZED_STOP_EVIDENCE_ONLY',
        'NEXT_TECHNICAL_ACTION':'Resolve generation-bound signaling contract/authorization before implementation; do not advance numeric-bound review'}
    common={'baseline':BASELINE,'branch':'checkpoint/package-0090-cloud-handoff','status':'STOP_BEFORE_WATCHDOG_IMPLEMENTATION; CLOSURE_NOT_ACHIEVED','result':result,
        'stop_reason':'Existing postgres permissions suffice for catalogs, marker DML and native signals, but the required strict identity binding is not supplied by the permitted signal interfaces. A SQL predicate/double read or wrapper cannot certify that the process generation is unchanged through the actual native signal. No alternate mechanism was authorized or introduced.',
        'evidence_limits':['No actual PID reuse/replacement or wrong-target signaling was induced. Runtime guards tested existing sessions and a deliberately stale expected backend_start, not native action atomicity.',
            'No watchdog was implemented, deployed or run. No heartbeat/cancel/terminate/drain/process-failure test is counted as PASS.',
            'The foreign-database subject was also unmanaged; database-OID and role-OID mismatches are independently visible, but this is not an orthogonal live managed-role foreign-database action test.',
            'Generation-bound final-action protection is a strict reading of the user gate, stronger than the bare OID/incarnation whitelist prose in SPEC18. The source review preserves that distinction; it does not amend SPEC or accept residual risk.'],
        'checkpoint_scope':'Read-only diagnostic tooling and four stop-evidence artifacts prepared locally; user section21 conditional commit/push not performed because watchdog implementation validation was not achieved'}
    def write(name,data):(ROOT/'docs/evidence'/('PACKAGE-0090-G3F-4-'+name)).write_text(json.dumps(data,indent=2,ensure_ascii=True)+'\n',encoding='utf-8',newline='\n')
    write('WATCHDOG-RUNTIME.json',{**common,'server':rec['server'],'native_signatures':rec['native_signatures'],'primary_source':rec['primary_source'],'read_only_identity_probes':rec['live_identity_guards'],
        'signaling_call_count':0,'heartbeat_update_count':0,'watchdog_process_count':0,'bounded_read_only_subject_count':3,
        'validation':'Actual PG18.4 version/signatures, managed match, wrong-incarnation/stale-backend-start/unmanaged/foreign guard rejection; no destructive native action'})
    write('WATCHDOG-AUTHORITY-REVIEW.json',{**common,'normative_matrix':matrix,'pre_post_non_secret_role_state_equal':rec['authority_equal'],'readiness_marker_unchanged':rec['marker_unchanged'],
        'new_roles':0,'new_grants':0,'new_public_sql_functions':0,'new_persistence_relations':0,'domain_writes':0,'role_attribute_mutations':0,
        'authority_and_cleanup_record_gzip_base64':authority.packed_log(work/'record.json'),
        'independent_review':'Gate-specific check of pinned native API and reconstructed ADR/SPEC plus strict user fencing requirements, separate from implementation (which was not started). No sub-agent or independent-human audit is claimed.'})
    cases=['normal_start','normal_stop','crash','SIGTERM_equivalent','DB_disconnect','DB_restart','invalid_credentials','network_interruption','catalog_unavailable','heartbeat_update_unavailable','continuous_refresh','after_stop_freshness_denial','restart_no_fabricated_recovery','healthy_transaction_untouched','transaction_timeout_cancel','idle_timeout_cancel_or_terminate','cancel_escape_termination','actual_PID_reuse','drain_trigger','uncertain_work_ownership_preservation']
    write('WATCHDOG-FAILURE-MATRIX.json',{**common,'runtime_cases':[{'case':c,'status':'NOT_EXECUTED_BOUNDARY_STOP','observations':None,'reason':'No compliant enforcement primitive authorized/available; no partial watchdog installed'} for c in cases],
        'read_only_guard_cases':rec['live_identity_guards'],'native_signal_ack_is_not_proof_of_target_identity_or_effect_completion':True,'missing_or_unexecuted_measurements_are_not_zero':True})
    md='''# Package 0090 - watchdog deployment closure boundary review

STATUS: STOP before watchdog implementation. Deployment closure was not achieved. G3F.4 HOLD, H01 OPEN/HIGH, watchdog deployment HIGH OPEN. Counts remain BLOCKER0/HIGH2/MEDIUM0/LOW0.

DECISION: preserve the strict target-identity requirement and do not execute destructive native signals. No compliant watchdog component is installed. NEXT_GATE remains G3F_4_WATCHDOG_DEPLOYMENT_CLOSURE; its next bounded technical prerequisite is generation-bound signaling contract/authorization, not numerical policy review.

The fetched local/remote baseline was 401a5e313efbec9a4100af8b6b6e237fffb4ca38, on checkpoint/package-0090-cloud-handoff, with a clean worktree before the new diagnostic. Previous transport review and all tracked baseline files remain byte-identical, including V001-V043, production adapters, ADR/SPEC, both fixtures and all historical HOLD evidence.

The authority review separates two facts. Existing directly authenticated postgres ADMIN already has sufficient catalog/readiness/native-signal privileges; no DB role, grant, service credential sharing or new SQL object is needed to call the existing APIs. However, the user sections5/7/13E/17 require a changed/reused backend identity to fail closed through the destructive action, forbid PID-only action and forbid introducing a third signaling mechanism. Under that strict reading, full implementation needs authorization for a generation-bound signaling primitive beyond the permitted native interface. WATCHDOG_NEW_AUTHORITY_REQUIRED=YES refers to this execution-mechanism authorization, not a missing database grant. No alternative mechanism, trust boundary or SQL function was introduced.

Real installed PostgreSQL18.4 catalog signatures are pg_cancel_backend(integer) and pg_terminate_backend(integer,bigint), the latter timeout defaulting to0. They accept no expected backend_start, database, role or incarnation. The version-tagged native source confirms PID lookup followed by signaling and documents a PID-reuse window. A caller-side predicate or repeated catalog read can reject an already changed identity; it cannot bind that checked generation to the eventual signal. This is an inference from the reviewed API/source, not an observed wrong-target signal. [Pinned PostgreSQL18.4 native source](https://raw.githubusercontent.com/postgres/postgres/REL_18_4/src/backend/storage/ipc/signalfuncs.c).

The strict user gate is stronger than SPEC18's bare OID/incarnation-whitelist wording. This review does not silently add an atomic primitive to SPEC, reinterpret successful observed guard tests as a universal replacement defense, or infer acceptance of the native residual race from the fact that native functions are named. A wrapper around those same functions cannot eliminate their unbound final-action window. A compliant stronger primitive needs separate governance under the existing no-new-mechanism boundary; none is implemented here.

Three real bounded read-only sessions were observed in the exact disposable container. The managed EXECUTOR in g3f4 matched the OID/database/backend_start/incarnation predicate. An unmanaged postgres session and a postgres session in the existing disposable postgres database were rejected. Wrong incarnation and deliberately stale expected backend_start were rejected for every subject. application_name was an observation label only, never the authority whitelist. All subjects finished naturally; no cancellation or termination was sent. The foreign subject also had an unmanaged role, so that case is disclosed as a combined negative control. No actual PID recycling was induced or claimed.

The full normative matrix below is reconstructed from ADR27/35/49/81/133 and SPEC5/6/7/18/21.2/21.3/25, with exact source text/lines retained in WATCHDOG-AUTHORITY-REVIEW.json. Proposed component boundaries are explicitly unimplemented. Shutdown/supervision details not concretely specified in SPEC are identified as derived fail-closed lifecycle obligations rather than invented normative protocol.

| Requirement | SPEC source | Proposed component | Failure action | Persisted state | Authority required |
|---|---|---|---|---|---|
'''
    for r in matrix:
        refs=', '.join(('USER '+x['section']) if x['path']=='USER_REQUEST' else ('ADR' if x['path']==adr else 'SPEC')+':'+str(x['line']) for x in r['SPEC_SOURCE'])
        values=[r['REQUIREMENT'],refs,r['IMPLEMENTATION_COMPONENT'],r['FAILURE_ACTION'],r['PERSISTED_STATE'],r['AUTHORITY_REQUIRED']]
        md+='| '+' | '.join(v.replace('|','/') for v in values)+' |\n'
    md+='''

The intended deployment boundary is out-of-process operations tooling, separate from AUDITOR/VERIFIER/ISSUER/EXECUTOR, with only the existing trusted ADMIN secret source. It must bind exact endpoint/deployment/incarnation and role whitelist; decode existing immutable policy rather than choose new durations; use database clocks for heartbeat and transaction/idle observations; make readiness ineligible on uncertainty; independently supervise failure and execute verified drain without domain effects. Restart is not recovery, receipt renewal or ownership release. A future component must use the approved control-lock recovery/reconciliation path, preserve decision/head evidence and never fabricate completion.

No startup/shutdown command, deployable configuration contract, health PASS or operational failure exit-code contract is supplied for a nonexistent component. The only executable command produced in this gate is the one-shot read-only boundary probe, `python scripts/validation/package_0090_watchdog_boundary_review.py`. It validates its pinned baseline and exact disposable identity, refuses to overwrite its private record, never invokes a signal and stops the disposable at completion. Re-running it after this checkpoint intentionally refuses the changed baseline. Proposed watchdog deployment location is scripts/operations/rehearsal-watchdog, not an enabled package.

Heartbeat refresh, cancellation, termination, normal stop/crash/SIGTERM, disconnect/restart/network/credential/catalog/write failures, timeout enforcement, real PID reuse, admission denial after a formerly healthy watchdog, drain and uncertain-work recovery are NOT_EXECUTED_BOUNDARY_STOP. Every unexecuted observation count is NULL, not an invented zero. Current readiness remains NOT_READY/unhealthy; no positive eligible state or synthetic READY was constructed. Previous continuous-marker observations are historical evidence, not runtime tests of a new component.

Validation: exact disposable project/image/volume/readonly bind and PG18.4 were verified. Existing native signatures and live non-destructive guard facts were confirmed. Complete non-secret role attributes/memberships/ownership/ACL/defaults/policy/migration state pre/post are equal; both canonical fingerprints are '''+rec['fingerprint_pre']+'''. Role/password mutation count is0. Local server-trust authentication was used for these disposable read-only probes; no credential was shared with a watchdog. The image startup file was required even for existing PGDATA, was not used to authenticate or rotate any database role, and was erased afterward. Marker contents and all baseline file hashes remain identical. Container stopped; no protected database/volume or production secret was used.

Prepared local scope: one read-only diagnostic tool and four required evidence artifacts. User section21 makes commit/push conditional on validation; the watchdog implementation was not validated, so no commit/push was performed. HEAD and fetched remote remain the accepted baseline; worktree contains only these five authorized new files. This is not a claim that the implementation, runtime matrix, contract coverage or deployment HIGH passed. No policy, fixture, production adapter, SQL authority or main branch changed. The necessary technical next action is to resolve the generation-bound signaling execution contract before implementation while preserving the same closed role/ACL/domain boundary. H01 cannot advance to numeric review until deployment closure and later eligible S01/Q timing are separately proven.

Requested return fields (conditional checkpoint is not performed):

```text
'''+''.join(k+'='+str(v)+'\n' for k,v in result.items())+'```\n'
    (ROOT/'docs/evidence/PACKAGE-0090-G3F-4-WATCHDOG-DEPLOYMENT-CLOSURE.md').write_text(md,encoding='utf-8',newline='\n')
    print('STOP_EVIDENCE_PUBLISHED; HIGH_REMAINS_OPEN; NO_WATCHDOG_IMPLEMENTED')

if __name__=='__main__':
    if sys.argv[1:]==['--publish']:publish()
    elif sys.argv[1:]:raise SystemExit('Use no arguments to probe, or --publish for completed stop evidence')
    else:measure()
