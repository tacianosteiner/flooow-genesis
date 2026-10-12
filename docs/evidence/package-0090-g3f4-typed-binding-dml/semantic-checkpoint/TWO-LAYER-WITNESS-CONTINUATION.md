# Two-layer witness continuation — logical contract, not runtime proof

Version: LAST-CODEX-DESIGN-1. Date: 2026-10-12. No native wire change or signing.
Frozen earlier artifacts remain unchanged; this is a proposed design refinement.

## Trust inputs and field bindings

LAYER_A binds actual SQL objects/checks/effects and their transactions.
LAYER_B independently binds OS anchors, participant lifecycle, publication,
consumption and observed outcomes. An SQL receipt alone cannot certify process
progress; an external health message cannot create SQL approval or ownership.

| Logical field | Typed meaning / independent origin | Decision obligation |
|---|---|---|
| frame_identity | Nonempty opaque message/receipt ID; exact expected ledger entry | Unique in its context; replay never accepted |
| frame_type | One of the eleven frozen logical type names | Unknown type denies; cannot relabel heartbeat as completion |
| frame_version | Exact reviewed logical version | Unknown/downgrade denies; not negotiation-by-self-assertion |
| participant_identity | Opaque independently enrolled anchor record | Resolve retained OS identity; bare PID/OID/self claim insufficient |
| participant_generation | Unsigned losslessly decoded generation ordinal | Equal current anchored slot generation; not SQL pointer revision |
| deployment_id / incarnation_id | Exact independently enrolled context IDs | Compare with current binding, not sender-selected values |
| boot_epoch | Exact independent boot identity | Monotonic time comparisons only within this boot |
| sequence | Unsigned per participant/generation/channel ordinal | Strict expected sequence; duplicates/gaps deny or reconcile |
| emitted_boottime_us | Unsigned original BOOTTIME emission | Not future, not restamped at dequeue; recheck freshness before decision |
| observation_epoch / registry_revision | Exact current census/promotion applicability | Pre-promotion snapshots cannot erase/revoke newer enrollment |
| payload_digest | SHA256 of the exact proposed canonical payload bytes | Compare independently recomputed digest; digest is not authenticity |
| challenge | Exact independent verifier-issued one-use token | Bind participant/generation/channel/context/operation and expiry; consume atomically |
| witness_type | Closed completion/observation kind | Must match frame type, operation class and independent result kind |
| witness_generation / witness_sequence | Independent observer ledger context | Distinct from participant generation/sequence; verify current observer slot |
| independent_verifier_identity | Independently anchored observer record | Producer cannot appoint itself verifier or inject observations |
| verification_result | Verifier-computed result, not producer authority | Sender VERIFIED text ignored as evidence; derive acceptance independently |

All integer ranges are serialization constraints from design schema, not timing
or resource policy. Freshness/ACK/drain/resource bounds are inputs from later
approved policy, never chosen here. Missing policy or observation denies
eligibility; it cannot be interpreted as unlimited time.

## Completion corroboration

Bind operation_class, operation_id, target_anchor_identity, input_revision,
completed_sequence, result_digest, durable_result_reference and
independent_observation_reference to an observer-owned record with exact
deployment/incarnation/boot, producer/consumer/verifier generations and
challenge/channel/sequence context. The reference must resolve independently;
accepting a producer-supplied reference string is insufficient.

The observer independently determines the actual outcome:
committed DB transition and receipt in LAYER_A; cancellation outcome rather than
signal-send ACK; retained anchor exit rather than PID disappearance; successful
applicable census and revision CAS rather than start-of-query timestamp;
original publication plus successful independent consumption rather than a file
hash supplied by producer. If effect is unknown, retain ownership and require
reconciliation. Progress counter/heartbeat/PROCESS_ALIVE does not prove completion.

On restart/ledger discontinuity, invalidate prior challenges, receipts and
observer generation. Never reset a sequence into an eligible previous generation.
A stale observation causes denial of that observation; it must not quarantine,
erase, revive or otherwise mutate later valid enrollment. Decision-time CAS
must compare the full current generation/anchor/enrollment/registry context.
Quarantine remains monotonic and provisional anchor grants no eligibility.

## Proposed deterministic encoding — not adopted native protocol

A future independently tested encoding uses exact UTF-8 bytes, no BOM, a closed
envelope/payload pair, ASCII schema keys sorted lexicographically, no extra keys,
minimal structural whitespace and lossless decimal integers. Reject duplicate
keys, floats/exponents/NaN/infinity, invalid UTF-8, lone surrogates and strings
outside the reviewed normalization rule. Do not silently normalize received
material: original byte identity must remain challengeable. Version, type,
UUID-like syntax, enum values and opaque anchor formats need an explicit
schema revision and independently generated vectors before this proposal is
complete. The existing schema's unconstrained strings are not that revision.

Domain-separate the full contextual receipt commitment from payload-only digest;
record original bytes plus exact context. Digest collision resistance does not
prove trust, freshness, or context applicability. This mission produces neither
a new signed artifact nor native encoding implementation.

## Eleven-frame obligations

| Type | Independent corroboration / denial specific to type |
|---|---|
| enrollment | Current OS/server role/database identity and approved binding; no provisional eligibility |
| identity_proof | Retained start/namespace/pidfd anchor, not claim equality alone |
| generation_proof | Current independent slot/allocation ledger |
| heartbeat | Original emission plus current anchor; liveness only |
| progress | Independently completed operation; arbitrary loop counter denies |
| completed_work_witness | Actual target result, committed receipt/outcome and contextual one-use challenge |
| approval_state | Original publication/context and independent consumption; no generic approval hash join |
| enforcement_state | Actual anchored cancel/terminate result, not command ACK |
| quarantine | Current enrollment/registry applicability; monotonic quarantine |
| drain | Current target/ownership set; receipt cannot authorize release by itself |
| recovery_observation | Current postmaster/receiver/supervisor/anchor/enrollment/registry tuple; no new eligibility |

Independent design structure checks are in WITNESS-DESIGN-REVIEW.json.
They establish required-field agreement for eleven schemas, not complete
encoding or deployed corroboration. Exact SQL closure-item mapping, authenticated
observation transport, atomic persistence and full verifier controls remain OPEN.
