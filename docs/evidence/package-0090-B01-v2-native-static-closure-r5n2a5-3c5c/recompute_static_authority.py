"""C5C evidence-only authority/lineage audit. No native implementation or attacks executed."""
import collections
import hashlib
import itertools
import json
import pathlib
import re
import subprocess

ROOT = pathlib.Path(__file__).resolve().parents[3]
HERE = pathlib.Path(__file__).resolve().parent
E = ROOT/'docs/evidence'
PREFIX = 'package-0090-B01-v2-native-static-closure-'
N = E/(PREFIX+'r5n')
N1 = E/(PREFIX+'r5n1')
N2 = E/(PREFIX+'r5n2')
A5 = E/(PREFIX+'r5n2a5')
A52 = E/(PREFIX+'r5n2a5-2')
C4B = E/(PREFIX+'r5n2a5-3c4b')
C5A = E/(PREFIX+'r5n2a5-3c5a-resumption')
C5B = E/(PREFIX+'r5n2a5-3c5b')


def rd(p):
    return json.loads(p.read_text(encoding='utf-8-sig'))


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def rel(p):
    return p.relative_to(ROOT).as_posix()


def canon(v):
    return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()


def select(v,ptr):
    for k in ptr.strip('/').split('/') if ptr not in ('','/') else []:
        k=k.replace('~1','/').replace('~0','~')
        v=v[int(k)] if isinstance(v,list) else v[k]
    return v


def out(name,value):
    (HERE/name).write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')


def ref(path,ptr,proposition,authority='FROZEN_ACCEPTED_STATIC_DESIGN',derived=False):
    value=select(rd(path),ptr)
    return dict(path=rel(path),sha256=sha(path),pointer=ptr,canonical_fact_sha256=canon(value),
                semantic_proposition=proposition,authority_class=authority,
                direct_or_derived='DERIVED_STATIC_LINEAGE_ANALYSIS' if derived else 'DIRECT_SOURCE_SELECTION')


VERIFIED_REFS = set()


def verify_ref(r):
    key=(r['path'],r['sha256'],r.get('pointer',''),r.get('canonical_fact_sha256',''))
    if key in VERIFIED_REFS:
        return
    path=ROOT/r['path'];assert sha(path)==r['sha256'],r['path']
    if 'pointer' in r and path.suffix=='.json':
        value=select(rd(path),r['pointer'])
        if 'canonical_fact_sha256' in r:
            assert canon(value)==r['canonical_fact_sha256'],key
    elif 'pointer' in r:
        assert r['pointer'] in ('','/') and 'canonical_fact_sha256' not in r
    VERIFIED_REFS.add(key)


def verify_nested(value):
    if isinstance(value,dict):
        if 'path' in value and 'sha256' in value:
            verify_ref(value)
        for v in value.values():
            verify_nested(v)
    elif isinstance(value,list):
        for v in value:
            verify_nested(v)


def adoption():
    text=(HERE/'project-authority-input.txt').read_text(encoding='utf-8-sig')
    keys=['PRE_STATE','EVENT','POST_STATE','CORE_RULE','FORBIDDEN_CONTINUITY','REQUIRED_DISCONTINUITY','ALLOWED_CONTINUITY']
    fields={k:re.search(r'(?m)^'+k+r'=\s*\n([A-Z0-9_/]+)',text).group(1) for k in keys}
    assert fields['EVENT']=='FRESH_GENERATION_LEDGER_SUCCESSION'
    record={
        'TARGET_GAP':'POSTMASTER/credential_inheritance','OBJECT':'INHERITED_CREDENTIAL_STATE',
        'AUTHORITATIVE_TRANSITION':'T8/FRESH_GENERATION_LEDGER_SUCCESSION',
        'AUTHORITY_CLASS':'EXPLICIT_PROSPECTIVE_PROJECT_AUTHORITY',
        'HISTORICAL_ENTAILMENT_CLAIMED':'NO',**fields,
        'source':{'path':rel(HERE/'project-authority-input.txt'),'sha256':sha(HERE/'project-authority-input.txt'),'section':'PROJECT AUTHORITY — PROSPECTIVE DESIGNATION','direct_or_derived':'DIRECT_USER_AUTHORITY'},
        'provenance_chain':['C5A: eight prospective non-dominated alternatives, no selection','C5B: no unique frozen-authority entailment, selection required','Current PROJECT_AUTHORITY: explicit prospective T8 designation','C5C: adoption/consistency and static witness authority audit'],
        'C5B_selected_T8':False,'candidate_selection_rerun':False,'historical_artifacts_rewritten':False,
        'substitution_necessary':'NOT_ESTABLISHED_BY_DESIGNATION','substitution_sufficient':'NOT_ESTABLISHED_BY_DESIGNATION',
        'I13_PRESERVED_IN_FULL':'YES','I13_REDEFINED':'NO',
    }
    out('prospective-authority-record.json',record)
    return fields


