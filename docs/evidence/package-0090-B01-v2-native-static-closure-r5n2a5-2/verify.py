"""Offline provenance/topology checks; retain the real original negative-witness gap."""
import ast,collections,hashlib,itertools,json,sys
from derive import O,R,N,N1,N2,A5,P,rd,sha,git,select
def evaluate():
    checks=[]
    def ck(n,v,category='INTEGRITY'):checks.append(dict(name=n,passed=bool(v),category=category))
    frozen=rd(O/'baseline-freeze.json');prov=rd(O/'pairwise-requirement-provenance.json');topo=rd(O/'replacement-topology.json');graph=rd(O/'replacement-dependency-graph.json');decomp=rd(O/'independence-dimension-decomposition.json');supervisor=rd(O/'supervisor-replacement-proof.json');old=rd(O/'28-expectation-adjudication.json');negative=rd(O/'original-negative-witness-audit.json');model=rd(O/'canonical-witness-model.json');native=rd(N/'native-participants.json')['participants'];ids=[p['PARTICIPANT_ID'] for p in native];pairs=list(itertools.combinations(ids,2))
    ck('branch',git('branch','--show-current')==frozen['branch']);ck('HEAD',git('rev-parse','HEAD')==frozen['head']);ck('tracking_ref',git('rev-parse','origin/checkpoint/package-0090-cloud-handoff')==frozen['remote_tracking_ref_head']);ck('tracked_clean',not git('diff','--name-only'));ck('staged_empty',not git('diff','--cached','--name-only'))
    for path,h in frozen['source_sha256'].items():ck('preserved:'+path,(R/path).is_file() and sha(R/path)==h)
    before=set(frozen['untracked_before_paths']);now=set(git('ls-files','--others','--exclude-standard').splitlines());prefix=O.relative_to(R).as_posix()+'/';report='docs/evidence/PACKAGE-0090-B01-v2-native-static-closure-r5n2a5-2.md'
    ck('324_prior_paths',len(before)==324 and before<=now);ck('authorized_scope_only',all(p in before or p.startswith(prefix) or p==report for p in now))
    accepted={'A_CANONICAL_EXPLICIT_REQUIREMENT','B_CANONICAL_REQUIREMENT_DERIVED_NECESSARILY','C_R5N_WITNESS_ASSUMPTION','D_TEST_HARNESS_ASSUMPTION','E_REVIEW_HEURISTIC','F_AMBIGUOUS','G_CONTRADICTED_BY_FROZEN_CONTRACT'}
    for i,s in enumerate(prov['records']):
        path=__import__('pathlib').Path(s['SOURCE_PATH']);path=path if path.is_absolute() else R/path
        ck('provenance_source:'+str(i),sha(path)==s['SOURCE_HASH']);ck('provenance_class:'+str(i),s['EXACT_REQUIREMENT_CLASS'] in accepted and bool(s['WHAT_PROPERTY_IT_ACTUALLY_REQUIRES']) and bool(s['SOURCE_SECTION']))
    ck('19_provenance_sources',len({s['SOURCE_PATH'] for s in prov['records']})==prov['source_count']==19)
    ck('canonical_context_not_strict',prov['canonical_strict_supporting_source_count']==0 and not any(s['SUPPORTS_STRICT_FULL_OTHER_TUPLE_PRESERVATION'] for s in prov['records']))
    ck('outcomeB_notS3',prov['SELECTED_OUTCOME']=='B' and prov['STRICT_21_PAIR_REQUIREMENT_CANONICAL']=='NO' and topo['no_S3'] is True and topo['no_S1_or_S2_attempt'] is True)
    prior=rd(O/'a5-1-frozen-contradiction.json');ck('S1_S2_and_parent_facts_preserved',prior['S1_VALID']==prior['S2_VALID']=='NO' and prior['PARENT_IDENTITY_IS_CHILD_INTRINSIC_IDENTITY_COMPONENT']=='YES' and prior['PARENT_IDENTITY_IS_LIVE_LOOKUP']=='NO')
    ck('7_dimension_decompositions',len(decomp['participants'])==7 and {p['PARTICIPANT'] for p in decomp['participants']}==set(ids))
    ck('12_dependency_edges',len(graph['edges'])==12 and set(graph['nodes'])==set(ids) and all(graph['premises'].values()))
    for t in topo['closures']:
        subject=t['REPLACE'];closure={subject}
        while True:
            new=closure|{e['target'] for e in graph['edges'] if e['source'] in closure}
            if new==closure:break
            closure=new
        ck('least_fixed_point:'+subject,closure==set(t['MANDATORY_DRAIN_SET'])==set(t['MANDATORY_NEW_GENERATION_SET'])==set(t['MANDATORY_REQUALIFICATION_SET'])==set(ids))
        ck('direct_and_restart_units:'+subject,t['DIRECTLY_REPLACED_PARTICIPANTS']==[subject] and set(t['DEPENDENT_RESTART_PARTICIPANTS'])==set(ids)-{subject} and t['UNAFFECTED_PARTICIPANTS']==[])
        ck('key_endpoint_scope:'+subject,set(t['MANDATORY_NEW_KEY_SET'])==set(ids)-{'POSTMASTER'} and t['MANDATORY_NEW_ENDPOINT_IDENTITY_SET']==['POSTMASTER'])
        ck('no_authority_widening:'+subject,t['AUTHORITY_IDENTITIES_CHANGED']['stable_role_capability_sets_changed']==[] and t['PRINCIPALS_CHANGED']['logical_slot_principals_changed']==[] and t['CUSTODY_IDENTITIES_CHANGED']['custody_classes_changed']==[] and t['REVOCATION_IDENTITIES_CHANGED']['slot_independence_relationships_changed']==[])
        for i,s in enumerate(t['EVIDENCE']):
            fact=select(rd(R/s['path']),s['pointer']);digest=hashlib.sha256(json.dumps(fact,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest();ck('topology_source:'+subject+':'+str(i),sha(R/s['path'])==s['sha256'] and digest==s['canonical_fact_sha256'])
    ck('supervisor_exact_counts',supervisor['SUPERVISOR_DIRECTLY_SUBSTITUTED_COUNT']==1 and supervisor['CHILDREN_REQUIRING_DRAIN_COUNT']==supervisor['CHILDREN_REQUIRING_NEW_GENERATION_COUNT']==supervisor['CHILDREN_REQUIRING_REQUALIFICATION_COUNT']==6 and supervisor['CHILDREN_REQUIRING_NEW_KEY_COUNT']==5 and supervisor['CHILDREN_REQUIRING_NEW_ENDPOINT_MANIFEST_COUNT']==1)
    matrix_files=sorted(O.glob('*-independence-matrix.json'));ck('nine_separate_dimensions',len(matrix_files)==9)
    for path in matrix_files:
        m=rd(path);ck('matrix_domain:'+m['dimension'],set(m['matrix'])==set(ids) and len(m['relations'])==m['required']==21 and bool(m['definition']))
        expected='PROVEN_DEPENDENT' if m['dimension'] in ['RESTART_INDEPENDENCE','STRICT_SUBSTITUTION_INDEPENDENCE'] else 'PROVEN_INDEPENDENT'
        for a,b in pairs:ck('matrix_relation:'+m['dimension']+':'+a+':'+b,m['matrix'][a][b]==m['matrix'][b][a]==expected)
        ck('matrix_diagonal:'+m['dimension'],all(m['matrix'][p][p]=='NOT_APPLICABLE' for p in ids))
        if m['dimension']=='GENERATION_INDEPENDENCE':ck('generation_namespace_vs_transition',all(r['generation_transition_independence']=='PROVEN_DEPENDENT' for r in m['relations']) and 'not independent advancement' in m['definition'])
    replacement=rd(O/'valid-replacement-witnesses.json');ck('7_valid_not_strict_restarts',len(replacement['witnesses'])==replacement['passing']==7 and all(all(w['CHECKS'].values()) and w['not_an_old_strict_test_PASS'] is True and w['runtime_executed'] is False for w in replacement['witnesses']))
    oldids={x['name'] for x in rd(A5/'test-results.json')['checks'] if not x['passed']};ck('28_exact_old_expectations',len(old['records'])==28 and {r['TEST_ID'] for r in old['records']}==oldids)
    ck('invalid_not_PASS',old['PREVIOUS_FAILURES_INVALID_EXPECTATION_ADJUDICATED']==28 and old['PREVIOUS_FAILURES_NOW_PASSING']==0 and old['PREVIOUS_FAILURES_UNCLASSIFIED']==old['PREVIOUS_FAILURES_STILL_VALID']==0 and all(r['CLASSIFICATION']=='OVERSTRONG_WITNESS_TEST' and r['CANONICAL_ADJUDICATION']=='INVALID_OVERSTRONG_WITNESS_EXPECTATION' and r['FINAL_RESULT']=='INVALID_EXPECTATION_ADJUDICATED' and r['not_PASS'] is True for r in old['records']))
    sources=rd(N2/'substitution-witnesses.json');ck('real350_universe_preserved',len(negative['records'])==350 and {r['ATTACK_ID'] for r in negative['records']}=={r['ATTACK_ID'] for r in sources['cases']})
    ck('historical168182_vs_current133217',negative['N1_preserved_cases']==168 and negative['N1_new_cases']==182 and negative['N2_structured_complete_flags']==133 and negative['N2_unresolved_flags']==217 and negative['unresolved_previously_preserved']==35 and negative['unresolved_previously_new']==182)
    for r in negative['records']:
        case=next(c for c in sources['cases'] if c['ATTACK_ID']==r['ATTACK_ID']);ck('negative_case_lineage:'+r['ATTACK_ID'],r['structured_witness_present']==case['STATIC_WITNESS_COMPLETE'] and r['still_required'] is True)
        # Data-completeness criteria, not a claimed attack execution or a PASS relabel.
        ck('closure_canonical_negative_witness_materialized:'+r['ATTACK_ID'],r['structured_witness_present'],'STATIC_CLOSURE')
    ck('no_attack_execution_claim',negative['current_attack_evaluations_performed']==0 and model['closure_allowed'] is False and model['valid_case_gap']['negative_witnesses_generic_or_incomplete']==217)
    decision=rd(O/'scope-and-closure-decision.json');ck('no_false_N1_or_native_promotion',decision['N1_SUBSTITUTION_STATIC_WITNESSES']=='OPEN' and decision['V2_NATIVE_STATUS']=='BLOCKED' and decision['root_cause_recomputation_executed'] is False and decision['architecture_mutated'] is False)
    provreview=rd(O/'independent-provenance-review.json');toporeview=rd(O/'independent-topology-review.json');finalreview=rd(O/'independent-final-review.json');adversary=rd(O/'adversarial-review.json')
    ck('independent_provenance_PASS',provreview['INDEPENDENT_PROVENANCE_REVIEW']=='PASS');ck('independent_topology_PASS',toporeview['INDEPENDENT_TOPOLOGY_REVIEW']=='PASS');ck('independent_final_FAIL_honest',finalreview['INDEPENDENT_FINAL_REVIEW']=='FAIL' and finalreview.get('review_completed') is True);ck('one_existing_negative_witness_finding',adversary['ADVERSARIAL_FINDINGS_OPEN']==1)
    for path,h in finalreview.get('source_sha256',{}).items():ck('review_hash:'+path,sha(R/path)==h)
    for path in O.glob('*.py'):ast.parse(path.read_text(encoding='utf-8-sig'));ck('syntax:'+path.name,True)
    manifest=rd(O/'SHA256-MANIFEST.json')
    for path,h in manifest['files'].items():ck('sealed:'+path,sha(R/path)==h)
    expected={p.relative_to(R).as_posix() for p in O.rglob('*') if p.is_file() and p.name!='SHA256-MANIFEST.json'}|{report};ck('manifest_exact',expected==set(manifest['files']));ck('distinct_names',len(checks)==len({c['name'] for c in checks}))
    return dict(scope='PROVENANCE_TOPOLOGY_STATIC_CHECKS_AND_REAL_NEGATIVE_WITNESS_COMPLETENESS',tests_distinct=len(checks),test_failures=sum(not c['passed'] for c in checks),integrity_failures=sum(not c['passed'] and c['category']=='INTEGRITY' for c in checks),static_closure_failures=sum(not c['passed'] and c['category']=='STATIC_CLOSURE' for c in checks),original_28_tests_not_rerun=True,canonical_attack_evaluations_performed=0,checks=checks)
if __name__=='__main__':
    out=evaluate();print(json.dumps(out if '--detail' in sys.argv else {k:v for k,v in out.items() if k!='checks'}));sys.exit(bool(out['test_failures']))
