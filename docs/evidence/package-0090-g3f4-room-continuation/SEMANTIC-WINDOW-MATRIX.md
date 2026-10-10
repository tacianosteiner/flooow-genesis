# Source-grounded semantic window matrix

Inspection baseline: e0e5e765e7ae5a1b9bdfbecb5a539985d0c8ca7d. This adds the
requested ten-column matrix without reopening the completed source adjudication.
CLASSIFICATION=SAME_SEMANTIC_CONFLICT for the accepted frozen rehearsal profile.
No new policy authority is created by this matrix.

Source abbreviations below refer to full paths:
- SPEC: `docs/specifications/SPEC-0090-governed-offline-field-proof-exclusive-capability-composition.md`.
- TIME: `docs/evidence/PACKAGE-0090-G3F-4-FINAL-CEREMONY-TIME-CONTRACT-CLOSURE.md`.
- CODEC: `applications/marketplace-operations/src/main/kotlin/io/flooow/marketplace/operations/authorization/ApprovalAttestationCanonicalCodec.kt`.
- FIXTURE: `docs/evidence/PACKAGE-0090-G3F-3B-FIXTURE-001.json`, exact29-tag policy.
- POLICY: `scripts/validation/package_0090_policy_fixture.py`, NAMES/validate/encode.

| VALUE | SEMANTIC_NAME | SOURCE_FILE | SOURCE_LINE_OR_CONTRACT | START_EVENT | END_EVENT | SECURITY_PURPOSE | AUTHORITY | IMMUTABILITY | CURRENT_CONSUMERS |
|---|---|---|---|---|---|---|---|---|---|
|1,000,000us actual;2,000,000us ceiling|Binding TTL|SPEC;FIXTURE;POLICY|SPEC596 VECTOR_1;586 tags14/15;18 nesting|Header valid_from|Permitted expiry<=valid_from+actual, also bounded by approved maximum|Bound lifetime and nested mutation authority; maximum is no extra grace|Original synthetic vector and retained approved rehearsal policy|Version/bytes/digest immutable|Header compatibility, policy decoding, wrapper nesting |
|Not separately assigned by29-tag policy|Credential TTL/private-key custody|SPEC;TIME|SPEC10 delivery/11 credential;TIME49 signing custody|Governed issuance or key birth, according to separate credential/signing contract|Independent admission/delivery/revocation/destruction boundary|Secret possession, custody and revocation|Existing credential/signing governance; no new value inferred|Original authority/deadlines not renewable|Credential admission, delivery and memory-only signing process |
|100us actual;200us ceiling|Watchdog freshness|SPEC;FIXTURE|SPEC18;586 tags24/25;596 vector|Externally qualified observation projected at DB checked_at|Fresh DB age<=100us, future denied|Reject stale host authority|Approved immutable policy and independent trusted observer|Policy immutable; observation projection mutable|Preflight and readiness guards; ADMIN R2 reads |
|100us actual;200us ceiling|Watchdog enforcement interval, distinct from freshness|SPEC;FIXTURE|SPEC18;586 tags22/23;596 vector|A supervised enforcement-loop inspection/control interval|Next bounded enforcement cycle; actual interval bound|Bound stalled JVM/backend enforcement delay|Approved policy and qualified independent host enforcement|Policy immutable; runtime cadence must be proven|Watchdog supervisor/cancel/terminate/drain; ACK is not this parameter |
|60,000,000us|Ceremony approval/execution envelope|TIME|TIME47-49/60/64; prior request section18|Transaction opening T0, read once after locks|T0+60s exclusive for signing/write checks, not retrospective COMMIT visibility|Finite nonrenewable approval|Bounded prior rehearsal instruction and accepted local profile|Frozen once captured; no refresh|Future TREG composer, PRE/POST_SIGN and PRE_COMMIT predicates |
|60,000,000us in accepted profile|Signed-manifest validity|TIME;CODEC|TIME46/47/60;CODEC canonicalManifestBytes signed fields12/13|approvalWindowStart=T0=header valid_from|approvalWindowEnd=T0+60s=header expires_at|Bound exact approved target/governance/evidence authorization|Original approval and explicit local endpoint mapping|Signed endpoints immutable|Manifest digest/preimage/JCA and header compatibility |
|1,000,000us actual;2,000,000us ceiling|Preflight receipt TTL/deadline|SPEC;FIXTURE|SPEC241/586 tags28/29;G3F.3B.1 amendment|Q server clock receipt issuance|Original issued_at+TTL exclusive|Expire authenticated preflight/replay authority|Separately approved preflight pair, not borrowed binding duration|Receipt timestamps and policy version immutable|Q/S01/S13 receipt verification |
|No separately assigned activation-duration scalar|Activation freshness|SPEC;TIME|SPEC18/25;TIME60;ADMIN R2 pre/post health checks|Current activation guard and independently observed checked_at|Current health age and original header/policy validity must each pass|Prevent activation on stale host/context|Approved policy/host evidence and exact trusted ADMIN scope|Original header immutable; health projection independently refreshed|PLAN_BINDING_ADMIN and readiness consumers; no invented activation lease |
|1,000,000us actual;2,000,000us ceiling|Execution validity/deadline|SPEC;FIXTURE|SPEC8/18;586 tags12/13;596 vector|Original claim/execution allocation DB clock|Absolute execution_expires_at<=binding expiry|Bound possessed execution authority and nested delivery/admission|Approved policy and authentic slot/possession guard|Execution deadline immutable, never revived by restart|Guard M, claim/delivery/admission and independent watchdog |
|1,000,000us actual;2,000,000us ceiling|Transaction timeout|SPEC;FIXTURE|SPEC18;586 tags2/3;596 vector|DB transaction opening, including lock waits|Finite wall-time transaction bound|Bound stalled transaction independently of caller SET|Approved immutable policy and trusted enforcement|Policy immutable; transaction opening cannot refresh|Entry/final guards and watchdog |

These clocks are distinct in general. The accepted TIME46/47/60 profile explicitly
identifies signed-manifest endpoints with binding endpoints; therefore the60s
interval must fit binding actual1s and ceiling2s. That explicit mapping, not a
comparison of unrelated units, establishes SAME_SEMANTIC_CONFLICT here.
Freshness, enforcement cadence, credential custody, preflight and execution
deadlines remain separate. No evidence establishes obsolete policy or obsolete
ceremony assumption. The previous new-policy/context proposal remains pending;
no scalar, fixture, header mapping, policy row or canonical source is changed.
