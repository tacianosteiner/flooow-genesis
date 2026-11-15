"""Static evidence construction only; no implementation, runtime or SQL invocation."""
import hashlib
import itertools
import json
import pathlib
import subprocess

ROOT = pathlib.Path(__file__).resolve().parents[3]
HERE = pathlib.Path(__file__).resolve().parent
PREVIOUS = ROOT / 'docs/evidence/package-0090-B01-v2-native-static-closure-r5n2a5-3c5-resumption'


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def write(name, data):
    (HERE / name).write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def relative(path):
    return path.relative_to(ROOT).as_posix()


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT, text=True).strip()


def pointer(value, path):
    for part in path.strip('/').split('/') if path else []:
        part = part.replace('~1', '/').replace('~0', '~')
        value = value[int(part)] if isinstance(value, list) else value[part]
    return value


def sources():
    records = read(PREVIOUS / 'provenance-index.json')['sources']
    for row in records:
        path = ROOT / row['path']
        assert digest(path) == row['sha256'], row['path']
        assert pointer(read(path), row['pointer']) == row['exact_fact'], row['id']
    additions = [
        ('S18', 'r5n/native-registry-generation.json', '/records/0', 'Registry credential_ref, enrollment identity, monotonic invalidation, replacement and restart constraints'),
        ('S19', 'r5n/native-registry-generation.json', '/records/1', 'Generation natural key, high-water, irreversible tombstone and checked succession'),
        ('S20', 'r5n1/execution-isolation.json', '/rules', 'Source-design rules scoped to ACTIVE; no physical enforcement proof'),
        ('S21', 'r5n/native-registry-generation.json', '/records/2', 'Extinction receipt and tombstone evidence are not physical extinction itself'),
    ]
    for ident, suffix, ptr, scope in additions:
        path = ROOT / ('docs/evidence/package-0090-B01-v2-native-static-closure-' + suffix)
        records.append(dict(id=ident, path=relative(path), sha256=digest(path), pointer=ptr,
                            exact_fact=pointer(read(path), ptr), scope=scope))
    write('provenance-index.json', {
        'sources': records,
        'frozen_source_selection': 'Same Package0090 source files selected by C5; four additional exact selections within those files',
        'source_files_total': len({s['path'] for s in records}),
        'provenance_selections_total': len(records),
        'no_semantic_authority_from': ['451265ff preservation metadata', '.gitattributes LFS rules', 'C5/C5A STOP records', 'docs/post-mvp'],
        'provenance_rule': 'Source facts establish event structure and constraints. C5A supplies unapproved prospective comparison-boundary proposals only; no historical event designation inferred.',
    })