def provenance():
    records=[]
    for filename,ptr,prop in [
        (N/'native-registry-generation.json','/state_edges/GENERATION_LEDGER','T8 is the same source TOMBSTONED→NEW_GENERATION edge, not a new event.'),
        (N/'native-registry-generation.json','/records/1','Ledger high-water, prior tombstone, old invalidation and checked previous+1 before new enrollment.'),
        (N/'native-registry-generation.json','/records/0','Old credential/channel ineligibility, no old-key/enrollment/work adoption, UNKNOWN barriers.'),
        (N1/'credential-custody.json','/credentials/0','POSTMASTER custody/currentness/retirement and endpoint form remain binding.'),
        (E/(PREFIX+'r5n2a3')/'credential-class-manifest.json','/classes/2','Conditional protected delivery; no operational transfer or inheritance; separate authority and generation bindings.'),
        (A52/'replacement-topology.json','/closures','Full seven-slot qualified ACTIVE replacement; six private fresh keys and POSTMASTER endpoint renewal, without automatic numeric UID delta.'),
        (A52/'canonical-witness-model.json','','Corrected required proof universe and withdrawn strict-tuple preservation expectations.'),
        (A52/'pairwise-requirement-provenance.json','','Strict21 is not canonical; exact original requirement provenance retained.'),
        (A52/'original-negative-witness-audit.json','','All350 remain required: 133 structured candidates un-reexecuted, 217 generic/incomplete.'),
        (A5/'qualification-input-ledger.json','','70 statically resolved input lineages, not live qualification.'),
        (A5/'qualification-closure.json','','Qualification input resolution CLOSED independently of still-open substitution.'),
        (N2/'substitution-witnesses.json','','Original350 attack IDs and their existing schema/predicate candidates; no new attack materialization.'),
        (C4B/'object-boundary.json','','O8 must not automatically aggregate credential material, identity, custody, authority, binding or principal.'),
        (E/(PREFIX+'r5n2a5-3c1')/'i13-reconstruction.json','','Full external concurrent seven-slot/21-pair principal invariant and auxiliary separation.'),
        (C5B/'gate.json','','C5B OutcomeB did not entail/designate T8 or close N1.'),
    ]:
        r=ref(filename,ptr,prop);verify_ref(r);records.append(r)
    out('authority-provenance.json',{'current_authority':rd(HERE/'prospective-authority-record.json')['source'],
        'source_records':records,'authority_precedence':'New explicit prospective event/core rule, within preserved frozen contracts; conditional permission is not an exception overriding existing scoped prohibitions.',
        'no_authority_from':['reviewer agreement','preservation checkpoint or LFS rules','docs/post-mvp','STOP or rejected drafts'],
        'all_preexisting_source_bytes_frozen':True})


