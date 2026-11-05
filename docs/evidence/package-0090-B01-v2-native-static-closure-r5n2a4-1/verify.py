"""Read-only offline checks. Exit 1 accurately denotes unmet semantic closure."""
import ast,hashlib,json,subprocess,sys
from pathlib import Path
O=Path(__file__).resolve().parent;R=O.parents[2]
def rd(n):return json.loads((O/n).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def git(*a):return subprocess.check_output(['git',*a],cwd=R).decode().strip()
def evaluate():
    checks=[]
    def ck(n,v,category='INTEGRITY'):checks.append(dict(name=n,passed=bool(v),category=category))
    f=rd('baseline-freeze.json');gaps=rd('semantic-gap-ledger.json')['gaps'];c=rd('global-graph-completeness.json')
    ck('branch',git('branch','--show-current')==f['branch']);ck('HEAD',git('rev-parse','HEAD')==f['head']);ck('remote_tracking_ref_unchanged',git('rev-parse','origin/checkpoint/package-0090-cloud-handoff')==f['remote_tracking_ref_head'])
    ck('tracked_clean',not git('diff','--name-only'));ck('staged_empty',not git('diff','--cached','--name-only'))
    for p,h in f['source_checkout_sha256'].items():ck('frozen:'+p,(R/p).is_file() and sha(R/p)==h)
    before=set(f['untracked_before_paths']);now=set(git('ls-files','--others','--exclude-standard').splitlines());prefix=O.relative_to(R).as_posix()+'/';report='docs/evidence/PACKAGE-0090-B01-v2-native-static-closure-r5n2a4-1.md'
    ck('baseline_untracked212',len(before)==212 and before<=now);ck('authorized_scope_only',all(p in before or p.startswith(prefix) or p==report for p in now))
    a=rd('failure-adjudication.json')['failures'];ck('17_adjudicated',len(a)==17 and len({v['TEST_OR_CHECK_ID'] for v in a})==17)
    ck('classification_exact',sum(v['CLASSIFICATION']=='EXPECTED_GAP_DETECTOR' for v in a)==16 and sum(v['CLASSIFICATION']=='DERIVED_DUPLICATE' for v in a)==1)
    ck('no_regression_infra_unknown',all(v['CLASSIFICATION'] in ['EXPECTED_GAP_DETECTOR','DERIVED_DUPLICATE'] for v in a))
    ck('16_gaps',len(gaps)==len({v['GAP_ID'] for v in gaps})==16)
    for name,value in [('relation_count',19),('field_count',146),('predicate_count',26),('canonical_authority_types',12),('requested_effect_categories',12),('edge_count',383)]:ck(name,c[name]==value,'COVERAGE')
    calls={v['GAP_ID']:v for v in rd('callable-identity-ledger.json')['binding_obligations']};principals={v['GAP_ID']:v for v in rd('principal-binding-ledger.json')['bindings']}
    # Same seventeen semantic criteria; no failure is counted as a pass merely for being informative.
    resolved={}
    for gap in gaps:
        gid=gap['GAP_ID'];b=calls[gid];p=principals[gid]
        resolved[gid]=gap['STATUS']=='CLOSED' and b['STATUS']=='CLOSED' and p['STATUS']=='CLOSED' and all(b[k]!='UNKNOWN' for k in ['CALLABLE_ID','PRODUCER_STEP','AUTHORITY_EXPANSION']) and all(p[k]!='UNKNOWN' for k in ['CALLER_PRINCIPAL','SESSION_PRINCIPAL','EFFECTIVE_PRINCIPAL','AUTHENTICATION_CONTEXT','CREDENTIAL_CLASS'])
        ck(('closure_field_effect:'+gap['FIELD_ID']) if 'FIELD_ID' in gap else ('closure_predicate_effect:'+gap['PREDICATE_ID']),resolved[gid],'STATIC_CLOSURE')
    plan=rd('producer-invocation-plan-binding.json')
    ck('closure_fixed_producer_callable_manifest',all(resolved.values()) and bool(plan['producer_steps']) and c['semantic_completeness'],'STATIC_CLOSURE')
    for cand in plan['candidates']:
        ck('candidate_hash:'+cand['SOURCE_FILE'],sha(R/cand['SOURCE_FILE'])==cand['SHA256']);ck('candidate_not_authority:'+cand['SOURCE_FILE'],cand['READER_BINDING_PROVEN'] is False and bool(cand['REJECTION_REASON']))
    ck('no_edges_upgraded_without_proof',not rd('affected-graph-edges.json')['patches'])
    ck('Reader_ACL_not_started',c['reader_acl_executed'] is False)
    review=rd('adversarial-review.json');ck('independent_review_present',review.get('independent_reviewer_invoked') is True);ck('graph_review_acceptance_not_fabricated',review.get('INDEPENDENT_GRAPH_REVIEW')=='FAIL')
    for p in O.glob('*.py'):ast.parse(p.read_text(encoding='utf-8-sig'));ck('syntax:'+p.name,True)
    manifest=rd('SHA256-MANIFEST.json')
    for p,h in manifest['files'].items():ck('sealed:'+p,sha(R/p)==h)
    actual={p.relative_to(R).as_posix() for p in O.rglob('*') if p.is_file() and p.name!='SHA256-MANIFEST.json'}|{report}
    ck('manifest_exact',set(manifest['files'])==actual)
    ck('distinct_names',len(checks)==len({v['name'] for v in checks}))
    return dict(tests_distinct=len(checks),test_failures=sum(not v['passed'] for v in checks),integrity_failures=sum(not v['passed'] and v['category']!='STATIC_CLOSURE' for v in checks),static_closure_failures=sum(not v['passed'] and v['category']=='STATIC_CLOSURE' for v in checks),checks=checks)
if __name__=='__main__':
    result=evaluate();print(json.dumps(result if '--detail' in sys.argv else {k:v for k,v in result.items() if k!='checks'}));sys.exit(bool(result['test_failures']))
