"""Freeze independent graph, then close only two matching disposable proofs.

No database action, currentness generator, T10 fence or mutation campaign here.
"""
import argparse,collections,json,shutil,sys
from pathlib import Path
import package_0090_source_closure as q
from package_0090_reachable_v2 import OUT,save

MANIFEST='expected-currentness-manifest-v6.json'
COMPONENTS=['corrected-source-freeze.json','expression-site-v3.json','expression-successor-mapping.json','function-context-groups-v2.json','operator-resolution-v3.json','cast-resolution-v3.json','polymorphic-resolution-v2.json','unknown-literal-resolution-v2.json','type-reachability-v2.json','collation-v2.json','relation-view-v2.json','column-v2.json','default-expression-v2.json','sequence-v2.json','constraint-v2.json','trigger-v2.json','index-v2.json','storage-dependency-v2.json','planner-support-v2.json','catalog-resolution-surface-v2.json','observer-provider-v2.json','function-reachability-v2.json','function-identity-v6.json','resolution-candidate-metadata.json','selected-operator-provider-graph.json','effective-acl-v6.json','default-bootstrap-v2.json','role-graph-v2.json','policy-readiness-v3.json','native-proof-v6.json','native-provider-identities.json','audit-v6.json','return-consumer-edge.json','resolution-attack-v2.json','view-composite-bindings-v2.json','typed-parse-witnesses.json','consumer-parse-witnesses.json','S04-CORRECTED-FUNCTION.sql']

def get(name):return json.loads((OUT/name).read_text())
COMPONENTS.append('function-resolution-candidates-v2.json')
COMPONENTS.append('derivation-reproducibility-v2.json')
def digest_map(paths):return {p.relative_to(q.ROOT).as_posix():q.sha(p.read_bytes()) for p in sorted(paths)}

