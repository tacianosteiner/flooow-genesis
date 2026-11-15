"""Continuation authorized by user 'continua': bounded C5J static work only."""
import collections
import copy
import functools
import hashlib
import itertools
import json
import pathlib
import re
import subprocess
import sys
sys.dont_write_bytecode=True
import role_closure as evaluator

P=pathlib.Path(__file__).resolve().parent;R=P.parents[2];I=P.with_name(P.name[:-1]+'i')
N1=R/'docs/evidence/package-0090-B01-v2-native-static-closure-r5n1'
SOURCE=R/'docs/evidence/package-0090-full-reachable-expectation-closure-v2/provider/acl.c'
BUILTIN=R/'docs/evidence/package-0090-B01-v2-native-static-closure-r5n2a3/postgres-source/src/include/catalog/pg_authid.dat'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
@functools.lru_cache(maxsize=None)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def canon(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
def rel(p):return p.relative_to(R).as_posix()
def ref(p,pointer=''):return {'path':rel(p),'sha256':sha(p),'pointer':pointer}
def write(n,x):(P/n).write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def git(*a):return subprocess.check_output(['git',*a],cwd=R,text=True).strip()
hist=read(I/'preflight.json')['historical_sha256'];hist.update(read(I/'SHA256-MANIFEST.json')['files']);hist[rel(I/'SHA256-MANIFEST.json')]=sha(I/'SHA256-MANIFEST.json')
assert len(hist)==9328 and all(sha(R/p)==h for p,h in hist.items())
prior=set(read(I/'preflight.json')['authorized_paths'])|set(read(I/'SHA256-MANIFEST.json')['files'])|{rel(I/'SHA256-MANIFEST.json')}
assert len(prior)==229
u=set(git('ls-files','--others','--exclude-standard').splitlines());assert not prior-u and all(x.startswith(rel(P)+'/') for x in u-prior)
assert git('rev-parse','HEAD')=='451265ff5b3d286eb4d27c4b3817c2f558f30123'
assert git('branch','--show-current')=='checkpoint/package-0090-cloud-handoff'
assert not git('diff','--name-only') and not git('diff','--cached','--name-only')
assert SOURCE.relative_to(R).as_posix() in hist and BUILTIN.relative_to(R).as_posix() in hist
assert sha(SOURCE)=='e2d27105df25c156028c148fdfab1c968922ac045f5c992b7c36793160fd6a71'
assert re.search(r"oid\s*=>\s*'6171',\s*oid_symbol\s*=>\s*'ROLE_PG_DATABASE_OWNER',\s*rolname\s*=>\s*'pg_database_owner'",BUILTIN.read_text())
assert evaluator.DATABASE_OWNER_ROLE_OID==6171
write('preflight.json',{'status':'PASS','branch':git('branch','--show-current'),'head':git('rev-parse','HEAD'),'frozen_baseline':'cbc284f62d9bd09b7169b55c8d66a3c51a68c6cb','authorized_untracked_before':229,'authorized_paths':sorted(prior),'historical_sha256':hist,'V043_sha256':read(I/'preflight.json')['V043_sha256'],'tracked_dirty':0,'staged':0})
write('authorization-and-scope.json',{'user_continuation':'continua','continued_from':ref(I/'final-summary.json'),'authorized_next_gate':'BOUNDED_COMPOUND_STATIC_GAP_DECOMPOSITION','bounded_work':'Group unchanged I fact blockers by source-scoped domains; implement independent local roleclosure for SET/INHERIT and scoped ADMIN from frozen semantics. No production code, database, network or new normative choice.','new_gate_label':'C5J local evidence namespace; no historical scope/report rewritten','canonical_witnesses_eligible_for_proof':0})

facts=read(I/'canonical-fact-registry.json')['facts'];assert len(facts)==14566
groups={}
for f in facts:
    key=f['CANONICAL_KEY'];scope=next((x for x in key if isinstance(x,dict)),{'scope':'FROZEN_SHARED_LITERAL'})
    definition=json.dumps(key,sort_keys=True)
    if f['STATUS']=='ESTABLISHED':domain='FROZEN_MODEL_CONSTANTS'
    elif f['STATUS']=='UNRESOLVED_CARDINALITY':domain='SOURCE_REQUIRED_COLLECTION_CARDINALITY'
    elif 'catalog_rows[]' in definition:domain='CATALOG_ROW_BINDINGS'
    elif 'REGISTRY/' in definition or 'WorkUse' in definition:domain='REGISTRY_AND_WORK_LINEAGE'
    elif any(x in definition for x in ['codec_trace/','source_constraint_trace/','binding_trace/']):domain='MECHANICAL_CONSTRAINT_ENCODING_AND_SOURCE_ADMISSION'
    elif any(x in definition for x in ['identity[','PrivateResourceRef','PrincipalRef','FRAME/','NESTED/']):domain='TYPED_NATIVE_PRINCIPAL_CREDENTIAL_AND_MESSAGE_BINDINGS'
    else:domain='OTHER_EXACT_MODEL_OR_OBSERVATION_BINDINGS'
    gkey={'context':scope,'domain':domain};gid='BLOCKER_GROUP/'+canon(gkey)
    g=groups.setdefault(gid,{'GROUP_ID':gid,'GROUP_KEY':gkey,'FACT_IDS':[],'statuses':collections.Counter(),'dependent_witnesses':set(),'minimum_closure':'Bind source facts or mechanically validate frozen symbolic terms and exact source constraints; no value invented. Grouping is work decomposition, not semantic fact deduplication or authority.'})
    g['FACT_IDS'].append(f['FACT_ID']);g['statuses'][f['STATUS']]+=1;g['dependent_witnesses'].update(f['DEPENDENT_WITNESSES'])
for g in groups.values():g['statuses']=dict(g['statuses']);g['dependent_witnesses']=sorted(g['dependent_witnesses'])
assert sum(len(g['FACT_IDS']) for g in groups.values())==14566
unresolved_groups=sum(any(k!='ESTABLISHED' and v for k,v in g['statuses'].items()) for g in groups.values())
write('compound-static-gap-decomposition.json',{'facts_total':14566,'source_context_work_groups_total':len(groups),'unresolved_blocker_groups_total':unresolved_groups,'supporting_resolved_groups_total':len(groups)-unresolved_groups,'groups':list(groups.values()),'no_fact_status_or_identity_changed':True,'unit':'Source-scoped engineering/evidence work groups including established supporting constants, not independent authority decisions or physical row counts','dominance':'Binding/cardinality and executable composition are coupled but neither alone supplies a complete canonical witness. Source-known executable composition can advance without inventing bound data.'})
write('role-closure-source-map.json',{'provider':ref(SOURCE),'provider_locations':{'roles_is_member_of':'lines5136-5248','is_admin_of_role':'lines5415-5427'},'project_predicates':ref(N1/'catalog-security-predicates.json','/predicates'),'project_edge_rules':ref(N1/'catalog-security-predicates.json','/role_edge_rules'),'builtin_binding':ref(BUILTIN),'builtin_constant':{'ROLE_PG_DATABASE_OWNER':6171,'rolname':'pg_database_owner','installed_row_existence_proven':False},'rules':['Reflexive source role seed','SET filters only set_option; INHERIT filters only inherit_option; MEMBER ignores both','Every reached current database owner has implicit pg_database_owner membership in all three traversals','Implicit membership is not an explicit row/admin_option grant','ADMIN examines explicit admin_option rows from MEMBER closure, preserving grantors/parallel rows','No arbitrary recursion cap; visited roles terminate finite cycles'],'scope':'Boolean closure/ADMIN property on validated consumed graph operands. Not general can_set_role/has_privs wrappers, full scalar encoding/ACL validation, source exhaustiveness or canonical qualification.'})
write('input-contract.json',{'input_keys':['roles','memberships','databases','database_context'],'row_projections':{'roles':sorted(evaluator.ROLE_FIELDS),'memberships':sorted(evaluator.MEMBER_FIELDS),'databases':sorted(evaluator.DB_FIELDS)},'database_context_variants':[{'kind':'DATABASE','database_oid':'source-bound exact current OID'},{'kind':'NO_DATABASE','meaning':'Explicit source no-database backend context; never inferred from missing row/None/zero'}],'consumed_fields_validated':'Exact nonzero OIDs, role endpoint/grantor references, independent boolean options, role superuser flag, exact current database owner, builtin OID/name, source name NFC/strictUTF8 and source int4 fields','external_gates':['Authenticated/exhaustive same-context source rowsets and source snapshot/cardinality proof','Name byte bounds and independent finite snapshot policy','Unused datacl element/encoding/ACL normalization; only NULL/array presence preserved locally','Canonical pre/post binding, parent full source-schema validation and decision/no-new-authority composition'],'parallel_rows':'Distinct membership OID/grantor rows retained; same OID rejected before traversal','outputs':{'availability':['AVAILABLE','UNAVAILABLE'],'value':'local boolean property iff AVAILABLE','no_automatic_mapping':['UNAVAILABLE to evidence UNKNOWN','UNAVAILABLE to qualification REJECT','local boolean to PROVEN']},'trace_scope':'Deterministic helper input-order BFS explanation, never provider-observed runtime order','canonical_fixture_or_snapshot_complete_claim':False})

def role(k,name=None,superuser=False):
    return {'oid':k,'rolname':name or 'UNIT_ROLE_'+str(k),'rolcanlogin':False,'rolinherit':False,'rolsuper':superuser,'rolcreaterole':False,'rolcreatedb':False,'rolreplication':False,'rolbypassrls':False}
def row(i,a,b,admin=False,inherit=False,set_role=False,grantor=3):
    return {'oid':10000+i,'roleid':b,'member':a,'grantor':grantor,'admin_option':admin,'inherit_option':inherit,'set_option':set_role}
def unit(rows,owner=None):
    return {'roles':[role(1),role(2),role(3),role(6171,'pg_database_owner')],'memberships':rows,'databases':[{'oid':55,'datname':'UNIT_DATABASE','datdba':owner or 1,'datallowconn':True,'datconnlimit':-1,'encoding':6,'datacl':None}],'database_context':{'kind':'NO_DATABASE'} if owner is None else {'kind':'DATABASE','database_oid':55}}

# Independent dense transitive-closure oracle, not the BFS implementation.
def reference(inputs,kind):
    ids=[r['oid'] for r in inputs['roles']];matrix={(a,b):a==b for a in ids for b in ids}
    for r in inputs['memberships']:
        if kind=='MEMBER' or r['set_option' if kind=='SET' else 'inherit_option']:matrix[r['member'],r['roleid']]=True
    ctx=inputs['database_context']
    if ctx['kind']=='DATABASE':
        dba=next(r['datdba'] for r in inputs['databases'] if r['oid']==ctx['database_oid']);matrix[dba,6171]=True
    for k in ids:
        for a in ids:
            for b in ids:matrix[a,b]=matrix[a,b] or (matrix[a,k] and matrix[k,b])
    return {b for b in ids if matrix[1,b]}
checks=0;digest=hashlib.sha256();coverage=collections.Counter()
edges=[(1,2),(2,3),(3,1)]
states=[None]+list(itertools.product([False,True],repeat=3))
for assignment in itertools.product(states,repeat=3):
    rows=[row(i,*edge,*bits) for i,(edge,bits) in enumerate(zip(edges,assignment)) if bits is not None]
    for owner in [None,1,2,3]:
        data=unit(rows,owner)
        for kind in ['MEMBER','SET','INHERIT']:
            result=evaluator.observe(data,kind,1,2);refset=reference(data,kind)
            assert result['availability']=='AVAILABLE' and result['value']==(2 in refset) and set(result['reached_roles'])==refset
            checks+=1;coverage[kind]+=1;digest.update(canon([assignment,owner,kind,result['value'],sorted(refset)]).encode())
        expected_admin=any(r['member'] in reference(data,'MEMBER') and r['roleid']==2 and r['admin_option'] for r in rows)
        result=evaluator.observe(data,'PROJECT_HAS_ADMIN_OPTION',1,2)
        assert result['availability']=='AVAILABLE' and result['value']==expected_admin
        checks+=1;coverage['PROJECT_HAS_ADMIN_OPTION']+=1;digest.update(canon([assignment,owner,'ADMIN',result['value']]).encode())
assert checks==11664

controls=[]
def unavailable(name,data,kind='SET',member=1,target=2):
    result=evaluator.observe(data,kind,member,target);assert result['availability']=='UNAVAILABLE',name
    controls.append({'name':name,'observed':result})
data=unit([]);data.pop('database_context');unavailable('missing context is not no database',data)
data=unit([],1);data['databases']=[];unavailable('missing exact current database row',data)
data=unit([],1);data['databases']*=2;unavailable('duplicate current database natural key retained',data)
data=unit([row(1,1,2),row(1,1,3)]);unavailable('duplicate membership OID not deduplicated',data)
data=unit([row(1,1,9)]);unavailable('dangling target endpoint',data)
data=unit([row(1,1,2)]);data['memberships'][0]['set_option']=1;unavailable('boolean numeric coercion rejected',data)
data=unit([]);data['roles'][0]['rolname']='bad\ud800';unavailable('strict UTF8 enforced',data)
data=unit([]);data['roles']=[r for r in data['roles'] if r['oid']!=6171];unavailable('builtin row not inferred from constant',data)
data=unit([]);unavailable('zero OID is not identity',data,member=0)
data=unit([]);unavailable('outside exact ADMIN R!=A domain',data,'PROJECT_HAS_ADMIN_OPTION',1,1)
data=unit([]);data['roles'][0]['rolsuper']=True;unavailable('self superuser remains outside scoped ADMIN domain',data,'PROJECT_HAS_ADMIN_OPTION',1,1)
parallel=unit([row(1,1,2,False,True,False,3),row(2,1,2,True,False,True,6171)])
assert evaluator.observe(parallel,'SET',1,2)['value'] and evaluator.observe(parallel,'INHERIT',1,2)['value'] and evaluator.observe(parallel,'PROJECT_HAS_ADMIN_OPTION',1,2)['value']
controls.append({'name':'parallel grants preserve grantor/options and ADMIN row','observed':'SET/INHERIT/ADMIN true; neither row overwritten'})
implicit=unit([row(1,1,2,False,True,True)],2)
assert all(evaluator.observe(implicit,k,1,6171)['value'] for k in ['MEMBER','SET','INHERIT'])
assert not evaluator.observe(implicit,'PROJECT_HAS_ADMIN_OPTION',1,6171)['value']
controls.append({'name':'transitively reached database owner has implicit edge in each class, never synthetic ADMIN','observed':True})
outgoing=unit([row(1,1,2,False,True,True),row(2,6171,3,True,True,True)],2)
assert all(evaluator.observe(outgoing,k,1,3)['value'] for k in ['MEMBER','SET','INHERIT','PROJECT_HAS_ADMIN_OPTION'])
controls.append({'name':'outgoing explicit edge from implicitly reached builtin retains SET/INHERIT/ADMIN flags','observed':True})
long=unit([row(i,i,i+1,False,False,True) for i in range(1,300)])
long['roles']=[role(i) for i in range(1,301)]+[role(6171,'pg_database_owner')]
assert evaluator.observe(long,'SET',1,300)['value']
controls.append({'name':'300-role UNIT chain has no arbitrary depth cap','observed':True})
superdata=unit([]);superdata['roles'][0]['rolsuper']=True
assert evaluator.observe(superdata,'PROJECT_HAS_ADMIN_OPTION',1,2)['value']
controls.append({'name':'distinct-target superuser branch in scoped project/provider agreement','observed':True})
def provider_admin_order_reference(superuser,member,target,explicit_admin):
    if superuser:return True
    if member==target:return False
    return explicit_admin
def project_admin_formula_reference(superuser,member,target,explicit_admin):
    return member!=target and (superuser or explicit_admin)
assert provider_admin_order_reference(True,1,1,False) is True
assert project_admin_formula_reference(True,1,1,False) is False
controls.append({'name':'static source-rule self-superuser counterexample','provider_rule_reference':True,'project_rule_reference':False,'provider_runtime_executed':False})
write('unit-verification.json',{'status':'PASS','reference_algorithm':'Independent dense Floyd-Warshall transitive closure versus deque BFS; ADMIN explicit edge query over reference MEMBER closure','exhaustive_normalized_unit_graph_checks':checks,'coverage':dict(coverage),'observation_digest':digest.hexdigest(),'negative_and_boundary_controls':controls,'data_generator':'decompose_and_verify.py unit()/row()/role(); UNIT_* inputs only','canonical_fixture_values_created':0,'canonical_witnesses_evaluated':0,'canonical_attacks_materialized':0,'canonical_attacks_evaluated':0,'full_source_snapshot_authentication_or_scalar_encoding_proven':False})
write('source-scope-divergence.json',{'finding':'ADMIN self-superuser ordering differs between frozen project predicate and general provider function','provider':{'source':ref(SOURCE),'rule':'superuser_arg(member) first -> TRUE, then member==role -> FALSE'},'project':{'source':ref(N1/'catalog-security-predicates.json','/predicates/7'),'rule':'AND(NE(member,target), OR(superuser,...))'},'counterexample_unit_state':{'member_equals_target':True,'member_superuser':True,'static_provider_rule_boolean':True,'static_project_formula_boolean':False,'provider_runtime_executed':False,'new_scoped_adapter':'UNAVAILABLE_OUTSIDE_R_NE_A_DOMAIN'},'canonical_scope':{'source':'C5D CLOSED_READER_AUTHORITY_MODEL role_rows R/A/M distinct; ADMIN case R nonsuperuser before mutation','affected_current_canonical_witnesses':0,'canonical_contradiction_or_disproof_claimed':False},'GENERAL_PROVIDER_EQUIVALENCE':False,'historical_evidence_repaired':False,'new_normative_choice':False,'minimum_safe_boundary':'Enforce frozen R!=A domain, preserve discrepancy, do not broaden general-provider equivalence or authority.'})
blocked=read(I/'blocked-evaluator-analysis.json')['classes']
addressed=[b for b in blocked if any(x in b['families'] for x in ['transitive_SET_ROLE','transitive_INHERIT','ADMIN_option_escalation'])]
assert len(addressed)==3
affected=sorted({w for b in addressed for w in b['AFFECTED_WITNESSES']});assert len(affected)==21
write('local-evaluator-extension.json',{'historical_C5I_local_functions':43,'new_scoped_local_program_implementations':3,'local_functions_available_with_declared_scope':46,'remaining_unimplemented_programs':3,'new_programs':[{'EVALUATOR_ID':b['BLOCKED_EVALUATOR_ID'],'PREDICATE_ID':b['PREDICATE_ID'],'families':b['families'],'SOURCE':ref(P/'role_closure.py'),'domain':'Validated consumed role-graph operands; ADMIN additionally R!=A; full source scalar/ACL/snapshot gates external','EXPECTED_RESULT_CONSUMED':'NO','SIDE_EFFECT_FREE':'YES','DATABASE_ACCESS':'NO','NETWORK_ACCESS':'NO','canonical_binding_and_composition_complete':False} for b in addressed],'affected_witnesses':affected,'all_affected_witnesses_remain_UNKNOWN':True,'complete_canonical_decision_evaluators':0,'legacy_evaluator_files_modified':False})
write('minimum-next-contract.json',{'next_action':'Source-normalized default ACL/SECURITY DEFINER/write-effect composition analysis, preserving input cardinality/binding gates','remaining_programs':[b['PREDICATE_ID'] for b in blocked if b not in addressed],'scope':'Technical source-derived work only. No database/runtime, guessed fixture values, new policy, old evidence edits, git add/commit/push.','binding_fact_root_statuses_changed':0,'canonical_fixture_completion':'NOT_ESTABLISHED','runtime_necessity':'NOT_ESTABLISHED','authority_required':'NOT_ESTABLISHED'})
summary={'BRANCH':git('branch','--show-current'),'BASELINE_HEAD':'cbc284f62d9bd09b7169b55c8d66a3c51a68c6cb','CURRENT_HEAD':git('rev-parse','HEAD'),'TRACKED_DIRTY_COUNT':0,'STAGED_COUNT':0,'AUTHORIZED_UNTRACKED_FILES_BEFORE':229,'C5I_INPUT_INTEGRITY':'PASS','CANONICAL_CASES_TOTAL':350,'CANONICAL_FACTS_UNCHANGED':14566,'BLOCKER_GROUPS_TOTAL':len(groups),'NEW_LOCAL_PROGRAM_IMPLEMENTATIONS':3,'LOCAL_PROGRAMS_AVAILABLE_WITH_DECLARED_SCOPE':46,'REMAINING_UNIMPLEMENTED_PROGRAMS':3,'CANONICAL_WITNESSES_AFFECTED_BUT_NOT_PROVEN':21,'GENERIC_UNIT_COMPARISONS':checks,'COMPLETE_CANONICAL_DECISION_EVALUATORS':0,'FIXTURES_COMPLETE':0,'STATICALLY_PROVEN':0,'STATICALLY_DISPROVEN':0,'UNKNOWN':350,'CONTRADICTED':0,'N1_SUBSTITUTION_STATIC_WITNESSES':'OPEN','N1_DECISIONS_CLOSED':11,'N1_DECISIONS_OPEN':1,'V2_NATIVE_STATIC_DESIGN_PROOF':'FAIL','V2_NATIVE_STATUS':'BLOCKED','PROJECT_AUTHORITY_TRANSITION':'T8','POSTMASTER_CONTEXT_BINDING_RESOLVED':'NO','INTERNAL_SCOPE_RESOLVED':'NO','ATOMIC_BOUNDARY_RESOLVED':'NO','CANONICAL_INTERNAL_OBLIGATION_UNIVERSE_ESTABLISHED':'NO','ATOMIC_NORMATIVE_CANDIDATES_TOTAL':108,'AMBIGUOUS_CANDIDATES_PRESERVED':105,'CANONICAL_ATTACK_DENOMINATOR':350,'DENOMINATOR_CHANGED':'NO','ATTACKS_MATERIALIZED_THIS_GATE':0,'ATTACKS_EVALUATED_THIS_GATE':0,'SHARED_DB_CONTACTED':'NO','PRODUCTION_CONTACTED':'NO','EXISTING_LOCAL_DB_CONTACTED':'NO','NETWORK_CONTACT_FOR_PROOF':'NO','V043_EXECUTED':'NO','V043_CHANGED':'NO','B02_EXECUTED':'NO','GIT_ADD':'NO','COMMIT':'NO','PUSH':'NO','SELECTED_OUTCOME':'COMPOUND_STATIC_GAPS_REMAIN_WITH_SCOPED_LOCAL_EVALUATOR_PROGRESS','NEXT_EXECUTED':False,'NEXT_GATE':'BOUNDED_REMAINING_STATIC_NORMALIZATION_AND_BINDING_CLOSURE'}
write('primary-result.json',{'result':summary['SELECTED_OUTCOME'],'scope':'Bounded continuation of C5I H routing, not a rewrite of C5I or a full canonical evaluator','progress':'Exact data/engineering groups preserved; implicit database-owner closure and scoped ADMIN implemented from frozen semantics, independently checked against dense closure reference.','limits':'No actual canonical binding/cardinality or source authentication proven. Full scalar/ACL validation remains external. Outside-domain ADMIN source difference is preserved, not repaired. No witness proof promoted.'})
summary['SOURCE_CONTEXT_WORK_GROUPS_TOTAL']=len(groups)
summary['BLOCKER_GROUPS_TOTAL']=unresolved_groups
summary['SUPPORTING_RESOLVED_GROUPS_TOTAL']=len(groups)-unresolved_groups
summary['UNIQUE_PREDICATES_TOTAL']=49
write('final-summary.json',summary)
print(json.dumps({'groups':len(groups),'local_implementations_added':3,'unit_checks':checks,'canonical_proofs':0,'unknown':350}))
