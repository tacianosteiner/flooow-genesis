# Package 0090 G3F.4 — final ceremony signing window contract review

G3F_4_FINAL_CEREMONY_SIGNING_WINDOW_CONTRACT_REVIEW=PASS (contract/design only). Current gate B0/H0/M0/L0; aggregate G3F.4 B0/H2/M0/L0, watchdog and H01 HIGH/OPEN, G3F.4 HOLD. No implementation, DB connection/mutation, key, signature, private material or identifier generation, production/schema/migration change, runtime experiment or next-gate execution.

## Baseline, authority and evidence precedence

Branch `checkpoint/package-0090-cloud-handoff`; clean local and live remote baseline `08d6025f3c30e70e32714aeaf49199b8d411d13e` independently verified equal before writing. Staged/tracked/untracked inventories empty; 1257 tracked file byte hashes captured. Read/parsed all166 prior PACKAGE0090 evidence files and relevant SPEC/ADR, approval/codec/verifier and V040-V043 sources before conclusions. The initial temporal report remains historical HOLD discovery evidence; TC-R01 remediation explicitly supersedes that status and preserves the approved temporal rules, as the user baseline confirms. No old file is rewritten. SPEC/ADR overrides historical prose; frozen local rehearsal profile supplies the already approved60s ADMIN signing/registration restriction, not a universal base-schema default.

This review defines legal admission of a signature and original registration, not physical prevention of every late cryptographic computation. A cryptographic operation already in progress can produce bytes after expiry; those bytes are an inadmissible candidate and must be discarded, never accepted/bound. Successful primitive return/byte availability is the deterministic logical creation event, distinct from entry, delayed state-copy/serialization and durable commit. There is no source-backed exact DB-clock timestamp at that CPU event, and this review creates none.

The legal-event test is conservative: fresh approved DB samples bracket SIGN and separately bracket local verification; both endpoints satisfy start<=N<end and qualified clock continuity/no regression, unchanged original context and approved authority. A delayed, expired, malformed or unavailable postguard denies admission even if the CPU operation may have finished earlier. No client/JVM clock certifies creation and no sampled DB value is called an exact crypto birth timestamp. Unobserved wall-clock changes cannot be proved absent by samples: qualified continuity is a mandatory future operational precondition; without it signing stays blocked. The successful-return event refines existing phaseE single SIGN, not a new production state/table/API/receipt. The final composer and guard instrumentation remain unimplemented/unqualified; those are separately gated proof obligations, not claimed runtime results.

## Evidence ledger

| CLAIM | SOURCE / SHA256 | SOURCE_TYPE | CURRENT_RULE | CONFLICT | RESOLUTION |
| --- | --- | --- | --- | --- | --- |
| DB clock sole authority | docs/specifications/SPEC-0090-governed-offline-field-proof-exclusive-capability-composition.md:239<br>`d12acc86cbed8d56cd774f427b79dce26258a36ac65a7d78bf2cb1fb37fd9a92` | NORMATIVE | Approved DB time; exact immutable policy finite actual/max | Application/transaction-start time mistaken for fresh eligibility | T0 identity retained; fresh same-cluster clock_timestamp for guards |
| Half-open lower/upper endpoint | docs/specifications/SPEC-0090-governed-offline-field-proof-exclusive-capability-composition.md:60<br>`d12acc86cbed8d56cd774f427b79dce26258a36ac65a7d78bf2cb1fb37fd9a92` | NORMATIVE | start<=DB now<end for effect eligibility | SPEC M governs operational effects, not direct trusted-ADMIN registration API | Retain already approved local rehearsal profile for ADMIN SIGN/JCA/T_REG; do not require M/READY to register or confer service privileges |
| Visibility after expiry | docs/adr/ADR-0090-governed-offline-field-proof-exclusive-capability-composition.md:81<br>`e1c26d2f202684d5ace54408c83a0fcf100085864270f0c32cb077b9398566a9` | NORMATIVE | Valid admitted effects may commit/become visible after expiry | Calling SQL write success durable or imposing new COMMIT-time deadline | Exact T_REG COMMIT is durability; admission guards remain in-window; unknown outcome query-first |
| Registration transaction composition | docs/evidence/PACKAGE-0090-G3F-4-FINAL-CEREMONY-RECOVERY-CLOSURE.md:7<br>`281fc2d1cb0f4c929d6b421bae9a4a408f9441aa5b48d6aa21b1d2cc1af74518` | ACCEPTED_DESIGN_EVIDENCE | One ADMIN T_REG: 2V040+9V043; no V041 accepted proof | Separate adapter commits or local JCA miscalled acceptance | Retain selected caller transaction and public-only local verification |
| Temporal basis/lifetime | docs/evidence/PACKAGE-0090-G3F-4-FINAL-CEREMONY-TIME-CONTRACT-CLOSURE.md:35<br>`4bafa0b9575ce6342b909c719acaa50a06df92cd916a8fa4059166145f70085f` | ACCEPTED_TEMPORAL_PROFILE_WITH_TC_R01_SUPERSESSION | Original T0 transaction opening; +60000000us; exact equality to signed endpoints | Initial report retains historical HOLD | Current TC-R01 adjudication and user baseline promote unchanged rules; no reopen/drift |
| Corrected recovery privacy | docs/evidence/PACKAGE-0090-G3F-4-TC-R01-PROTECTED-MATERIAL-PROJECTION-REMEDIATION.md:9<br>`ebe3b97de6a40b48437ebbe3badd41a43a9f8ec4bf36de9fdf865da8f3b9060f` | CURRENT_REMEDIATION_EVIDENCE | Old Q12/snapshot declarations superseded; only explicit public projection | Historical raw Q12 contains private digest | Use replacement Q1-Q26 only; no protected/opaque/shadow comparison oracle |
| Signing event | docs/evidence/PACKAGE-0090-G3F-4-FINAL-CEREMONY-RECOVERY-CLOSURE.md:19<br>`281fc2d1cb0f4c929d6b421bae9a4a408f9441aa5b48d6aa21b1d2cc1af74518` | ACCEPTED_DESIGN_EVIDENCE | Phase E single SIGN then independent local public verification/destruction | No physical-created-at DB timestamp or fully implemented composer exists | Choose successful primitive-return/byte-availability logical event; conservative pre/post fresh guards, no new timestamp claim |
| Manifest temporal commitment | applications/marketplace-operations/src/main/kotlin/io/flooow/marketplace/operations/authorization/ApprovalAttestationCanonicalCodec.kt:31<br>`74763cd4b0c3ab49b3f2c882f724df3ec10561f9aaa452c7b29fd1d6a943b26d` | PRODUCTION_SOURCE | Positions12/13 sign start/end through canonical manifest digest | issued_at is not separately/directly signed | Frozen equality derives all3 instants; future validator checks exact relation |
| Signature preimage | applications/marketplace-operations/src/main/kotlin/io/flooow/marketplace/operations/authorization/ApprovalAttestationCanonicalCodec.kt:72<br>`74763cd4b0c3ab49b3f2c882f724df3ec10561f9aaa452c7b29fd1d6a943b26d` | PRODUCTION_SOURCE | Ed25519/keyID/keyfingerprint/manifestDigest | Header fingerprint mistaken for Ed25519 signature over entire header | Retain existing preimage; no new field/algorithm or creation-time payload |
| Precision/UTC roundtrip | applications/marketplace-operations/src/main/kotlin/io/flooow/marketplace/operations/authorization/ApprovalAttestationCanonicalCodec.kt:189<br>`74763cd4b0c3ab49b3f2c882f724df3ec10561f9aaa452c7b29fd1d6a943b26d` | PRODUCTION_SOURCE | UTC appendInstant(6), strict decode/encode | Timezone/precision conversion changes bytes | Typed exact microseconds; display offset only; reject coercion |
| New vs replay V041 | applications/marketplace-operations-persistence-postgres/src/main/resources/db/migration/V041__create_s2a_accepted_attestation.sql:135<br>`3ff1421dd56de17270a9c44054055c0c1afc91f855d903697268088a53f1182d` | PRODUCTION_SOURCE | Replay original verified_at; new result uses transaction_timestamp; half-open check197 | verified_at mistaken for actual signature birth or fresh wall time | V041 accepted-attestation stage remains distinct; later V043 mutable wrappers retain wall-clock pre/post guards; no reinterpretation or standalone V041 rewrite |
| Frozen admission vs later current effects | applications/marketplace-operations-persistence-postgres/src/main/resources/db/migration/V042__create_s2a_attestation_consumption_and_attested_command_authority.sql:1937<br>`3bfc5f7c95d235235ff8444453523a6a757980b464bff60ad5150e622d2f1ae1` | PRODUCTION_SOURCE | Later final effect resolves current key/authority | Historical registration treated as ongoing live permission | Read-only historical outcome, then independent current eligibility on later effects |
| Header DDL weaker than profile | applications/marketplace-operations-persistence-postgres/src/main/resources/db/migration/V043__create_governed_offline_field_proof_capability_composition.sql:576<br>`3301b254e883ae2ebf9e1d41036f15bc7839c1ae9e2404e692bc2ec864204109` | FENCED_PRODUCTION_SOURCE | Finite valid intervals, no exact60s/equality check | DDL mistaken for current implementation of local signer policy | Future trusted ADMIN checks exact stronger profile; fence stays; no source edit |
| Locks and append authority | applications/marketplace-operations-persistence-postgres/src/main/resources/db/migration/V040__create_s2a_approval_governance.sql:217<br>`58753e9d702169311f5ea74099f89e5068d982ef9c30d0e1da275b4e40b6bedd` | PRODUCTION_SOURCE | Existing key/authority advisory locks and append-only lineage | Two runtimes create signatures before canonical serialization/custody proof | Freeze custody and hold selected canonical transaction locks before capture/key/sign; loser query-first, no extra coordinator |
| Restart/unknown custody | docs/specifications/SPEC-0090-governed-offline-field-proof-exclusive-capability-composition.md:235<br>`d12acc86cbed8d56cd774f427b79dce26258a36ac65a7d78bf2cb1fb37fd9a92` | NORMATIVE | No deadline/ownership refresh, secret not reconstructed | Another runtime/restart silently resumes failed preparation | No automatic mutable resume; existing original query-first/disposition |
| Read replay after expiry | docs/specifications/SPEC-0090-governed-offline-field-proof-exclusive-capability-composition.md:58<br>`d12acc86cbed8d56cd774f427b79dce26258a36ac65a7d78bf2cb1fb37fd9a92` | NORMATIVE | Authenticated R ignores mutation expiry, subject to read policy/identity/READY | ADMIN raw inspection confused with service R/anonymous API | ADMIN safe recovery is separate; service replay obeys its original R guard; no widened access |
| Policy drift | docs/specifications/SPEC-0090-governed-offline-field-proof-exclusive-capability-composition.md:241<br>`d12acc86cbed8d56cd774f427b79dce26258a36ac65a7d78bf2cb1fb37fd9a92` | NORMATIVE | Immutable version/digest, new approval for changes, no in-place renewal | Reload changes signed window or adopts a shorter/longer default | Unfinished root blocks on relevant drift; original history remains fixed; any fresh root separately governed |
| Watchdog authority boundary | docs/specifications/SPEC-0090-governed-offline-field-proof-exclusive-capability-composition.md:245<br>`d12acc86cbed8d56cd774f427b79dce26258a36ac65a7d78bf2cb1fb37fd9a92` | NORMATIVE | Existing identity-whitelisted finite enforcement; no readiness without proof | Service watchdog assumed to supervise trusted ADMIN postgres or signer process without authority | Do not widen whitelist; ADMIN guarding/clock continuity must be separately qualified; watchdog remains OPEN |
| H01 and feasibility | docs/evidence/PACKAGE-0090-G3F-4-TRANSPORT-MODEL-REVIEW.md:1<br>`d8488c63390f3c29c9775c8f402e318fd6eab35416a9d0371a9d52f28275f192` | PRIOR_OPEN_FINDING_EVIDENCE | Transport/RR/jitter envelope unqualified, HIGH OPEN | Contract definition promoted into measured headroom/runtime result | This review freezes checkpoints only; next existing operational review proves policy fit/latency/continuity prerequisites |
| Next gate already named in sequence | docs/evidence/PACKAGE-0090-G3F-4-FINAL-CEREMONY-RECOVERY-CLOSURE.md:45<br>`281fc2d1cb0f4c929d6b421bae9a4a408f9441aa5b48d6aa21b1d2cc1af74518` | ACCEPTED_SEQUENCE_EVIDENCE | G3F_4_SIGNING_WINDOW_OPERATIONAL_REVIEW before any execution | Pre-assuming implementation after legal-contract review | Recommend operational feasibility/policy/authority qualification review only; do not start it |

## Frozen legal contract