def freeze():
 q.require(not (OUT/MANIFEST).exists(),'Never overwrite a frozen release')
 expr=get('expression-site-v3.json');casts=get('cast-resolution-v3.json');calls=get('function-context-groups-v2.json')
 q.require(expr['total']==190 and expr['untyped']==0 and len({x['SITE_ID'] for x in expr['sites']})==190,'Expression denominator/typing')
 q.require(get('operator-resolution-v3.json')['resolved']==110 and casts['explicit_total']==14 and casts['unresolved_consumer_edges']==0,'Operator/coercion derivation')
 q.require(get('unknown-literal-resolution-v2.json')['unresolved']==0,'Unknown literals unresolved')
 q.require(calls['total']==33 and calls['resolved']==33 and calls['unresolved']==0,'Function context group denominator')
 # The independently derived expectations are not copied from this evidence;
 # a completed development run is only a preflight before the final two runs.
 developments=[p for p in OUT.glob('development-target-*/foundation-runtime.json') if not json.loads(p.read_text())['errors'] and json.loads(p.read_text()).get('cleanup')]
 q.require(developments,'Complete development preflight required')
 preflight=max(developments,key=lambda p:p.stat().st_mtime)
 q.require(all((preflight.parent/name).exists() for name in ['resolution-attack-runtime.json','corrected-runtime.json','view-composite-runtime.json','function-candidates-runtime.json']),'Preflight must include full current callback')
 acl=get('effective-acl-v6.json');acl.update(complete=True,completion_scope='Independent expected privileges, not live S04 eligibility');save('effective-acl-v6.json',acl)
 provider=digest_map([p for p in (OUT/'provider').rglob('*') if p.is_file()]);recipes=digest_map([p for p in (q.ROOT/'scripts/validation').glob('package_0090_*.py')]+[q.ROOT/'scripts/validation/Package0090SourceClosureFlyway.java'])
 inputs=[q.ROOT/'docs/evidence/PACKAGE-0090-G3F-3B-FIXTURE-001.json',q.ROOT/'docs/specifications/SPEC-0090-governed-offline-field-proof-exclusive-capability-composition.md',q.ROOT/'docs/evidence/package-0090-g3f4-full-domain-fixture-contract/NATIVE-HEALTH-DESIGN.json',q.ROOT/'docs/evidence/package-0090-s04-return-tuple-correction-applied/return-contract.json']
 for dirname,files in [('package-0090-semantic-ledger-active-fixture-final',['active-fixture-manifest.json','expected-acl-manifest.json','source-function-contexts.json']),('package-0090-test-activation-native-health-first-positive',['s04-source-addendum.json']),('package-0090-full-reachable-expectation-closure',['expression-site-denominator.json','return-tuple-expectation.json']),('package-0090-effective-expectation-t10-fence',['policy-readiness-contract.json','native-proof-expectation-v4.json','audit-expectation-v4.json']),('package-0090-t10-governed-currentness-closure',['unresolved-field-resolution.json','run-3/test-admin-audit-chain.json'])]:
  inputs.extend(q.ROOT/'docs/evidence'/dirname/f for f in files)
 parser_root=Path.home()/'.codex/tmp/package0090-pglast-8.5/pglast';external=[Path(sys.executable),Path(shutil.which('java')),Path(shutil.which('javac'))]+[p for p in parser_root.rglob('*') if p.is_file() and p.suffix in ['.py','.pyd']]+sorted((Path.home()/'.gradle/caches/modules-2/files-2.1').rglob('*.jar'))
 save('independent-input-freeze-v2.json',dict(provider_files=provider,recipe_files=recipes,normative_inputs=digest_map(inputs),external_toolchain={p.as_posix():q.sha(p.read_bytes()) for p in external},pglast_version='8.5',parser_scope='Syntax grammar18.6; selected provider/type/collation corroboration uses actual PG18.4',expected_values_observed_from_target=False,preflight_artifact=preflight.relative_to(q.ROOT).as_posix(),preflight_sha256=q.sha(preflight.read_bytes())))
 nodes=[];edges=[];node_ids=set()
 def add(kind,identity,fields,component,pointer,mutable=True):
  key=kind+':'+str(identity);q.require(key not in node_ids,'Duplicate graph node '+key);node_ids.add(key)
  nodes.append(dict(id=key,object_class=kind,fields=sorted(fields),component=component,pointer=pointer,mutable_currentness=mutable));return key
 def rows(kind,component,key,identity):
  for i,row in enumerate(get(component)[key]):add(kind,identity(row),row.keys(),component,'/'+key+'/'+str(i))
 rows('expression','expression-site-v3.json','sites',lambda x:x['SITE_ID'])
 rows('builtin_type','type-reachability-v2.json','types',lambda x:x['oid'])
 rows('builtin_function','function-identity-v6.json','provider_functions',lambda x:x['oid'])
 rows('function_candidate_signature','function-resolution-candidates-v2.json','functions',lambda x:x['oid'])
 rows('candidate_type_metadata','function-resolution-candidates-v2.json','types',lambda x:x['oid'])
 rows('source_native_function','function-identity-v6.json','source_profiles',lambda x:x['signature'])
 rows('relation','relation-view-v2.json','relations',lambda x:x['name'])
 rows('column','column-v2.json','columns',lambda x:x['relation']+'.'+x['name'])
 rows('constraint','constraint-v2.json','constraints',lambda x:x['relation']+'.'+x['source']['conname'])
 rows('index','index-v2.json','indexes',lambda x:x['relation']+'.'+x['name'])
 rows('trigger','trigger-v2.json','triggers',lambda x:x['relation']+'.'+x['source']['trigname'])
 rows('collation','collation-v2.json','providers',lambda x:x['oid'])
 rows('role','role-graph-v2.json','roles',lambda x:x['name'])
 for kind,component in [('policy_readiness_binding','policy-readiness-v3.json'),('native_binding','native-proof-v6.json'),('audit_binding','audit-v6.json')]:
  for i,row in enumerate(get(component)['rules']):add(kind,row['field'],[row['field']],component,'/rules/'+str(i))
 for component,key,kind in [('native-proof-v6.json','participants','native_participant'),('native-provider-identities.json','ELF_files','native_ELF'),('native-provider-identities.json','locale_data_files','native_locale')]:
  rows(kind,component,key,lambda x:x.get('PARTICIPANT_NAME',x.get('path')))
 native=get('native-provider-identities.json');add('native_module',native['custom_module']['path'],native['custom_module'].keys(),'native-provider-identities.json','/custom_module')
 for name in ['HEALTH_GUARD','HOST_PLATFORM']:add('native_anchor',name,get('native-proof-v6.json')[name].keys(),'native-proof-v6.json','/'+name)
 for table,entry in get('catalog-resolution-surface-v2.json')['tables'].items():
  for i,row in enumerate(entry['rows']):add('catalog_'+table,row.get('oid',row.get('aggfnoid')),row.keys(),'catalog-resolution-surface-v2.json','/tables/'+table+'/rows/'+str(i))
 for rel in get('relation-view-v2.json')['relations']:
  for kind in ['composite','array']:add('generated_'+kind,rel['name'],get('view-composite-bindings-v2.json')[kind+'_profile'].keys(),'view-composite-bindings-v2.json','/'+kind+'_profile')
 for i,parent in enumerate(get('storage-dependency-v2.json')['parents']):
  add('storage_binding',parent['parent'],parent.keys(),'storage-dependency-v2.json','/parents/'+str(i))
  if parent['required']:add('toast_factory',parent['parent'],get('storage-dependency-v2.json')['factory_flags'].keys(),'storage-dependency-v2.json','/factory_flags')
 for i,entry in enumerate(acl['entries']):add('effective_acl',str(i),['role','kind','object','column','privilege','allowed','grantable','binding'],'effective-acl-v6.json','/entries/'+str(i))
 for i,row in enumerate(get('default-expression-v2.json')['defaults']):add('default_expression',row['relation']+'.'+row['column'],row.keys(),'default-expression-v2.json','/defaults/'+str(i))
 for creator in get('default-bootstrap-v2.json')['creators']:
  for kind in get('default-bootstrap-v2.json')['object_kinds']:add('future_default_acl',creator+':'+kind,['creator','schema','object_kind','PUBLIC','owner','extra_grantees'],'default-bootstrap-v2.json','/')
 for name,fields,component in [('membership_absence',['roleid','member','grantor','admin_option','inherit_option','set_option'],'role-graph-v2.json'),('sequence_absence',['column_identity','default_nextval','owned_sequence_dependency'],'sequence-v2.json'),('inheritance_absence',['inhrelid','inhparent','partition_bounds'],'relation-view-v2.json'),('view_expansion',['full_view_query','owner','security_invoker','security_barrier','ordered_output'],'view-composite-bindings-v2.json'),('role_superuser',['rolsuper','rolcanlogin','implicit_database_owner'],'role-graph-v2.json'),('database_environment',['encoding','locale_provider','collate','ctype','locale_version','owner'],'collation-v2.json'),('session_environment',['session_user','effective_role','transaction_isolation','search_path','encoding','timezone','standard_conforming_strings'],'function-identity-v6.json'),('return_consumer',['declared_tuple','projected_tuple','ordered42rows','exact_content'],'return-consumer-edge.json'),('provider_ABI',['immutable_image','full_bootstrap_catalog','extension_versions','loaded_library_epoch'],'native-provider-identities.json'),('expected_release',['source_hash','recipe_hashes','provider_hashes','component_hashes','manifest_identity'],'corrected-source-freeze.json')]:add(name,name,fields,component,'/')
 # Each component is an explicit rule/value authority node. Detailed provider
 # edges below bind typed sites; source-factory nodes bind dynamic identities.
 for name in COMPONENTS+['independent-input-freeze-v2.json']:add('component',name,['sha256'],name,'/',False)
 for node in list(nodes):
  if node['object_class']!='component':edges.append(dict(source=node['id'],kind='independently_expected_by',target='component:'+node['component']))
 for site in expr['sites']:
  a=site['analysis'];source='expression:'+site['SITE_ID']
  if a['provider_oid']:edges.append(dict(source=source,kind='selected_function',target='builtin_function:'+a['provider_oid']))
  if a['type'] in {t['typname'] for t in get('type-reachability-v2.json')['types']}:
   t=next(t for t in get('type-reachability-v2.json')['types'] if t['typname']==a['type']);edges.append(dict(source=source,kind='result_type',target='builtin_type:'+t['oid']))
  for cast in a['casts']:
   if cast.get('provider_oid') not in [None,'0','-']:edges.append(dict(source=source,kind='coercion_provider',target='builtin_function:'+cast['provider_oid']))
 types=get('type-reachability-v2.json')['types'];type_oids={t['oid'] for t in types};functions=get('function-identity-v6.json')['provider_functions']
 for t in types:
  for field in ['typinput','typoutput','typreceive','typsend','typmodin','typmodout','typanalyze','typsubscript']:
   if t[field] not in ['0','-']:edges.append(dict(source='builtin_type:'+t['oid'],kind=field,target='builtin_function:'+t[field]))
  for field in ['typelem','typarray','typbasetype']:
   if t[field] not in ['0','-']:edges.append(dict(source='builtin_type:'+t['oid'],kind=field,target='builtin_type:'+t[field]))
 for p in functions:
  for oid in set(p['proargtypes'].split()+[p['prorettype']]):edges.append(dict(source='builtin_function:'+p['oid'],kind='signature_type',target='builtin_type:'+oid))
  if p['prosupport'] not in ['0','-']:edges.append(dict(source='builtin_function:'+p['oid'],kind='planner_support',target='builtin_function:'+p['prosupport']))
 for op in get('selected-operator-provider-graph.json')['operators']:
  for field in ['oprcode','oprrest','oprjoin']:
   if op[field] not in ['0','-']:edges.append(dict(source='catalog_pg_operator:'+op['oid'],kind=field,target='builtin_function:'+op[field]))
 for c in get('column-v2.json')['columns']:
  edges.append(dict(source='relation:'+c['relation'],kind='ordered_column',target='column:'+c['relation']+'.'+c['name']))
  t=next(t for t in types if t['typname']==c['type']);edges.append(dict(source='column:'+c['relation']+'.'+c['name'],kind='column_type',target='builtin_type:'+t['oid']))
 for dependency in ['pg_catalog.pg_authid','pg_catalog.pg_db_role_setting']:edges.append(dict(source='relation:pg_catalog.pg_roles',kind='owner_context_view_expansion',target='relation:'+dependency))
 for kind in ['S04_READ','INTEGRITY_METADATA','QUALIFICATION_OBSERVER','FUTURE_ELIGIBILITY_RULES']:add('scope_root',kind,['scope'],MANIFEST,'/',False)
 # Scope roots distinguish metadata/future rules from expressions actually
 # evaluated by S04. All nodes remain reviewable even if read-inactive.
 for node in list(nodes):
  k=node['object_class']
  if k in ['scope_root','component']:continue
  scope='FUTURE_ELIGIBILITY_RULES' if k in ['policy_readiness_binding','native_binding','audit_binding','native_participant','native_anchor'] else 'INTEGRITY_METADATA' if k in ['constraint','index','trigger','toast_factory','storage_binding','generated_composite','generated_array'] else 'QUALIFICATION_OBSERVER' if k.startswith('catalog_') else 'S04_READ'
  edges.append(dict(source='scope_root:'+scope,kind='scope_member_not_execution_claim',target=node['id']))
 ids={n['id'] for n in nodes};unresolved=[x for x in edges if x['source'] not in ids or x['target'] not in ids];q.require(not unresolved,'Unresolved graph edge')
 save('s04-reachability-graph-v3.json',dict(nodes=nodes,edges=edges,node_count=len(nodes),edge_count=len(edges),unresolved_nodes=[],unresolved_edges=[],complete=True,semantic_bound=False,scope='Independent expected S04 read graph plus explicitly separate integrity/qualification observer metadata and future eligibility rules. Trigger bodies not invoked on SELECT; metadata is still bound. PostgreSQL C/internal implementations are opaque provider boundaries bound to full immutable image/artifact/source, not claimed as globally expanded SQL dependencies.',historical_expression_sites=190))
 hashes={name:q.sha((OUT/name).read_bytes()) for name in COMPONENTS+['independent-input-freeze-v2.json','s04-reachability-graph-v3.json']}
 save(MANIFEST,dict(version=6,baseline=get('corrected-source-freeze.json')['baseline'],canonical_source_sha256=q.SOURCE_HASH,qualification_body_sha256=get('corrected-source-freeze.json')['body_sha'],components=hashes,component_gates={name:'COMPLETE_INDEPENDENT_EXPECTATION' for name in COMPONENTS},complete=True,semantic_bound=False,live_eligible=False,currentness_generator_implemented=False,final_consumer_invalidation_proven=False,authority='TEST_ONLY_EXPECTATION_QUALIFICATION; no V043 promotion/S04 execution/activation'))
 print(json.dumps(dict(manifest=q.sha((OUT/MANIFEST).read_bytes()),nodes=len(nodes),edges=len(edges))))

