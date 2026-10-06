# Package 0090 G3F.4 - final ceremony time contract closure

G3F_4_FINAL_CEREMONY_TIME_CONTRACT_CLOSURE=HOLD. One selected deterministic temporal model is fully specified below, but it is not promoted to canonical PASS: direct source evidence contradicts the nonsecret recovery projection in the preceding closure. No implementation, DB connection/write, runtime time capture, identifier/key generation or signature is performed. No commit or push is permitted.

Branch `checkpoint/package-0090-cloud-handoff`; expected local/fetched origin baseline `1ffbaa312f3c80f478c89298d2e3914ae50ae785` verified equal and CLEAN before writing. Staged/tracked/untracked inventories were empty. One new evidence artifact is the only authorized repository change. All previous source and evidence remains byte-identical.

TC-R01 / HIGH / OPEN: prior Q12 in [ambiguous-commit recovery](PACKAGE-0090-G3F-4-AMBIGUOUS-COMMIT-RECOVERY.json) names `offline_execution.possession_digest` in `PUBLIC_COLUMNS`, its SELECT and the composed `nonsecret_recovery_snapshot`. [SPEC 21.1](../specifications/SPEC-0090-governed-offline-field-proof-exclusive-capability-composition.md) line282 forbids secret/proof/private possession digest in an audit projection; section22 read-purpose rows independently say digest never output. V043 line644 confirms it is the private stored execution-authentication digest. Ability of trusted ADMIN to inspect it internally does not make it public recovery evidence. This is a design contradiction, not a demonstrated runtime disclosure: Q12 was marked unexecuted and no DB was queried in either this gate or the recovery-design gate. No actual digest, credential, proof or private key is copied into this report.

This narrow finding satisfies the current request section0 exception for reopening prior recovery only on direct repository contradiction. The one-transaction graph, query-first outcome doctrine, public governance cleanup, whole-root allocation authority and key lifetime remain preserved. Only the previous nonsecret-projection claim needs a bounded correction. No normative inconsistency requires editing SPEC/ADR; do not rewrite history, operational SQL or old evidence in this temporal-only gate.

Severity scope: this gate B0/H1/M0/L0 (TC-R01); inherited watchdog/H01 B0/H2/M0/L0 remain unchanged; combined current risk B0/H3/M0/L0. TC-R01 is distinct from G3F4-H01. No downgrade or suppression of an existing HIGH makes this a PASS.

Evidence ledger was built before this artifact and before promotion of any final design decision. Source type, current contract, conflict and resolution are explicit:

| ID / claim | Source / type | Current contract | Conflict | Resolution |
| --- | --- | --- | --- | --- |
| L01 Database is sole time authority | docs/specifications/SPEC-0090-governed-offline-field-proof-exclusive-capability-composition.md:239 / NORMATIVE | DB authorization uses DB clock; JVM clock only UX | NONE | Retain database authority; distinguish identity basis from fresh eligibility readings |
| L02 Expiry concerns canonical write, not later visibility | docs/specifications/SPEC-0090-governed-offline-field-proof-exclusive-capability-composition.md:60 / NORMATIVE | Before/after-effect fresh DB checks; committed visibility may follow expiry | Strict commit-visibility deadline would contradict this rule | Guard signing/writes/pre-COMMIT; in-flight COMMIT is query-first, no retroactive undo |
| L03 ADR confirms commit race interpretation | docs/adr/ADR-0090-governed-offline-field-proof-exclusive-capability-composition.md:81 / NORMATIVE | Admitted valid effects may become visible after expiry | NONE | No commit-time oracle, new journal or coordinator |
| L04 Header fingerprints three instants | docs/specifications/SPEC-0090-governed-offline-field-proof-exclusive-capability-composition.md:81 / NORMATIVE | Tags29/30/31 are issued_at/valid_from/expires_at; epoch microseconds | These are not direct signed-manifest fields | Select exact equality to two signed endpoints in this local profile; do not claim whole header is Ed25519-signed |
| L05 Manifest signs start/end through digest | applications/marketplace-operations/src/main/kotlin/io/flooow/marketplace/operations/authorization/ApprovalAttestationCanonicalCodec.kt:31 / PRODUCTION_SOURCE | Positions12/13; six-fraction UTC text; signature preimage contains manifest SHA256 | No codec rule currently equates header timestamps | Chosen profile requires issued=valid_from=start and expires=end at all future provisioning/recovery checks |
| L06 DDL interval checks are weaker than profile | applications/marketplace-operations-persistence-postgres/src/main/resources/db/migration/V043__create_governed_offline_field_proof_capability_composition.sql:575 / FENCED_SOURCE | Finite instants; issued<expires; valid_from<expires | No schema enforcement of exact equality or60s duration | Existing trusted ADMIN must check stricter profile; no source/migration change or implementation claim |
| L07 Prior review left only three time inputs open | docs/evidence/PACKAGE-0090-G3F-4-BINDING-TIMESTAMP-AUTHORITY.json / PRIOR_EVIDENCE | Semantic coordinates were distinct and mapping unresolved | Prior proposed equality was not an approved repository fact | Define one local equality profile in this review; promotion remains blocked by TC-R01 |
| L08 Allocation and atomic recovery authority remain preserved | docs/evidence/PACKAGE-0090-G3F-4-AMBIGUOUS-COMMIT-RECOVERY.json / PRIOR_DESIGN | One T_REG; query-first unknown commit; historical registration is not live permission | Only direct private-projection contradiction below | Preserve PLAN_BINDING_ADMIN, allocation, commit graph, orphan order and key lifetime; no general recovery redesign |
| L09 Recovery public snapshot includes private digest | docs/evidence/PACKAGE-0090-G3F-4-AMBIGUOUS-COMMIT-RECOVERY.json / PRIOR_DESIGN | Q12 PUBLIC_COLUMNS/SQL and composed nonsecret recovery snapshot include possession_digest | TC-R01 HIGH: secret-exclusion property is contradicted | HOLD; separate bounded correction excludes private digest from public projection and snapshot; previous evidence unchanged |
| L10 Private execution digest must never appear in audit output | docs/specifications/SPEC-0090-governed-offline-field-proof-exclusive-capability-composition.md:282 / NORMATIVE | No secret/proof/private possession digest in audit projection; section22 says digest never output | Admin ability to read internally does not make digest public/nonsecret evidence | No digest bytes queried/copied here; public recovery classification needs only identity/state/deadline metadata |
| L11 Restart never refreshes windows or ownership | docs/specifications/SPEC-0090-governed-offline-field-proof-exclusive-capability-composition.md:235 / NORMATIVE | Restart inspects durable state; terminal results remain readable; no automatic continuation | NONE | Recover exact original basis/read-only history; no signing or mutable replay after interruption |
| L12 H01 remains runtime qualification | docs/evidence/PACKAGE-0090-G3F-4-TRANSPORT-MODEL-REVIEW.md / PRIOR_REVIEW | Transport/RR/jitter and deployment gaps remain OPEN/HIGH | Old G3F3B-H01 is a distinct namespace | Current H01/watchdog findings unchanged; no runtime closure from time definition |
| L13 Preflight issue/expiry is separate | docs/specifications/SPEC-0090-governed-offline-field-proof-exclusive-capability-composition.md:588 / NORMATIVE | Q clock_timestamp issuance + approved preflight TTL, never renewed | Using receipt time/TTL for header confuses events | One cluster clock; separate existing events. Never copy Q instants/TTL into this ceremony |
| L14 Immutable policy still bounds actual validity | docs/specifications/SPEC-0090-governed-offline-field-proof-exclusive-capability-composition.md:586 / NORMATIVE | 29-field policy actual/max pairs, BINDING_VALIDITY and version/digest | Fixed60s profile cannot bypass shorter/unapproved bound | Policy conflict => BLOCK; next signing-window review must qualify actual policy/latency, no cap change here |
| L15 60s and transaction-start basis were already required | C:/Users/xmz_r/.codex/attachments/fa38ec36-d0cf-469d-9ee1-cf97aaa4ef5a/Pasted text.txt:517 / USER_AUTHORITY | Prior request fixes DB transaction clock/UTC microseconds/+60s nonrenewable; must not widen60s | This is rehearsal authority, not universal production default | Preserve60000000us; no use of config, Q TTL or benchmark as lifetime authority |
| L16 Public key governance and historical replay retain original proof | applications/marketplace-operations-persistence-postgres/src/main/resources/db/migration/V041__create_s2a_accepted_attestation.sql:230 / PRODUCTION_SOURCE | Exact accepted replay resolves historical governance; fresh acceptance has different eligibility | Historical verified_at must not become new ceremony basis | Public exact replay only; preserve stored times, no renew/re-sign |
| L17 Final command uses current effect-time clock | applications/marketplace-operations-persistence-postgres/src/main/resources/db/migration/V042__create_s2a_attestation_consumption_and_attested_command_authority.sql:1937 / PRODUCTION_SOURCE | Final decision rederives current effective key/current authority at effect time | T0 identity is not current eligibility clock | Future operations retain own fresh clock/governance guards; no backdated authority from T0 |
| L18 UTC microsecond input is strict | applications/marketplace-operations/src/main/kotlin/io/flooow/marketplace/operations/authorization/ApprovalGovernance.kt:198 / PRODUCTION_SOURCE | nano%1000==0; canonical text constraints | Silent rounding/truncation could change signature identity | Reject unsupported precision; typed DB/UTC/JDBC round-trip must be exact |

One selected local temporal profile (not a historical equality assumption, not a general production default, and not runtime authorization):

```json
{
  "TIME_CONTRACT_AUTHORITY": "Existing PLAN_BINDING_ADMIN for immutable binding profile; existing separately governed rehearsal S2A approval authority for manifest lifetime. Database cluster alone supplies instants.",
  "TIME_CAPTURE_EVENT": "FINAL_CEREMONY_TIME_CAPTURE: once in the already selected T_REG after canonical locks, before key birth/governance/signing; value is the DB-owned opening instant of that SAME transaction, not the time of the read.",
  "TIME_SOURCE": "T0 := pg_catalog.transaction_timestamp() from exact T_REG; fresh pg_catalog.clock_timestamp() on same approved cluster for every eligibility/recovery observation. These are two functions of one authority, not two independent clocks.",
  "TIMEZONE": "UTC; typed Instant transport; canonical manifest text ends Z, no local civil-time interpretation",
  "PRECISION": "Exact integer microseconds; reject sub-microsecond data, silent round/truncate, nonfinite/out-of-range and failed typed round-trip",
  "ISSUED_AT_RULE": "issued_at=T0. Existing binding issuance begins at canonical T_REG opening, after identity allocation but before signing; not allocation time, signature time, verified_at, durable commit time or Q receipt issuance.",
  "VALID_FROM_RULE": "valid_from=issued_at=T0=manifest.approvalWindowStart. No future-dating relative to fresh DB now; no delayed-start alternative in this profile.",
  "EXPIRES_AT_RULE": "expires_at=manifest.approvalWindowEnd=T0+60000000us, exact checked addition. Lifetime is the preexisting immutable60s rehearsal approval contract, not config, mutable default, preflight TTL or new policy value.",
  "EXPIRY_BOUNDARY_RULE": "Half-open [T0,T0+60000000us). Fresh DB now==expires_at is expired; now<valid_from is future/not-yet-valid and blocks. Eligibility applies at signing and canonical write/postcheck/pre-COMMIT guard, not eventual commit visibility/ACK.",
  "SIGNING_WINDOW_RULE": "One unchanged60s approval/header window; key/public authority start at T0 and authority end matches frozen approval end under existing approval governance. Validate fresh DB clock before key/sign, after signature/JCA, before writes, after complete write set and after constraints immediately before COMMIT. No extension, grace, stale transaction-start eligibility check or new receipt.",
  "RETRY_RULE": "One root/one T0 forever. Same live preparation may read/continue its exact frozen context with no second sign; duplicate mutable invocation BLOCK. Failed/interrupted preparation invokes prior query-first recovery and then proven abandonment/whole fresh root, never resample within old identity.",
  "REPLAY_RULE": "Exact committed root -> REPLAY_EXISTING historical header/original/receipts with original T0/expiry unchanged; zero new mutation/signing/time capture, including expiry or new process/runtime/policy. Conflicting/missing root -> BLOCK or RECOVER, never repair.",
  "RECOVERY_RULE": "Before any durable outcome assumption use exact identity and corrected nonsecret query set after writer quiescence/canonical locks. Unknown -> RECOVER/HOLD; exact commit -> REPLAY_EXISTING regardless current expiry, with fresh effects denied after expiry; confirmed absent -> prior abandonment/cleanup and whole fresh authorized ceremony. TC-R01 prevents current snapshot from being used/promoted as nonsecret evidence.",
  "WATCHDOG_BOUNDARY": "Later observe original T0/expiry and fresh approved DB time, health/elapsed transaction/idle bounds, detection/rollback/drain under existing duties; cannot author/modify times, renew/sign/allocate/register or infer COMMIT outcome. ADMIN alone governs existing EXPIRED/REVOKED lifecycle. Watchdog OPEN.",
  "H01_EFFECT": "Narrows only design ambiguity of header/start/end relationship; transport/RR/jitter/numeric envelope and watchdog qualification unchanged, current G3F4-H01 remains OPEN/HIGH.",
  "TEMPORAL_IDENTITY_STABLE_ACROSS_RETRY": "YES_SELECTED_DESIGN; never recompute original basis",
  "TEMPORAL_CONTRACT_CRYPTOGRAPHICALLY_BOUND": "YES_SELECTED_DERIVED_PROFILE: manifest signature binds start/end via manifest digest; equality derives all three header instants. No direct three-header-field signature or whole-header signature claim.",
  "PROFILE_STATUS": "SELECTED_DETERMINISTIC_DESIGN_PENDING_GATE_PASS; not promoted to canonical closure because TC-R01 remains HIGH",
  "SINGLE_CAPTURE_RULE": "ONE_CEREMONY_ONE_T0; many fresh eligibility observations cannot replace T0",
  "HEADER_CONTRACT_PROMOTION": "37 previously closed/3 time inputs not promoted while this gate HOLD; no actual runtime values created",
  "POLICY_COMPATIBILITY": "Before runtime, approved immutable29-field policy/version/digest must match whole header/readiness approval;60000000us must be within BINDING_VALIDITY actual<=maximum. Missing/shorter/drifted policy => BLOCK, not min(), fallback, larger policy or changed window."
}
```

