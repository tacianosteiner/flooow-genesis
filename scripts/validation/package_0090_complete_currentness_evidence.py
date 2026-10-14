"""Source-only expectations and fail-closed T10 currentness gate evidence."""
import argparse
import json
import zlib
from pathlib import Path
import package_0090_source_closure as q
import package_0090_complete_currentness as c

SPEC='docs/specifications/SPEC-0090-governed-offline-field-proof-exclusive-capability-composition.md'
NATIVE='docs/evidence/package-0090-g3f4-full-domain-fixture-contract/NATIVE-HEALTH-CONTRACT.md'
ADDENDUM='docs/evidence/package-0090-test-activation-native-health-first-positive/s04-source-addendum.json'
PRIOR='docs/evidence/package-0090-semantic-ledger-active-fixture-final/'


def save(name, value): (c.OUT/name).write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
def walk(v):
    if isinstance(v,dict):
        yield v
        for child in v.values(): yield from walk(child)
    elif isinstance(v,list):
        for child in v: yield from walk(child)


def prepare():
    c.OUT.mkdir(exist_ok=True)
    paths=[q.V043.relative_to(q.ROOT).as_posix(),SPEC,'docs/adr/ADR-0090-governed-offline-field-proof-exclusive-capability-composition.md',NATIVE,NATIVE.replace('NATIVE-HEALTH-CONTRACT.md','NATIVE-HEALTH-DESIGN.json'),ADDENDUM,'docs/evidence/package-0090-native-health-concurrent-100us/currentness-model.json','docs/evidence/package-0090-native-health-concurrent-100us/prebinding-proof.json']
    paths += [p.relative_to(q.ROOT).as_posix() for p in (q.ROOT/'docs/evidence/package-0090-native-health-100us-feasibility').glob('*.json')]
    freeze={}
    for path in paths:
        frozen=q.git('show',c.BASELINE+':'+path)
        q.require(frozen==(q.ROOT/path).read_bytes().replace(b'\r\n',b'\n'),'Source drift: '+path)
        freeze[path]=dict(git_lf_sha256=q.sha(frozen),working_bytes_sha256=q.sha((q.ROOT/path).read_bytes()))
    q.require(freeze[paths[0]]['git_lf_sha256']==q.SOURCE_HASH,'Canonical differs')
    refs={'main':'77d482c97a663a527dcacc85036c7577dfc92782','feature/room-v2-executive-product-evolution':'22181b5d821e343658928e6feaa06b96838757e2','research/global-commerce-signal-intelligence':'27019d7b3093b7a7d9aeb67d0c099756b13e005a'}
    for ref,head in refs.items():
        for name in [ref,'origin/'+ref]: q.require(q.git('rev-parse',name).decode().strip()==head,'Protected ref differs')
    save('source-freeze.json',dict(baseline=c.BASELINE,initial_head=c.BASELINE,initial_remote_head=c.BASELINE,initial_worktree_clean=True,sources=freeze,protected_refs=refs))
    add=json.loads((q.ROOT/ADDENDUM).read_text())
    relations=sorted({(node['RangeVar'].get('schemaname'),node['RangeVar'].get('relname')) for node in walk(add['statements']) if 'RangeVar' in node},key=str)
    groups={
        'database':'OID owner CONNECT CREATE TEMP PUBLIC_ACL grant_options allow_connections connection_limit relevant_role_settings',
        'schemas':'OID name owner USAGE CREATE PUBLIC_ACL grant_options',
        'roles':'OID name LOGIN SUPERUSER INHERIT CREATEROLE CREATEDB REPLICATION BYPASSRLS VALID_UNTIL connection_limit role_config',
        'memberships':'direct_edges inherited_closure roleid member grantor admin_option inherit_option set_option membership_graph',
        'functions':'OID name exact_signature owner security_mode language volatility strictness parallel search_path proconfig EXECUTE PUBLIC_EXECUTE grant_options prosrc probin prosqlbody argument_defaults argument_modes support leakproof return_type extension_dependency',
        'relations':'OID name namespace owner relkind persistence table_ACL column_ACL sequence_ACL grant_options RLS_flags forced_RLS reloptions view_rules index_identity partition_identity',
        'constraints_triggers':'constraint_OID PK UK FK CHECK exclusion_constraint constraint_definition validation deferrability initially_deferred trigger_OID trigger_enabled trigger_function trigger_arguments trigger_definition',
        'resolution_dependencies':'types casts operators collations languages extensions native_function_binding pg_depend pg_shdepend default_ACLs',
        'migration_history':'installed_rank version type script checksum success no_extra_rows table_owner table_ACL column_ACL',
        'policy':'version digest canonical_bytes effective_from current_reference registration_identity trusted_TEST_audit_terminal trusted_audit_tip',
        'readiness':'deployment incarnation policy_reference generation_vector history_expectation ACL_expectation health_proof_identity lifecycle_state watchdog_timestamp watchdog_healthy active_key_version',
        'binding_slot':'immutable_header binding_fingerprint canonical_manifest plan_reference policy_reference readiness_reference auditor_OID auditor_name deployment incarnation surface original_attestation lifecycle',
        'native':'binary_identity loaded_library_identity participant_generation process_identity pidfd_target enrollment authenticated_channel current_epoch nonce counter functional_result guard_identity host_root_identity incarnation_identity generation_registry_revision observer_liveness',
    }
    fields=[]
    for cls,names in groups.items():
        for name in names.split():
            unresolved=(cls=='native' or name in ['trusted_TEST_audit_terminal','trusted_audit_tip','generation_vector','health_proof_identity','registration_identity'])
            fields.append(dict(object_class=cls,field=name,provenance=[SPEC, NATIVE if cls=='native' else ADDENDUM,'User complete-currentness request phase 1'],classification='UNRESOLVED' if unresolved else 'MUST_BE_OBSERVED_AT_T10',why='Current accepted generation/publication/audit binding has not been fully implemented' if unresolved else 'Applicable mutable state can affect eligibility or name/type resolution',mutator='Trusted governed ADMIN/host; operational permissions require independent verification',mutation_operation='OS exec/replacement/enrollment/publication changes' if cls=='native' else 'Applicable ALTER/GRANT/REVOKE/DDL/DML or administrative registration',invalidates='Any relevant committed mismatch before final consumer event',concurrent_mutation_possible=True,protection_evidence='NOT_PROVEN',expected_source='Frozen source/accepted fixture/governance only',observed_source='SQL catalog/data tuples; external native/audit observation still incomplete'))
    save('currentness-surface.json',dict(scope='CONSERVATIVE_ENUMERATED_SURFACE_NOT_CLOSED_RUNTIME_DEPENDENCY_GRAPH',object_classes=list(groups),fields_total=len(fields),s04_static_relations=relations,static_call_sites=45,static_context_groups=33,static_operator_cast_sites=add['operator_and_implicit_expression_sites_total'],unbound_semantic_contexts=33,fields=fields))
    save('currentness-classification-v2.json',dict(fields=fields,unresolved=sum(x['classification']=='UNRESOLVED' for x in fields),classification_does_not_prove_observation_atomicity=True))
    history=[]
    for rank,p in enumerate(sorted(p for p in q.MIGRATIONS.glob('V*.sql') if int(p.name.split('__')[0][1:])<=42),1):
        b=q.git('show',c.BASELINE+':'+p.relative_to(q.ROOT).as_posix()); q.require(b==q.git('show',q.FROZEN+':'+p.relative_to(q.ROOT).as_posix()),'Frozen baseline differs')
        crc=0
        for line in b.decode('utf-8-sig').splitlines(): crc=zlib.crc32(line.encode(),crc)
        history.append(dict(installed_rank=rank,version=p.name.split('__')[0][1:],type='SQL',script=p.name,checksum=crc if crc<2**31 else crc-2**32,success=True))
    acl=json.loads((q.ROOT/PRIOR/'expected-acl-manifest.json').read_text())
    contexts=json.loads((q.ROOT/PRIOR/'source-function-contexts.json').read_text())
    # Source expectation stays explicitly partial. No bootstrap OID/owner/ACL or
    # arbitrary native identity is copied from runtime to fill missing entries.
    save('expected-currentness-manifest.json',dict(scope='INDEPENDENT_SOURCE_EXPECTATIONS_PARTIAL_NOT_ELIGIBLE',complete=False,provenance=list(freeze),history_rows=history,column_grants=acl['column_grants'],function_contexts=contexts,service_role_expectations=dict(roles=['test_0090_'+x for x in ['verification','issuance','execution','audit']],login=True,inherit=False,superuser=False,createdb=False,createrole=False,replication=False,bypassrls=False,memberships=[]),source_dependency_relations=relations,expected_policy_fixture='docs/evidence/PACKAGE-0090-G3F-3B-FIXTURE-001.json',missing=['Complete normalized effective database/schema/table/sequence/default/object ACLs including grant options and PUBLIC', 'Full independent constraints/triggers/type/operator/cast/extension resolution tuples', 'Independently accepted live native incarnation/generation/enrollment/loaded-image bindings', 'Current committed policy/audit/readiness/header/original references'],observed_values_used_as_expected=False))
    save('trusted-admin-model.json',dict(model='PARTIAL_IN_SCOPE_GOVERNED_MUTATIONS; HOSTILE_SUPERUSER_OUTSIDE_OPERATIONAL_ATTACKER_MODEL',authority=dict(source=SPEC,line=11,excerpt='Host/database superuser is trusted, outside operational attacker model, can bypass ACL/data/session authorization.'),additional_authority=[SPEC+':96',SPEC+':218','User phases 6,8,10'],reason='Hostile-superuser resistance is not claimed. Governed concurrent administrative transitions still must invalidate a pre-T10 observation in this qualification contract.',admin_mutation_impossible_assumed=False,superuser_counterexamples_prove_operational_impossibility=False))
    save('t10-decision-contract.json',dict(definition='Final qualification consumer event accepting all seven original-emission freshness bounds and all mutable dependencies',threshold_ns=100000,inclusive=True,clock='CLOCK_BOOTTIME',before_T10_invalidating_commit='DENY',after_T10_change='Does not retroactively invalidate completed decision',native_consumer_implemented=False,diagnostic_race_clock='Host perf_counter_ns; not a native BOOTTIME T10 or timing control',currentness_sql_isolation='READ COMMITTED diagnostic final observation; no retained-snapshot currentness claim',query_count=1,query_sha256=q.sha(c.QUERY.encode()),observation_fields=list(c.CATALOGS),atomic_final_observation_to_consumer_fence=False))