def verify_lock():
 manifest=get(MANIFEST)
 for name,digest in manifest['components'].items():q.require(q.sha((OUT/name).read_bytes())==digest,'Expected component drift '+name)
 inputs=get('independent-input-freeze-v2.json')
 for section in ['provider_files','recipe_files','normative_inputs']:
  for name,digest in inputs[section].items():q.require(q.sha((q.ROOT/name).read_bytes())==digest,'Frozen input drift '+name)
 for name,digest in inputs.get('external_toolchain',{}).items():q.require(q.sha(Path(name).read_bytes())==digest,'Frozen external toolchain drift '+name)
 return q.sha((OUT/MANIFEST).read_bytes())

def close():
 digest=verify_lock();targets=[]
 for number in [1,2]:
  folder=OUT/('target-'+str(number));path=folder/'foundation-runtime.json';runtime=json.loads(path.read_text());cases=runtime['cases']
  q.require(not runtime['errors'] and runtime['cleanup'] and all(c['passed'] for c in cases),'Target not fully passed/cleaned')
  q.require(runtime.get('expected_manifest_sha256_before')==digest==runtime.get('expected_manifest_sha256_after'),'Target manifest mismatch/drift')
  q.require(runtime['source_hash']==q.SOURCE_HASH and not runtime['canonical_v043_executed'],'Canonical boundary')
  result=dict(target=number,manifest_sha256=digest,matched=True,foundation_sha256=q.sha(path.read_bytes()),files={p.name:q.sha(p.read_bytes()) for p in sorted(folder.iterdir()) if p.is_file()},distinct_cases=len({(c.get('group'),c['name']) for c in cases}),cases=len(cases),groups=dict(collections.Counter(c.get('group','FOUNDATION') for c in cases)),cleanup=True,isolation=runtime['isolation'],canonical_S04_executed=False,live_eligible=False)
  save('runtime-match-target-'+str(number)+'.json',result);targets.append(result)
 q.require(targets[0]['isolation']['project']!=targets[1]['isolation']['project'],'Targets must have distinct ownership')
 one=json.loads((OUT/'target-1/foundation-runtime.json').read_text());two=json.loads((OUT/'target-2/foundation-runtime.json').read_text());keys=lambda x:{(c.get('group'),c['name']) for c in x['cases']};q.require(keys(one)==keys(two),'Reproducibility test denominator')
 save('reproducibility-v2.json',dict(reproducible=True,manifest_sha256=digest,targets=['runtime-match-target-1.json','runtime-match-target-2.json'],same_distinct_test_keys=True,total_distinct_tests=len(keys(one)),repeated_executions=len(one['cases'])+len(two['cases']),optimization_modes=['normal','python -O'],both_cleanup=True,expected_values_learned_from_target=False))
 # Derive classes only here, after both complete matching fresh targets.
 # Same object-class/field/protection mechanism => one class with full scope;
 # never invent a minimum list or count each repeated ACL assertion twice.
 graph=get('s04-reachability-graph-v3.json');groups=collections.defaultdict(list)
 for node in graph['nodes']:
  if node['mutable_currentness']:groups[node['object_class']].append(node)
 classes=[]
 for kind,nodes in sorted(groups.items()):
  sql=kind.startswith(('catalog_','builtin_','source_','generated_')) or kind in ['function_candidate_signature','candidate_type_metadata','relation','column','constraint','index','trigger','collation','role','effective_acl','future_default_acl','default_expression','storage_binding','toast_factory','membership_absence','sequence_absence','inheritance_absence','view_expansion','role_superuser','database_environment']
  classes.append(dict(CLASS_ID='0090/CURRENTNESS/'+kind,OBJECT_CLASS=kind,FIELDS=sorted({f for n in nodes for f in n['fields']}),GRAPH_OBJECTS=[n['id'] for n in nodes],MUTATION_OPERATIONS=['create/drop/replace/rename','alter identity/source/ownership/flags/ACL/dependencies','direct privileged catalog edit or provider replacement'] if sql else ['replace/revoke/enroll/restart','update generation/epoch/context/state/bytes/tip','loss/staleness/unprovable observation'],MUTATORS=['Governed ADMIN/owner','PostgreSQL superuser/provider administrator; operational identities cannot widen authority'] if sql else ['Independent trusted TEST bootstrap/audit/guard/HOST_PLATFORM/release authority as specified by each component'],CURRENTNESS_REQUIREMENT='Every listed graph object/field must still satisfy its frozen value or independently sourced generated-value rule at the final consuming T10; missing/unknown denies',REQUIRED_PROTECTION_OR_INVALIDATION='Governed qualification generation plus complete mutator coverage, monotonic invalidation and proven atomic final-consumer fence. Until separately implemented and proved, all execution/recovery authority remains blocked.'))
 save('mutation-class-denominator-v3.json',dict(authoritative=True,derived_after_manifest_and_two_matches=True,manifest_sha256=digest,classes=classes,total=len(classes),mutable_graph_objects=sum(len(v) for v in groups.values()),coverage='Every graph node marked mutable_currentness appears exactly once; fields union by shared object-class mutation/protection mechanism, full object scopes retained',campaign_executed=False,T10_implemented=False))
 print(json.dumps(dict(targets_match=True,distinct_tests=len(keys(one)),mutation_classes=len(classes))))

if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('phase',choices=['freeze','verify','close']);args=parser.parse_args()
 if args.phase=='freeze':freeze()
 elif args.phase=='verify':print(verify_lock())
 else:close()
