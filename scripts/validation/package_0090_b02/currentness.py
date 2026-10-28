"""B02 capability preflight. Never expands the frozen B01 actor/API vector.

Missing capability terminates class qualification, not the evidence record.
No negative capability finding is converted into a live currentness proof.
"""
import ast
import collections
import json
from pathlib import Path
import shutil
import subprocess
import sys
import zlib
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import package_0090_source_closure as q
import package_0090_sealed_boundary as b

BASELINE = '8e02abfb598989fe5327dbbc171176bec111160d'
OUT = q.ROOT/'docs/evidence/package-0090-B02-integrated-currentness-closure'
B01 = q.ROOT/'docs/evidence/package-0090-sealed-capability-mediation-boundary'
EXPECTED = q.ROOT/'docs/evidence/package-0090-full-reachable-expectation-closure-v2'
REPORT = q.ROOT/'docs/evidence/PACKAGE-0090-B02-integrated-currentness-closure.md'
WINDOWS = ['W'+str(i) for i in range(8)] + ['UNKNOWN','REPLAY']


def read(folder, name): return json.loads((folder/name).read_text())
def save(name, value): b.save(OUT, name, value)
def sha_file(path): return q.sha(path.read_bytes())


def frozen_inputs():
    baseline = read(OUT,'baseline-freeze.json')
    for path, sha in baseline['input_hashes'].items():
        q.require(sha_file(q.ROOT/path)==sha, 'Frozen B01/manifest input drift: '+path)
        q.require((q.ROOT/path).read_bytes()==q.git('show',BASELINE+':'+path),'Frozen file differs from baseline Git bytes')
    for ref, oid in baseline['protected_refs'].items():
        q.require(q.git('rev-parse',ref).decode().strip()==oid, 'Protected ref drift')
    return baseline


def mutation_api():
    tree=ast.parse(b.SERVICE.read_text())
    values=[]
    for node in ast.walk(tree):
        if isinstance(node,ast.Compare) and isinstance(node.left,ast.Subscript) and ast.unparse(node.left)=="request['op']" and any(isinstance(op,ast.NotIn) for op in node.ops):
            for target in node.comparators:
                if isinstance(target,ast.List):
                    items=ast.literal_eval(target)
                    if 'db_enable' in items: values.append(items)
    q.require(len(values)==1, 'Unambiguous frozen mutation allowlist required')
    return values[0]


