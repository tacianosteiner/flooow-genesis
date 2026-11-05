"""Record only the explicit project-authority O8 designation after independent review."""
import hashlib,json,subprocess,sys
from pathlib import Path
O=Path(__file__).resolve().parent;R=O.parents[2];E=O.parent;P='package-0090-B01-v2-native-static-closure-'
HEAD='cbc284f62d9bd09b7169b55c8d66a3c51a68c6cb';ND='NOT_ESTABLISHED'
REPORT=E/'PACKAGE-0090-B01-v2-native-static-closure-r5n2a5-3c4b.md'
INPUT=Path('C:/Users/xmz_r/.codex/attachments/6ab17e13-ba9e-4c7c-b2b1-426752d29991/Pasted text.txt')
REMAINING=['TRANSITION','POSTMASTER_CONTEXT_BINDING','INTERNAL_SCOPE_AND_EXCEPTIONS','EXHAUSTIVE_ATOMIC_BOUNDARY']
REVIEW_KEYS=['INDEPENDENT_OBJECT_BOUNDARY_REVIEW','INDEPENDENT_ANTI_AGGREGATION_REVIEW','INDEPENDENT_I13_PRESERVATION_REVIEW','INDEPENDENT_NON_PREJUDGMENT_REVIEW','INDEPENDENT_HISTORICAL_TRUTHFULNESS_REVIEW']
def rd(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(n,v):(O/n).write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def git(*a):return subprocess.check_output(['git',*a],cwd=R).decode().strip()
def clean():
    assert git('branch','--show-current')=='checkpoint/package-0090-cloud-handoff' and git('rev-parse','HEAD')==HEAD
    assert not git('diff','--name-only') and not git('diff','--cached','--name-only')
def build():
    clean();prev=E/(P+'r5n2a5-3c4a');pb=rd(prev/'baseline-freeze.json');ps=rd(prev/'scope-receipt.json')
    before=[p for p in git('ls-files','--others','--exclude-standard').splitlines() if not p.startswith(O.relative_to(R).as_posix()+'/') and p!=REPORT.relative_to(R).as_posix()]
    assert len(before)==561 and set(before)==set(pb['untracked_before_paths'])|set(ps['new_paths'])
    for p,h in pb['source_sha256'].items():assert sha(R/p)==h,p
    for p,h in rd(prev/'SHA256-MANIFEST.json')['files'].items():assert sha(R/p)==h,p
    form=prev/'project-authority-object-decision-form.json';oldform=rd(form)
    assert oldform['PROJECT_AUTHORITY_SELECTION']==oldform['PROJECT_AUTHORITY_RATIONALE']=='UNSET'
    hashes={p:sha(R/p) for p in sorted(set(git('ls-files').splitlines()+before))}
    put('baseline-freeze.json',dict(branch=git('branch','--show-current'),head=HEAD,untracked_before_paths=before,source_sha256=hashes,UNTRACKED_BEFORE=561,historical_UNSET_form=dict(path=form.relative_to(R).as_posix(),sha256=sha(form),selection='UNSET',rationale='UNSET'),unauthorized_untracked_count=0))
    (O/'project-authority-input.txt').write_bytes(INPUT.read_bytes());text=INPUT.read_text(encoding='utf-8-sig')
    start=text.index('The semantic object representing credential state relevant to');end=text.index('\n\n',start)
    definition=text[start:end]
    rstart=text.index('O8 is selected because the target gap concerns credential');rend=text.index('4. ANTI-AGGREGATION RULE',rstart)
    rationale=text[rstart:rend].rstrip('=\n\r ')
    def source(section):return dict(path='project-authority-input.txt',sha256=sha(INPUT),section=section,authority='EXPLICIT_PROJECT_AUTHORITY_PROSPECTIVE_DESIGNATION_NOT_INFERRED_OLD_MEANING')
    decision=dict(DECISION_ID='R5N2A5_3C4_OBJECT_DESIGNATION',TARGET_GAP='POSTMASTER/credential_inheritance',PROJECT_AUTHORITY_SELECTION='O8',PROTECTED_SEMANTIC_OBJECT='INHERITED_CREDENTIAL_STATE',EXACT_OBJECT_DEFINITION=definition,PROJECT_AUTHORITY_RATIONALE=rationale,AUTHORITY_EFFECT='PROSPECTIVE_SEMANTIC_DESIGNATION_FOR_UNDER_SPECIFIED_ORIGINAL_CASE',DOES_NOT_REWRITE_HISTORY=True,DOES_NOT_CLAIM_PREVIOUS_UNIQUE_DEFINITION=True,RECORDING_STATUS='PENDING_INDEPENDENT_ARTIFACT_REVIEW',OBJECT_RESOLVED='NOT_RECORDED_BEFORE_FINAL_REVIEW',scope='Object designation only; no state schema/constituent membership/event/context/atomicity decision',source=source('§0–§3'))
    put('project-authority-object-designation.json',decision)
    put('object-definition.json',dict(PROTECTED_SEMANTIC_OBJECT='INHERITED_CREDENTIAL_STATE',EXACT_OBJECT_DEFINITION=definition,definition_status='PROJECT_AUTHORITY_TEXT_PENDING_RECORDING_REVIEW',constituent_properties=ND,forbidden_inheritance_conditions=ND,transition=ND,context_predicate=ND,internal_membership_predicate=ND,atomicity_rule=ND,no_runtime_instance_created=True,source=source('§2')))
    excluded=['CREDENTIAL_MATERIAL','CREDENTIAL_IDENTITY','CREDENTIAL_CLASS','AUTHENTICATION_CAPABILITY','CREDENTIAL_CUSTODY_RELATION','CREDENTIAL_AUTHORITY_RELATION','CREDENTIAL_TO_PRINCIPAL_BINDING','CREDENTIAL_BEARING_CAPABILITY','HOST_HELD_EXPECTED_SERVER_ENDPOINT_MANIFEST','PRINCIPAL_IDENTITY','ROLE_IDENTITY','PARTICIPANT_SLOT_IDENTITY']
    put('object-boundary.json',dict(OBJECT_AGGREGATION_BY_FIAT='FORBIDDEN',not_automatic_constituents=excluded,rule='A future property may enter inheritance scope only through explicit semantic analysis with authoritative provenance; credential-related wording alone is insufficient.',any_credential_property_persistence_implies_inheritance=False,object_name_does_not_define_extent=True,distinctions_preserved=True,source=source('§2;§4')))
    questions=[('A','Silently aggregates the other nine candidate objects?','§2 expressly rejects automatic union/aggregation; §4 forbids aggregation by fiat.'),('B','Makes inheritance true merely because any credential-related property persists?','§2 does not determine forbidden inheritance; §4 rejects credential-related therefore member reasoning.'),('C','Absorbs I13/principal independence?','§5 preserves full I13 externally and excludes principal identity as protected object.'),('D','Preselects custody, authority or binding as internal?','§2–§4 preserve distinct concepts and require future independent property membership provenance.'),('E','Determines transition before transition gate?','§3 and §9 explicitly leave TRANSITION unresolved; across the POSTMASTER transition is an uninstantiated context variable.'),('F','Expands POSTMASTER context before context binding?','§3 and §9 explicitly leave POSTMASTER_CONTEXT_BINDING unresolved; no classifier predicate is supplied.'),('G','Establishes an obligation denominator?','§7 forbids N/count/classification/atomicity/coverage inference and preserves108/105/350.'),('H','Rewrites historical intent?','§1 states prospective effect and prohibits prior-unique/always-intended/retroactive invalidation claims.')]
    put('anti-aggregation-review.json',dict(review_type='PRIMARY_EXPLICIT_DECISION_TEXT_FALSIFICATION',checks=[dict(id=i,question=q,answer='NO',reason=reason,source=source('§8 with cited clauses')) for i,q,reason in questions],primary_result='PASS_PENDING_INDEPENDENT_ARTIFACT_REVIEW',no_definition_repair_performed=True))
    put('i13-preservation-review.json',dict(I13_CLASSIFICATION='MANDATORY_EXTERNAL_CROSS_CUTTING_INVARIANT',I13_INTERNAL_FAMILY_MEMBER='NO',I13_PRESERVED_IN_FULL='YES',PRINCIPAL_IDENTITY_IS_PROTECTED_OBJECT='NO',full_principal_independence_remains_required=True,A5_2_reopened=False,source=source('§5'),historical_C1_source_hash=hashes[(E/(P+'r5n2a5-3c1')/'i13-reconstruction.json').relative_to(R).as_posix()]))
    put('three-dimension-non-prejudgment.json',dict(historical_candidates=dict(D1='CREDENTIAL_CUSTODY_INHERITANCE',D2='CREDENTIAL_AUTHORITY_INHERITANCE',D3='CREDENTIAL_BINDING_INHERITANCE'),THREE_DIMENSION_DECOMPOSITION_VALIDATED='NO',individual_dimensions_validated=False,completeness_inferred=False,claim_no_fourth_dimension_exists_made=False,additional_dimension_created=False,source=source('§6')))
    put('denominator-non-prejudgment.json',dict(ATOMIC_NORMATIVE_CANDIDATES_TOTAL=108,AMBIGUOUS_CANDIDATES_PRESERVED=105,candidates_classified=0,CANONICAL_INTERNAL_OBLIGATION_UNIVERSE_ESTABLISHED='NO',CANONICAL_INTERNAL_OBLIGATIONS_TOTAL=ND,CANONICAL_ATTACK_DENOMINATOR=350,DENOMINATOR_CHANGED='NO',ATTACKS_MATERIALIZED_THIS_GATE=0,ATTACKS_EVALUATED_THIS_GATE=0,atomicity_resolved=False,attack_coverage_inferred=False,N1_closed=11,N1_open=1,source=source('§7;§9;§11')))
    put('provenance-index.json',dict(authoritative_input=source('complete user-supplied decision'),authority_event='Project authority explicitly selects O8 now; no inference from evidence or previous dossier preference',historical_dossier=dict(path=(prev/'gate.json').relative_to(R).as_posix(),sha256=hashes[(prev/'gate.json').relative_to(R).as_posix()],selection_at_that_gate='UNSET'),historical_form_preserved=dict(path=form.relative_to(R).as_posix(),sha256=hashes[form.relative_to(R).as_posix()]),current_selection_does_not_mutate_historical_form=True,review_before_authoritative_recording_required=True,preexisting_files=len(hashes)))
    put('outcome.json',dict(SELECTED_OUTCOME='PENDING_REVIEW',status='NO_AUTHORITATIVE_RECORD_UNTIL_ALL_EIGHT_NO_AND_INDEPENDENT_PASS',source_selection='O8',four_remaining_decisions=REMAINING,NEXT_EXECUTED=False,NEXT_GATE='TRANSITION_DECISION_FOR_INHERITED_CREDENTIAL_STATE'))
    print(json.dumps(dict(provisional_record='READY_FOR_INDEPENDENT_REVIEW',source_selection='O8',checks=8,preexisting_files=len(hashes),historical_form='UNSET')))
def finalize():
    clean();b=rd(O/'baseline-freeze.json');review=rd(O/'independent-decision-review.json')
    assert review['DECISION_RECORDING_REVIEW']=='PASS'
    for k in REVIEW_KEYS:assert review[k]=='PASS'
    assert len(review['adversarial_checks'])==8 and all(x['answer']=='NO' for x in review['adversarial_checks'])
    for p,h in b['source_sha256'].items():assert sha(R/p)==h,p
    oldform=rd(R/b['historical_UNSET_form']['path']);assert oldform['PROJECT_AUTHORITY_SELECTION']==oldform['PROJECT_AUTHORITY_RATIONALE']=='UNSET'
    decision=rd(O/'project-authority-object-designation.json');decision.update(RECORDING_STATUS='AUTHORITATIVE_PROJECT_DECISION_RECORDED_AFTER_INDEPENDENT_PASS',OBJECT_RESOLVED='YES');put('project-authority-object-designation.json',decision)
    definition=rd(O/'object-definition.json');definition['definition_status']='RECORDED_EXACT_PROJECT_AUTHORITY_DESIGNATION_OBJECT_ONLY';put('object-definition.json',definition)
    put('outcome.json',dict(SELECTED_OUTCOME='A',status='PROJECT_AUTHORITY_O8_OBJECT_DESIGNATION_RECORDED',OBJECT_RESOLVED='YES',OBJECT='INHERITED_CREDENTIAL_STATE',authority_effect=decision['AUTHORITY_EFFECT'],four_remaining_decisions=REMAINING,UNRESOLVED_ARCHITECTURAL_DECISIONS_TOTAL=4,NEXT_EXECUTED=False,NEXT_GATE='TRANSITION_DECISION_FOR_INHERITED_CREDENTIAL_STATE'))
    REPORT.write_text('''# Package0090 A5.3C.4B — project-authority protected-object designation

PROJECT_AUTHORITY_SELECTION=O8. OBJECT_RESOLVED=YES. OBJECT=INHERITED_CREDENTIAL_STATE. This records the explicit new project-authority decision after eight negative adversarial findings and independent PASS. It is not an autonomous object choice or a claim of previous unique architectural meaning.

Exact definition from the authority input:

> '''+decision['EXACT_OBJECT_DEFINITION'].replace('\n','\n> ')+'''

The designation establishes the object name and this semantic role only. It does not specify its constituent properties, identity schema, forbidden continuity condition or the transition. project-authority-object-designation.json records the supplied rationale verbatim; the complete authority input is copied byte-for-byte with SHA256 provenance. Its assessment of alternatives is the project's prospective rationale, not retroactive invalidation of O1–O7/O9/O10 or a prior Codex recommendation.

## Anti-aggregation boundary

OBJECT_AGGREGATION_BY_FIAT=FORBIDDEN. The state is not automatically a union/super-object of the other nine candidates, principal, role or slot identity. Credential-related wording does not prove membership. Any later property inclusion requires explicit semantic analysis and authoritative provenance. Persistence of any credential-related property does not by itself make forbidden inheritance true. No field list, state schema, hidden conjunction or classified internal set is created here.

## Independent falsification before recording

The primary and independent reviews answer all eight§8questions NO: no automatic aggregation; no any-persistence trigger; no principal/I13 absorption; no custody/authority/binding preselection; no transition selection; no POSTMASTER-context expansion; no N; no rewritten historical intent. The literal phrase across the POSTMASTER transition does not choose the event or a context membership predicate. No repair to the decision is made.

I13 remains full, mandatory and external; principal identity is not the protected object. No A5.2 proof is reopened. D1/D2/D3 remain historical candidates only; none is validated, completeness is unproved and no assertion excludes a possible residual. No D4 is created.

## History and unresolved decisions

AUTHORITY_EFFECT=PROSPECTIVE_SEMANTIC_DESIGNATION_FOR_UNDER_SPECIFIED_ORIGINAL_CASE. DOES_NOT_REWRITE_HISTORY=true. DOES_NOT_CLAIM_PREVIOUS_UNIQUE_DEFINITION=true. The A5.3C.4A decision form remains UNSET/UNSET and byte-identical, correctly showing the state at that earlier gate. The new decision exists only in this new evidence scope, not an edit to the historical form.

Exactly four architectural decisions remain: TRANSITION; POSTMASTER_CONTEXT_BINDING; INTERNAL_SCOPE_AND_EXCEPTIONS; EXHAUSTIVE_ATOMIC_BOUNDARY. They are not executed or resolved here. Candidate108/ambiguous105 remain unchanged and unclassified. No canonical internal universe/N, atomicity rule or attack coverage is established.350attack IDs remain frozen;0attacks materialized/evaluated. N1 qualification CLOSED/substitution OPEN;12decisions=11closed+1open. V2 proof FAIL/status BLOCKED.

## Integrity and execution boundary

All9043pre-existing files, including561prior authorized untracked paths, are hash-preserved. Only new gate evidence is written. Tracked and staging remain clean. No implementation/build/native runtime/SQL/database/shared/production/V043/B02/migration/identity/principal/credential/secret/key/signature/physical-role/privilege/gitadd/commit/push. The authorized architectural designation itself is recorded exactly; no further normative property is invented.

NEXT_GATE=TRANSITION_DECISION_FOR_INHERITED_CREDENTIAL_STATE. NEXT_EXECUTED=false. STOP: OBJECT ONLY.
''',encoding='utf-8')
    g=dict(BRANCH=b['branch'],BASELINE_HEAD=HEAD,CURRENT_HEAD=git('rev-parse','HEAD'),TRACKED_DIRTY_COUNT=0,STAGED_COUNT=0,UNTRACKED_BEFORE=561,UNAUTHORIZED_UNTRACKED_COUNT=0,TARGET_GAP='POSTMASTER/credential_inheritance',PROJECT_AUTHORITY_SELECTION='O8',PROTECTED_SEMANTIC_OBJECT='INHERITED_CREDENTIAL_STATE',AUTHORITY_EFFECT=decision['AUTHORITY_EFFECT'],DOES_NOT_REWRITE_HISTORY=True,DOES_NOT_CLAIM_PREVIOUS_UNIQUE_DEFINITION=True,OBJECT_RESOLVED='YES',OBJECT='INHERITED_CREDENTIAL_STATE',OBJECT_AGGREGATION_BY_FIAT='FORBIDDEN',I13_CLASSIFICATION='MANDATORY_EXTERNAL_CROSS_CUTTING_INVARIANT',I13_INTERNAL_FAMILY_MEMBER='NO',I13_PRESERVED_IN_FULL='YES',PRINCIPAL_IDENTITY_IS_PROTECTED_OBJECT='NO',THREE_DIMENSION_DECOMPOSITION_VALIDATED='NO',ATOMIC_NORMATIVE_CANDIDATES_TOTAL=108,AMBIGUOUS_CANDIDATES_PRESERVED=105,CANONICAL_INTERNAL_OBLIGATION_UNIVERSE_ESTABLISHED='NO',CANONICAL_INTERNAL_OBLIGATIONS_TOTAL=ND,CANONICAL_ATTACK_DENOMINATOR=350,DENOMINATOR_CHANGED='NO',ATTACKS_MATERIALIZED_THIS_GATE=0,ATTACKS_EVALUATED_THIS_GATE=0,N1_QUALIFICATION_INPUT_RESOLUTION='CLOSED',N1_SUBSTITUTION_STATIC_WITNESSES='OPEN',N1_DECISIONS_REQUIRED=12,N1_DECISIONS_CLOSED=11,N1_DECISIONS_OPEN=1,V2_NATIVE_STATIC_DESIGN_PROOF='FAIL',V2_NATIVE_STATUS='BLOCKED',DECISION_RECORDING_REVIEW='PASS',UNRESOLVED_ARCHITECTURAL_DECISIONS_TOTAL=4,UNRESOLVED_ARCHITECTURAL_DECISIONS=REMAINING,IMPLEMENTATION_PERFORMED='NO',NATIVE_BUILD_PERFORMED='NO',NATIVE_RUNTIME_EXECUTED='NO',SQL_EXECUTED='NO',DATABASE_CONTACTED='NO',V043_EXECUTED='NO',B02_EXECUTED='NO',GIT_ADD='NO',COMMIT='NO',PUSH='NO',SELECTED_OUTCOME='A',R5N2A5_3C4B_STATUS='OUTCOME_A_PROJECT_AUTHORITY_OBJECT_DESIGNATION_RECORDED',NEXT_EXECUTED=False,NEXT_GATE='TRANSITION_DECISION_FOR_INHERITED_CREDENTIAL_STATE',EVIDENCE_REPORT=REPORT.relative_to(R).as_posix(),HISTORICAL_C4A_FORM_SELECTION='UNSET',HISTORICAL_C4A_FORM_PRESERVED='YES',CANDIDATES_CLASSIFIED_THIS_GATE=0,TRANSITION_RESOLVED=ND,POSTMASTER_CONTEXT_BINDING_RESOLVED=ND,INTERNAL_SCOPE_RESOLVED=ND,ATOMIC_BOUNDARY_RESOLVED=ND,REMOTE_NETWORK_VERIFIED='NO',INTEGRITY_FAILURES=0,CLOSED_CONTRACTS_REOPENED=0)
    for k in REVIEW_KEYS:g[k]=review[k]
    for n in ['gate.json','scope-receipt.json','SHA256-MANIFEST.json']:
        if not (O/n).exists():put(n,{})
    before=set(b['untracked_before_paths']);now=set(git('ls-files','--others','--exclude-standard').splitlines());new=sorted(now-before);unauthorized=[p for p in new if not(p.startswith(O.relative_to(R).as_posix()+'/') or p==g['EVIDENCE_REPORT'])];assert not unauthorized and before<=now
    g['UNTRACKED_AFTER']=len(now);put('gate.json',g);put('scope-receipt.json',dict(untracked_before=561,untracked_after=len(now),new_paths=new,unauthorized=unauthorized,preexisting_files_verified=len(b['source_sha256']),historical_form_unchanged=True,tracked_dirty=0,staged=0));put('SHA256-MANIFEST.json',dict(algorithm='SHA256',self_excluded=True,files={p:sha(R/p) for p in new if p!=(O/'SHA256-MANIFEST.json').relative_to(R).as_posix()}));print(json.dumps(g,indent=2))
def verify():
    clean();b=rd(O/'baseline-freeze.json');g=rd(O/'gate.json')
    for p,h in b['source_sha256'].items():assert sha(R/p)==h,p
    for p,h in rd(O/'SHA256-MANIFEST.json')['files'].items():assert sha(R/p)==h,p
    before=set(b['untracked_before_paths']);now=set(git('ls-files','--others','--exclude-standard').splitlines());s=rd(O/'scope-receipt.json');assert before<=now and now-before==set(s['new_paths']) and len(now)==g['UNTRACKED_AFTER'] and not s['unauthorized']
    f=rd(R/b['historical_UNSET_form']['path']);assert f['PROJECT_AUTHORITY_SELECTION']==f['PROJECT_AUTHORITY_RATIONALE']=='UNSET'
    assert sha(O/'project-authority-input.txt')==rd(O/'provenance-index.json')['authoritative_input']['sha256']
    d=rd(O/'project-authority-object-designation.json');assert d['PROJECT_AUTHORITY_SELECTION']=='O8' and d['OBJECT_RESOLVED']=='YES' and d['RECORDING_STATUS']=='AUTHORITATIVE_PROJECT_DECISION_RECORDED_AFTER_INDEPENDENT_PASS'
    assert all(x['answer']=='NO' for x in rd(O/'independent-decision-review.json')['adversarial_checks'])
    assert g['OBJECT_AGGREGATION_BY_FIAT']=='FORBIDDEN' and g['UNRESOLVED_ARCHITECTURAL_DECISIONS']==REMAINING
    assert g['I13_PRESERVED_IN_FULL']=='YES' and g['I13_INTERNAL_FAMILY_MEMBER']=='NO'
    assert g['CANDIDATES_CLASSIFIED_THIS_GATE']==g['ATTACKS_MATERIALIZED_THIS_GATE']==g['ATTACKS_EVALUATED_THIS_GATE']==0
    assert g['CANONICAL_INTERNAL_OBLIGATIONS_TOTAL']==ND and g['THREE_DIMENSION_DECOMPOSITION_VALIDATED']=='NO' and g['N1_DECISIONS_CLOSED']==11 and g['V2_NATIVE_STATUS']=='BLOCKED'
    print(json.dumps(dict(DECISION_RECORD_INTEGRITY='PASS',preexisting_files=len(b['source_sha256']),designation='O8',object_resolved=True,unresolved=4,historical_form='UNSET',classified=0,attacks=0,tracked_dirty=0,staged=0,untracked_after=len(now))))
if __name__=='__main__':{'build':build,'finalize':finalize,'verify':verify}[sys.argv[1]]()
