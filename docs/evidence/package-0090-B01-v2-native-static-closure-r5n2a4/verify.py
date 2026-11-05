"""Offline integrity/coverage plus explicitly failing static closure criteria."""
import sys
sys.dont_write_bytecode=True
import ast,hashlib,json,subprocess,zlib
from pathlib import Path
O=Path(__file__).resolve().parent;R=O.parents[2]
def rd(n):return json.loads((O/n).read_text(encoding='utf-8-sig'))
def sha(b):return hashlib.sha256(b).hexdigest()
def git(*a):return subprocess.check_output(['git',*a],cwd=R).decode().strip()
checks=[]
def ck(n,v,category='INTEGRITY'):checks.append({'name':n,'passed':bool(v),'category':category})
def main():
    f=rd('baseline-freeze.json');ck('branch',git('branch','--show-current')==f['branch']);ck('HEAD',git('rev-parse','HEAD')==f['baseline_head']);ck('tracked_clean',not git('diff','--name-only'));ck('staged_empty',not git('diff','--cached','--name-only'))
    for p,h in f['source_checkout_sha256'].items():ck('frozen:'+p,(R/p).is_file() and sha((R/p).read_bytes())==h)
    paths=list(f['source_Git_LF_sha256']);b=subprocess.run(['git','cat-file','--batch'],cwd=R,input=''.join('HEAD:'+p+'\n' for p in paths).encode(),stdout=subprocess.PIPE,check=True).stdout;off=0
    for p in paths:
        end=b.index(b'\n',off);size=int(b[off:end].split()[-1]);off=end+1;ck('GitLF:'+p,sha(b[off:off+size])==f['source_Git_LF_sha256'][p]);off+=size+1
    vp=next(p for p in paths if p.startswith('applications/') and '/V043__' in p);vb=subprocess.check_output(['git','show','HEAD:'+vp],cwd=R);crc=zlib.crc32(b''.join(vb.splitlines()));crc=crc if crc<2**31 else crc-2**32
    ck('V043_SHA',sha(vb)==f['CURRENT_V043_GIT_LF_SHA256']);ck('V043_CRC',crc==f['FLYWAY_SIGNED_CRC32']);fence=b"RAISE EXCEPTION USING ERRCODE = '55000'";ck('V043_fence',fence in vb and vb.index(fence)<vb.index(b'SET LOCAL search_path'))
    old=set(f['untracked_before_paths']);now=set(git('ls-files','--others','--exclude-standard').splitlines());prefix=O.relative_to(R).as_posix()+'/'
    report='docs/evidence/PACKAGE-0090-B01-v2-native-static-closure-r5n2a4.md';ck('old197',len(old)==197 and old<=now);ck('newscope_only',all(p in old or p.startswith(prefix) or p==report for p in now))
    g=rd('effect-graph.json');c=rd('graph-completeness.json');nodes={n['id'] for n in g['nodes']};ids={e['id'] for e in g['edges']}
    ck('unique_nodes',len(nodes)==len(g['nodes']));ck('unique_edges',len(ids)==len(g['edges']))
    ck('19_relation_mappings',len(c['relation_map'])==len({r['source'] for r in c['relation_map']})==19,'COVERAGE')
    ck('146_field_mappings',len(c['field_map'])==len({r['key'] for r in c['field_map']})==146,'COVERAGE')
    ck('26_predicate_mappings',len(c['predicate_map'])==len({r['id'] for r in c['predicate_map']})==26,'COVERAGE')
    ck('8_actual_credential_references',len(c['credential_map'])==len({r['reference'] for r in c['credential_map']})==8,'COVERAGE')
    ck('12_canonical_authority_names',len(g['canonical_authority_edge_types'])==12)
    ck('12_requested_effect_names',len(g['effect_edge_types'])==12)
    required={'source_node','target_node','edge_type','initiating_principal','effective_principal','authority_source','credential_class','catalog_source_provenance','security_predicate','visibility_condition','redaction_null_behavior','mutation_possibility','role_escalation_possibility','secret_material_possibility','arbitrary_object_possibility','generation_custody_binding','static_evidence_reference','unresolved_status'}
    for e in g['edges']:
        ck('edge_fields:'+e['id'],required<=set(e),'COVERAGE');ck('endpoints:'+e['id'],e['source_node'] in nodes and e['target_node'] in nodes)
        frozen={k:v for k,v in e.items() if k!='id'};frozen['security_predicate']=[]
        ck('edge_identity:'+e['id'],'EDGE/'+sha(json.dumps(frozen,sort_keys=True,separators=(',',':')).encode())==e['id'])
    for r in c['field_map']:ck('field_edges:'+r['key'],r['edges'] and set(r['edges'])<=ids,'COVERAGE')
    for r in c['predicate_map']:ck('predicate_edges:'+r['id'],r['affected_edges'] and set(r['affected_edges'])<=ids,'COVERAGE')
    for r in c['credential_map']:ck('credential_edge:'+r['reference'],r['edge'] in ids,'COVERAGE')
    # These checks deliberately record the unmet user closure criteria, rather than hiding them as green inventory tests.
    for field in c['unresolved_fields']:ck('closure_field_effect:'+field,False,'STATIC_CLOSURE')
    for pid in c['unresolved_predicates']:ck('closure_predicate_effect:'+pid,False,'STATIC_CLOSURE')
    ck('closure_fixed_producer_callable_manifest',c['semantic_completeness'],'STATIC_CLOSURE')
    ck('Reader_ACL_not_started',rd('reader-effective-acl.json')['section4_executed'] is False)
    ck('adversarial_not_fabricated',rd('adversarial-review.json')['independent_reviewer_invoked'] is False)
    ck('preserved_contracts',rd('preserved-facts.json')['closed_contracts_reopened']==rd('preserved-facts.json')['contradictions_discovered']==0)
    for p in O.glob('*.py'):ast.parse(p.read_text(encoding='utf-8-sig'));ck('syntax:'+p.name,True)
    if (O/'EFFECT-GRAPH-GATE.json').exists():
        gate=rd('EFFECT-GRAPH-GATE.json');ck('gate_failclosed',gate['TARGET_BLOCKERS_CLOSED']==0 and gate['N1_CATALOG_EFFECT_GRAPH']=='OPEN' and gate['N1_READER_EFFECTIVE_ACL']=='OPEN')
        ck('no_execution',all(gate[k]=='NO' for k in ['IMPLEMENTATION_PERFORMED','NATIVE_BUILD_PERFORMED','NATIVE_RUNTIME_EXECUTED','SQL_EXECUTED','DATABASE_CONTACTED','V043_EXECUTED','B02_EXECUTED']))
    if (O/'SHA256-MANIFEST.json').exists():
        manifest=rd('SHA256-MANIFEST.json')
        for p,h in manifest['files'].items():ck('sealed:'+p,sha((R/p).read_bytes())==h)
        expected={p.relative_to(R).as_posix() for p in O.rglob('*') if p.is_file() and p.name!='SHA256-MANIFEST.json'}|{report};ck('manifest_exact',expected==set(manifest['files']))
    ck('test_names_distinct',len({c['name'] for c in checks})==len(checks))
    out={'scope':'INTEGRITY_COVERAGE_AND_EXPLICIT_STATIC_CLOSURE_FAILURES','tests_distinct':len(checks),'test_failures':sum(not c['passed'] for c in checks),'integrity_failures':sum(not c['passed'] and c['category']!='STATIC_CLOSURE' for c in checks),'static_closure_failures':sum(not c['passed'] and c['category']=='STATIC_CLOSURE' for c in checks),'checks':checks}
    print(json.dumps(out if '--detail' in sys.argv else {k:v for k,v in out.items() if k!='checks'}));return out
if __name__=='__main__':sys.exit(bool(main()['test_failures']))