```json
{
  "SIGNING_WINDOW_START": "valid_from=issued_at=signed_start=T0 (same T_REG transaction opening)",
  "SIGNING_WINDOW_END": "expires_at=signed_end=T0+60000000us",
  "SIGNING_WINDOW_INTERVAL": "[T0,T0+60000000us), immutable and nonrenewable",
  "SIGNATURE_CREATION_ELIGIBILITY": "Existing authorized originating live preparation only; fresh same-cluster DB wall-clock guards before SIGN and after successful byte return must satisfy start<=N<end, qualified continuity/no regression and unchanged root/policy/authority/payload; at most one SIGN invocation.",
  "SIGNATURE_CREATED_AT_EVENT": "Successful return of the single cryptographic SIGN operation, when complete final signature bytes first become available to the originating transient preparation. Logical event only: no new SQL field, timestamp receipt or client-clock authority.",
  "SIGNATURE_VERIFICATION_RULE": "Separate local public JCA verification of exact original preimage/SPKI/signature plus header-to-signed-endpoint equality; fresh DB eligibility immediately before and after verification, within same immutable window. No fresh acceptance after expiry; historical cryptographic read verification remains allowed with original evidence and no new effect.",
  "DURABLE_BINDING_ELIGIBILITY": "Complete original eleven-row T_REG only after eligible single signature/local verification and private-key destruction; fresh DB guards before/after write batches and after exact write-set/constraints immediately before COMMIT. Every guard inside [start,end); no new write at/after expiry.",
  "DURABLE_BINDING_COMMIT_POINT": "Successful database COMMIT of the exact complete T_REG; staged SQL writes and an in-memory signature are not durable. Unknown ACK requires TC-R01-safe query-first proof of exact complete committed root before declaring success.",
  "EXPIRY_DURING_SIGNING_RULE": "BLOCK candidate at completion>=end or failed/unavailable postguard; discard ephemeral candidate/private material and abort controlled open T_REG. An already invoked SIGN is never retried on the old root.",
  "EXPIRY_AFTER_SIGNATURE_BEFORE_BINDING_RULE": "BLOCK any new binding write at/after end even with a mathematically valid pre-expiry signature. Existing complete committed root may be read; no window/signature renewal.",
  "EXPIRY_DURING_COMMIT_RULE": "Before final eligible guard/dispatch: BLOCK and rollback only if transaction is known controlled/open. After valid final guard and COMMIT dispatch: visibility may occur after end; confirmed complete -> historical success, unknown -> RECOVER/query-first. No retroactive rollback or new mutation.",
  "AMBIGUOUS_COMMIT_AFTER_EXPIRY_RULE": "Q1 exact complete committed root -> REPLAY_EXISTING; Q2 authoritative full absence after writer quiescence/locks/fresh snapshot -> BLOCK old root and govern abandonment; Q3 unprovable/partial/conflicting -> ESCALATE existing ADMIN and HOLD with no mutation. No replacement IDs/key/signature/tuple.",
  "RETRY_RULE": "Fresh eligibility samples may change N only; never T0/expiry/identity/payload. Only original uninterrupted already-live preparation may continue an unexecuted next step once. Duplicate mutable calls, unknown SIGN completion, process loss or another-runtime takeover deny resume and require existing query-first disposition.",
  "REPLAY_RULE": "Exact original committed tuple and public evidence may be observed/verified after expiry; no new authority effect, signer creation, capture, signing, INSERT or reactivation.",
  "RECOVERY_RULE": "Existing ADMIN, original immutable root, original-writer quiescence, canonical existing locks and one fresh corrected nonsecret Q1-Q26 snapshot; full root plus independently verified public original -> historical replay; full absence -> block/dispose old root; partial/unknown/conflict -> hold/escalate. Later domain effects require existing domain reconciliation.",
  "POLICY_CHANGE_DURING_CEREMONY_RULE": "Freeze exact approved policy version/digest and authority with original root. Relevant live eligibility/governance drift blocks unfinished work; never reload lifetime/payload/T0 or repair the old root. Committed original remains historical; future effects recheck their own current authority. Unrelated config reload has no authority to alter approved data.",
  "WATCHDOG_BOUNDARY": "Existing identity-bound observe/detect/report/cancel-drain duties only within approved whitelist. Stale/expiry observations are not signer authority or new durable states; existing ADMIN owns lifecycle disposition. No signing, renewal, tuple changes, blind retry, outcome inference or scope expansion; OPEN/HIGH.",
  "H01_EFFECT": "Narrows semantic checkpoints for future latency/transport qualification; no numeric envelope, runtime transport, execution proof or HIGH closure. H01 OPEN/HIGH.",
  "SIGNING_AT_VALID_FROM": "ALLOW_TEMPORAL_PREDICATE_ONLY_ALL_PREREQUISITES_REQUIRED",
  "SIGNING_BEFORE_VALID_FROM": "BLOCK",
  "SIGNING_AT_EXPIRES_AT": "BLOCK",
  "SIGNING_AFTER_EXPIRES_AT": "BLOCK",
  "BIND_BEFORE_EXPIRY": "ALLOW_ADMITTED_WRITE_ONLY_ALL_PREREQUISITES_REQUIRED",
  "BIND_AT_EXPIRY": "BLOCK_NEW_WRITE",
  "BIND_AFTER_EXPIRY_WITH_PREEXPIRY_SIGNATURE": "BLOCK_NEW_WRITE; existing validly admitted COMMIT visibility is historical",
  "TEMPORAL_CONTRACT_CHANGED": "NO",
  "CRYPTOGRAPHIC_PAYLOAD_STABLE": "YES",
  "WINDOW_RENEWAL_ALLOWED": "NO"
}
```

The temporal predicate permits equality at valid_from and rejects equality at expires_at. This is temporal permission only: approved actor/root/custody, current unchanged binding/policy/governance context, actual canonical payload, qualified same-cluster clock and all separate A prerequisites must also pass. Current OPEN watchdog/H01 and unqualified operational feasibility do not acquire execution authority from this contract PASS. Registration is trusted ADMIN provisioning of REGISTERED/NOT_READY, not a service effect under guardM, READY activation, V041 acceptance or command/admission authority.

Creation eligibility, verification eligibility and write admission each use fresh pg_catalog.clock_timestamp() from the same approved T_REG/cluster solely for current eligibility. The immutable basis remains the one pg_catalog.transaction_timestamp() transaction opening T0. Fresh observations never change T0, issued_at, valid_from, expires_at, root or signed bytes. Same uninterrupted original preparation may read fresh eligibility before its next unexecuted step; failed/unknown/in-flight crypto invocation is not retryable as a second SIGN.

Local JCA verification here proves mathematical validity and original approved byte identity only. Later V041 accepted-attestation persistence is a separate governed stage, with its existing transaction_timestamp-based verified_at/current governance and exact historical replay rules; V043 operational wrappers perform their own fresh wall-clock pre/post effect checks. No accepted proof is inserted during T_REG, and no verified_at is repurposed as signature creation time. A historical public signature can be checked after expiry without creating a new acceptance, authority or binding.

A successful signature in memory is cryptographic commitment, not durable authority binding. All eleven original rows are tentative until the one actual T_REG COMMIT. Only exact successful COMMIT makes the registration durable; when ACK is unknown the agent cannot declare that fact until independently proving the complete mutually bound original root through corrected query-first recovery. Historical registration does not prove runtime readiness, elapsed latency/commit-before-expiry, possession, accepted command truth or human receipt.

## Conceptual C0-C16 mapping

These user labels are explanatory checkpoints, not the previous crash-point namespace (whose C labels have different meanings) or new persisted production states. Existing A-G phases and single T_REG remain authoritative.

| Label | Existing concept | Exact rule / durability meaning |
| --- | --- | --- |
| C0 | A existing authority confirmed | Validate approval, exact target/root/actor, policy/clock qualification prerequisites; no signing authority inferred from model PASS |
| C1 | B complete immutable identity allocation | Existing whole-root selected before T_REG; no new allocation here; original preparation custody unique |
| C2 | C T_REG BEGIN + canonical locks | One actual future ADMIN connection; verify previous same-root outcome after locks; no second writer/key |
| C3 | C one authoritative T0 capture | Read transaction_timestamp from exact T_REG after locks; value is transaction opening, waits consumed |
| C4 | C/D issued_at frozen | issued_at=T0; no write/clock/receipt substitution |
| C5 | C/D valid_from frozen | valid_from=issued_at=signed_start=T0 |
| C6 | C/D expires_at frozen | expires_at=signed_end=T0+60000000us exact checked addition |
| C7 | Existing transient immutable ceremony-input custody | Freeze public tuple/policy/canonical input; committed to preparation state means immutable in memory/public custody, NOT DB COMMIT/new journal |
| C8 | C ephemeral key birth eligibility | Fresh DB guard, approval/qualified continuity/policy/custody; one key only; no durable secret |
| C9 | E single SIGN entry eligibility | Fresh pre-SIGN DB guard; exact canonical preimage/approved root; no duplicate invocation |
| C10 | E successful SIGN byte return | Chosen logical creation event; fresh immediate post-SIGN guard; candidate outside/unknown window discarded; no created_at payload field |
| C11 | E local public verification and private-key destruction | Fresh before/after JCA guards; actual original preimage/SPKI/signature and exact endpoint relations; finally destroys key before F; not V041 acceptance |
| C12 | F registration-write eligibility | Same original T_REG; fresh DB guard, complete approved eleven-row set; no READY/command/admission transition |
| C13 | F complete tentative SQL row write | User label durable binding write maps to staged uncommitted rows; postcheck/write-set/constraints required; not yet durable |
| C14 | F T_REG COMMIT | Fresh eligible final guard immediately before dispatch, no external work gap; exact successful database COMMIT makes root durable, even with permitted later visibility |
| C15 | G query-first outcome verification | On uncertain ACK or restart, quiescent writer/canonical locks/fresh TC-R01-safe snapshot; full public proof, no protected data |
| C16 | G registration completion/terminal disposition | Historical registration completion only; no READY/operational proof. Conditional/later existing T_CLOSE at proven terminal event, never premature governance retirement |

## Expiry cases A-G

| Case | Exact precondition | Decision | Reason / preserved boundary |
| --- | --- | --- | --- |
| A | SIGN start/end before expiry | ALLOW | Creation only when all fresh guards/context pass; no promise remaining stages fit |
| B | SIGN finishes exactly at expiry | BLOCK | Exclusive end; no admitted candidate, destroy/discard/controlled abort |
| C | SIGN finishes after expiry | BLOCK | Same as B; starting early is insufficient |
| D | Pre-expiry candidate verified after expiry | BLOCK | No new local acceptance/binding. Exact already committed original can instead be cryptographically read-verified as REPLAY_EXISTING; that is a different historical-read precondition |
| E | Pre-expiry signature, new binding write at/after expiry | BLOCK | Signature does not reserve later write permission. If durable binding means visibility of an already validly admitted COMMIT, use caseF, not this new-write case |
| F | Complete writes/postchecks/final guard before end, COMMIT dispatched and finishes after end | ALLOW | Only completion of previously admitted T_REG. Known expired before final guard -> BLOCK; unknown ACK after dispatch -> RECOVER |
| G | Exact COMMIT succeeds before expiry; response/query arrives after expiry | REPLAY_EXISTING | Return original historical root; no second capture/sign/write or renewed authority |

COMMIT race resolution is deterministic on the known point reached: an expired guard in a controlled open transaction means BLOCK/rollback; valid final guard then COMMIT dispatch moves the case to outcome recovery, never assumed rollback. Source permits later visibility. A successful original COMMIT is historical success; unknown result RECOVER. This adds no commit-time oracle, new persisted admission receipt or backdated eligibility. The final guard-to-dispatch critical section must have no intervening signing, output, user interaction or external work; actual scheduling/network delay and enforcement feasibility remain operational qualification, not an invented zero-latency guarantee.

## Query-first after expiry

| Outcome | One action | Required evidence / prohibited work |
| --- | --- | --- |
| Q1 full durable binding found | REPLAY_EXISTING | Exact complete11-row original root, public original signature/SPKI/manifest/equalities, all lineage/controls, exact target and immutable context. TC-R01-safe projection; later effects require domain reconciliation. No new writes/signatures/activation. |
| Q2 full durable root absent | BLOCK | Original writer quiescent, locks acquired, fresh complete snapshot, no attributable registration/effects; a missing header alone is not proof. Block old root and govern whole-root abandonment; separately authorized future root only after disposition/legacy public cleanup if needed. No fresh allocation here. |
| Q3 outcome unprovable/partial/conflicting | ESCALATE | Existing trusted ADMIN incident/recovery HOLD; no inference of zero/completeness, no repair or blind retry. In the four-action scenario/model vocabulary this is RECOVER, never mutable continuation. |

Recovery reuses exact public approved original bytes/window and the TC-R01 replacement26 queries. No private digest or equivalent, opaque frozen receipt or unproved administrative hash is exported. Existing internal/ADMIN guard and tombstone checks retain their private boundary; no presence/equality oracle, shadow digest or reconstruction is added. Current expiry does not erase historical rows, reopen permissions or allow old candidate resubmission.

## Retry R1-R10

| Case | Trigger | Deterministic contract |
| --- | --- | --- |
| R1 | Before SIGN | ALLOW next unexecuted step only original uninterrupted live custody with all fresh guards; process loss instead RECOVER |
| R2 | During signing eligibility | Fresh eligibility read allowed; duplicate/in-flight SIGN invocation BLOCK, no second primitive call |
| R3 | After signature creation | Original live candidate may enter verification once while eligible; no second signature. Interrupted/failed preparation -> RECOVER, no resubmission |
| R4 | After local verification | Original live verified candidate may start complete write once while eligible; no re-sign/refresh; private key already destroyed |
| R5 | After tentative binding write | Only same known-open T_REG may complete validated sequence; unknown write/COMMIT outcome -> query-first; no second INSERT/UPSERT |
| R6 | After ambiguous COMMIT | RECOVER exact durable original first; full root REPLAY_EXISTING, proven absent BLOCK old root, unknown ESCALATE/HOLD |
| R7 | After expiry | BLOCK new creation/acceptance/write; RECOVER possibly durable outcome; exact original read replay permitted |
| R8 | After successful completion | REPLAY_EXISTING only; no new authority effect |
| R9 | Another runtime | No mutable takeover or signature/key regeneration; existing authorized inspection/query-first only after original writer disposition |
| R10 | After process restart | Same as R9; continuity/private custody lost, no automatically resumed unfinished signing/registration |