def transition(fields):
    result={**fields,'TRANSITION_RESOLVED':'YES','resolution_scope':'Prospective T8 identity and supplied authority-continuity rule only; not exhaustive O8 membership/context/atomicity or witness closure.',
        'source_event':{'id':'T8','name':'FRESH_GENERATION_LEDGER_SUCCESSION','PRE':'GENERATION_LEDGER.TOMBSTONED','EVENT':'Checked previous+1 ledger succession with prior tombstone retained','POST':'GENERATION_LEDGER.NEW_GENERATION; new enrollment/qualification not established by edge alone'},
        'semantic_to_source_mapping':[
            {'field':'PRE_STATE','mapping':'Source-generation credential-state provenance/domain is referenced; it is not a CURRENT usable grant immediately before T8. The immediate source ledger state remains TOMBSTONED, and old authority remains ineligible. No private live source material is asserted to survive.',
             'basis':[ref(N/'native-registry-generation.json','/records/1/replacement','Old invalidation/extinction/tombstone precede new eligibility'),ref(N/'native-registry-generation.json','/records/1/stale_generation','No earlier-generation fallback')]},
            {'field':'EVENT','mapping':'Exactly the existing T8 source ledger edge, not a replacement compound, process birth or new credential creation.',
             'basis':[ref(N/'native-registry-generation.json','/state_edges/GENERATION_LEDGER','Source edge TOMBSTONED→NEW_GENERATION')]},
            {'field':'POST_STATE','mapping':'Target generation exists and its credential authority REQUIRES target-generation qualification. This does not assert qualification or a valid grant already exists at ledger advancement.',
             'basis':[ref(N1/'credential-custody.json','/credentials/0/GENERATION_BINDING','Independently current exact generation mandatory'),ref(N1/'credential-custody.json','/credentials/0/REGISTRY_BINDING','Current enrollment/publication revisions mandatory')]},
        ],
        'derived_rules':[
            {'id':'R1','rule':'Source-generation credential authority alone is insufficient to establish target-generation authority.', 'basis':'DIRECT_CURRENT_CORE_RULE'},
            {'id':'R2','rule':'At T8, do not treat the old authority as qualified target authority without independent target qualification.', 'basis':'DIRECT_CURRENT_FORBIDDEN_CONTINUITY_AND_POST_STATE'},
            {'id':'R3','rule':'Material equality or difference alone cannot prove target authority; no automatic material rotation requirement is derived.', 'basis':'CURRENT_MANDATORY_DISTINCTION_AND_CORE_RULE'},
            {'id':'R4','rule':'Missing/unknown independently current target qualification cannot grant authority; preserve fail-closed UNKNOWN/NOT_QUALIFIED.', 'basis':[ref(N/'native-registry-generation.json','/records/0/UNKNOWN','No new eligibility while unresolved'),ref(N1/'credential-custody.json','/credentials/0/UNKNOWN_CUSTODY_BEHAVIOR','Unknown custody fails closed')]},
            {'id':'R5','rule':'Conditional allowed material/identity continuity requires separate authorization AND qualification; neither is supplied by the word may.', 'basis':'DIRECT_CURRENT_ALLOWED_CONTINUITY'},
            {'id':'R6','rule':'Existing fresh-key, renewed endpoint, retirement, extinction, retained-parent and full-cohort requirements remain binding in their approved ACTIVE replacement scope.', 'basis':[ref(A52/'replacement-topology.json','/closures','Frozen qualified ACTIVE replacement scope and exact mandatory renewal sets')]},
            {'id':'R7','rule':'I13 remains mandatory external; substitution necessity/sufficiency, all-credential revocation and principal-change obligations are not inferred from this designation.', 'basis':'DIRECT_CURRENT_MANDATORY_DISTINCTION; independent existing constraints retained'},
        ],
        'CREDENTIAL_MATERIAL_ROTATION_REQUIRED':'NOT_BY_DESIGNATION; independent scoped fresh-key/endpoint requirements retained',
        'PRINCIPAL_IDENTITY_CHANGE_REQUIRED':'NOT_BY_DESIGNATION; independent fresh qualified-subject requirements retained, no numeric UID delta inferred',
        'SUBSTITUTION_NECESSARY':'NOT_ESTABLISHED_BY_DESIGNATION','SUBSTITUTION_SUFFICIENT':'NOT_ESTABLISHED_BY_DESIGNATION',
        'I13_PRESERVED_IN_FULL':'YES','DISTINCT_CONCURRENT_PRINCIPALS_REQUIREMENT':'INDEPENDENT_I13_NOT_DERIVED_FROM_DESIGNATION',
        'target_qualification_evidence_supplied_by_designation':False,
    }
    out('transition-recomputation.json',result)
    out('contradiction-analysis.json',{
        'status':'NO_CONTRADICTION_FOUND_WITH_PRESERVED_SOURCE_EVENT_AND_SCOPED_RULES',
        'checks':[
            {'question':'PRE restores usable source authority in TOMBSTONED?', 'result':'NO','reason':'State provenance/domain is not live eligibility. Both raw semantic wording and immediate ledger cut are preserved explicitly; no CURRENT source grant inferred.'},
            {'question':'POST assumes target qualification already true?', 'result':'NO','reason':'Requires qualification expresses a prerequisite, not its successful satisfaction.'},
            {'question':'Allowed continuity silently overrides fresh6keys/POSTMASTER endpoint renewal?', 'result':'NO','reason':'Conditional separate authorization is not a new exception; frozen qualified-restart rules remain in force.'},
            {'question':'Designation rotates all material, revokes every prior credential or changes every principal?', 'result':'NO','reason':'Those global propositions do not follow. Only independently scoped prior rules retain their existing effect.'},
            {'question':'T8 renamed/combined or C5B made historical selector?', 'result':'NO','reason':'Source edge and complete prospective provenance chain remain unchanged.'},
            {'question':'O8 authority non-transfer rule automatically makes every authority/custody/material property an internal member?', 'result':'NO','reason':'New explicit bounded rule is adopted, not an automatic expansion of the O8 universe.'},
        ],'contradictions_found':[],'no_repair_of_historical_evidence':True})


def denominator():
    model=rd(A52/'canonical-witness-model.json');universe=model['required_proof_universe']
    assert universe=={'dimension_specific_pair_comparisons':189,'valid_ACTIVE_replacement_closures':7,'original_negative_attack_cases':350,'qualification_inputs':70}
    old=rd(A5/'substitution-witness-ledger.json');assert old['required']==21
    audit=rd(A52/'pairwise-requirement-provenance.json');assert audit['STRICT_21_PAIR_REQUIREMENT_CANONICAL']=='NO'
    out('denominator-audit.json',{
        'historical_reported_21_21_21':{'source':ref(A5/'gate.json','','Historical untyped pair counts'),
            'pair_key_universe':21,'legacy_substitution_ledger_rows':len(old['witnesses'])},
        'canonical_corrected_universe':universe,
        'canonical_universe_source':ref(A52/'canonical-witness-model.json','/required_proof_universe','Already accepted corrected proof universe, not a C5C invention'),
        'strict21_not_canonical_source':ref(A52/'pairwise-requirement-provenance.json','/STRICT_21_PAIR_REQUIREMENT_CANONICAL','No canonical strict complete-other-tuple preservation requirement'),
        'old28_expectations':model['noncanonical_old_expectations'],
        'interpretation':{
            'INDEPENDENCE_RELATIONS_REQUIRED':'21 unordered pair keys in the canonical static concurrent non-collapse view, separately audited across nine dimensions (189 rows); not strict hot-replacement independence.',
            'REVOCATION_RELATIONS_REQUIRED':'21 static distinct revocation-unit pair relations; not unaffected service availability.',
            'SUBSTITUTION_WITNESSES_REQUIRED':'350 canonical original negative cases, not the old21 strict pair-preservation ledger. Seven valid replacement closures and70 qualification inputs are separate existing proof units.',
            'relation_views_not_additive':'The 21 non-collapse and21 revocation views reuse dimension rows; they do not increase the canonical189/7/350/70 universe or attack350.',
        },
        'attack_denominator_changed':False,'canonical_proof_universe_changed':False,
        'historical_generic21_substitution_is_not_full_N1_denominator':True})


