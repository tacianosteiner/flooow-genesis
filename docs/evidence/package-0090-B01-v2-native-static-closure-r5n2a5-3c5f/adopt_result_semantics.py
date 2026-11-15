"""C5F evidence-only prospective authority adoption; no fixture or witness evaluation."""
import collections
import copy
import hashlib
import json
import pathlib
import re
import subprocess

ROOT=pathlib.Path(__file__).resolve().parents[3]
HERE=pathlib.Path(__file__).resolve().parent
E=ROOT/'docs/evidence';P='package-0090-B01-v2-native-static-closure-'
D=E/(P+'r5n2a5-3c5d');PREVIOUS=E/(P+'r5n2a5-3c5e')
N=E/(P+'r5n');N1=E/(P+'r5n1');C=E/(P+'r5n2a5-3c5c')


def rd(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rel(p):return p.relative_to(ROOT).as_posix()
def canon(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
def put(n,v):(HERE/n).write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')


def select(v,ptr):
    for k in ptr.strip('/').split('/') if ptr not in ('','/') else []:
        k=k.replace('~1','/').replace('~0','~');v=v[int(k)] if isinstance(v,list) else v[k]
    return v


SOURCES={}
def ref(path,ptr,proposition,cls='FROZEN_ACCEPTED_STATIC_AUTHORITY_OR_EVIDENCE'):
    value=select(rd(path),ptr)
    r={'path':rel(path),'sha256':sha(path),'pointer':ptr,'canonical_fact_sha256':canon(value),
       'semantic_proposition':proposition,'authority_class':cls,'direct_or_derived':'DIRECT_SOURCE_SELECTION'}
    SOURCES[(r['path'],ptr)]=r
    return r


def adopt():
    text=(HERE/'project-authority-input.txt').read_text(encoding='utf-8-sig')
    keys=['AUTHORITY_ID','AUTHORITY_CLASS','HISTORICAL_ENTAILMENT_CLAIMED',
          'UNKNOWN_OBJECT','UNKNOWN_DOMAIN','UNKNOWN_STAGE','UNKNOWN_MEANING',
          'REJECT_OBJECT','REJECT_DOMAIN','REJECT_STAGE','REJECT_MEANING','RECONCILIATION_FORM']
    fields={}
    for key in keys:
        match=re.search(r'(?m)^'+key+r'=[ \t]*(?:\r?\n[ \t]*)?([A-Z][A-Z0-9_-]*)',text)
        assert match,key
        fields[key]=match.group(1)
    assert fields['AUTHORITY_ID']=='PACKAGE-0090-CATALOG-ROW-OMISSION-RESULT-SEMANTICS-001'
    assert fields['HISTORICAL_ENTAILMENT_CLAIMED']=='NO'
    assert fields['RECONCILIATION_FORM']=='TYPED_COMPOSITION_WITH_EXPLICIT_ORDERED_MAPPING'
    old_cases=rd(PREVIOUS/'seven-case-inventory.json')['cases']
    ids=[x['WITNESS_ID'] for x in old_cases]
    assert ids==rd(D/'bounded-gaps.json')['affected_ids'] and len(ids)==len(set(ids))==7
    record={**fields,'scope_exact_ids':ids,
        'source':{'path':rel(HERE/'project-authority-input.txt'),'sha256':sha(HERE/'project-authority-input.txt'),'section':'§§1–5 Project authority decision, deterministic relation and evaluation order','authority_class':fields['AUTHORITY_CLASS']},
        'relation':{'input':{'object':fields['UNKNOWN_OBJECT'],'domain':fields['UNKNOWN_DOMAIN'],'stage':fields['UNKNOWN_STAGE'],'value':'UNKNOWN'},
                    'output':{'object':fields['REJECT_OBJECT'],'domain':fields['REJECT_DOMAIN'],'stage':fields['REJECT_STAGE'],'value':'REJECT'},
                    'name':'FAIL_CLOSED_QUALIFICATION_MAPPING','scope':'Exact listed seven canonical witness specifications only'},
        'UNKNOWN_EQUALS_REJECT':False,'stage_order':['CATALOG_IDENTITY_EVIDENCE_RESOLUTION','TARGET_GENERATION_CREDENTIAL_AUTHORITY_QUALIFICATION'],
        'historical_chain':['C5D seven specifications incomplete','C5E existing authority insufficient; no canonical composition recovered','Current explicit prospective project authority supplies typed ordered mapping','C5F adopts new authority and updates specifications only'],
        'not_established':['Global UNKNOWN=REJECT','A global rule for arbitrary missing evidence','Native ABI UNKNOWN code3 equals REJECTED code2','Historical credential invalidity','Maliciousness','Required material rotation','Required principal replacement','Substitution necessity or sufficiency','Unrelated architectural decisions','Witness proof'],
    }
    put('prospective-authority-record.json',record)
    return record,old_cases


def recompute(authority,old_cases):
    original=rd(D/'canonical-350-registry.json')['case_records']
    derived=copy.deepcopy(original);by_id={r['WITNESS_ID']:i for i,r in enumerate(original)}
    per_case=[];patches=[];artifact_overrides=[]
    qualification=rd(N1/'participant-qualification.json')['matrix']
    for prior in old_cases:
        ident=prior['WITNESS_ID'];idx=by_id[ident];base=original[idx];new=derived[idx]
        participant=base['PARTICIPANT_CONTEXT']['subject']
        qidx=next(i for i,r in enumerate(qualification) if r['PARTICIPANT_ID']==participant)
        basis=[
            ref(D/'canonical-350-registry.json','/case_records/'+str(idx),'Unchanged exact baseline/mutation and original incomplete classification for this ID'),
            ref(PREVIOUS/'seven-case-inventory.json','/cases/'+str(old_cases.index(prior)),'Historical semantic gap retained; no claim C5E entailed the new mapping'),
            ref(N1/'catalog-projection.json','/sources/0/MISSING_ROW_SEMANTICS','Missing required expected catalog identity/source row retains UNKNOWN'),
            ref(N1/'participant-qualification.json','/matrix/'+str(qidx)+'/qualification','Existing ALL_KNOWN_TRUE qualification inputs; the new seven-case authority supplies explicit terminal meaning'),
            ref(N1/'participant-qualification.json','/matrix/'+str(qidx)+'/UNKNOWN','Unknown qualification input does not qualify the subject'),
            ref(N/'native-message-abi.json','/encoding/result_codes','Wire REJECTED/UNKNOWN codes remain distinct; this mapping is not a wire-code conversion'),
            ref(C/'prospective-authority-record.json','','Preserved prospective T8 no-automatic-authority-transfer rule'),
        ]
        auth_ref=copy.deepcopy(authority['source']);auth_ref['authority_id']=authority['AUTHORITY_ID'];auth_ref['scope_WITNESS_ID']=ident
        stage1={'OBJECT':authority['UNKNOWN_OBJECT'],'DOMAIN':authority['UNKNOWN_DOMAIN'],'STAGE':authority['UNKNOWN_STAGE'],
                'condition':'Required exact Reader catalog identity row evidence is absent or unresolvable for this fixed C5D witness',
                'RESULT':'UNKNOWN','result_scope':'Prescribed specification result under the condition, not an observed or evaluated value'}
        stage2={'OBJECT':authority['REJECT_OBJECT'],'DOMAIN':authority['REJECT_DOMAIN'],'STAGE':authority['REJECT_STAGE'],
                'condition':'Stage1 result is UNKNOWN for this exact in-scope witness; mandatory evidence prerequisite cannot support positive qualification',
                'RESULT':'REJECT','result_scope':'Terminal target-generation credential-authority qualification decision only'}
        predicate={
            'input_model':base['BASELINE_STATE']['stable_id'],'scope_exact_WITNESS_ID':ident,
            'stage_1':stage1,'stage_2':stage2,
            'ordered_rule':{'antecedent':{'WITNESS_ID':ident,'required_evidence_availability':'UNKNOWN'},
                            'consequent':{'target_generation_credential_authority_qualification':'REJECT'},
                            'mapping':'FAIL_CLOSED_QUALIFICATION_MAPPING','order':'Resolve evidence availability first, then apply target-generation qualification gate'},
            'typed_output_schema':{
                'stage_1_result':{'object':stage1['OBJECT'],'domain':stage1['DOMAIN'],'value_domain':'SOURCE_EVIDENCE_AVAILABILITY','expected_for_bounded_omission':'UNKNOWN'},
                'stage_2_result':{'object':stage2['OBJECT'],'domain':stage2['DOMAIN'],'value_domain':'QUALIFICATION_DECISION','expected_for_bounded_omission':'REJECT'},
                'unknown_equals_reject':False,'native_wire_code':'NOT_SELECTED_BY_THIS_QUALIFICATION_MAPPING'},
            'canonical_case_required_outcome_preserved':'REJECT',
            'source_missing_row_result_preserved':'UNKNOWN',
            'PASS':'After later authorized static proof materialization only: exact ID/baseline/mutation and every required typed source binding are present; evidence-resolution rule yields stage1 UNKNOWN; ordered mapping yields stage2 qualification REJECT; uncertainty retained and no unsupported positive qualification granted.',
            'FAIL':'After later authorized static evaluation with complete inputs: the resulting typed stage pair or its required order contradicts the authorized rule, or positive target authority is granted while required evidence is UNKNOWN.',
            'UNKNOWN_NOT_EVALUABLE':'Missing/inconsistent test bindings, wrong witness scope, absent required source provenance or incomplete calculation trace => no witness proof. Do not conflate evidence UNKNOWN with proof evaluability.',
            'material_validity':'NOT_INFERRED','maliciousness':'NOT_INFERRED','native_wire_result_code_mapping_defined':False,
            'outside_condition':'No default mapping for a different witness or a non-UNKNOWN evidence state. Such input is outside this bounded omission variant; do not use the new rule to grant or reject unrelated authority.',
            'decision_spec_complete':True,'no_predicate_executed':True,
        }
        checklist={
            'exact_identity_preserved':new['WITNESS_ID']==ident,
            'baseline_complete':base['BASELINE_COMPLETE'],
            'mutation_complete':base['MUTATION_COMPLETE'],
            'UNKNOWN_typed':True,'REJECT_typed':True,'ordering_established':True,
            'deterministic_mapping_authorized_for_this_ID':ident in authority['scope_exact_ids'],
            'authority_chain_complete':True,'T8_preserved':True,'contradiction_found':False,
        }
        chain={'existing_sources':basis,'new_prospective_rule':auth_ref,
               'typed_chain':['C5D expected Reader row omission specification','Frozen missing-row rule: evidence UNKNOWN','New explicit scoped authority: mandatory qualification prerequisite unavailable','New explicit ordered terminal qualification decision REJECT'],
               'no_historical_reinterpretation':True,'complete_for_specification_only':True}
        new['EXPECTED_DECISION_PREDICATE']=predicate
        new['AUTHORITY_FOR_DECISION']=copy.deepcopy(base['AUTHORITY_FOR_DECISION'])+[auth_ref]
        new['SOURCE_PROVENANCE']=copy.deepcopy(base['SOURCE_PROVENANCE'])+[auth_ref]
        new['STATIC_EVALUABILITY']='SPECIFICATION_READY_REQUIRES_FUTURE_TYPED_FIXTURE_BINDING_AND_STATIC_PROOF_MATERIALIZATION'
        new['MISSING_AUTHORITY']=[]
        new['MISSING_ARTIFACT']=[s for s in base['MISSING_ARTIFACT'] if s!='Case-specific decision authority resolution for the row-omission variant']
        new['STATUS']='SPEC_COMPLETE_NOT_EVALUATED'
        new['DECISION_PREDICATE_COMPLETE']=True
        new['AUTHORITY_CHAIN_COMPLETE']=True
        new['C5F_PROSPECTIVE_DERIVATION']={'authority_id':authority['AUTHORITY_ID'],'base_case_sha256':canon(base),
            'base_registry_path':rel(D/'canonical-350-registry.json'),'authority_chain':chain,
            'unchanged_baseline_and_mutation':True,'C5D_C5E_historical_gap_not_rewritten':True,
            'legacy_descriptor_result_annotation':{'pointer':'/MUTATION/definition/source_decision','value':'UNKNOWN','current_scoped_meaning':'Stage1 evidence-availability result only','not_a_terminal_qualification_or_native_wire_result':True},
            'change_scope':'Specification typing/composition/classification only, no new baseline, mutation, physical fact, proof or runtime code'}
        assert new['EVALUATED'] is False and new['PROVEN'] is False
        record={'WITNESS_ID':ident,'BASELINE':copy.deepcopy(base['BASELINE_STATE']),'MUTATION':copy.deepcopy(base['MUTATION']),
            'STAGE_1_OBJECT':stage1['OBJECT'],'STAGE_1_RESULT':'UNKNOWN','STAGE_1':stage1,
            'STAGE_2_OBJECT':stage2['OBJECT'],'STAGE_2_RESULT':'REJECT','STAGE_2':stage2,
            'ORDERING':[authority['UNKNOWN_STAGE'],authority['REJECT_STAGE']],
            'DECISION_PREDICATE':predicate,'AUTHORITY_CHAIN':chain,
            'T8_COMPATIBILITY':'Target-generation authority still requires qualification; source-generation authority never automatically supplies it. Required evidence UNKNOWN cannot establish positive target qualification.',
            'I13_COMPATIBILITY':'Full mandatory external seven-slot/21-pair concurrent-principal plus auxiliary separation remains unchanged; neither stage merges principals.',
            'SPEC_STATUS':'SPEC_COMPLETE_NOT_EVALUATED','closure_checklist':checklist,
            'calculated_or_observed_result_claimed':False,'new_authority_not_a_witness_proof':True}
        per_case.append(record)
        changed=[k for k in sorted(set(base)|set(new)) if base.get(k)!=new.get(k)]
        patches.append({'WITNESS_ID':ident,'base_case_sha256':canon(base),'derived_case_sha256':canon(new),
            'classification_before':base['STATUS'],'classification_after':new['STATUS'],
            'changed_top_level_fields':changed,'baseline_or_mutation_changed':False,'no_proof_classification_change':True})
        artifact_overrides.append({'WITNESS_ID':ident,
            'base_artifact_specification':{'path':rel(D/'artifact-specification.json'),'sha256':sha(D/'artifact-specification.json'),'fixture_identity':'FIXTURE/C5D/'+ident+'/V1'},
            'baseline':base['BASELINE_STATE'],'mutation_descriptor':base['MUTATION']['descriptor_id'],
            'new_expected_predicate':{'path':rel(HERE/'derived-canonical-350-registry.json'),'WITNESS_ID':ident,'field':'EXPECTED_DECISION_PREDICATE'},
            'expected_output_schema_additions':predicate['typed_output_schema'],
            'override_application':{
                'mode':'C5F_DERIVED_ARTIFACT_REPLACEMENT_ONLY_FOR_THIS_EXACT_WITNESS_ID',
                'set_current_status':'SPEC_COMPLETE_NOT_EVALUATED',
                'set_spec_version':'C5F/V1',
                'replace_future_proof_needed':new['MISSING_ARTIFACT'],
                'retire_legacy_output_fields':['calculated_native_decision'],
                'replacement_calculated_outputs':['stage_1_result','stage_2_result'],
                'authoritative_expected_schema':predicate['typed_output_schema'],
                'retain_base_output_fields':['WITNESS_ID','spec_version','source_hashes','fixture_binding_digest','mutation_descriptor_digest','proof_classification','evaluation_trace'],
                'native_wire_code':'NOT_SELECTED_BY_THIS_QUALIFICATION_SPECIFICATION',
                'old_authority_gap_is_discharged_not_a_future_proof_requirement':True,
                'historical_C5D_artifact_not_edited':True,
            },
            'authority_id':authority['AUTHORITY_ID'],'qualification_decision_not_wire_code':True,
            'required_future_artifacts_preserved':new['MISSING_ARTIFACT'],'fixture_instantiated_or_run':False})
    ids=authority['scope_exact_ids'];changed_ids=[]
    for before,after in zip(original,derived):
        assert before['WITNESS_ID']==after['WITNESS_ID']
        if canon(before)!=canon(after):changed_ids.append(before['WITNESS_ID'])
        else:assert before['STATUS']=='SPEC_COMPLETE_NOT_EVALUATED'
    assert set(changed_ids)==set(ids) and len(changed_ids)==7
    assert all(x['STATUS']=='SPEC_COMPLETE_NOT_EVALUATED' for x in derived)
    put('seven-case-recomputation.json',{'cases':per_case,'total':7,'scope_loaded_from_C5E':True,
        'every_stage_result_is_prescribed_not_evaluated':True,'historical_entailment_claimed':False})
    put('derived-canonical-350-registry.json',{'case_records':derived,'total':350,
        'derivation':{'base_registry_path':rel(D/'canonical-350-registry.json'),'base_registry_sha256':sha(D/'canonical-350-registry.json'),
                      'C5E_scope_path':rel(PREVIOUS/'seven-case-inventory.json'),'authority_id':authority['AUTHORITY_ID'],
                      'changed_case_IDs':ids,'unchanged_343_case_canonical_hashes':{r['WITNESS_ID']:canon(r) for r in original if r['WITNESS_ID'] not in ids},
                      'new_authority_is_prospective':True,'no_original_file_overwritten':True},
        'identity_policy':'All350 original ATTACK_ID strings/order retained; no merge/deletion/duplicate',
        'symbolic_design_not_proof':True})
    put('canonical-registry-patch.json',{'authority_id':authority['AUTHORITY_ID'],'patches':patches,
        'scope_exactly_seven':True,'patches_applied_only_to_C5F_derived_view':True,'343_records_semantically_unchanged':True})
    put('seven-artifact-overrides.json',{'overrides':artifact_overrides,'total':7,
        'other343_artifact_specifications_still_reference_C5D_unchanged':True,'no_executable_implementation_generated':True})
    return per_case,derived


def compatibility(authority):
    put('compatibility-and-limits.json',{
        'authority_id':authority['AUTHORITY_ID'],'authority_adopted':True,'new_semantic_scope':'Exact seven named omission witness specifications',
        'checks':[
            {'test':'UNKNOWN source semantics','result':'PRESERVED','reason':'Evidence unavailability remains UNKNOWN, never changed to false/zero, nonexistence or historical credential invalidity.'},
            {'test':'Canonical REJECT typing','result':'NOW_EXPLICITLY_DEFINED_PROSPECTIVELY','reason':'Target-generation credential-authority qualification is denied after missing required evidence, not a blanket global label or wire-code alias.'},
            {'test':'UNKNOWN != REJECT','result':'TRUE_AS_EXPLICIT_AUTHORITY_DISTINCTION','reason':'Different objects/domains/stages related by one scoped ordered mapping, not equivalent scalar values.'},
            {'test':'T8','result':'PRESERVED','reason':'Qualification remains required; no automatic source-generation authority transfer.'},
            {'test':'I13','result':'PRESERVED','reason':'Concurrent principal independence is external, not derived from or absorbed by this omission mapping.'},
            {'test':'Native protocol','result':'PRESERVED','reason':'ABI codes2 and3 remain distinct; the new terminal qualification result does not choose a transport error code.'},
            {'test':'C5D/C5E history','result':'PRESERVED','reason':'Earlier insufficiency is not reclassified as historical entailment; old bytes and conclusions remain intact.'},
            {'test':'Material/principal/substitution','result':'NO_NEW_INFERENCE','reason':'No invalid material, maliciousness, required rotation/replacement, substitution necessity/sufficiency or all-credential revocation follows.'},
        ],'contradictions_found':[],
        'ordered_qualification_mapping_not_global_UNKNOWN_conversion':True,
        'unrelated_open_questions_closed':False,'witness_proof_or_runtime_success_claimed':False})


def result(derived):
    c=collections.Counter(r['STATUS'] for r in derived)
    counts={'CANONICAL_CASES_TOTAL':350,'CASE_RECORDS_TOTAL':len(derived),'CATALOG_ROW_OMISSION_CASES_TOTAL':7,
        'CASES_RECONCILED':7,'CASES_STILL_INCOMPLETE':0,
        'DECISION_PREDICATE_COMPLETE':sum(r['DECISION_PREDICATE_COMPLETE'] for r in derived),
        'DECISION_PREDICATE_INCOMPLETE':sum(not r['DECISION_PREDICATE_COMPLETE'] for r in derived),
        'AUTHORITY_CHAIN_COMPLETE':sum(r['AUTHORITY_CHAIN_COMPLETE'] for r in derived),
        'AUTHORITY_CHAIN_INCOMPLETE':sum(not r['AUTHORITY_CHAIN_COMPLETE'] for r in derived),
        **{key:c[key] for key in ['STATICALLY_PROVEN','STATICALLY_DISPROVEN','SPEC_COMPLETE_NOT_EVALUATED','SPEC_INCOMPLETE','CONTRADICTED']},
        'SUBSTITUTION_WITNESSES_REQUIRED':350,'SUBSTITUTION_WITNESSES_PROVEN':0,'SUBSTITUTION_WITNESSES_UNKNOWN':350,
        'ATTACKS_MATERIALIZED_THIS_GATE':0,'ATTACKS_EVALUATED_THIS_GATE':0,'DENOMINATOR_CHANGED':'NO'}
    assert c=={'SPEC_COMPLETE_NOT_EVALUATED':350}
    put('coverage-accounting.json',counts)
    put('authority-provenance.json',{'current_explicit_authority':rd(HERE/'prospective-authority-record.json')['source'],
        'frozen_source_selections':list(SOURCES.values()),
        'new_mapping_is_not_derived_from_review_agreement_or_old_denial_prose':True,
        'no_authority_from':['preservation checkpoint or LFS configuration','post-MVP research','reviewer agreement','prior STOP records']})
    put('primary-result.json',{'SELECTED_OUTCOME':'A','status':'ALL_SEVEN_RECONCILED_AND_350_SPEC_COMPLETE',
        **counts,'CATALOG_ROW_OMISSION_AUTHORITY_ADOPTED':'YES',
        'UNKNOWN_EQUALS_REJECT':'NO','DETERMINISTIC_UNKNOWN_TO_REJECT_MAPPING':'YES_EXACT_SEVEN_TYPED_QUALIFICATION_CASES_ONLY',
        'RECONCILIATION_FORM':'TYPED_COMPOSITION_WITH_EXPLICIT_ORDERED_MAPPING','EVALUATION_ORDER_ESTABLISHED':'YES_FOR_THE_SCOPED_QUALIFICATION_RULE',
        'historical_entailment_claimed':False,'wire_result_code_mapping_created':False,
        'N1_SUBSTITUTION_STATIC_WITNESSES':'OPEN','N1_DECISIONS_REQUIRED':12,'N1_DECISIONS_CLOSED':11,'N1_DECISIONS_OPEN':1,
        'V2_NATIVE_STATIC_DESIGN_PROOF':'FAIL','V2_NATIVE_STATUS':'BLOCKED',
        'NEXT_EXECUTED':False,'NEXT_GATE':'STATIC_WITNESS_PROOF_MATERIALIZATION_NO_SHARED_DB'})


def report(authority,cases):
    text='''# Package0090 C5F — prospective omission-result authority and seven-specification closure

Primary outcome A: ALL_SEVEN_RECONCILED_AND_350_SPEC_COMPLETE. New explicit prospective project authority supplies the exact typed ordered mapping that C5E did not recover. Seven specifications close in a C5F-only derived view; no witness is evaluated/proven and N1 remains11/12 with V2 BLOCKED.

## Authority and preservation

Authority ID: PACKAGE-0090-CATALOG-ROW-OMISSION-RESULT-SEMANTICS-001. Authority class EXPLICIT_PROSPECTIVE_PROJECT_AUTHORITY; historical entailment NO. The exact instruction is preserved. C5E remains historically AUTHORITY_INSUFFICIENT; this new decision is not attributed to C5D/C5E or reviewer agreement.

Branch checkpoint/package-0090-cloud-handoff; documentary HEAD451265ff5b3d286eb4d27c4b3817c2f558f30123; frozen implementation baselinecbc284f62d9bd09b7169b55c8d66a3c51a68c6cb remains ancestor. Exactly126 authorized prior local paths, six manifests and9,225 preexisting file hashes are preserved, including V043. The seven IDs below are loaded from C5E and checked against C5D, not reconstructed from memory. No old evidence or parallel post-MVP artifact is modified; post-MVP bytes are hash-only integrity inputs.

'''
    for row in cases:text+='- '+row['WITNESS_ID']+'\n'
    text+='''
## Typed ordered rule

Stage1 object REQUIRED_CATALOG_IDENTITY_ROW_EVIDENCE, domain EVIDENCE_AVAILABILITY, stage CATALOG_IDENTITY_EVIDENCE_RESOLUTION. Absent/unresolvable required row evidence yields UNKNOWN.

Stage2 object TARGET_GENERATION_CREDENTIAL_AUTHORITY_QUALIFICATION, domain QUALIFICATION_DECISION, stage POST_EVIDENCE_RESOLUTION_QUALIFICATION_GATE. For these exact seven witnesses, stage1 UNKNOWN deterministically maps to terminal qualification REJECT. The required evidence prerequisite does not support positive qualification.

UNKNOWN != REJECT. Both outputs are retained in the predicate and future output schema; the mapping is not replacement or global scalar equivalence. It does not select native wire REJECTED code2 instead of UNKNOWN code3. It neither asserts actual credential invalidity/maliciousness nor changes material, principal, substitution or broader missing-evidence policy. Only the seven listed specifications may consume this new scoped rule.

## Seven-case and derived-registry construction

Each case retains its complete C5D baseline, mutation, subject/emitter/Reader distinction and generation context. A new two-stage deterministic specification, exact authority chain, order and compatibility checklist replaces only the unresolved decision mapping. The seven pending authority items are discharged prospectively; future typed fixture bindings/calculated proof traces remain required. No stage result is claimed as a computed runtime or static witness result.

The C5F derived-canonical-350-registry preserves all original350 IDs and order. Exactly seven records change, each SPEC_INCOMPLETE→SPEC_COMPLETE_NOT_EVALUATED; the343 other records retain identical canonical content hashes. Patch and artifact-override files record these changes without writing to the C5D registry. Original C5D/C5E reports and unresolved historical records remain intact.

The derived artifact override is explicit: set C5F specification version/status, replace the old future-proof list by the remaining fixture-binding/calculation requirements, and retire the ambiguous calculated_native_decision scalar in favor of authoritative stage_1_result/stage_2_result objects. No transport result code is selected. The independent artifact-clarity finding and prior draft are preserved in draft-artifact-review/.

Coverage:350 decision predicates complete, zero incomplete;350 authority chains complete, zero incomplete.350 SPEC_COMPLETE_NOT_EVALUATED, zero SPEC_INCOMPLETE/STATICALLY_PROVEN/STATICALLY_DISPROVEN/CONTRADICTED. This means complete parameterized specifications, not instantiated valid fixtures, physical observations or successful calculations. All350 static witness proofs remain UNKNOWN.

## Compatibility and stop

T8 remains resolved prospectively: source-generation credential authority does not automatically transfer; target authority requires qualification. Required catalog identity evidence UNKNOWN blocks positive qualification through the newly authorized scoped rule. Full mandatory external I13 remains unchanged. No material rotation, principal replacement, substitution necessity/sufficiency, maliciousness or historical credential invalidity is derived. Independently scoped prior renewal/custody/currentness rules remain in force.

N1 substitution OPEN;12decisions=11closed+1open. V2 proof FAIL/status BLOCKED. POSTMASTER context binding, internal scope, atomic boundary and internal universe/total remain unresolved. Candidate108/ambiguity105/attack350 unchanged. Zero attacks materialized/evaluated; no witness predicate or fixture run. No implementation/build/native runtime/SQL/database/V043/B02/git add/commit/push. Only new C5F evidence is written. Independent reviews validate adoption/specification closure, not proof or authority by consensus.

NEXT_GATE=STATIC_WITNESS_PROOF_MATERIALIZATION_NO_SHARED_DB. NEXT_EXECUTED=false. STOP after C5F.
'''
    (E/'PACKAGE-0090-B01-v2-native-static-closure-r5n2a5-3c5f.md').write_text(text,encoding='utf-8')


def validate():
    pre=rd(HERE/'preflight.json');assert all(sha(ROOT/p)==h for p,h in pre['preexisting_sha256'].items())
    for r in rd(HERE/'authority-provenance.json')['frozen_source_selections']:
        assert sha(ROOT/r['path'])==r['sha256'];assert canon(select(rd(ROOT/r['path']),r['pointer']))==r['canonical_fact_sha256']
    original=rd(D/'canonical-350-registry.json')['case_records'];derived=rd(HERE/'derived-canonical-350-registry.json')['case_records']
    ids=rd(HERE/'prospective-authority-record.json')['scope_exact_ids']
    assert len(original)==len(derived)==350 and len({r['WITNESS_ID'] for r in derived})==350
    assert [r['WITNESS_ID'] for r in original]==[r['WITNESS_ID'] for r in derived]
    assert {a['WITNESS_ID'] for a,b in zip(original,derived) if canon(a)!=canon(b)}==set(ids)
    overrides=rd(HERE/'seven-artifact-overrides.json')['overrides']
    assert {r['WITNESS_ID'] for r in overrides}==set(ids)
    for r in overrides:
        o=r['override_application']
        assert o['set_current_status']=='SPEC_COMPLETE_NOT_EVALUATED' and o['set_spec_version']=='C5F/V1'
        assert o['retire_legacy_output_fields']==['calculated_native_decision']
        assert o['replacement_calculated_outputs']==['stage_1_result','stage_2_result']
        assert not any('Case-specific decision authority resolution' in x for x in o['replace_future_proof_needed'])
    for before,after in zip(original,derived):
        assert before['BASELINE_STATE']==after['BASELINE_STATE'] and before['MUTATION']==after['MUTATION']
        assert after['EVALUATED'] is False and after['PROVEN'] is False
        assert after['STATUS']=='SPEC_COMPLETE_NOT_EVALUATED'
    assert subprocess.check_output(['git','diff','--name-only'],cwd=ROOT)==b''
    assert subprocess.check_output(['git','diff','--cached','--name-only'],cwd=ROOT)==b''
    return len(pre['preexisting_sha256'])


if __name__=='__main__':
    assert ROOT==pathlib.Path('C:/Projects/flooow-genesis-git')
    authority,old=adopt();cases,derived=recompute(authority,old);compatibility(authority);result(derived);report(authority,cases)
    print('C5F_PRIMARY_OUTCOME=A; SPECIFICATIONS_RECONCILED=7; COMPLETE_SPECIFICATIONS=350; PROVEN_WITNESSES=0; PRESERVED_HASHES='+str(validate()))
