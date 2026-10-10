# VERSIONED_REHEARSAL_POLICY_CONTEXT — minimal proposed governance object

Input head: `7814d6749060b9f41877d3638310fbefdb4dd5f9`. Status: DESIGN PROPOSAL / GOVERNANCE HOLD. Implementation and runtime PASS are not asserted. No canonical access or execution was performed in this mission.

## Status and retained conflict

POLICY_CONTEXT_CONTRACT_CLOSED=YES_STRUCTURAL_PROPOSAL_ONLY
POLICY_CONTEXT_IMPLEMENTATION_AUTHORIZED=NO
NEW_NUMERIC_POLICY_SELECTED=NO

Accepted local ceremony profile60,000,000us, selected fixture actual1,000,000us and max2,000,000us remain unchanged and inconsistent when header=signed endpoints. Warm P99=97028.8us/MAX=98078.1us exclude cold startup and are not an exposure/maximum proof. The [precedence decision](../package-0090-g3f4-policy-host-authority/CONTRACT-PRECEDENCE-AND-POLICY-DECISION.md) requires one new immutable versioned context, not in-place changes or fallback to an unrelated shorter header.

## Minimal record and necessity

| Field | Contract and reason |
|---|---|
| context_schema_version, context_name, context_version | Identifies immutable governance record and decoder; no allocated canonical UUID needed |
| policy_version, policy_digest, exact_policy_bytes_reference | Existing29-tag immutable policy identity/digest, preventing partial scalar approval |
| ceremony_profile_reference, ceremony_profile_digest | Pins accepted interval profile; explicitly records frozen V6 remains untouched |
| interval_semantics | DB transaction time issuance basis, finite nonrenewable half-open signed/header interval with endpoint equality; actual covers approved interval and max covers actual |
| transaction_effect_bounds | References every existing actual/max policy pair, nested execution/attempt/admission/delivery/read/lock/statement/idle/effect bounds and clock basis; no unnamed defaults |
| health_freshness_semantics | Independent DB-wall-clock checked_at, no future observation, actual age and separate enforcement cadence; no lease, renewal or timestamp laundering |
| native_protocol_reference, native_protocol_digest | Pins exact V1 frame/namespace/epoch/ACK/enforcement proposal accepted by future decision |
| ack_deadline_us, ack_deadline_max_us, ack_qualification_reference | New native protocol configuration durations, not silently aliased to any29-tag field; numeric values UNAUTHORIZED_PENDING_POLICY_CONTEXT |
| enforcement_drain_qualification_reference | Qualified failure detection, identity signaling and drain envelope and resource/cold paths; not inferred from interval or freshness alone |
| deployment_approval_reference, incarnation_approval_reference | Same historical host approval may supply both references; new purpose compatibility and current status must be checked |
| effective_from, scope | Finite administrative effect time and exact isolated rehearsal target/role/database boundary, not T0 or signing time |
| dependent_roots_artifacts | Exact hashes, disposition KEEP_FROZEN/NEW_SEPARATE_CONTEXT and causal dependencies; no V6 rebinding or silently renewed attestation |
| retirement_revocation | Existing trusted administrative responsibility, current authenticated status channel, invalidation/copy/restart rules and cessation of admission; no mutable policy edits |
| approval_authority_reference, qualification_references | Exact principal/purpose/scope and independently reviewed evidence; hash alone never approves |

Canonical governance encoding proposal: strict UTF-8 JSON, fixed versioned keys, sorted keys, no duplicate keys, no floating-point durations, no BOM/insignificant whitespace; durations positive finite signed-int64 microseconds, UUID references lowercase canonical only where already existing. No optional unknown fields; unavailable required values prevent an executable instance. Context SHA256 is computed over exact canonical bytes, excluded from its body; the independent administrative decision pins it. Identity/context version and integrity digest are not a new signing key or domain authority.

The complete existing29-tag policy stays in V043. Native ACK remains protected host configuration governed by this external context; no new SQL column/migration or reinterpretation of existing policy tags is proposed. Numerical configuration is not selected here. Before concrete approval, independently qualify security exposure, full cold/degraded path, ACK/admission scheduling and health/enforcement/drain envelope. A context with UNAUTHORIZED or unqualified values is non-executable and cannot claim POLICY_READY.

100us is the synthetic VECTOR1 historical value retained as strict selected rehearsal health age; a separate100us parameter is enforcement interval. Each has max200us. Neither is transport grace, ACK deadline nor general production requirement. Ten failed real cross-process freshness observations reject that route only; pidfd process identity remains safe. Preserve current values and record a separate future version if independently approved, never widen them in-place.