T0 is read once after the C locks on the same T_REG selected in recovery; its semantic event is transaction opening, which occurred before any lock wait. Read timing cannot refresh it. This preserves the previously governed DB-transaction-start/60s approval rule. A wait can exhaust the window: check fresh DB wall clock immediately after locks and before key birth; if already expired or future-issued, abort without generating a key. Do not move issuance after the wait to buy time. A lost time-capture response makes the old context uncertain; recover/dispose the whole root rather than request another basis.

A single identity capture does not prohibit later DB observations. Every eligibility observation N uses pg_catalog.clock_timestamp(), not transaction_timestamp(), now(), statement_timestamp(), client/JVM time, file dates, receipt issuance, policy effective_from, previous verified_at or a benchmark marker. All observations refer to the same independently approved disposable cluster. Client clock skew has no authority; no tolerance/grace is chosen. Stale application time is ignored, unavailable/invalid/stale authoritative context blocks. The existing preflight receipt has a separate Q issuance event/TTL; none of its fields becomes a header source.

Exact representation: DB timestamptz/Java Instant carry instants, not local wall-time labels. Require microsecond precision, no nano remainder; use UTC-calendar typed JDBC Timestamp/Instant bindings with explicit timestamptz casts, UTC reads, and exact epoch-microsecond equality after round-trip. DB display offsets may differ without changing the typed instant; the signed manifest wire form is exactly UTC six fractional digits plus Z as CanonicalWriter.appendInstant(6) requires. Header tags29-31 encode signed-i64 network-order epoch microseconds with the existing present marker/tag framing. Text and binary codecs are intentionally different existing contracts; neither can silently replace the other.

Selected local representation range is UTC AD year0001 through year9999, inclusive at microsecond granularity: epoch-us [-62135596800000000,253402300799999999]. This is a stricter common four-digit-year profile, not a claim that PostgreSQL/Java cannot represent wider ranges. It prevents era/extended-year coercion between SQL/JDBC and signed text. Require T0<=upper-60000000, checked signed64 addition, and exact representable endpoints in every existing codec/DB round-trip; reject null, infinity, sub-microsecond, leap-second textual substitutes, out-of-range, wrap, clamp, float arithmetic or saturation. No rounding is permitted. These arithmetic examples are synthetic design checks, not live temporal values.

Clock continuity is a qualification precondition, not an asserted property of wall-clock functions. In the uninterrupted future runner retain the highest observed DB N in existing transient ceremony context; N<T0 or N<previous observed N fails closed, destroys/discards ephemeral state and invokes existing outcome recovery. Forward jumps reaching expiry block; equal successive microsecond readings are allowed. An observed expiry is sticky within that live preparation. Existing terminal EXPIRED/REVOKED lifecycle and DISABLED/RETIRED signer history are never undone by a later clock reading. No new persistent high-water journal or timer is added.

No finite set of wall-clock samples proves all unobserved adjustments or real elapsed-time monotonicity. Existing trusted host/watchdog/database-clock qualification must establish continuity before time-sensitive use; absent such evidence, BLOCK. Interruption/restart loses transient continuity: only exact query-first historical recovery is permitted for that final ceremony, no automatic unfinished signing/registration continuation even if a later DB clock lies within the old interval. Current operational watchdog/time-health qualification remains OPEN. This review does not manufacture a global rollback detector, restart clock attestation or elapsed-time proof.

Expiry decision points for the future trusted ADMIN sequence: (1) fresh check after lock acquisition and before key birth; (2) fresh check immediately before single SIGN; (3) fresh check after signing/local JCA and private-key destruction; (4) fresh check before canonical write batches; (5) fresh postcheck after all eleven staged rows; (6) SET CONSTRAINTS ALL IMMEDIATE and full exact write-set/scope validation; (7) final fresh DB clock guard immediately before COMMIT, no signing/output/user interaction in between. Require valid_from<=N<expires_at at every applicable point, approved current policy, unchanged root and existing transaction/deadline bounds. A failed guard while the transaction is controlled/open rolls it back; no claim that this sequence is implemented today.

There is no atomic way in the current source to prove COMMIT visibility or client ACK occurred strictly before expiry. That property is not required by SPEC3/18 or ADR Revocation: eligibility is canonical write-time admission with final revalidation, and admitted writes may become visible later. This selected profile additionally checks just before COMMIT. If expiry is observed before that final guard, BLOCK/rollback; if COMMIT was already sent following a valid guard and expiry arrives in-flight, do not invent rollback or delete the result. Query exact allocated identity and full mutually-bound state. A confirmed complete registration is historical success with original window, even if now expired; it never authorizes new effects. Unknown outcome remains RECOVER/HOLD. No post-ACK clock sample rewrites identity or retroactively cancels committed history.

The final pre-COMMIT guard is an admission observation, not a stored authoritative commit timestamp or a new receipt. A restart can prove canonical registration from its immutable rows without proving elapsed latency/commit timing. The earlier recovery scope expressly separates historical COMMITTED_VALID from runtime timing/readiness/command proof. Later independently authorized V041/V042 effects still have their own fresh governance/window guards; registration or old verified_at cannot substitute for them.

Cryptographic relation: canonical ApprovalManifest positions12/13 contain approvalWindowStart/End as UTC microsecond text. SHA256 of all22 canonical fields enters the exact existing signature preimage with algorithm/key identity/fingerprint. Under this chosen profile, issued_at=valid_from=signed start and expires_at=signed end, so all three header instants are uniquely derived from cryptographically committed values. Header fingerprint independently hashes those instants at tags29-31 and the retained manifest hash. A bare SHA256 header hash is not signer authority; no whole-header Ed25519 signature is claimed. The future trusted ADMIN/JCA/recovery validator must decode the actual signed original and enforce all equalities and exact+60s before accepting the profile. Current DDL/codec alone does not enforce that new local mapping.

Temporal values cannot drift even before signing once T0 was captured. Signing never changes them. After signing/header fingerprinting there is no re-materialization under new dates, signature reuse or subset ID repair. Public original commitments may be retained in the already existing immutable input components; private material is never persisted. The original existing plan/allocation authority is unchanged.

Lifetime source and policy: the60s nonrenewable approval window comes from the pinned prior request/closure, not an application setting or new maximum. This local equality profile requires its60s header duration to satisfy the exact already-approved29-field deadline-policy BINDING_VALIDITY actual/maximum and all existing nesting/deadline rules. If the approved deployment policy cannot permit60s, BLOCK; do not shorten via min(), widen the policy, substitute a fixture, read a mutable configuration or invent a default. Actual policy compatibility, complete critical-path latency and margin must be proven in the separate signing-window review. This gate installs or changes no lifetime, policy row or numeric enforcement bound.

Ordering and expiry decisions:

| Condition | Deterministic result |
| --- | --- |
| issued_at==valid_from==signed_start | ALLOW only if all other scope/clock/policy guards pass |
| issued_at<valid_from | BLOCK: this profile requires equality even if broader base interval admits it |
| valid_from<issued_at | BLOCK: source mutation guard ordering violation |
| issued_at==expires_at | BLOCK: zero/invalid window |
| valid_from==expires_at | BLOCK: exclusive end/nonempty invariant |
| expires_at<valid_from | BLOCK: inverted window |
| issued_at>fresh DB now | BLOCK: clock rollback/future issue, no timestamp repair |
| fresh DB now==T0 | ALLOW lower-bound equality, provided other guards pass |
| fresh DB now==expires_at-1us | ALLOW temporal predicate only; no guarantee next stage fits; check again at next boundary |
| fresh DB now==expires_at | BLOCK any new signing/write/continuation; if commit already sent RECOVER then exact historical REPLAY_EXISTING |
| fresh DB now==expires_at+1us | Same expired decision as equality; no rounding/grace |
| already expired before key/sign | BLOCK/abort uncommitted root; prior recovery/disposition before whole fresh root |
| expires during SIGN/JCA or before durable-write precheck | BLOCK; discard failed-root signature; rollback tentative rows; no re-sign/reuse old root |
| expires after final admitted write but before final pre-COMMIT guard | BLOCK/rollback if transaction still controlled/open; no delete-and-recreate |
| expires after valid final guard while COMMIT is in flight | RECOVER if ACK unknown; REPLAY_EXISTING if exact commit proved. Normative visibility-after-expiry rule, no retroactive undo/new live validity |
| recovery/retry after expiry | RECOVER exact state; committed -> historical REPLAY_EXISTING with no new effects; absent -> cleanup/abandonment before entirely new authorized root |
| malformed,missing,unsupported precision/range or mismatched signed/header instants | BLOCK; committed mismatch -> invariant violation/HOLD, no silent field repair |

Durability: B reserves identities in existing immutable public context, C captures T0 before key/governance, D/E use the fixed tuple for canonical manifest/signature, and F stages header/original/all required controls alongside V040 rows in that same T_REG. All DB temporal values become durable together only at T_REG COMMIT. Staged writes are not durable rows. Any possibly durable outcome requires authoritative query first. Existing external immutable original-input components preserve public temporal bytes without a new recovery table/column/journal. Missing capture context or a lost write outcome is uncertainty, never zero/absence.

A known controlled uncommitted failure aborts the complete preparation. On process death the key is lost by the preserved prior doctrine. Fresh T0 belongs only to a separately authorized entire fresh root after old disposition is proven; changing only dates/IDs inside the old root is forbidden. If the header was committed, recover its actual original tuple and signed input; never sample a new issuance time. Partial/corrupted durable times/rows are invariant violations requiring existing ADMIN escalation. Cleanup remains DISABLED authority then RETIRED key at the prior correct terminal event; no cleanup writes occur here.

Replay/idempotency matrix:

| ID | Case | Result |
| --- | --- | --- |
| R1 | Same request/plan first execution | ALLOW only the one live authorized preparation captures T0 once; no actual execution in this gate |
| R2 | Identical retry before durable writes | BLOCK second mutable invocation; same uninterrupted first preparation may continue exact T0. Failed original -> RECOVER/absence/disposition before full fresh set, no old-root clock recapture |
| R3 | Retry after temporal state durable | RECOVER query-first; exact root -> REPLAY_EXISTING original tuple; never new clock basis |
| R4 | After signing before final confirmation | RECOVER commit outcome. Known open normal continuation may make first registration with exact original; failed invocation cannot reuse signature. Unknown -> query; proven absent -> abandon/fresh |
| R5 | After complete success | REPLAY_EXISTING public historical exact state, no new time/sign/binding/authority |
| R6 | After process restart | RECOVER from immutable original inputs/header; key is lost; no automatic unfinished signing/registration continuation, no fresh old-root T0 |
| R7 | Another runtime instance | BLOCK mutable duplicate; RECOVER/REPLAY_EXISTING exact approved deployment/incarnation only. Foreign runtime/incarnation BLOCK; existing ADMIN exclusion/locks, no distributed lock mechanism |
| R8 | Retry after expires_at | BLOCK fresh effect; query unknown state, historical exact replay permitted; no renewal |
| R9 | Recovery after expires_at | RECOVER exact durable root then historical replay or confirmed absence/orphan terminal cleanup; preserve original window |
| R10 | Same ceremony with a new wall-clock sample | BLOCK any basis replacement; fresh sample is eligibility observation only. No alternate temporal identity under same root |

Watchdog may later observe original deadlines, fresh DB wall-clock/health facts and existing transaction/idle/execution bounds. It detects eligibility loss and enforces existing bounded cancellation/drain duties. It does not author expiry: crossing the immutable exclusive endpoint determines expiry; only existing ADMIN governs durable EXPIRED/REVOKED lifecycle. It cannot alter any header instant, renew a window, sign/retry/create a ceremony or decide whether an unknown commit succeeded. This gate neither adds a scheduler/timer/coordinator/lock service nor changes signaling authority. WATCHDOG_STATUS=OPEN; H01_STATUS=OPEN; G3F_4_STATUS=HOLD; ROOM_OPERATIONAL=NO; RUNTIME_PROOF_COMPLETE=NO.

H01 effect: the selected temporal mapping removes a design prerequisite ambiguity once promoted, but does not qualify the previously failing numerical/transport/RR/timing envelope. H01 itself is unchanged, not closed or downgraded. Gate findings and inherited findings have separate explicit counts; no scope laundering.

Adversarial design matrix (all rows are design decisions, not executed runtime tests; any reference to mutation is future permitted canonical action, while allowed mutation in THIS gate is always NONE):

| ID | PRECONDITION | EXPECTED DECISION | AUTHORITATIVE FACT | ALLOWED MUTATION (future only) | FORBIDDEN MUTATION | RECOVERY PATH | FAIL-CLOSED CONDITION |
| --- | --- | --- | --- | --- | --- | --- | --- |
| T01 | Different DB values across retry | BLOCK replacement / RECOVER existing root | Original retained T0/header is identity, not fresh observation | Read original public state | Resample original identity | Prior query-first root disposition | Missing original basis or unknown writer |
| T02 | Application clock behind DB | ALLOW only if DB predicate permits; otherwise BLOCK | Fresh DB wall clock | Read DB time only | Client clock override | DB-authoritative classification | DB clock unavailable/invalid |
| T03 | Application clock ahead DB | Same as T02 | Fresh DB wall clock | Read DB time only | Client grace or future dating | DB-authoritative classification | DB clock unavailable/invalid |
| T04 | Wall clock rolls back | BLOCK new effect on observed regression / RECOVER after interruption | DB observation N<T0 or N<last observed N; original window/terminal lifecycle retained | Read evidence; later existing ADMIN terminal handling only | Renewal, expiry reversal or guessing clock health | No mutable resume without qualified continuity; interruption -> prior recovery | Unproven clock continuity, regression, or unavailable qualifying host evidence |
| T05 | Precision truncation changes equality | BLOCK | Exact epoch microseconds and canonical bytes | Read validation only | Truncate/round to manufacture match | HOLD malformed root | Any nanos%1000 nonzero or changed round-trip |
| T06 | Serialization changes precision | BLOCK | Original six-fraction UTC text and signed-i64 header bytes | Read decode/re-encode only | Alternative byte encoding | HOLD exact-byte mismatch | Loss/addition of nonzero precision or noncanonical text |
| T07 | Timezone conversion alters instant | BLOCK | Typed instant/microseconds; manifest canonical Z text | Equivalent typed DB display conversion only | Local-time reinterpretation or non-Z manifest form | Reject rather than repair | Instant/epoch mismatch |
| T08 | valid_from earlier than issued_at | BLOCK | Frozen equality profile and source ordering guard | None | Backdate lower bound | HOLD committed malformed root | Any inequality to signed start |
| T09 | expires_at equals valid_from | BLOCK | Nonempty half-open window | None | Zero TTL or artificial epsilon | HOLD/reject | End<=start |
| T10 | expires_at earlier than valid_from | BLOCK | Exact checked+60000000us | None | Swap, clamp or repair fields | HOLD/reject | Inverted or corrupted window |
| T11 | Expiry during signature operation | BLOCK/abort | Fresh DB post-sign/JCA observation >=end | Rollback tentative registration only in future controlled transaction | Reuse signature or extend window | Discard ephemeral state; query if outcome unknown; proven disposition before fresh root | Expiry or absent qualifying observation |
| T12 | Expiry after signature before binding | BLOCK before new write/final guard; in-flight commit RECOVER | Fresh DB observation and whether COMMIT was sent | Rollback only when known open; historical inspection otherwise | Infer rollback of unknown COMMIT | Prior exact query-first classification | No fresh eligible DB guard or unknown outcome |
| T13 | Durable tuple exists but ACK lost | RECOVER then REPLAY_EXISTING exact | Header/original/control exact identity and prior predicates | Read-only inspection | Blind INSERT/resign/new timestamps | Quiescence then corrected nonsecret exact snapshot | TC-R01 unresolved, partial/missing/conflicting row |
| T14 | Retry samples new timestamp | BLOCK as identity input | Original T0/canonical commitments | Sample only fresh eligibility clock | Replace T0 even before durable commit | Same root original-or-HOLD; failed root disposition before fresh set | Unrecoverable original context |
| T15 | Crash after time capture | RECOVER; no unfinished mutable resume | Frozen public context or proven absence under existing authority | Existing public inspection/terminal disposition only | Restore private key/new T0 for old IDs | Prior C8/C2/precommit recovery; abandon whole root only after proof | Missing context/quiescence or unknown durable state |
| T16 | Crash after signature | RECOVER; signature reuse DENY | Original public envelope/immutable context, no private-key persistence | Read exact original only | Re-sign, renew or submit failed-root signature again | Prior C6/C7 and complete root classification | Unknown state/context; no private-key recovery |
| T17 | Crash after durable binding | RECOVER then REPLAY_EXISTING historical | Exact committed header/original/controls | Read-only exact historical state | Duplicate registration/command authority | Prior C14-C16 and terminal signer cleanup at correct event | TC-R01/partial/conflicting state |
| T18 | Restart after expiry | RECOVER/REPLAY_EXISTING history; BLOCK fresh effects | Original expiry plus exact durable terminal/current state | Existing governed terminal cleanup later, no timestamp write | Automatic activation/renewal | No restored time-sensitive authority; proof before fresh root | Missing originals, unqualified clock continuity, unresolved effects |
| T19 | Watchdog observes stale ceremony | BLOCK new admission/continuation; detect/drain under existing duty | Original header deadline + current DB observations/health | Only existing bounded detection/enforcement, later ADMIN lifecycle handling | Authoring time, signing or new binding | Exact ADMIN query-first disposition | Watchdog unavailable/stale/unsafe identity; remains OPEN |
| T20 | Two runtimes race same root | BLOCK duplicate writer; RECOVER winner outcome | Existing immutable allocation custody and canonical key/authority locks | One original registration only at future authorized execution | Second capture/sign/attempt UUID or lock service | Observe exact root after quiescence; no blind duplicate | Cannot prove original-owner/writer disposition |
| T21 | Completed ceremony replay | REPLAY_EXISTING | Original canonical temporal tuple/receipts | Read only | New timestamps or effect | Exact historical verification only | Changed scope/identity/receipt |
| T22 | Policy lifetime changes after capture | BLOCK live continuation on policy drift | Original independently approved immutable version/digest; fixed60s unchanged | Read/recover only | Adopt newer TTL/cap or mutate old policy | Abort if open; query unknown commit; retain old history | Policy/header/readiness mismatch |
| T23 | Policy lifetime changes after completion | REPLAY_EXISTING history; BLOCK old root for new-policy effect | Original tuple and original immutable policy binding | Read original history | Recalculate old expiry under new policy | Existing historical root recovery | Trying to use old root as newly approved configuration |
| T24 | Corrupt or missing time field | BLOCK | All three actual instants and exact two signed endpoints required | Read detect only | Default, NULL->zero, repair or placeholder | HOLD/escalate malformed committed state | Absent/invalid/mismatched field |
| T25 | Overflow/out-of-range time | BLOCK | Exact checked signed-i64 microsecond arithmetic and common four-digit UTC profile | Read validate only | Saturate, clamp, float arithmetic or wrap | Reject before any key/sign/effect | Any unsupported endpoint or failed DB/JDBC/canonical round-trip |
| T26 | Exactly at expires_at | BLOCK any new effect; RECOVER unknown commit; REPLAY_EXISTING history | Fresh DB N>=end, exclusive end | Read history/terminal disposition only | Expiry-inclusive grace/clock recapture | Exact committed-vs-absent classification | Treating equality as valid |
| T27 | Duplicate invocation same plan | BLOCK second mutable invocation | Existing (incarnation,plan_id)/binding uniqueness and frozen input custody | Read winner outcome only | Generate partial IDs or alternate timestamp tuple | Prior idempotency and query-first path | Unknown lineage/conflict |
| T28 | Old ceremony under new configuration | BLOCK new effects; REPLAY_EXISTING original history | Original policy/version/digest, deployment/incarnation and signed endpoints | Read exact originals | Rebind policy/configuration/incarnation or renewal | Existing domain/ADMIN reconciliation, then separately authorized full fresh root | Any substituted configuration or lost original input |

Remediation handoff, not executed: revise the prior recovery Q12 public column allowlist and SELECT to omit possession_digest, and rebuild its composed nonsecret snapshot without that column. Apply the same explicit no-secret/proof/private-digest check to every projected/nested receipt field, retaining identity/state/deadline/receipt metadata needed for canonical outcome classification. Verify the complete public query set, privacy property, C0-C16/R1-R10 behavior, exact historical replay and unchanged authority without DB execution. Record the specific correction as an explicit bounded supersession of the false nonsecret claim. Do not silently edit the previous PASS/history in this gate; do not change SQL authority/schema or generate keys/signatures. Then revalidate this time gate before any checkpoint/signing-window progression. No broader recovery architecture or additional authority is required.

Validation result:

```json
{
  "review_kind": "FORENSIC_DESIGN_ONLY_NO_RUNTIME_PROOF",
  "prior_evidence_read": 164,
  "tracked_files_preserved": 1255,
  "evidence_ledger_rows": 18,
  "adversarial_scenarios": 28,
  "replay_cases": 10,
  "boundary_cases": 17,
  "source_signature_binding": "TWO_SIGNED_ENDPOINTS_THREE_DERIVED_HEADER_INSTANTS",
  "clock_or_runtime_time_capture": 0,
  "DB_connections": 0,
  "DB_mutations": 0,
  "UUID_generation": 0,
  "key_generation": 0,
  "signatures": 0,
  "arithmetic_and_wire_checks": "PASS_DESIGN",
  "prior_recovery_secret_exclusion": "FAIL_DIRECT_SOURCE_CONTRADICTION_TC_R01",
  "gate_result": "HOLD",
  "gate_blocker_count": 0,
  "gate_high_count": 1,
  "baseline_high_count": 2,
  "overall_high_count": 3
}
```