## Signed payload and drift prevention

Canonical ApprovalManifest has22 ordered fields. Only temporal positions12/13 are approvalWindowStart/approvalWindowEnd, UTC six fractional digits with Z, strict microsecond precision and decode/encode round-trip. Existing SHA256 manifest digest enters the Ed25519 signature preimage alongside algorithm/key identity/key fingerprint. issued_at is not independently/directly signed. Its derivation is normative for the accepted local rehearsal profile: issued_at=valid_from=signed_start=T0 and expires_at=signed_end=T0+60000000us; this equality must be validated against the actual original. It is not a universal DDL equality invariant. Header tags29/30/31 use existing signed-i64 network-order epoch microseconds; the38-field header fingerprint is not a signature over the entire40-field storage row. No new creation-time field is added to either codec.

After original public temporal inputs are frozen, every retry/recovery/restart/node/DB reread must preserve exact original tuple/manifest/preimage/bytes and approved policy. Display timezone conversion may preserve an instant, but alternate signed text, local civil-time reinterpretation, sub-us truncation/rounding, changed epoch, drifted expires_at, substituted source fingerprint, configuration reload or reuse with another payload BLOCK. Existing common year0001..9999 range and checked+60000000us remain unchanged; overflow/null/nonfinite/missing context fail closed. No payload is materialized or cryptographically signed in this review.

## Policy cases P1-P6

| Case | Timing | Result |
| --- | --- | --- |
| P1 | Before T0 | If before selection of approved root, only independently approved finite policy may be selected, still fixed60s compatible. If root already frozen at A/B, relevant drift BLOCK before key/capture continuation; whole-root disposition/fresh approval, never live refresh |
| P2 | After T0 before key birth | BLOCK on frozen version/digest/scope/authority eligibility drift, no key generated; no new T0 or expiry |
| P3 | After key birth before SIGN | BLOCK, discard private preparation and rollback controlled open T_REG; no re-key under old root |
| P4 | After SIGN before binding | BLOCK new acceptance/write on relevant drift; original signed bytes never changed; unknown COMMIT query-first |
| P5 | After binding COMMIT | Original exact tuple/policy retained for historical replay; independent later effects check current policy/governance; no activation/renewal from old registration |
| P6 | During recovery | Read/rederive original approved policy/window/public proof; a new live policy cannot rewrite historic identity. Unknown original context HOLD; any later operation retains current guards |

Relevant change means approved header/readiness/policy/deployment/authority mismatch, revocation or effective eligibility loss, not arbitrary unrelated configuration movement. Protected immutable policy rows cannot be edited in place. Actual BINDING_VALIDITY must permit the unchanged60s within its approved maximum, and nested transaction/read/effect bounds remain enforced; no min(), default, grace or cap widening substitutes for proof. Current finite policy compatibility/numeric margin is not established by source-only review. Canonical key/authority locks serialize the selected T_REG path; original preparation custody plus query-before-duplicate prevents two processes from generating independently valid candidates for one root. A second actor never assumes ownership because a UUID/lock flag matches, or because the first process disappeared. Custody/lock runtime enforcement is a future proof requirement, not a new coordinator or inferred implementation.

## Watchdog and H01

Watchdog may observe the original fixed deadline and fresh approved DB/health/elapsed facts, detect/report expiry or stale process observations, and use only its existing approved identity-bound cancel/drain authority. It may not create a signature, authorize signing, mutate T0/valid_from/expires_at, renew, trigger blind retry, change identity, infer COMMIT outcome or make an expired root eligible. “Stale” observation is not a new durable state transition: existing ADMIN owns lifecycle disposition. Existing service OID/incarnation whitelist is not automatically authority over postgres ADMIN or an external signer process; this review adds no such scope. Future operational review must qualify the actual selected ADMIN path and host/clock continuity under existing authority; if unavailable it stays blocked. WATCHDOG_STATUS=OPEN/HIGH.

H01 effect is limited to resolving semantic checkpoint/expiry interpretation for its later transport/RR/jitter and numerical-margin review. No timing bound changes, measurements, envelope feasibility, readiness or runtime execution are proven; H01 remains OPEN/HIGH. Current aggregate B0/H2/M0/L0 remains unchanged, G3F.4 HOLD. This gate has no new normative contradiction or unresolved legal interval/event/decision: B0/H0/M0/L0. Implementation and operational qualification are explicitly separate outstanding gates, not suppressed contract findings.

## Adversarial S01-S36

Each case was exercised against the offline finite model and checked against the source/contract mapping. Authorized-mutation descriptions are future conditional authority only; this review performs zero such mutations. Historical query actions require existing approved ADMIN identity, exact root/public proofs and writer quiescence; “found/absent” in the model means verified full outcome, not an arbitrary caller assertion.

| Case / PRECONDITION | WINDOW_STATE | SIGNATURE_STATE | DURABLE_STATE | EXPECTED_DECISION | AUTHORIZED_MUTATION | FORBIDDEN_MUTATION | RECOVERY_ACTION | FAIL_CLOSED_CONDITION | Validation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| S01 Originating preparation, all other prerequisites, sign starts at lower endpoint | AT_START | Not invoked | None | ALLOW | None in this review; future step only if separately qualified/authorized | New T0/IDs/key/signature, renewal, blind write, private persistence, public protected projection | Existing query-first disposition on any possible durable outcome | Unqualified clock/authority/policy, missing exact context, expired fresh guard or unknown outcome | PASS_OFFLINE_CONTRACT |
| S02 Sign requested at start-1us | BEFORE | Not invoked | None | BLOCK | None in this review; future step only if separately qualified/authorized | New T0/IDs/key/signature, renewal, blind write, private persistence, public protected projection | Existing query-first disposition on any possible durable outcome | Unqualified clock/authority/policy, missing exact context, expired fresh guard or unknown outcome | PASS_OFFLINE_CONTRACT |
| S03 SIGN returns complete bytes at end-1us, independent guards pass | PRE_END | In flight | None | ALLOW | None in this review; future step only if separately qualified/authorized | New T0/IDs/key/signature, renewal, blind write, private persistence, public protected projection | Creation predicate only; later verify/write/commit guards can still block | Unqualified clock/authority/policy, missing exact context, expired fresh guard or unknown outcome | PASS_OFFLINE_CONTRACT |
| S04 SIGN returns at exclusive end | AT_END | Candidate bytes must be discarded | None | BLOCK | None in this review; future step only if separately qualified/authorized | New T0/IDs/key/signature, renewal, blind write, private persistence, public protected projection | Existing query-first disposition on any possible durable outcome | Unqualified clock/authority/policy, missing exact context, expired fresh guard or unknown outcome | PASS_OFFLINE_CONTRACT |
| S05 SIGN returns at end+1us | AFTER | Candidate bytes must be discarded | None | BLOCK | None in this review; future step only if separately qualified/authorized | New T0/IDs/key/signature, renewal, blind write, private persistence, public protected projection | Existing query-first disposition on any possible durable outcome | Unqualified clock/authority/policy, missing exact context, expired fresh guard or unknown outcome | PASS_OFFLINE_CONTRACT |
| S06 SIGN starts end-1us then crosses end before completion | CROSSED | Single invocation, inadmissible candidate | Open T_REG | BLOCK | None in this review; future step only if separately qualified/authorized | New T0/IDs/key/signature, renewal, blind write, private persistence, public protected projection | Existing query-first disposition on any possible durable outcome | Unqualified clock/authority/policy, missing exact context, expired fresh guard or unknown outcome | PASS_OFFLINE_CONTRACT |
| S07 Verification begins before end, finishes at/after end | CROSSED | Pre-expiry candidate; no new acceptance | Open T_REG | BLOCK | None in this review; future step only if separately qualified/authorized | New T0/IDs/key/signature, renewal, blind write, private persistence, public protected projection | Existing query-first disposition on any possible durable outcome | Unqualified clock/authority/policy, missing exact context, expired fresh guard or unknown outcome | PASS_OFFLINE_CONTRACT |
| S08 Write begins before end, final write postcheck at end | CROSSED | Verified original | Tentative rows only | BLOCK | None in this review; future step only if separately qualified/authorized | New T0/IDs/key/signature, renewal, blind write, private persistence, public protected projection | Existing query-first disposition on any possible durable outcome | Unqualified clock/authority/policy, missing exact context, expired fresh guard or unknown outcome | PASS_OFFLINE_CONTRACT |
| S09 All guards valid, COMMIT already dispatched, DB completes after end | AFTER | Verified original | Valid admission, commit in flight | ALLOW | Only completion/visibility of previously admitted exact T_REG; no new writes | New T0/IDs/key/signature, renewal, blind write, private persistence, public protected projection | Historical success; unknown response instead requires query-first | Unqualified clock/authority/policy, missing exact context, expired fresh guard or unknown outcome | PASS_OFFLINE_CONTRACT |
| S10 Ambiguous dispatched COMMIT after expiry; exact complete root independently proven | AFTER | Original public signature | Exact complete committed root | REPLAY_EXISTING | None in this review; future step only if separately qualified/authorized | New T0/IDs/key/signature, renewal, blind write, private persistence, public protected projection | Existing query-first disposition on any possible durable outcome | Unqualified clock/authority/policy, missing exact context, expired fresh guard or unknown outcome | PASS_OFFLINE_CONTRACT |
| S11 Same live owner reads fresh DB eligibility N without recapture | INSIDE | Not invoked | Open T_REG | ALLOW | Fresh read only; tuple unchanged | New T0/IDs/key/signature, renewal, blind write, private persistence, public protected projection | Existing query-first disposition on any possible durable outcome | Unqualified clock/authority/policy, missing exact context, expired fresh guard or unknown outcome | PASS_OFFLINE_CONTRACT |
| S12 Retry attempts new T0 on same root | INSIDE | Any | Any | BLOCK | None in this review; future step only if separately qualified/authorized | New T0/IDs/key/signature, renewal, blind write, private persistence, public protected projection | Existing query-first disposition on any possible durable outcome | Unqualified clock/authority/policy, missing exact context, expired fresh guard or unknown outcome | PASS_OFFLINE_CONTRACT |
| S13 Retry attempts another key on same root | INSIDE | Existing prepared key | Open T_REG | BLOCK | None in this review; future step only if separately qualified/authorized | New T0/IDs/key/signature, renewal, blind write, private persistence, public protected projection | Existing query-first disposition on any possible durable outcome | Unqualified clock/authority/policy, missing exact context, expired fresh guard or unknown outcome | PASS_OFFLINE_CONTRACT |
| S14 Retry attempts second signature | INSIDE | One original candidate | Open T_REG | BLOCK | None in this review; future step only if separately qualified/authorized | New T0/IDs/key/signature, renewal, blind write, private persistence, public protected projection | Existing query-first disposition on any possible durable outcome | Unqualified clock/authority/policy, missing exact context, expired fresh guard or unknown outcome | PASS_OFFLINE_CONTRACT |
| S15 Process crashes immediately before SIGN | INSIDE | Never invoked; key lost | No proven committed root | RECOVER | None in this review; future step only if separately qualified/authorized | New T0/IDs/key/signature, renewal, blind write, private persistence, public protected projection | Existing query-first disposition on any possible durable outcome | Unqualified clock/authority/policy, missing exact context, expired fresh guard or unknown outcome | PASS_OFFLINE_CONTRACT |
| S16 Process crashes after SIGN byte return | INSIDE | Original bytes may be lost/retained public-only | No proven committed root | RECOVER | None in this review; future step only if separately qualified/authorized | New T0/IDs/key/signature, renewal, blind write, private persistence, public protected projection | Existing query-first disposition on any possible durable outcome | Unqualified clock/authority/policy, missing exact context, expired fresh guard or unknown outcome | PASS_OFFLINE_CONTRACT |
| S17 Binding writes staged; COMMIT dispatched; process dies before response | INSIDE_OR_AFTER | Verified original | Unknown commit | RECOVER | None in this review; future step only if separately qualified/authorized | New T0/IDs/key/signature, renewal, blind write, private persistence, public protected projection | Existing query-first disposition on any possible durable outcome | Unqualified clock/authority/policy, missing exact context, expired fresh guard or unknown outcome | PASS_OFFLINE_CONTRACT |
| S18 COMMIT succeeded; process dies before caller response; later query proves it | AFTER | Original public signature | Exact complete committed root | REPLAY_EXISTING | None in this review; future step only if separately qualified/authorized | New T0/IDs/key/signature, renewal, blind write, private persistence, public protected projection | Existing query-first disposition on any possible durable outcome | Unqualified clock/authority/policy, missing exact context, expired fresh guard or unknown outcome | PASS_OFFLINE_CONTRACT |
| S19 Relevant approved policy/version/authority drifts during SIGN | INSIDE | In-flight candidate | Open T_REG | BLOCK | None in this review; future step only if separately qualified/authorized | New T0/IDs/key/signature, renewal, blind write, private persistence, public protected projection | Existing query-first disposition on any possible durable outcome | Unqualified clock/authority/policy, missing exact context, expired fresh guard or unknown outcome | PASS_OFFLINE_CONTRACT |
| S20 New policy lifetime during recovery, original exact root committed | AFTER | Original signed window | Exact complete original root | REPLAY_EXISTING | None in this review; future step only if separately qualified/authorized | New T0/IDs/key/signature, renewal, blind write, private persistence, public protected projection | Retain original lifetime/history; never apply new policy as old-root permission | Unqualified clock/authority/policy, missing exact context, expired fresh guard or unknown outcome | PASS_OFFLINE_CONTRACT |
| S21 Timezone display changes but typed instant and canonical UTC bytes remain exact | INSIDE | Original candidate | Open T_REG | ALLOW | None in this review; future step only if separately qualified/authorized | New T0/IDs/key/signature, renewal, blind write, private persistence, public protected projection | Existing query-first disposition on any possible durable outcome | Any civil-time reinterpretation/noncanonical signed text -> BLOCK | PASS_OFFLINE_CONTRACT |
| S22 Precision conversion truncates a nonzero sub-us remainder | INSIDE | Changed canonical payload | Open T_REG | BLOCK | None in this review; future step only if separately qualified/authorized | New T0/IDs/key/signature, renewal, blind write, private persistence, public protected projection | Existing query-first disposition on any possible durable outcome | Unqualified clock/authority/policy, missing exact context, expired fresh guard or unknown outcome | PASS_OFFLINE_CONTRACT |
| S23 App clock disagrees; approved fresh DB sample remains inside | INSIDE_DB | Original candidate | Open T_REG | ALLOW | None in this review; future step only if separately qualified/authorized | New T0/IDs/key/signature, renewal, blind write, private persistence, public protected projection | Use DB only; app time never edits identity or supplies eligibility | Unqualified clock/authority/policy, missing exact context, expired fresh guard or unknown outcome | PASS_OFFLINE_CONTRACT |
| S24 DB observed wall clock regresses below prior eligible sample | REGRESSION | In-flight candidate | Open T_REG | BLOCK | None in this review; future step only if separately qualified/authorized | New T0/IDs/key/signature, renewal, blind write, private persistence, public protected projection | Existing query-first disposition on any possible durable outcome | Unqualified clock/authority/policy, missing exact context, expired fresh guard or unknown outcome | PASS_OFFLINE_CONTRACT |
| S25 Two runtimes request SIGN on same frozen root; actor2 is not original owner | INSIDE | Owner1 not yet invoked | Open owner1 T_REG | BLOCK | None in this review; future step only if separately qualified/authorized | New T0/IDs/key/signature, renewal, blind write, private persistence, public protected projection | No takeover; query original writer after quiescence | Unqualified clock/authority/policy, missing exact context, expired fresh guard or unknown outcome | PASS_OFFLINE_CONTRACT |
| S26 Two runtimes request binding write; actor2 lacks original preparation custody | INSIDE | Original verified candidate | Open owner1 T_REG | BLOCK | None in this review; future step only if separately qualified/authorized | New T0/IDs/key/signature, renewal, blind write, private persistence, public protected projection | Existing query-first disposition on any possible durable outcome | Unqualified clock/authority/policy, missing exact context, expired fresh guard or unknown outcome | PASS_OFFLINE_CONTRACT |
| S27 Completed exact ceremony observed after expiry | AFTER | Original public signature | Committed exact | REPLAY_EXISTING | None in this review; future step only if separately qualified/authorized | New T0/IDs/key/signature, renewal, blind write, private persistence, public protected projection | Existing query-first disposition on any possible durable outcome | Unqualified clock/authority/policy, missing exact context, expired fresh guard or unknown outcome | PASS_OFFLINE_CONTRACT |
| S28 Expired incomplete root; full absence independently proven | AFTER | Incomplete/failed preparation | Full root absent after quiescence | BLOCK | None in this review; future step only if separately qualified/authorized | New T0/IDs/key/signature, renewal, blind write, private persistence, public protected projection | Block old root; existing governed abandonment, no fresh allocation in this gate | Unqualified clock/authority/policy, missing exact context, expired fresh guard or unknown outcome | PASS_OFFLINE_CONTRACT |
| S29 Valid old signature submitted for new binding after end | AFTER | Cryptographically valid pre-expiry original | No committed root | BLOCK | None in this review; future step only if separately qualified/authorized | New T0/IDs/key/signature, renewal, blind write, private persistence, public protected projection | Existing query-first disposition on any possible durable outcome | Unqualified clock/authority/policy, missing exact context, expired fresh guard or unknown outcome | PASS_OFFLINE_CONTRACT |
| S30 Old signature paired with changed canonical payload | INSIDE | Signature/payload mismatch | Open T_REG | BLOCK | None in this review; future step only if separately qualified/authorized | New T0/IDs/key/signature, renewal, blind write, private persistence, public protected projection | Existing query-first disposition on any possible durable outcome | Unqualified clock/authority/policy, missing exact context, expired fresh guard or unknown outcome | PASS_OFFLINE_CONTRACT |
| S31 Old signature paired with altered expires_at | INSIDE_OR_AFTER | Frozen original endpoints | Open T_REG | BLOCK | None in this review; future step only if separately qualified/authorized | New T0/IDs/key/signature, renewal, blind write, private persistence, public protected projection | Existing query-first disposition on any possible durable outcome | Unqualified clock/authority/policy, missing exact context, expired fresh guard or unknown outcome | PASS_OFFLINE_CONTRACT |
| S32 Recovery independently proves complete row set plus original tuple/signature | AFTER | Original public proof | Complete exact root | REPLAY_EXISTING | None in this review; future step only if separately qualified/authorized | New T0/IDs/key/signature, renewal, blind write, private persistence, public protected projection | Existing query-first disposition on any possible durable outcome | Unqualified clock/authority/policy, missing exact context, expired fresh guard or unknown outcome | PASS_OFFLINE_CONTRACT |
| S33 Recovery proves full root/effect absence, not merely a missing header | AFTER | Old candidate, no resubmission | Proven absent | BLOCK | None in this review; future step only if separately qualified/authorized | New T0/IDs/key/signature, renewal, blind write, private persistence, public protected projection | Existing whole-root disposition; any legacy governance orphan uses existing cleanup first | Unqualified clock/authority/policy, missing exact context, expired fresh guard or unknown outcome | PASS_OFFLINE_CONTRACT |
| S34 DB/writer/snapshot/identity/lineage outcome cannot be proven | UNKNOWN | No fresh signing | Unknown | RECOVER | None in this review; future step only if separately qualified/authorized | New T0/IDs/key/signature, renewal, blind write, private persistence, public protected projection | Q3 ESCALATE existing ADMIN and HOLD; no inference of zero or completeness | Unqualified clock/authority/policy, missing exact context, expired fresh guard or unknown outcome | PASS_OFFLINE_CONTRACT |
| S35 Watchdog observes expiry during SIGN; final DB check reaches end | AT_END | In flight | Open T_REG | BLOCK | None in this review; future step only if separately qualified/authorized | New T0/IDs/key/signature, renewal, blind write, private persistence, public protected projection | Existing bounded detect/drain/report only; ADMIN disposition; no watchdog signer authority | Unqualified clock/authority/policy, missing exact context, expired fresh guard or unknown outcome | PASS_OFFLINE_CONTRACT |
| S36 H01 changes independently; execution prerequisites remain unqualified | ANY | No newly authorized candidate | None | BLOCK | None in this review; future step only if separately qualified/authorized | New T0/IDs/key/signature, renewal, blind write, private persistence, public protected projection | Temporal contract unchanged; H01 OPEN/HIGH; no execution authorization from this review | Unqualified clock/authority/policy, missing exact context, expired fresh guard or unknown outcome | PASS_OFFLINE_CONTRACT |

