"""Collect partial reachable expectations; never invent full graph/fence closure."""
import json
from pathlib import Path
import package_0090_source_closure as q
import package_0090_reachable_expectations as r


def walk(node,path=()):
    if isinstance(node,dict):
        for key,value in node.items():
            yield key,value,path+(key,)
            yield from walk(value,path+(key,))
    elif isinstance(node,list):
        for i,value in enumerate(node): yield from walk(value,path+(i,))


def prepare():
    prior=q.ROOT/'docs/evidence/package-0090-t10-governed-currentness-closure'
    paths=['docs/adr/ADR-0090-governed-offline-field-proof-exclusive-capability-composition.md','docs/specifications/SPEC-0090-governed-offline-field-proof-exclusive-capability-composition.md',q.V043.relative_to(q.ROOT).as_posix(),r.ADDENDUM.relative_to(q.ROOT).as_posix()]
    paths += ['docs/evidence/package-0090-complete-currentness-concurrent-100us/'+name for name in ['currentness-surface.json','currentness-classification-v2.json']]
    paths += [(prior/name).relative_to(q.ROOT).as_posix() for name in ['effective-acl-expectation.json','role-graph-expectation.json','function-identity-expectation.json','native-binding-expectation.json','audit-binding-expectation.json','policy-readiness-expectation.json']]
    freeze={}
    for path in paths:
        b=q.git('show',r.BASELINE+':'+path); q.require(b==(q.ROOT/path).read_bytes().replace(b'\r\n',b'\n'),'Frozen source changed: '+path)
        freeze[path]=dict(git_lf_sha256=q.sha(b),working_bytes_sha256=q.sha((q.ROOT/path).read_bytes()))
    q.require(freeze[q.V043.relative_to(q.ROOT).as_posix()]['git_lf_sha256']==q.SOURCE_HASH,'Canonical differs')
    refs={'main':'77d482c97a663a527dcacc85036c7577dfc92782','feature/room-v2-executive-product-evolution':'22181b5d821e343658928e6feaa06b96838757e2','research/global-commerce-signal-intelligence':'27019d7b3093b7a7d9aeb67d0c099756b13e005a'}
    for name,h in refs.items():
        for actual in [name,'origin/'+name]: q.require(q.git('rev-parse',actual).decode().strip()==h,'Protected ref changed')
    for p in q.MIGRATIONS.glob('V*.sql'):
        if int(p.name.split('__')[0][1:])<=42: q.require(q.git('show',q.FROZEN+':'+p.relative_to(q.ROOT).as_posix())==p.read_bytes().replace(b'\r\n',b'\n'),'Frozen migration differs')
    r.save('source-freeze.json',dict(baseline=r.BASELINE,initial_remote_head=r.BASELINE,initial_worktree_clean=True,inputs=freeze,protected_refs=refs))
    root=json.loads((prior/'effective-acl-expectation.json').read_text())['function']
    r.save('s04-root.json',dict(**root,argument_types=['uuid','bytea','uuid','text'],return_type='TABLE(installed_rank int4,version text,type text,script text,checksum int4,success bool)',OID_rule='Unique exact source signature and attributes under trusted qualification bootstrap; never identity from name/OID alone',execute_acl_rule='PUBLIC denied; audit-owner default ownership and direct test_0090_audit grant only',not_executed=True))
    source=json.loads(r.ADDENDUM.read_text()); calls=json.loads((r.OUT/'s04-expected-resolution.json').read_text())
    root_id='FUNCTION:public.offline_read_history(uuid,bytea,uuid,text)'; nodes={root_id:dict(id=root_id,type='FUNCTION',source='canonical S04 statement 1159')}; edges=[]
    for context in calls['contexts']:
        for site in context['sites']:
            target='FUNCTION:'+site['expected_signature']; nodes[target]=dict(id=target,type='FUNCTION',expected_oid=site['expected_oid'],provider_definition=site['provider_definition'])
            edges.append(dict(SOURCE_NODE=root_id,EDGE_KIND='FUNCTION_CALL',TARGET_NODE=target,SOURCE_LOCATION=site['source_location'],EXPECTED_BINDING_RULE=dict(signature=site['expected_signature'],input_types=site['input_types'],result_type=site['result_type']),RUNTIME_RESOLUTION_METHOD='Frozen-provider identity comparison and typed NULL-operand witness; canonical S04 expression consumer semantics remain UNBOUND'))
            if site['provider_definition'].get('prosupport'):
                support='FUNCTION:pg_catalog.'+site['provider_definition']['prosupport']; nodes[support]=dict(id=support,type='FUNCTION',resolution='PENDING_EXACT_IDENTITY')
                edges.append(dict(SOURCE_NODE=target,EDGE_KIND='PLANNER_SUPPORT_DEPENDENCY',TARGET_NODE=support,SOURCE_LOCATION='Frozen pg_proc.dat prosupport field',EXPECTED_BINDING_RULE='Exact provider support function; attributes/ACL/runtime comparison pending',RUNTIME_RESOLUTION_METHOD='NOT_EXECUTED'))
    for statement in source['statements']:
        for key,value,path in walk(statement['ast']):
            if key=='RangeVar':
                name=value.get('schemaname','UNQUALIFIED')+'.'+value['relname']; target='RELATION:'+name; nodes[target]=dict(id=target,type='RELATION')
                edges.append(dict(SOURCE_NODE=root_id,EDGE_KIND='RELATION_READ',TARGET_NODE=target,SOURCE_LOCATION=dict(statement_ordinal=statement['ordinal'],control_path=statement['control_path'],ast_path=path),EXPECTED_BINDING_RULE='Exact qualified source relation with separate owner/ACL/view/type expectations',RUNTIME_RESOLUTION_METHOD='Dependency expansion and full independent runtime comparison pending'))
    r.save('s04-reachability-graph.json',dict(complete=False,root=root_id,nodes=list(nodes.values()),edges=edges,call_sites=45,remaining=['190 operator/cast/implicit-expression sites have not been fully resolved','Column/type/default/sequence/constraint/trigger and pg_roles view dependency expansion incomplete','Planner support function requires exact expectation/runtime comparison','Native/readiness/audit current-target proof-reference graph not closed'],no_unrelated_V043_names_added=True))
    r.save('operator-cast-expectation.json',dict(complete=False,source_sites=source['operator_and_implicit_expression_sites_total'],sites=source['operator_and_implicit_expression_sites'],provider_operator_definitions_frozen=True,provider_cast_definitions_frozen=True,exact_site_to_operator_cast_binding_complete=False,unknown_literal_input_coercions_in_call_contexts_frozen=True))
    r.save('default-sequence-type-expectation.json',dict(complete=False,local_declaration_defaults=source['statements'][:3],read_only_does_not_itself_prove_all_dependencies_unreachable=True,missing='Independent reachable relation/view/column/type/default/sequence and constraint/trigger expansion with actual catalog comparison',provider_type_definitions_frozen=True))
    # Preserve expected submanifest's scope. Do not count unverified candidate
    # builtin privileges as independently closed effective access entries.
    acl=json.loads((prior/'effective-acl-expectation.json').read_text())
    r.save('effective-acl-v4.json',dict(complete=False,independent_direct_entries=len(acl['entries']),direct_submanifest_artifact=(prior/'effective-acl-expectation.json').relative_to(q.ROOT).as_posix(),new_reachable_builtin_owner_EXECUTE_schema_checks='Covered only in typed witnesses; full principal/PUBLIC/grant-option/closure expectation still pending'))
    r.save('function-identity-v4.json',dict(complete=False,root=root,reachable_call_functions=[nodes[k] for k in nodes if k.startswith('FUNCTION:pg_catalog.') and nodes[k].get('provider_definition')],remaining='Full operator/cast/type/array planner support function closure and privilege projections not yet complete'))
    for src,dst in [('policy-readiness-expectation.json','policy-readiness-contract.json'),('native-binding-expectation.json','native-proof-expectation-v4.json'),('audit-binding-expectation.json','audit-expectation-v4.json')]:
        prior_data=json.loads((prior/src).read_text())
        r.save(dst,dict(expected_rules_provenance=(prior/src).relative_to(q.ROOT).as_posix(),rules=prior_data,current_target_runtime_proof=False,historical_target_proof_not_reused=True,complete=False if src!='native-binding-expectation.json' else 'RULES_ONLY'))
    r.save('expected-currentness-manifest-v4.json',dict(complete=False,stop_phase=11,stop_instruction='If NO: STOP here. Do not continue into invalidation.',call_context_expectations_resolved=33,semantic_contexts_bound=0,remaining=['Complete operator/cast/column/type/default/view/constraint/trigger/planner-support dependency and effective privilege expectations','Complete policy/readiness/guard/current-target native/audit proof relationships'],observed_target_not_used_as_expected=True))


