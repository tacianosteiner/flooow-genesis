"""Verify semantic stop evidence, preserving one unmet closure criterion as FAIL."""
import ast,hashlib,json,re,sys
from adjudicate import O,R,P,N,N1,rd,sha,git,select
def evaluate():
    checks=[]
    def ck(n,v,category='INTEGRITY'):checks.append(dict(name=n,passed=bool(v),category=category))
    frozen=rd(O/'baseline-freeze.json');adj=rd(O/'parent-identity-semantic-adjudication.json');decision=rd(O/'substitution-semantics-decision.json');inventory=rd(O/'parent-identity-use-inventory.json');decomp=rd(O/'identity-decomposition.json');failures=rd(O/'28-failure-reconciliation.json');frontier=rd(O/'stop-frontier.json');codec=rd(N/'native-identity-codec.json');participants=rd(N/'native-participants.json')['participants'];execution=rd(N1/'execution-isolation.json')['profiles'];custody=rd(N1/'credential-custody.json')['credentials']
    ck('branch',git('branch','--show-current')==frozen['branch']);ck('HEAD',git('rev-parse','HEAD')==frozen['head']);ck('tracking_ref',git('rev-parse','origin/checkpoint/package-0090-cloud-handoff')==frozen['remote_tracking_ref_head']);ck('tracked_clean',not git('diff','--name-only'));ck('staged_empty',not git('diff','--cached','--name-only'))
    for p,h in frozen['source_sha256'].items():ck('preserved:'+p,(R/p).is_file() and sha(R/p)==h)
    before=set(frozen['untracked_before_paths']);now=set(git('ls-files','--others','--exclude-standard').splitlines());prefix=O.relative_to(R).as_posix()+'/';report='docs/evidence/PACKAGE-0090-B01-v2-native-static-closure-r5n2a5-1.md'
    ck('308_baseline_paths_preserved',len(before)==308 and before<=now);ck('newscope_only',all(p in before or p.startswith(prefix) or p==report for p in now))
    for i,e in enumerate(adj['STATIC_EVIDENCE']):ck('semantic_source:'+str(i),sha(R/e['path'])==e['sha256'] and select(rd(R/e['path']),e['pointer'])==e['fact'])
    ck('parent_in_frozen_process_codec','parent_identity' in {f['name'] for f in codec['schemas']['process_instance_identity']})
    ck('parent_and_process_in_enrollment',{'parent_identity','process_identity'}<={f['name'] for f in codec['schemas']['enrollment_identity']})
    ck('retained_parent_birth_not_name',{'retained_pidfd_dev','retained_pidfd_inode','kernel_start_ticks'}<={f['name'] for f in codec['schemas']['parent_identity']})
    for i,p in enumerate(participants):
        pid=p['PARTICIPANT_ID'];parent='HOST_PLATFORM' if pid=='SUPERVISOR' else 'SUPERVISOR';ck('parent_class:'+pid,execution[i]['EXPECTED_PARENT_CLASS']==parent)
        ck('parent_measurement_pre_enrollment:'+pid,'before child enrollment' in p['identity_tuple']['measured_fields']['parent_identity']['MEASUREMENT_ALGORITHM'])
        if pid!='SUPERVISOR':ck('frozen_drain_requirement:'+pid,'replacement during sealed generation forbidden' in p['PARENT_REQUIREMENT'] and 'full generation drain' in p['PARENT_REQUIREMENT'])
        ck('restart_scope:'+pid,'fresh bootstrap/new generation' in execution[i]['RESTART_POLICY'])
        ck('no_old_key_adoption:'+pid,'New generation/key' in custody[i]['RESTART_BEHAVIOR'] and 'No key/channel adoption' in custody[i]['RECONNECT_BEHAVIOR'])
    ck('no_grant_or_key_derivation_inference',adj['DOES_PARENT_IDENTITY_DEFINE_CHILD_AUTHORITY']=='NO' and adj['DOES_PARENT_IDENTITY_DEFINE_CHILD_CREDENTIAL_CUSTODY']=='NO')
    ck('intrinsic_answer_scope_explicit',adj['DOES_PARENT_IDENTITY_DEFINE_CHILD_INTRINSIC_IDENTITY']=='YES' and bool(adj['INTRINSIC_ANSWER_SCOPE']))
    ck('no_critical_semantic_UNKNOWN',adj['AUTHORITY_CRITICAL_UNKNOWNS']==[])
    ck('seven_existing_field_decompositions',len(decomp['participants'])==7 and all(p['not_a_new_identity_schema'] for p in decomp['participants']))
    for p in decomp['participants']:
        ck('decomposition_qualified_codec_unchanged:'+p['PARTICIPANT_ID'],p['INTRINSIC_IDENTITY_FIELDS']['qualified_process_identity_components']==codec['schemas']['process_instance_identity'])
    # Re-scan every frozen file so inventory omissions cannot be hidden by a supplied file list.
    pattern=re.compile(rb'parent_identity',re.I);actual={}
    for path in frozen['source_sha256']:
        data=(R/path).read_bytes();matches=list(pattern.finditer(data))
        if matches:actual[path]=[(m.start(),data.count(b'\n',0,m.start())+1,m.group().decode('ascii')) for m in matches]
    indexed={f['path']:f for f in inventory['files']};ck('inventory_all_matching_files',set(actual)==set(indexed) and inventory['files_scanned']==len(frozen['source_sha256']))
    for path,locations in actual.items():ck('inventory_locations:'+path,locations==[(u['byte_offset'],u['line'],u['token']) for u in indexed[path]['uses']] and indexed[path]['sha256']==sha(R/path))
    ck('inventory_total',sum(len(v) for v in actual.values())==inventory['occurrences'])
    ck('S1_counterexample_retained',decision['S1_STRICT_FULL_TUPLE_PRESERVATION_VALID']=='NO')
    ck('S2_not_silently_approved',decision['S2_DEPENDENCY_AWARE_SUBSTITUTION_VALID']=='NO' and decision['SELECTED_SUBSTITUTION_SEMANTICS']=='NONE' and decision['stop_section']==4)
    ck('no_rebind_allowlist_invented',decision['DEPENDENT_REBIND_FIELDS_TOTAL']==decision['DEPENDENT_REBIND_FIELDS_ENUMERATED']==0 and bool(decision['allowlist_meaning']))
    ck('closure_substitution_semantics_selected',decision['SELECTED_SUBSTITUTION_SEMANTICS'] in ['S1','S2'],'STATIC_CLOSURE')
    ck('section4_downstream_fence',frontier['stop_section']==4 and not any(frontier[k] for k in ['substitution_semantics_approved','dependent_rebinding_contract_created','six_child_rebinding_executed','seven_individual_substitutions_recomputed','twenty_one_pairwise_witnesses_recomputed','authority_matrix_recomputed','credential_custody_revocation_matrices_recomputed','final_v2_native_recomputation_executed']))
    prior={c['name'] for c in rd(P/'test-results.json')['checks'] if not c['passed']};ck('28_exact_old_failure_ids',len(failures['failures'])==28 and {f['TEST_OR_CHECK_ID'] for f in failures['failures']}==prior)
    ck('no_prior_failure_relabeled_PASS',failures['PREVIOUS_FAILURES_ADJUDICATED']==28 and failures['PREVIOUS_FAILURES_UNCLASSIFIED']==0 and failures['PREVIOUS_FAILURES_NOW_PASSING']==0 and failures['PREVIOUS_FAILURES_NOT_RETESTED']==28 and all(f['now_passing'] is False and f['POST_ADJUDICATION_RESULT']=='NOT_RECOMPUTED_STOP_SECTION_4' for f in failures['failures']))
    review=rd(O/'independent-review.json');adversary=rd(O/'adversarial-review.json');ck('independent_review_completed',review.get('review_completed') is True);ck('independent_acceptance_FAIL_honest',review['INDEPENDENT_SUBSTITUTION_REVIEW']==review['INDEPENDENT_FINAL_REVIEW']=='FAIL')
    ck('candidate_conflict_reported',adversary['SUBSTITUTION_ADVERSARIAL_FINDINGS_OPEN']==1)
    for path,h in review.get('source_sha256',{}).items():ck('review_hash:'+path,sha(R/path)==h)
    for p in O.glob('*.py'):ast.parse(p.read_text(encoding='utf-8-sig'));ck('syntax:'+p.name,True)
    manifest=rd(O/'SHA256-MANIFEST.json')
    for path,h in manifest['files'].items():ck('sealed:'+path,sha(R/path)==h)
    expected={p.relative_to(R).as_posix() for p in O.rglob('*') if p.is_file() and p.name!='SHA256-MANIFEST.json'}|{report};ck('manifest_exact',set(manifest['files'])==expected);ck('distinct_names',len(checks)==len({c['name'] for c in checks}))
    return dict(scope='PARENT_SEMANTIC_ADJUDICATION_AND_SECTION4_STOP_NOT_WITNESS_RECOMPUTATION',tests_distinct=len(checks),test_failures=sum(not c['passed'] for c in checks),integrity_failures=sum(not c['passed'] and c['category']=='INTEGRITY' for c in checks),static_closure_failures=sum(not c['passed'] and c['category']=='STATIC_CLOSURE' for c in checks),previous28_failures_retested=False,checks=checks)
if __name__=='__main__':
    out=evaluate();print(json.dumps(out if '--detail' in sys.argv else {k:v for k,v in out.items() if k!='checks'}));sys.exit(bool(out['test_failures']))