## Finite abstract state/transition check

The private offline model enumerates the full declared finite domain of conceptual phases, five relative DB boundary instants (-1us, start, end-1us, end, end+1us), previous-sample high water, two original-owner/contender actors, approved-policy match, qualified clock continuity and zero/one SIGN count. Phase/signature consistency excludes invalid state combinations explicitly. Original tuple is immutable(0,0,60000000) as synthetic relative coordinates; no actual ceremony identifiers, clock samples, keys, signature bytes or payload generation occur. ROOT/TX/FROZEN/key/sign/verify/write/commit/ambiguous/history labels are model variables only, not new DB states.

Every admissible state is tested with all31 model actions and both actors. Guarded creation/verification/write/send actions are compared to an independent categorical START/PRE_END permission oracle; invariants cover immutable T0/expiry/payload, at-most-one SIGN, wrong-owner denial, expired/new effects denied, no historical reactivation, original replay, conservative rollback detection, valid admission before COMMIT, successor-domain closure, and unknown outcome remaining recovery. Fresh observations can change eligibility only. COMMIT success after valid dispatch is deliberately allowed outside window; read-only recovery remains allowed after expiry. Crashes destroy resumability of incomplete preparations, not infer durable absence.

Ordered witnesses exercise complete one-sign registration, COMMIT ACK loss across expiry then exact replay, original-owner vs contender races, and crashes before/after signing/verification/staged writes with no mutable resume. Negative controls exercise the tempting start-only expiry crossing and duplicate SIGN, both rejected. Synthetic exact signed-i64 microsecond transport and equal-instant timezone display checks plus source strict precision checks pass. This is finite contract checking; it does not exhaust PostgreSQL concurrency, JCA scheduling, locks, network faults, deployment clock continuity or production implementation. Public outcome proofs, original custody, canonical lock acquisition, qualified clocks and same-connection sequencing are explicit preconditions requiring later qualification.

```json
{
  "MODEL_STATES_TESTED": 3400,
  "MODEL_TRANSITIONS_TESTED": 210800,
  "INVALID_TRANSITIONS_REJECTED": 166140,
  "INVALID_STATE_COMBINATIONS_EXCLUDED": 2600,
  "COUNTEREXAMPLES_FOUND": 0,
  "NEGATIVE_CONTROLS_REJECTED": 2,
  "DOMAIN": {
    "relative_microseconds": [
      -1,
      0,
      59999999,
      60000000,
      60000001
    ],
    "phases": [
      "ROOT",
      "TX_OPEN",
      "FROZEN",
      "KEY",
      "SIGNING",
      "CANDIDATE",
      "VERIFYING",
      "VERIFIED",
      "WRITING",
      "STAGED",
      "COMMIT_SENT",
      "AMBIGUOUS",
      "COMMITTED",
      "ABORTED",
      "REPLAYED"
    ],
    "actors": 2,
    "policy_match": 2,
    "qualified_clock": 2,
    "signature_calls": "0/1 with phase invariants"
  },
  "MODEL_SCOPE": "finite offline contract abstraction, no runtime/production exhaustiveness"
}
```

## Final validation and next bounded gate

All source checks PASS; S01-S36 PASS_OFFLINE_CONTRACT; zero counterexamples in the final selected model. All1257 tracked byte hashes—including frozen time evidence and TC-R01 remediation—remain unchanged. Only this new evidence file is created. No DB/container/credential access, migration, production edit, UUID/key/signature generation, private-key persistence, authority/role/privilege mutation, fixture, timer, coordinator or changed temporal bound. This review does not claim a database pre/post snapshot equality.

Recommended NEXT_GATE=G3F_4_SIGNING_WINDOW_OPERATIONAL_REVIEW, the existing recovery sequence next step. Remaining actual gap: qualify approved finite policy actual/max compatibility with fixed60s, full selected ADMIN critical-path/transaction/lock/JCA/write/pre-COMMIT transport latency and headroom, clock continuity and supervision/custody prerequisites within existing authority. No numeric margin or runtime proof is inferred here, and OPEN watchdog/H01 must stay separate. This recommendation is a review/qualification handoff, not authorization to generate keys/signatures, implement/execute a ceremony, start runtime tests or close remaining findings. NEXT_GATE_STARTED=NO.

Stage only this artifact after PASS and final one-path audit. One docs(package-0090) evidence commit follows prior gate convention; push only checkpoint branch, then fetch/live-remote equality and clean-worktree verification. Final commit hash is returned after that verification rather than invented inside its own immutable body.

