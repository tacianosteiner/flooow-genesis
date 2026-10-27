"""46-class TEST qualification, preserving failure when mediation is absent."""
import copy,json,os,subprocess,sys,tempfile,types,uuid
from pathlib import Path
import package_0090_source_closure as q
from package_0090_t10_46_fence import Fence,Denied,digest

OUT=q.ROOT/'docs/evidence/package-0090-46-class-t10-currentness-closure'
OLD=q.ROOT/'docs/evidence/package-0090-full-reachable-expectation-closure-v2'
BASELINE='05eb515153036cb2da5657a7b3e9a74595d65848'

def save(name,data):
    (OUT/name).write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')
def load(name):return json.loads((OUT/name).read_text())
def old(name):return json.loads((OLD/name).read_text())
def lit(s):return "'"+s.replace("'","''")+"'"

class Cases:
    def __init__(self,sink=None):self.rows=[];self.sink=sink
    def check(self,name,passed,group,details):
        self.rows.append(dict(name=name,passed=bool(passed),group=group,details=details))
        if self.sink is not None:self.sink.append(self.rows[-1])
    def demand(self,name,passed,group,details):
        self.check(name,passed,group,details);q.require(passed,name)

def model_tests(cases):
    directory=Path(tempfile.mkdtemp(prefix='flooow-0090-t10-reference-'));context=dict(deployment=str(uuid.uuid4()),incarnation=str(uuid.uuid4()));f=Fence(directory,**context,initialize=True)
    classes=load('mutation-denominator-freeze.json')['class_ids'];model_receipts={k:'PROVEN' for k in classes}
    value=dict(context,policy='MODEL_ONLY',expected_manifest='MODEL_ONLY',observed_manifest='MODEL_ONLY',native_epoch='MODEL_ONLY',guard_proof='MODEL_ONLY',participant_generations='MODEL_ONLY',history='MODEL_ONLY',return_consumer='MODEL_ONLY')
    s=f.snapshot();result=f.decide([s,s,s],value,model_receipts)
    cases.demand('conditional_reference_control_is_not_live_eligibility',result['decision']=='CONDITIONAL_REFERENCE_MATCH_ONLY' and not result['live_eligibility'],'TRANSITION_FENCE',result)
    cases.demand('missing_class_receipts_fail_closed',f.decide([s,s,s],value,{})['decision']=='DENY','TRANSITION_FENCE',dict(model_only=True))
    for number,class_id in enumerate(classes):
        before=f.snapshot();transition=f.begin(class_id,'MODEL_ONLY_CONTEXT_BINDING','TEST_REFERENCE_ACTOR','TEST_ONLY/0090/46-class-currentness/v1');tid=transition['transition_id'];prepared=f.snapshot()
        cases.demand('prepared_invalidates_'+class_id,prepared['generation']==before['generation']+1 and prepared['state']=='PREPARED' and f.decide([before]*3,value,model_receipts)['decision']=='DENY','GENERATION',dict(generation_before=before['generation'],generation_after=prepared['generation'],journal_only_not_object_mutation=True))
        f.stage(tid,'APPLYING');f.stage(tid,'COMMITTED_PENDING_RECONCILIATION')
        evidence=dict(context,transition_id=tid,outcome='COMMITTED',independent_evidence_identity='MODEL_ONLY_TRACE_'+str(number));f.reconcile(tid,evidence)
        cases.demand('generation_not_reused_'+class_id,f.snapshot()['generation']==prepared['generation'] and f.snapshot()['state']=='STABLE','GENERATION',dict(model_only=True))
    stale=s;current=f.snapshot()
    for field,replacement in [('generation',stale['generation']),('deployment','OLD_DEPLOYMENT'),('incarnation','OLD_INCARNATION'),('state','UNKNOWN')]:
        bad=dict(current);bad[field]=replacement;decision=f.decide([bad,current,current],value,model_receipts)
        cases.demand('reference_replay_reject_'+field,decision['decision']=='DENY','REPLAY',dict(model_only=True,decision=decision))
    for failure in ['prepared_process_crash','applying_process_loss','database_commit_unknown','audit_terminal_failure','generation_write_uncertainty','native_replacement_uncertainty','guard_proof_uncertainty']:
        transition=f.begin(classes[0],failure,'TEST_REFERENCE_ACTOR','TEST_ONLY_UNKNOWN');tid=transition['transition_id']
        if failure!='prepared_process_crash':f.stage(tid,'APPLYING')
        f.stage(tid,'UNKNOWN');reopened=Fence(directory,**context)
        cases.demand('unknown_denies_'+failure,reopened.snapshot()['state']=='UNKNOWN' and reopened.decide([reopened.snapshot()]*3,value,model_receipts)['decision']=='DENY','UNKNOWN_OUTCOME',dict(injection=failure,scope='durable state-machine injection; not an actual host crash/native proof'))
        denied=False
        try:reopened.reconcile(tid,dict(context,transition_id=tid,outcome='UNKNOWN',independent_evidence_identity=None))
        except Denied:denied=True
        cases.demand('unknown_cannot_timeout_reconcile_'+failure,denied and reopened.snapshot()['state']=='UNKNOWN','RECONCILIATION',dict(model_only=True))
        reopened.reconcile(tid,dict(context,transition_id=tid,outcome='ROLLED_BACK',independent_evidence_identity='MODEL_ONLY_INDEPENDENT_EVIDENCE'));f=reopened
    # Actual child process dies after durable PREPARED; no clean exit handler
    # changes its state, and reopening cannot silently reset to STABLE.
    crash_dir=directory/'crash';code='import os,sys;sys.path.insert(0,sys.argv[1]);from package_0090_t10_46_fence import Fence;f=Fence(sys.argv[2],"d","i",initialize=True);f.begin("c","o","a","decision");os._exit(77)'
    child=subprocess.run([sys.executable,'-c',code,str(q.ROOT/'scripts/validation'),str(crash_dir)],capture_output=True)
    crashed=Fence(crash_dir,'d','i');cases.demand('actual_process_exit_preserves_nonstable',child.returncode==77 and crashed.snapshot()['state']=='PREPARED','UNKNOWN_OUTCOME',dict(exit_code=child.returncode,state=crashed.snapshot()['state']))
    crashed.journal.unlink();denied=False
    try:Fence(crash_dir,'d','i')
    except Denied:denied=True
    cases.demand('missing_durable_journal_does_not_reset_STABLE',denied,'UNKNOWN_OUTCOME',dict(actual_file_loss=True))
    records=f._read();export=dict(records=records,trusted_tip=records[-1]['record_hash'],context=context,scope='REFERENCE_PROTOCOL_MODEL_ONLY_NO_ACTIVATION_AUTHORITY',private_keys=False)
    save('audit-transition-binding.json',export)
    save('test-transition-fence.json',dict(states=sorted(Fence.STATES),implemented=True,scope='TEST_ONLY_REFERENCE_EXTERNAL_JOURNAL',complete_mutator_mediation=False,eligibility_without_complete_mediation='DENY',crash_recovers_to='PENDING/UNKNOWN, never assumed STABLE',OS_lock='Windows msvcrt one-byte exclusive lock / POSIX flock; cooperative users only',canonical_schema_changed=False))
    save('qualification-generation-v3.json',dict(monotonic_model_tests=True,initial=0,final=f.snapshot()['generation'],deployment=context['deployment'],incarnation=context['incarnation'],non_reusable=True,append_only_hash_chained_and_fsynced=True,ready_for_full_46_class_currentness=False,reason='No complete enforcement across direct ADMIN/owner/host mutators'))
    save('unknown-outcome-v3.json',dict(cases=[x for x in cases.rows if x['group']=='UNKNOWN_OUTCOME'],reference_protocol_fail_closed=True,full_T10_gate_proven=False))
    save('transition-reconciliation.json',dict(cases=[x for x in cases.rows if x['group']=='RECONCILIATION'],scope='Protocol model only; MODEL_ONLY evidence cannot authorize real reconciliation',complete_for_live_target=False))
    save('replay-v3.json',dict(cases=[x for x in cases.rows if x['group']=='REPLAY'],full_tuple_replay_proven=False,unproven=['old manifest observation','old audit tip','old native generation','old guard proof','old policy version','old binding identity','combined replay'],reason='Must not infer full native/audit/source replay protection from token tests'))
    return cases