def runtime():
    frozen_inputs()
    folder=OUT/'runtime-01';q.require(not folder.exists(),'Never overwrite a runtime attempt');folder.mkdir()
    cases=[]
    def case(name,passed,group,details):
        row=dict(name=name,passed=bool(passed),group=group,details=details);cases.append(row)
        save('tests-runtime.json',cases);q.require(passed,name)
    before=q.command(['docker','volume','ls','-q','--filter','label=com.docker.volume.anonymous']).stdout.decode().splitlines()
    inputs=q.ROOT/'docs/evidence/package-0090-semantic-ledger-active-fixture-final'
    for name in ['active-fixture-manifest.json','expected-acl-manifest.json','source-function-contexts.json']:shutil.copy2(inputs/name,folder/name)
    p=subprocess.Popen([sys.executable,str(Path(b.__file__)),'bootstrap','--directory',str(folder)],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    project=None
    try:
        stdout,stderr=p.communicate(timeout=600)
        save('bootstrap-process.json',dict(pid=p.pid,exit=p.returncode,stdout=stdout.decode(errors='replace'),stderr=stderr.decode(errors='replace'),exited_before_seal=True))
        q.require(p.returncode==0,'Frozen bootstrap failed; no promotion')
        receipt=read(folder,'handoff.json');project=receipt['project'];broker=receipt['endpoints']['broker'];native=receipt['endpoints']['native']
        case('bootstrap_exited_and_secret_files_unlinked',p.poll()==0 and p.pid==receipt['bootstrap_pid'] and not (Path(receipt['work'])/'postgres-password').exists() and not (Path(receipt['work'])/'flyway.properties').exists(),'B01_VECTOR',receipt['last_privileged_receipt'])
        state=b.call(broker,dict(op='seal'));save('fixture-initial-snapshot.json',state)
        case('fresh_exact_B01_epoch_sealed',state['eligible'] and state['state']=='SEALED' and not state['pending'],'B01_VECTOR',state)
        census=b.call(broker,dict(op='census'));save('database-census.json',census)
        old=read(B01/'clean-credential','database-census.json')
        normalize=lambda rows:sorted([{k:v for k,v in r.items() if k!='oid'} for r in rows],key=lambda r:r['rolname'])
        case('role_graph_and_effective_privileges_identical_to_B01',normalize(census['roles'])==normalize(old['roles']) and census['memberships']==old['memberships'] and census['ordinary_effective_paths']==old['ordinary_effective_paths'] and census['superuser_sessions']==0 and census['database_owner']==old['database_owner'],'B01_VECTOR',dict(memberships=census['memberships'],ordinary_paths=census['ordinary_effective_paths']))
        containers={}
        for actor in ['postgres','broker','native','campaign']:
            name=receipt['container'] if actor=='postgres' else project+'-'+actor
            d=json.loads(q.command(['docker','inspect',name]).stdout)[0]
            containers[actor]=dict(image=d['Image'],user=d['Config']['User'],readonly=d['HostConfig']['ReadonlyRootfs'],cap_drop=d['HostConfig']['CapDrop'],security=d['HostConfig']['SecurityOpt'],mounts=sorted([dict(destination=m['Destination'],type=m['Type'],rw=m['RW']) for m in d['Mounts']],key=lambda m:m['destination']),tmpfs=d['HostConfig']['Tmpfs'],pid_mode=d['HostConfig']['PidMode'],network_mode_is_owned=d['HostConfig']['NetworkMode']==project,env=d['Config']['Env'],host_socket_mounted=any('docker.sock' in m['Destination'] for m in d['Mounts']))
        save('container-census.json',containers)
        old=read(B01/'clean-credential','container-census.json')
        fields=['image','user','readonly','cap_drop','security','env']
        equal=all(all(value[k]==old[actor][k] for k in fields) and value['mounts']==sorted(old[actor]['mounts'],key=lambda m:m['destination']) and not value['host_socket_mounted'] and not value['pid_mode'] and value['network_mode_is_owned'] for actor,value in containers.items())
        case('confinement_mounts_images_and_namespaces_unchanged',equal,'B01_VECTOR',containers)
        native_state=b.call(native,dict(op='status'));save('native-status.json',native_state)
        case('same_single_TEST_native_enrollment_not_seven_canonical_participants',native_state['identity']['module']=='5aeedcdb693442b7738b6f33604e059094f584af29d1879bf35482ca06ef63b5' and native_state['identity']['pid']>0,'CLASS_CAPABILITY',dict(scope='B01 TEST participant only',native=native_state))
        def sql(statement,role):
            return q.command(['docker','exec','-i','--user','10004:10004',project+'-campaign','psql','-X','-w','-h',receipt['container'],'-U',role,'-d','g3f4','-At','-v','ON_ERROR_STOP=1','-v','VERBOSITY=verbose'],data=statement.encode(),check=False)
        identity=sql('SELECT current_user;','test_0090_audit')
        case('ordinary_SQL_transport_executes_as_exact_caller',identity.returncode==0 and identity.stdout.strip()==b'test_0090_audit','CLASS_CAPABILITY',dict(stdout=identity.stdout.decode(),exit=identity.returncode))
        history=sql('SELECT count(*) FROM public.flyway_schema_history;','test_0090_audit')
        case('frozen_caller_cannot_observe_required_return_history',history.returncode!=0 and b'42501' in history.stderr,'CLASS_CAPABILITY',dict(exit=history.returncode,stderr=history.stderr.decode(),interpretation='Expected capability denial, not B02 observer success'))
        observed=sql("SELECT has_function_privilege(current_user,'public.offline_read_history(uuid,bytea,uuid,text)','EXECUTE');",'test_0090_audit')
        acl=read(EXPECTED,'effective-acl-v6.json')
        expected=next(x for x in acl['entries'] if x['role']=='test_0090_audit' and x['kind']=='function' and x['object']=='public.offline_read_history(uuid,bytea,uuid,text)' and x['privilege']=='EXECUTE')
        mismatch=dict(component='effective-acl-v6.json',component_sha256=sha_file(EXPECTED/'effective-acl-v6.json'),expected_entry=expected,actual_allowed=observed.stdout.strip()==b't',actual_exit=observed.returncode,expected_memberships=read(EXPECTED,'role-graph-v2.json')['memberships_touching_these_roles'],actual_owner_memberships=[m for m in census['memberships'] if m['owner'] in b.OWNERS],full_observer_run=False)
        save('frozen-manifest-fixture-contradictions.json',mismatch)
        case('frozen_v6_fixture_contradiction_is_preserved_not_normalized',observed.returncode==0 and expected['allowed'] and not mismatch['actual_allowed'] and not mismatch['expected_memberships'] and bool(mismatch['actual_owner_memberships']),'REPRESENTATIVE_ADEQUACY',mismatch)
        for name,request in [('column_mutation',dict(op='db_column_set_not_null',fault='none')),('native_retarget',dict(op='native_replace',fault='none',target='canonical-participant')),('final_T10_operation',dict(op='final_t10',tuple=state['qualification_tuple']))]:
            before_state=b.call(broker,dict(op='status'));result=b.call(broker,request,check=False);after_state=b.call(broker,dict(op='status'))
            case('unqualified_API_'+name+'_denied', 'error' in result and before_state==after_state,'CLASS_CAPABILITY',dict(request=request,result=result,epoch_unchanged=True))
        mutations=[]
        for operation,value in [('db_enable',True),('db_disable',False)]:
            result=b.call(broker,dict(op=operation,fault='none'));actual=b.call(broker,dict(op='census'))['rls']
            q.require(actual==value and result['snapshot']['eligible'],'Existing RLS path failed')
            mutations.append(dict(operation=operation,result=result,actual_RLS=actual))
        save('existing-RLS-representative.json',dict(representatives=1,executions=2,mutations=mutations,not_a_W0_W7_or_T10_campaign=True))
        case('only_existing_DB_representative_works_without_expansion',len(mutations)==2,'CLASS_CAPABILITY',dict(representative='header RLS enable/disable',window_currentness_proven=False))
        after=b.call(broker,dict(op='status'));save('fixture-final-snapshot.json',after)
        required={'attempt_identity','epoch_id','generation','transition_state','deployment','incarnation','policy_identity','expected_manifest_digest','observed_manifest_digest','B01_vector_digest','audit_terminal_tip','native_epoch','participant_generations','guard_proof_identity','history_expectation_identity','return_consumer_identity','observer_execution_identity','decision_timestamp','decision_result'}
        missing=sorted(required-set(after['qualification_tuple']))
        save('decision-tuple-gap.json',dict(B01_tuple=after['qualification_tuple'],B02_required_fields=sorted(required),missing_exact_field_names=missing,semantic_aliases={'epoch':'epoch_id','native':'TEST native proof, not complete canonical participant vector'},new_T10_API_not_added=True))
        case('B01_boundary_tuple_is_not_claimed_as_full_B02_T10',bool(missing) and set(after['qualification_tuple'])=={'epoch','generation','native'},'REPRESENTATIVE_ADEQUACY',dict(fields=list(after['qualification_tuple']),missing=missing))
        save('runtime-audit.json',b.call(broker,dict(op='audit')))
    finally:
        if project is None and (folder/'handoff.json').exists():project=read(folder,'handoff.json')['project']
        if project:save('cleanup.json',b.cleanup(project))
        after=q.command(['docker','volume','ls','-q','--filter','label=com.docker.volume.anonymous']).stdout.decode().splitlines()
        save('anonymous-volume-comparison.json',dict(before=sorted(before),after=sorted(after),new_anonymous_volume_leaks=len(set(after)-set(before)),old_provenance_finding_unchanged=True,no_old_volume_deleted=True))


def build():
    baseline=frozen_inputs();tests=read(OUT,'tests-runtime.json')
    def test(name,passed,group,details):
        q.require(passed,name);tests.append(dict(name=name,passed=bool(passed),group=group,details=details))
    test('B01_baseline_sources_and_evidence_exact',True,'B01_VECTOR',dict(frozen_inputs=len(baseline['input_hashes'])))
    operations=mutation_api();test('frozen_mutation_API_is_closed_and_exact',operations==['db_enable','db_disable','native_replace'],'CLASS_CAPABILITY',operations)
    denominator=read(EXPECTED,'mutation-class-denominator-v3.json')
    classes=denominator['classes'];ids=[x['CLASS_ID'] for x in classes]
    test('exact_46_class_identity_and_field_denominator_retained',len(classes)==46 and len(set(ids))==46,'CLASS_CAPABILITY',dict(sha256=sha_file(EXPECTED/'mutation-class-denominator-v3.json')))
    graph=read(B01,'capability-actor-graph.json');authority=read(B01,'authority-map-v4.json');contract=read(B01,'mutation-broker-contract.json')
    vector_digest=q.sha(json.dumps(baseline['input_hashes'],sort_keys=True,separators=(',',':')).encode())
    save('b01-vector-freeze.json',dict(SEALED_MEDIATION_BASELINE_FROZEN=True,B01_VECTOR_CHANGED=False,vector_digest=vector_digest,identity_rule='Content-addressed B01 source/evidence input vector; generated runtime epoch/PID/port/OID values are not vector identities',baseline=baseline,actor_graph_sha256=sha_file(B01/'capability-actor-graph.json'),broker_source_sha256=sha_file(b.SERVICE),fixture_source_sha256=sha_file(Path(b.__file__)),native_delegate_participant_fence_generation_implementation='All are in the exact same frozen service source; no edits',operations=operations,contract=contract))
    save('mutation-denominator-freeze-v2.json',dict(sha256=sha_file(EXPECTED/'mutation-class-denominator-v3.json'),MUTATION_CLASS_DENOMINATOR_STABLE=True,denominator=denominator,no_merge_split_exclusion=True))
    rows=[]
    for source in classes:
        kind=source['OBJECT_CLASS'];old=next(x for x in authority['classes'] if x['CLASS_ID']==source['CLASS_ID'])
        available=kind=='relation'
        if available:
            reason='Existing fixed db_enable/db_disable changes only public.offline_binding_header.RLS. Valid narrow representative, not adequate for every relation/field/owner partition.'
            category='BROKER_DB'
        elif kind.startswith(('builtin_','catalog_')) or kind in ['native_ELF','native_module','native_locale','provider_ABI','expected_release','collation','database_environment','role','role_superuser']:
            reason='Protected definition/provider/admin path is unavailable in the sealed vector. Readonly/B01 immutability does not supply the mandatory live mutation representative; host/bootstrap intervention would change the qualified vector. No blanket window N/A is asserted.'
            category='IMMUTABLE_DURING_SEALED'
        elif kind.startswith('native_'):
            reason='B01 can restart only sealed-test-participant. This does not enroll/mutate the seven canonical participant contracts, native anchors, functional guard or complete native binding; retargeting/actor expansion requires a new B01 gate.'
            category='BROKER_NATIVE' if kind=='native_participant' else 'READONLY_OBSERVABLE_ONLY'
        elif kind=='audit_binding':
            reason='B01 journal is not the complete frozen approval/policy/deployment audit binding. No terminal-audit-write-failure operation or complete canonical binding mutation is exposed.';category='EXTERNAL_AUDIT'
        elif kind=='session_environment':
            reason='Caller-local SET affects an unbound helper connection, not a protected final consumer. Broker exposes no arbitrary consumer session mutation or final T10 decision operation.';category='SESSION_LOCAL'
        else:
            reason='SQL ownership held privately by broker is not an exposed capability for arbitrary DDL/DML. No fixed qualified broker operation mutates these exact protected objects/fields; new operation/target or privileges are required.';category='CAPABILITY_EXPANSION_REQUIRED'
        rows.append(dict(**source,classification=category,valid_existing_representative=available,CAPABILITY_EXPANSION_REQUIRED=not available,reason=reason,B01_capabilities=old['required_capabilities'],available_representatives=['public.offline_binding_header.RLS enable/disable'] if available else [],representative_coverage_complete=False,full_coverage_requires_requalification=True))
    save('class-capability-map.json',dict(classes=rows,CLASSES_WITH_EXISTING_CAPABILITY=1,CLASSES_REQUIRING_CAPABILITY_EXPANSION=45,count_definition='Phase 3: at least one exact protected representative. Relation alone has one; its complete phase-4 partitions also need broader operations/targets. All 46 remain unproven.',capability_expansion_performed=False,scope_invariant='No unsupported native TEST restart is counted as a canonical participant representative. No immutable class is excluded.'))
    relation=next(x for x in classes if x['OBJECT_CLASS']=='relation')
    test('one_RLS_target_does_not_cover_relation_mechanism_partitions',len(relation['GRAPH_OBJECTS'])==20 and set(relation['FIELDS'])-{'RLS'},'REPRESENTATIVE_ADEQUACY',dict(existing_target='header.RLS',objects=len(relation['GRAPH_OBJECTS']),uncovered_fields=sorted(set(relation['FIELDS'])-{'RLS'})))
    save('representative-adequacy.json',dict(MUTATION_REPRESENTATIVES_TOTAL=1,REPRESENTATIVE_COVERAGE_COMPLETE=False,existing_representative=read(OUT,'existing-RLS-representative.json'),relation_partition_gap=dict(GRAPH_OBJECTS=relation['GRAPH_OBJECTS'],FIELDS=relation['FIELDS'],uncovered='19 additional relation targets plus non-RLS owner/kind/persistence/name/view/force-RLS mechanisms'),other_classes='45 lack an exact representative. No per-field adequacy is inferred from shared capability labels.',complete_class_count=0))
    save('integrated-fixture-seal.json',dict(INTEGRATED_FIXTURE_SEALED=True,scope='Fresh exact B01 environment sealed for B02 capability preflight; full expected-manifest fixture integration is blocked',initial=read(OUT,'fixture-initial-snapshot.json'),final=read(OUT,'fixture-final-snapshot.json'),role_graph_exact=True,privilege_mount_HBA_credential_lifecycle_unchanged=True,expected_manifest_compatible=False,cleanup=read(OUT,'cleanup.json')))
    blocked=dict(status='NOT_EXECUTED_BLOCKED_NEEDS_MEDIATION_REQUALIFICATION',reason='Mandatory phase 32 negative gate: existing B01 cannot execute complete 46-class representatives. No expansion authorized in this tranche.',currentness_proven=False,no_model_substitute=True)
    save('qualification-generation-v4.json',dict(**blocked,QUALIFICATION_GENERATION_BOUND=False,existing_B01_tuple=read(OUT,'fixture-final-snapshot.json')['qualification_tuple'],required_B02_tuple_gap=read(OUT,'decision-tuple-gap.json'),B01_generation_semantics_changed=False))
    save('final-observer-contract.json',dict(**blocked,built=False,new_read_grants_or_broker_API=False,history_observation='Ordinary caller SELECT denied; no history read API exists',frozen_expected_manifest_sha256=sha_file(EXPECTED/'expected-currentness-manifest-v6.json'),canonical_S04_invoked=False))
    save('observer-logical-epoch.json',dict(**blocked,OBSERVER_LOGICAL_EPOCH_MODEL_DEFINED=False,required_model='A future governed observer must combine a DB consistency model with external native/audit/generation compatibility and actual protected final decision; a DB snapshot alone is insufficient',implemented=False))
    save('baseline-positive-observation.json',dict(status='COUNTEREXAMPLE_TO_BASELINE_COMPATIBILITY',BASELINE_OBSERVED_MANIFEST_MATCH=False,full_observer_executed=False,counterexamples=read(OUT,'frozen-manifest-fixture-contradictions.json'),observed_manifest_digest=None,expected_manifest_not_rewritten=True))
    coverage=[]
    for row in rows:
        coverage.append(dict(CLASS_ID=row['CLASS_ID'],REPRESENTATIVES=row['available_representatives'],CAPABILITY=row['classification'],**{w:dict(status='NOT_EXECUTED',reason=blocked['reason']) for w in WINDOWS},PREBINDING_CLASS=None,FINAL_STATUS='BLOCKED_NEEDS_MEDIATION_REQUALIFICATION',currentness_proven=False,reason=row['reason'],full_coverage_requires_requalification=True))
    save('class-campaign-46.json',dict(executed=False,classes=coverage,no_window_NA_or_PASS_inferred=True))
    save('class-coverage-46-v2.json',dict(classes=coverage,required=46,proven=0,unproven=46,denominator_stable=True))
    filenames=['window-pre-g0-v2.json','window-g0-observation-v2.json','window-during-observation-v2.json','window-observation-g1-v2.json','window-g1-native-v2.json','window-native-g2-v2.json','window-g2-t10-v2.json','window-post-t10-v2.json','unknown-pre-mutation-v2.json','unknown-post-commit-v2.json','unknown-native-v2.json','audit-failure-v2.json','replay-v4.json','t10-decision-tuple-v2.json','final-decision-boundary.json','coherence-adversarial.json','final-observer-target-1.json','final-observer-target-2.json','integrated-reproducibility.json']
    for name in filenames:save(name,dict(**blocked,live_B02_tests=0,B01_historical_proof_not_promoted=True))
    save('prebinding-v6.json',dict(**blocked,classification_performed=False,PREBOUND_FIELDS_FINAL=None,PER_EPOCH_FIELDS_FINAL=None,PER_EVENT_FIELDS_FINAL=None,FINAL_REOBSERVED_FIELDS=None,CURRENTNESS_PREBINDING_PROVEN=False,prior_916118_FINAL_REOBSERVED_not_carried_forward=True,fields_not_counted_as_tests=True))
    cleanup=read(OUT,'anonymous-volume-comparison.json')
    test('owned_preflight_runtime_destroyed_without_new_anonymous_leak',all(x['removed'] for x in read(OUT,'cleanup.json')) and cleanup['new_anonymous_volume_leaks']==0,'B01_VECTOR',cleanup)
    gate=dict(B01_VECTOR_CHANGED=False,SEALED_CAPABILITY_MEDIATION_GATE='PASS',B01_scope=read(B01,'mediation-gate.json')['scope'],ACTIVE_QUALIFICATION_ACTORS=graph['active_qualification_actors'],ACTIVE_MUTATION_CAPABILITY_EDGES=graph['active_mutation_capability_edges'],UNMEDIATED_ACTIVE_MUTATION_EDGES=0,CLASSES_WITH_EXISTING_CAPABILITY=1,CLASSES_REQUIRING_CAPABILITY_EXPANSION=45,MUTATION_REPRESENTATIVES_TOTAL=1,REPRESENTATIVE_COVERAGE_COMPLETE=False,INTEGRATED_FIXTURE_SEALED=True,QUALIFICATION_GENERATION_BOUND=False,OBSERVER_LOGICAL_EPOCH_MODEL_DEFINED=False,BASELINE_OBSERVED_MANIFEST_MATCH=False,CURRENTNESS_MUTATION_CLASSES_REQUIRED=46,CURRENTNESS_MUTATION_CLASSES_PROVEN=0,CURRENTNESS_MUTATION_CLASSES_UNPROVEN=46,B02_CURRENTNESS_INTEGRATION_GATE='BLOCKED',COMPLETE_CURRENTNESS_GATE='FAIL',PASS=False,NEXT='Requalify B01 with proposed expanded capability vector',NEXT_EXECUTED=False,capability_expansion_performed=False,full_observer_built=False,full_B02_campaign_run=False,scope='Capability preflight and live incompatibility evidence; no currentness completion claim')
    save('b02-gate.json',gate)
    save('READINESS.json',dict(READY=False,SEMANTIC_BOUND=False,readiness_created=False,S04_executed=False,execution_authority='BLOCKED',recovery_authority='BLOCKED',Room_operational=False,optimization_100us_started=False,production_mediation_component_created=False,production_currentness_schema_created=False,NEXT_executed=False))
    save('findings.json',dict(scope='Integrated currentness only',blocker_count=2,high_count=1,medium_count=0,low_count=0,blockers=[dict(id='B02-CAPABILITY',finding='45 classes have no exact representative; relation has only narrow RLS coverage. Requalification required before any operation/target/actor expansion.'),dict(id='B02-FINAL-BOUNDARY',finding='B01 tuple/API is a TEST boundary only; complete final consumer/read-history/audit-failure/atomic decision capabilities are absent.')],high=[dict(id='B02-FROZEN-FIXTURE',finding='Frozen v6 audit read_history EXECUTE entitlement and absence of touching owner memberships differ from the frozen sealed B01 fixture. Neither artifact was rewritten to manufacture a match.')],medium=[],low=[],residual_hygiene=dict(severity_unchanged='MEDIUM',source_sha256=sha_file(B01/'anonymous-volume-provenance-gap.json'),new_evidence_upgrade_or_downgrade=False,new_anonymous_volume_leaks=cleanup['new_anonymous_volume_leaks'])))
    source=q.git('show','HEAD:'+q.V043.relative_to(q.ROOT).as_posix());crc=0
    for line in source.decode('utf-8-sig').splitlines():crc=zlib.crc32(line.encode(),crc)
    q.require(q.sha(source)==q.SOURCE_HASH and source.count(q.FENCE)==1 and crc==1279591798,'Canonical source drift')
    migrations={}
    for p in sorted(q.MIGRATIONS.glob('V*.sql')):
        if int(p.name.split('__')[0][1:])<=42:
            rel=p.relative_to(q.ROOT).as_posix();data=q.git('show','HEAD:'+rel);q.require(data==q.git('show',BASELINE+':'+rel)==q.git('show',q.FROZEN+':'+rel),'Frozen migration drift');migrations[rel]=q.sha(data)
    save('source-integrity.json',dict(baseline=BASELINE,V043_Git_LF_SHA256=q.sha(source),Flyway_signed_CRC32=crc,V043_fence_present=True,canonical_V043_mutated=False,canonical_V043_executed=False,V001_V042_migrations=migrations,protected_refs=baseline['protected_refs'],B01_vector_changed=False,shared_DB_contacted=False,production_contacted=False,production_currentness_schema_created=False,production_mediation_component_created=False))
    groups=collections.Counter(x['group'] for x in tests);q.require(all(x['passed'] for x in tests),'Preflight validation failure')
    save('tests.json',dict(distinct_tests=len(tests),failures=0,groups=dict(groups),cases=tests,foundation_checks=93,foundation_checks_not_recounted=True,class_IDs_not_tests=True,zero_live_B02_mutation_window_tests=True,expected_negative_capability_findings_are_not_test_failures=True))
    report(gate,groups,len(tests))
    paths=sorted(p for p in OUT.rglob('*') if p.is_file() and p.name!='SHA256-MANIFEST.json')+[Path(__file__),Path(__file__).with_name('.gitattributes'),REPORT]
    report_rel=REPORT.relative_to(q.ROOT).as_posix()
    save('SHA256-MANIFEST.json',dict(self_excluded=True,git_LF_normalized_paths=[report_rel],files={p.relative_to(q.ROOT).as_posix():q.sha(p.read_bytes().replace(b'\r\n',b'\n') if p==REPORT else p.read_bytes()) for p in paths}))
    print(json.dumps(dict(gate='BLOCKED',existing=1,expansion=45,proven=0,tests=len(tests),groups=dict(groups))))


def report(gate,groups,total):
    text=f'''# Package 0090 — B02 integrated currentness closure

Status: **BLOCKED**, complete currentness **FAIL**, **0/46 proved**. B01 remains PASS only for its exact frozen TEST vector. Branch `checkpoint/package-0090-cloud-handoff`; input baseline `{BASELINE}`. Completion commit is the Git commit containing this report.

The prescribed negative gate applies: B01 deliberately exposes only header RLS enable/disable and replacement of one `sealed-test-participant`. Its private owner capability is not a raw SQL API. Phase 3 finds **one class with an exact narrow representative** (`relation`) and **45 classes requiring additional capability to execute an exact representative**. The relation class itself contains 20 relation objects and multiple non-RLS mechanisms; its complete phase-4 coverage also requires a broader target/operation vector. Therefore **no class has complete adequate coverage**. All 46 class IDs, fields, graph objects, mutators and requirements are retained without merges, exclusions or blanket window N/A claims.

A fresh PG18.4 disposable target was provisioned using the **unchanged B01 bootstrap/service**, with a separate exited provisioner, disabled postgres login and password, zero superuser client sessions, exact owner memberships and ordinary effective privileges, identical pinned images/mounts/confinement, and intact sealed journal. The controlled preflight used existing campaign/SQL/broker actors only. Header RLS enable and disable worked through the existing broker and were restored. They are **one representative/two executions**, not W0–W7 or T10 proofs. Native enrollment remained the single TEST identity; it was not substituted for the seven canonical participant contracts.

Live capability probes confirmed that an ordinary caller cannot SELECT protected Flyway history, and the broker rejects column mutation, native retargeting and a proposed final-T10 operation without changing epoch/generation. No unsupported operation, privilege, membership, actor or writable mount was added. B01 source/evidence hashes remain exact. Actor/capability counts remain 11/17 with zero B01 unmediated active edges; these historical boundary claims are not promoted into B02 currentness claims.

There is also a measured frozen-fixture contradiction. The v6 effective ACL entry permits `test_0090_audit` to EXECUTE `public.offline_read_history(uuid,bytea,uuid,text)`, whereas the sealed B01 fixture explicitly revoked runtime source functions and live `has_function_privilege` returns false. The frozen role component expects no memberships touching the Package roles, while B01 necessarily grants its private control-owner SET path. The report preserves both frozen inputs. It does not normalize those differences into an observed-manifest match or alter expected v6. See [contradictions](package-0090-B02-integrated-currentness-closure/frozen-manifest-fixture-contradictions.json).

B01's accepted tuple binds epoch, generation and a TEST native proof. It does not implement the full policy/manifest/deployment/incarnation/history/audit/observer decision contract. Adding a final mutation/decision API, broadening observation access or enrolling additional native participants would cross the user's explicit requalification boundary. Accordingly, no full final observer, full B02 tuple, window campaign, replay/coherence campaign, or terminal audit-write fault injection was built or claimed. All requested later artifacts explicitly record **NOT_EXECUTED_BLOCKED_NEEDS_MEDIATION_REQUALIFICATION**. Prebinding counts remain **unknown/null**, rather than inferred zero or automatically carrying forward 916118 FINAL_REOBSERVED fields.

Validation: **{total} distinct preflight tests, zero validation failures**; groups `{json.dumps(dict(groups),sort_keys=True)}`. Negative capability denials and the expected-manifest contradiction are expected preflight findings, not successful currentness qualifications. The 93 foundation checks are separately retained and not recounted. Class IDs and JSON leaves are not tests. See [gate](package-0090-B02-integrated-currentness-closure/b02-gate.json), [coverage](package-0090-B02-integrated-currentness-closure/class-coverage-46-v2.json), [capability map](package-0090-B02-integrated-currentness-closure/class-capability-map.json) and [test ledger](package-0090-B02-integrated-currentness-closure/tests.json).

Findings for integrated currentness: two blockers (complete representative capabilities; complete protected final decision/observation contract) and one high finding (frozen expected-manifest/B01 fixture incompatibility). The earlier anonymous-volume provenance finding remains **MEDIUM, separately**, with no severity change or assumed ownership. This preflight created no new anonymous volume leak; owned resources were label-checked and destroyed, with no pruning of old volumes.

Canonical V043 remains fenced, unmodified and unexecuted, SHA256 `{q.SOURCE_HASH}`, signed Flyway CRC32 `1279591798`. Only the previously authorized separately derived body was installed on the owned disposable fixture after exact V001–V042. Main, Room, research, canonical migrations, B01 source/evidence and the v6 denominator/manifest remain unchanged. No shared/production database, repair, READY, canonical S04, production component/schema, V043 promotion or 100µs work occurred. Execution/recovery remain blocked; Room is not operational.

Next, as mandated by phase 32: **requalify B01 with a proposed expanded capability vector**, including exact class/field partitions, controlled observation and protected final decision requirements, and a governed compatibility treatment for frozen expected inputs. **NEXT was not executed.** This blocked outcome preserves the already qualified security boundary.
'''
    REPORT.write_text(text,encoding='utf-8',newline='\n')


def verify():
    frozen_inputs();manifest=read(OUT,'SHA256-MANIFEST.json')
    for path,sha in manifest['files'].items():
        data=(q.ROOT/path).read_bytes()
        if path in manifest['git_LF_normalized_paths']:data=data.replace(b'\r\n',b'\n')
        q.require(q.sha(data)==sha,'Evidence drift: '+path)
    gate=read(OUT,'b02-gate.json');ready=read(OUT,'READINESS.json')
    q.require(gate['B02_CURRENTNESS_INTEGRATION_GATE']=='BLOCKED' and gate['CURRENTNESS_MUTATION_CLASSES_PROVEN']==0 and not gate['B01_VECTOR_CHANGED'] and not ready['READY'] and not gate['NEXT_EXECUTED'],'False promotion')
    print(json.dumps(dict(verified=True,files=len(manifest['files']),B01_unchanged=True,gate='BLOCKED',currentness_proven=0)))


if __name__=='__main__':
    if len(sys.argv)!=2 or sys.argv[1] not in ['runtime','build','verify']:raise SystemExit('runtime | build | verify')
    if sys.argv[1]=='runtime':runtime()
    elif sys.argv[1]=='build':build()
    else:verify()