```json
{
  "G3F_4_FINAL_CEREMONY_SIGNING_WINDOW_CONTRACT_REVIEW": "PASS_CONTRACT_ONLY",
  "BRANCH": "checkpoint/package-0090-cloud-handoff",
  "BASELINE_HEAD": "08d6025f3c30e70e32714aeaf49199b8d411d13e",
  "SIGNING_WINDOW_START": "valid_from=issued_at=signed_start=T0 (same T_REG transaction opening)",
  "SIGNING_WINDOW_END": "expires_at=signed_end=T0+60000000us",
  "SIGNING_WINDOW_INTERVAL": "[T0,T0+60000000us), immutable and nonrenewable",
  "SIGNATURE_CREATION_ELIGIBILITY": "Existing authorized originating live preparation only; fresh same-cluster DB wall-clock guards before SIGN and after successful byte return must satisfy start<=N<end, qualified continuity/no regression and unchanged root/policy/authority/payload; at most one SIGN invocation.",
  "SIGNATURE_CREATED_AT_EVENT": "Successful return of the single cryptographic SIGN operation, when complete final signature bytes first become available to the originating transient preparation. Logical event only: no new SQL field, timestamp receipt or client-clock authority.",
  "SIGNATURE_VERIFICATION_RULE": "Separate local public JCA verification of exact original preimage/SPKI/signature plus header-to-signed-endpoint equality; fresh DB eligibility immediately before and after verification, within same immutable window. No fresh acceptance after expiry; historical cryptographic read verification remains allowed with original evidence and no new effect.",
  "DURABLE_BINDING_ELIGIBILITY": "Complete original eleven-row T_REG only after eligible single signature/local verification and private-key destruction; fresh DB guards before/after write batches and after exact write-set/constraints immediately before COMMIT. Every guard inside [start,end); no new write at/after expiry.",
  "DURABLE_BINDING_COMMIT_POINT": "Successful database COMMIT of the exact complete T_REG; staged SQL writes and an in-memory signature are not durable. Unknown ACK requires TC-R01-safe query-first proof of exact complete committed root before declaring success.",
  "EXPIRY_DURING_SIGNING_RULE": "BLOCK candidate at completion>=end or failed/unavailable postguard; discard ephemeral candidate/private material and abort controlled open T_REG. An already invoked SIGN is never retried on the old root.",
  "EXPIRY_AFTER_SIGNATURE_BEFORE_BINDING_RULE": "BLOCK any new binding write at/after end even with a mathematically valid pre-expiry signature. Existing complete committed root may be read; no window/signature renewal.",
  "EXPIRY_DURING_COMMIT_RULE": "Before final eligible guard/dispatch: BLOCK and rollback only if transaction is known controlled/open. After valid final guard and COMMIT dispatch: visibility may occur after end; confirmed complete -> historical success, unknown -> RECOVER/query-first. No retroactive rollback or new mutation.",
  "AMBIGUOUS_COMMIT_AFTER_EXPIRY_RULE": "Q1 exact complete committed root -> REPLAY_EXISTING; Q2 authoritative full absence after writer quiescence/locks/fresh snapshot -> BLOCK old root and govern abandonment; Q3 unprovable/partial/conflicting -> ESCALATE existing ADMIN and HOLD with no mutation. No replacement IDs/key/signature/tuple.",
  "RETRY_RULE": "Fresh eligibility samples may change N only; never T0/expiry/identity/payload. Only original uninterrupted already-live preparation may continue an unexecuted next step once. Duplicate mutable calls, unknown SIGN completion, process loss or another-runtime takeover deny resume and require existing query-first disposition.",
  "REPLAY_RULE": "Exact original committed tuple and public evidence may be observed/verified after expiry; no new authority effect, signer creation, capture, signing, INSERT or reactivation.",
  "RECOVERY_RULE": "Existing ADMIN, original immutable root, original-writer quiescence, canonical existing locks and one fresh corrected nonsecret Q1-Q26 snapshot; full root plus independently verified public original -> historical replay; full absence -> block/dispose old root; partial/unknown/conflict -> hold/escalate. Later domain effects require existing domain reconciliation.",
  "POLICY_CHANGE_DURING_CEREMONY_RULE": "Freeze exact approved policy version/digest and authority with original root. Relevant live eligibility/governance drift blocks unfinished work; never reload lifetime/payload/T0 or repair the old root. Committed original remains historical; future effects recheck their own current authority. Unrelated config reload has no authority to alter approved data.",
  "WATCHDOG_BOUNDARY": "Existing identity-bound observe/detect/report/cancel-drain duties only within approved whitelist. Stale/expiry observations are not signer authority or new durable states; existing ADMIN owns lifecycle disposition. No signing, renewal, tuple changes, blind retry, outcome inference or scope expansion; OPEN/HIGH.",
  "H01_EFFECT": "Narrows semantic checkpoints for future latency/transport qualification; no numeric envelope, runtime transport, execution proof or HIGH closure. H01 OPEN/HIGH.",
  "SIGNING_AT_VALID_FROM": "ALLOW_TEMPORAL_PREDICATE_ONLY_ALL_PREREQUISITES_REQUIRED",
  "SIGNING_BEFORE_VALID_FROM": "BLOCK",
  "SIGNING_AT_EXPIRES_AT": "BLOCK",
  "SIGNING_AFTER_EXPIRES_AT": "BLOCK",
  "BIND_BEFORE_EXPIRY": "ALLOW_ADMITTED_WRITE_ONLY_ALL_PREREQUISITES_REQUIRED",
  "BIND_AT_EXPIRY": "BLOCK_NEW_WRITE",
  "BIND_AFTER_EXPIRY_WITH_PREEXPIRY_SIGNATURE": "BLOCK_NEW_WRITE; existing validly admitted COMMIT visibility is historical",
  "TEMPORAL_CONTRACT_CHANGED": "NO",
  "CRYPTOGRAPHIC_PAYLOAD_STABLE": "YES",
  "WINDOW_RENEWAL_ALLOWED": "NO",
  "WATCHDOG_STATUS": "OPEN",
  "H01_STATUS": "OPEN",
  "G3F_4_STATUS": "HOLD",
  "BLOCKER_COUNT": 0,
  "HIGH_COUNT": 0,
  "MEDIUM_COUNT": 0,
  "LOW_COUNT": 0,
  "AGGREGATE_G3F_4_BLOCKER_COUNT": 0,
  "AGGREGATE_G3F_4_HIGH_COUNT": 2,
  "AGGREGATE_G3F_4_MEDIUM_COUNT": 0,
  "AGGREGATE_G3F_4_LOW_COUNT": 0,
  "DATABASE_MUTATION": "NO",
  "KEY_GENERATION": "NO",
  "PRIVATE_KEY_PERSISTENCE": "NO",
  "SIGNATURE_CREATION": "NO",
  "IDENTIFIER_GENERATION": "NO",
  "PRODUCTION_IMPLEMENTATION": "NO",
  "MODEL_STATES_TESTED": 3400,
  "MODEL_TRANSITIONS_TESTED": 210800,
  "INVALID_TRANSITIONS_REJECTED": 166140,
  "COUNTEREXAMPLES_FOUND": 0,
  "ARTIFACTS_CREATED": [
    "docs/evidence/PACKAGE-0090-G3F-4-FINAL-CEREMONY-SIGNING-WINDOW-CONTRACT-REVIEW.md"
  ],
  "ARTIFACTS_MODIFIED": [],
  "NEXT_GATE": "G3F_4_SIGNING_WINDOW_OPERATIONAL_REVIEW",
  "NEXT_GATE_STARTED": "NO"
}
```

## Preserved prior evidence inventory

