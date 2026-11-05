"""Offline semantic-contract graph verification; no runtime or Reader ACL evaluation."""
import ast,copy,hashlib,json,subprocess,sys
from pathlib import Path
O=Path(__file__).resolve().parent;R=O.parents[2];E=R/'docs/evidence';D=E/'package-0090-B01-v2-native-static-closure-r5n2a4-1d';P=E/'package-0090-B01-v2-native-static-closure-r5n2a4';A=E/'package-0090-B01-v2-native-static-closure-r5n2a4-1'
def rd(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def digest(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def git(*a):return subprocess.check_output(['git',*a],cwd=R).decode().strip()
def binding_ok(b,steps,calls,mapping,original):
    try:
        gid=b['GAP_ID'];m=mapping[gid];s=steps[m['DESIGN_PRODUCER_STEP_ID']];call=calls[m['DESIGN_CALLABLE_ID']];gap=original[gid]
        props=['CALLER_PRINCIPAL','SESSION_PRINCIPAL','EFFECTIVE_PRINCIPAL','AUTHORITY_SOURCE','AUTHORITY_SCOPE']
        field=gap.get('FIELD_ID');pid=gap.get('PREDICATE_ID');output=field or pid
        inputs=b['SOURCE_FIELD_BINDING'];covered=s['SOURCE_FIELD_SET'] if field else s['INPUT_FIELD_SET']
        expr=gap['SOURCE_FIELD_OR_EXPRESSION']['expression'] if field else gap['CURRENT_PROOF']['expression']
        if b['TRANSFORMATION_BINDING']['exact_expression']!=expr or b['ORIGINAL_MISSING_PROOF']!=gap['MISSING_PROOF']:return False
        if field and field.endswith(('.proconfig','.setconfig')) and b['TRANSFORMATION_BINDING'].get('effective_override')!='CONFIG_ASSERTIONS_V2':return False
        return b['BINDING_STATUS']=='BOUND' and b['APPROVED_PRODUCER_STEP_ID']==s['PRODUCER_STEP_ID'] and b['APPROVED_CALLABLE_ID']==call['CALLABLE_ID']==s['TRANSFORMER_ID'] and all(b[k]==s[k] for k in props) and b['INPUT_SCHEMA_BINDING']==call['INPUT_SCHEMA'] and b['OUTPUT_SCHEMA_BINDING']==call['OUTPUT_SCHEMA'] and b['OUTPUT_FIELD_BINDING']==output and output in s['OUTPUT_FIELD_SET'] and set(inputs)<=set(covered) and b['TRANSFORMATION_BINDING']['approved_step_transform']==s['TRANSFORMATION_SET']==call['TRANSFORMATIONS_PERFORMED'] and all(b['SEMANTIC_LINK_CHECKS'].values()) and all(call[k] is False for k in ['MUTATION_CAPABILITY','ROLE_ESCALATION_CAPABILITY','GENERIC_SQL_CAPABILITY','ARBITRARY_OBJECT_CAPABILITY','SECRET_ACCESS_CAPABILITY','IDENTIFIER_PARAMETERS_ALLOWED','SQL_TEXT_PARAMETERS_ALLOWED','OBJECT_NAME_PARAMETERS_ALLOWED']) and len(b['SUPPORTING_ACQUISITION_CHAINS'])==len(inputs) and bool(b['FAIL_CLOSED_BINDING'])
    except (KeyError,TypeError):return False
def evaluate():
    checks=[]
    def ck(n,v,category='INTEGRITY'):checks.append(dict(name=n,passed=bool(v),category=category))
    f=rd(O/'baseline-freeze.json');bs=rd(O/'canonical-binding-ledger.json')['bindings'];steps={s['PRODUCER_STEP_ID']:s for s in rd(D/'G1-producer-execution-plan.json')['steps']};calls={c['CALLABLE_ID']:c for c in rd(D/'G2-callable-effect-universe.json')['callables']};mapping={m['GAP_ID']:m for m in rd(D/'16-gap-design-resolution.json')['mapping']};original={g['GAP_ID']:g for g in rd(A/'semantic-gap-ledger.json')['gaps']}
    ck('branch',git('branch','--show-current')==f['branch']);ck('HEAD',git('rev-parse','HEAD')==f['head']);ck('tracking_ref',git('rev-parse','origin/checkpoint/package-0090-cloud-handoff')==f['remote_tracking_ref_head']);ck('tracked_clean',not git('diff','--name-only'));ck('staged_empty',not git('diff','--cached','--name-only'))
    for p,h in f['source_sha256'].items():ck('frozen:'+p,(R/p).is_file() and sha(R/p)==h)
    before=set(f['untracked_before_paths']);now=set(git('ls-files','--others','--exclude-standard').splitlines());prefix=O.relative_to(R).as_posix()+'/';report='docs/evidence/PACKAGE-0090-B01-v2-native-static-closure-r5n2a4-1b.md'
    ck('old244',len(before)==244 and before<=now);ck('newscope_only',all(p in before or p.startswith(prefix) or p==report for p in now))
    ck('16_unique_original_gaps',len(bs)==len({b['GAP_ID'] for b in bs})==16 and {b['GAP_ID'] for b in bs}==set(original))
    ck('approved_steps_unchanged',[v['approved_step'] for v in rd(O/'producer-step-binding-ledger.json')['steps']]==list(steps.values()))
    ck('approved_callables_unchanged',[v['approved_callable'] for v in rd(O/'callable-binding-ledger.json')['callables']]==list(calls.values()))
    # Reevaluate the exact 17 predecessor criterion identities against actual semantic bindings.
    for b in bs:
        subject=b['OUTPUT_FIELD_BINDING'];ck(('closure_field_effect:' if b['GAP_TYPE']=='FIELD' else 'closure_predicate_effect:')+subject,binding_ok(b,steps,calls,mapping,original),'STATIC_CLOSURE')
        for i,link in enumerate(b['SUPPORTING_ACQUISITION_CHAINS']):
            s=steps[link['SOURCE_STEP']];ck('source_chain:'+b['GAP_ID']+':'+str(i),link['FIELD'] in s['OUTPUT_FIELD_SET'] and link['SOURCE_CALLABLE']==s['TRANSFORMER_ID'] and link['CALLER']==s['CALLER_PRINCIPAL'] and link['SESSION']==s['SESSION_PRINCIPAL'] and link['EFFECTIVE']==s['EFFECTIVE_PRINCIPAL'] and link['AUTHORITY']==s['AUTHORITY_SOURCE'] and link['OUTPUT_FIELD']==link['FIELD'],'SEMANTIC')
    graph=rd(O/'catalog-effect-graph.json');c=rd(O/'graph-completeness.json');norm=rd(O/'edge-normalization.json');oldgraph=rd(P/'effect-graph.json');ids={e['id'] for e in graph['edges']};nodes={n['id'] for n in graph['nodes']};oldbyid={e['id']:e for e in oldgraph['edges']};newbyid={e['id']:e for e in graph['edges']}
    invocation=[e for e in graph['edges'] if e.get('target_node')=='SOURCE_OPERATION/PRODUCER_CALLABLE_SET']
    ck('closure_fixed_producer_callable_manifest',all(binding_ok(b,steps,calls,mapping,original) for b in bs) and len(invocation)==8 and {e['producer_step'] for e in invocation}==set(steps) and c['semantic_completeness'],'STATIC_CLOSURE')
    ck('390_unique_edges',len(ids)==len(graph['edges'])==390);ck('24_types_12plus12',len(graph['canonical_authority_edge_types'])==len(graph['effect_edge_types'])==12);ck('edge_count_delta',norm['old_count']==383 and norm['new_count']==390 and norm['delta']==7)
    for e in graph['edges']:
        ck('endpoints:'+e['id'],e['source_node'] in nodes and e['target_node'] in nodes)
        if e['id'].startswith('BOUND_EDGE/'):
            payload={k:v for k,v in e.items() if k!='id'};ck('edge_hash:'+e['id'],e['id']=='BOUND_EDGE/'+digest(payload))
        else:ck('edge_preserved:'+e['id'],e==oldbyid[e['id']])
        if 'producer_step' in e:
            s=steps[e['producer_step']];ck('edge_invocation:'+e['id'],e['callable']==s['TRANSFORMER_ID'] and e['effective_principal']==s['EFFECTIVE_PRINCIPAL'] and e['authority_source']==s['AUTHORITY_SOURCE'])
            ck('no_raw_ACL_inference:'+e['id'],'relation_authority_edge' not in e and e.get('observed_acl_is_producer_authorization',False) is False)
    for eid in norm['unmodified_edge_ids']:ck('unrelated_byte_values:'+eid,newbyid[eid]==oldbyid[eid])
    ck('complete_lineage',set(oldbyid)==set(norm['unmodified_edge_ids'])|{x['old_id'] for x in norm['changes']})
    for key,count,identity in [('relation_map',19,'source'),('field_map',146,'key'),('predicate_map',26,'id')]:ck('coverage:'+key,len(c[key])==len({v[identity] for v in c[key]})==count)
    for v in c['field_map']:ck('field_edges:'+v['key'],set(v['edges'])<=ids and bool(v['edges']))
    for v in c['predicate_map']:ck('predicate_edges:'+v['id'],set(v['affected_edges'])<=ids and bool(v['affected_edges']))
    ck('no_unresolved_static_fields_predicates_families',not c['unresolved_fields'] and not c['unresolved_predicates'] and c['missing_field_families']==0)
    ck('family_universe_acceptance_not_runtime',bool(c['family_proof']) and c['runtime_coverage_claimed'] is False)
    ret=rd(O/'previous-failure-reconciliation.json');ck('17_results_now_passing',len(ret['checks'])==17 and all(v['POST_BINDING_RESULT']=='PASS' for v in ret['checks']))
    previous={v['TEST_OR_CHECK_ID'] for v in rd(A/'failure-adjudication.json')['failures']};ck('same_17_criteria',previous=={v['TEST_OR_CHECK_ID'] for v in ret['checks']})
    for b in bs:
        mutated=copy.deepcopy(b);mutated['EFFECTIVE_PRINCIPAL']='postgres';ck('reject_broadened_principal:'+b['GAP_ID'],not binding_ok(mutated,steps,calls,mapping,original),'ADVERSARIAL')
        mutated=copy.deepcopy(b);mutated['OUTPUT_FIELD_BINDING']='pg_authid.rolpassword';ck('reject_secret_output:'+b['GAP_ID'],not binding_ok(mutated,steps,calls,mapping,original),'ADVERSARIAL')
        mutated=copy.deepcopy(b);mutated['APPROVED_CALLABLE_ID']='UNBOUND';ck('reject_nominal_callable:'+b['GAP_ID'],not binding_ok(mutated,steps,calls,mapping,original),'ADVERSARIAL')
    order=rd(O/'predicate-order-proof.json');ck('six_ordered_predicates',len(order['predicates'])==6 and all(v['EVALUATION_ORDER'] in [7,8] and v['publication_proof'] for v in order['predicates']))
    ck('no_Reader_ACL',c['reader_acl_may_begin'] is False)
    review=rd(O/'independent-review.json');attack=rd(O/'adversarial-graph-review.json');ck('independent_graph_review_PASS',review.get('INDEPENDENT_GRAPH_REVIEW')=='PASS');ck('zero_review_findings',attack.get('GRAPH_ADVERSARIAL_FINDINGS_OPEN')==0)
    for p,h in review.get('source_sha256',{}).items():ck('review_hash:'+p,sha(R/p)==h)
    for p in O.glob('*.py'):ast.parse(p.read_text());ck('syntax:'+p.name,True)
    manifest=rd(O/'SHA256-MANIFEST.json')
    for p,h in manifest['files'].items():ck('sealed:'+p,sha(R/p)==h)
    actual={p.relative_to(R).as_posix() for p in O.rglob('*') if p.is_file() and p.name!='SHA256-MANIFEST.json'}|{report};ck('manifest_exact',set(manifest['files'])==actual);ck('names_distinct',len(checks)==len({v['name'] for v in checks}))
    return dict(scope='STATIC_APPROVED_DESIGN_GRAPH_BINDING_NOT_RUNTIME_OR_READER_ACL',tests_distinct=len(checks),test_failures=sum(not v['passed'] for v in checks),integrity_failures=sum(not v['passed'] and v['category']=='INTEGRITY' for v in checks),checks=checks)
if __name__=='__main__':
    out=evaluate();print(json.dumps(out if '--detail' in sys.argv else {k:v for k,v in out.items() if k!='checks'}));sys.exit(bool(out['test_failures']))