def sql_cases():
    fk=next(x for x in old('constraint-v2.json')['constraints'] if x['source']['contype']=='CONSTR_FOREIGN' and x['relation']=='public.offline_readiness' and not x['source'].get('deferrable'))['source']['conname']
    index=old('index-v2.json')['indexes'][0];table=index['relation'];ix=index['name']
    source_fn='public.offline_read_history(uuid,bytea,uuid,text)'
    checks={
      'relation':('flooow_offline_control_owner','ALTER TABLE public.offline_binding_header ENABLE ROW LEVEL SECURITY','ALTER TABLE public.offline_binding_header DISABLE ROW LEVEL SECURITY',"SELECT relrowsecurity::text FROM pg_class WHERE oid='public.offline_binding_header'::regclass;"),
      'source_native_function':('flooow_offline_audit_owner','ALTER FUNCTION '+source_fn+" SET work_mem='65kB'",'ALTER FUNCTION '+source_fn+' RESET work_mem',"SELECT proconfig::text FROM pg_proc WHERE oid='"+source_fn+"'::regprocedure;"),
      'role':('postgres','ALTER ROLE test_0090_audit INHERIT','ALTER ROLE test_0090_audit NOINHERIT',"SELECT rolinherit::text FROM pg_roles WHERE rolname='test_0090_audit';"),
      'role_superuser':('postgres','ALTER DATABASE g3f4 OWNER TO flooow_offline_control_owner','ALTER DATABASE g3f4 OWNER TO postgres',"SELECT pg_get_userbyid(datdba) FROM pg_database WHERE datname=current_database();"),
      'membership_absence':('postgres','GRANT flooow_offline_audit_owner TO test_0090_audit','REVOKE flooow_offline_audit_owner FROM test_0090_audit',"SELECT count(*)::text FROM pg_auth_members WHERE member='test_0090_audit'::regrole;"),
      'effective_acl':('flooow_offline_control_owner','GRANT SELECT ON public.offline_binding_header TO test_0090_audit','REVOKE SELECT ON public.offline_binding_header FROM test_0090_audit',"SELECT has_table_privilege('test_0090_audit','public.offline_binding_header','SELECT')::text;"),
      'future_default_acl':('postgres','ALTER DEFAULT PRIVILEGES GRANT EXECUTE ON FUNCTIONS TO PUBLIC','ALTER DEFAULT PRIVILEGES REVOKE EXECUTE ON FUNCTIONS FROM PUBLIC',"SELECT COALESCE((SELECT defaclacl::text FROM pg_default_acl WHERE defaclrole='postgres'::regrole AND defaclobjtype='f' AND defaclnamespace=0),'NULL');"),
      'default_expression':('postgres',"ALTER TABLE public.flyway_schema_history ALTER COLUMN installed_on SET DEFAULT NULL",'ALTER TABLE public.flyway_schema_history ALTER COLUMN installed_on SET DEFAULT now()',"SELECT pg_get_expr(d.adbin,d.adrelid) FROM pg_attrdef d JOIN pg_attribute a ON a.attrelid=d.adrelid AND a.attnum=d.adnum WHERE d.adrelid='public.flyway_schema_history'::regclass AND a.attname='installed_on';"),
      'index':('postgres','ALTER INDEX public.'+ix+' RENAME TO probe_0090_renamed_index','ALTER INDEX public.probe_0090_renamed_index RENAME TO '+ix,"SELECT COALESCE(to_regclass('public."+ix+"')::text,'NULL');"),
      'trigger':('flooow_offline_control_owner','ALTER TABLE public.offline_binding_header DISABLE TRIGGER offline_header_original_input_immutable','ALTER TABLE public.offline_binding_header ENABLE TRIGGER offline_header_original_input_immutable',"SELECT tgenabled::text FROM pg_trigger WHERE tgrelid='public.offline_binding_header'::regclass AND tgname='offline_header_original_input_immutable';"),
      'constraint':('flooow_offline_control_owner','ALTER TABLE public.offline_readiness ALTER CONSTRAINT '+fk+' DEFERRABLE','ALTER TABLE public.offline_readiness ALTER CONSTRAINT '+fk+' NOT DEFERRABLE',"SELECT condeferrable::text FROM pg_constraint WHERE conrelid='public.offline_readiness'::regclass AND conname="+lit(fk)+';'),
      'return_consumer':('postgres','UPDATE public.flyway_schema_history SET checksum=checksum+1 WHERE installed_rank=1','UPDATE public.flyway_schema_history SET checksum=checksum-1 WHERE installed_rank=1','SELECT checksum::text FROM public.flyway_schema_history WHERE installed_rank=1;'),
      'column':('flooow_offline_control_owner','ALTER TABLE public.offline_binding_header ALTER COLUMN deployment_id DROP NOT NULL','ALTER TABLE public.offline_binding_header ALTER COLUMN deployment_id SET NOT NULL',"SELECT attnotnull::text FROM pg_attribute WHERE attrelid='public.offline_binding_header'::regclass AND attname='deployment_id';")}
    return checks