def witnesses():
    matrices=[];dimension_rows=[];by_dim={}
    for path in sorted(A52.glob('*-independence-matrix.json')):
        d=rd(path)
        if 'relations' not in d:
            continue
        assert d['required']==21 and len(d['relations'])==21
        assert len({tuple(r['pair']) for r in d['relations']})==21
        by_dim[d['dimension']]=d
        for i,row in enumerate(d['relations']):
            verify_nested(row)
            cls=row['classification'];assert cls in ['PROVEN_INDEPENDENT','PROVEN_DEPENDENT']
            claim=('Distinct concurrent non-collapsing source units under the named scoped dimension' if cls=='PROVEN_INDEPENDENT' else 'Valid ACTIVE replacement necessarily renews dependent complete process-generation subjects; strict unaffected-process preservation is not required')
            dimension_rows.append({'id':d['dimension']+'/'+('/'.join(row['pair'])),'dimension':d['dimension'],'pair':row['pair'],
                'claim':claim,'status':'PROVEN','scope':'STATIC_ACCEPTED_DIMENSION_RELATION_NOT_PHYSICAL_OBSERVATION_OR_NEGATIVE_ATTACK_RESULT',
                'independence_predicate_truth':'TRUE' if cls=='PROVEN_INDEPENDENT' else 'FALSE_PROVEN_DEPENDENT',
                'source_property':row['property'],'source_classification':cls,
                'source':ref(path,'/relations/'+str(i),'Preserved scoped dimension conclusion and verified evidence chain'),
                'evidence':row['evidence'],'T8_effect':'No automatic transfer rule does not collapse concurrent units or remove required full-cohort dependencies.'})
        matrices.append(ref(path,'','Nine separately typed dimension matrices'))
    assert len(by_dim)==9 and len(dimension_rows)==189
    independent_dims=[k for k,v in by_dim.items() if all(r['classification']=='PROVEN_INDEPENDENT' for r in v['relations'])]
    assert len(independent_dims)==7
    roster=by_dim['PRINCIPAL_INDEPENDENCE']['participants'];pairs=list(itertools.combinations(roster,2));assert len(pairs)==21
    noncollapse=[]
    for pair in pairs:
        supporting=[x for x in dimension_rows if set(x['pair'])==set(pair) and x['dimension'] in independent_dims]
        assert len(supporting)==7
        noncollapse.append({'pair':list(pair),'status':'PROVEN','property':'STATIC_CONCURRENT_SLOT_AUTHORITY_CREDENTIAL_CUSTODY_GENERATION_PRINCIPAL_PROCESS_AND_REVOCATION_NON_COLLAPSE',
            'supporting_dimension_ids':[x['id'] for x in supporting],
            'not_proven_by_this':'Complete substitution witness, unchanged other process tuples, hot restart independence, runtime principal values or every future substitution.'})
    revocation=[x for x in dimension_rows if x['dimension']=='REVOCATION_INDEPENDENCE'];assert len(revocation)==21
    restart=rd(A52/'valid-replacement-witnesses.json');assert restart['required']==restart['passing']==7
    restart_rows=[]
    topology=rd(A52/'replacement-topology.json')['closures']
    for i,w in enumerate(restart['witnesses']):
        assert w['RESULT']=='PASS_STATIC_RESTART_CONTRACT' and all(w['CHECKS'].values())
        assert w['closure']==next(c for c in topology if c['REPLACE']==w['subject'])
        restart_rows.append({'id':w['WITNESS_ID'],'status':'PROVEN','source':ref(A52/'valid-replacement-witnesses.json','/witnesses/'+str(i),'Valid full-cohort static restart contract, not a strict old test PASS'),
            'scope':'STATIC_RESTART_CONTRACT_ONLY','preserved_checks':w['CHECKS'],'T8_effect':'Requires fresh qualification; generation ledger advancement alone is insufficient.'})
    qual=rd(A5/'qualification-input-ledger.json');assert len(qual['inputs'])==70
    qualification_rows=[]
    for i,q in enumerate(qual['inputs']):
        assert q['RESOLUTION_STATUS']=='RESOLVED' and not q['physical_values_present'];verify_nested(q)
        qualification_rows.append({'id':q['QUALIFICATION_INPUT_ID'],'status':'PROVEN','scope':q['resolution_scope'],
            'source':ref(A5/'qualification-input-ledger.json','/inputs/'+str(i),'Already closed static input lineage/validation; live truth remains future'),
            'T8_effect':'No target qualification truth inferred from existing input contract or ledger succession.'})
    cases=rd(N2/'substitution-witnesses.json')['cases'];audit=rd(A52/'original-negative-witness-audit.json')
    prior={x['ATTACK_ID']:x for x in audit['records']};assert len(cases)==len(prior)==350
    negative=[]
    keys={'ATTACK_ID','SUBSTITUTED_COMPONENT','EXPECTED_IDENTITY','OBSERVED_IDENTITY_SOURCE','WITNESS','COMPARISON','REJECTION','UNKNOWN_BEHAVIOR','STATIC_WITNESS_COMPLETE'}
    for i,c in enumerate(cases):
        assert set(c)==keys
        before=prior[c['ATTACK_ID']];assert before['still_required'];verify_nested(c);verify_ref(before['source'])
        structured=isinstance(c['WITNESS'],dict) and isinstance(c['COMPARISON'],dict)
        assert structured==c['STATIC_WITNESS_COMPLETE']
        missing=['Case-specific typed STATIC baseline (not live production measurements)',
                 'Exact attack mutation against that baseline, bound to the selected predicate/context',
                 'Reproducible calculated REJECT/UNKNOWN decision and full static authority/effect chain']
        if not structured:
            missing.insert(0,'Exact attack-specific field/effect mapping; current generic WITNESS explicitly says pending')
        target=c['ATTACK_ID']=='POSTMASTER/credential_inheritance'
        negative.append({'id':c['ATTACK_ID'],'status':'UNKNOWN','source_index':i,
            'source':ref(N2/'substitution-witnesses.json','/cases/'+str(i),'Original case ID/payload; schema/formula candidate is not a calculated static attack witness'),
            'prior_audit_source':ref(A52/'original-negative-witness-audit.json','/records/'+str(i),'Original full-negative proof gap preserved'),
            'legacy_STATIC_WITNESS_COMPLETE_flag':c['STATIC_WITNESS_COMPLETE'],
            'existing_partial_artifact':'STRUCTURED_SCHEMA_AND_COMPARISON_FORMULA_CANDIDATE' if structured else 'GENERIC_EXACT_MAPPING_PENDING',
            'full_chain_artifact_audit':{'typed_schema_template_present':structured,'comparison_formula_template_present':structured,
                'case_specific_typed_baseline_present':False,'exact_instantiated_attack_mutation_present':False,'calculated_case_decision_present':False},
            'missing_authority_or_evidence':missing,
            'T8_effect':'Prospective event and bounded no-automatic-authority-transfer rule now fixed; no field/effect mapping, typed case mutation or calculated witness supplied.' if target else 'No new case-level baseline/mutation/calculation supplied. POSTMASTER T8 designation does not silently define other participants or attack semantics.',
            'target_scope_or_membership_presumed':False,'static_case_evaluated_this_gate':False,'runtime_or_attack_executed':False})
    assert sum(r['legacy_STATIC_WITNESS_COMPLETE_flag'] for r in negative)==133
    old=rd(A5/'substitution-witness-ledger.json')
    legacy=[]
    for i,w in enumerate(old['witnesses']):
        legacy.append({'id':w['WITNESS_ID'],'source':ref(A5/'substitution-witness-ledger.json','/witnesses/'+str(i),'Historical pair ledger, not full canonical substitution proof denominator'),
            'adjudication':'SUPERSEDED_EXPECTATION_VIEW_NOT_COUNTED_AS_FULL_N1_WITNESS',
            'correction_basis':ref(A52/'pairwise-requirement-provenance.json','/STRICT_21_PAIR_REQUIREMENT_CANONICAL','Strict complete-other-process preservation is not canonical'),
            'no_relabel_as_PASS':True})
    out('full-witness-matrix.json',{
        'scope':'Complete existing corrected STATIC proof surface; lineage/authority audit only, no attack materialization/evaluation.',
        'dimension_relations':dimension_rows,'valid_ACTIVE_replacement_closures':restart_rows,
        'qualification_inputs':qualification_rows,'canonical_negative_witnesses':negative,
        'derived_noncollapse_pair_view':noncollapse,'revocation_view_ids':[x['id'] for x in revocation],
        'historical21_pair_ledger_adjudication':legacy,
        'canonical_rows_total':616,'canonical_status_counts':{'PROVEN':266,'DISPROVEN':0,'UNKNOWN':350},
        'independence_predicate_counts_within_189':{'TRUE_PROVEN_INDEPENDENT':147,'FALSE_PROVEN_DEPENDENT':42,'UNKNOWN':0},
        'false_independence_is_not_a_failed_canonical_obligation':'42 known dependency comparisons confirm approved full-cohort restart constraints; they are not old strict preservation tests relabeled PASS.',
        'non_additive_views':True,'INDEPENDENCE_RELATIONS_REQUIRED':21,'INDEPENDENCE_RELATIONS_PROVEN':21,'INDEPENDENCE_RELATIONS_UNKNOWN':0,
        'INDEPENDENCE_SCOPE':'STATIC_CONCURRENT_NON_COLLAPSE_COMPOSITE_ACROSS_SEVEN_INDEPENDENT_DIMENSIONS; not strict replacement independence',
        'REVOCATION_RELATIONS_REQUIRED':21,'REVOCATION_RELATIONS_PROVEN':21,'REVOCATION_RELATIONS_UNKNOWN':0,
        'SUBSTITUTION_WITNESSES_REQUIRED':350,'SUBSTITUTION_WITNESSES_PROVEN':0,'SUBSTITUTION_WITNESSES_UNKNOWN':350,
        'qualification_scope_not_live':True,'existing_133_partial_candidates_retained':133,'existing_217_generic_mapping_gaps_retained':217,
        'postmaster_credential_inheritance_new_status':'UNKNOWN_FULL_WITNESS_CHAIN_DESPITE_RESOLVED_EVENT',
        'verified_unique_source_selections':len(VERIFIED_REFS)})