The artifact is reread and checked for all required contract/return fields, T01-T28/R1-R10 coverage and no extra repository path. All prior tracked/source/evidence hashes are verified unchanged; only this evidence is untracked. No DB was connected, container started, migration changed, key/private material/identifier created or signature produced. Synthetic checked arithmetic/binary framing checks pass; the privacy source check deliberately fails on TC-R01. Container status is observed only through docker inspect, not a database operation. No database pre/post equality claim is inferred from historical snapshots.

Decision: final gate cannot PASS while TC-R01 is HIGH. Preserve this one authorized dirty evidence file; no staging/commit/push, ADR/SPEC/source edit, merge/rebase/main operation or next-gate execution. NEXT_GATE=STOP_AND_REMEDIATE. After the bounded correction and a successful rerun with gate B0/H0 and local=remote/clean, the requested next gate is G3F_4_FINAL_CEREMONY_SIGNING_WINDOW_CONTRACT_REVIEW (not started here).

Complete required return; Git outcome is unchanged baseline and one authorized new file:

```json
{
  "G3F_4_FINAL_CEREMONY_TIME_CONTRACT_CLOSURE": "HOLD",
  "BRANCH": "checkpoint/package-0090-cloud-handoff",
  "BASELINE_HEAD": "1ffbaa312f3c80f478c89298d2e3914ae50ae785",
  "FINAL_LOCAL_HEAD": "1ffbaa312f3c80f478c89298d2e3914ae50ae785",
  "FINAL_REMOTE_HEAD": "1ffbaa312f3c80f478c89298d2e3914ae50ae785",
  "LOCAL_EQUALS_REMOTE": "YES",
  "WORKTREE_CLEAN": "NO",
  "TIME_CONTRACT_AUTHORITY": "Existing PLAN_BINDING_ADMIN for immutable binding profile; existing separately governed rehearsal S2A approval authority for manifest lifetime. Database cluster alone supplies instants.",
  "TIME_CAPTURE_EVENT": "FINAL_CEREMONY_TIME_CAPTURE: once in the already selected T_REG after canonical locks, before key birth/governance/signing; value is the DB-owned opening instant of that SAME transaction, not the time of the read.",
  "TIME_SOURCE": "T0 := pg_catalog.transaction_timestamp() from exact T_REG; fresh pg_catalog.clock_timestamp() on same approved cluster for every eligibility/recovery observation. These are two functions of one authority, not two independent clocks.",
  "TIMEZONE": "UTC",
  "PRECISION": "INTEGER_MICROSECONDS_NO_ROUNDING",
  "ISSUED_AT_CONTRACT": "SELECTED issued_at=T_REG transaction opening T0",
  "VALID_FROM_CONTRACT": "SELECTED valid_from=issued_at=signed approvalWindowStart=T0",
  "EXPIRES_AT_CONTRACT": "SELECTED expires_at=signed approvalWindowEnd=T0+60000000us",
  "EXPIRY_BOUNDARY_CONTRACT": "SELECTED [start,end); canonical write/postcheck/pre-COMMIT eligibility; commit visibility may be later",
  "SIGNING_WINDOW_CONTRACT": "IMMUTABLE_NONRENEWABLE_60_SECONDS; operational feasibility NOT_PROVEN",
  "TEMPORAL_IDENTITY_STABLE_ACROSS_RETRY": "YES_SELECTED_DESIGN_NOT_PROMOTED",
  "REPLAY_IDEMPOTENCY": "DEFINED_ORIGINAL_TUPLE_ONLY; TC_R01_REMEDIATION_REQUIRED",
  "RECOVERY_DETERMINISM": "PRESERVED_QUERY_FIRST; NONSECRET_QUERY_PROJECTION_CONTRADICTED_TC_R01",
  "CRYPTOGRAPHIC_TIME_BINDING": "DEFINED_DERIVED_FROM_TWO_SIGNED_ENDPOINTS; future exact-equality validation required, not direct header signature",
  "WATCHDOG_STATUS": "OPEN",
  "H01_STATUS": "OPEN",
  "G3F_4_STATUS": "HOLD",
  "BLOCKER_COUNT": 0,
  "HIGH_COUNT": 1,
  "MEDIUM_COUNT": 0,
  "LOW_COUNT": 0,
  "FINDING_COUNT_SCOPE": "THIS_FORENSIC_GATE; baseline B0/H2/M0/L0 preserved separately, overall B0/H3/M0/L0 with TC-R01",
  "DATABASE_MUTATION": "NO",
  "KEY_GENERATION": "NO",
  "PRIVATE_KEY_PERSISTENCE": "NO",
  "SIGNATURE_CREATION": "NO",
  "IDENTIFIER_GENERATION": "NO",
  "PRODUCTION_IMPLEMENTATION": "NO",
  "ARTIFACTS_CREATED": [
    "docs/evidence/PACKAGE-0090-G3F-4-FINAL-CEREMONY-TIME-CONTRACT-CLOSURE.md"
  ],
  "ARTIFACTS_MODIFIED": [],
  "COMMIT": "NO_GATE_HOLD",
  "PUSH": "NO_GATE_HOLD",
  "NEXT_GATE": "STOP_AND_REMEDIATE"
}
```

Primary source pins:

| Source / location | SHA256 |
| --- | --- |
| docs/specifications/SPEC-0090-governed-offline-field-proof-exclusive-capability-composition.md | `d12acc86cbed8d56cd774f427b79dce26258a36ac65a7d78bf2cb1fb37fd9a92` |
| docs/adr/ADR-0090-governed-offline-field-proof-exclusive-capability-composition.md | `e1c26d2f202684d5ace54408c83a0fcf100085864270f0c32cb077b9398566a9` |
| applications/marketplace-operations/src/main/kotlin/io/flooow/marketplace/operations/authorization/ApprovalAttestationCanonicalCodec.kt | `74763cd4b0c3ab49b3f2c882f724df3ec10561f9aaa452c7b29fd1d6a943b26d` |
| applications/marketplace-operations-persistence-postgres/src/main/resources/db/migration/V043__create_governed_offline_field_proof_capability_composition.sql | `3301b254e883ae2ebf9e1d41036f15bc7839c1ae9e2404e692bc2ec864204109` |
| docs/evidence/PACKAGE-0090-G3F-4-BINDING-TIMESTAMP-AUTHORITY.json | `1e04dd75234935bff8fcc3b215c275cd3cdbdf69b837081e96314b08ffc880a9` |
| docs/evidence/PACKAGE-0090-G3F-4-AMBIGUOUS-COMMIT-RECOVERY.json | `f22949d33e9daab11765e30f8b3da47be6e874c68f6f3e52e44f81cc367d5743` |
| docs/evidence/PACKAGE-0090-G3F-4-TRANSPORT-MODEL-REVIEW.md | `d8488c63390f3c29c9775c8f402e318fd6eab35416a9d0371a9d52f28275f192` |
| C:/Users/xmz_r/.codex/attachments/fa38ec36-d0cf-469d-9ee1-cf97aaa4ef5a/Pasted text.txt | `cd82b95093297ee0b62153fe2704134cf16615fa4c4040545e9e60260b0e6b1e` |
| applications/marketplace-operations-persistence-postgres/src/main/resources/db/migration/V041__create_s2a_accepted_attestation.sql | `3ff1421dd56de17270a9c44054055c0c1afc91f855d903697268088a53f1182d` |
| applications/marketplace-operations-persistence-postgres/src/main/resources/db/migration/V042__create_s2a_attestation_consumption_and_attested_command_authority.sql | `3bfc5f7c95d235235ff8444453523a6a757980b464bff60ad5150e622d2f1ae1` |
| applications/marketplace-operations/src/main/kotlin/io/flooow/marketplace/operations/authorization/ApprovalGovernance.kt | `bb71114ceb00501499adefe1ce3a1418cdb2a0e36d71fdf5f44fa54773a246dc` |

All prior Package0090 evidence read and preserved (including prior recovery, signing-window, clock, policy, authority and historical runtime provenance). Filenames do not establish behavior; decisions use the source ledger above:

| Prior artifact | Bytes | SHA256 |
| --- | --- | --- |
| [PACKAGE-0090-BINDING-AUTHORITY-INTEGRITY.json](PACKAGE-0090-BINDING-AUTHORITY-INTEGRITY.json) | 15365204 | `5c0f957f9682f744e1f88a4c4cef0f479a8909bea8f28c343ccdc1e679e54001` |
| [PACKAGE-0090-BINDING-PROVISIONING-CONTRACT-DESIGN.md](PACKAGE-0090-BINDING-PROVISIONING-CONTRACT-DESIGN.md) | 14465 | `5add8c6da53ffcb722cd78fdc4f4e35c1a50f43431dd4349d8684f02b8254787` |
| [PACKAGE-0090-BINDING-PROVISIONING-MATRIX.json](PACKAGE-0090-BINDING-PROVISIONING-MATRIX.json) | 561827 | `8be5d6141b6cfa459137e778362be4161a9f6b440ea07981aca3c24a812eed5a` |
| [PACKAGE-0090-BINDING-PROVISIONING-NEGATIVE-MATRIX.json](PACKAGE-0090-BINDING-PROVISIONING-NEGATIVE-MATRIX.json) | 9828 | `5efbd2450fd94990a1cb7c0cbcda789d747006c76176914af96afb7d16689496` |
| [PACKAGE-0090-CURRENT-INDEPENDENT-SOURCE-REVIEW.json](PACKAGE-0090-CURRENT-INDEPENDENT-SOURCE-REVIEW.json) | 505867 | `631b68e8c483ab283c4caa11b96bd6ceac60f3226c6af9bac14d68e564699d36` |
| [PACKAGE-0090-DEPLOYMENT-INCARNATION-APPROVAL-MATRIX.json](PACKAGE-0090-DEPLOYMENT-INCARNATION-APPROVAL-MATRIX.json) | 16532764 | `ca5550e9273c95b5d91ad9c33e6c8bedd0771135e7f16a2303c76de72d67e1da` |
| [PACKAGE-0090-ED25519-NATIVE-REVIEW.json](PACKAGE-0090-ED25519-NATIVE-REVIEW.json) | 31105 | `f5e255dbd134656e58af257c411ca5bd36a5b86b432117bbccf710eaba91f5dc` |
| [PACKAGE-0090-ED25519-NATIVE-REVIEW.md](PACKAGE-0090-ED25519-NATIVE-REVIEW.md) | 9277 | `ef1c29c29ea19b221bfa5c3a9e03194576587c028ee8b8074b9f75043cd739ae` |
| [PACKAGE-0090-ENROLLMENT-BINDING-CONTRACT-CLOSURE.md](PACKAGE-0090-ENROLLMENT-BINDING-CONTRACT-CLOSURE.md) | 10003 | `f091d0b11446151dcb9db3636f8d1bc82c9ed0c724767e00fb537a267b64ac86` |
| [PACKAGE-0090-ENROLLMENT-ENTRYPOINT-AUTHORITY-REVIEW.json](PACKAGE-0090-ENROLLMENT-ENTRYPOINT-AUTHORITY-REVIEW.json) | 31486 | `a719df6b7ce319d92d701d012711eafd1d46df45a84a84e98d0d944e87858657` |
| [PACKAGE-0090-ENROLLMENT-ENTRYPOINT-AUTHORITY-REVIEW.md](PACKAGE-0090-ENROLLMENT-ENTRYPOINT-AUTHORITY-REVIEW.md) | 18739 | `1b673e92df11070105e0bfb326ab6b23aa262f3543af2ab73476741742412c7b` |
| [PACKAGE-0090-ENROLLMENT-ENTRYPOINT-READONLY-SNAPSHOT.json](PACKAGE-0090-ENROLLMENT-ENTRYPOINT-READONLY-SNAPSHOT.json) | 559267 | `3b9cf2ca67890eb3cb42f9ee451b5c495a5fd2a5403b7454831b2965e61aadb0` |
| [PACKAGE-0090-EXECUTOR-FINAL-TESTS.txt](PACKAGE-0090-EXECUTOR-FINAL-TESTS.txt) | 914 | `9b149f2b6bcfb5ef8ec1de75dcb9758ab5f0570180ff73263d923f140bb63bf5` |
| [PACKAGE-0090-FULL-TESTS.txt](PACKAGE-0090-FULL-TESTS.txt) | 26075 | `9d4996a557ba6cbabc5a1e90a6e70e596d48c19170b039c680d74a207aabdbc0` |
| [PACKAGE-0090-G3F-3B-CATALOG-GOLDEN-CLOSURE.md](PACKAGE-0090-G3F-3B-CATALOG-GOLDEN-CLOSURE.md) | 2421 | `39e220d5fabcf62e1e37c08603b17681a283a13ec31c7813bba4c718c8373e40` |
| [PACKAGE-0090-G3F-3B-CATALOG-GOLDENS.json](PACKAGE-0090-G3F-3B-CATALOG-GOLDENS.json) | 284137 | `f53bbfb436348ea2c2e75599946fe883c02ad03d0b91ddc5196b296ab3c65b2c` |
| [PACKAGE-0090-G3F-3B-CLOUD-EXECUTION.md](PACKAGE-0090-G3F-3B-CLOUD-EXECUTION.md) | 12044 | `5413f976c7d157557250e74918b6b537446a633b6eccd8f23b976ff9716ed5eb` |
| [PACKAGE-0090-G3F-3B-CODEC-GOLDENS.json](PACKAGE-0090-G3F-3B-CODEC-GOLDENS.json) | 53108 | `2876d9774823f285fc714cf8ad021cd0b38adb568614a399defa6cc2cd1d1766` |
| [PACKAGE-0090-G3F-3B-EVIDENCE-FIXTURE-001.json](PACKAGE-0090-G3F-3B-EVIDENCE-FIXTURE-001.json) | 7765 | `0c071e9f4de63f3515a3147ea979e872012f3d90602b02fa09f895a869dde15c` |
| [PACKAGE-0090-G3F-3B-FIXTURE-001.json](PACKAGE-0090-G3F-3B-FIXTURE-001.json) | 5744 | `edfb8fe983a2adc5c7fed224fbc418108c4dbfcba9caa67fd15f640d92ddf820` |
| [PACKAGE-0090-G3F-3B-FIXTURE-CLOSURE.md](PACKAGE-0090-G3F-3B-FIXTURE-CLOSURE.md) | 6533 | `4715aa42f0bb5402d4be12b2f18ea53c98bb1211d0e023216cb78c194b223a0c` |
| [PACKAGE-0090-G3F-3B-INTERNAL-P-SOURCE-REVIEW.md](PACKAGE-0090-G3F-3B-INTERNAL-P-SOURCE-REVIEW.md) | 3442 | `c412a8b08e28d39ace980f95e7e3df7cdc7bf28f7881f398f36266b0730194b9` |
| [PACKAGE-0090-G3F-3B-INTERNAL-Q-SOURCE-REVIEW.md](PACKAGE-0090-G3F-3B-INTERNAL-Q-SOURCE-REVIEW.md) | 4581 | `28551d80e34c2471813333f44dfce09589616c4cbcd8644df7a43a6d6180c7c9` |
| [PACKAGE-0090-G3F-3B-INTERNAL-Z-SOURCE-REVIEW.md](PACKAGE-0090-G3F-3B-INTERNAL-Z-SOURCE-REVIEW.md) | 2129 | `7559b27c50ec158fbeb7600b3e0c17817cc8764bfac775373560acadd6a47f59` |
| [PACKAGE-0090-G3F-3B-ISOLATED-REHEARSAL-HANDOFF.md](PACKAGE-0090-G3F-3B-ISOLATED-REHEARSAL-HANDOFF.md) | 7706 | `0b4ad2cfd1358613bbae22f3c2a9e1c95f93494f7c6e036f0812e02892e08f76` |
| [PACKAGE-0090-G3F-3B-NORMATIVE-EVIDENCE-CLOSURE.md](PACKAGE-0090-G3F-3B-NORMATIVE-EVIDENCE-CLOSURE.md) | 3650 | `a407056d3581f1e6aad4b70337cef2c59a548a77980e0803ff298693d19a85a8` |
| [PACKAGE-0090-G3F-3B-POST-H02-SECURITY-REVIEW.json](PACKAGE-0090-G3F-3B-POST-H02-SECURITY-REVIEW.json) | 2793 | `8e01fe605a44b5575bbf831d39c8ec6959fa8e5b9f4c784e8d1f1af6cb066b0f` |
| [PACKAGE-0090-G3F-3B-POST-H02-SECURITY-REVIEW.md](PACKAGE-0090-G3F-3B-POST-H02-SECURITY-REVIEW.md) | 7083 | `7f99b920c2c0e00b406a8fa73503748b7f07fe3350eefb27c3d7b1f753192033` |
| [PACKAGE-0090-G3F-3B-PUBLIC-WRAPPER-PREREQUISITES.json](PACKAGE-0090-G3F-3B-PUBLIC-WRAPPER-PREREQUISITES.json) | 26233 | `cf4f6e0aae1649782e1eb21b8994906e02410b9876ca1936a8374eb237fedde0` |
| [PACKAGE-0090-G3F-3B-PUBLIC-WRAPPER-PROGRESS.json](PACKAGE-0090-G3F-3B-PUBLIC-WRAPPER-PROGRESS.json) | 3661 | `4195c94597cf3439ec23c1afd55a3f4c6802cb62da2f553ca01b49101460f31b` |
| [PACKAGE-0090-G3F-3B-PUBLIC-WRAPPERS-CONTRACT-HOLD.md](PACKAGE-0090-G3F-3B-PUBLIC-WRAPPERS-CONTRACT-HOLD.md) | 5024 | `6c579261c4c791262258fc999f149e7d523ed9561209ba3ab47d62b0d59213d3` |
| [PACKAGE-0090-G3F-3B-S01-READINESS-AUTHORITY.json](PACKAGE-0090-G3F-3B-S01-READINESS-AUTHORITY.json) | 12635 | `1b1e835256d0e222bf6e445738e59a7805e9107d1b484f43725d2d94c5308645` |
| [PACKAGE-0090-G3F-3B-S01-TARGET-AUTHORITY-HOLD.md](PACKAGE-0090-G3F-3B-S01-TARGET-AUTHORITY-HOLD.md) | 6033 | `5817365e55ee35f27fcb94c2f7fba5440000244340d38c0c08afeee64be09968` |
| [PACKAGE-0090-G3F-3B-S01-TARGET-CLOSURE.json](PACKAGE-0090-G3F-3B-S01-TARGET-CLOSURE.json) | 300273 | `3778f846c1e0a0baa700f231e4627601c635fbcce42d6105349f83d27d77e0d6` |
| [PACKAGE-0090-G3F-3B-S01-TARGET-SOURCE-REVIEW.md](PACKAGE-0090-G3F-3B-S01-TARGET-SOURCE-REVIEW.md) | 3234 | `8b5e8d2d0e7a7365a3f7e9a059bcd5f496d0b935991414a6e3b7f4153f5614b0` |
| [PACKAGE-0090-G3F-3B-S02-CONSUMER-AUTHORITY-HOLD.md](PACKAGE-0090-G3F-3B-S02-CONSUMER-AUTHORITY-HOLD.md) | 3809 | `ba97d272c245ab2a387a116afb81ccb65ec62899c65a4d46640dadbe42b73968` |
| [PACKAGE-0090-G3F-3B-S02-CONSUMER-AUTHORITY.json](PACKAGE-0090-G3F-3B-S02-CONSUMER-AUTHORITY.json) | 8909 | `44bd3a1187c247a4c016890c339d8228d2e83be765aef9e303e53f804fd9e624` |
| [PACKAGE-0090-G3F-3B-S02-VERIFICATION-PATH-HOLD.md](PACKAGE-0090-G3F-3B-S02-VERIFICATION-PATH-HOLD.md) | 4892 | `6c6f19474942bcff9f1cf803f60e8743b4775b2c794f1b69ed0fb29392f8edf2` |
| [PACKAGE-0090-G3F-3B-SOURCE-VALIDATION.json](PACKAGE-0090-G3F-3B-SOURCE-VALIDATION.json) | 10259 | `9e547dfd80671c2f4d34839ca4bfa537ca221a5a52a5a78b3677fa965a8c0b67` |
| [PACKAGE-0090-G3F-4-08006-DIAGNOSTICS.json](PACKAGE-0090-G3F-4-08006-DIAGNOSTICS.json) | 28711321 | `448b0e84a53763f843fc73f68c6a07446a06d77ea215f5fdc73d964d6db5d18e` |
| [PACKAGE-0090-G3F-4-AMBIGUOUS-COMMIT-RECOVERY.json](PACKAGE-0090-G3F-4-AMBIGUOUS-COMMIT-RECOVERY.json) | 77751 | `f22949d33e9daab11765e30f8b3da47be6e874c68f6f3e52e44f81cc367d5743` |
| [PACKAGE-0090-G3F-4-APPROVAL-AUTHORITY-CLOSURE.md](PACKAGE-0090-G3F-4-APPROVAL-AUTHORITY-CLOSURE.md) | 8271 | `399040f3e47892302bff29a7e5920c8663f8b3f01cc91fb2576f58e8564cf24a` |
| [PACKAGE-0090-G3F-4-ATTESTATION-HEADER-TRANSACTION-GRAPH.json](PACKAGE-0090-G3F-4-ATTESTATION-HEADER-TRANSACTION-GRAPH.json) | 38733 | `7b283eb7a7f12d86753ad2b348caf0252a521c5dd0bba2c61eaff84fb2b2b677` |
| [PACKAGE-0090-G3F-4-BINDING-DEPENDENCY-GRAPH.json](PACKAGE-0090-G3F-4-BINDING-DEPENDENCY-GRAPH.json) | 2233692 | `da505a68c1bfd9099d01308a0dd7ed27797017efc9e8cf089521331138c3df85` |
| [PACKAGE-0090-G3F-4-BINDING-GENERATION-AUTHORITY.json](PACKAGE-0090-G3F-4-BINDING-GENERATION-AUTHORITY.json) | 6771 | `961119a4894ca5f77540a13824712ec985d63ceabf430e959a11faf7fca93add` |
| [PACKAGE-0090-G3F-4-BINDING-HEADER-40-FIELD-MATRIX.json](PACKAGE-0090-G3F-4-BINDING-HEADER-40-FIELD-MATRIX.json) | 197580 | `908ffd5ed0b61a506ea8522309efacae43b660e7ffbcaf7a51de890ac7c5afec` |
| [PACKAGE-0090-G3F-4-BINDING-HEADER-INPUT-CONTRACT-CLOSURE.md](PACKAGE-0090-G3F-4-BINDING-HEADER-INPUT-CONTRACT-CLOSURE.md) | 17118 | `2f053e975cfcd0b6413c1982cd865bf7b37e5b2b65253e51b2cc3fff548cd8a0` |
| [PACKAGE-0090-G3F-4-BINDING-HEADER-INPUT-MATRIX.json](PACKAGE-0090-G3F-4-BINDING-HEADER-INPUT-MATRIX.json) | 44779 | `dd067e6b45207cfc41528f9e3309b02d8f95481000e6404229f2a069cc333646` |
| [PACKAGE-0090-G3F-4-BINDING-PLAN-AUTHORITY-CLOSURE.md](PACKAGE-0090-G3F-4-BINDING-PLAN-AUTHORITY-CLOSURE.md) | 12914 | `e8e1b23236f32116c7c1d3ad9c59160b9fff370c852a60594003dfcfaf979af9` |
| [PACKAGE-0090-G3F-4-BINDING-PLAN-AUTHORITY-MATRIX.json](PACKAGE-0090-G3F-4-BINDING-PLAN-AUTHORITY-MATRIX.json) | 58809 | `4b6183c0eef78cf254e1ac3ab30b73b0e9a30c76c00362078a44377c6ad8a9e3` |
| [PACKAGE-0090-G3F-4-BINDING-PLAN-FINGERPRINT-CONTRACT.json](PACKAGE-0090-G3F-4-BINDING-PLAN-FINGERPRINT-CONTRACT.json) | 9672 | `493208b50d2da8f81185f1c8dc93c16676f8ced3ee064133f8b975c798b40de8` |
| [PACKAGE-0090-G3F-4-BINDING-PLAN-REGISTRATION-INPUT-CLOSURE.md](PACKAGE-0090-G3F-4-BINDING-PLAN-REGISTRATION-INPUT-CLOSURE.md) | 16852 | `44e07adf21d4cc9cb823079acef3aa4f9724e4e07da19a823ce902c825f21db9` |
| [PACKAGE-0090-G3F-4-BINDING-REGISTRATION-ID-LINEAGE.json](PACKAGE-0090-G3F-4-BINDING-REGISTRATION-ID-LINEAGE.json) | 1057154 | `0c51ba0d4e74fc06b7db790ac3ad925bc6ae053b76cd9b0337e89783e0dbf6a7` |
| [PACKAGE-0090-G3F-4-BINDING-TIMESTAMP-AUTHORITY.json](PACKAGE-0090-G3F-4-BINDING-TIMESTAMP-AUTHORITY.json) | 7233 | `1e04dd75234935bff8fcc3b215c275cd3cdbdf69b837081e96314b08ffc880a9` |
| [PACKAGE-0090-G3F-4-CANONICAL-BINDING-PREREQUISITE-SCOPE.md](PACKAGE-0090-G3F-4-CANONICAL-BINDING-PREREQUISITE-SCOPE.md) | 10961 | `47f863125c3dd2272eddac768f6ca293b4d8378eefc429c29f6d153b4aac251d` |
| [PACKAGE-0090-G3F-4-CANONICAL-SOURCE-COMMITTER-RUNTIME.json](PACKAGE-0090-G3F-4-CANONICAL-SOURCE-COMMITTER-RUNTIME.json) | 15963994 | `4b8dffa159baf07506b98645b1b60343768f52aa81278b106d39424ec0f6841e` |
| [PACKAGE-0090-G3F-4-CEREMONY-CRASH-POINT-MATRIX.json](PACKAGE-0090-G3F-4-CEREMONY-CRASH-POINT-MATRIX.json) | 44624 | `9313ed5258fcaa17b6d52fb41e13129959ea2c2f3c4b459f5495af25f8a616f4` |
| [PACKAGE-0090-G3F-4-COMMAND-AUTHORITY-INPUT-GRAPH.json](PACKAGE-0090-G3F-4-COMMAND-AUTHORITY-INPUT-GRAPH.json) | 9082 | `6b17cdd3fc575037bbbeef70756bd09f8fcbbf13f9fd7a71b5d200f7c00dbf8b` |
| [PACKAGE-0090-G3F-4-CONCURRENCY-2.json](PACKAGE-0090-G3F-4-CONCURRENCY-2.json) | 2034 | `6c3b4f4dc20ada0013e23976c73e60a5bc86d13479e4ae71719cfded4816a234` |
| [PACKAGE-0090-G3F-4-CONCURRENCY.json](PACKAGE-0090-G3F-4-CONCURRENCY.json) | 7494 | `4fcba43d874705981f55cf77232cee618f9be6bd9e34a31ed9aa995807e08d56` |
| [PACKAGE-0090-G3F-4-DATA-SCOPE-INTEGRITY.json](PACKAGE-0090-G3F-4-DATA-SCOPE-INTEGRITY.json) | 1246988 | `edb846a66415b5861e7ef2e8c0674975b7b836611d8829d8a3d75ac20cb6b042` |
| [PACKAGE-0090-G3F-4-DNA-INVARIANT-REVIEW.md](PACKAGE-0090-G3F-4-DNA-INVARIANT-REVIEW.md) | 3106 | `c8dd9b3b3c14c73b1bbe39327477ab8a95252007c1659d763f6ca3f5fccc0bd1` |
| [PACKAGE-0090-G3F-4-DOMAIN-DEPENDENCY-GRAPH.json](PACKAGE-0090-G3F-4-DOMAIN-DEPENDENCY-GRAPH.json) | 46796 | `ef3346b9660448a8815261e16ecb7c03fb2930f0645484730d65d2d1222825cd` |
| [PACKAGE-0090-G3F-4-E2E-RUNTIME.json](PACKAGE-0090-G3F-4-E2E-RUNTIME.json) | 2837 | `9f63fda8b6728b5a8fbca903f4e7fbfc5c1b6ef68edad30149e65caa2c87ec53` |
| [PACKAGE-0090-G3F-4-ELIGIBLE-S01-TIMING.json](PACKAGE-0090-G3F-4-ELIGIBLE-S01-TIMING.json) | 8044 | `ad634aaf8ed1a885132e0f02d58401a31ed8e739dfe36325c4e2ee6c9483fb06` |
| [PACKAGE-0090-G3F-4-EPHEMERAL-REHEARSAL-CREDENTIAL-LIFECYCLE.json](PACKAGE-0090-G3F-4-EPHEMERAL-REHEARSAL-CREDENTIAL-LIFECYCLE.json) | 7276 | `6b135c84d2db7e0ddc1cd024af0a5c7385445701af6758b4c6ab2f9b86880a4a` |
| [PACKAGE-0090-G3F-4-EVIDENCE-BINDING-FINGERPRINT-MATRIX.json](PACKAGE-0090-G3F-4-EVIDENCE-BINDING-FINGERPRINT-MATRIX.json) | 30203 | `de884a0c2d83b886a072c51978fcf8020549130f0e6b18871127324fa8a8b868` |
| [PACKAGE-0090-G3F-4-EVIDENCE-BINDING-FINGERPRINT-RUNTIME.json](PACKAGE-0090-G3F-4-EVIDENCE-BINDING-FINGERPRINT-RUNTIME.json) | 12209 | `ec46ab8b9c62f6964e1fa1968f25d6954dcd22493567c6186fab7038aefc52cc` |
| [PACKAGE-0090-G3F-4-EVIDENCE-BINDING-REPRODUCIBILITY.json](PACKAGE-0090-G3F-4-EVIDENCE-BINDING-REPRODUCIBILITY.json) | 1116256 | `c42a1161499b669f3364c41697371b9fd02e185c54044bcac5f1fb405a236d8b` |
| [PACKAGE-0090-G3F-4-FINAL-ATOMIC-CEREMONY-GRAPH.json](PACKAGE-0090-G3F-4-FINAL-ATOMIC-CEREMONY-GRAPH.json) | 15041440 | `70a7e45bd3e3a03e022b692178386615cd3f36b5489b372bac086a33ea56d467` |
| [PACKAGE-0090-G3F-4-FINAL-CEREMONY-FAILURE-MATRIX.json](PACKAGE-0090-G3F-4-FINAL-CEREMONY-FAILURE-MATRIX.json) | 20538 | `9260d6410f277d887738d419a0d72320881b441d29d6863c84c62352f27a6668` |
| [PACKAGE-0090-G3F-4-FINAL-CEREMONY-RECOVERY-CLOSURE.md](PACKAGE-0090-G3F-4-FINAL-CEREMONY-RECOVERY-CLOSURE.md) | 51262 | `281fc2d1cb0f4c929d6b421bae9a4a408f9441aa5b48d6aa21b1d2cc1af74518` |
| [PACKAGE-0090-G3F-4-FINAL-HEADER-40-FIELD-MATRIX.json](PACKAGE-0090-G3F-4-FINAL-HEADER-40-FIELD-MATRIX.json) | 40300 | `6c09b93703c84c70416dd077aa8391ef96ed317fe2d422d4b4de27fa12d5324f` |
| [PACKAGE-0090-G3F-4-FINAL-REHEARSAL.md](PACKAGE-0090-G3F-4-FINAL-REHEARSAL.md) | 5020 | `050f5e8f377d3737115a6ca2cc8f0025befdc1f9ceb5e2de4745a8551fdc5d88` |
| [PACKAGE-0090-G3F-4-FIXTURE-002.json](PACKAGE-0090-G3F-4-FIXTURE-002.json) | 6533 | `55dd5e816a714987710447ca3ae40d2294d2d8f8a2baa63c26e39ff855a4fcef` |
| [PACKAGE-0090-G3F-4-GOVERNED-ECONOMIC-EVIDENCE.json](PACKAGE-0090-G3F-4-GOVERNED-ECONOMIC-EVIDENCE.json) | 60074 | `fe769ded569a40feea1b04eb856c8c0ae99dc98c81788286d7f6d63676a1b5b6` |
| [PACKAGE-0090-G3F-4-HEARTBEAT-MODEL-REVIEW.md](PACKAGE-0090-G3F-4-HEARTBEAT-MODEL-REVIEW.md) | 7579 | `bd8b75c55bd379b61d6ad1dee0f55691248213dab642005fca2be4450e5bf7fc` |
| [PACKAGE-0090-G3F-4-HISTORICAL-ATTESTATION-REUSE-MATRIX.json](PACKAGE-0090-G3F-4-HISTORICAL-ATTESTATION-REUSE-MATRIX.json) | 68827 | `bced0e65443678fa9c89ee923de52b48d7e830f131005d2e6fc0fb9cc39b90ba` |
| [PACKAGE-0090-G3F-4-IDENTITY-SIGNAL-CLOSURE.md](PACKAGE-0090-G3F-4-IDENTITY-SIGNAL-CLOSURE.md) | 13495 | `57b6fb92b71c2bff1910cd745ba7bc9dc935e4f072e96c6ec77d1ee1b744100c` |
| [PACKAGE-0090-G3F-4-IDENTITY-SIGNAL-REVIEW.json](PACKAGE-0090-G3F-4-IDENTITY-SIGNAL-REVIEW.json) | 17783 | `1b159acadfb3f86b63d20f46ae50267ef42da7c0b7a8ccdcffc17f0c7cdad010` |
| [PACKAGE-0090-G3F-4-IDENTITY-SIGNAL-RUNTIME.json](PACKAGE-0090-G3F-4-IDENTITY-SIGNAL-RUNTIME.json) | 642341 | `f0067665ae37d4e4a56c98604a7e7f72465cc0b4b386a6436ce5b0934373e0b6` |
| [PACKAGE-0090-G3F-4-INSTALLED-ACL.json](PACKAGE-0090-G3F-4-INSTALLED-ACL.json) | 221850 | `709ff68e0b56cf0b48817de326656ae07ddcc25d8b46d4eb8c1f83518a65b662` |
| [PACKAGE-0090-G3F-4-INSTALLED-CATALOG.json](PACKAGE-0090-G3F-4-INSTALLED-CATALOG.json) | 142870 | `fc1fbd866c984e76da3d7c7c256894de7f8b94898130e11f10b78976d048b715` |
| [PACKAGE-0090-G3F-4-ISOLATED-POSTGRES18-REHEARSAL.md](PACKAGE-0090-G3F-4-ISOLATED-POSTGRES18-REHEARSAL.md) | 8154 | `7fd17925b2eb7125b012a3f8d83e367fd8dfb351bd9e140dadbf1667e8e26b2f` |
| [PACKAGE-0090-G3F-4-LOGIN-EVENT-ENROLLMENT-RUNTIME.json](PACKAGE-0090-G3F-4-LOGIN-EVENT-ENROLLMENT-RUNTIME.json) | 5262 | `7ceadd1ee9100c485d9397ff300c2de5a78af7c24399472b016fcb6b18b8c949` |
| [PACKAGE-0090-G3F-4-ORIGINAL-ATTESTATION-CONTEXT-CLOSURE.md](PACKAGE-0090-G3F-4-ORIGINAL-ATTESTATION-CONTEXT-CLOSURE.md) | 38443 | `4efaff86af2bf81b0ba1045bedbb1a1903686bd3c243a5341e096d37013a1787` |
| [PACKAGE-0090-G3F-4-ORIGINAL-ATTESTATION-CONTEXT-MATRIX.json](PACKAGE-0090-G3F-4-ORIGINAL-ATTESTATION-CONTEXT-MATRIX.json) | 1119900 | `dc31510de3abc5271292e370e6dc5ed5e243cb47c9f97fa649300e1564f09e42` |
| [PACKAGE-0090-G3F-4-ORPHAN-SIGNER-RECOVERY.json](PACKAGE-0090-G3F-4-ORPHAN-SIGNER-RECOVERY.json) | 19704 | `aeff2a66622e9c9aa15f0eaac8fde81ebb1a45af926da74e32f2e62c9916c7a5` |
| [PACKAGE-0090-G3F-4-PLAN-IDENTITY-ALLOCATION-CONTRACT.json](PACKAGE-0090-G3F-4-PLAN-IDENTITY-ALLOCATION-CONTRACT.json) | 18588 | `c7bbbef6a549dcff8a003569b7ef4ea681af3ab222304ee93f541557d7e8685f` |
| [PACKAGE-0090-G3F-4-PLAN-REPLAY-IDEMPOTENCY-MATRIX.json](PACKAGE-0090-G3F-4-PLAN-REPLAY-IDEMPOTENCY-MATRIX.json) | 7375 | `5747dcd1b52019ec4ebc0a5e4401cb4e17d89851ba7843af13ba5d7719acd7b6` |
| [PACKAGE-0090-G3F-4-POSITIVE-READINESS.json](PACKAGE-0090-G3F-4-POSITIVE-READINESS.json) | 2559 | `7fda92880398e112f9263aead8211e24e9af68e4eae24ca1b7d127f39ff8b0f2` |
| [PACKAGE-0090-G3F-4-POST-REVOCATION-EVIDENCE-PROOF.json](PACKAGE-0090-G3F-4-POST-REVOCATION-EVIDENCE-PROOF.json) | 7829 | `0ad1308925f4f6f22f02a1ad6f6d9454639f238bfbf2cfa9aa18840c2360aa19` |
| [PACKAGE-0090-G3F-4-PREREQUISITE-NEGATIVE-MATRIX.json](PACKAGE-0090-G3F-4-PREREQUISITE-NEGATIVE-MATRIX.json) | 10093 | `81f4ac478a0907faa744a798d40eba3ab38546091702e66bf5da848de30e096a` |
| [PACKAGE-0090-G3F-4-PREREQUISITE-PROVISIONING-MATRIX.json](PACKAGE-0090-G3F-4-PREREQUISITE-PROVISIONING-MATRIX.json) | 15277 | `aa16c0678b3162692b2e81cead6d9e01f7dfa191cbd9d487b8f89384b7edbd0a` |
| [PACKAGE-0090-G3F-4-RECOVERY-2.json](PACKAGE-0090-G3F-4-RECOVERY-2.json) | 1896 | `7667c937530c1a833ac626a6b33a305a36bb08934aa5eda27cb7bb7640c6ad66` |
| [PACKAGE-0090-G3F-4-REHEARSAL-BINDING-AUTHORIZATION.json](PACKAGE-0090-G3F-4-REHEARSAL-BINDING-AUTHORIZATION.json) | 4399 | `e869dcff6562ed0ce2410efab90bdf6273821da63c37853f0bbffec4ee82e48c` |
| [PACKAGE-0090-G3F-4-REHEARSAL-BINDING-PROVISIONING.json](PACKAGE-0090-G3F-4-REHEARSAL-BINDING-PROVISIONING.json) | 17540151 | `75abf244535a33e2fd35a7ef373659f146dafc07fa7274bb2d78bc2170e1ad55` |
| [PACKAGE-0090-G3F-4-REHEARSAL-DEPLOYMENT-APPROVAL.json](PACKAGE-0090-G3F-4-REHEARSAL-DEPLOYMENT-APPROVAL.json) | 5043 | `84a0afd98f68a25c360e7b3e2056e92c9c9d945f364bf9d8931a730908d752de` |
| [PACKAGE-0090-G3F-4-REHEARSAL-DOMAIN-ALLOCATION.json](PACKAGE-0090-G3F-4-REHEARSAL-DOMAIN-ALLOCATION.json) | 5491 | `6402750ec87ba8a894d590502eebd32e19769d566614cd854c808e9b9f41a313` |
| [PACKAGE-0090-G3F-4-REHEARSAL-DOMAIN-AUTHORITY-CLOSURE.md](PACKAGE-0090-G3F-4-REHEARSAL-DOMAIN-AUTHORITY-CLOSURE.md) | 18816 | `5ed65ebbd0e84b93b82573d9465e85b3b75bb383b62ecf5e32c897a1fcb42fe2` |
| [PACKAGE-0090-G3F-4-REHEARSAL-SECRET-RESIDUE-SCAN.json](PACKAGE-0090-G3F-4-REHEARSAL-SECRET-RESIDUE-SCAN.json) | 2359 | `006d46adc2ab0e2282f04f9c33200ffc2fabe002afd6e5f09bbb5341cc2a7848` |
| [PACKAGE-0090-G3F-4-REHEARSAL-SIGNED-DOMAIN.json](PACKAGE-0090-G3F-4-REHEARSAL-SIGNED-DOMAIN.json) | 58467 | `ea0c0b15e6d371f88f807d0e2635ec8a2e337fa94f370670ee429823ca7ba4c1` |
| [PACKAGE-0090-G3F-4-REHEARSAL-SOURCE-STORAGE-AUTHORITY-CLOSURE.md](PACKAGE-0090-G3F-4-REHEARSAL-SOURCE-STORAGE-AUTHORITY-CLOSURE.md) | 9439 | `ab02a2d15915695593edddde518a0773b12edc7e77d95a88ee7f78743dd45a69` |
| [PACKAGE-0090-G3F-4-RR-SNAPSHOT-PLACEMENT.json](PACKAGE-0090-G3F-4-RR-SNAPSHOT-PLACEMENT.json) | 1230986 | `6045826ac91e866c20edc8634a5b4d126cac1adc04c03952f0c96c1e54412802` |
| [PACKAGE-0090-G3F-4-RUNTIME-TESTS.json](PACKAGE-0090-G3F-4-RUNTIME-TESTS.json) | 76873 | `1da479d9bca30260552346f20daa7a215b71423faa5ba2c86bf184e54a6372d0` |
| [PACKAGE-0090-G3F-4-SIGNED-ATTESTATION-VERIFICATION.json](PACKAGE-0090-G3F-4-SIGNED-ATTESTATION-VERIFICATION.json) | 28491 | `0cd7c0a1a8d91c64d00ededf533f9c04b79aa67dbe31fefb9aa6854aff76fce2` |
| [PACKAGE-0090-G3F-4-SIGNED-DOMAIN-MATRIX.json](PACKAGE-0090-G3F-4-SIGNED-DOMAIN-MATRIX.json) | 41164 | `f1b89f4b5a89d4c0794de5460c3aa8f4cf6be44fa3ddc201670dd54b7e7e37a1` |
| [PACKAGE-0090-G3F-4-SIGNER-AUTHORITY-REGISTRATION.json](PACKAGE-0090-G3F-4-SIGNER-AUTHORITY-REGISTRATION.json) | 1110601 | `9ceca53f1a099da6d68c0d8254e5add03674c8fe299d434819bca8ecdb8e7f19` |
| [PACKAGE-0090-G3F-4-SIGNER-KEY-AUTHORITY-MATRIX.json](PACKAGE-0090-G3F-4-SIGNER-KEY-AUTHORITY-MATRIX.json) | 1091512 | `609b6b69b8fd68c1fc7eb8ecb6fe3408adbb126c99fde68868c9db8a845f8b5b` |
| [PACKAGE-0090-G3F-4-SIGNER-KEY-REGISTRATION.json](PACKAGE-0090-G3F-4-SIGNER-KEY-REGISTRATION.json) | 28842 | `f82b3df65ffa02c121b7f4100e1e0a9bb55dbd4e759305fffd305f3ce2a515cc` |
| [PACKAGE-0090-G3F-4-SIGNING-CEREMONY-AUTHORITY-CLOSURE.md](PACKAGE-0090-G3F-4-SIGNING-CEREMONY-AUTHORITY-CLOSURE.md) | 16499 | `a13cad70eefd2c1267c53cdb7d042955ea0edd902e56872f57477e87ceb5d0bd` |
| [PACKAGE-0090-G3F-4-SIGNING-CEREMONY-CAPABILITY-MATRIX.json](PACKAGE-0090-G3F-4-SIGNING-CEREMONY-CAPABILITY-MATRIX.json) | 159332 | `ee3c7024451f0bfddbbac66221021b11ad565f27d4b8ed32f90fda7cda89177d` |
| [PACKAGE-0090-G3F-4-SIGNING-CEREMONY-RESIDUE-SCAN.json](PACKAGE-0090-G3F-4-SIGNING-CEREMONY-RESIDUE-SCAN.json) | 29473 | `fa6cc39d260037383bc207d2e980659fc0a8ed7aebe340db821b0931c0afc10e` |
| [PACKAGE-0090-G3F-4-TEMPORAL-BOUNDS-REVIEW.md](PACKAGE-0090-G3F-4-TEMPORAL-BOUNDS-REVIEW.md) | 6351 | `026aaaad878ecb8ff9ecdb46ffd73b210108300df658dc5f2eb0c9b6e80be4f6` |
| [PACKAGE-0090-G3F-4-TIMING-08006-DIAGNOSIS.md](PACKAGE-0090-G3F-4-TIMING-08006-DIAGNOSIS.md) | 9623 | `08b91488bbc8e9b8030cb3f16224bbae15e03409745249096bf45295cee14862` |
| [PACKAGE-0090-G3F-4-TIMING-PHASES.json](PACKAGE-0090-G3F-4-TIMING-PHASES.json) | 44080725 | `934a01c237140e781e98aba0bea205f8902bbda6b0bea49453dbb8ca6a1b575a` |
| [PACKAGE-0090-G3F-4-TIMING-QUALIFICATION-2.json](PACKAGE-0090-G3F-4-TIMING-QUALIFICATION-2.json) | 1090465 | `998e4b3930fbb9b44c7d07c2c1eaeb5f63e1972068469adefbe54349662a17ea` |
| [PACKAGE-0090-G3F-4-TIMING-QUALIFICATION.md](PACKAGE-0090-G3F-4-TIMING-QUALIFICATION.md) | 10695 | `c30c60f340b2c779fefe4bbc17e0294bfb42f13c77a82c0afa6b64196717d65b` |
| [PACKAGE-0090-G3F-4-TIMING-SAMPLES.json](PACKAGE-0090-G3F-4-TIMING-SAMPLES.json) | 526553 | `e6415ef00764e10a030d1d74ff667870605210a4e1f4a06463bc233707daf15e` |
| [PACKAGE-0090-G3F-4-TRANSPORT-MODEL-REVIEW.md](PACKAGE-0090-G3F-4-TRANSPORT-MODEL-REVIEW.md) | 13792 | `d8488c63390f3c29c9775c8f402e318fd6eab35416a9d0371a9d52f28275f192` |
| [PACKAGE-0090-G3F-4-WATCHDOG-AUTHORITY-REVIEW.json](PACKAGE-0090-G3F-4-WATCHDOG-AUTHORITY-REVIEW.json) | 692996 | `b5165e1199147939336654739261389a47e96a42d6385eb8598cefe5be5a2baa` |
| [PACKAGE-0090-G3F-4-WATCHDOG-DEPLOYMENT-CLOSURE.md](PACKAGE-0090-G3F-4-WATCHDOG-DEPLOYMENT-CLOSURE.md) | 16917 | `858f26755b1d81043f38e96f62c6672ed816f51287571f6c4860cd4b6eb385cb` |
| [PACKAGE-0090-G3F-4-WATCHDOG-FAILURE-MATRIX.json](PACKAGE-0090-G3F-4-WATCHDOG-FAILURE-MATRIX.json) | 11294 | `4e4b90dc0aaf552449098fdb179807dfa05550a89c11279524f96caf70ca228b` |
| [PACKAGE-0090-G3F-4-WATCHDOG-RUNTIME.json](PACKAGE-0090-G3F-4-WATCHDOG-RUNTIME.json) | 8154 | `97eb1391c509b33a6ce1c902b6b73cd67c399d6c6fc22754942ab217145930e8` |
| [PACKAGE-0090-G3F-4-WATCHDOG-VISIBILITY.json](PACKAGE-0090-G3F-4-WATCHDOG-VISIBILITY.json) | 18895509 | `397fced6ced8063d537d75429ec75cf79c4125931db5a5bf4645f0c3a14fb145` |
| [PACKAGE-0090-GOVERNED-ROLE-RECOGNITION-MATRIX.json](PACKAGE-0090-GOVERNED-ROLE-RECOGNITION-MATRIX.json) | 14236 | `f1c41a79dad696da214b97f7fb654f0a360bc5a49f2cecfb7862ba63ddaeb354` |
| [PACKAGE-0090-H02-ADAPTER-SCOPE.md](PACKAGE-0090-H02-ADAPTER-SCOPE.md) | 8863 | `efd9b654f431a4c270070837f657067f5d5f0efb74f9b393ce3474963a102a12` |
| [PACKAGE-0090-H02-ADAPTER-TEST-RESULTS.json](PACKAGE-0090-H02-ADAPTER-TEST-RESULTS.json) | 3862 | `4bb0027e8f967649264887d06f74ecadbd0874cd3dd24f8b5d2de3038f15a4da` |
| [PACKAGE-0090-H02-CLOSURE.json](PACKAGE-0090-H02-CLOSURE.json) | 1515 | `e35aaea61c683b1de65c6058b2281108fcb682b82bc6996a9027cb2779b5c41a` |
| [PACKAGE-0090-H02-FULL-OFFLINE-TESTS.txt](PACKAGE-0090-H02-FULL-OFFLINE-TESTS.txt) | 27316 | `80a16772cbd0fd245d4ed63403f08dd698e6039cb81a5374d5e75f3705750242` |
| [PACKAGE-0090-H02-G3F4-HANDOFF.md](PACKAGE-0090-H02-G3F4-HANDOFF.md) | 2307 | `3b5c386b1488db2f3f451273b10866caa80d4f11a504fa15eac7805ae31762ef` |
| [PACKAGE-0090-H02-INDEPENDENT-ADAPTER-REVIEW.json](PACKAGE-0090-H02-INDEPENDENT-ADAPTER-REVIEW.json) | 1426 | `60bfbec29558c8fc7e7258cb6e0efba1045b42f054d9afee678d4a7f20bdc7ea` |
| [PACKAGE-0090-H02-INDEPENDENT-SQL-REVIEW.json](PACKAGE-0090-H02-INDEPENDENT-SQL-REVIEW.json) | 505867 | `39a891e38abe205f46c8fa7418277d1e1042c87de27d2cc2d11f7bca0479f981` |
| [PACKAGE-0090-INDEPENDENT-G3F-3B-SECURITY-REVIEW.json](PACKAGE-0090-INDEPENDENT-G3F-3B-SECURITY-REVIEW.json) | 9378 | `d15fe89cf666d64edd62f712d4981eb6388a97e0b54da085fd04612ec6f93c71` |
| [PACKAGE-0090-INDEPENDENT-G3F-3B-SECURITY-REVIEW.md](PACKAGE-0090-INDEPENDENT-G3F-3B-SECURITY-REVIEW.md) | 25654 | `f8d16c117da7e217c8bbf6f7a9e73ad585f55535a2ddecbe93df26c78a9a7429` |
| [PACKAGE-0090-INDEPENDENT-MUTATION-REVIEW.json](PACKAGE-0090-INDEPENDENT-MUTATION-REVIEW.json) | 2958 | `516a820d7dc0ba1f7b4e1303beddbeac6fa80ea58b74f2f9cfb29bc3cd38b80d` |
| [PACKAGE-0090-INDEPENDENT-NATIVE-REVIEW.json](PACKAGE-0090-INDEPENDENT-NATIVE-REVIEW.json) | 31171 | `95572ab1715a8c9dbea4cc98b61c1e158cc829ec8faff410dfbc75c4c4e7a439` |
| [PACKAGE-0090-INDEPENDENT-ORIGINAL-INPUT-REVIEW.json](PACKAGE-0090-INDEPENDENT-ORIGINAL-INPUT-REVIEW.json) | 3675 | `7acd0fe26b853a086f03faa4c665508edcc92cd69bf2640e560460aeb57700e6` |
| [PACKAGE-0090-INDEPENDENT-SOURCE-REVIEW.json](PACKAGE-0090-INDEPENDENT-SOURCE-REVIEW.json) | 470357 | `29ae7bd4a7590e83b332829135f910fccda52e8990c23eca2cc17e2ed7f9dd52` |
| [PACKAGE-0090-INDEPENDENT-TEST-INVENTORY.json](PACKAGE-0090-INDEPENDENT-TEST-INVENTORY.json) | 2740 | `21ff81a9ed01491fee3c765dd0eee2300688c911bdb84ac6c5c069622b49e88d` |
| [PACKAGE-0090-ISSUER-DELIVERY-ACK-AUTHORITY.json](PACKAGE-0090-ISSUER-DELIVERY-ACK-AUTHORITY.json) | 4206 | `e7c6ddaff433cd49a485ba1f6672f3e1acc069745c6d6071718970e71613604e` |
| [PACKAGE-0090-LOGIN-EVENT-BINDING-RUNTIME.json](PACKAGE-0090-LOGIN-EVENT-BINDING-RUNTIME.json) | 12874 | `b7767cc2139c4b6b2cdb87252a3ae61ff21bbbfbec416d7c124fa62daa569c1f` |
| [PACKAGE-0090-MUTATION-ORIGINAL-INPUT-AUTHORITY.json](PACKAGE-0090-MUTATION-ORIGINAL-INPUT-AUTHORITY.json) | 2013 | `bbc19ac21dabbb7fe01f8b4b5a36d0c2d9eecc1624c2ad07c6ac8e309592e0bd` |
| [PACKAGE-0090-MUTATION-ORIGINAL-INPUT-AUTHORITY.md](PACKAGE-0090-MUTATION-ORIGINAL-INPUT-AUTHORITY.md) | 1681 | `9c37ee42cf8a8660184a6ca77b28875dba059b666550d19a8c6af89a4b8dd64c` |
| [PACKAGE-0090-MUTATION-ORIGINAL-MATCH-REVIEW.json](PACKAGE-0090-MUTATION-ORIGINAL-MATCH-REVIEW.json) | 1347 | `5e1e9c662efcf1704d5556be8a81e47ed06bae41e8b88be3ede7a15478ad8586` |
| [PACKAGE-0090-PHASE-A-CLOSURE.json](PACKAGE-0090-PHASE-A-CLOSURE.json) | 939 | `36983e944e2f7bc56dc51c7f7b4b6ca6d9a77a4886d2eb25b5bbb28e36e2871e` |
| [PACKAGE-0090-PHASE-A-FULL-TESTS.txt](PACKAGE-0090-PHASE-A-FULL-TESTS.txt) | 26339 | `88ec2118db9feea0ff9163a9448e897271a343b0ac451a3dc6ee99881132875c` |
| [PACKAGE-0090-S02-EXPECTED-ATTESTATION-AUTHORITY.json](PACKAGE-0090-S02-EXPECTED-ATTESTATION-AUTHORITY.json) | 3740 | `67c63d386aff18660289c340351857f6bdf1e598f7592df0e16e8b5d3e054851` |
| [PACKAGE-0090-S02-EXPECTED-ATTESTATION-AUTHORITY.md](PACKAGE-0090-S02-EXPECTED-ATTESTATION-AUTHORITY.md) | 7466 | `0008fd06ced70d6c2b485da308a32eba1fb1cc745d0171d7cbe58f6a40917f10` |
| [PACKAGE-0090-S02-ISOLATED-PREDICATE-REVIEW.json](PACKAGE-0090-S02-ISOLATED-PREDICATE-REVIEW.json) | 2014 | `90cf5c3bd99ebad7ed51890c6fe3db4863e59fc386df938017abb6b624720855` |
| [PACKAGE-0090-S02-ORIGINAL-INPUT-CLOSURE.md](PACKAGE-0090-S02-ORIGINAL-INPUT-CLOSURE.md) | 3401 | `f2cea24b34c3d1db628fc662cf13aaf54ac0f1279ff600972edc91bf01ad88ed` |
| [PACKAGE-0090-S02-ORIGINAL-INPUT-GOLDENS.json](PACKAGE-0090-S02-ORIGINAL-INPUT-GOLDENS.json) | 11726 | `56c71b6a2834158718bea4cc8652ee6971087a37dc8501d8a7aac9ce35e22d22` |
| [PACKAGE-0090-S03-SOURCE-REVIEW.md](PACKAGE-0090-S03-SOURCE-REVIEW.md) | 2166 | `605b2af3f44aa6d2fbd6ee2cdf2c8c7e1042d278a55816a18ec686b3b72d5a9d` |
| [PACKAGE-0090-S05-S06-ISOLATED-REVIEW.json](PACKAGE-0090-S05-S06-ISOLATED-REVIEW.json) | 859 | `11dad47242f12a6074167da45b8127e69815f8c1f9482f1dc9e151998e709ef2` |
| [PACKAGE-0090-S05-S06-TRANSPORT-GOLDENS.json](PACKAGE-0090-S05-S06-TRANSPORT-GOLDENS.json) | 11902 | `3a8b2cda92514064f712c4e4f71bcb1773c519eaca8b30740547a827174afb50` |
| [PACKAGE-0090-S05-S12-SOURCE-REVIEW.md](PACKAGE-0090-S05-S12-SOURCE-REVIEW.md) | 2226 | `d11abb145d1082c6f973c0cb6fa3e5b6c73375055a0b39fa5c3353643be00785` |
| [PACKAGE-0090-S07-S18-ISOLATED-REVIEW.json](PACKAGE-0090-S07-S18-ISOLATED-REVIEW.json) | 2180 | `9800d386c58099026f48cd15cdec4dd148b43be5ff6dfe27eba7ebffeff183c4` |
| [PACKAGE-0090-S07-S18-TRANSPORT-GOLDENS.json](PACKAGE-0090-S07-S18-TRANSPORT-GOLDENS.json) | 52734 | `eb8eba300cc73a41d1e17f9093a5f264ba886813a4013e792d4d80116c55f754` |
| [PACKAGE-0090-S13-S18-SOURCE-REVIEW.md](PACKAGE-0090-S13-S18-SOURCE-REVIEW.md) | 3676 | `83673b94b7e8900d5a8b1ff069b342341136dfe2af2b9af7c1886675367533b0` |
| [PACKAGE-0090-SELF-ENROLLED-ANCHOR-PROOF.md](PACKAGE-0090-SELF-ENROLLED-ANCHOR-PROOF.md) | 16705 | `e45122541346e7ab1a872a54f6e5290af0823b38a7b11bbdbe8e6b47b4891431` |
| [PACKAGE-0090-SELF-ENROLLED-ANCHOR-REVIEW.json](PACKAGE-0090-SELF-ENROLLED-ANCHOR-REVIEW.json) | 25565 | `9bff9f1f1f0ee845652aac1d02261511b1956d354b29095c2055aadb27cdde63` |
| [PACKAGE-0090-SELF-ENROLLED-ANCHOR-RUNTIME.json](PACKAGE-0090-SELF-ENROLLED-ANCHOR-RUNTIME.json) | 578932 | `d7cd3aa05e5bb0ea184596c4d2236e817048b413bd6ece554b02c7477944462b` |
| [PACKAGE-0090-SOURCE-COMPOSITION-CLOSURE.json](PACKAGE-0090-SOURCE-COMPOSITION-CLOSURE.json) | 1663 | `01291f864f1e4dfd3a2852b647aec018d6ed5fd986af5966474d101bc1615388` |
| [PACKAGE-0090-V-BRIDGE-CAPABILITY-INVENTORY.json](PACKAGE-0090-V-BRIDGE-CAPABILITY-INVENTORY.json) | 34264 | `b010edcaf2d98cfae596176619355dce7344be9aa7b2bda39927edaf257265c8` |