| Path | Bytes | SHA256 |
| --- | --- | --- |
| docs/evidence/PACKAGE-0090-BINDING-AUTHORITY-INTEGRITY.json | 15365204 | `5c0f957f9682f744e1f88a4c4cef0f479a8909bea8f28c343ccdc1e679e54001` |
| docs/evidence/PACKAGE-0090-BINDING-PROVISIONING-CONTRACT-DESIGN.md | 14465 | `5add8c6da53ffcb722cd78fdc4f4e35c1a50f43431dd4349d8684f02b8254787` |
| docs/evidence/PACKAGE-0090-BINDING-PROVISIONING-MATRIX.json | 561827 | `8be5d6141b6cfa459137e778362be4161a9f6b440ea07981aca3c24a812eed5a` |
| docs/evidence/PACKAGE-0090-BINDING-PROVISIONING-NEGATIVE-MATRIX.json | 9828 | `5efbd2450fd94990a1cb7c0cbcda789d747006c76176914af96afb7d16689496` |
| docs/evidence/PACKAGE-0090-CURRENT-INDEPENDENT-SOURCE-REVIEW.json | 505867 | `631b68e8c483ab283c4caa11b96bd6ceac60f3226c6af9bac14d68e564699d36` |
| docs/evidence/PACKAGE-0090-DEPLOYMENT-INCARNATION-APPROVAL-MATRIX.json | 16532764 | `ca5550e9273c95b5d91ad9c33e6c8bedd0771135e7f16a2303c76de72d67e1da` |
| docs/evidence/PACKAGE-0090-ED25519-NATIVE-REVIEW.json | 31105 | `f5e255dbd134656e58af257c411ca5bd36a5b86b432117bbccf710eaba91f5dc` |
| docs/evidence/PACKAGE-0090-ED25519-NATIVE-REVIEW.md | 9277 | `ef1c29c29ea19b221bfa5c3a9e03194576587c028ee8b8074b9f75043cd739ae` |
| docs/evidence/PACKAGE-0090-ENROLLMENT-BINDING-CONTRACT-CLOSURE.md | 10003 | `f091d0b11446151dcb9db3636f8d1bc82c9ed0c724767e00fb537a267b64ac86` |
| docs/evidence/PACKAGE-0090-ENROLLMENT-ENTRYPOINT-AUTHORITY-REVIEW.json | 31486 | `a719df6b7ce319d92d701d012711eafd1d46df45a84a84e98d0d944e87858657` |
| docs/evidence/PACKAGE-0090-ENROLLMENT-ENTRYPOINT-AUTHORITY-REVIEW.md | 18739 | `1b673e92df11070105e0bfb326ab6b23aa262f3543af2ab73476741742412c7b` |
| docs/evidence/PACKAGE-0090-ENROLLMENT-ENTRYPOINT-READONLY-SNAPSHOT.json | 559267 | `3b9cf2ca67890eb3cb42f9ee451b5c495a5fd2a5403b7454831b2965e61aadb0` |
| docs/evidence/PACKAGE-0090-EXECUTOR-FINAL-TESTS.txt | 914 | `9b149f2b6bcfb5ef8ec1de75dcb9758ab5f0570180ff73263d923f140bb63bf5` |
| docs/evidence/PACKAGE-0090-FULL-TESTS.txt | 26075 | `9d4996a557ba6cbabc5a1e90a6e70e596d48c19170b039c680d74a207aabdbc0` |
| docs/evidence/PACKAGE-0090-G3F-3B-CATALOG-GOLDEN-CLOSURE.md | 2421 | `39e220d5fabcf62e1e37c08603b17681a283a13ec31c7813bba4c718c8373e40` |
| docs/evidence/PACKAGE-0090-G3F-3B-CATALOG-GOLDENS.json | 284137 | `f53bbfb436348ea2c2e75599946fe883c02ad03d0b91ddc5196b296ab3c65b2c` |
| docs/evidence/PACKAGE-0090-G3F-3B-CLOUD-EXECUTION.md | 12044 | `5413f976c7d157557250e74918b6b537446a633b6eccd8f23b976ff9716ed5eb` |
| docs/evidence/PACKAGE-0090-G3F-3B-CODEC-GOLDENS.json | 53108 | `2876d9774823f285fc714cf8ad021cd0b38adb568614a399defa6cc2cd1d1766` |
| docs/evidence/PACKAGE-0090-G3F-3B-EVIDENCE-FIXTURE-001.json | 7765 | `0c071e9f4de63f3515a3147ea979e872012f3d90602b02fa09f895a869dde15c` |
| docs/evidence/PACKAGE-0090-G3F-3B-FIXTURE-001.json | 5744 | `edfb8fe983a2adc5c7fed224fbc418108c4dbfcba9caa67fd15f640d92ddf820` |
| docs/evidence/PACKAGE-0090-G3F-3B-FIXTURE-CLOSURE.md | 6533 | `4715aa42f0bb5402d4be12b2f18ea53c98bb1211d0e023216cb78c194b223a0c` |
| docs/evidence/PACKAGE-0090-G3F-3B-INTERNAL-P-SOURCE-REVIEW.md | 3442 | `c412a8b08e28d39ace980f95e7e3df7cdc7bf28f7881f398f36266b0730194b9` |
| docs/evidence/PACKAGE-0090-G3F-3B-INTERNAL-Q-SOURCE-REVIEW.md | 4581 | `28551d80e34c2471813333f44dfce09589616c4cbcd8644df7a43a6d6180c7c9` |
| docs/evidence/PACKAGE-0090-G3F-3B-INTERNAL-Z-SOURCE-REVIEW.md | 2129 | `7559b27c50ec158fbeb7600b3e0c17817cc8764bfac775373560acadd6a47f59` |
| docs/evidence/PACKAGE-0090-G3F-3B-ISOLATED-REHEARSAL-HANDOFF.md | 7706 | `0b4ad2cfd1358613bbae22f3c2a9e1c95f93494f7c6e036f0812e02892e08f76` |
| docs/evidence/PACKAGE-0090-G3F-3B-NORMATIVE-EVIDENCE-CLOSURE.md | 3650 | `a407056d3581f1e6aad4b70337cef2c59a548a77980e0803ff298693d19a85a8` |
| docs/evidence/PACKAGE-0090-G3F-3B-POST-H02-SECURITY-REVIEW.json | 2793 | `8e01fe605a44b5575bbf831d39c8ec6959fa8e5b9f4c784e8d1f1af6cb066b0f` |
| docs/evidence/PACKAGE-0090-G3F-3B-POST-H02-SECURITY-REVIEW.md | 7083 | `7f99b920c2c0e00b406a8fa73503748b7f07fe3350eefb27c3d7b1f753192033` |
| docs/evidence/PACKAGE-0090-G3F-3B-PUBLIC-WRAPPER-PREREQUISITES.json | 26233 | `cf4f6e0aae1649782e1eb21b8994906e02410b9876ca1936a8374eb237fedde0` |
| docs/evidence/PACKAGE-0090-G3F-3B-PUBLIC-WRAPPER-PROGRESS.json | 3661 | `4195c94597cf3439ec23c1afd55a3f4c6802cb62da2f553ca01b49101460f31b` |
| docs/evidence/PACKAGE-0090-G3F-3B-PUBLIC-WRAPPERS-CONTRACT-HOLD.md | 5024 | `6c579261c4c791262258fc999f149e7d523ed9561209ba3ab47d62b0d59213d3` |
| docs/evidence/PACKAGE-0090-G3F-3B-S01-READINESS-AUTHORITY.json | 12635 | `1b1e835256d0e222bf6e445738e59a7805e9107d1b484f43725d2d94c5308645` |
| docs/evidence/PACKAGE-0090-G3F-3B-S01-TARGET-AUTHORITY-HOLD.md | 6033 | `5817365e55ee35f27fcb94c2f7fba5440000244340d38c0c08afeee64be09968` |
| docs/evidence/PACKAGE-0090-G3F-3B-S01-TARGET-CLOSURE.json | 300273 | `3778f846c1e0a0baa700f231e4627601c635fbcce42d6105349f83d27d77e0d6` |
| docs/evidence/PACKAGE-0090-G3F-3B-S01-TARGET-SOURCE-REVIEW.md | 3234 | `8b5e8d2d0e7a7365a3f7e9a059bcd5f496d0b935991414a6e3b7f4153f5614b0` |
| docs/evidence/PACKAGE-0090-G3F-3B-S02-CONSUMER-AUTHORITY-HOLD.md | 3809 | `ba97d272c245ab2a387a116afb81ccb65ec62899c65a4d46640dadbe42b73968` |
| docs/evidence/PACKAGE-0090-G3F-3B-S02-CONSUMER-AUTHORITY.json | 8909 | `44bd3a1187c247a4c016890c339d8228d2e83be765aef9e303e53f804fd9e624` |
| docs/evidence/PACKAGE-0090-G3F-3B-S02-VERIFICATION-PATH-HOLD.md | 4892 | `6c6f19474942bcff9f1cf803f60e8743b4775b2c794f1b69ed0fb29392f8edf2` |
| docs/evidence/PACKAGE-0090-G3F-3B-SOURCE-VALIDATION.json | 10259 | `9e547dfd80671c2f4d34839ca4bfa537ca221a5a52a5a78b3677fa965a8c0b67` |
| docs/evidence/PACKAGE-0090-G3F-4-08006-DIAGNOSTICS.json | 28711321 | `448b0e84a53763f843fc73f68c6a07446a06d77ea215f5fdc73d964d6db5d18e` |
| docs/evidence/PACKAGE-0090-G3F-4-AMBIGUOUS-COMMIT-RECOVERY.json | 77751 | `f22949d33e9daab11765e30f8b3da47be6e874c68f6f3e52e44f81cc367d5743` |
| docs/evidence/PACKAGE-0090-G3F-4-APPROVAL-AUTHORITY-CLOSURE.md | 8271 | `399040f3e47892302bff29a7e5920c8663f8b3f01cc91fb2576f58e8564cf24a` |
| docs/evidence/PACKAGE-0090-G3F-4-ATTESTATION-HEADER-TRANSACTION-GRAPH.json | 38733 | `7b283eb7a7f12d86753ad2b348caf0252a521c5dd0bba2c61eaff84fb2b2b677` |
| docs/evidence/PACKAGE-0090-G3F-4-BINDING-DEPENDENCY-GRAPH.json | 2233692 | `da505a68c1bfd9099d01308a0dd7ed27797017efc9e8cf089521331138c3df85` |
| docs/evidence/PACKAGE-0090-G3F-4-BINDING-GENERATION-AUTHORITY.json | 6771 | `961119a4894ca5f77540a13824712ec985d63ceabf430e959a11faf7fca93add` |
| docs/evidence/PACKAGE-0090-G3F-4-BINDING-HEADER-40-FIELD-MATRIX.json | 197580 | `908ffd5ed0b61a506ea8522309efacae43b660e7ffbcaf7a51de890ac7c5afec` |
| docs/evidence/PACKAGE-0090-G3F-4-BINDING-HEADER-INPUT-CONTRACT-CLOSURE.md | 17118 | `2f053e975cfcd0b6413c1982cd865bf7b37e5b2b65253e51b2cc3fff548cd8a0` |
| docs/evidence/PACKAGE-0090-G3F-4-BINDING-HEADER-INPUT-MATRIX.json | 44779 | `dd067e6b45207cfc41528f9e3309b02d8f95481000e6404229f2a069cc333646` |
| docs/evidence/PACKAGE-0090-G3F-4-BINDING-PLAN-AUTHORITY-CLOSURE.md | 12914 | `e8e1b23236f32116c7c1d3ad9c59160b9fff370c852a60594003dfcfaf979af9` |
| docs/evidence/PACKAGE-0090-G3F-4-BINDING-PLAN-AUTHORITY-MATRIX.json | 58809 | `4b6183c0eef78cf254e1ac3ab30b73b0e9a30c76c00362078a44377c6ad8a9e3` |
| docs/evidence/PACKAGE-0090-G3F-4-BINDING-PLAN-FINGERPRINT-CONTRACT.json | 9672 | `493208b50d2da8f81185f1c8dc93c16676f8ced3ee064133f8b975c798b40de8` |
| docs/evidence/PACKAGE-0090-G3F-4-BINDING-PLAN-REGISTRATION-INPUT-CLOSURE.md | 16852 | `44e07adf21d4cc9cb823079acef3aa4f9724e4e07da19a823ce902c825f21db9` |
| docs/evidence/PACKAGE-0090-G3F-4-BINDING-REGISTRATION-ID-LINEAGE.json | 1057154 | `0c51ba0d4e74fc06b7db790ac3ad925bc6ae053b76cd9b0337e89783e0dbf6a7` |
| docs/evidence/PACKAGE-0090-G3F-4-BINDING-TIMESTAMP-AUTHORITY.json | 7233 | `1e04dd75234935bff8fcc3b215c275cd3cdbdf69b837081e96314b08ffc880a9` |
| docs/evidence/PACKAGE-0090-G3F-4-CANONICAL-BINDING-PREREQUISITE-SCOPE.md | 10961 | `47f863125c3dd2272eddac768f6ca293b4d8378eefc429c29f6d153b4aac251d` |
| docs/evidence/PACKAGE-0090-G3F-4-CANONICAL-SOURCE-COMMITTER-RUNTIME.json | 15963994 | `4b8dffa159baf07506b98645b1b60343768f52aa81278b106d39424ec0f6841e` |
| docs/evidence/PACKAGE-0090-G3F-4-CEREMONY-CRASH-POINT-MATRIX.json | 44624 | `9313ed5258fcaa17b6d52fb41e13129959ea2c2f3c4b459f5495af25f8a616f4` |
| docs/evidence/PACKAGE-0090-G3F-4-COMMAND-AUTHORITY-INPUT-GRAPH.json | 9082 | `6b17cdd3fc575037bbbeef70756bd09f8fcbbf13f9fd7a71b5d200f7c00dbf8b` |
| docs/evidence/PACKAGE-0090-G3F-4-CONCURRENCY-2.json | 2034 | `6c3b4f4dc20ada0013e23976c73e60a5bc86d13479e4ae71719cfded4816a234` |
| docs/evidence/PACKAGE-0090-G3F-4-CONCURRENCY.json | 7494 | `4fcba43d874705981f55cf77232cee618f9be6bd9e34a31ed9aa995807e08d56` |
| docs/evidence/PACKAGE-0090-G3F-4-DATA-SCOPE-INTEGRITY.json | 1246988 | `edb846a66415b5861e7ef2e8c0674975b7b836611d8829d8a3d75ac20cb6b042` |
| docs/evidence/PACKAGE-0090-G3F-4-DNA-INVARIANT-REVIEW.md | 3106 | `c8dd9b3b3c14c73b1bbe39327477ab8a95252007c1659d763f6ca3f5fccc0bd1` |
| docs/evidence/PACKAGE-0090-G3F-4-DOMAIN-DEPENDENCY-GRAPH.json | 46796 | `ef3346b9660448a8815261e16ecb7c03fb2930f0645484730d65d2d1222825cd` |
| docs/evidence/PACKAGE-0090-G3F-4-E2E-RUNTIME.json | 2837 | `9f63fda8b6728b5a8fbca903f4e7fbfc5c1b6ef68edad30149e65caa2c87ec53` |
| docs/evidence/PACKAGE-0090-G3F-4-ELIGIBLE-S01-TIMING.json | 8044 | `ad634aaf8ed1a885132e0f02d58401a31ed8e739dfe36325c4e2ee6c9483fb06` |
| docs/evidence/PACKAGE-0090-G3F-4-EPHEMERAL-REHEARSAL-CREDENTIAL-LIFECYCLE.json | 7276 | `6b135c84d2db7e0ddc1cd024af0a5c7385445701af6758b4c6ab2f9b86880a4a` |
| docs/evidence/PACKAGE-0090-G3F-4-EVIDENCE-BINDING-FINGERPRINT-MATRIX.json | 30203 | `de884a0c2d83b886a072c51978fcf8020549130f0e6b18871127324fa8a8b868` |
| docs/evidence/PACKAGE-0090-G3F-4-EVIDENCE-BINDING-FINGERPRINT-RUNTIME.json | 12209 | `ec46ab8b9c62f6964e1fa1968f25d6954dcd22493567c6186fab7038aefc52cc` |
| docs/evidence/PACKAGE-0090-G3F-4-EVIDENCE-BINDING-REPRODUCIBILITY.json | 1116256 | `c42a1161499b669f3364c41697371b9fd02e185c54044bcac5f1fb405a236d8b` |
| docs/evidence/PACKAGE-0090-G3F-4-FINAL-ATOMIC-CEREMONY-GRAPH.json | 15041440 | `70a7e45bd3e3a03e022b692178386615cd3f36b5489b372bac086a33ea56d467` |
| docs/evidence/PACKAGE-0090-G3F-4-FINAL-CEREMONY-FAILURE-MATRIX.json | 20538 | `9260d6410f277d887738d419a0d72320881b441d29d6863c84c62352f27a6668` |
| docs/evidence/PACKAGE-0090-G3F-4-FINAL-CEREMONY-RECOVERY-CLOSURE.md | 51262 | `281fc2d1cb0f4c929d6b421bae9a4a408f9441aa5b48d6aa21b1d2cc1af74518` |
| docs/evidence/PACKAGE-0090-G3F-4-FINAL-CEREMONY-TIME-CONTRACT-CLOSURE.md | 75203 | `4bafa0b9575ce6342b909c719acaa50a06df92cd916a8fa4059166145f70085f` |
| docs/evidence/PACKAGE-0090-G3F-4-FINAL-HEADER-40-FIELD-MATRIX.json | 40300 | `6c09b93703c84c70416dd077aa8391ef96ed317fe2d422d4b4de27fa12d5324f` |
| docs/evidence/PACKAGE-0090-G3F-4-FINAL-REHEARSAL.md | 5020 | `050f5e8f377d3737115a6ca2cc8f0025befdc1f9ceb5e2de4745a8551fdc5d88` |
| docs/evidence/PACKAGE-0090-G3F-4-FIXTURE-002.json | 6533 | `55dd5e816a714987710447ca3ae40d2294d2d8f8a2baa63c26e39ff855a4fcef` |
| docs/evidence/PACKAGE-0090-G3F-4-GOVERNED-ECONOMIC-EVIDENCE.json | 60074 | `fe769ded569a40feea1b04eb856c8c0ae99dc98c81788286d7f6d63676a1b5b6` |
| docs/evidence/PACKAGE-0090-G3F-4-HEARTBEAT-MODEL-REVIEW.md | 7579 | `bd8b75c55bd379b61d6ad1dee0f55691248213dab642005fca2be4450e5bf7fc` |
| docs/evidence/PACKAGE-0090-G3F-4-HISTORICAL-ATTESTATION-REUSE-MATRIX.json | 68827 | `bced0e65443678fa9c89ee923de52b48d7e830f131005d2e6fc0fb9cc39b90ba` |
| docs/evidence/PACKAGE-0090-G3F-4-IDENTITY-SIGNAL-CLOSURE.md | 13495 | `57b6fb92b71c2bff1910cd745ba7bc9dc935e4f072e96c6ec77d1ee1b744100c` |
| docs/evidence/PACKAGE-0090-G3F-4-IDENTITY-SIGNAL-REVIEW.json | 17783 | `1b159acadfb3f86b63d20f46ae50267ef42da7c0b7a8ccdcffc17f0c7cdad010` |
| docs/evidence/PACKAGE-0090-G3F-4-IDENTITY-SIGNAL-RUNTIME.json | 642341 | `f0067665ae37d4e4a56c98604a7e7f72465cc0b4b386a6436ce5b0934373e0b6` |
| docs/evidence/PACKAGE-0090-G3F-4-INSTALLED-ACL.json | 221850 | `709ff68e0b56cf0b48817de326656ae07ddcc25d8b46d4eb8c1f83518a65b662` |
| docs/evidence/PACKAGE-0090-G3F-4-INSTALLED-CATALOG.json | 142870 | `fc1fbd866c984e76da3d7c7c256894de7f8b94898130e11f10b78976d048b715` |
| docs/evidence/PACKAGE-0090-G3F-4-ISOLATED-POSTGRES18-REHEARSAL.md | 8154 | `7fd17925b2eb7125b012a3f8d83e367fd8dfb351bd9e140dadbf1667e8e26b2f` |
| docs/evidence/PACKAGE-0090-G3F-4-LOGIN-EVENT-ENROLLMENT-RUNTIME.json | 5262 | `7ceadd1ee9100c485d9397ff300c2de5a78af7c24399472b016fcb6b18b8c949` |
| docs/evidence/PACKAGE-0090-G3F-4-ORIGINAL-ATTESTATION-CONTEXT-CLOSURE.md | 38443 | `4efaff86af2bf81b0ba1045bedbb1a1903686bd3c243a5341e096d37013a1787` |
| docs/evidence/PACKAGE-0090-G3F-4-ORIGINAL-ATTESTATION-CONTEXT-MATRIX.json | 1119900 | `dc31510de3abc5271292e370e6dc5ed5e243cb47c9f97fa649300e1564f09e42` |
| docs/evidence/PACKAGE-0090-G3F-4-ORPHAN-SIGNER-RECOVERY.json | 19704 | `aeff2a66622e9c9aa15f0eaac8fde81ebb1a45af926da74e32f2e62c9916c7a5` |
| docs/evidence/PACKAGE-0090-G3F-4-PLAN-IDENTITY-ALLOCATION-CONTRACT.json | 18588 | `c7bbbef6a549dcff8a003569b7ef4ea681af3ab222304ee93f541557d7e8685f` |
| docs/evidence/PACKAGE-0090-G3F-4-PLAN-REPLAY-IDEMPOTENCY-MATRIX.json | 7375 | `5747dcd1b52019ec4ebc0a5e4401cb4e17d89851ba7843af13ba5d7719acd7b6` |
| docs/evidence/PACKAGE-0090-G3F-4-POSITIVE-READINESS.json | 2559 | `7fda92880398e112f9263aead8211e24e9af68e4eae24ca1b7d127f39ff8b0f2` |
| docs/evidence/PACKAGE-0090-G3F-4-POST-REVOCATION-EVIDENCE-PROOF.json | 7829 | `0ad1308925f4f6f22f02a1ad6f6d9454639f238bfbf2cfa9aa18840c2360aa19` |
| docs/evidence/PACKAGE-0090-G3F-4-PREREQUISITE-NEGATIVE-MATRIX.json | 10093 | `81f4ac478a0907faa744a798d40eba3ab38546091702e66bf5da848de30e096a` |
| docs/evidence/PACKAGE-0090-G3F-4-PREREQUISITE-PROVISIONING-MATRIX.json | 15277 | `aa16c0678b3162692b2e81cead6d9e01f7dfa191cbd9d487b8f89384b7edbd0a` |
| docs/evidence/PACKAGE-0090-G3F-4-RECOVERY-2.json | 1896 | `7667c937530c1a833ac626a6b33a305a36bb08934aa5eda27cb7bb7640c6ad66` |
| docs/evidence/PACKAGE-0090-G3F-4-REHEARSAL-BINDING-AUTHORIZATION.json | 4399 | `e869dcff6562ed0ce2410efab90bdf6273821da63c37853f0bbffec4ee82e48c` |
| docs/evidence/PACKAGE-0090-G3F-4-REHEARSAL-BINDING-PROVISIONING.json | 17540151 | `75abf244535a33e2fd35a7ef373659f146dafc07fa7274bb2d78bc2170e1ad55` |
| docs/evidence/PACKAGE-0090-G3F-4-REHEARSAL-DEPLOYMENT-APPROVAL.json | 5043 | `84a0afd98f68a25c360e7b3e2056e92c9c9d945f364bf9d8931a730908d752de` |
| docs/evidence/PACKAGE-0090-G3F-4-REHEARSAL-DOMAIN-ALLOCATION.json | 5491 | `6402750ec87ba8a894d590502eebd32e19769d566614cd854c808e9b9f41a313` |
| docs/evidence/PACKAGE-0090-G3F-4-REHEARSAL-DOMAIN-AUTHORITY-CLOSURE.md | 18816 | `5ed65ebbd0e84b93b82573d9465e85b3b75bb383b62ecf5e32c897a1fcb42fe2` |
| docs/evidence/PACKAGE-0090-G3F-4-REHEARSAL-SECRET-RESIDUE-SCAN.json | 2359 | `006d46adc2ab0e2282f04f9c33200ffc2fabe002afd6e5f09bbb5341cc2a7848` |
| docs/evidence/PACKAGE-0090-G3F-4-REHEARSAL-SIGNED-DOMAIN.json | 58467 | `ea0c0b15e6d371f88f807d0e2635ec8a2e337fa94f370670ee429823ca7ba4c1` |
| docs/evidence/PACKAGE-0090-G3F-4-REHEARSAL-SOURCE-STORAGE-AUTHORITY-CLOSURE.md | 9439 | `ab02a2d15915695593edddde518a0773b12edc7e77d95a88ee7f78743dd45a69` |
| docs/evidence/PACKAGE-0090-G3F-4-RR-SNAPSHOT-PLACEMENT.json | 1230986 | `6045826ac91e866c20edc8634a5b4d126cac1adc04c03952f0c96c1e54412802` |
| docs/evidence/PACKAGE-0090-G3F-4-RUNTIME-TESTS.json | 76873 | `1da479d9bca30260552346f20daa7a215b71423faa5ba2c86bf184e54a6372d0` |
| docs/evidence/PACKAGE-0090-G3F-4-SIGNED-ATTESTATION-VERIFICATION.json | 28491 | `0cd7c0a1a8d91c64d00ededf533f9c04b79aa67dbe31fefb9aa6854aff76fce2` |
| docs/evidence/PACKAGE-0090-G3F-4-SIGNED-DOMAIN-MATRIX.json | 41164 | `f1b89f4b5a89d4c0794de5460c3aa8f4cf6be44fa3ddc201670dd54b7e7e37a1` |
| docs/evidence/PACKAGE-0090-G3F-4-SIGNER-AUTHORITY-REGISTRATION.json | 1110601 | `9ceca53f1a099da6d68c0d8254e5add03674c8fe299d434819bca8ecdb8e7f19` |
| docs/evidence/PACKAGE-0090-G3F-4-SIGNER-KEY-AUTHORITY-MATRIX.json | 1091512 | `609b6b69b8fd68c1fc7eb8ecb6fe3408adbb126c99fde68868c9db8a845f8b5b` |
| docs/evidence/PACKAGE-0090-G3F-4-SIGNER-KEY-REGISTRATION.json | 28842 | `f82b3df65ffa02c121b7f4100e1e0a9bb55dbd4e759305fffd305f3ce2a515cc` |
| docs/evidence/PACKAGE-0090-G3F-4-SIGNING-CEREMONY-AUTHORITY-CLOSURE.md | 16499 | `a13cad70eefd2c1267c53cdb7d042955ea0edd902e56872f57477e87ceb5d0bd` |
| docs/evidence/PACKAGE-0090-G3F-4-SIGNING-CEREMONY-CAPABILITY-MATRIX.json | 159332 | `ee3c7024451f0bfddbbac66221021b11ad565f27d4b8ed32f90fda7cda89177d` |
| docs/evidence/PACKAGE-0090-G3F-4-SIGNING-CEREMONY-RESIDUE-SCAN.json | 29473 | `fa6cc39d260037383bc207d2e980659fc0a8ed7aebe340db821b0931c0afc10e` |
| docs/evidence/PACKAGE-0090-G3F-4-TC-R01-PROTECTED-MATERIAL-PROJECTION-REMEDIATION.md | 80317 | `ebe3b97de6a40b48437ebbe3badd41a43a9f8ec4bf36de9fdf865da8f3b9060f` |
| docs/evidence/PACKAGE-0090-G3F-4-TEMPORAL-BOUNDS-REVIEW.md | 6351 | `026aaaad878ecb8ff9ecdb46ffd73b210108300df658dc5f2eb0c9b6e80be4f6` |
| docs/evidence/PACKAGE-0090-G3F-4-TIMING-08006-DIAGNOSIS.md | 9623 | `08b91488bbc8e9b8030cb3f16224bbae15e03409745249096bf45295cee14862` |
| docs/evidence/PACKAGE-0090-G3F-4-TIMING-PHASES.json | 44080725 | `934a01c237140e781e98aba0bea205f8902bbda6b0bea49453dbb8ca6a1b575a` |
| docs/evidence/PACKAGE-0090-G3F-4-TIMING-QUALIFICATION-2.json | 1090465 | `998e4b3930fbb9b44c7d07c2c1eaeb5f63e1972068469adefbe54349662a17ea` |
| docs/evidence/PACKAGE-0090-G3F-4-TIMING-QUALIFICATION.md | 10695 | `c30c60f340b2c779fefe4bbc17e0294bfb42f13c77a82c0afa6b64196717d65b` |
| docs/evidence/PACKAGE-0090-G3F-4-TIMING-SAMPLES.json | 526553 | `e6415ef00764e10a030d1d74ff667870605210a4e1f4a06463bc233707daf15e` |
| docs/evidence/PACKAGE-0090-G3F-4-TRANSPORT-MODEL-REVIEW.md | 13792 | `d8488c63390f3c29c9775c8f402e318fd6eab35416a9d0371a9d52f28275f192` |
| docs/evidence/PACKAGE-0090-G3F-4-WATCHDOG-AUTHORITY-REVIEW.json | 692996 | `b5165e1199147939336654739261389a47e96a42d6385eb8598cefe5be5a2baa` |
| docs/evidence/PACKAGE-0090-G3F-4-WATCHDOG-DEPLOYMENT-CLOSURE.md | 16917 | `858f26755b1d81043f38e96f62c6672ed816f51287571f6c4860cd4b6eb385cb` |
| docs/evidence/PACKAGE-0090-G3F-4-WATCHDOG-FAILURE-MATRIX.json | 11294 | `4e4b90dc0aaf552449098fdb179807dfa05550a89c11279524f96caf70ca228b` |
| docs/evidence/PACKAGE-0090-G3F-4-WATCHDOG-RUNTIME.json | 8154 | `97eb1391c509b33a6ce1c902b6b73cd67c399d6c6fc22754942ab217145930e8` |
| docs/evidence/PACKAGE-0090-G3F-4-WATCHDOG-VISIBILITY.json | 18895509 | `397fced6ced8063d537d75429ec75cf79c4125931db5a5bf4645f0c3a14fb145` |
| docs/evidence/PACKAGE-0090-GOVERNED-ROLE-RECOGNITION-MATRIX.json | 14236 | `f1c41a79dad696da214b97f7fb654f0a360bc5a49f2cecfb7862ba63ddaeb354` |
| docs/evidence/PACKAGE-0090-H02-ADAPTER-SCOPE.md | 8863 | `efd9b654f431a4c270070837f657067f5d5f0efb74f9b393ce3474963a102a12` |
| docs/evidence/PACKAGE-0090-H02-ADAPTER-TEST-RESULTS.json | 3862 | `4bb0027e8f967649264887d06f74ecadbd0874cd3dd24f8b5d2de3038f15a4da` |
| docs/evidence/PACKAGE-0090-H02-CLOSURE.json | 1515 | `e35aaea61c683b1de65c6058b2281108fcb682b82bc6996a9027cb2779b5c41a` |
| docs/evidence/PACKAGE-0090-H02-FULL-OFFLINE-TESTS.txt | 27316 | `80a16772cbd0fd245d4ed63403f08dd698e6039cb81a5374d5e75f3705750242` |
| docs/evidence/PACKAGE-0090-H02-G3F4-HANDOFF.md | 2307 | `3b5c386b1488db2f3f451273b10866caa80d4f11a504fa15eac7805ae31762ef` |
| docs/evidence/PACKAGE-0090-H02-INDEPENDENT-ADAPTER-REVIEW.json | 1426 | `60bfbec29558c8fc7e7258cb6e0efba1045b42f054d9afee678d4a7f20bdc7ea` |
| docs/evidence/PACKAGE-0090-H02-INDEPENDENT-SQL-REVIEW.json | 505867 | `39a891e38abe205f46c8fa7418277d1e1042c87de27d2cc2d11f7bca0479f981` |
| docs/evidence/PACKAGE-0090-INDEPENDENT-G3F-3B-SECURITY-REVIEW.json | 9378 | `d15fe89cf666d64edd62f712d4981eb6388a97e0b54da085fd04612ec6f93c71` |
| docs/evidence/PACKAGE-0090-INDEPENDENT-G3F-3B-SECURITY-REVIEW.md | 25654 | `f8d16c117da7e217c8bbf6f7a9e73ad585f55535a2ddecbe93df26c78a9a7429` |
| docs/evidence/PACKAGE-0090-INDEPENDENT-MUTATION-REVIEW.json | 2958 | `516a820d7dc0ba1f7b4e1303beddbeac6fa80ea58b74f2f9cfb29bc3cd38b80d` |
| docs/evidence/PACKAGE-0090-INDEPENDENT-NATIVE-REVIEW.json | 31171 | `95572ab1715a8c9dbea4cc98b61c1e158cc829ec8faff410dfbc75c4c4e7a439` |
| docs/evidence/PACKAGE-0090-INDEPENDENT-ORIGINAL-INPUT-REVIEW.json | 3675 | `7acd0fe26b853a086f03faa4c665508edcc92cd69bf2640e560460aeb57700e6` |
| docs/evidence/PACKAGE-0090-INDEPENDENT-SOURCE-REVIEW.json | 470357 | `29ae7bd4a7590e83b332829135f910fccda52e8990c23eca2cc17e2ed7f9dd52` |
| docs/evidence/PACKAGE-0090-INDEPENDENT-TEST-INVENTORY.json | 2740 | `21ff81a9ed01491fee3c765dd0eee2300688c911bdb84ac6c5c069622b49e88d` |
| docs/evidence/PACKAGE-0090-ISSUER-DELIVERY-ACK-AUTHORITY.json | 4206 | `e7c6ddaff433cd49a485ba1f6672f3e1acc069745c6d6071718970e71613604e` |
| docs/evidence/PACKAGE-0090-LOGIN-EVENT-BINDING-RUNTIME.json | 12874 | `b7767cc2139c4b6b2cdb87252a3ae61ff21bbbfbec416d7c124fa62daa569c1f` |
| docs/evidence/PACKAGE-0090-MUTATION-ORIGINAL-INPUT-AUTHORITY.json | 2013 | `bbc19ac21dabbb7fe01f8b4b5a36d0c2d9eecc1624c2ad07c6ac8e309592e0bd` |
| docs/evidence/PACKAGE-0090-MUTATION-ORIGINAL-INPUT-AUTHORITY.md | 1681 | `9c37ee42cf8a8660184a6ca77b28875dba059b666550d19a8c6af89a4b8dd64c` |
| docs/evidence/PACKAGE-0090-MUTATION-ORIGINAL-MATCH-REVIEW.json | 1347 | `5e1e9c662efcf1704d5556be8a81e47ed06bae41e8b88be3ede7a15478ad8586` |
| docs/evidence/PACKAGE-0090-PHASE-A-CLOSURE.json | 939 | `36983e944e2f7bc56dc51c7f7b4b6ca6d9a77a4886d2eb25b5bbb28e36e2871e` |
| docs/evidence/PACKAGE-0090-PHASE-A-FULL-TESTS.txt | 26339 | `88ec2118db9feea0ff9163a9448e897271a343b0ac451a3dc6ee99881132875c` |
| docs/evidence/PACKAGE-0090-S02-EXPECTED-ATTESTATION-AUTHORITY.json | 3740 | `67c63d386aff18660289c340351857f6bdf1e598f7592df0e16e8b5d3e054851` |
| docs/evidence/PACKAGE-0090-S02-EXPECTED-ATTESTATION-AUTHORITY.md | 7466 | `0008fd06ced70d6c2b485da308a32eba1fb1cc745d0171d7cbe58f6a40917f10` |
| docs/evidence/PACKAGE-0090-S02-ISOLATED-PREDICATE-REVIEW.json | 2014 | `90cf5c3bd99ebad7ed51890c6fe3db4863e59fc386df938017abb6b624720855` |
| docs/evidence/PACKAGE-0090-S02-ORIGINAL-INPUT-CLOSURE.md | 3401 | `f2cea24b34c3d1db628fc662cf13aaf54ac0f1279ff600972edc91bf01ad88ed` |
| docs/evidence/PACKAGE-0090-S02-ORIGINAL-INPUT-GOLDENS.json | 11726 | `56c71b6a2834158718bea4cc8652ee6971087a37dc8501d8a7aac9ce35e22d22` |
| docs/evidence/PACKAGE-0090-S03-SOURCE-REVIEW.md | 2166 | `605b2af3f44aa6d2fbd6ee2cdf2c8c7e1042d278a55816a18ec686b3b72d5a9d` |
| docs/evidence/PACKAGE-0090-S05-S06-ISOLATED-REVIEW.json | 859 | `11dad47242f12a6074167da45b8127e69815f8c1f9482f1dc9e151998e709ef2` |
| docs/evidence/PACKAGE-0090-S05-S06-TRANSPORT-GOLDENS.json | 11902 | `3a8b2cda92514064f712c4e4f71bcb1773c519eaca8b30740547a827174afb50` |
| docs/evidence/PACKAGE-0090-S05-S12-SOURCE-REVIEW.md | 2226 | `d11abb145d1082c6f973c0cb6fa3e5b6c73375055a0b39fa5c3353643be00785` |
| docs/evidence/PACKAGE-0090-S07-S18-ISOLATED-REVIEW.json | 2180 | `9800d386c58099026f48cd15cdec4dd148b43be5ff6dfe27eba7ebffeff183c4` |
| docs/evidence/PACKAGE-0090-S07-S18-TRANSPORT-GOLDENS.json | 52734 | `eb8eba300cc73a41d1e17f9093a5f264ba886813a4013e792d4d80116c55f754` |
| docs/evidence/PACKAGE-0090-S13-S18-SOURCE-REVIEW.md | 3676 | `83673b94b7e8900d5a8b1ff069b342341136dfe2af2b9af7c1886675367533b0` |
| docs/evidence/PACKAGE-0090-SELF-ENROLLED-ANCHOR-PROOF.md | 16705 | `e45122541346e7ab1a872a54f6e5290af0823b38a7b11bbdbe8e6b47b4891431` |
| docs/evidence/PACKAGE-0090-SELF-ENROLLED-ANCHOR-REVIEW.json | 25565 | `9bff9f1f1f0ee845652aac1d02261511b1956d354b29095c2055aadb27cdde63` |
| docs/evidence/PACKAGE-0090-SELF-ENROLLED-ANCHOR-RUNTIME.json | 578932 | `d7cd3aa05e5bb0ea184596c4d2236e817048b413bd6ece554b02c7477944462b` |
| docs/evidence/PACKAGE-0090-SOURCE-COMPOSITION-CLOSURE.json | 1663 | `01291f864f1e4dfd3a2852b647aec018d6ed5fd986af5966474d101bc1615388` |
| docs/evidence/PACKAGE-0090-V-BRIDGE-CAPABILITY-INVENTORY.json | 34264 | `b010edcaf2d98cfae596176619355dce7344be9aa7b2bda39927edaf257265c8` |

