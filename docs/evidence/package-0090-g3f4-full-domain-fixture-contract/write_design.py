"""Design documents and machine-readable native contracts, no runtime operations."""
from pathlib import Path
import json
HERE=Path(__file__).parent
def md(name,s):
    p=HERE/name;assert not p.exists();p.write_bytes(s.encode())
def main():
    work={'POSTMASTER':('Successful server-derived generation/catalog probe','Server start identity + fresh consistent catalog snapshot independently queried'),'SUPERVISOR':('Completed spawn/enrollment/dependency validation','Observer checks retained child anchor, generation ledger publication and target process identity'),'RECEIVER':('Completed bound enrollment decision','Observer checks fresh challenged decision transcript and authoritative promotion registry revision; loop tick/ping insufficient'),'CENSUS_OBSERVER':('Completed applicable catalog reconciliation','Independent query checks snapshot epoch, membership/revision CAS and reconciled identities; pre-query tick insufficient'),'APPROVAL_PRODUCER':('Published fully verified immutable approval generation','Consumer independently verifies exact original signature, full context and committed publication digest'),'APPROVAL_CONSUMER':('Successfully consumed current verified approval generation','External guard cross-checks immutable publication, verification result and current registry decision'),'ENFORCEMENT_WORKER':('Completed target-bound control action','External guard verifies retained target anchor and actual observed outcome; signal-send ACK alone insufficient')}
    participants=[]
    for name,(progress,witness) in work.items():
        participants.append({'PARTICIPANT_NAME':name,'IDENTITY_SOURCE':'Trusted bootstrap OS process creation + atomic pidfd anchor; server-derived start/database facts for postmaster','IDENTITY_BINDING':'Exact boot_id, namespace/cgroup/container identity, start identity, pidfd target, deployment/incarnation and participant slot; never caller-supplied PID/OID','GENERATION_SOURCE':'Trusted bootstrap allocates a fresh independent slot generation on each replacement before admission','GENERATION_BINDING':'Tuple incarnation+slot+generation+OS anchor+channel; observers compare exact current ledger revision','LIVENESS_SOURCE':'Independent pidfd existence observation plus authenticated original BOOTTIME emission with boot epoch; stale queued heartbeat never renews','PROGRESS_SOURCE':progress,'COMPLETED_WORK_WITNESS':witness,'INDEPENDENT_OBSERVER':'HEALTH_GUARD; HOST_PLATFORM independently anchors and monitors the guard','FAIL_CLOSED_ACTION':'Deny ACCEPT/promotion, monotonic quarantine, retain ownership, mark reconciliation required; owned drain only under separately authorized existing controls','GENERATION_CREATED_WHEN':'Atomic trusted spawn/enrollment allocation, before publication; no adopted numeric bound','GENERATION_INVALIDATED_WHEN':'Process death/replacement, namespace or incarnation change, anchor/channel mismatch, revocation or observed generation replacement','GENERATION_STORED_WHERE':'Authoritative external noncanonical runtime ledger with append-only invalidation/tombstones, not in participant-controlled heartbeat','GENERATION_OBSERVED_BY':'HEALTH_GUARD; dependent decision consumers require current exact ledger epoch/revision','STALE_GENERATION_DENIAL':'Deny without modifying newer registration, ownership, quarantine or eligibility','RESTART_BEHAVIOR':'New anchor and generation; no receipt/approval/enrollment reuse from old generation; cold restart requires new incarnation if prior lineage cannot be established'})
    nodes=['HOST_PLATFORM','HEALTH_GUARD',*work];edges=[['HOST_PLATFORM','HEALTH_GUARD'],*(['HEALTH_GUARD',n] for n in work)]
    (HERE/'NATIVE-HEALTH-DESIGN.json').write_bytes((json.dumps({'status':'DESIGN_ONLY_NO_IMPLEMENTATION','participants':participants,'nodes':nodes,'required_edges':edges,'self_health_only_edges':0,'unobserved_critical_participants':[],'root_assumption':'HOST_PLATFORM is an explicit external trusted OS/service-manager authority. Loss/unprovability of this root denies all admission; it is not silently treated healthy.','decision_rule':'AND of all required independent observations, identities/generations, dependencies, original freshness and independently verified completed work; no cycle/majority fallback','generation_implementation':'NOT_AUTHORIZED'},indent=2)+'\n').encode())
    md('README.md','''# Full-domain fixture + native health design

Status: HOLD_FIXTURE_CONTRACT_ONLY. No positive wrapper execution and no native implementation. The previous executable successor and all historical bytes remain unchanged.

This package defines 13 candidate prerequisite contracts, a complete scalar fixture envelope, 40 exact model joins, explicitly test-only policy classes/values, an independent fail-closed model validator and a design for independently observed native health. It does not claim that the model joins exhaust the frozen SQL authority graph. Full semantic row/frame witness coverage remains open; FULL_DOMAIN_FIXTURE_CONTRACT_READY=NO.

SOURCE-OBLIGATIONS.json preserves actual DDL/functions/foreign keys across V001–V043. FIXTURE-SCHEMA.json identifies the runtime witness mapping HOLD. CANDIDATE-MODEL.json is a deterministic unit-test model, not an instantiated/validated positive-domain fixture. Final validation results distinguish model checks from authority/readiness/time/generation runtime completeness. No JSON boolean or generated OID grants eligibility.

The numeric handling ambiguity is resolved by this user authorization: all 28 int8 duration values carry value/unit/reason/scope/nonproduction metadata. No production policy value is selected or adopted. Production and Room eligibility remain NO. No database, Docker runtime, role, key, secret or resource is created by this gate.

Native health design readiness denotes a reviewed specification only. It does not resolve any runtime health finding or authorize wire/pidfd/SCM_RIGHTS/identity/progress implementation.
''')
    md('FULL-DOMAIN-FIXTURE-CONTRACT.md','''# Full-domain fixture contract v1 — candidate semantic closure

Input HEAD: c19644fc77ce930eeae7f83c2d219d8d5e07433f. Accepted successor SHA256: 6ad78ba61d70e803d2a878034aa7988b69b6374568f96949b2ef6c8defc7a8c7. The source reviewed b0ea86b6... and already approved envelope remain immutable; this gate does not regenerate or repromote them.

All requested envelope fields are required and typed. Four real service identities must be allocated inside a freshly isolated target and their OIDs must be read from pg_roles. Symbolic OIDs in unit-test data are marked MODEL_ONLY_NOT_PG_ROLES. Initial service grants must equal the existing independently reviewed S surface for their slot, with no raw table/column/private-function access, owner membership or service privilege expansion. Eight frozen owner roles remain unchanged in specification.

Actual fixture provisioning would proceed: target/hash guards -> full source installation -> live role/catalog binding -> isolated test-only policy/key/readiness prerequisites -> immutable manifest/header and original signed attestation/source/approval lineage -> preflight -> claim -> verification -> staged principal/credential/grant creation -> admission -> actual attested decision -> retained/released ownership -> independent reconciliation. No downstream effect or receipt is prefilled to make a case pass. Any possession/MAC/signing material must be disposable, never deterministic public-seed secrets, and erased after use.

Allocation/binding/approval/attestation/receipt/execution generations in the envelope are separate typed namespaces. Some are external registry concepts and are not invented SQL columns. offline_attempt_pointer.generation, offline_attempt.generation and offline_execution.generation must match exactly under the actual guards; signer/key/credential/grant revisions remain distinct. Tombstones prevent lineage reuse. Neither an increasing number nor a matching model row substitutes for current enrollment.

Determinism: public seed + case ID + exact HEAD + successor + contract/schema/generator digests define canonical UTF-8 sorted-key JSON. No timestamp is excluded from byte identity. The fixed evaluation instant is explicit model input and is never treated as a live DB clock. Runtime timestamps, actual OIDs/anchors, original signatures and committed receipts require a new fully bound runtime manifest, independently captured evidence and frozen-domain codecs. Self-hash omits only fixture_manifest_sha256 from its own calculation; it does not certify authority.

Every positive stage requires all frozen body and transitive predicates, exact original frames, current runtime witnesses and applicable tenant/revision/generation/time joins. SOURCE-OBLIGATIONS is a lexical exact-byte ledger, not an independent semantic proof. Two remaining contract closure obligations are explicit: complete typed SQL relation/overload/predicate-to-witness mapping; independently validated original binding/attestation/receipt/consumption and live readiness/history/ACL proofs. Until both close, no validated positive fixture or wrapper execution is permitted.

Reconciliation completion is explicitly separate from the auditor's stable read-only offline_reconcile snapshot. Only disposable administrative recomputation may later record RECONCILED and terminal evidence; the auditor receives no UPDATE authority. Recovery/expiry/failure cannot manufacture release or erase effects, tombstones or quarantine.
''')
    md('POLICY-READINESS-FIXTURE-CONTRACT.md','''# Test-only policy and readiness

POLICY_FIXTURE_AUTHORITY=TEST_ONLY; NUMERIC_POLICY_ADOPTED=NO; PRODUCTION_POLICY_ELIGIBLE=NO. Every value in POLICY-TEST-VALUES.json carries VALUE, UNIT, WHY_REQUIRED, TEST_SCOPE and NOT_PRODUCTION_POLICY=YES. These finite model classes exercise nesting and expiry. They are neither benchmark recommendations nor production bounds. The fixture metadata hash is explicitly not yet a certified SHA256 of the frozen 29-tag canonical_policy frame; the final validator reports runtime policy completeness NO.

Actual policy storage must use the exact DEADLINE-POLICY/V1 codec: 4-byte domain length, domain UTF-8, 2-byte field count 29, ascending two-byte tag, four-byte payload length, presence byte, version UTF-8 then 28 signed-positive int8 microsecond values. No duplicate/omitted/reordered/trailing fields. Actual/max pairs and all exact frozen cross-field inequalities must hold. The column called an approved maximum remains solely a test-bound value inside a marked isolated fixture and grants no production numeric authority.

State machine: NOT_READY -> ELIGIBLE_FOR_TEST after model/provenance checks -> READY_FOR_TEST_ONLY_SUCCESSOR_CONSUMPTION only after complete independent runtime validation. Any stale/missing identity, proof, source generation or observation -> QUARANTINED -> DRAINING -> RECONCILIATION_REQUIRED -> TERMINAL. No direct return from quarantine to eligibility; a new separately enrolled generation must be evaluated anew. Actual effect completion also requires reconciliation. All original windows are immutable; no lease extension through setup, heartbeat or retry.

The frozen SQL state literal READY may be used later only within the marked disposable target after test-scoped readiness validation. It never means ROOM_OPERATIONAL=YES and never proves native health. A synthetic watchdog scenario is labelled simulation; it cannot be evidence of an actually healthy independent participant. Real acceptance immediately revalidates the original-emission monotonic heartbeat, census applicability epoch and generation/registry revision. Symbolic model time is not DB time or a monotonic host clock.

The non-executing model remains ELIGIBLE_FOR_TEST with SYMBOLIC_ONLY watchdog/census. The validator denies positive execution even when JSON runtime-evidence fields are replaced with TRUE. No policy/readiness rows are provisioned in this gate.
''')
    md('NATIVE-HEALTH-CONTRACT.md','''# Smallest native health contract — design only

NATIVE_PROTOCOL_CHANGED=NO. NATIVE-HEALTH-DESIGN.json specifies all ten requested participant fields plus exact creation/invalidation/storage/observation/stale-denial/restart generation semantics. It covers postmaster, supervisor, receiver, census observer, approval producer, approval consumer and independently identified enforcement worker.

Identity is derived from the trusted OS/bootstrap and server, retained through an atomic pidfd anchor, and bound to boot/namespace/start/deployment/incarnation/slot/channel. PID, role OID, socket label, process existence and signed material alone are insufficient. Independent slot replacements get new externally recorded generations before eligibility. An old generation may not revoke/erase a newer enrollment or recreate eligibility. A pre-promotion census snapshot is applicable only when all observed context remains current immediately before acting.

Acceptance requires independently observed identity, exact generation, liveness, original-emission heartbeat freshness, completed functional work, authenticated channel, current dependencies and catalog binding. PROCESS_ALIVE != PARTICIPANT_MAKING_PROGRESS; HEARTBEAT_FRESH != COMPLETED_WORK. Provisional anchors grant no eligibility; quarantine is monotonic. Unknown health denies promotion and retains ownership/reconciliation duties.

Seven managed participants plus one external guard and an explicit trusted host-platform root are the minimum proposed graph. Splitting approval producer/consumer and enforcement identity is required to remove the documented gaps. These are future architectural requirements, not processes created by this gate. All framing/counters/channels/SCM_RIGHTS/pidfd/enforcement implementation changes remain separately unauthorized.
''')
    md('COMPLETED-WORK-WITNESS-REVIEW.md','''# Completed-work witness candidate review

| Candidate | Spoof resistance | Generation binding | Crash | Restart | Replay | Independent observation | Storage boundary | Failure semantics |
|---|---|---|---|---|---|---|---|---|
| Heartbeat/loop tick | Producer can emit without work | Can tag generation, insufficient | Fresh queued tick hides failure | Old queue survives | Replayed freshness risk | Self-report | Volatile | Reject as progress |
| Monotonic completion counter alone | Counter can advance before/without completion | Exact epoch necessary | Last increment may precede durable completion | Reset ambiguous without epoch | Old counter can be replayed | Self-report unless verified | Volatile or ledger | Insufficient alone |
| Durable transition count alone | Stronger for committed DB transitions | Must bind transaction, tenant, generation | Commit survives, producer ACK may be lost | Must reconcile original commit | Unique receipt/operation required | Independent DB read possible | DB only | Does not cover census/OS/approval work alone |
| Last consumed generation alone | Proves material consumption only | Naturally bound to material, not whole process | Consumption may survive stalled producer | New actor cannot inherit health | Old valid approval remains replayable | Independent publication comparison possible | Publication ledger | Insufficient general work proof |
| Externally verified operation sequence + typed completion evidence | Counter is advisory until independently corroborated | Full actor/target/dependency epoch + operation ID + registry revision | Unacknowledged commit becomes UNKNOWN/reconciliation | New generation starts distinct sequence; no old receipt reuse | Exact challenge/sequence/epoch and target outcome required | Guard checks actual catalog/publication/target outcome | External append-only ledger plus actual domain outcome | Unknown/partial/stale denies eligibility and retains ownership |

Selected smallest general design: the last hybrid. No single convenient scalar satisfies all seven actors. Use one envelope with participant-specific evidence classes, rather than changing the domain semantics. Fields: participant anchor/slot/generation, operation class/ID, challenge, input/dependency revision, begin/emission monotonic instant+boot epoch, completed sequence, exact result digest, independently observed completion and ledger revision. Emit completion only after the work actually succeeds; atomically publish evidence+sequence. Observer freshness cannot convert an old queued result into new work.

For enforcement, successful send/ACK is not completion: terminate requires independent target-pidfd exit observation; cancel requires independently observed query cancellation/outcome. A vanished query with uncertain effect is UNKNOWN, requiring reconciliation. For census, publication begins only after successful query and applicability CAS, never before query. For approval, verified original signed bytes and successfully consumed current generation are distinct producer/consumer events. Idle health requires a real bounded functional check with explicit workload class, not fabricated business activity or a ping.

Crash after commit/before witness publication never authorizes retry effects: independently reconcile the committed outcome. Loss of ledger continuity invalidates the generation. No witness TTL, resource/drain bound or numeric production value is selected by this design.
''')
    md('INDEPENDENT-OBSERVER-GRAPH.md','''# Non-self-referential observation graph

OBSERVER_GRAPH_NODES=9; OBSERVER_GRAPH_EDGES=8; SELF_HEALTH_ONLY_EDGES=0; UNOBSERVED_CRITICAL_PARTICIPANTS=0_IN_DESIGN.

HOST_PLATFORM -> HEALTH_GUARD -> {POSTMASTER, SUPERVISOR, RECEIVER, CENSUS_OBSERVER, APPROVAL_PRODUCER, APPROVAL_CONSUMER, ENFORCEMENT_WORKER}.

The mandatory graph is acyclic. The trusted host platform/service manager independently anchors and monitors the guard, and is an explicit trust boundary, not an assumed healthy participant hidden from the model. If root/guard health is unavailable or unprovable, all new acceptance is denied. Its supervision uses retained OS identity and an externally observed control loop/result, not solely a self-written heartbeat file.

Existing reciprocal observations may remain supplementary but cannot satisfy or bypass a required independent edge. Every decision requires all required dependencies, not majority, OR or mutual self-certification. No critical actor is sole authority for its own health. Missing observations retain quarantine/ownership and require reconciliation. The graph is a design obligation; it does not claim these processes or edges currently exist.
''')
    md('ADVERSARIAL-REVIEW.md','''# Adversarial design review

Review method: separate generator and validator modules; validator imports no generator, independently pins baseline/successor and expected field sets. Exact source inventory is labelled lexical and not promoted into semantic completeness. Model mutation tests are not counted as frozen wrapper PASS.

| Attack | Resolution / residual |
|---|---|
| Over-permission | Exact reviewed slot S signatures; no raw/private grants or owner memberships; no database provisioning here |
| Circular fixture authority | Seed registry/model equalities prove consistency only; runtime authority/readiness remain NO |
| Implicit prerequisites | All requested case dimensions explicit; unresolved complete SQL predicate/frame mapping remains BLOCKER |
| Stale generation | Exact model registry + all generation dimensions; actual catalog/allocation generation witnesses still required |
| Numeric leakage | Every numeric value scoped TEST_ONLY_NONAUTHORITATIVE; production policy eligibility/adoption NO |
| Synthetic READY confusion | Model only ELIGIBLE_FOR_TEST/SYMBOLIC_ONLY; operational READY and Room status cannot be inferred |
| Successor substitution | Independently pinned accepted artifact hash + schema/generator/source provenance checks |
| Unbound timestamps | Fixed explicit UTC microsecond model clock, no digest exclusions; actual monotonic/DB clock bridge unqualified |
| Fixture replay | Model determinism grants no runtime freshness; actual enrollment/allocation challenge must invalidate replay |
| Cross-organization contamination | Tenant/context joins and immutable original registry mismatch reject model mutations; full source joins still need semantic proof |
| Ownership/effect fabrication | Case states are symbolic; no prefilled effects/receipts accepted as actual commits |
| Self-reported health | JSON proof booleans never enable execution; external guard/root observations required |
| Heartbeat as progress | Explicitly rejected; independent typed completed-work witness selected |
| Observer cycles mask failure | Acyclic mandatory graph, all independent edges required; reciprocal loops supplementary only |

Corrected during review: target aliases oid/rolname initially used unrelated defaults; deterministic generator now maps exact source value to target alias. Broad model generation/policy/time labels initially risked implying runtime completeness; final validator separates MODEL_* from FIXTURE_* and leaves unverified runtime dimensions NO. Unknown nested fields/relations/evidence keys now fail closed. Historical drafts and superseded validation are preserved, not reused as final PASS.

Residual BLOCKER B01: 40 model joins are not yet the complete independently verified typed frozen SQL authority graph; full predicate/overload mapping remains open. Residual BLOCKER B02: original binding/attestation/receipt/accepted-consumption/live history/ACL/key/readiness witness validation is not implemented by this symbolic validator. These are ordinary technical closure work under the present contract-design authority, not a request for additional numeric permission. HIGH/MEDIUM/LOW residual design findings: 0. Native design requirements are fully specified; all native implementation/runtime qualification remains future work.
''')
    print('DESIGN_DOCUMENTS_CREATED')
if __name__=='__main__':main()
