# Logical completion witness and eleven-frame successor contract

Version: TEST_ONLY_NONCANONICAL_LOGICAL_V3. Research/design validation only.
The approved native V1 protocol and frozen SQL remain unchanged.

COMPLETION_WITNESS_CONTRACT_COMPLETE=YES_LOGICAL_DESIGN_WITH_EXPLICIT_RUNTIME_OBLIGATIONS.
FRAME_SCHEMA_COMPLETE_N=11_LOGICAL.
FRAME_VERIFIER_MODEL_COMPLETE_N=11.
FRAME_REPLAY_MODEL_COMPLETE_N=11.
Runtime corroboration, authenticated observation transport, durable atomic
persistence and deployed enforcement are NOT proven.

## Frozen logical commitment

The pair contains exactly envelope and payload. Every envelope/payload field
has an exact name/type/order in LOGICAL-FRAME-CONTRACT-AND-CONTROLS.json.
Keys sort by ASCII lexical order. Encode compact UTF-8 JSON without BOM,
whitespace, floats, non-finite values, duplicate keys, invalid UTF-8 or
unpaired surrogates. Strings must already be NFC; reject rather than silently
normalize. The verifier reencodes and requires original bytes to match exactly.
Integers are lossless decimal U64; role/database OIDs are unsigned 32-bit.
Those widths are serialization semantics, not operational numeric policy.

Domain/version are exact test-only constants. Unknown version, frame type,
keys, NULL or wrong types deny. UUIDs use exact lowercase hyphenated canonical
syntax. SHA256 fields use 64 lowercase hex characters. Opaque identity strings
are nonempty, NFC and control-free, and must resolve to independently current
enrolled records. Sender assertions cannot establish identity.

The actual producer, consumer and verifier roles are separately fixed for each
type from the preceding logical contract. Enrollment, bootstrap, generation
ledger, participants, approval producer, enforcement actor, supervisor and
census observer remain distinct roles. The model checks an independent role
binding rather than assigning authority from frame_type.

## Receipt/type and context

Receipt identity is frame_identity. Completion kind is the exact frame_type
and witness_type pair, plus a closed operation class. The reviewed operation
classes cover SQL commit receipt, readiness census, anchor registration,
approval publication/consumption, reconciliation receipt, cancel outcome,
anchored terminate exit and identity observation. A heartbeat accepts only
PROCESS_ALIVE and never establishes PARTICIPANT_MAKING_PROGRESS.

Bind participant/consumer/verifier identities and separate generations,
deployment/incarnation/binding UUIDs, plan/policy hashes, boot epoch, enrollment
generation, postmaster/receiver/supervisor generations, observation epoch,
registry revision and retained anchor identity. Runtime generations are never
equated with SQL pointer, key, credential, grant or approval revisions.

Before completion, an observer challenge commits to exact operation class/ID,
target anchor, input revision and expected completed operation sequence.
Completion result digest, durable result and independent observation reference
must match independently obtained outcome evidence. Payload-only SHA256 detects
substitution, not authority. Sender VERIFIED text is rejected; verification is
computed by the independent observer.

The nonce/challenge and strict next sequence belong to a specific participant,
consumer, generation and frame channel. Restart/ledger discontinuity invalidates
old context. Challenges cannot move between operations or generations.
Unknown effect retains ownership and requires reconciliation; ACK or signal
delivery cannot certify actual cancellation/exit/commit.

## Freshness and final applicability

Use original BOOTTIME emission in the same boot; never stamp at dequeue.
Check freshness both on observation and immediately before decision. All timing
values in the model are recorded TEST_ONLY_EXPERIMENTAL_NOT_POLICY controls.
No numeric ACK, health, drain, policy or resource bound is adopted.

The final observation rechecks full context and independent outcome. A pre-
promotion census snapshot cannot revoke or erase later enrollment; stale
observations deny without creating eligibility. Quarantine is monotonic and
provisional anchors grant no eligibility. The comparison snapshots detach from
mutable input; an in-place ledger change cannot evade the model CAS check.

Actual implementation must compare-and-consume current context plus the
challenge/sequence atomically under one independently governed decision
primitive. The Python model expresses the single-transition contract and
detects injected changes before decision, but is NOT a concurrent native
atomicity, persistence, cross-process authentication or OS/pidfd proof.

## Model evidence and limits

The final model performs 605 controls across all eleven frame types:
required-field denial, wrong context, replay, stale queued heartbeat, final
freshness race, census promotion race, receiver/postmaster restart, supervisor
generation loss, anchor change, participant death, provisional enrollment,
missing/changed corroboration, changed experimental bound, in-place ledger
mutation, boolean-as-generation, malformed/duplicate/noncanonical encoding.
MODEL_FAIL_N=0 applies only to those logical controls.

No SQL positive wrapper, PostgreSQL server, socket, signing key, native code
change or canonical resource was executed. Original binding/attestation/receipt
bytes and external authenticated observations still need actual qualification.
FULL_DOMAIN_FIXTURE_CONTRACT_READY remains NO until the complete SQL semantic
closure and both authority layers are independently covered.