def collect():
    folder=r.OUT/'run-2'; runtime=json.loads((folder/'foundation-runtime.json').read_text())
    q.require(not runtime['errors'] and runtime['owned_runtime_destroyed'],'Runtime failed or not cleaned')
    proof=json.loads((folder/'resolution-identity-runtime.json').read_text())
    q.require(len(proof['cases'])==46 and all(x['passed'] for x in proof['cases']),'Resolution comparison incomplete')
    for filename,h in runtime['recipe_hashes'].items(): q.require(q.sha((q.ROOT/'scripts/validation'/filename).read_bytes())==h,'Recipe drift')
    failed=json.loads((r.OUT/'run-1/foundation-runtime.json').read_text())
    q.require(failed['owned_runtime_destroyed'] and len(failed['errors'])==1,'Development attempt accounting differs')
    r.save('development-attempts.json',dict(failed_disposable_attempt=failed['errors'],failed_assertions=1,superseded_not_counted=True,cleanup=True,correction='Parse observed OID JSON string losslessly as integer; compare independently frozen source OID and exact signature/result',preparation_errors=['Python urllib TLS reset; used curl with certificate verification','Encoding unknown-literal must resolve to name for convert_to/from; corrected using frozen provider signature'],preparation_errors_count=2))
    pending=dict(status='NOT_EXECUTED_PHASE_11_EXPECTATION_GATE_FAIL',production_protocol_claimed=False,reason='Complete independently expected manifest remains NO; explicit STOP before invalidation')
    for name in ['mutation-class-denominator.json','mutator-authority-map-v2.json','decision-fence-authority.json','qualification-currentness-generation-v2.json','transition-state-runtime.json','db-protection-map.json','t10-protocol-v2.json','mutation-detection-v3.json','t10-toctou-v3.json','unknown-outcome-v2.json','replay-v2.json','final-observer-v2.json','prebinding-v4.json','t10-coherence-v2.json']:
        r.save(name,pending)
    r.save('currentness-gate.json',dict(status='FAIL',stop_phase=11,context_expectations_total=33,context_expectations_resolved=33,context_expectations_unresolved=0,complete_reachability_graph=False,operator_cast_closure=False,semantic_bound=0,global_bound=0,global_unbound=851,new_resolution_tests=46,foundation_reused=93,measurement_samples=0,accepted_failures=0,failed_development_assertions=1,preparation_errors=2,benchmark_epochs=0))
    r.save('READINESS.json',dict(created=False,s04_executed=False,pipeline_built=False,current_target_native_proof_created=False,current_target_policy_activated=False,canonical_v043_executed=False,shared_db_contacted=False,production_contacted=False,execution_authority='BLOCKED',recovery_authority='BLOCKED',room_operational=False))
    report=q.ROOT/'docs/evidence/PACKAGE-0090-effective-expectation-t10-fence.md'
    report.write_text('''# Package 0090 reachable effective expectation and T10 fence\n\nCOMPLETE_CURRENTNESS_GATE=FAIL. The expected-manifest stop boundary is phase 11. No decision fence, generation, mutation denominator/campaign, TOCTOU, unknown-outcome/replay campaign, prebinding or final observer is implemented. No READY, header/original registration, auditor slot, S04 execution or concurrent benchmark occurred.\n\nThe 33 existing call candidate groups now have independent expected signatures, exact source-defined provider OIDs, operand/result types and unknown-literal input coercions. All 45 call sites remain attached to their original source/control paths. Exact declared parameters/locals and selected record-field types are traced to the frozen S04 source. PostgreSQL REL_18_4 pg_proc.dat, pg_proc.h, operator/cast/type definitions are frozen separately, not extracted from the live target. Function resolution follows [PostgreSQL type-resolution rules](https://www.postgresql.org/docs/18/typeconv-func.html); provider definitions come from the [official PostgreSQL REL_18_4 source](https://github.com/postgres/postgres/tree/REL_18_4/src/include/catalog).\n\nThis corrects previous static argument mistakes: bytea substring feeds convert_from; its encoding-name literal is coerced to name, not text. All three EXTRACT(EPOCH FROM timestamp subtraction) calls resolve to extract(text,interval). Polymorphic array_append retains distinct int8[] and text[] instantiated results. The original 33 groups remain UNBOUND; no consumer/error/NULL/security semantics are promoted by these expectation comparisons.\n\nA fresh disposable PostgreSQL 18.4 target passed 13 unique provider identity assertions (signature/result/source, owner/language/security/strictness/volatility/parallel/config) and 33 typed NULL-operand witnesses with audit-owner EXECUTE/schema checks. These witnesses compare concrete return types without invoking canonical S04 or its original expressions. They are not full runtime semantic binding. The 93 foundation assertions are reused separately, not counted as new.\n\nThe graph starts only at the actual S04 root. It records exact function-call and qualified relation-read source edges and identifies the array_append planner-support dependency. Graph completeness is NO: all 190 operator/cast/implicit-expression sites still require exact binding; view/column/type/default/sequence/constraint/trigger expansion and complete effective privilege closure remain pending. Frozen operator/cast catalogs alone are not a proof of expression resolution. No unrelated V043 names are added merely by textual presence.\n\nThe prior 3848 independent direct S04 effective access entries remain a scoped submanifest. They are not expanded into an unproven complete manifest. Native/audit/ready expectations retain prior source rules but no proof from a destroyed target is reused as current-target evidence. Readiness/guard-proof and current external audit-generation relationships remain incomplete.\n\nOne development target exposed OID JSON serialization as text; the assertion was corrected to perform lossless integer comparison to the independently frozen provider OID, with signature/result checks added, and rerun on a second fresh target. Both targets were destroyed. Two preparation errors (urllib TLS reset and encoding-name coercion) were corrected and recorded. All 46 accepted new assertions passed with Python -O; zero accepted failures, zero benchmark/observer measurement samples.\n\nCanonical V043, its fence, all V001–V042 migrations and protected refs remain unchanged; canonical V043 was not executed. Only the exact separately derived qualification body was applied in owned disposable targets. No shared or production database was contacted.\n\nNEXT, not executed: complete exact operator/cast/type/view/default/constraint/trigger/planner-support reachability and effective privileges, then independent readiness/native/current-audit proof-reference expectations. Only after the complete manifest passes may the authorized TEST-only T10 fence be implemented.\n''',encoding='utf-8')
    inputs={p.relative_to(q.ROOT).as_posix():q.sha(p.read_bytes()) for p in [Path(__file__),Path(r.__file__),q.ROOT/'scripts/validation/package_0090_active_foundation.py']}
    outputs={p.relative_to(q.ROOT).as_posix():q.sha(p.read_bytes()) for p in sorted(r.OUT.rglob('*')) if p.is_file() and p.name!='SHA256-MANIFEST.json'}
    outputs[report.relative_to(q.ROOT).as_posix()]=q.sha(report.read_bytes())
    r.save('SHA256-MANIFEST.json',dict(inputs=inputs,outputs=outputs,baseline=r.BASELINE,canonical_git_lf_sha256=q.SOURCE_HASH))
    print(json.dumps(dict(gate='FAIL',stop_phase=11,resolved_context_expectations=33,new_assertions=46,accepted_failures=0)))


if __name__=='__main__':
    import argparse
    ap=argparse.ArgumentParser(); ap.add_argument('--prepare',action='store_true'); args=ap.parse_args()
    prepare() if args.prepare else collect()
