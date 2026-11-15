"""C5B static authority analysis/evidence only. Never invokes native code or SQL."""
import hashlib
import itertools
import json
import pathlib
import subprocess

ROOT = pathlib.Path(__file__).resolve().parents[3]
HERE = pathlib.Path(__file__).resolve().parent
C5A = ROOT / 'docs/evidence/package-0090-B01-v2-native-static-closure-r5n2a5-3c5a-resumption'
C5 = ROOT / 'docs/evidence/package-0090-B01-v2-native-static-closure-r5n2a5-3c5-resumption'
C4B = ROOT / 'docs/evidence/package-0090-B01-v2-native-static-closure-r5n2a5-3c4b'
IDS = ['T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'T8', 'T12']


def read(p):
    return json.loads(p.read_text(encoding='utf-8-sig'))


def write(name, value):
    (HERE / name).write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def rel(p):
    return p.relative_to(ROOT).as_posix()


def resolve(value, ptr):
    for part in ptr.strip('/').split('/') if ptr else []:
        part = part.replace('~1', '/').replace('~0', '~')
        value = value[int(part)] if isinstance(value, list) else value[part]
    return value


def authority():
    sources = read(C5A / 'provenance-index.json')['sources']
    for s in sources:
        path = ROOT / s['path']
        assert sha(path) == s['sha256']
        assert resolve(read(path), s['pointer']) == s['exact_fact']
        s['authority_class'] = ('EXPLICIT_PROJECT_AUTHORITY_RECORDED_DECISION' if s['id'] in ['S15','S16'] else 'FROZEN_ACCEPTED_STATIC_DESIGN_CONTRACT_OR_DERIVATION')
        s['direct_or_derived'] = 'DERIVED_RECONSTRUCTION' if s['id'] in ['S13','S14','S17'] else 'DIRECT_SOURCE_SELECTION'
        s['semantic_proposition'] = s['scope']
        s['authority_limit'] = 'Retains its prior accepted scope. Source existence and preservation do not select a target event or prove runtime enforcement.'
    raw = C4B / 'project-authority-input.txt'
    text = raw.read_text(encoding='utf-8-sig')
    selections = [
        ('A_OBJECT', '2. EXACT OBJECT DEFINITION', '3. DESIGN RATIONALE', 'O8 is credential state relevant to continuity across the POSTMASTER transition; constituents and transition are not determined by this object designation.'),
        ('A_OPEN', '3. DESIGN RATIONALE', '4. ANTI-AGGREGATION RULE', 'TRANSITION, POSTMASTER_CONTEXT_BINDING, INTERNAL_SCOPE_AND_EXCEPTIONS and EXHAUSTIVE_ATOMIC_BOUNDARY are intentionally unanswered.'),
        ('A_NO_AGGREGATION', '4. ANTI-AGGREGATION RULE', '5. I13 PRESERVATION', 'O8 membership requires independently proven semantic analysis, not any credential-related wording.'),
        ('A_I13', '5. I13 PRESERVATION', '6. THREE-DIMENSION NON-PREJUDGMENT', 'I13 is mandatory external cross-cutting, preserved in full; principal independence is not absorbed by O8.'),
        ('A_COUNTS', '7. DENOMINATOR NON-PREJUDGMENT', '8. ADVERSARIAL DECISION REVIEW', 'Object designation establishes neither internal universe/atomicity nor classification; 108/105 and attack350 are preserved.'),
    ]
    for ident, start, end, proposition in selections:
        excerpt = text[text.index(start):text.index(end)]
        sources.append(dict(id=ident, path=rel(raw), sha256=sha(raw), section=start,
                            exact_excerpt=excerpt, semantic_proposition=proposition,
                            authority_class='EXPLICIT_PROJECT_AUTHORITY_INPUT_OBJECT_ONLY', direct_or_derived='DIRECT'))
    for ident, path, ptr, cls, proposition in [
        ('A_C5', C5/'outcome.json', '', 'ACCEPTED_PREDECESSOR_EVIDENCE_NOT_NEW_SEMANTIC_AUTHORITY', 'C5 did not recover a unique transition.'),
        ('A_C5A', C5A/'gate.json', '', 'USER_FROZEN_C5A_RESULT', 'Eight prospective alternatives, no compounds or selected transition, frozen accounting.'),
        ('A_C5A_PROPOSALS', C5A/'prospective-alternatives.json', '/alternatives', 'UNAPPROVED_PROSPECTIVE_PROPOSALS_NOT_DESIGNATIONS', 'Names bounded comparisons only, no inherited O8 continuity rule or preference.'),
    ]:
        sources.append(dict(id=ident, path=rel(path), sha256=sha(path), pointer=ptr,
                            exact_fact=resolve(read(path), ptr), semantic_proposition=proposition,
                            authority_class=cls, direct_or_derived='DIRECT_RECORD_OF_PRIOR_RESULT'))
    write('authority-inventory.json', {
        'records': sources,
        'inventory_scope': 'Already-frozen sources used by C5/C5A plus original C4B authority input and the C5B instruction. No new discovery/source expansion.',
        'current_gate_instruction': {'path': 'project-authority-input.txt', 'authority_class': 'CURRENT_USER_GATE_AUTHORIZATION_NOT_CANDIDATE_SELECTION', 'selection_supplied': False},
        'preservation_only_not_semantic_authority': ['451265ff checkpoint identity', '.gitattributes LFS rules', 'local STOP evidence', 'docs/post-mvp'],
        'authority_order': 'Explicit object-only project authority constrains accepted source contracts; predecessor dossier proposals and reviewer agreement cannot create a target designation.',
        'direct_designation_chain_found': False,
    })


KNOWN = {
    'T2': [('/credentials/0/REGISTRY_BINDING', 'Exact native current enrollment/publication revisions are required for credential use.', 'S10'),
           ('/records/0/canonical_tuple', 'Registry independently identifies process, enrollment, credential_ref, channel and current generation; none is automatically O8 membership.', 'S18')],
    'T3': [('/credentials/0/MEMORY_RESIDENCE_POLICY', 'Private import before ACTIVE; zeroization after retirement, not a claim zeroization equals this edge.', 'S10'),
           ('/phase_gate', 'HOST independently verifies confinement before ACTIVE; no self weakening or bootstrap return.', 'S4')],
    'T4': [('/phase_edges/2', 'Execution ACTIVE becomes REVOKED; writer invalidation or key destruction at that exact edge is not established.', 'S3'),
           ('/rules', 'Source ACTIVE-scoped operational rules motivate phase-exit comparison; no runtime enforcement proof.', 'S20')],
    'T5': [('/records/0/revocation', 'Monotonic invalidation before new eligibility; every old receipt/credential/channel remains ineligible.', 'S18'),
           ('/credentials/0/REVOCATION_AUTHORITY', 'Writer invalidation and HOST custody teardown remain separated.', 'S10')],
    'T6': [('/credentials/0/GENERATION_BINDING', 'Exact independently current slot/generation high-water mandatory, no fallback.', 'S10'),
           ('/records/1/revocation', 'Generation retirement invalidation precedes fresh eligibility; no simultaneous registry/phase event inferred.', 'S19')],
    'T7': [('/records/1/tombstone', 'Retired slot/generation remains irreversible even if newer process dies or lookup fails.', 'S19'),
           ('/records/1/monotonicity', 'No decreasing high-water/revision or deleted tombstone; missing/corrupt latest state is UNKNOWN, not old-state fallback.', 'S19')],
    'T8': [('/records/1/replacement', 'Old enrollment revoked, UNKNOWN reconciled, extinction proved, tombstone durable; checked previous+1 generation before new enrollment.', 'S19'),
           ('/credentials/0/RESTART_BEHAVIOR', 'Fresh generation/key only after old reconciliation/extinction/tombstone; POSTMASTER endpoint form retained.', 'S10')],
    'T12': [('/classes/2/TRANSFER', 'Transfer forbidden except explicit trusted bootstrap delivery before eligibility.', 'S11'),
            ('/classes/2/INHERITANCE', 'No operational credential inheritance; only explicit pre-enrollment inventory. This class policy does not completely define O8.', 'S11')],
}


def link(source_id, proposition, pointer=None, derived=False):
    inventory = {x['id']: x for x in read(HERE/'authority-inventory.json')['records']}
    source = inventory[source_id]
    return {'source_id': source_id, 'source_path': source['path'],
            'section_or_identifier': pointer or source.get('pointer', source.get('section','')),
            'exact_semantic_proposition': proposition, 'authority_class': source['authority_class'],
            'direct_or_derived': 'DERIVED_C5B_NON_ENTAILMENT_ANALYSIS' if derived else source['direct_or_derived']}


def candidates():
    proposals = read(C5A/'prospective-alternatives.json')['alternatives']
    rows = []
    for proposal in proposals:
        ident = proposal['alternative_id']
        pd = proposal['prospective_definition']
        q = next(x for x in read(C5A/'qualification-matrix.json')['rows'] if x['TRANSITION_ID']==ident)
        facts = [link(s, proposition, ptr) for ptr, proposition, s in KNOWN[ident]]
        state_refs = [link(s, 'Source structure supports this candidate event in its own state domain, not designation as the O8 target.', derived=True) for s in q['source_refs']]
        row = {
            'candidate': ident, 'identity': proposal['source_event'],
            'PRE_STATE': pd['PRE_STATE'], 'EVENT': pd['TRANSITION_EVENT'], 'POST_STATE': pd['POST_STATE'],
            'pre_post_scope': 'SOURCE_EVENT_STATES_ONLY; relevant concrete O8 pre/post state and observability are NOT_ESTABLISHED',
            'state_basis': state_refs,
            'actor': q['actor_principal'], 'participant': q['participant_slot'], 'generation': q['generation_identity'],
            'credential': q['credential_state'], 'temporal_scope': q['temporal_position'],
            'FORBIDDEN_CONTINUITY': 'NOT_ESTABLISHED_AS_COMPLETE_O8_TARGET_RULE',
            'REQUIRED_DISCONTINUITY': 'NOT_ESTABLISHED_AS_COMPLETE_O8_TARGET_RULE',
            'ALLOWED_CONTINUITY': 'NOT_ESTABLISHED_AS_COMPLETE_O8_TARGET_RULE',
            'continuity_basis': [link('A_OBJECT','Object designation alone does not identify forbidden constituent persistence or target event.'), link('A_NO_AGGREGATION','Credential-related rules cannot be automatically aggregated into a complete O8 membership/continuity contract.')],
            'known_frozen_constraints_still_mandatory': facts,
            'not_claimed': 'NOT_ESTABLISHED does not mean native currentness, invalidation, zeroization, transfer restrictions or approved replacement renewal rules are absent or optional.',
            'I13_relation': {
                'preserved_in_full': True, 'classification':'MANDATORY_EXTERNAL_CROSS_CUTTING_INVARIANT',
                'intersects': 'Credential use/custody/qualification must respect distinct concurrent principals; intersection does not absorb that invariant.',
                'designation_would_narrow_I13': 'NO_IF_EXTERNAL_INVARIANT_RETAINED; no designation emitted',
                'basis':[link('A_I13','Principal independence is mandatory external; O8 cannot absorb it.'), link('S17','Seven concurrent native slots, 21 unordered distinct-principal pairs and auxiliary separation remain required; no inferred cross-generation numeric UID delta.')],
            },
            'substitution_relation': {'necessary':'UNKNOWN','sufficient':'UNKNOWN','category':'UNKNOWN',
                'scope':'Participant substitution relation to this candidate and the target inheritance obligation is not established. Generic replacement terminology is not evidence of exact edge equivalence.',
                'basis':[link('S1','Original generic required REJECT case identifies no transition event.'),link('S2','Exact credential_inheritance attack-specific mapping remains pending; no substitution necessity/sufficiency theorem.')],
            },
            'credential_inheritance_relation': {'status':'UNKNOWN','reason':'Source event occurrence and credential eligibility effects do not establish that target O8 inheritance occurs or cannot occur here.',
                'basis':[link('A_OBJECT','O8 constituents and target transition remain unassigned.'),link('A_OPEN','The earlier explicit decision intentionally left TRANSITION unanswered.')]},
            'distinct_concurrent_principal_obligation': {'established_by_candidate_itself':'NO',
                'source_of_obligation':'Independent frozen I13; event occurrence does not create, replace or restrict it.',
                'basis':[link('A_I13','Principal independence remains an external mandatory prerequisite.'),link('S17','Concurrent pairwise principal distinction is independently reconstructed from frozen sources.')]},
            'positive_target_designation_authority':'NOT_FOUND_IN_FROZEN_AUTHORITY_CHAIN',
            'normative_trigger_basis': [link('A_OPEN','A meaningful source boundary is not an O8 target trigger; explicit prior authority left this decision open.', derived=True)],
            'survives':'NORMATIVELY_POSSIBLE_PROSPECTIVE_DESIGNATION_NOT_ALREADY_ENTAILED',
            'direct_elimination_authority':None,
        }
        rows.append(row)
        write('candidate-'+ident+'.json', row)
    assert [r['candidate'] for r in rows] == IDS
    return rows


def decision_tests(rows):
    matrix = []
    for row in rows:
        tests = {
            'D1': ('UNKNOWN', 'A source-backed credential-relevant comparison is prospectively fit, but actual transition of O8 rather than surrounding lifecycle is not authoritatively designated.', ['A_OBJECT','A_OPEN']),
            'D2': ('UNKNOWN', 'No direct frozen normative trigger ties the generic credential_inheritance obligation uniquely to this candidate.', ['S1','S2','A_OPEN']),
            'D3': ('UNKNOWN', 'Source event pre/event/post states are established. Relevant O8 pre/post contents and target-specific bindings are not; source-state determinacy is not complete O8 determinacy.', ['A_OBJECT','A_NO_AGGREGATION']),
            'D4': ('UNKNOWN', 'Native credential constraints remain binding, but forbidden/required/allowed continuity of the target O8 across this exact candidate is not completely established.', ['S10','S11','A_OBJECT','A_NO_AGGREGATION']),
            'D5': ('PASS', 'The candidate can be considered while full mandatory external I13 is retained; no designation, principal merge or I13 absorption occurs.', ['A_I13','S17']),
            'D6': ('UNKNOWN', 'No independent necessity/sufficiency relation to participant substitution is established; the still-open witness cannot be used as its own premise.', ['S1','S2']),
            'D7': ('UNKNOWN', 'Distinct event identities and chronology do not exclude other candidates from prospective target designation.', ['A_C5A','A_C5A_PROPOSALS','A_OPEN']),
            'D8': ('UNKNOWN', 'No complete positive authority chain entails this candidate as THE target. Not disproven is not entailed.', ['A_OBJECT','A_OPEN','A_C5A']),
        }
        matrix.append({'candidate':row['candidate'], 'tests':{k:{'result':v,'reason':reason,'basis':[link(s,reason,derived=True) for s in refs]} for k,(v,reason,refs) in tests.items()},
                       'all_D1_D8_PASS':False, 'source_event_pre_post_established':True,'complete_O8_pre_post_established':False})
    write('D1-D8-matrix.json', {'rows':matrix, 'test_names':{'D1':'OBJECT_FIT','D2':'NORMATIVE_TRIGGER','D3':'PRE_POST_DETERMINACY','D4':'CONTINUITY_SEMANTICS','D5':'I13_PRESERVATION','D6':'SUBSTITUTION_SEMANTICS','D7':'EXCLUSIVITY','D8':'SUFFICIENCY_FOR_DESIGNATION'},
        'allowed_test_results':['PASS','FAIL','UNKNOWN'], 'unknown_is_neither_pass_nor_fail':True,
        'not_the_historical_D1_D2_D3_dimensions':True,'scoring_or_ranking_performed':False,'candidates_passing_all_tests':[]})


def countermodels(rows):
    out = []
    for row in rows:
        ident = row['candidate']
        out.append({
            'id':ident+'/A','candidate':ident,'family':'A_CANDIDATE_OCCURS_NOT_TARGET_HERE',
            'source_occurrence': {'PRE_STATE':row['PRE_STATE'],'EVENT':row['EVENT'],'POST_STATE':row['POST_STATE']},
            'counterinterpretation':'This source edge occurs in its approved source domain, but the unassigned target-event relation does not designate this occurrence as the target credential-inheritance transition. Occurrence is not equated with harmful inheritance or absence of harmful inheritance.',
            'candidate_specific_constraints':[x['exact_semantic_proposition'] for x in row['known_frozen_constraints_still_mandatory']],
            'target_relation_assignment': {'TargetAt_this_candidate':False,'TargetAt_other_survivors':'UNASSIGNED_IN_THIS_PARTIAL_COUNTERINTERPRETATION'},
            'compatibility_basis':[link('A_OPEN','Prior authority intentionally leaves target transition unresolved.'),link('A_OBJECT','Object definition supplies no event selector.'),link('S1','Generic required REJECT case does not demand every occurrence of this source edge be the target.')],
            'status':'SURVIVES_AS_AUTHORITY_COMPATIBLE_PARTIAL_COUNTERINTERPRETATION',
            'rejection_authority':None,'O8_properties_assigned':False,'operational_trace_executed':False,
        })
        for other in rows:
            if other['candidate']==ident:
                continue
            out.append({
                'id':ident+'/B/'+other['candidate'], 'candidate':ident,'family':'B_TARGET_AT_ANOTHER_SURVIVOR',
                'alternative_target_in_counterinterpretation':other['candidate'],
                'other_source_occurrence':{'PRE_STATE':other['PRE_STATE'],'EVENT':other['EVENT'],'POST_STATE':other['POST_STATE']},
                'counterinterpretation':'A hypothetical completion of the unassigned target-event relation locates the target comparison at the other existing source boundary. This is a counterinterpretation testing entailment, not an approved normative trigger, actual inheritance observation, new semantic member, or project-authority selection.',
                'target_relation_assignment':{'TargetAt_this_candidate':False,'TargetAt_other_candidate':True},
                'source_constraints_unchanged':[x['exact_semantic_proposition'] for x in other['known_frozen_constraints_still_mandatory']],
                'compatibility_basis':[link('A_C5A','The other boundary remains an unselected prospective alternative; no authority elimination is supplied.'),link('A_OPEN','Existing explicit object authority did not assign a target event.'),link('A_NO_AGGREGATION','No O8 member/property is added by this event-relation counterinterpretation.')],
                'status':'SURVIVES_AS_AUTHORITY_COMPATIBLE_COUNTERINTERPRETATION',
                'rejection_authority':None,'O8_properties_assigned':False,'operational_trace_executed':False,
            })
    write('countermodels.json', {'records':out,'total':len(out),'rejected':0,'surviving':len(out),
        'family_A_total':8,'family_B_total':56,'every_candidate_tested':IDS,
        'purpose':'Non-entailment of unique designation, not safety/enforcement verification or completed O8 semantics.',
        'model_scope':'Partial semantic counterinterpretations of the currently unassigned target-event relation, preserving every quoted source constraint; not concrete runtime attack traces or fully specified O8 continuity models.',
        'no_harmful_inheritance_occurrence_claimed':True,'no_positive_designation_inferred_from_compatibility':True,
        'not_a_model_count_denominator_for_attacks_or_obligations':True})


def pairwise(rows):
    by_id={r['candidate']:r for r in rows}
    prior={frozenset((x['A'],x['B'])):x for x in read(C5A/'event-relation-matrix.json')['pairs']}
    pairs=[]
    for a,b in itertools.combinations(IDS,2):
        relation=prior[frozenset((a,b))]
        pairs.append({'A':a,'B':b,'result':'UNKNOWN',
            'source_event_A':by_id[a]['identity'],'source_event_B':by_id[b]['identity'],
            'event_identity_relation':relation['relation'],'source_order_if_any':relation['proven_order'],
            'target_designation_question':'Does normative authority distinguish these as eligible versus ineligible target event, not merely as two event identities?',
            'reason':'Source states and domain/order distinctions are recorded, but no target-selector or exclusion chain establishes a normative designation distinction. UNKNOWN is not an assertion that the events are equal or that all future authority must treat them alike.',
            'basis':[link('A_OPEN','The object-only authority intentionally leaves the target event unassigned.'),link('A_C5A','Both source boundaries survive without selection; chronology or domain is not a selection theorem.',derived=True)],
            'candidate_A_constraints':[x['exact_semantic_proposition'] for x in by_id[a]['known_frozen_constraints_still_mandatory']],
            'candidate_B_constraints':[x['exact_semantic_proposition'] for x in by_id[b]['known_frozen_constraints_still_mandatory']],
            'converted_to_score_or_ranking':False})
    write('pairwise-distinguishability.json', {'pairs':pairs,'total':28,'DISTINGUISHED_BY_AUTHORITY':0,'NOT_DISTINGUISHED_BY_AUTHORITY':0,'UNKNOWN':28,
        'interpretation':'UNKNOWN is used conservatively for target-relevant normative distinguishability. It is not proof of universal equivalence, absence of all normative source differences, or event SAME_EVENT.',
        'identity_or_chronology_not_sufficient':True,'ranking_performed':False})


WORDING = ('For PACKAGE-0090 V2-native POSTMASTER credential-inheritance analysis, the authoritative transition comparison boundary for INHERITED_CREDENTIAL_STATE is [Tx], identified by [EXACT_SOURCE_EVENT], from [SOURCE_PRE_STATE] to [SOURCE_POST_STATE] on [SOURCE_SUBJECT]. This is an explicit prospective designation; it does not claim unique historical intent. It does not establish O8 constituent membership or forbidden/required/allowed continuity, redefine or absorb I13, resolve POSTMASTER context binding/internal scope/atomic boundary, establish internal N, close the N1 witness, or alter 108/105/350. Existing native currentness, invalidation, custody and retirement constraints remain mandatory.')


def decision_surface(rows):
    write('project-authority-decision-surface.json', {
        'surviving_alternatives':IDS,'eliminated_alternatives':[],
        'elimination_authority':[], 'unique_designation_entailed':False,
        'minimum_decision_required':'Provide an explicit prospective target-event designation using an existing surviving source-boundary identity and its source pre/event/post states; no candidate or eventual cardinality is selected by C5B. Any choice requiring a new compound, multiple-event set or new identity is outside this bounded gate and requires separate authority, not automatic selection of every survivor.',
        'minimum_decision_does_not_require_now':['Concrete O8 members or continuity partition','POSTMASTER_CONTEXT_BINDING','INTERNAL_SCOPE','ATOMIC_BOUNDARY','CANONICAL_INTERNAL_OBLIGATION_UNIVERSE'],
        'consequences':[{'candidate':r['candidate'],'identity':r['identity'],'source_pre':r['PRE_STATE'],'source_event':r['EVENT'],'source_post':r['POST_STATE'],
            'demonstrated_comparison_consequence':next(a['semantic_capability'] for a in read(C5A/'prospective-alternatives.json')['alternatives'] if a['alternative_id']==r['candidate']),
            'mandatory_source_constraints':r['known_frozen_constraints_still_mandatory'],
            'does_not_establish':'O8 continuity outcome/extent, substitution necessity/sufficiency, I13 as an internal member, exact context/scope/atomic universe, operational enforcement or N1 closure.'} for r in rows],
        'required_wording_unfilled':WORDING,'Tx_placeholder_filled':False,
        'scope_of_future_wording':'Resolves only prospective event ambiguity if explicitly approved. It does not satisfy all C5B unique-entailment tests from old authority or invent the missing O8 continuity contract.',
        'no_recommendation':True,'no_ranking':True,'selection_performed':False,
        'dependency_analysis':{'outcome_D_required':False,'reason':'Existing source boundaries and authority limits suffice to evaluate non-entailment and enumerate survivors. Missing target/O8 continuity authority prevents a unique old-authority designation; that does not prove that a particular unrelated frozen context/scope/atomic decision must be resolved first. Event-only prospective wording remains possible without those decisions.','unresolved_O8_continuity_is_not_assigned_to_an_unproven_architectural_dependency':True}})


def conclusion():
    write('primary-conclusion.json', {
        'SELECTED_OUTCOME':'B','status':'EXPLICIT_PROJECT_AUTHORITY_SELECTION_REQUIRED',
        'unique_designation_entailed':False,'designated_transition':None,'surviving':IDS,'eliminated':[],
        'positive_chain_test':'No candidate passes all D1-D8. D5 preserves I13; all other target-specific tests remain UNKNOWN rather than FAIL. No positive normative trigger or exclusivity chain was recovered.',
        'why_not_A':'Source boundary fitness and known native credential validity rules do not entail THE O8 transition or its complete continuity semantics.',
        'why_not_C':'No direct contradiction of C5/C5A found; event ambiguity and all eight prospective alternatives preserved.',
        'why_not_D':'No minimum prerequisite among context/scope/atomic/universe has been proven necessary to evaluate the absence of unique entailment or draft an event-only authority choice.',
        'why_not_E':'Exact 31-path preflight, both C5A manifests, frozen ancestry, V043 and preexisting hashes verified.',
        'countermodels':'64 authority-compatible partial target-relation counterinterpretations survive; none is a positive approved designation or concrete inheritance trace.',
        'pairwise':'28 target-normative distinction results UNKNOWN; event identity differences do not supply selection authority.',
        'TRANSITION_RESOLVED':'NO','PROJECT_AUTHORITY_SELECTION_PERFORMED':'NO',
        'I13_PRESERVED_IN_FULL':'YES','next_gate':'EXPLICIT_PROJECT_AUTHORITY_TRANSITION_SELECTION','NEXT_EXECUTED':False})


def report(rows):
    text='''# Package0090 C5B — project authority transition designation

Primary outcome B: **EXPLICIT_PROJECT_AUTHORITY_SELECTION_REQUIRED**. Frozen authority does not positively entail a unique target designation among T2,T3,T4,T5,T6,T7,T8,T12. No candidate is selected, ranked, combined, renamed or directly eliminated. No historical C5/C5A result is overturned.

## Preflight and authority

Branch remains `checkpoint/package-0090-cloud-handoff`, HEAD/documentary checkpoint `451265ff5b3d286eb4d27c4b3817c2f558f30123`. Implementation/semantic baseline remains `cbc284f62d9bd09b7169b55c8d66a3c51a68c6cb` and ancestry is valid. The LFS rules are preservation machinery only. Exactly 31 authorized local files were present: seven C5A STOP and 24 C5A resumption evidence. Both manifests and all 9,130 preexisting raw-byte hashes are preservation inputs. V043 is hash-frozen. Post-MVP files are hash-only inputs with no semantic authority.

Authority inventory verifies the 21 C5A source selections directly, records five exact sections of the original object-only project-authority input, and preserves predecessor records. The explicit O8 decision intentionally leaves TRANSITION unanswered; the N1 generic required case and still-pending exact attack mapping do not supply an event selector. Accepted native custody/currentness/retirement rules remain binding. Dossier proposals and review agreement do not become new normative triggers.

## Eight designation records and uniform decision tests

Every candidate file independently records source pre/event/post, principal/slot/generation/execution state, complete-O8 unknowns, known mandatory source constraints, full I13, substitution and target inheritance relations, with source path/identifier/proposition/authority class/direct-or-derived provenance.

| Candidate | Source boundary | Source pre → post |
|---|---|---|
'''
    for row in rows:
        text+=f"| {row['candidate']} | {row['identity']} | {row['PRE_STATE']} → {row['POST_STATE']} |\n"
    text+='''
The source event states are established in their own domains. They are not complete concrete pre/post states of O8. FORBIDDEN_CONTINUITY, REQUIRED_DISCONTINUITY and ALLOWED_CONTINUITY remain NOT_ESTABLISHED as complete target-specific rules. This does not erase generation/enrollment currentness, stale-use denial, no adoption while UNKNOWN, irreversible tombstones, protected-delivery limits, retirement/renewal or destruction obligations.

All eight receive the same D1–D8 entailment tests: D5 PASS (full I13 can be retained), D1/D2/D3/D4/D6/D7/D8 UNKNOWN. These are not scores. UNKNOWN does not mean failure or permission. Relevant O8 object fit, normative trigger, full O8 state determinacy, complete continuity, substitution necessity/sufficiency and exclusivity remain unestablished. Source-state determinacy alone cannot make D3 PASS for O8. Not disproven cannot make D8 PASS.

I13 remains the full mandatory external invariant: distinct concurrent seven-slot/21-pair principal subjects and auxiliary separation. No event itself creates that independent obligation. Principal equality/change and credential equality/change remain distinct; across-generation numeric UID difference is not inferred. Substitution necessity/sufficiency and whether target inheritance occurs at a source edge remain UNKNOWN.

## Counterinterpretations and pairwise test

Even though no candidate passes all designation tests, every one is challenged. Eight family-A records preserve each source event while leaving it undesignated as the target. Fifty-six family-B records consider each other surviving boundary as a hypothetical completion of the unassigned target-event relation. These are 64 partial semantic counterinterpretations, not runtime traces, catalog attacks, approvals or full O8 continuity models. No actual harmful inheritance is asserted. No candidate becomes designated just because one completion is compatible. All quoted source constraints, anti-aggregation and I13 remain unchanged. No rejecting target-selection authority was found; all 64 remain unrefuted within this frozen authority surface.

All 28 unordered candidate pairs are tested for **target-designation-relevant normative distinction**, not for lexical or temporal difference. Results: zero DISTINGUISHED_BY_AUTHORITY, zero NOT_DISTINGUISHED_BY_AUTHORITY, 28 UNKNOWN. This conservatively preserves uncertainty rather than claiming universal equivalence or absence of every source distinction. The known source-domain and ordering relations remain recorded; no pair matrix is converted to ranking.

## Bounded authority decision surface

All eight remain prospectively possible; none has direct elimination authority. Each available designation would focus comparison at only its source-defined edge: registry enrollment (T2), entry/exit ACTIVE (T3/T4), registry/generation invalidation (T5/T6), durable anti-rollback sealing (T7), checked generation succession (T8), or protected bootstrap delivery (T12). These are demonstrated comparison consequences, not O8 membership or inheritance outcomes.

The minimum missing normative act is an explicit prospective target-event designation drawn from the existing bounded surface, with its source pre/event/post. C5B does not decide that eventual target cardinality is one or eight. A new compound, multiple-event set or new identity is outside this bounded gate and would require separate authority. No unrelated architecture choice is requested. The narrow wording remains deliberately unfilled:

> '''+WORDING+'''

That prospective event-only proposition would resolve the event ambiguity if later explicitly authorized; it would not retroactively make old authority pass D1–D8 or supply missing O8 continuity semantics. Missing complete continuity remains a real limitation, not a fabricated prerequisite that context/scope/atomic/universe must be decided first. Existing sources suffice to evaluate non-entailment, so Outcome B applies rather than an unproven dependency Outcome D.

## Preserved status and stop

TRANSITION unresolved/cardinality UNKNOWN; POSTMASTER context binding, internal scope and atomic boundary unresolved; internal universe/total NOT_ESTABLISHED. Historical D1/D2/D3 decomposition is not validated by these separately named decision tests. Candidate108/ambiguity105 and attack350 remain unchanged; zero attacks materialized/evaluated. N1 qualification CLOSED/substitution OPEN; 12 decisions = 11 closed + one open. V2 proof FAIL/status BLOCKED. No compound admitted, no source authority promoted and no next gate executed.

Two independent reviews must validate this primary analysis before final closure; their PASS means no unsupported normative designation was found, not authority by consensus. All artifacts are C5B evidence only. No implementation/native build/native runtime/SQL/database/V043/B02 or git add/commit/push is performed. Historical evidence and parallel post-MVP files are untouched.

NEXT_GATE=EXPLICIT_PROJECT_AUTHORITY_TRANSITION_SELECTION. NEXT_EXECUTED=false. STOP with Outcome B.
'''
    (ROOT/'docs/evidence/PACKAGE-0090-B01-v2-native-static-closure-r5n2a5-3c5b.md').write_text(text,encoding='utf-8')


def validate():
    inv=read(HERE/'authority-inventory.json')['records']
    for s in inv:
        assert sha(ROOT/s['path'])==s['sha256']
    rows=[read(HERE/('candidate-'+i+'.json')) for i in IDS]
    assert [r['candidate'] for r in rows]==IDS
    matrix=read(HERE/'D1-D8-matrix.json')['rows']
    assert len(matrix)==8 and all(len(r['tests'])==8 for r in matrix)
    assert all(t['result'] in ['PASS','FAIL','UNKNOWN'] for r in matrix for t in r['tests'].values())
    assert not any(r['all_D1_D8_PASS'] for r in matrix)
    cm=read(HERE/'countermodels.json')['records'];assert len(cm)==64 and len({r['id'] for r in cm})==64
    assert len(read(HERE/'pairwise-distinguishability.json')['pairs'])==28
    pre=read(HERE/'preflight.json')
    assert all(sha(ROOT/p)==h for p,h in pre['preexisting_sha256'].items())
    assert subprocess.check_output(['git','diff','--name-only'],cwd=ROOT)==b''
    assert subprocess.check_output(['git','diff','--cached','--name-only'],cwd=ROOT)==b''
    return len(pre['preexisting_sha256'])


if __name__=='__main__':
    assert ROOT==pathlib.Path('C:/Projects/flooow-genesis-git')
    authority()
    rows=candidates()
    decision_tests(rows)
    countermodels(rows)
    pairwise(rows)
    decision_surface(rows)
    conclusion()
    report(rows)
    print('PRIMARY_OUTCOME=B; STATIC_STRUCTURE=PASS; PREEXISTING_HASHES='+str(validate()))