def collect():
    folder=c.OUT/'run-2'; runtime=json.loads((folder/'foundation-runtime.json').read_text())
    q.require(not runtime['errors'] and runtime['owned_runtime_destroyed'],'Runtime failed or not cleaned')
    proof=json.loads((folder/'runtime-results.json').read_text())
    q.require(all(x['passed'] for x in proof['cases']),'Assertion failure')
    for filename,h in runtime['recipe_hashes'].items(): q.require(q.sha((q.ROOT/'scripts/validation'/filename).read_bytes())==h,'Runtime recipe drift')
    observed=json.loads((folder/'observed-currentness-manifest.json').read_text())
    observed_file=folder/'observed-currentness-manifest.json'
    save('observed-currentness-manifest.json',dict(scope='OBSERVED_ONLY_NOT_EXPECTED',artifact=observed_file.relative_to(q.ROOT).as_posix(),artifact_sha256=q.sha(observed_file.read_bytes()),normalized_tuple_digest=observed['sha256'],observation_classes=list(observed['tuples']),normalized_tuples_retained_in_artifact=True))
    save('mutation-detection-matrix.json',dict(cases=proof['mutations'],detected_mutations=len(proof['mutations']),complete=False,not_proven=['Committed live policy/readiness divergence from valid activation/readiness','Native loaded binary/generation/channel/currentness mutations','All omitted/unbound resolution contexts'],copy_only_cases_not_live_proof=True))
    save('t10-toctou-results.json',dict(tests=proof['races'],characterization_tests=len(proof['races']),qualification_pass=False,unsafe_retained_final_observation_detected=True,remaining_race_coverage='Role class tested at six controlled phases; other classes and valid native controls are not race-qualified'))
    save('currentness-invalidation.json',dict(canonical_tokens=['Policy version/digest','Binding fingerprint','Incarnation identity','Execution generation (different scope; not global catalog revision)'],canonical_global_revision_exists=False,qualification_only_tokens=['Host diagnostic phase barriers and normalized observation SHA256; not mutation fences or production tokens'],protection_tests=['SHARE blocks history DML, not ALTER ROLE','Advisory lock does not bind uncoordinated ADMIN','Direct restricted LOGIN ALTER ROLE denied'],bypassing_mutator_exists=True,final_consumer_fence_proven=False,existing_revisions_cover_full_catalog=False))
    fields=json.loads((c.OUT/'currentness-classification-v2.json').read_text())
    blockers=['Independent effective catalog manifest is incomplete','Native and external trusted audit fields remain unresolved','No proven atomic protection/invalidation between final observation and T10','Valid policy/readiness and full mutable-class race coverage not executed']
    counts={}
    for row in proof['cases']: counts[row['group']]=counts.get(row['group'],0)+1
    failed=json.loads((c.OUT/'run-1/foundation-runtime.json').read_text())
    q.require(failed['owned_runtime_destroyed'] and len(failed['errors'])==1,'Failed development attempt cleanup or accounting differs')
    save('development-attempts.json',dict(superseded_attempt='run-1',errors=failed['errors'],counted_as_accepted_tests=False,destroyed=True,correction='Remove PostgreSQL 18-absent attcacheoff and normalize effective ACL defaults; retry on a new target'))
    save('currentness-gate.json',dict(status='FAIL',currentness_coverage_complete=False,expected_observed_separation_proven=True,expected_manifest_complete=False,mutation_detection_complete=False,unresolved_currentness_fields=fields['unresolved'],t10_toctou_pass=False,t10_currentness_proven=False,prebinding_proven=False,concurrent_snapshot_coherent=False,blockers=blockers,test_counts=counts,distinct_new_tests=len(proof['cases']),foundation_cases_reused=93,diagnostic_observation_samples=len(proof['observation_measurements_ns']),observation_query_count=1,minimum_diagnostic_observation_us=min(proof['observation_measurements_ns'])/1000,observation_latency_includes_local_TCP_query_transport_and_Python_decode=True,benchmark_epochs=0,pipeline_implemented=False,user_stop_boundary='Phase 13: If FAIL: STOP. Do not implement benchmark pipeline.',accepted_assertion_failures=0,development_attempt_failures=1))
    save('READINESS.json',dict(created=False,header_registered=False,original_registered=False,s04_executed=False,s04_rows=None,valid_fresh_control=False,native_ready=False,feasibility='INCONCLUSIVE',timing_amendment_required=False,s04_bound=0,s04_unbound=33,global_bound=0,global_unbound=851,canonical_executed=False,production_contacted=False,shared_db_contacted=False,execution_authority='BLOCKED',recovery_authority='BLOCKED',room_operational=False))
    report=q.ROOT/'docs/evidence/PACKAGE-0090-complete-currentness-concurrent-100us.md'
    report.write_text('''# Package 0090 complete currentness and concurrent 100us gate\n\nCOMPLETE_CURRENTNESS_GATE=FAIL. The tranche stopped at the explicit phase 13 boundary; the concurrent pipeline and benchmark were not implemented. Timing remains 100000ns inclusive. No READY, policy activation, header/original registration or S04 invocation occurred.\n\nThe observer retains normalized catalog/data tuples and their digest across 30 SQL observation classes, including complete role edges/options, owners, ACL arrays and grant options, function attributes/bodies, schema/database privileges, constraints/triggers, type/operator/cast/dependency catalogs and exact history/data state. This is broad observation coverage, not a complete independently expected eligibility manifest. Observed baseline tuples are used only to diagnose mutations/restoration and never as expected truth. Source-derived expectations separately contain the independently computed 42 history rows, 1040 column grants, function contexts, restricted role contract and S04 static relation references. Effective ACL, resolution and native expectation closure remains incomplete.\n\nTrusted hostile host/database superuser is outside the operational attacker model under SPEC-0090 line 11. Governed administrative transitions are still in scope for the requested committed-before-T10 qualification boundary. Counterexamples involving ADMIN do not establish impossibility against operational roles. Direct operational LOGIN ALTER ROLE attempts are tested and denied.\n\nReal catalog mutations exercise grants/revokes, column grant options, function EXECUTE/owner/search_path/security mode, table/schema owner, role membership/attributes, schema CREATE, database CONNECT, trigger enablement, constraints and history. VALID UNTIL is mutated in an actual writer transaction and rolled back; policy/readiness divergence is COPY_ONLY, not a live qualified state proof. All live catalog changes are checked for normalized restoration before target destruction.\n\nSix controlled role-mutation interleavings expose the final-observation-to-consumer gap: READ COMMITTED detects mutations committed before its statement, but a commit after that observation and before a retained-observation decision escapes. A change after a completed decision does not retroactively change that decision. These are host-clock characterization tests, not native T10 controls or complete multi-class TOCTOU qualification. RR history consistency is separately demonstrated to retain a stale committed history. SHARE blocks history DML but not role changes; advisory locks do not bind uncoordinated administrators.\n\nNo canonical global catalog invalidation token exists in the inspected contract. Existing policy/binding/incarnation/execution identities do not cover the full catalog and native health surface. Qualification hashes and diagnostic phase barriers supply no production revision semantics or final-consumer protection. Currentness gate failure reflects incomplete expectations, unresolved native/audit bindings, missing final-consumer invalidation and incomplete valid-state race coverage. It is not a 100us impossibility finding. Remaining legitimate mechanisms require further bounded implementation; no timing amendment is justified.\n\nThe only database was a newly labelled disposable PostgreSQL target. It used the unchanged V001–V042 baseline and separately derived V043 qualification body, never canonical V043. Foundation and new assertions are counted separately; measurements are not test cases. The target and private credentials were destroyed. Protected refs and migration source remain unchanged.\n\nNEXT, not executed: finish independent effective catalog/native/audit expectation bindings and implement a tested governed-writer/final-consumer invalidation boundary. Only after the complete currentness gate passes may the concurrent pipeline and >=1000 epochs per topology run.\n''',encoding='utf-8')
    report.write_text(report.read_text(encoding='utf-8') + '\nValidation: '+str(len(proof['cases']))+' distinct accepted new assertions ('+json.dumps(counts,sort_keys=True)+'), 93 reused foundation assertions, '+str(len(proof['observation_measurements_ns']))+' diagnostic full-observer samples, zero benchmark epochs. All accepted assertions passed with Python -O. One superseded development attempt failed on the PostgreSQL 18-absent attcacheoff column; its error and cleanup remain recorded. Both disposable targets were destroyed. The final diagnostic query minimum was '+str(min(proof['observation_measurements_ns'])/1000)+'us, including local TCP transport and Python decoding of full catalog tuples. This broad diagnostic measurement is not a native T10 observation, an optimized hot path, or an unavoidable timing lower bound.\n',encoding='utf-8')
    save('test-accounting.json',dict(new_distinct=len(proof['cases']),groups=counts,foundation_reused=93,observation_samples=len(proof['observation_measurements_ns']),benchmark_epochs=0,accepted_assertion_failures=0,development_attempt_failures=1,complete_TOCTOU_qualification_pass=False))
    manifest=dict(inputs={p.relative_to(q.ROOT).as_posix():q.sha(p.read_bytes()) for p in [Path(__file__),Path(c.__file__),q.ROOT/'scripts/validation/package_0090_active_foundation.py']},outputs={p.relative_to(q.ROOT).as_posix():q.sha(p.read_bytes()) for p in sorted(c.OUT.rglob('*')) if p.is_file() and p.name!='SHA256-MANIFEST.json'},canonical_git_lf_sha256=q.SOURCE_HASH,baseline=c.BASELINE)
    manifest['outputs'][report.relative_to(q.ROOT).as_posix()]=q.sha(report.read_bytes())
    save('SHA256-MANIFEST.json',manifest)
    print(json.dumps(dict(gate='FAIL',new_cases=len(proof['cases']),groups=counts,measurements=len(proof['observation_measurements_ns']),minimum_query_us=min(proof['observation_measurements_ns'])/1000,unresolved=fields['unresolved'],runtime_destroyed=True)))


if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('--prepare',action='store_true'); args=ap.parse_args()
    prepare() if args.prepare else collect()
