"""Read-only static ACL completeness, authority and preservation checks."""
import ast,collections,copy,json,sys
from derive import O,R,B,D,A3,rd,sha,git,interpret,ROOT
def evaluate():
    checks=[]
    def ck(n,v,category='INTEGRITY'):checks.append(dict(name=n,passed=bool(v),category=category))
    frozen=rd(O/'baseline-freeze.json');graph=rd(B/'catalog-effect-graph.json');reach=rd(O/'reader-graph-reachability.json');acl=rd(O/'effective-acl-ledger.json');completeness=rd(O/'acl-completeness.json');transitive=rd(O/'transitive-authority-proof.json');invariants=rd(O/'five-invariant-proofs.json')['invariants'];negative=rd(O/'forbidden-capability-negative-proof.json')['proofs'];future=rd(O/'future-implementation-boundary.json');steps={s['PRODUCER_STEP_ID']:s for s in rd(D/'G1-producer-execution-plan.json')['steps']};calls={c['CALLABLE_ID']:c for c in rd(D/'G2-callable-effect-universe.json')['callables']};nodes={n['id']:n for n in graph['nodes']};edgebyid={e['id']:e for e in graph['edges']};disposition={e['EDGE_ID']:e for e in reach['all_edge_dispositions']};entries={a['CAPABILITY_ID']:a for a in acl['entries']};sensitive={b['OUTPUT_FIELD_BINDING'] for b in rd(B/'canonical-binding-ledger.json')['bindings'] if b['GAP_TYPE']=='FIELD'};authority_types={'AUTHORITY/'+x for x in graph['canonical_authority_edge_types']}
    ck('branch',git('branch','--show-current')==frozen['branch']);ck('HEAD',git('rev-parse','HEAD')==frozen['head']);ck('tracking_ref',git('rev-parse','origin/checkpoint/package-0090-cloud-handoff')==frozen['remote_tracking_ref_head']);ck('tracked_clean',not git('diff','--name-only'));ck('staged_empty',not git('diff','--cached','--name-only'))
    for p,h in frozen['source_sha256'].items():ck('preserved:'+p,(R/p).is_file() and sha(R/p)==h)
    before=set(frozen['untracked_before_paths']);now=set(git('ls-files','--others','--exclude-standard').splitlines());prefix=O.relative_to(R).as_posix()+'/';report='docs/evidence/PACKAGE-0090-B01-v2-native-static-closure-r5n2a4-2.md'
    ck('263_baseline_preserved',len(before)==263 and before<=now);ck('authorized_scope_only',all(p in before or p.startswith(prefix) or p==report for p in now))
    ck('closed_390_graph',rd(B/'gate.json')['N1_CATALOG_EFFECT_GRAPH']=='CLOSED' and len(graph['edges'])==390 and reach['graph_sha256']==sha(B/'catalog-effect-graph.json'))
    ck('all390_dispositioned_once',len(disposition)==len(reach['all_edge_dispositions'])==390 and set(disposition)==set(edgebyid));ck('unique_acl_entries',len(entries)==len(acl['entries']))
    ck('8_stages_8_fixed_callables',len(steps)==len(calls)==8 and set(reach['stages_admitted'])==set(steps) and all(c['FIXED_OR_DYNAMIC']=='FIXED' for c in calls.values()))
    required={'EDGE_ID','SOURCE_NODE','TARGET_NODE','EDGE_TYPE','PRODUCER_STEP_ID','CALLABLE_ID','CALLER_PRINCIPAL','SESSION_PRINCIPAL','EFFECTIVE_PRINCIPAL','AUTHORITY_SOURCE','AUTHORITY_SCOPE','SOURCE_RELATION','SOURCE_FIELDS','PREDICATE_ID','TRANSFORMATION','OUTPUT_FIELDS','MUTATION_POSSIBILITY','ROLE_ESCALATION_POSSIBILITY','SECRET_ACCESS_POSSIBILITY','GENERIC_SQL_POSSIBILITY','ARBITRARY_OBJECT_POSSIBILITY','READER_REACHABILITY_REASON','READER_EFFECT'}
    for eid,e in edgebyid.items():
        actual=disposition[eid];expected=interpret(e,steps,nodes,sensitive,authority_types)
        ck('edge_fields:'+eid,required<=actual.keys(),'COVERAGE');ck('interpretation:'+eid,actual['classification']==expected,'SEMANTIC');ck('edge_to_acl:'+eid,entries['GRAPH/'+eid]['ACL_RESULT']==expected['result'] and entries['GRAPH/'+eid]['AUTHORITY_CRITICAL_UNRESOLVED']==expected['critical_unknown'],'SEMANTIC')
        ck('endpoints_preserved:'+eid,actual['SOURCE_NODE']==e['source_node'] and actual['TARGET_NODE']==e['target_node'])
        if e['edge_type'].startswith('AUTHORITY/'):
            symbolic=e.get('constructor_only') is True and e['source_node']=='SYMBOLIC_SOURCE/'+e['edge_type'].split('/',1)[1] and e['target_node']=='SYMBOLIC_TARGET/'+e['edge_type'].split('/',1)[1]
            public=e['edge_type']=='AUTHORITY/PUBLIC_ACL' and e['source_node']=='PRINCIPAL/PUBLIC' and nodes[e['target_node']]['kind']=='FROZEN_SOURCE_RELATION'
            ck('authority_template_not_real_grant:'+eid,symbolic or public,'SEMANTIC')
    actual_reach=[d for d in disposition.values() if d['classification']['reachable']];ck('reachable_edges_exact',{x['EDGE_ID'] for x in actual_reach}==set(reach['reachable_edge_ids']) and len(actual_reach)==len(reach['edges']))
    expected_nodes={ROOT}|{x[k] for x in actual_reach for k in ['SOURCE_NODE','TARGET_NODE']}|{n['id'] for n in graph['nodes'] if n['kind']=='ACTUAL_CREDENTIAL_REFERENCE'}|{'PREDICATE/'+p for p in completeness['predicate_ids']}
    ck('reachable_nodes_exact',set(reach['reachable_node_ids'])==expected_nodes and expected_nodes<=set(nodes))
    ck('no_critical_UNKNOWN',not any(a['AUTHORITY_CRITICAL_UNRESOLVED'] for a in acl['entries']),'STATIC_CLOSURE')
    ck('ACL_enum',all(a['ACL_RESULT'] in acl['allowed_result_enum'] for a in acl['entries']))
    ck('ACL_counts',dict(collections.Counter(a['ACL_RESULT'] for a in acl['entries']))==completeness['result_counts'])
    ck('all_relevant_families',len(completeness['source_relation_ids'])==19 and len(completeness['projected_fields'])==146 and len(completeness['predicate_ids'])==26 and len(completeness['credential_edge_ids'])==8 and not completeness['omitted_edge_ids'])
    for sid,s in steps.items():
        c=calls[s['TRANSFORMER_ID']];ck('call_effects:'+sid,all(c[k] is False for k in ['MUTATION_CAPABILITY','ROLE_ESCALATION_CAPABILITY','GENERIC_SQL_CAPABILITY','ARBITRARY_OBJECT_CAPABILITY','SECRET_ACCESS_CAPABILITY','IDENTIFIER_PARAMETERS_ALLOWED','SQL_TEXT_PARAMETERS_ALLOWED','OBJECT_NAME_PARAMETERS_ALLOWED']),'SEMANTIC')
        if sid in ['S06','S07','S08']:ck('pure_no_source:'+sid,s['SESSION_PRINCIPAL']=='NONE_NO_DATABASE_SESSION' and s['INPUT_CREDENTIAL_CLASS']=='NONE' and not s['SOURCE_FIELD_SET'])
    # Independently walk the capability-state transition graph to recompute direct and transitive effects.
    reachable={ROOT};witness={ROOT:[]}
    while True:
        old=len(reachable)
        for t in transitive['transitions']:
            if t['from_state'] in reachable and t['to_state'] not in reachable:reachable.add(t['to_state']);witness[t['to_state']]=witness[t['from_state']]+[t]
        if len(reachable)==old:break
    ck('transitive_fixed_point',reachable==set(transitive['visited_states']))
    for i,proof in enumerate(negative):
        category=proof['CAPABILITY'];positive=[t for t in transitive['transitions'] if t['from_state'] in reachable and t['effect_flags'][category] is True];unknown=[t for t in transitive['transitions'] if t['from_state'] in reachable and type(t['effect_flags'][category]) is not bool]
        ck('negative_direct_and_transitive:'+category,not positive and not unknown and not proof['POSITIVE_GRANT_OR_EFFECT'] and not proof['TRANSITIVE_DERIVATION_PATHS'] and proof['RESULT']=='TRUE','STATIC_CLOSURE')
        ck('invariant:'+invariants[i]['INVARIANT'],invariants[i]['VALUE']=='TRUE' and invariants[i]['negative_capability']==category and not invariants[i]['critical_unknown_edges'],'STATIC_CLOSURE')
        # A forbidden effect at a reachable second hop must falsify absence, not be hidden by direct-entry checks.
        modified=copy.deepcopy(transitive['transitions']);second=next(t for t in modified if t['mode']=='BOUNDED_DATA_NOT_AUTHORITY');second['effect_flags'][category]=True
        ck('detect_transitive_forbidden_effect:'+category,any(t['from_state'] in reachable and t['effect_flags'][category] is True for t in modified),'ADVERSARIAL')
    for category,ctype in [('wrong_principal','AUTHORITY/OWNS'),('direct_grant','AUTHORITY/DIRECT_ACL')]:
        malicious=copy.deepcopy(next(e for e in graph['edges'] if e['edge_type']==ctype));malicious['source_node']=ROOT;malicious['constructor_only']=False
        result=interpret(malicious,steps,nodes,sensitive,authority_types);ck('actual_authority_not_demoted:'+category,result['critical_unknown'] and result['result']!='DENY','ADVERSARIAL')
    malicious=copy.deepcopy(graph['edges'][0]);malicious['edge_type']='EFFECT/UNCLASSIFIED';malicious.pop('producer_step',None);ck('unknown_not_DENY',interpret(malicious,steps,nodes,sensitive,authority_types)['critical_unknown'],'ADVERSARIAL')
    for pid in completeness['predicate_ids']:ck('predicate_coverage:'+pid,entries['PREDICATE/'+pid]['ACL_RESULT']=='ALLOW')
    for n in [n for n in graph['nodes'] if n['kind']=='ACTUAL_CREDENTIAL_REFERENCE']:
        a=entries['CREDENTIAL_METADATA/'+n['id']];ck('metadata_not_payload:'+n['id'],a['RESOURCE_SCOPE']['not_material_payload'] is True and a['ACL_RESULT']=='ALLOW' and a['OPERATION']=='READ_FIXED_GRAPH_REFERENCE_METADATA_ONLY')
    ck('identity_preserved',future['READER_PARTICIPANT_ID']=='AUXILIARY_READ_PROXY_NOT_ONE_OF_SEVEN_NATIVE_PARTICIPANTS' and future['READER_PRINCIPAL_ID']=='R5N1_READ_PROXY_LOGICAL_PRINCIPAL')
    ck('physical_and_runtime_future',future['PHYSICAL_ACL_IMPLEMENTATION_PROOF']==future['RUNTIME_ACL_PROOF']=='FUTURE')
    review=rd(O/'independent-review.json');adversarial=rd(O/'adversarial-review.json');ck('independent_review_PASS',review['INDEPENDENT_READER_ACL_REVIEW']=='PASS','STATIC_CLOSURE');ck('no_open_adversarial_findings',adversarial['READER_ACL_ADVERSARIAL_FINDINGS_OPEN']==0,'STATIC_CLOSURE')
    for p,h in review.get('source_sha256',{}).items():ck('review_hash:'+p,sha(R/p)==h)
    for p in O.glob('*.py'):ast.parse(p.read_text());ck('syntax:'+p.name,True)
    manifest=rd(O/'SHA256-MANIFEST.json')
    for p,h in manifest['files'].items():ck('sealed:'+p,sha(R/p)==h)
    actual={p.relative_to(R).as_posix() for p in O.rglob('*') if p.is_file() and p.name!='SHA256-MANIFEST.json'}|{report};ck('manifest_exact',actual==set(manifest['files']));ck('distinct_check_names',len(checks)==len({c['name'] for c in checks}))
    return dict(scope='STATIC_READER_ACL_DERIVATION_NOT_PHYSICAL_OR_RUNTIME',tests_distinct=len(checks),test_failures=sum(not c['passed'] for c in checks),integrity_failures=sum(not c['passed'] and c['category']=='INTEGRITY' for c in checks),checks=checks)
if __name__=='__main__':
    out=evaluate();print(json.dumps(out if '--detail' in sys.argv else {k:v for k,v in out.items() if k!='checks'}));sys.exit(bool(out['test_failures']))
