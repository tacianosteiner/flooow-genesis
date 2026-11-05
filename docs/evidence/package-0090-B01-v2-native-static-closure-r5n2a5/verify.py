"""Offline integrity plus honestly failing unresolved static witness criteria."""
import ast,hashlib,itertools,json,sys
from qualification import O,R,N,N1,N2,rd,sha,git,pointer
from close_qualification import checks as phase_a_checks
def evaluate():
    checks=[]
    def ck(n,v,category='INTEGRITY'):checks.append(dict(name=n,passed=bool(v),category=category))
    frozen=rd(O/'baseline-freeze.json');qual=rd(O/'qualification-closure.json');bentry=rd(O/'phase-b-entry.json');witness=rd(O/'substitution-witness-ledger.json');participants=rd(O/'seven-participant-qualification.json')['participants'];ids=[p['PARTICIPANT_ID'] for p in participants];pairs=list(itertools.combinations(ids,2));tests=rd(O/'participant-substitution-tests.json');revocation=rd(O/'revocation-independence-proof.json');authority=rd(O/'authority-overlap-matrix.json');custody=rd(O/'credential-custody-matrix.json');decisions=rd(O/'original-12-decision-reconciliation.json');roots=rd(O/'original-root-cause-reconciliation.json');v2=rd(O/'v2-native-recomputation.json');registry=rd(N/'native-registry-generation.json')
    ck('branch',git('branch','--show-current')==frozen['branch']);ck('HEAD',git('rev-parse','HEAD')==frozen['head']);ck('tracking_ref',git('rev-parse','origin/checkpoint/package-0090-cloud-handoff')==frozen['remote_tracking_ref_head']);ck('tracked_clean',not git('diff','--name-only'));ck('staged_empty',not git('diff','--cached','--name-only'))
    for p,h in frozen['source_sha256'].items():ck('preserved:'+p,(R/p).is_file() and sha(R/p)==h)
    before=set(frozen['untracked_before_paths']);now=set(git('ls-files','--others','--exclude-standard').splitlines());prefix=O.relative_to(R).as_posix()+'/';report='docs/evidence/PACKAGE-0090-B01-v2-native-static-closure-r5n2a5.md'
    ck('old280_preserved',len(before)==280 and before<=now);ck('newscope_only',all(p in before or p.startswith(prefix) or p==report for p in now))
    for c in phase_a_checks()['checks']:ck('phaseA/'+c['name'],c['passed'])
    ck('A_closed_before_B',qual['N1_QUALIFICATION_INPUT_RESOLUTION']=='CLOSED' and bentry['required_phase_a']=='CLOSED' and bentry['qualification_closure_sha256']==sha(O/'qualification-closure.json') and bentry['qualification_review_sha256']==sha(O/'qualification-adversarial-review.json'))
    ck('seven_identity_denominator',len(ids)==len(set(ids))==7 and not any('READ_PROXY' in p for p in ids));ck('21_pair_denominator',len(witness['witnesses'])==21 and {(w['PARTICIPANT_A'],w['PARTICIPANT_B']) for w in witness['witnesses']}==set(pairs))
    required={'WITNESS_ID','PARTICIPANT_A','PARTICIPANT_B','IDENTITY_DISTINCT','PRINCIPAL_DISTINCT','OWNER_DISTINCT_OR_NON_COLLAPSING','SESSION_CONTEXT_DISTINCT','PROCESS_CONTEXT_DISTINCT','ENDPOINT_OR_BINDING_DISTINCT','GENERATION_SCOPE_DISTINCT','CUSTODY_SCOPE_DISTINCT','REVOCATION_SCOPE_DISTINCT','CREDENTIAL_CLASS_RELATION','ROLE_MEMBERSHIP_RELATION','AUTHORITY_OVERLAP','CALLABLE_SURFACE_OVERLAP','SHARED_STATE','SHARED_SECRET','SHARED_AUTHORITY','SHARED_MUTATION_PATH','SHARED_ESCALATION_PATH','SUBSTITUTE_A_WITH_B_EFFECT','SUBSTITUTE_B_WITH_A_EFFECT','INDEPENDENCE_STATUS'}
    for w in witness['witnesses']:
        wid=w['WITNESS_ID'];ck('witness_fields:'+wid,required<=w.keys(),'COVERAGE');ck('noncollapse_not_substitution:'+wid,all(w['checks'].values()) and w['INDEPENDENCE_STATUS']=='UNKNOWN' and bool(w['MISSING_PROOF']))
        ck('closure_pair_independence:'+wid,w['INDEPENDENCE_STATUS']=='PROVEN_INDEPENDENT','STATIC_CLOSURE')
        for i,s in enumerate(w['SOURCE_PROVENANCE']):
            value=pointer(rd(R/s['path']),s['pointer']);digest=hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest();ck('witness_source:'+wid+':'+str(i),sha(R/s['path'])==s['sha256'] and digest==s['canonical_fact_sha256'])
    ck('seven_static_tests',len(tests['tests'])==7 and {t['PARTICIPANT_ID'] for t in tests['tests']}==set(ids))
    for t in tests['tests']:ck('closure_single_substitution:'+t['PARTICIPANT_ID'],t['STATUS']=='PASS','STATIC_CLOSURE')
    counter=next(t for t in tests['tests'] if t['PARTICIPANT_ID']=='SUPERVISOR');codec=rd(N/'native-identity-codec.json')
    ck('supervisor_counterexample_exact',counter['STATUS']=='FAIL' and len(counter['CHILD_PARENT_REQUIREMENT_SOURCES'])==6 and 'parent_identity' in {f['name'] for f in codec['schemas']['process_instance_identity']} and 'process_identity' in {f['name'] for f in codec['schemas']['enrollment_identity']})
    ck('unknown_not_not_independent',sum(w['INDEPENDENCE_STATUS']=='NOT_INDEPENDENT' for w in witness['witnesses'])==0 and sum(t['STATUS']=='UNKNOWN' for t in tests['tests'])==6)
    for name,matrix,allowed in [('authority',authority['matrix'],{'SELF','BOUNDED_OVERLAP'}),('credential',custody['matrix'],{'SELF','SHARED_NON_SECRET_CONTEXT'})]:
        ck('matrix_rows:'+name,set(matrix)==set(ids))
        for a in ids:
            ck('matrix_cols:'+name+':'+a,set(matrix[a])==set(ids))
            for b in ids:ck('matrix_cell:'+name+':'+a+':'+b,matrix[a][b] in allowed and matrix[a][b]==matrix[b][a] and (matrix[a][b]=='SELF')==(a==b))
    ck('no_authority_collapse',authority['AUTHORITY_COLLAPSE_COUNT']==authority['AUTHORITY_OVERLAP_UNKNOWN_COUNT']==0);ck('no_shared_secret_or_unjustified_custody',custody['SHARED_SECRET_MATERIAL_PAIR_COUNT']==custody['UNJUSTIFIED_SHARED_CUSTODY_PAIR_COUNT']==custody['CREDENTIAL_CUSTODY_UNKNOWN_PAIR_COUNT']==0)
    ck('21_revocation_units',len(revocation['pairs'])==revocation['proven']==21 and revocation['unresolved']==0)
    for i,r in enumerate(revocation['pairs']):
        for j,d in enumerate(r['directions']):ck('revocation_key:'+str(i)+':'+str(j),d['revocation_entity_key']==registry['records'][2]['primary_identity'] and d['subject_slot']!=d['other_slot'] and d['independent_revocation_unit'] is True and d['dependent_requalification_may_be_required'] is True)
    originalids={r['BLOCKER_ID'] for r in rd(N2/'twelve-blocker-register.json')['records']};ck('exact12decisionlineage',len(decisions['records'])==12 and {r['BLOCKER_ID'] for r in decisions['records']}==originalids and decisions['closed']==11 and decisions['open']==1)
    ck('original3rootlineage',len(roots['roots'])==3 and roots['closed']==1 and roots['open']==2 and roots['final_recomputation_executed'] is False)
    ck('final_recomputation_fenced',v2['executed'] is False and v2['V2_NATIVE_STATIC_DESIGN_PROOF']=='FAIL' and v2['V2_NATIVE_STATUS']=='BLOCKED' and v2['NATIVE_PARTICIPANTS_FULLY_QUALIFIED']=='NOT_RECOMPUTED_DEPENDENCY_OPEN')
    qa=rd(O/'qualification-adversarial-review.json');sa=rd(O/'substitution-adversarial-review.json');review=rd(O/'independent-final-review.json')
    ck('independent_qualification_stays_PASS',qa['INDEPENDENT_QUALIFICATION_REVIEW']=='PASS' and qa['QUALIFICATION_ADVERSARIAL_FINDINGS_OPEN']==0)
    ck('substitution_open_finding_not_hidden',sa['SUBSTITUTION_ADVERSARIAL_FINDINGS_OPEN']==1)
    ck('independent_acceptance_FAIL_honest',review['INDEPENDENT_FINAL_REVIEW']=='FAIL' and review.get('review_completed') is True)
    for p,h in review.get('source_sha256',{}).items():ck('final_review_hash:'+p,sha(R/p)==h)
    for p in O.glob('*.py'):ast.parse(p.read_text());ck('syntax:'+p.name,True)
    manifest=rd(O/'SHA256-MANIFEST.json')
    for p,h in manifest['files'].items():ck('sealed:'+p,sha(R/p)==h)
    actual={p.relative_to(R).as_posix() for p in O.rglob('*') if p.is_file() and p.name!='SHA256-MANIFEST.json'}|{report};ck('manifest_exact',actual==set(manifest['files']));ck('distinct_names',len(checks)==len({c['name'] for c in checks}))
    return dict(scope='STATIC_INTEGRITY_AND_UNMET_WITNESS_CLOSURE_CRITERIA',tests_distinct=len(checks),test_failures=sum(not c['passed'] for c in checks),integrity_failures=sum(not c['passed'] and c['category']=='INTEGRITY' for c in checks),static_closure_failures=sum(not c['passed'] and c['category']=='STATIC_CLOSURE' for c in checks),checks=checks)
if __name__=='__main__':
    out=evaluate();print(json.dumps(out if '--detail' in sys.argv else {k:v for k,v in out.items() if k!='checks'}));sys.exit(bool(out['test_failures']))