## Source validation pins

```json
{
  "DB_AUTHORITY": {
    "path": "docs/specifications/SPEC-0090-governed-offline-field-proof-exclusive-capability-composition.md",
    "line": 239,
    "sha256": "d12acc86cbed8d56cd774f427b79dce26258a36ac65a7d78bf2cb1fb37fd9a92",
    "result": "PASS_SOURCE"
  },
  "HALF_OPEN_MUTATION": {
    "path": "docs/specifications/SPEC-0090-governed-offline-field-proof-exclusive-capability-composition.md",
    "line": 60,
    "sha256": "d12acc86cbed8d56cd774f427b79dce26258a36ac65a7d78bf2cb1fb37fd9a92",
    "result": "PASS_SOURCE"
  },
  "WRITE_NOT_VISIBILITY": {
    "path": "docs/specifications/SPEC-0090-governed-offline-field-proof-exclusive-capability-composition.md",
    "line": 60,
    "sha256": "d12acc86cbed8d56cd774f427b79dce26258a36ac65a7d78bf2cb1fb37fd9a92",
    "result": "PASS_SOURCE"
  },
  "NO_REFRESH": {
    "path": "docs/specifications/SPEC-0090-governed-offline-field-proof-exclusive-capability-composition.md",
    "line": 235,
    "sha256": "d12acc86cbed8d56cd774f427b79dce26258a36ac65a7d78bf2cb1fb37fd9a92",
    "result": "PASS_SOURCE"
  },
  "JVM_NOT_AUTHORITY": {
    "path": "docs/specifications/SPEC-0090-governed-offline-field-proof-exclusive-capability-composition.md",
    "line": 247,
    "sha256": "d12acc86cbed8d56cd774f427b79dce26258a36ac65a7d78bf2cb1fb37fd9a92",
    "result": "PASS_SOURCE"
  },
  "READ_IGNORES_MUTATION_EXPIRY": {
    "path": "docs/specifications/SPEC-0090-governed-offline-field-proof-exclusive-capability-composition.md",
    "line": 58,
    "sha256": "d12acc86cbed8d56cd774f427b79dce26258a36ac65a7d78bf2cb1fb37fd9a92",
    "result": "PASS_SOURCE"
  },
  "ADR_VISIBILITY": {
    "path": "docs/adr/ADR-0090-governed-offline-field-proof-exclusive-capability-composition.md",
    "line": 81,
    "sha256": "e1c26d2f202684d5ace54408c83a0fcf100085864270f0c32cb077b9398566a9",
    "result": "PASS_SOURCE"
  },
  "V041_HALF_OPEN": {
    "path": "applications/marketplace-operations-persistence-postgres/src/main/resources/db/migration/V041__create_s2a_accepted_attestation.sql",
    "line": 197,
    "sha256": "3ff1421dd56de17270a9c44054055c0c1afc91f855d903697268088a53f1182d",
    "result": "PASS_SOURCE"
  },
  "V041_EXISTING_VERIFIED_AT": {
    "path": "applications/marketplace-operations-persistence-postgres/src/main/resources/db/migration/V041__create_s2a_accepted_attestation.sql",
    "line": 135,
    "sha256": "3ff1421dd56de17270a9c44054055c0c1afc91f855d903697268088a53f1182d",
    "result": "PASS_SOURCE"
  },
  "V041_NEW_TRANSACTION_BASIS": {
    "path": "applications/marketplace-operations-persistence-postgres/src/main/resources/db/migration/V041__create_s2a_accepted_attestation.sql",
    "line": 157,
    "sha256": "3ff1421dd56de17270a9c44054055c0c1afc91f855d903697268088a53f1182d",
    "result": "PASS_SOURCE"
  },
  "SIGNED_ENDPOINTS": {
    "path": "applications/marketplace-operations/src/main/kotlin/io/flooow/marketplace/operations/authorization/ApprovalAttestationCanonicalCodec.kt",
    "line": 31,
    "sha256": "74763cd4b0c3ab49b3f2c882f724df3ec10561f9aaa452c7b29fd1d6a943b26d",
    "result": "PASS_SOURCE"
  },
  "SIGNATURE_PREIMAGE": {
    "path": "applications/marketplace-operations/src/main/kotlin/io/flooow/marketplace/operations/authorization/ApprovalAttestationCanonicalCodec.kt",
    "line": 80,
    "sha256": "74763cd4b0c3ab49b3f2c882f724df3ec10561f9aaa452c7b29fd1d6a943b26d",
    "result": "PASS_SOURCE"
  },
  "SIX_FRACTION_UTC": {
    "path": "applications/marketplace-operations/src/main/kotlin/io/flooow/marketplace/operations/authorization/ApprovalAttestationCanonicalCodec.kt",
    "line": 194,
    "sha256": "74763cd4b0c3ab49b3f2c882f724df3ec10561f9aaa452c7b29fd1d6a943b26d",
    "result": "PASS_SOURCE"
  },
  "STRICT_CANONICAL_ROUNDTRIP": {
    "path": "applications/marketplace-operations/src/main/kotlin/io/flooow/marketplace/operations/authorization/ApprovalAttestationCanonicalCodec.kt",
    "line": 68,
    "sha256": "74763cd4b0c3ab49b3f2c882f724df3ec10561f9aaa452c7b29fd1d6a943b26d",
    "result": "PASS_SOURCE"
  },
  "MICROSECOND_REJECTION": {
    "path": "applications/marketplace-operations/src/main/kotlin/io/flooow/marketplace/operations/authorization/ApprovalGovernance.kt",
    "line": 199,
    "sha256": "bb71114ceb00501499adefe1ce3a1418cdb2a0e36d71fdf5f44fa54773a246dc",
    "result": "PASS_SOURCE"
  },
  "FENCE": {
    "path": "applications/marketplace-operations-persistence-postgres/src/main/resources/db/migration/V043__create_governed_offline_field_proof_capability_composition.sql",
    "line": 16,
    "sha256": "3301b254e883ae2ebf9e1d41036f15bc7839c1ae9e2404e692bc2ec864204109",
    "result": "PASS_SOURCE"
  },
  "INITIAL_NOT_V041_ACCEPTANCE": {
    "path": "docs/evidence/PACKAGE-0090-G3F-4-FINAL-CEREMONY-RECOVERY-CLOSURE.md",
    "line": 7,
    "sha256": "281fc2d1cb0f4c929d6b421bae9a4a408f9441aa5b48d6aa21b1d2cc1af74518",
    "result": "PASS_SOURCE"
  },
  "ONE_T_REG": {
    "path": "docs/evidence/PACKAGE-0090-G3F-4-FINAL-CEREMONY-RECOVERY-CLOSURE.md",
    "line": 7,
    "sha256": "281fc2d1cb0f4c929d6b421bae9a4a408f9441aa5b48d6aa21b1d2cc1af74518",
    "result": "PASS_SOURCE"
  },
  "TC_R01_CLOSED": {
    "path": "docs/evidence/PACKAGE-0090-G3F-4-TC-R01-PROTECTED-MATERIAL-PROJECTION-REMEDIATION.md",
    "line": 3,
    "sha256": "ebe3b97de6a40b48437ebbe3badd41a43a9f8ec4bf36de9fdf865da8f3b9060f",
    "result": "PASS_SOURCE"
  },
  "REPLACEMENT_NO_PUBLIC_PROTECTED": {
    "path": "docs/evidence/PACKAGE-0090-G3F-4-TC-R01-PROTECTED-MATERIAL-PROJECTION-REMEDIATION.md",
    "line": 15,
    "sha256": "ebe3b97de6a40b48437ebbe3badd41a43a9f8ec4bf36de9fdf865da8f3b9060f",
    "result": "PASS_SOURCE"
  }
}
```