def countermodels():
    specs=[
        ('CM1','Same credential material survives T8 but receives independently qualified target authority',
         'Conditional logical distinction; separate reuse authorization is not supplied. In approved full-cohort ACTIVE restart, reuse of an old private key or unchanged POSTMASTER endpoint identity conflicts with independent renewal rules. Do not call that a compliant path.',
         'NO_AUTOMATIC_AUTHORITY_TRANSFER_DOES_NOT_EQUAL_MATERIAL_ROTATION','UNKNOWN_FULL_CONTRACT_REUSE_AUTHORIZATION'),
        ('CM2','Material changes but target authority is not validly established',
         'Changed material without independently current target enrollment/qualification cannot establish authority. Target qualification remains absent/UNKNOWN; material difference alone does not cure it.',
         'MATERIAL_CHANGE_NOT_SUFFICIENT_FOR_AUTHORITY','COMPATIBLE_FAIL_CLOSED_STATE_NOT_SUCCESSFUL_TARGET_GRANT'),
        ('CM3','Same principal survives T8 with separately qualified authority',
         'Stable logical slot or potentially reused numeric UID is not the same retained qualified process/enrollment subject. New qualified subjects are independently required for approved full-cohort restart; an unchanged old birth subject is not authorized by the designation.',
         'PRINCIPAL_AND_AUTHORITY_DISCONTINUITY_DISTINCT','CONDITIONAL_ON_MEANING_OF_PRINCIPAL_AND_SEPARATE_QUALIFICATION'),
        ('CM4','Participant substitution occurs without target authority established',
         'Replacement/fresh birth without complete target qualification cannot establish usable authority. Failed/pending qualification remains representable and is not a completed qualified T1 success.',
         'SUBSTITUTION_NOT_AUTOMATIC_AUTHORITY_PROOF','COMPATIBLE_PENDING_OR_FAILED_QUALIFICATION_STATE'),
        ('CM5','Target authority established without participant substitution',
         'T8 does not prove substitution necessary or sufficient. No approved ACTIVE replacement path avoiding required fresh qualified subjects is established; the general logical claim remains conditional, not a newly permitted bypass.',
         'SUBSTITUTION_NECESSITY_NOT_INFERRED','UNKNOWN_CONFORMING_PATH_WITHOUT_QUALIFIED_SUBJECT_RENEWAL'),
        ('CM6','Source authority revoked but target authority absent',
         'Source invalidation is a prerequisite, not a target grant. Retirement with no completed replacement remains distinguishable from successful target qualification.',
         'REVOCATION_NOT_TARGET_QUALIFICATION','COMPATIBLE_RETIREMENT_WITHOUT_TARGET_GRANT'),
        ('CM7','Target authority exists while I13 independently requires concurrent-principal separation',
         'A qualified target grant does not absorb or discharge seven-slot/21-pair principal independence or auxiliary separation; I13 remains independently mandatory.',
         'I13_NOT_REDUCIBLE_TO_AUTHORITY_CONTINUITY','COMPATIBLE_WITH_FULL_EXTERNAL_I13_AS_A_STATIC_OBLIGATION'),
        ('CM8','T8 occurs while another lifecycle event occurs independently',
         'Distinct event types are not one compound. Exact concurrency/independence for a particular subject/domain pair must be independently proved; same-source before-enrollment and old retirement prerequisites cannot be reordered.',
         'NO_LIFECYCLE_OR_ATOMIC_SIMULTANEITY_INFERRED','UNKNOWN_EXACT_INDEPENDENT_INTERLEAVING_NOT_PROVEN_TRACE'),
    ]
    rows=[]
    for ident,scenario,analysis,distinction,status in specs:
        rows.append({'id':ident,'scenario':scenario,'analysis':analysis,'distinction_tested':distinction,
            'result':status,'family_rejected':False,'survives_as':'Logical/conditional falsification attempt; not a verified compliant runtime path',
            'independent_limits':[ref(A52/'replacement-topology.json','/closures','Independent scoped renewal/retained-subject rules remain'),ref(N/'native-registry-generation.json','/records/0','Old invalidation/currentness/UNKNOWN requirements'),ref(E/(PREFIX+'r5n2a5-3c1')/'i13-reconstruction.json','','Independent I13 remains external')],
            'rejected_solely_because_T8_designated':False,'actual_trace_or_attack':False})
    out('countermodels.json',{'records':rows,'total':8,'rejected_families':0,'surviving_conditional_distinction_attempts':8,
        'eight_compliant_source_paths_claimed':False,'specific_old_key_or_retained_subject_bypass_interpretations':'NOT_AUTHORIZED_BY_CURRENT_CONDITIONAL_PERMISSION; independently scoped renewal constraints still apply',
        'no_countermodel_eliminated_by_preference_or_event_designation_alone':True})


