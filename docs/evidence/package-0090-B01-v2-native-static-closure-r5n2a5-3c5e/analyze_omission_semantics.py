"""C5E bounded authority/type analysis. Does not instantiate or evaluate witnesses."""
import hashlib
import json
import pathlib
import subprocess

ROOT=pathlib.Path(__file__).resolve().parents[3]
HERE=pathlib.Path(__file__).resolve().parent
E=ROOT/'docs/evidence';P='package-0090-B01-v2-native-static-closure-'
N=E/(P+'r5n');N1=E/(P+'r5n1');D=E/(P+'r5n2a5-3c5d')
G1=E/(P+'r5n2a4-1d')/'G1-producer-execution-plan.json'


def rd(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rel(p):return p.relative_to(ROOT).as_posix()
def canon(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
def put(name,v):(HERE/name).write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')


def select(value,ptr):
    for k in ptr.strip('/').split('/') if ptr not in ('','/') else []:
        k=k.replace('~1','/').replace('~0','~');value=value[int(k)] if isinstance(value,list) else value[k]
    return value


AUTH={}
def ref(ident,path,ptr,proposition,authority='FROZEN_ACCEPTED_STATIC_CONTRACT',derived=False):
    value=select(rd(path),ptr)
    row={'id':ident,'SOURCE_PATH':rel(path),'sha256':sha(path),'SECTION_OR_IDENTIFIER':ptr,
        'canonical_fact_sha256':canon(value),'exact_fact':value,'AUTHORITY_CLASS':authority,
        'NORMATIVE_PROPOSITION':proposition,'direct_or_derived':'DERIVED_C5E_SCOPE_BINDING' if derived else 'DIRECT_SOURCE_SELECTION'}
    AUTH[ident]=row
    return ident


def authority_inventory():
    ref('U_ROW',N1/'catalog-projection.json','/sources/0/MISSING_ROW_SEMANTICS',
        'Expected identity/source row missing => UNKNOWN; collection absence is evidence only after complete verified snapshot, never query failure.')
    ref('U_SOURCE',N1/'catalog-projection.json','/sources/0',
        'Full pg_roles projected fields, natural key oid, source identity/snapshot rules; no expected missing identity is silently resolved to false/zero.')
    predicates=rd(N1/'catalog-security-predicates.json')['predicates']
    for name,ident in [('IS_EXPECTED_ROLE','U_ROLE'),('ROLE_ROSTER_EXACT','U_ROSTER'),('SNAPSHOT_COHERENT','U_SNAPSHOT'),('NATIVE_QUALIFIED','U_NATIVE')]:
        i=next(i for i,x in enumerate(predicates) if x['id']==name)
        ref(ident,N1/'catalog-security-predicates.json','/predicates/'+str(i),
            'Explicit predicate expression with truth_domain TRUE/FALSE/UNKNOWN and UNKNOWN -> not qualified; no false/zero inference.')
    ref('U_FAILCLOSED',N1/'substitution-matrix.json','/UNKNOWN_fails_closed','UNKNOWN denies unsupported positive authority; this boolean is not a result-code equivalence.')
    ref('U_NOT_ALL_REJECT_PROVEN',N1/'substitution-matrix.json','/not_all_coverage_rows_are_proven_rejection','Coverage rows are not automatically proven rejection witnesses.')
    ref('G_S06',G1,'/steps/5','S06 joins exact immutable row keys and frames typed data; duplicate/missing identity rejects; depends on S01-S05. Its prose denial is not an explicit canonical required_outcome type equation.')
    ref('G_S07',G1,'/steps/6','S07 consumes S06 and emits three-valued predicate output; missing evidence UNKNOWN, reject qualification preserving uncertainty.')
    ref('G_S08',G1,'/steps/7','S08 consumes S06/S07, evaluates remaining predicates and rejects qualification on UNKNOWN, preserving uncertainty.')
    ref('G_ORDER',E/(P+'r5n2a4-1b')/'predicate-order-proof.json','/complete_order','Accepted producer step order S01..S08, not a proven order relative to the generic case REJECT label.')
    ref('WIRE_ENUM',N/'native-message-abi.json','/encoding/result_codes','Native result codes distinguish REJECTED=2 and UNKNOWN=3. Neither is automatically the meaning of canonical text REJECT.')
    ref('WIRE_ERROR',N/'native-message-abi.json','/error_encoding','REJECTED and UNKNOWN share a fixed error schema but retain distinct code selection; no missing-catalog-row-specific mapping is defined.')
    ref('WIRE_RESULT',N/'native-message-abi.json','/result_record_rule','Error record selection follows result_code; errors never enter observed/published health states. No error/denial equivalence with every canonical case label follows.')
    ref('I13',E/(P+'r5n2a5-3c1')/'i13-reconstruction.json','','Full mandatory external concurrent-principal invariant, independently preserved.')
    ref('T8',E/(P+'r5n2a5-3c5c')/'prospective-authority-record.json','','Explicit prospective T8 bounded authority no-transfer rule is unchanged.','EXPLICIT_PROSPECTIVE_PROJECT_AUTHORITY_RECORDED')
    ref('C5D_GAPS',D/'bounded-gaps.json','','Exact seven original gap identities and unresolved decision mapping.','FROZEN_PREDECESSOR_EVIDENCE')


def case_analysis():
    # IDs are loaded from predecessor evidence, never reconstructed from suffix/roster.
    ids=rd(D/'bounded-gaps.json')['affected_ids']
    reg=rd(D/'canonical-350-registry.json')['case_records'];by_id={x['WITNESS_ID']:x for x in reg}
    n1=rd(N1/'substitution-matrix.json')['new_cases'];qualification=rd(N1/'participant-qualification.json')['matrix']
    rows=[]
    for i,ident in enumerate(ids):
        old=by_id[ident];participant=old['PARTICIPANT_CONTEXT']['subject']
        idx=next(j for j,x in enumerate(n1) if x['id']==ident)
        qidx=next(j for j,x in enumerate(qualification) if x['PARTICIPANT_ID']==participant)
        reject=ref('R_CASE_'+str(i),N1/'substitution-matrix.json','/new_cases/'+str(idx),
            'This exact participant/catalog_row_omission canonical case requires literal REJECT and the generic all-known catalog/IO predicate; it does not define the result target/algebra/stage.')
        q=ref('Q_CASE_'+str(i),N1/'participant-qualification.json','/matrix/'+str(qidx),
            'This subject qualification is ALL_KNOWN_TRUE of ten named inputs. UNKNOWN -> NOT_QUALIFIED. This does not equate NOT_QUALIFIED with the canonical literal REJECT.')
        dref=ref('D_CASE_'+str(i),D/'canonical-350-registry.json','/case_records/'+str(reg.index(old)),
            'C5D exact baseline/mutation/provenance and incomplete classification are preserved.','FROZEN_PREDECESSOR_EVIDENCE')
        unknown_rule={
            'SOURCE_IDS':['U_ROW','U_SOURCE','U_ROLE','U_ROSTER'],
            'EXACT_SEMANTIC_TARGET':'Availability/completeness of the required catalog identity/source-row evidence at the expected Reader row key, not existence of Reader as a principal or a global DB membership fact.',
            'INPUT_DOMAIN':'Protected expected Reader (oid,name) anchor plus typed observed pg_roles row multiset and its source/snapshot completeness provenance.',
            'OUTPUT_DOMAIN':'Explicit UNKNOWN marker for missing expected row; associated catalog predicates use TRUE/FALSE/UNKNOWN. No full independent RESOLVED/UNKNOWN row-result algebra is invented.',
            'EVALUATION_STAGE':'Source-row availability semantics; acquisition/frame validation precedes predicate/publication stages. Exact first triggering step for this omission is not uniquely identified by the projection rule.',
            'PRECONDITIONS':'The expected Reader row is absent in the stipulated candidate collection. This rule covers missing essential identity; verified collection absence is not inferred from query failure.',
            'AUTHORITY_CLASS':'FROZEN_ACCEPTED_STATIC_PROJECTION_AND_PREDICATE_CONTRACT',
        }
        reject_rule={
            'SOURCE_IDS':[reject],
            'EXACT_SEMANTIC_TARGET':'Required expected-outcome marker of this named canonical attack case. The exact rejected object/result variable is NOT_ESTABLISHED: native response code, admission/qualification decision, row admissibility or witness oracle are not selected by the field.',
            'INPUT_DOMAIN':'Named participant attack case plus generic exact-catalog/IO/custody/peer predicate. No original typed omission fixture or stage-specific expected-output type is supplied here.',
            'OUTPUT_DOMAIN':'Literal required_outcome="REJECT". The matrix also uses literal UNKNOWN on other cases, but supplies no typed projection from native error/predicate/qualification results to this literal.',
            'EVALUATION_STAGE':'NOT_ESTABLISHED_FOR_CANONICAL_REJECT_LABEL',
            'PRECONDITIONS':'Case identity/catalog_row_omission and generic predicate are known; its exact canonical response classification for the C5D omission variant is not specified.',
            'AUTHORITY_CLASS':'FROZEN_ACCEPTED_STATIC_REQUIRED_CASE_NOT_ENFORCEMENT_ORACLE_PROOF',
        }
        row={
            'WITNESS_ID':ident,'SOURCE_PROVENANCE':['U_ROW',reject,q,dref],
            'BASELINE':old['BASELINE_STATE'],'MUTATION':old['MUTATION'],
            'IDENTITY_BEFORE':'Protected expected Reader identity (OID_R,NAME_R) and its row r are referenced from the C5D symbolic baseline; this is not a captured runtime identity.',
            'IDENTITY_AFTER':'Expected OID_R/NAME_R and independent own-session identity remain unchanged; stipulated candidate row multiset has no row r. Do not infer Reader does not exist globally.',
            'CATALOG_ROW_EXPECTED':'Exact expected Reader SQL role pg_roles row r (source natural key oid); not a fabricated SQL role for native participant '+participant,
            'CATALOG_ROW_ACTUAL':'After-state specified by DELETE_ONE_EXACT_ROW(r) in the observed model collection. Not a database observation, DDL deletion, query result or evaluated witness.',
            'UNKNOWN_RULE_SOURCE':unknown_rule,
            'UNKNOWN_RULE_EXACT_SEMANTIC_TARGET':unknown_rule['EXACT_SEMANTIC_TARGET'],
            'UNKNOWN_RULE_EVALUATION_STAGE':unknown_rule['EVALUATION_STAGE'],
            'REJECT_RULE_SOURCE':reject_rule,
            'REJECT_RULE_EXACT_SEMANTIC_TARGET':reject_rule['EXACT_SEMANTIC_TARGET'],
            'REJECT_RULE_EVALUATION_STAGE':reject_rule['EVALUATION_STAGE'],
            'SAME_SEMANTIC_VARIABLE':'UNKNOWN_NOT_PROVEN_SAME_OR_DIFFERENT',
            'SAME_EVALUATION_STAGE':'UNKNOWN',
            'ORDERING_RELATION':'Producer acquisition/frame/predicate ordering is known. Canonical REJECT relative to missing-row UNKNOWN is NOT_ESTABLISHED; no short-circuit/refinement inferred.',
            'CONTRADICTION':'NOT_ESTABLISHED_SAME_VARIABLE_STAGE_PRECONDITIONS_NOT_PROVEN',
            'RECONCILIATION':'INSUFFICIENT_AUTHORITY',
            'DECISION_PREDICATE':{
                'source_prescribed_missing_evidence':'UNKNOWN retained; cannot support a positive qualified receipt or native qualification',
                'qualification_guard':'ALL_KNOWN_TRUE source inputs; UNKNOWN -> NOT_QUALIFIED',
                'canonical_required_marker':'REJECT retained exactly, not replaced by UNKNOWN',
                'unresolved_composition':'No authoritative function from these typed/prose source results to this required marker is defined. Do not make a final witness PASS/FAIL oracle.',
                'evaluable_in_C5E':False,'predicate_executed':False,
            },
            'AUTHORITY_CHAIN':{'known':['U_ROW','U_SOURCE',q,'G_S06','G_S07','G_S08','WIRE_ENUM','WIRE_ERROR','WIRE_RESULT',reject],
                'missing':'Exact canonical REJECT governed target/domain/stage and deterministic composition, precedence or precondition distinction for this exact omission mutation.',
                'complete':False},
            'SPEC_STATUS':'SPEC_INCOMPLETE','C5D_classification_changed':False,
        }
        rows.append(row)
    put('seven-case-inventory.json',{'cases':rows,'total':7,'identities_loaded_from':rel(D/'bounded-gaps.json'),'scope_exactly_loaded_ids':True,'all_identity_and_after_state_descriptions_are_unevaluated_specification_data':True})
    return rows,reg


def type_analysis(rows):
    dimensions=[
        ('LOOKUP_RESULT','C5D stipulated candidate match set lacks row r; no lookup is run. Empty candidate evidence does not establish physical DB absence.',['U_SOURCE']),
        ('IDENTITY_RESOLUTION','Independent expected Reader identity remains known; required catalog evidence for its current row is unavailable. Do not say the principal itself becomes nonexistent or unknown in every domain.',['U_ROW','U_ROLE']),
        ('CATALOG_MEMBERSHIP','Truth of actual database role membership is not established by an omitted candidate row; source requires complete verified snapshot evidence and forbids false/zero inference.',['U_ROW','U_SOURCE']),
        ('ROW_PRESENCE','The exact mutation stipulates omission in the candidate collection; this is not a measured result.',['C5D_GAPS']),
        ('ROW_ADMISSIBILITY','Generic canonical REJECT has no independently declared row-admission variable/stage. Do not bind it to row admissibility by wording alone.',['R_CASE_0']),
        ('WITNESS_EVALUABILITY','Specification remains incomplete without a canonical output composition rule; no proof/evaluation result is emitted.',['U_NOT_ALL_REJECT_PROVEN','C5D_GAPS']),
        ('FINAL_DECISION','Unsupported positive qualification/publication is denied. Exact canonical REJECT classification/result algebra remains unresolved.',['U_FAILCLOSED','G_S07','G_S08','R_CASE_0']),
    ]
    put('semantic-type-test.json',{
        'seven_required_dimensions':[{'dimension':k,'finding':v,'basis':s} for k,v,s in dimensions],
        'known_result_domains':[
            {'domain':'Catalog predicate truth','values':['TRUE','FALSE','UNKNOWN'],'basis':['U_ROLE','U_ROSTER','U_SNAPSHOT','U_NATIVE']},
            {'domain':'Qualification consequence','unknown_maps_to':'NOT_QUALIFIED','basis':['Q_CASE_'+str(i) for i in range(7)]},
            {'domain':'Native wire result_code','values':AUTH['WIRE_ENUM']['exact_fact'],'basis':['WIRE_ENUM','WIRE_ERROR','WIRE_RESULT'],'canonical_REJECT_marker_bound_to_wire_REJECTED':False},
            {'domain':'Canonical case required_outcome','known_value':'REJECT','type_and_target':'NOT_ESTABLISHED','basis':['R_CASE_'+str(i) for i in range(7)]},
        ],
        'same_result_algebra':'NOT_ESTABLISHED_FOR_THE_TWO_RULES_AT_ISSUE',
        'different_result_algebra':'ALSO_NOT_PROVEN_FOR_CANONICAL_REJECT; native wire distinctions alone do not type that label',
        'identity_result_algebra_NOT_invented':True,
        'reconciliation_forms_tested':[
            {'form':'TYPED_COMPOSITION','established':False,'reason':'Missing canonical target/domain and composition function; known qualification denial does not supply it.'},
            {'form':'ORDERED_REFINEMENT','established':False,'reason':'No typed UNKNOWN->canonical REJECT or inverse transition is supplied.'},
            {'form':'CONDITIONALLY_DISTINCT','established':False,'reason':'No source binds the generic required marker to an independently distinct omission precondition.'},
            {'form':'EXPLICIT_PRECEDENCE','established':False,'reason':'No governing precedence between these exact rules was recovered.'},
            {'form':'TRUE_CONTRADICTION','established':False,'reason':'Same governed variable, stage and mutually incompatible outputs under identical preconditions are not proven.'},
            {'form':'INSUFFICIENT_AUTHORITY','established':True,'reason':'The link needed to type/reconcile or prove contradiction is missing.'},
        ],'no_seventh_form':True})
    steps=rd(G1)['steps']
    put('evaluation-order-test.json',{
        'source_steps':[{'step':s['PRODUCER_STEP_ID'],'order':s['STEP_ORDER'],'depends_on':s['DEPENDENCIES']} for s in steps],
        'known_constraints':[
            {'proposition':'S06 depends on acquisition/sanitization S01-S05 and rejects duplicate/missing identity in prose.', 'basis':['G_S06']},
            {'proposition':'S07 depends on S06; S08 depends on S06/S07. Three-valued outputs and uncertainty are retained.', 'basis':['G_S07','G_S08','G_ORDER']},
            {'proposition':'Failure/unknown prevents a qualified receipt and unsupported authority result; no fallback role/query.', 'basis':['G_S06','G_S07','G_S08']},
        ],
        'not_established':['Exact first step that fires for this deleted expected pg_roles row','Placement/type of generic canonical required_outcome=REJECT','Whether UNKNOWN is an intermediate code then canonical REJECT terminal','Whether canonical REJECT precedes a final UNKNOWN witness value','Omission-specific wire error reason/result-code mapping'],
        'canonical_composition_order_established':False,'no_short_circuit_inferred':True,
        'prose_rejects_not_ignored':'It establishes denial/abort, but does not explicitly equate that with the untyped canonical marker.'})
    put('fail-closed-test.json',{
        'unknown_denies_positive_authority':True,
        'unknown_is_still_uncertainty':True,
        'canonical_REJECT_equivalence_proven':False,
        'explicit_normative_canonical_REJECT_marker_exists':True,
        'marker_governed_object_and_stage_known':False,
        'basis':['U_FAILCLOSED','U_NOT_ALL_REJECT_PROVEN','G_S06','G_S07','G_S08']+['Q_CASE_'+str(i) for i in range(7)],
        'wire_codes_distinct':AUTH['WIRE_ENUM']['exact_fact'],
        'not_concluded':['UNKNOWN means successful acceptance','All denial is canonical REJECT','REJECT and UNKNOWN are interchangeable protocol codes','A shared error schema makes result codes equal','A vocabulary resemblance proves typed composition'],
    })


def cross_case(rows,reg):
    ids=[x['WITNESS_ID'] for x in rows]
    tests=[]
    for i,r in enumerate(rows):
        sourcecase=AUTH['R_CASE_'+str(i)]['exact_fact']
        q=AUTH['Q_CASE_'+str(i)]['exact_fact']
        tests.append({'WITNESS_ID':r['WITNESS_ID'],'exact_case_id_matches':sourcecase['id']==r['WITNESS_ID'],
            'required_marker':sourcecase['required_outcome'],'unknown_qualification_rule':q['UNKNOWN'],
            'mutation':r['MUTATION'],'baseline_expected_row':'Same exact Reader R pg_roles row under the case-specific participant observation context',
            'actual_subject_context':q['PARTICIPANT_ID'],
            'S03_bridge_substitution':False,'same_source_missing_row_rule':'U_ROW',
            'result':'INSUFFICIENT_AUTHORITY; no per-participant exceptional canonical composition rule found in these sources'})
    assert all(x['exact_case_id_matches'] and x['required_marker']=='REJECT' and x['unknown_qualification_rule']=='NOT_QUALIFIED' for x in tests)
    put('cross-case-consistency.json',{'rows':tests,'count':7,
        'family_uniformity_basis':'Compared each exact source case, qualification row and predecessor mutation; not inferred from suffix or majority.',
        'uniform_conclusion':'All seven have the same missing canonical typing/composition authority, not a proof that every future chosen terminal outcome must be the same.',
        'participant_subjects_not_merged':True,'no_witness_evaluation':True})
    put('registry-preservation.json',{
        'base_registry':{'path':rel(D/'canonical-350-registry.json'),'sha256':sha(D/'canonical-350-registry.json')},
        'canonical_cases':350,'unique_IDs':350,'changes':[],
        'seven_classifications_unchanged':{i:'SPEC_INCOMPLETE' for i in ids},
        'complete_343_record_hashes':{r['WITNESS_ID']:canon(r) for r in reg if r['STATUS']=='SPEC_COMPLETE_NOT_EVALUATED'},
        'derived_closed_case_registry_created':False,
        'reason':'No case meets reconciliation conditions; no canonical classification update is authorized. C5D remains byte-preserved.'})


def result(rows):
    ids=[r['WITNESS_ID'] for r in rows]
    put('minimum-authority-required.json',{
        'scope_exact_IDs':ids,'baseline_and_mutation_change_requested':False,
        'minimum_normative_decision':'Specify the governed object/result variable, result domain and evaluation stage of canonical required_outcome=REJECT for these seven fixed C5D omission mutations; explicitly define its deterministic relationship to the preserved missing-row UNKNOWN and NOT_QUALIFIED/receipt-denial consequences.',
        'unfilled_authority_proposition':'For the seven named C5D catalog_row_omission specifications, canonical required_outcome=REJECT denotes [GOVERNED_OBJECT_AND_RESULT_VARIABLE] in [RESULT_DOMAIN] at [EVALUATION_STAGE]. Given the source-prescribed UNKNOWN for the absent expected Reader row and consequent lack of qualification, apply [EXACT_COMPOSITION_OR_PRECONDITION_OR_PRECEDENCE_RULE]. Preserve UNKNOWN evidence and distinct native wire codes unless independently authorized otherwise. No witness is evaluated or proven by this clarification.',
        'no_placeholder_filled':True,'no_form_recommended':True,
        'not_requested':['T8 redesignation','Material rotation or principal replacement','Substitution necessity/sufficiency','I13 change','POSTMASTER context/internal scope/atomic boundary/internal universe closure','Evaluation or implementation','Historical artifact rewrite'],
        'new_decision_must_not_be_claimed_historically_entailed':True,
        'existing_safe_behavior_without_decision':'Retain uncertainty and deny unsupported positive qualification/publication/authority. Do not claim canonical expected-output compliance.'})
    put('primary-result.json',{
        'SELECTED_OUTCOME':'D','status':'AUTHORITY_INSUFFICIENT','RECONCILIATION_FORM':'INSUFFICIENT_AUTHORITY',
        'CATALOG_ROW_OMISSION_CASES_TOTAL':7,'CASES_RECONCILED':0,'CASES_STILL_INCOMPLETE':7,'TRUE_CONTRADICTIONS':0,
        'true_contradictions_scope':'Zero PROVEN same-variable/same-stage/same-precondition contradictions; not an assertion that all possible interpretations are consistent.',
        'affected_ids':ids,'why_not_A_or_B':'No case has complete canonical semantic typing/composition; zero cases close, not a partial reconciliation.',
        'why_not_C':'The generic canonical REJECT result target/stage is unestablished; do not infer a true contradiction from different words.',
        'why_not_E':'Exact repository, hashes, manifests and seven predecessor gap identities passed preflight.',
        'safe_known_result':'Missing expected-row evidence remains UNKNOWN; qualification/qualified receipt unavailable; no positive authority inferred.',
        'CANONICAL_CASES_TOTAL':350,'DECISION_PREDICATE_COMPLETE':343,'DECISION_PREDICATE_INCOMPLETE':7,'AUTHORITY_CHAIN_COMPLETE':343,'AUTHORITY_CHAIN_INCOMPLETE':7,
        'STATICALLY_PROVEN':0,'STATICALLY_DISPROVEN':0,'SPEC_COMPLETE_NOT_EVALUATED':343,'SPEC_INCOMPLETE':7,
        'SUBSTITUTION_WITNESSES_REQUIRED':350,'SUBSTITUTION_WITNESSES_PROVEN':0,'SUBSTITUTION_WITNESSES_UNKNOWN':350,
        'N1_SUBSTITUTION_STATIC_WITNESSES':'OPEN','N1_DECISIONS_REQUIRED':12,'N1_DECISIONS_CLOSED':11,'N1_DECISIONS_OPEN':1,
        'V2_NATIVE_STATIC_DESIGN_PROOF':'FAIL','V2_NATIVE_STATUS':'BLOCKED','NEXT_EXECUTED':False,
        'NEXT_GATE':'PROJECT_AUTHORITY_CATALOG_ROW_OMISSION_RESULT_SEMANTICS'})
    put('authority-inventory.json',{'sources':list(AUTH.values()),'current_gate_instruction':{'path':rel(HERE/'project-authority-input.txt'),'sha256':sha(HERE/'project-authority-input.txt'),'authority_class':'USER_BOUNDED_ANALYSIS_AUTHORIZATION_NOT_NEW_RESULT_MAPPING'},
        'scope':'Exact seven-case recovery and directly relevant existing type/order/qualification/protocol authority only.',
        'source_code_or_review_is_not_new_normative_authority':True})


def report(rows):
    text='''# Package0090 C5E — catalog-row omission semantic reconciliation

Primary outcome D: **AUTHORITY_INSUFFICIENT**. The seven exact C5D omission records remain SPEC_INCOMPLETE. No UNKNOWN→REJECT, REJECT→UNKNOWN, precedence or distinct semantic layer is selected to obtain closure. Zero true contradictions are proven, because sameness of governed variable/stage/preconditions is itself unestablished. This is a limit on recovered authority, not proof the words are equivalent or necessarily contradictory.

## Preservation and exact scope

Branch checkpoint/package-0090-cloud-handoff, documentary HEAD451265ff5b3d286eb4d27c4b3817c2f558f30123. Frozen implementation/semantic baselinecbc284f62d9bd09b7169b55c8d66a3c51a68c6cb remains ancestor. Exactly107 authorized prior local paths, five manifests,350 unique C5D IDs and9,206 preexisting hashes are verified. IDs below are loaded directly from C5D bounded-gaps, not reconstructed from memory. The343 complete records are semantically untouched; their canonical hashes are frozen individually. No V043 or historical evidence change.

'''
    for row in rows:text+='- '+row['WITNESS_ID']+'\n'
    text+='''
## Recovered semantic targets

The missing-row rule is direct: N1 catalog-projection `/sources/0/MISSING_ROW_SEMANTICS` states that an expected identity/source row missing produces UNKNOWN; a collection absence is evidence only after a complete verified snapshot, never query failure. In these exact mutations the expected Reader (OID_R,NAME_R) stays independently specified while its candidate pg_roles row is omitted. The actual Reader principal does not thereby cease to exist, its independent own-session identity does not become universally unknown, and actual DB membership is not inferred from a missing candidate row. The after-state is stipulated specification data, not an executed lookup or database observation.

Catalog predicates explicitly use TRUE/FALSE/UNKNOWN and retain uncertainty without false/zero inference. Each participant qualification separately requires ALL_KNOWN_TRUE and maps UNKNOWN to NOT_QUALIFIED. This establishes lack of positive qualification, not the literal canonical classification REJECT.

The REJECT source is each exact N1 `new_cases` record: required_outcome=REJECT with a generic catalog/IO/custody/peer predicate. That record does not identify a governed row-admission object, native response variable, qualification output variable or witness-oracle result algebra/stage. It cannot be silently interpreted as any one of those. Native ABI codes REJECTED=2 and UNKNOWN=3 are explicitly distinct even though they share an error schema; no source identifies the generic REJECT string with either numeric code for this omission.

## Ordering and fail-closed behavior

Accepted G1 dependencies order acquisition/sanitization S01–S05 before S06 typed frame assembly, then S07/S08 pure predicate evaluation. S06 prose says duplicate/missing identity rejects. S07/S08 and participant qualification deny qualification while retaining UNKNOWN/NULL. Failures abort the snapshot before unsupported authority output and never permit a broader fallback role/query. These denial/ordering statements are preserved, not ignored.

They do not explicitly bind the canonical required_outcome marker to a stage or define a conversion of missing-row UNKNOWN to that marker. The exact first firing step for this omission, a canonical REJECT-versus-UNKNOWN short-circuit, a precedence rule, or an omission-specific wire error mapping cannot be invented from dependency order. Known partial pipeline order therefore does not establish the full reconciliation evaluation order.

Seven distinctions are separately recorded: lookup result; identity resolution; catalog membership; row presence; row admissibility; witness evaluability; final decision. Fail-closed means no unsupported positive grant. It does not automatically equate uncertainty with canonical REJECT or make an unknown witness pass. `UNKNOWN_fails_closed=true` and `not_all_coverage_rows_are_proven_rejection=true` reinforce that limit.

## Form tests and cross-case consistency

TYPED_COMPOSITION lacks the canonical target and composition function. ORDERED_REFINEMENT lacks a typed conversion. CONDITIONALLY_DISTINCT lacks an independently bound second precondition. EXPLICIT_PRECEDENCE lacks a priority statement. TRUE_CONTRADICTION lacks proof of the same variable/stage/preconditions. Only INSUFFICIENT_AUTHORITY is established; no seventh reconciliation form is created.

Each original case and qualification row is checked independently. All seven specify the same expected Reader-row omission under distinct participant contexts, the same source missing-row semantics, and the same untyped canonical REJECT label. That supports a uniform missing-authority finding, not a majority-selected outcome or a proof that every future authorized terminal rule must be identical. No case closes.

## Minimum required authority and retained status

The minimum decision is to define **what canonical REJECT governs, its result domain and evaluation stage, and its deterministic relation to the source-prescribed UNKNOWN and NOT_QUALIFIED/receipt-denial consequences for these exact seven mutations**. An unfilled proposition is in minimum-authority-required.json; no outcome or algebra is recommended. This does not require T8, I13 or unrelated context/scope/atomic/universe decisions, and cannot be represented as historically entailed.

No C5D registry is overwritten and no classification patch is applied:343 SPEC_COMPLETE_NOT_EVALUATED +7 SPEC_INCOMPLETE =350. Zero STATICALLY_PROVEN/DISPROVEN. All350 witness proofs remain UNKNOWN; N1 OPEN,12decisions=11closed+1open; V2 proof FAIL/status BLOCKED. T8 stays resolved within its prospective bounded authority rule. Material/principal changes, substitution necessity/sufficiency and I13 are unchanged. Frozen context, internal scope, atomic boundary and internal universe/total remain unresolved;108/105/350 unchanged. Zero attacks materialized/evaluated, no witness predicate run.

Only new C5E evidence is written. No implementation/build/native runtime/SQL/database/V043/B02/git add/commit/push. Independent reviews assess this bounded authority recovery and uncertainty preservation; agreement supplies no missing authority.

NEXT_GATE=PROJECT_AUTHORITY_CATALOG_ROW_OMISSION_RESULT_SEMANTICS. NEXT_EXECUTED=false. STOP with Outcome D.
'''
    (E/'PACKAGE-0090-B01-v2-native-static-closure-r5n2a5-3c5e.md').write_text(text,encoding='utf-8')


def validate():
    pre=rd(HERE/'preflight.json');assert all(sha(ROOT/k)==v for k,v in pre['preexisting_sha256'].items())
    for s in rd(HERE/'authority-inventory.json')['sources']:
        assert sha(ROOT/s['SOURCE_PATH'])==s['sha256']
        assert canon(select(rd(ROOT/s['SOURCE_PATH']),s['SECTION_OR_IDENTIFIER']))==s['canonical_fact_sha256']
    rows=rd(HERE/'seven-case-inventory.json')['cases'];assert [x['WITNESS_ID'] for x in rows]==rd(D/'bounded-gaps.json')['affected_ids']
    assert len(rows)==7 and all(x['SPEC_STATUS']=='SPEC_INCOMPLETE' for x in rows)
    complete=rd(HERE/'registry-preservation.json')['complete_343_record_hashes'];assert complete==pre['complete_343_records_frozen']
    assert subprocess.check_output(['git','diff','--name-only'],cwd=ROOT)==b''
    assert subprocess.check_output(['git','diff','--cached','--name-only'],cwd=ROOT)==b''
    return len(pre['preexisting_sha256'])


if __name__=='__main__':
    assert ROOT==pathlib.Path('C:/Projects/flooow-genesis-git')
    authority_inventory();rows,reg=case_analysis();type_analysis(rows);cross_case(rows,reg);result(rows);report(rows)
    print('C5E_PRIMARY_OUTCOME=D; EXACT_CASES=7; RECONCILED=0; SEMANTIC_CONTRADICTIONS_PROVEN=0; PRESERVED_HASHES='+str(validate()))