def qualify(sql,run,container,folder,record,fixture,runtime_work):
    cases=Cases(record['cases']);classes=load('mutation-denominator-freeze.json')['classes'];journal=Fence(Path(runtime_work)/'t10-journal',record['isolation']['project'],record['isolation']['id'],initialize=True);observed=[]
    record['recipe_hashes'][Path(__file__).name]=q.sha(Path(__file__).read_bytes())
    fence_path=q.ROOT/'scripts/validation/package_0090_t10_46_fence.py';record['recipe_hashes'][fence_path.name]=q.sha(fence_path.read_bytes())
    roles=json.loads(sql("SELECT jsonb_agg(jsonb_build_object('role',rolname,'superuser',rolsuper,'login',rolcanlogin,'createrole',rolcreaterole,'createdb',rolcreatedb) ORDER BY rolname) FROM pg_roles WHERE rolname='postgres' OR rolname LIKE 'flooow_offline_%_owner' OR rolname LIKE 'test_0090_%';").stdout)
    authority=json.loads(sql("SELECT jsonb_build_object('database_owner',(SELECT pg_get_userbyid(datdba) FROM pg_database WHERE datname=current_database()),'header_owner',(SELECT pg_get_userbyid(relowner) FROM pg_class WHERE oid='public.offline_binding_header'::regclass),'function_owner',(SELECT pg_get_userbyid(proowner) FROM pg_proc WHERE oid='public.offline_read_history(uuid,bytea,uuid,text)'::regprocedure),'control_can_create_public',has_schema_privilege('flooow_offline_control_owner','public','CREATE'),'memberships',(SELECT COALESCE(jsonb_agg(jsonb_build_object('role',pg_get_userbyid(roleid),'member',pg_get_userbyid(member),'admin',admin_option,'inherit',inherit_option,'set',set_option)),'[]'::jsonb) FROM pg_auth_members));").stdout)
    save('runtime-role-authority.json',dict(roles=roles,authority=authority,container=record['isolation'],scope='Owned disposable target only'))
    for role in ['test_0090_audit','test_0090_execution','test_0090_verification','test_0090_issuance']:
        result=sql('ALTER TABLE public.offline_binding_header ENABLE ROW LEVEL SECURITY;',role=role,check=False)
        cases.demand('operational_cannot_alter_'+role,result.returncode!=0,'AUTHORITY_MAP',dict(role=role,sqlstate='42501' if b'42501'in result.stderr else 'OTHER',denied=True))
    owner=sql("SELECT pg_get_userbyid(relowner) FROM pg_class WHERE oid='public.offline_binding_header'::regclass;").stdout.strip().decode()
    cases.demand('owner_is_catalog_proven',owner=='flooow_offline_control_owner','AUTHORITY_MAP',dict(observed_owner=owner,source='pg_class.relowner; not naming inference'))
    # Each mutation commits in an independent psql transaction after G2. These
    # are reviewed TEST ADMIN operations, not a hostile superuser exploit.
    for kind,(role,apply,undo,read) in sql_cases().items():
        before=sql(read).stdout.strip().decode();g0=journal.snapshot();g1=journal.snapshot();g2=journal.snapshot();changed=False
        try:
            result=sql('SET ROLE '+role+'; '+apply+';');changed=True;after=sql(read).stdout.strip().decode();last=journal.snapshot()
            actual_role=sql('SET ROLE '+role+'; SELECT current_user;').stdout.decode().splitlines()[-1]
            cases.demand('valid_committed_mutation_'+kind,before!=after and actual_role==role,'MUTATION',dict(class_id='0090/CURRENTNESS/'+kind,actor=role,before=before,after=after,sql=apply,committed_before_T10=True))
            silent=g0['generation']==g1['generation']==g2['generation']==last['generation'] and last['state']=='STABLE'
            weak_accept=all(x['generation']==g0['generation'] and x['state']=='STABLE' for x in [g0,g1,g2,last])
            details=dict(class_id='0090/CURRENTNESS/'+kind,actor=role,capability='object ownership via SET ROLE' if role!='postgres' else 'governed TEST ADMIN superuser',before=before,after=after,G0=g0,G1=g1,G2=g2,after_commit=last,committed_before_T10_DECISION=True,unmediated=silent,weak_generation_only_would_accept=weak_accept,actual_eligibility='DENY_FULL_GATE_NOT_PROVEN',sql=apply)
            observed.append(details)
            cases.check('mandatory_mediation_'+kind,not silent,'TOCTOU',details)
        finally:
            if changed:sql('SET ROLE '+role+'; '+undo+';')
        cases.demand('restored_'+kind,sql(read).stdout.strip().decode()==before,'MUTATION',dict(restored=True))
    path='/usr/lib/postgresql/18/lib/flooow_offline_mac32.so';before=run(['docker','exec',container,'sha256sum',path]).decode().split()[0];size=int(run(['docker','exec',container,'stat','-c','%s',path]).decode());uid=run(['docker','exec',container,'id','-u']).decode().strip();g2=journal.snapshot()
    try:
        run(['docker','exec',container,'sh','-c','printf x >> '+path]);after=run(['docker','exec',container,'sha256sum',path]).decode().split()[0];last=journal.snapshot()
        cases.demand('valid_native_module_mutation',uid=='0' and before!=after,'MUTATION',dict(actor='NATIVE_HOST_ROOT',uid=uid,path=path,before=before,after=after,scope='Owned disposable container file only; immutable image/source untouched'))
        details=dict(class_id='0090/CURRENTNESS/native_module',actor='NATIVE_HOST_ROOT',capability='Actual UID0 write to its owned target module',before=before,after=after,G2=g2,after_commit=last,committed_before_T10_DECISION=True,unmediated=g2==last,weak_generation_only_would_accept=g2==last,actual_eligibility='DENY_FULL_GATE_NOT_PROVEN')
        observed.append(details);cases.check('mandatory_mediation_native_module',g2!=last,'TOCTOU',details)
    finally:run(['docker','exec',container,'truncate','-s',str(size),path])
    cases.demand('restored_native_module',run(['docker','exec',container,'sha256sum',path]).decode().split()[0]==before,'MUTATION',dict(restored=True))
    # Demonstrate a genuine PostgreSQL prevention boundary for one owned
    # relation, without claiming it covers pg_proc/roles/external authorities.
    blocker="BEGIN; LOCK TABLE public.offline_binding_header IN SHARE MODE; SELECT pg_sleep(2); COMMIT;"
    import concurrent.futures,time
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        future=pool.submit(sql,blocker)
        for attempt in range(100):
            held=sql("SELECT count(*) FROM pg_locks WHERE relation='public.offline_binding_header'::regclass AND mode='ShareLock' AND granted;").stdout.strip()
            if held!=b'0':break
            time.sleep(.01)
        cases.demand('share_lock_actually_held',held!=b'0','DB_PROTECTION',dict(actual_pg_locks=True))
        result=sql("SET lock_timeout='150ms'; SET ROLE flooow_offline_control_owner; ALTER TABLE public.offline_binding_header ENABLE ROW LEVEL SECURITY;",check=False)
        cases.demand('share_lock_blocks_owner_DDL',result.returncode!=0 and b'55P03'in result.stderr,'DB_PROTECTION',dict(sqlstate='55P03',scope='One relation/probe only; not all class fields'))
        future.result()
    rows=[dict(x) for x in cases.rows]
    save('direct-mutation-runtime.json',dict(cases=rows,observations=observed,governed_mutation_mediation_proven=False,canonical_S04_executed=False))
    save('window-g2-t10.json',dict(status='FAIL',observations=observed,reason='Reviewed direct ADMIN/owner SQL commits after G2 without changing the external journal or acquiring its OS lock',hostile_superuser_protection_claimed=False))
    save('db-protection-v2.json',dict(tested=[r for r in rows if r['group']=='DB_PROTECTION'],complete_classes=[],partially_protected=['relation','column','constraint','index','trigger'],reobserved_classes=[],unprotected_classes=[c['CLASS_ID'] for c in classes],reason='One relation lock is not a full 46-class protection proof; no complete catalog/external protected decision exists'))
    q.require(sql('SELECT count(*) FROM public.offline_readiness;').stdout.strip()==b'0','No READY permitted')