def result():
    out('primary-result.json',{
        'SELECTED_OUTCOME':'B','status':'TRANSITION_RESOLVED_WITNESS_INCOMPLETE','TRANSITION_RESOLVED':'YES',
        'T8_survives_consistency_and_adversarial_rule_recomputation':True,
        'SUBSTITUTION_WITNESSES_REQUIRED':350,'SUBSTITUTION_WITNESSES_PROVEN':0,'SUBSTITUTION_WITNESSES_UNKNOWN':350,
        'missing_witness_authority':'217 generic cases still lack exact attack field/effect mapping; all350 lack case-specific typed static baseline, exact mutation and calculated complete decision proof. 133 existing schema/formula candidates remain partial and are not erased.',
        'T8_specific_gap':'Event and bounded no-automatic-authority-transfer obligation are now designated; POSTMASTER/credential_inheritance exact witness mapping/mutation/calculation remains missing. Designation is not qualified target authority or a complete O8 scope.',
        'why_not_A':'Required full negative witness chains remain UNKNOWN.',
        'why_not_C':'No source-event identity or scoped frozen rule contradicted by conditional prospective designation.',
        'why_not_D':'A separate frozen architectural decision has not been proven to be the minimum prerequisite for this authority-chain completeness audit. Missing witness artifacts already suffice to block closure; exact scope/context dependencies are not invented or resolved here.',
        'why_not_E':'Exact55 authorized paths, manifests, frozen ancestry and9154 preexisting hashes verified.',
        'POSTMASTER_CONTEXT_BINDING_RESOLVED':'NO','INTERNAL_SCOPE_RESOLVED':'NO','ATOMIC_BOUNDARY_RESOLVED':'NO',
        'CANONICAL_INTERNAL_OBLIGATION_UNIVERSE_ESTABLISHED':'NO','CANONICAL_INTERNAL_OBLIGATIONS_TOTAL':'NOT_ESTABLISHED',
        'N1_SUBSTITUTION_STATIC_WITNESSES':'OPEN','N1_DECISIONS_REQUIRED':12,'N1_DECISIONS_CLOSED':11,'N1_DECISIONS_OPEN':1,
        'V2_NATIVE_STATIC_DESIGN_PROOF':'FAIL','V2_NATIVE_STATUS':'BLOCKED',
        'NEXT_EXECUTED':False,'NEXT_GATE':'BOUNDED_STATIC_WITNESS_AUTHORITY_AND_ARTIFACT_COMPLETION_NO_EXECUTION'})