TARGETS = ['T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'T8', 'T12']
CLASS = {
    'T1': 'INSUFFICIENT_TO_CLASSIFY',
    'T2': 'TARGET_TRANSITION_CANDIDATE',
    'T3': 'TARGET_TRANSITION_CANDIDATE',
    'T4': 'TARGET_TRANSITION_CANDIDATE',
    'T5': 'TARGET_TRANSITION_CANDIDATE',
    'T6': 'TARGET_TRANSITION_CANDIDATE',
    'T7': 'TARGET_TRANSITION_CANDIDATE',
    'T8': 'TARGET_TRANSITION_CANDIDATE',
    'T9': 'OBSERVATION_OR_RECONCILIATION_ONLY',
    'T10': 'OBSERVATION_OR_RECONCILIATION_ONLY',
    'T11': 'PARTICIPANT_LIFECYCLE_BOUNDARY',
    'T12': 'TARGET_TRANSITION_CANDIDATE',
    'T13': 'PARTICIPANT_LIFECYCLE_BOUNDARY',
    'T14': 'OBSERVATION_OR_RECONCILIATION_ONLY',
}

# Every row describes source facts separately from prospective O8 comparison fitness.
DETAIL = {
    'T1': dict(actor='Trusted provisioning/retirement authorities, NATIVE_REGISTRY_WRITER, HOST_PLATFORM and independent observers; not an operational participant spawn API',
        slot='POSTMASTER triggers the complete seven-slot qualified ACTIVE replacement closure', generation='All seven old generations retired; fresh generation identities and requalification required',
        credential='Six private instance renewals plus POSTMASTER expected endpoint renewal; not an O8 constituent list', temporal='Old qualified ACTIVE/sealed cohort through retirement barriers to fresh qualified cohort; cross-domain interleavings not fully ordered',
        verb='REPLACES through multiple lifecycle events',
        relevance='Old/new credential-relevant qualified states are explicit, but a compound cannot be certified by endpoint comparison alone',
        reason='Six compound criteria not all established, especially no hidden intermediate continuity. Not excluded by alleged impossibility of every partial-order compound.', refs=['S10','S13','S14']),
    'T2': dict(actor='NATIVE_REGISTRY_WRITER; HEALTH_GUARD observes and HOST_PLATFORM independently observes guard/journal',
        slot='POSTMASTER registry entity; native-participant-generic edge', generation='Same registry entity generation; independently current high-water required',
        credential='Registry canonical tuple has credential_ref/enrollment_identity; current enrollment required by custody contract; protected bootstrap precedes eligibility',
        temporal='Own retained birth precedes valid enrollment; registry ENROLLED precedes same-entity REVOKED; ACTIVE ordering remains UNKNOWN', verb='ACTIVATES registry enrollment',
        relevance='Source explicitly relates credential currentness to enrollment. Comparing abstract O8 before/after does not make credential_ref an O8 constituent.',
        reason='Prospective registry eligibility comparison boundary; source supplies both states and direct credential relevance without requiring participant substitution.', refs=['S6','S9','S10','S18']),
    'T3': dict(actor='HOST_PLATFORM independently verifies phase gate; participant cannot self-weaken policy or return to bootstrap',
        slot='POSTMASTER execution subject; generic phase edge', generation='Exact qualified process/current generation; no generation increment inferred at admission',
        credential='Protected import before ACTIVE; fresh slot/purpose/generation policy and ACTIVE-scoped operations',
        temporal='Birth and confinement precede own ACTIVE admission; registry ENROLLED versus ACTIVE remains UNKNOWN', verb='ACTIVATES operational execution phase',
        relevance='Comparison across entry into a credential-bearing operational phase is meaningful prospectively even if all relevant O8 state later proves continuous.',
        reason='Prospective phase admission boundary, distinct from registry enrollment and generation succession.', refs=['S3','S4','S5','S10','S20']),
    'T4': dict(actor='Execution phase authority/confinement system; exact initiator of this phase edge UNKNOWN, not equated with registry writer',
        slot='Same POSTMASTER execution subject; generic phase edge', generation='No fresh generation or successor inferred from execution REVOKED',
        credential='Exit from source-designed credential-bearing ACTIVE operations; exact key retirement/zeroization timing at this edge UNKNOWN',
        temporal='Same subject ACTIVE admission precedes its execution REVOKED; no order or equality with registry/generation revocation inferred', verb='REVOKES execution phase eligibility only',
        relevance='Prospective comparison at exit from ACTIVE can ask about O8 persistence without asserting that O8 changes or the key is destroyed.',
        reason='Retained symmetrically with T3 as phase-exit comparison. Does not require coincident credential invalidation; absence of ACTIVE rules is not physical enforcement evidence.', refs=['S3','S5','S10','S20']),
    'T5': dict(actor='NATIVE_REGISTRY_WRITER; HEALTH_GUARD/HOST independent observation; HOST custody teardown separate',
        slot='POSTMASTER registry entity; generic participant registry edge', generation='Same enrollment generation invalidated, not a fresh generation',
        credential='Registry revocation requires monotonic invalidation; every old receipt/credential/channel remains ineligible',
        temporal='Same entity ENROLLED before REVOKED before EXTINCT; old enrollment revoked before approved fresh replacement eligibility', verb='REVOKES registry eligibility',
        relevance='Explicit source credential invalidation relates pre/post eligibility; no assertion of physical material destruction.',
        reason='Prospective enrollment invalidation comparison; different entity/domain from phase and generation revocation.', refs=['S6','S10','S18']),
    'T6': dict(actor='NATIVE_REGISTRY_WRITER; independent HEALTH_GUARD/HOST observation',
        slot='POSTMASTER slot generation ledger, generic native ledger edge', generation='CURRENT becomes REVOKED; no high-water rollback/fallback; no successor automatically created',
        credential='Exact independently current generation mandatory; monotonic invalidation before fresh eligibility',
        temporal='CURRENT→REVOKED before TOMBSTONED→NEW_GENERATION path; no registry/phase simultaneity inferred', verb='REVOKES generation eligibility',
        relevance='Generation-bound credential eligibility has explicit before/after status independently of material bytes or principal identity.',
        reason='Prospective generation invalidation comparison, not synonym for T5 or T4.', refs=['S6','S10','S11','S19']),
    'T7': dict(actor='NATIVE_REGISTRY_WRITER and independent observers',
        slot='POSTMASTER generation ledger; generic edge', generation='Already REVOKED becomes irreversibly TOMBSTONED; prior tombstone retained',
        credential='Already ineligible credentials remain ineligible; durable anti-rollback metadata is required, not secret destruction',
        temporal='Same ledger revocation before tombstoning before new generation; no physical death/proof simultaneity', verb='RECORDS/SEALS irreversible generation retirement',
        relevance='Irreversible anti-rollback retirement relates credential eligibility to durable generation history. An abstract O8 comparison at sealing is possible without assuming any O8 change or tombstone membership.',
        reason='Prospective durable retirement comparison. As for T4, neither a coincident material/eligibility change nor a new successor is a qualification prerequisite.', refs=['S6','S18','S19']),
    'T8': dict(actor='NATIVE_REGISTRY_WRITER with independent HEALTH_GUARD/HOST witnesses; trusted provisioning remains separate',
        slot='Same POSTMASTER ledger natural key qualification/incarnation/epoch/slot; generic native succession edge', generation='Checked predecessor+1 high-water; prior tombstone retained; new generation before new enrollment',
        credential='Exact generation binding and restart rule: fresh generation/key or endpoint only after old reconciliation/extinction/tombstone',
        temporal='Predecessor revoked/tombstoned and old extinction/reconciliation barriers before approved new eligibility; no full birth/allocation/ACTIVE ordering invented', verb='SUCCEEDS generation identity',
        relevance='Explicit predecessor/successor generation relation supports prospective O8 comparison; predecessor O8 reference can remain meaningful after physical endpoint extinction.',
        reason='Prospective ledger succession boundary without assuming this is the original historical inheritance event or that ledger mutation itself creates a process/key.', refs=['S6','S10','S13','S19']),
    'T9': dict(actor='NATIVE_REGISTRY_WRITER records independently observed extinction; physical observer/subject kept distinct',
        slot='POSTMASTER participant registry entity; generic recognition', generation='Retired enrollment generation; does not create successor',
        credential='Extinction recognition supports retirement barrier; not a material destruction operation', temporal='Registry REVOKED before EXTINCT; physical extinction versus recording time UNKNOWN', verb='OBSERVES/RECORDS extinction',
        relevance='Evidence about old subject, not proof this observation is the O8 state transition.', reason='Recognition must not be promoted to the physical event recognized.', refs=['S6','S10','S18']),
    'T10': dict(actor='Independent extinction observer and NATIVE_REGISTRY_WRITER; claimant boolean insufficient',
        slot='POSTMASTER retired generation tombstone; generic proof completion', generation='Retired generation proof state only',
        credential='Extinction receipt proves a prerequisite for fresh credentials; receipt is not itself private credential state', temporal='Pending extinction proof becomes proven; exact physical death instant/order with T9 UNKNOWN', verb='OBSERVES/COMPLETES extinction proof',
        relevance='Changes knowledge/proof state, not established change of O8 itself.', reason='Do not equate evidence availability with physical or credential transition.', refs=['S6','S10','S21']),
    'T11': dict(actor='HOST_PLATFORM confinement/verification authority; no participant self-return to bootstrap',
        slot='POSTMASTER execution subject; generic confinement', generation='Pre-enrollment process subject; no fresh generation automatically asserted',
        credential='Signed bootstrap FD/environment inventory controls inheritance channels; precise allocation/import order at confinement UNKNOWN', temporal='TRUSTED_BOOTSTRAP before CONFINED_PRE_ENROLLMENT before ACTIVE', verb='CONFINES participant execution',
        relevance='Infrastructure controlling possible channels; no established credential-state succession at this precise edge.', reason='Neither endpoint is ACTIVE; confinement does not itself establish O8 on both sides or a credential admission/succession event.', refs=['S3','S4','S5']),
    'T12': dict(actor='HOST_PLATFORM trusted custodian/endpoint provisioning; recipient may not select target/channel',
        slot='POSTMASTER endpoint subject, generic protected delivery policy with POSTMASTER-specific manifest form', generation='Explicit pre-enrollment inventory bound to intended exact generation; not free operational transfer',
        credential='Protected bootstrap assignment/delivery allowed; operational transfer/duplication/inheritance forbidden by existing custody contract', temporal='Before eligibility; precise relation to birth/confinement/allocation UNKNOWN except retained-parent authentication prerequisites', verb='DELIVERS/ASSIGNS approved bootstrap inventory',
        relevance='Explicit protected credential assignment supplies before/after delivery states. Pre-delivery inventory status is a meaningful comparison point without assuming custody/material belongs to O8 or harmful inheritance occurred.', reason='Prospective protected bootstrap delivery comparison; authorized delivery need not be harmful inheritance. No recipient principal succession or new credential-eligibility change is required by the uniform standard.', refs=['S10','S11']),
    'T13': dict(actor='Approved SUPERVISOR retained parent under trusted fixed pre-enrollment plan; HOST not operational substitute parent',
        slot='Fresh POSTMASTER subject; generic native process birth, not arbitrary engine-child exception', generation='Fresh retained process identity distinct from enrollment and ledger record; exact allocation timing UNKNOWN',
        credential='Birth inventory controlled; principal birth neither creates a credential by definition nor proves old-state transfer', temporal='Own retained birth precedes valid enrollment/ACTIVE; no full order versus material allocation', verb='CREATES process subject',
        relevance='Before fresh birth no recipient process exists; no source-backed same-O8 predecessor relation from principal birth alone.', reason='Participant lifecycle, not credential identity. Reclassifying by birth alone would collapse principal identity into credential identity.', refs=['S5','S12','S13']),
    'T14': dict(actor='Distinct independent exact-outcome observer; writer records evidence, never claimant success boolean/timeout',
        slot='POSTMASTER-related pending work when applicable; generic work publication edge', generation='Preserves original work generation/pending tuple; no fresh eligibility by retry',
        credential='No key/channel adoption while UNKNOWN; reconciliation can lift uncertainty barrier but is not a transfer', temporal='After UNKNOWN work outcome, before fresh eligibility where applicable; not mandatory if outcomes already independently known', verb='RECONCILES/OBSERVES exact work outcome',
        relevance='Observes an earlier event, not by itself the transition observed.', reason='Knowledge-state resolution must not be selected as physical credential inheritance by receipt existence.', refs=['S6','S7','S10','S18']),
}


def qualification():
    rows = read(PREVIOUS / 'transition-candidates.json')['candidates']
    for row in rows:
        ident = row['TRANSITION_ID']
        d = DETAIL[ident]
        row.update({
            'classification': CLASS[ident], 'classification_reason': d['reason'],
            'source_refs': list(dict.fromkeys(row['source_refs'] + d['refs'])),
            'actor_principal': d['actor'], 'participant_slot': d['slot'],
            'credential_state': d['credential'], 'generation_identity': d['generation'],
            'temporal_position': d['temporal'], 'event_effect': d['verb'],
            'O8_relevance_analysis': d['relevance'],
            'O8_exists_meaningfully_before_and_after': 'POTENTIALLY_COMPARABLE_ABSTRACT_STATES_NOT_INSTANTIATED_PROOF' if ident in TARGETS or ident == 'T1' else 'NOT_ESTABLISHED_AS_TARGET_COMPARISON',
            'O8_continuity_observable': 'UNKNOWN_PHYSICAL_OBSERVABILITY; later independent semantic predicate and evidence required',
            'O8_discontinuity_observable': 'UNKNOWN_PHYSICAL_OBSERVABILITY; source record difference alone is insufficient',
            'necessary_for_credential_inheritance': 'UNKNOWN',
            'sufficient_for_credential_inheritance': 'UNKNOWN',
            'inheritance_without_this_boundary': 'UNKNOWN; not inferred impossible',
            'boundary_without_credential_inheritance': 'Not ruled out; target inheritance predicate remains undefined. This is a logical distinction, not an observed compliant trace.',
            'specific_to_POSTMASTER': 'NO_EXCLUSIVE_EVENT_TYPE; analysis scopes existing generic edge/workflow to POSTMASTER without resolving its context predicate',
            'native_participant_generic': True,
            'lifecycle_infrastructure_or_target': 'Source lifecycle boundary proposed for prospective target designation only; not historically certified' if ident in TARGETS else CLASS[ident],
            'qualification_standard': 'A prospective candidate needs a bounded source event and credential-relevant comparison relation, not proof inheritance occurred. UNKNOWN concrete O8 predicates remain UNKNOWN.',
        })
    write('qualification-matrix.json', {'source_boundaries_total': 14, 'rows': rows,
        'classification_exclusive': True,
        'target_status': 'CANDIDATES_FOR_FUTURE_AUTHORITY_ONLY_NOT_SELECTED_OR_RUNTIME_QUALIFIED',
        'no_automatic_promotion_of_all_14': True})


def relations():
    prior = read(PREVIOUS / 'transition-event-relations.json')
    assert len(prior['pairs']) == 91
    write('event-relation-matrix.json', {
        'pairs': prior['pairs'], 'pair_count': 91,
        'provenance': {'path': relative(PREVIOUS / 'transition-event-relations.json'), 'sha256': digest(PREVIOUS / 'transition-event-relations.json'), 'pointer': '/pairs'},
        'independent_C5A_assessment': 'All 91 identities and source-domain orders retained after checking S3/S6/S10/S12/S13/S18/S19. No new SAME_EVENT proof. Required workflow results are not identical to one edge.',
        'source_temporal_constraints': read(PREVIOUS / 'transition-temporal-order.json'),
        'ordering_limit': 'Same-entity path order is not cross-domain simultaneity. In particular T2 versus T3, and T4/T5/T6, remain UNKNOWN_RELATION. T8 before new enrollment alone does not prove T8 before ACTIVE.',
        'conditional_reconciliation': 'T14 edge required only when relevant old outcome is UNKNOWN; replacement barrier still mandatory. Known outcomes require independent positive evidence, not absent rows.',
        'no_events_merged': True})


def alternatives():
    rows = read(HERE / 'qualification-matrix.json')['rows']
    capabilities = {
        'T2': 'Registry enrollment eligibility at a particular current entity/revision, without equating enrollment with executable ACTIVE phase.',
        'T3': 'Entry into operational ACTIVE phase after independent confinement gate, without making registry ENROLLED the same event.',
        'T4': 'Exit from operational ACTIVE phase, without asserting key zeroization or registry/generation invalidation at that instant.',
        'T5': 'Invalidation of an enrolled participant entity and its old credential/channel eligibility, without requiring a generation-ledger mutation to be simultaneous.',
        'T6': 'Generation-level currentness invalidation independently of participant registry and execution phase.',
        'T7': 'Irreversible durable retirement/anti-rollback sealing after revocation, without treating public tombstone bytes as O8 or equating sealing with secret destruction.',
        'T8': 'Explicit predecessor/successor generation high-water advancement with retained tombstone, before new enrollment, rather than operational activation.',
        'T12': 'Explicit trusted pre-enrollment credential delivery/assignment, independently of later admission, material creation and principal substitution.',
    }
    out = []
    for row in rows:
        ident = row['TRANSITION_ID']
        if ident not in TARGETS:
            continue
        subject = 'POSTMASTER execution subject' if ident in ['T3','T4'] else 'POSTMASTER participant registry entity' if ident in ['T2','T5'] else 'Exact intended POSTMASTER bootstrap inventory/delivery subject' if ident == 'T12' else 'POSTMASTER slot generation ledger natural key'
        out.append({
            'alternative_id': ident, 'source_event': row['TRANSITION_NAME'], 'source_refs': row['source_refs'],
            'prospective_definition': {
                'authority_status': 'PROPOSED_FOR_LATER_PROJECT_AUTHORITY_APPROVAL_ONLY',
                'designation_text': 'For prospective POSTMASTER credential-state continuity analysis, designate only the following source-defined comparison boundary. Compare abstract O8 immediately before and immediately after this event on the independently identified source subject; do not infer which properties of O8 persist or must change.',
                'subject_anchor': subject,
                'PRE_STATE': row['PRE_STATE'], 'TRANSITION_EVENT': row['EVENT'], 'POST_STATE': row['POST_STATE'],
                'subject_anchor_is_not_context_resolution': True,
                'T8_specificity': 'If T8 is later selected: checked previous+1 high-water, durable prior tombstone and source retirement barriers; this event does not itself instantiate a process/key, enroll it, or establish ACTIVE.' if ident == 'T8' else 'NOT_APPLICABLE',
                'T4_specificity': 'Execution phase REVOKED only. Credential retirement, registry/generation invalidation, physical extinction and zeroization are separate and not inferred simultaneous.' if ident == 'T4' else 'NOT_APPLICABLE',
                'independent_later_specifications': ['FORBIDDEN_CONTINUITY', 'REQUIRED_DISCONTINUITY', 'ALLOWED_CONTINUITY'],
                'no_current_continuity_rule': True,
            },
            'semantic_capability': capabilities[ident],
            'O8_compatibility': 'Exact C4B object retained. Source credential references/bindings motivate the comparison, not automatic O8 membership. Concrete O8 state/observability remains unestablished.',
            'I13': 'Full mandatory external concurrent seven-slot/21-pair principal distinction plus auxiliary separation; never an internal O8 member. Across-generation numeric UID delta not inferred.',
            'substitution_non_circularity': 'Neither occurrence nor absence of participant substitution defines this event or inheritance. Necessity/sufficiency remain UNKNOWN; allowed source-native initial/retirement paths must remain representable.',
            'static_witness_fitness': 'Can name pre/event/post in a later static witness without deciding the required outcome from the event alone. Existing required REJECT case is not completed by this dossier.',
            'lifecycle_conflation': 'NO: only the named source edge, not its neighboring events or the whole replacement workflow.',
            'downstream_circularity': 'No need to resolve exact context predicate, O8 property membership, canonical N or atomic obligation partition to name this boundary; those remain separate required decisions.',
            'unresolved_semantic_consequences': [
                'Whether this boundary is the intended prospective target: requires later explicit selection',
                'Whether and which O8 properties are meaningfully observable and continuous/discontinuous across it',
                'Exact POSTMASTER context binding, internal scope/exceptions and exhaustive atomic boundary',
                'Inheritance without substitution/substitution without inheritance; no necessity/sufficiency inference',
                'Source-UNKNOWN cross-machine order and exact allocation/custody/zeroization timing',
                'Physical evidence and enforcement remain future; no source digest substitutes for observation',
            ],
            'selected': False, 'recommended': False, 'historically_designated': False,
        })
    write('prospective-alternatives.json', {
        'alternatives': out, 'count': len(out), 'ordering': 'SOURCE_ID_ORDER_ONLY_NOT_PREFERENCE',
        'non_domination_scope': 'Retain all prospectively fit candidates for which frozen sources provide no strict domination proof. No all-future-semantic-orders or uniqueness theorem claimed.',
        'selection_performed': False, 'ranking_performed': False,
    })


def compound():
    tests = [
        ('explicit_ordering', 'PARTIAL_SOURCE_ORDER_ONLY', 'Registry, phase and generation paths each ordered; cross-domain interleavings remain UNKNOWN. Lack of total order alone does not prove impossibility.'),
        ('identifiable_start_end', 'YES_FOR_SOURCE_WORKFLOW', 'Old qualified ACTIVE/sealed cohort to fresh qualified same-role cohort under full7 replacement closure.'),
        ('representable_intermediate_states', 'SOURCE_STATES_REPRESENTABLE_NOT_COMPLETE_O8_TRACE', 'Separate phase/registry/ledger/tombstone/work-state tuples retained; no collapse to two endpoint digests.'),
        ('no_hidden_credential_continuity', 'NOT_ESTABLISHED', 'No complete source-backed O8 comparison cuts/trace coverage through subevents. Endpoint equality/difference cannot rule out transient preservation/adoption; adding a blanket capture-all rule would invent a new contract.'),
        ('independent_principal_distinction', 'REQUIRED_NOT_WEAKENED', 'Full external I13 remains independently enforceable; physical enforcement future.'),
        ('no_manufactured_history', 'YES_IF_ONLY_PROSPECTIVE', 'C5 event ambiguity and rejected event-identity primary remain preserved.'),
    ]
    write('compound-analysis.json', {
        'examined_workflow': 'T1', 'source_refs': ['S3','S6','S10','S13','S14','S17','S18'],
        'criteria': [dict(criterion=k, result=v, reason=r) for k,v,r in tests],
        'admitted_compounds': [], 'admitted_count': 0, 'result': 'NONE_ADMITTED_ADMISSIBILITY_NOT_ESTABLISHED',
        'other_composition_analysis': 'Same-domain subchains T11→T3→T4, T2→T5→T9 and T6→T7→T8 preserve ordered source states, but none proves no hidden O8 continuity across constituent cuts. Adding delivery/birth/reconciliation likewise does not establish this. Concatenating unknown cross-domain edges does not cure it.',
        'not_claimed': ['Every semantically coherent future compound is impossible', 'UNKNOWN cross-domain order equals independence', 'An accepted compound follows from all individual edges being insufficient'],
        'dependency': 'To admit a compound, authoritative event/cut structure with representable intermediate credential comparison and no-hidden-continuity assurance is required; it cannot be silently supplied by a downstream atomic/scope decision in this gate.'})


def minimality():
    a = read(HERE / 'prospective-alternatives.json')['alternatives']
    pairs = []
    for x, y in itertools.combinations(a, 2):
        ids = (x['alternative_id'], y['alternative_id'])
        domain = 'Same execution phase path, opposite entry/exit directions' if set(ids) == {'T3','T4'} else 'Same participant registry path, opposite enrollment/invalidation directions' if set(ids) == {'T2','T5'} else 'Same generation ledger path, invalidation versus later predecessor/successor advancement' if set(ids) == {'T6','T8'} else 'Distinct source state machines or eligibility scopes; equality/strict containment not proved'
        pairs.append({'A': ids[0], 'B': ids[1], 'source_distinction': domain,
                      'A_unique_comparison_capability': x['semantic_capability'], 'B_unique_comparison_capability': y['semantic_capability'],
                      'strictly_broader_without_necessary_meaning': 'NOT_PROVEN_IN_EITHER_DIRECTION',
                      'strictly_narrower_unable_to_express_known_case': 'NOT_PROVEN_FOR_UNDESIGNATED_TARGET; no candidate purports to encompass every other lifecycle edge',
                      'domination_proof': 'NONE_ESTABLISHED', 'removed': None,
                      'result': 'RETAIN_BOTH_NO_PROOF_BASED_ELIMINATION'})
    rows = read(HERE / 'qualification-matrix.json')['rows']
    write('minimality-analysis.json', {
        'pairwise_tests': pairs, 'pairwise_count': len(pairs),
        'retained': TARGETS, 'domination_eliminations': [],
        'qualification_exclusions': [dict(id=r['TRANSITION_ID'], classification=r['classification'], reason=r['classification_reason']) for r in rows if r['TRANSITION_ID'] not in TARGETS],
        'minimality_claim': 'Smallest set obtainable from these qualified source boundaries by the required proof-based domination rule: no pair has a proven strict domination relation. This is evidence-relative retention, not a proof of eight necessary eventual semantic transitions.',
        'counterexample_to_one_candidate_reduction': 'T8 ledger succession does not express same-generation registry enrollment or entry/exit of ACTIVE; those do not themselves perform high-water succession. Choosing T8 by convenience would discard distinct comparison capability and prejudge substitution.',
        'no_rank_or_winner': True})


CM = [
    ('CM1', 'Participant substitution occurs but credential inheritance does not', 'Conditional semantic countermodel, not a materialized compliant trace: renewal can satisfy all later O8 discontinuity requirements. Never infer harmful inheritance merely from renewed principal/slot/process.', 'SUBSTITUTION_NOT_SUFFICIENT'),
    ('CM2', 'Credential inheritance occurs without participant substitution', 'Conditional semantic countermodel: a later authority may identify relevant continuity across same-participant admission/invalidation. Existing transfer prohibitions remain enforced; this possibility is not an authorized operational path.', 'SUBSTITUTION_NOT_NECESSARY_BY_FIAT'),
    ('CM3', 'Credential material changes but relevant O8 continuity survives', 'Logical conditional on later O8 membership and continuity predicate. Material-byte difference cannot prove O8 discontinuity, and no non-material member is added now.', 'MATERIAL_DIFFERENCE_NOT_O8_PROOF'),
    ('CM4', 'Credential material survives but relevant O8 continuity does not', 'Logical conditional: retained bytes can be unusable after monotonic eligibility loss. Does not authorize retaining secrets or define eligibility as an O8 member.', 'MATERIAL_EQUALITY_NOT_O8_PROOF'),
    ('CM5', 'Principal changes while some credential state remains continuous', 'Keep qualified principal/birth distinction independent of any future O8 equality. Full I13 applies; cross-generation numeric UID change is not automatically required.', 'PRINCIPAL_NOT_CREDENTIAL_IDENTITY'),
    ('CM6', 'Principal remains while credential state is replaced', 'Logical comparison distinction; no source-approved arbitrary same-generation credential rotation API is created. Do not require principal change to express a credential-state comparison.', 'CREDENTIAL_CHANGE_NOT_PRINCIPAL_CHANGE'),
    ('CM7', 'Generation succession occurs before participant activation', 'Separate ledger succession from later enrollment/activation. Source proves checked new generation before new enrollment. ACTIVE versus ENROLLED remains UNKNOWN, so this scenario is a conditional distinction, not a claimed fully sourced total-order trace.', 'NO_GENERATION_ACTIVATION_COLLAPSE'),
    ('CM8', 'Revocation occurs after replacement', 'If replacement means completed approved T1/fresh eligibility and revocation means old enrollment/generation invalidation, the scenario violates frozen retirement-before-new-eligibility requirements and is not a compliant counterexample. If replacement means only birth/delivery, or revocation means another source domain, order must be independently established; no overloaded replacement term.', 'NO_REORDERED_COMPLIANT_T1_FABRICATION'),
    ('CM9', 'Delivery occurs but credential is never admitted', 'A delivery permission is not enrollment or ACTIVE admission. Failed/stopped qualification is not inherited operational authority. No successful deployment trace claimed.', 'DELIVERY_NOT_ADMISSION'),
    ('CM10', 'Admission occurs using independently created credential state', 'Initial approved provisioning illustrates why admission need not be predecessor credential adoption. Exact later O8 interpretation still UNKNOWN; no inheritance outcome declared from event alone.', 'ADMISSION_NOT_INHERITANCE'),
    ('CM11', 'Process birth occurs without inheritance', 'Fresh process birth supplies a retained process subject, not credential identity or inheritance by definition. No new runtime birth performed.', 'BIRTH_NOT_INHERITANCE'),
    ('CM12', 'Reconciliation observes a transition but is not itself the transition', 'UNKNOWN→OBSERVED_PROVEN is exact evidence of outcome, not automatic equality with the observed event. An approved replacement can start with independently known outcomes and need not traverse T14.', 'OBSERVATION_NOT_OBSERVED_EVENT'),
]


def countermodels():
    focus = {
        'T2': 'Track same registry entity PROVISIONAL→ENROLLED; neither delivered inventory nor phase ACTIVE is this edge.',
        'T3': 'Track same execution subject CONFINED_PRE_ENROLLMENT→ACTIVE; no enrollment/ledger equality inferred.',
        'T4': 'Track ACTIVE→REVOKED execution phase only; do not infer key retirement, writer invalidation or destruction.',
        'T5': 'Track ENROLLED→REVOKED registry eligibility; no physical credential erasure or fresh process required by this edge alone.',
        'T6': 'Track CURRENT→REVOKED generation validity; no successor/birth/phase transition follows by definition.',
        'T7': 'Track REVOKED→TOMBSTONED irreversible retirement; no assertion about private material destruction or O8 membership.',
        'T8': 'Track TOMBSTONED→NEW_GENERATION checked lineage; no enrollment/ACTIVE or credential continuity result inferred.',
        'T12': 'Track protected bootstrap delivery/assignment before eligibility; not an operational transfer or enrollment event.',
    }
    event_meaning = {
        'T2': 'registry enrollment', 'T3': 'entry into ACTIVE', 'T4': 'exit from ACTIVE',
        'T5': 'registry invalidation', 'T6': 'generation currentness loss',
        'T7': 'durable anti-rollback sealing', 'T8': 'checked generation succession',
        'T12': 'protected bootstrap delivery/assignment',
    }

    def occurrence(alt, cm):
        event = event_meaning[alt]
        if cm == 'CM1':
            return 'UNKNOWN_FROM_SUBSTITUTION_WORD_ALONE', f'{event} must be independently identified. A completed approved T1 has mandatory fresh/retirement results, but a generic substitution statement is not proof of this exact edge or of harmful inheritance.'
        if cm == 'CM2':
            return 'UNKNOWN_CONDITIONAL_ON_LATER_TARGET_SEMANTICS', f'A same-participant {event} comparison remains expressible where source subject permits; whether inheritance can occur there is not established. Absence of participant substitution neither removes nor proves {alt}.'
        if cm == 'CM3':
            return 'UNKNOWN_MATERIAL_CHANGE_NOT_EVENT_PROOF', f'Changed bytes do not establish {event}; if {alt} also occurs, the candidate compares O8 without treating changed material as sufficient discontinuity.'
        if cm == 'CM4':
            return 'UNKNOWN_MATERIAL_PERSISTENCE_NOT_EVENT_PROOF', f'Unchanged bytes do not prevent {event}. If {alt} occurs with independently established eligibility/history differences, O8 continuity still requires its later predicate; no preservation permission is created.'
        if cm == 'CM5':
            return 'UNKNOWN_FROM_PRINCIPAL_CHANGE_ALONE', f'A changed principal is not {event}; {alt} still requires its own source event witness. No principal equality or numeric UID delta decides O8 continuity.'
        if cm == 'CM6':
            return 'UNKNOWN_FROM_CREDENTIAL_REPLACEMENT_ALONE', f'A retained principal does not rule out a state comparison at {event}. Source authorization of an arbitrary rotation is not inferred; {alt} is present only if its own edge independently occurs.'
        if cm == 'CM7':
            if alt == 'T8':
                return 'PRESENT_IF_SUCCESSION_MEANS_SOURCE_T8', 'The named generation edge may be present while activation has not occurred. Its before-enrollment order is source-proven; no full enrollment-versus-ACTIVE order is inferred.'
            if alt == 'T3':
                return 'ABSENT_AT_THE_STIPULATED_PRE_ACTIVATION_CUT', 'If activation means this same successor execution ACTIVE admission, T3 has not yet occurred at the cut. Succession does not itself perform admission; it may occur later.'
            if alt == 'T2':
                return 'UNKNOWN_AT_GENERIC_PRE_ACTIVATION_CUT', 'At the exact T8 edge the successor enrollment is still future by source rule. At a later generic pre-ACTIVE cut, T2 status remains UNKNOWN because registry-versus-ACTIVE order is not established.'
            return 'UNKNOWN_FOR_THIS_DOMAIN_OR_SUBJECT', f'The scenario alone does not identify {event} for predecessor versus successor. Ledger predecessor revocation/tombstone requirements do not establish all execution/delivery ordering or subject equality.'
        if cm == 'CM8':
            if alt in ['T5','T6']:
                return 'OUT_OF_APPROVED_PATH_IF_OLD_INVALIDATION_AFTER_COMPLETED_T1', f'If delayed revocation denotes old {event}, a completed approved replacement cannot be used as a compliant counterexample; old invalidation must precede fresh eligibility. Other meanings require separate evidence.'
            if alt == 'T4':
                return 'UNKNOWN_PHASE_ORDER_NOT_WRITER_INVALIDATION', 'Execution REVOKED cannot be equated with registry/generation invalidation. A generic after-replacement statement does not establish this phase ordering; a compliant T1 with delayed old writer invalidation is rejected.'
            return 'UNKNOWN_UNLESS_REPLACEMENT_AND_REVOCATION_DOMAINS_FIXED', f'If replacement means completed T1 and old writer invalidation is late, the trace violates source prerequisites regardless of {event}. If it means only birth/delivery, neither completion nor {alt} is proved.'
        if cm == 'CM9':
            if alt == 'T12':
                return 'PRESENT_IF_DELIVERY_IS_APPROVED_T12', 'Protected bootstrap delivery may occur and be followed by stopped/failed qualification. Present T12 does not establish registry or ACTIVE admission or inheritance.'
            if alt == 'T2':
                return 'ABSENT_IF_NEVER_ADMITTED_MEANS_REGISTRY_ENROLLMENT_ELSE_UNKNOWN', 'Delivery alone cannot make PROVISIONAL become ENROLLED. If non-admission refers only to ACTIVE, registry status remains UNKNOWN; do not collapse the domains.'
            if alt == 'T3':
                return 'ABSENT_IF_NEVER_ADMITTED_MEANS_ACTIVE_ADMISSION_ELSE_UNKNOWN', 'If operational admission never happens, T3 is absent. A registry-only admission statement cannot decide execution status; delivery alone does not prove ACTIVE.'
            return 'UNKNOWN_DELIVERY_DOES_NOT_ENTAIL_THIS_EDGE', f'Delivery followed by no admission does not prove {event}. Fresh-generation/retirement events may have other prerequisites; no automatic order or completion follows.'
        if cm == 'CM10':
            if alt == 'T2':
                return 'PRESENT_IF_ADMISSION_IS_REGISTRY_ENROLLMENT_ELSE_UNKNOWN', 'Independently created approved credential state can accompany registry enrollment without predecessor adoption. Execution admission alone does not prove the registry edge.'
            if alt == 'T3':
                return 'PRESENT_IF_ADMISSION_IS_ACTIVE_ELSE_UNKNOWN', 'Independently created approved credential state can enter ACTIVE through T3 without inheritance being proved. Registry enrollment alone does not establish T3.'
            return 'UNKNOWN_ADMISSION_IS_NOT_THIS_EVENT', f'Independent material creation/admission does not imply {event}; it neither refutes this source edge nor makes it necessary for inheritance. T12, if needed, must be separately established as delivery rather than creation.'
        if cm == 'CM11':
            return 'UNKNOWN_BIRTH_ALONE_DOES_NOT_ENTAIL_EDGE', f'Fresh retained process birth is T13, not {event}. {alt} requires its own event and subject anchoring even if birth is an eventual prerequisite for valid subject admission; no inheritance is inferred from birth.'
        assert cm == 'CM12'
        return 'UNKNOWN_OBSERVATION_DOES_NOT_IDENTIFY_OBSERVED_EDGE', f'Reconciliation T14 can establish an exact outcome without itself being {event}. If its evidence concerns {alt}, occurrence must be established from that evidence, not from the receipt label; otherwise {alt} remains UNKNOWN.'

    rows = []
    for alt in TARGETS:
        for ident, scenario, reasoning, distinction in CM:
            status, implication = occurrence(alt, ident)
            rows.append({'alternative': alt, 'countermodel': ident, 'scenario': scenario,
                         'candidate_specific_test': focus[alt], 'reasoning': reasoning,
                         'boundary_occurrence_analysis': status,
                         'candidate_specific_implication': implication,
                         'distinction_preserved': distinction,
                         'definition_attack_result': 'NO_CONTRADICTION_FOUND_IN_BOUNDARY_DEFINITION_UNDER_STATED_CONDITIONS',
                         'observed_or_executed': False, 'O8_outcome': 'UNKNOWN_UNTIL_SEPARATE_SEMANTIC_CONTRACT',
                         'accounting': 'DOSSIER_CONCEPTUAL_DISTINCTION_TEST_NOT_CATALOG_ATTACK'})
    write('countermodel-analysis.json', {'records': rows, 'alternatives_total': len(TARGETS), 'tests_per_alternative': 12,
        'conceptual_distinction_tests_total': len(rows), 'source_realizable_runtime_traces_claimed': 0,
        'attacks_materialized': 0, 'attacks_evaluated': 0,
        'interpretation': 'Survival means the boundary definition does not collapse the attacked distinction; it is not a PASS of unknown O8 semantics or physical enforcement.'})


def report():
    rows = read(HERE / 'qualification-matrix.json')['rows']
    text = '''# Package0090 C5A resumption — bounded transition decision dossier

Outcome A: DECISION_DOSSIER_COMPLETE, subject to completed independent dossier-quality review recorded alongside this report. Eight unranked prospective comparison boundaries are retained: T2, T3, T4, T5, T6, T7, T8, T12. None is selected. No unique historical transition is recovered. C5 Outcome B remains truthful: this dossier proposes future designations rather than attributing original intent.

## Authority and preflight

User explicitly reconciled `451265ff5b3d286eb4d27c4b3817c2f558f30123` as a documentary/preservation checkpoint, including two LFS rules only. Frozen implementation/semantic baseline remains `cbc284f62d9bd09b7169b55c8d66a3c51a68c6cb`, an ancestor. The previous 617 paths are preserved in that checkpoint. The only previous baseline byte delta is the authorized root `.gitattributes` preservation configuration. Seven local C5A STOP artifacts remain untouched, local and without semantic authority. All 9,106 preexisting worktree files are hash-frozen for this resumption. No remote or LFS validation is rerun; the earlier remote closure is user-reported authority, not a new measurement.

The 617 paths retain their classifications: 578 historical authorized evidence, seven original C5 STOP, 30 completed C5 resumption, and two parallel post-MVP files. Seven additional local C5A STOP paths are recorded separately. No unexplained artifact was found. Post-MVP files are hash-only preservation inputs and have zero semantic authority. No old evidence, implementation, V043 or protected configuration is edited.

## Qualification of all original boundaries

Classification is exclusive. A target candidate is prospectively fit to name a bounded source comparison, not a declaration that O8 has been instantiated, observed or inherited. Unknown physical observability and O8 extent remain unknown. Source credential references and validity bindings are relevance evidence, never automatic O8 membership. All 14 rows independently record actor, slot, credential state, generation, timing, effect, O8 comparisons and unknown necessity/sufficiency.

| ID | Boundary | Classification |
|---|---|---|
'''
    for row in rows:
        text += f"| {row['TRANSITION_ID']} | {row['TRANSITION_NAME']} | {row['classification']} |\n"
    text += '''
## Exact prospective alternatives, without selection

The proposed authority text common to every alternative is: **For prospective POSTMASTER credential-state continuity analysis, designate only the following source-defined comparison boundary. Compare abstract INHERITED_CREDENTIAL_STATE immediately before and immediately after this event on the independently identified source subject. Do not infer which O8 properties persist or must change.** This text is a proposal awaiting later explicit authority, not an amendment to accepted semantics.

| ID | PRE → EVENT → POST | Comparison capability |
|---|---|---|
| T2 | Registry PROVISIONAL → source enrollment → ENROLLED | Enrollment-bound credential eligibility on the same entity/revision |
| T3 | Execution CONFINED_PRE_ENROLLMENT → independently gated admission → ACTIVE | Entry into credential-bearing operational phase |
| T4 | Execution ACTIVE → phase revocation → REVOKED | Exit from that phase, without asserting coincident key destruction or writer invalidation |
| T5 | Registry ENROLLED → monotonic registry revocation → REVOKED | Loss of enrollment-bound credential/channel eligibility |
| T6 | Generation CURRENT → ledger revocation → REVOKED | Loss of generation currentness, distinct from phase/registry status |
| T7 | Generation REVOKED → durable retirement sealing → TOMBSTONED | Irreversible anti-rollback boundary, without equating public metadata with O8 |
| T8 | Generation TOMBSTONED → checked previous+1 succession → NEW_GENERATION | Predecessor/successor high-water boundary with durable prior tombstone, before new enrollment |
| T12 | Before protected bootstrap delivery/assignment → authenticated delivery → after delivery before eligibility | Inventory delivery boundary, distinct from creation and admission |

Each proposal keeps FORBIDDEN_CONTINUITY, REQUIRED_DISCONTINUITY and ALLOWED_CONTINUITY independently specifiable later. T8 is not process/key creation or activation. T4 is not credential zeroization, registry revocation or physical extinction. Subject anchoring uses existing source entity domains; it does not resolve the outstanding POSTMASTER context predicate. Existing source prohibitions on adoption, stale credentials and operational transfer remain mandatory; this dossier does not turn them into a complete O8 member list.

The order above follows source IDs and encodes no preference. No ranking, recommendation, winner or unique cardinality claim is made.

## Exclusions and compound analysis

T1 has credible old/new source endpoints but is not admitted as one compound transition. Source partial orders and intermediate state tuples remain representable; a missing total order alone is not proof of impossibility. The decisive unestablished criterion is protection against hidden O8 continuity at intermediate cuts. Endpoint equality/difference is insufficient. A blanket new capture-all observation rule would manufacture a contract. No compound is admitted, and no universal impossibility of every future compound is claimed.

The first draft excluded T7/T12 under stricter conditions than it applied to T4. Independent review rejected that asymmetry. The draft and findings are preserved in `draft-review-rejected/`. The corrected uniform criterion requires a bounded source event plus credential-relevant comparison relation, without requiring a coincident O8 change, new principal or harmful inheritance. T7 therefore remains a candidate for irreversible anti-rollback sealing; T12 remains a candidate for protected delivery/assignment. Public tombstones and custody are not automatically O8 members. T9/T10 recognize or prove extinction and T14 reconciles an outcome; evidence arrival is not the observed physical transition. T11 confinement controls channels but does not establish a credential-state succession at that exact edge. T13 process birth does not establish credential identity or a recipient O8 predecessor. These exclusions are present source-qualification limits, not proof no future explicit redesign could relate those boundaries to O8. No candidate is removed by an invented domination relation.

## Relations, minimality and adversarial distinctions

All 91 unordered boundary pairs preserve the corrected C5 source relations and provenance. No SAME_EVENT is newly proved. T2/T3 order and T4/T5/T6 equivalence/order remain UNKNOWN. Same-state-machine paths retain their explicit ordering. New generation before enrollment does not establish full ordering against ACTIVE. T14 is a conditional edge when an outcome is UNKNOWN; the independent-known-outcome barrier remains mandatory.

Twenty-eight pairwise non-domination tests retain all eight qualified alternatives because no source proves strict domination. Registry admission is not phase admission; entry is not exit; registry invalidation is not generation invalidation; neither is checked generation succession. This is evidence-relative minimality under the required proof-based removal rule, not a theorem that eight eventual semantic transitions are necessary. No candidate must express every other lifecycle event or the whole T1 workflow.

Each alternative receives CM1–CM12: 96 conceptual distinction tests, zero catalog attacks or executed traces. Substitution is neither sufficient nor necessary by fiat; material equality/change does not decide O8 equality/change; principal and credential identities remain distinct; delivery is not admission; birth is not inheritance; observation is not the event observed. Each row states whether its named boundary is conditionally PRESENT, conditionally ABSENT, UNKNOWN or outside the approved path, with a candidate-specific implication. No row asserts a positive harmful-inheritance trace. CM3/CM4 remain conditional on future O8 semantics. CM8 explicitly rejects completed approved T1 with old invalidation delayed past fresh eligibility as a compliant counterexample. No source-realizable runtime trace or harmful event is manufactured.

## Preserved unresolved decisions and accounting

O8 remains exactly the C4B designation with automatic aggregation forbidden. Full mandatory external I13 remains independent: concurrent seven-slot/21-pair principal distinction and auxiliary separation, not a credential-family member or a rule that numeric UIDs must change across generations. No participant substitution assumption establishes the open witness.

TRANSITION remains unresolved; POSTMASTER_CONTEXT_BINDING, INTERNAL_SCOPE_AND_EXCEPTIONS and EXHAUSTIVE_ATOMIC_BOUNDARY remain unresolved. Four architectural decisions remain. Internal universe N and denominator remain unestablished; D1/D2/D3 remain unvalidated; 108 candidate records/105 ambiguities unchanged. The existing 350 attack denominator is frozen and is not O8 semantics. N1 qualification CLOSED, substitution OPEN, decisions 12 = 11 closed + one open. V2 proof FAIL/status BLOCKED.

Independent reviews concern dossier quality only and cannot approve a transition or unknown O8 outcome. Execution fences: no implementation/build/native runtime/SQL/database/V043/B02, no role/credential creation, no git add/commit/push. Only new C5A-resumption evidence is written.

NEXT_GATE=PROJECT_AUTHORITY_TRANSITION_DESIGNATION. NEXT_EXECUTED=false. Stop after C5A; no selection is performed here.
'''
    path = ROOT / 'docs/evidence/PACKAGE-0090-B01-v2-native-static-closure-r5n2a5-3c5a-resumption.md'
    path.write_text(text, encoding='utf-8')


def validate_static():
    q = read(HERE / 'qualification-matrix.json')['rows']
    assert len(q) == 14 and len({r['TRANSITION_ID'] for r in q}) == 14
    assert [r['TRANSITION_ID'] for r in q if r['classification'] == 'TARGET_TRANSITION_CANDIDATE'] == TARGETS
    assert len(read(HERE / 'event-relation-matrix.json')['pairs']) == 91
    cm = read(HERE / 'countermodel-analysis.json')['records']
    assert len(cm) == 96 and len({(r['alternative'], r['countermodel']) for r in cm}) == 96
    assert all(not r['observed_or_executed'] for r in cm)
    assert not read(HERE / 'compound-analysis.json')['admitted_compounds']
    assert len(read(HERE / 'minimality-analysis.json')['pairwise_tests']) == 28
    assert all(not r['selected'] and not r['recommended'] for r in read(HERE / 'prospective-alternatives.json')['alternatives'])
    pre = read(HERE / 'preflight.json')
    assert all(digest(ROOT / p) == h for p,h in pre['preexisting_sha256'].items())
    assert not git('diff', '--name-only') and not git('diff', '--cached', '--name-only')
    assert git('rev-parse','HEAD') == pre['documental_checkpoint']
    return len(pre['preexisting_sha256'])


if __name__ == '__main__':
    assert ROOT == pathlib.Path('C:/Projects/flooow-genesis-git')
    sources()
    qualification()
    relations()
    alternatives()
    compound()
    minimality()
    countermodels()
    report()
    print('DRAFT_CONSTRUCTED; STATIC_STRUCTURAL_CHECKS=PASS; PREEXISTING_HASHES=' + str(validate_static()))