def run_target():
    folder=OUT/'target-1';folder.mkdir(exist_ok=False)
    for name in ['active-fixture-manifest.json','expected-acl-manifest.json','source-function-contexts.json']:
        (folder/name).write_bytes((q.ROOT/'docs/evidence/package-0090-semantic-ledger-active-fixture-final'/name).read_bytes())
    import package_0090_active_foundation as foundation
    # Adapt the existing frozen driver without editing historical recipes.
    sys.modules['package_0090_reachable_v2_runtime']=types.SimpleNamespace(complete_qualification=qualify)
    sys.argv=[str(Path(foundation.__file__)),'--parser-path',str(Path.home()/'.codex/tmp/package0090-pglast-8.5'),'--directory',str(folder),'--reachable-v2']
    status=foundation.main();runtime=json.loads((folder/'foundation-runtime.json').read_text())
    return int(bool(status) or any(not row['passed'] for row in runtime['cases']))

if __name__=='__main__':
    if len(sys.argv)>1 and sys.argv[1]=='model':
        cases=model_tests(Cases());save('reference-protocol-tests.json',dict(cases=cases.rows,scope='Reference protocol only; not 46-class protection'));print(json.dumps(dict(tests=len(cases.rows),failures=sum(not r['passed'] for r in cases.rows))))
    else:raise SystemExit(run_target())