def report(fields):
    text='''# Package0090 C5C — authority adoption and static witness recomputation

Primary outcome B: **TRANSITION_RESOLVED_WITNESS_INCOMPLETE**. Explicit prospective project authority now designates T8/FRESH_GENERATION_LEDGER_SUCCESSION. This resolves the event and the supplied bounded authority-continuity semantics, not the full negative witness chain. No candidate selection is rerun. C5B remains historically Outcome B; it did not select T8.

## Preservation and authority adoption

Branch `checkpoint/package-0090-cloud-handoff`; documentary HEAD `451265ff5b3d286eb4d27c4b3817c2f558f30123`; frozen implementation baseline `cbc284f62d9bd09b7169b55c8d66a3c51a68c6cb` remains ancestor. Preflight reconciles exactly55 authorized untracked files: seven C5A STOP,24 C5A resumption,24 C5B. Three manifests and all9,154 preexisting file hashes, including V043, are preserved. LFS machinery is not semantic authority. Parallel post-MVP files remain hash-only preservation inputs.

The exact current authority input is retained. Provenance is C5A eight alternatives → C5B no unique frozen entailment → current explicit prospective T8 designation → C5C consequence/authority-chain audit. No historical entailment is claimed and no old evidence is repaired.

## Transition recomputation

'''
    for k,v in fields.items():
        text+='- '+k+'='+v+'\n'
    text+='''
The immediate source cut remains GENERATION_LEDGER.TOMBSTONED → NEW_GENERATION with checked previous+1 high-water and durable prior tombstone. The supplied semantic PRE refers to source-generation state provenance/domain; it does not restore usable source authority in TOMBSTONED or assert live source private material. POST requires target qualification rather than proving it. This preserves the source boundary rather than broadening T8 into a retirement/bootstrap/activation compound.

Source authority alone cannot establish target authority. Material equality/change and principal equality/change do not independently establish a qualified target grant. Conditional allowed material/identity continuity requires separate authorization and qualification; the designation supplies neither an exception to existing fresh-key/endpoint renewal nor a successful qualification witness. Approved full-cohort restart still requires its independently sourced fresh qualified subjects, six private keys and POSTMASTER endpoint renewal. No global all-previous-credentials revocation proposition or numeric UID delta is derived from this designation. Full external I13 remains mandatory.

## Denominator reconciliation — no replacement of the canonical universe

The historical21/21/21 report is audited, not trusted as the complete witness universe. A5.2 had already corrected the model: **189 dimension-specific pair comparisons, seven valid ACTIVE replacement closures,350 original negative cases and70 qualification inputs**. The strict21 complete-other-process preservation expectation is noncanonical; the28 earlier failed expectations were invalidated, not approved. C5C does not change that correction or attack350.

All189 dimension rows are rechecked with source hashes/pointers/canonical fact digests.147 prove scoped concurrent independence;42 prove restart/strict-substitution dependence. The42 false independence predicates are confirmed dependency relationships, not failed canonical obligations and not old tests relabeled PASS. A derived21-pair static non-collapse view is supported across the seven independent dimensions. The21 revocation-unit comparisons remain proven static contracts, without any unaffected-service-availability guarantee. These views overlap the189 rows and are not additive denominators.

Seven valid restart closures and70 qualification input lineages remain proven in their accepted static scopes. They do not prove live qualification or every attack outcome. The full corrected proof matrix contains616 canonical rows:266 PROVEN static contract/lineage propositions, zero DISPROVEN canonical propositions,350 UNKNOWN full negative proof chains.

## Complete negative witness audit

Every original350 case ID is audited independently against its prior payload and original-negative-witness audit.133 retain structured schema/comparison-formula candidates;217 explicitly remain generic with exact field/effect mapping pending. None is promoted from a STATIC_WITNESS_COMPLETE flag alone.

All350 lack a case-specific typed static baseline, exact instantiated attack mutation and reproducible calculated full decision proof in the existing case payload. Static symbolic case values/derivations could supply such evidence; live production measurements are not being demanded to prove static contracts. No attack is materialized or evaluated here. Each row records the specific artifact structure, retained partial evidence, missing chain and T8 relevance. For POSTMASTER/credential_inheritance, the transition and bounded normative no-transfer rule are now fixed, but its exact witness mapping/mutation/calculation remains unprovided. The new authority therefore removes event ambiguity and leaves a distinct witness gap; it does not discharge that gap by generation succession alone.

## Adversarial tests and consistency

CM1–CM8 are recorded as conditional/logical falsification attempts, not eight proven compliant paths. Same old private keys or unchanged qualified birth subjects in approved full-cohort restart are not authorized merely by conditional allowed continuity. Stable logical slots/numeric UIDs remain different from qualified process subjects. New material, substitution or source revocation without target qualification cannot establish target authority. Conversely, a general replacement-free target grant is not invented. I13 remains independently mandatory even when authority is qualified. Exact lifecycle independence/interleaving stays UNKNOWN where not sourced; chronology is not authority.

No countermodel family is rejected solely because T8 is designated. Specific bypass interpretations remain barred or unestablished by independent frozen rules. The source-cut/provenance distinction, qualification prerequisite and conditional permission avoid contradiction without modifying any historical artifact.

## Result and retained limitations

TRANSITION_RESOLVED=YES applies only to the prospective identity and supplied bounded continuity rule. N1 substitution remains OPEN:350 required full negative chains UNKNOWN, decisions12=11closed+1open. V2 proof FAIL/status BLOCKED. Context binding, internal scope, atomic boundary and canonical internal universe/total remain unresolved. No particular separately frozen architectural decision is invented as a necessary prerequisite for observing the missing witness artifacts; Outcome B applies, rather than an unproven dependency Outcome D.

Candidate108/ambiguity105/attack350 unchanged; zero attacks materialized/evaluated. Independent reviews concern the adoption and this fail-closed authority-chain audit; agreement creates no authority. No implementation/build/native runtime/SQL/database/V043/B02/git add/commit/push. Only new C5C evidence is written.

NEXT_GATE=BOUNDED_STATIC_WITNESS_AUTHORITY_AND_ARTIFACT_COMPLETION_NO_EXECUTION. NEXT_EXECUTED=false. STOP after C5C.
'''
    (E/'PACKAGE-0090-B01-v2-native-static-closure-r5n2a5-3c5c.md').write_text(text,encoding='utf-8')


def validate():
    w=rd(HERE/'full-witness-matrix.json')
    assert len(w['dimension_relations'])==189 and len(w['valid_ACTIVE_replacement_closures'])==7
    assert len(w['qualification_inputs'])==70 and len(w['canonical_negative_witnesses'])==350
    assert len(w['derived_noncollapse_pair_view'])==21
    assert len({r['id'] for r in w['canonical_negative_witnesses']})==350
    assert all(r['status']=='UNKNOWN' and not r['static_case_evaluated_this_gate'] for r in w['canonical_negative_witnesses'])
    assert sum(r['legacy_STATIC_WITNESS_COMPLETE_flag'] for r in w['canonical_negative_witnesses'])==133
    pre=rd(HERE/'preflight.json');assert all(sha(ROOT/k)==v for k,v in pre['preexisting_sha256'].items())
    assert subprocess.check_output(['git','diff','--name-only'],cwd=ROOT)==b''
    assert subprocess.check_output(['git','diff','--cached','--name-only'],cwd=ROOT)==b''
    return len(pre['preexisting_sha256'])


if __name__=='__main__':
    assert ROOT==pathlib.Path('C:/Projects/flooow-genesis-git')
    fields=adoption()
    provenance()
    transition(fields)
    denominator()
    witnesses()
    countermodels()
    result()
    report(fields)
    print('C5C_PRIMARY_OUTCOME=B; TRANSITION_RESOLVED=YES; FULL_NEGATIVE_WITNESSES_UNKNOWN=350; PRESERVED_HASHES='+str(validate()))
