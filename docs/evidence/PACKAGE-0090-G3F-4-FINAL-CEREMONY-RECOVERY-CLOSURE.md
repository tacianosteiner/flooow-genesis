# Package 0090 G3F.4 - final ceremony recovery closure

FINAL_CEREMONY_RECOVERY_CLOSURE=PASS (bounded design). G3F_4=HOLD; WATCHDOG_DEPLOYMENT_HIGH and G3F4_H01 remain OPEN; B0/H2/M0/L0.

Reviewed branch `checkpoint/package-0090-cloud-handoff`, local/fetched baseline `05fc44e474aa3a3ad1a461912d56b0196e7150d0`, clean before this gate. This gate creates only the four requested evidence files. No UUID, key, signature, SQL write, recovery write, container start, fixture, timing-bound change or readiness/admission transition occurs.

The selected future registration uses one actual trusted ADMIN connection and one T_REG COMMIT for two canonical V040 public governance rows and all nine required V043 rows. Local signature verification uses public planned SPKI and exact approved canonical inputs; it is not V041 accepted-attestation verification. The expected-original table has no dependency on a durable accepted attestation. Separate convenience-adapter key/authority commits are eliminated by this design, rather than mislabeled as atomic.

DURABLE_COMMIT_BOUNDARY_COUNT=2 across A-G: one T_REG registration boundary, then one eventual T_CLOSE terminal governance boundary. Only ONE is required before positive binding-registration acknowledgment. T_CLOSE cannot be merged with registration while later independently authorized V041/V042 mutations need ACTIVE/ENABLED governance. Those later operational commits have their own gates/receipts and are outside this registration-only count; they must be proven terminal before cleanup. A known precommit abort has zero root mutation commits. The old convenience-adapter path has three registration commits (key, authority, binding), plus terminal closure; it is analyzed as a legacy/deviation path only.

C3/C4 are unreachable independent commits in selected T_REG but explicitly covered as legacy orphan states. C8 is the actual T_REG BEGIN at C, before key generation; F reuses that connection/transaction and has no second BEGIN. User crash labels are preserved, with selected order C0,C1,C8,C2,C5,C6,C7,C9-C14,C16. C15 excess private-key custody is eliminated by destruction at E, but its defensive crash behavior remains covered. No runtime crash experiment or complete ceremony composer was implemented/qualified here.

| Phase | Durable write | Signer secret | Retry/authority | Commit |
| --- | --- | --- | --- | --- |
| A Preflight validation | NO | NO signer private key | Read-only validation; STOP until time/window/watchdog and complete inputs separately close; NONE | NONE |
| B Final identity allocation | NO DB write; existing nonsecret immutable ceremony-input custody | NO signer private key | Never regenerate a subset. Before effects only an exact still-running preparation can retain the entire root. Failed preparation is abandoned before a new complete set.; NONE; reservations do not issue credentials or grants | NONE |
| C Ephemeral signer preparation and staged canonical governance | Two uncommitted V040 public rows inside T_REG only | One process-local signer private key until E; public SPKI/lineage only in DB | Abort uncommitted root as a unit; any possibly committed write requires authoritative query; ACTIVE key + ENABLED bounded authority staged; become durable only with entire registration | T_REG shared with F; no C-only commit |
| D Manifest materialization | NO additional durable effect; T_REG remains open | Signer private key in memory | Abort/fresh entire root; no timestamp substitution or renewal; NONE | NONE |
| E One signature and independent local verification | NO additional DB effect; retain public original only in existing ceremony-input context | Signer private key through single SIGN; destroy before F after local verification completes | Failed ceremony signature reuse DENY. Public verification/reconciliation needs no private key.; NONE; local JCA validity is not V041 acceptance | NONE |
| F Complete registration and one atomic commit | Exactly 11 newly staged rows: 2 V040 + 9 V043 | NO signer private key; separate governed ADMIN preflight-HMAC key domain remains subject to its existing custody contract | COMMIT outcome unknown -> QUERY_FIRST. Exact committed root -> return exact existing state. Confirmed rollback -> abandon/fresh.; T_REG makes bounded public signer governance and REGISTERED non-operational binding durable together; no command authority or admission | T_REG: ONE |
| G Post-commit reconciliation and terminal governance closure | T_CLOSE: one existing-governance append transaction only at independently proven terminal event | NO signer private key; normal continuation already destroyed it at E | QUERY_FIRST on every unknown T_CLOSE outcome; already exact DISABLED/RETIRED -> no-op; DISABLED successor then RETIRED key successor; never reactivate or rewrite history | T_CLOSE: ONE conditional/later boundary, separate from registration |

Exact phase operations, commit objects, source checks and all 26 public query templates are in [ambiguous-commit recovery](PACKAGE-0090-G3F-4-AMBIGUOUS-COMMIT-RECOVERY.json). All templates are unexecuted, parameter-bound review artifacts; the composed SELECT uses one fresh snapshot after canonical lock acquisition and original-writer quiescence. No time guess or pre-lock stale snapshot establishes absence. Secret key material and credential verifiers are excluded from projections.

All C0-C16 fields and 18 adversarial scenarios are in [crash-point matrix](PACKAGE-0090-G3F-4-CEREMONY-CRASH-POINT-MATRIX.json). All exact public successor fields, authority, idempotency, custody and cleanup order are in [orphan-signer recovery](PACKAGE-0090-G3F-4-ORPHAN-SIGNER-RECOVERY.json).

Recovery inspects the immutable allocated root, signer lineage, binding/original and all controls/effects. Complete exact registration returns its existing historical state; absent state permits whole-root abandonment only after quiescence and public proof; an exact legacy orphan is disabled then retired before new allocation; a partial/conflicting/unknown state remains HOLD. Missing required controls are not auto-filled. SET CONSTRAINTS alone cannot prove every control row exists: the selected composer must explicitly validate the complete write set before its single COMMIT.

COMMITTED_VALID denotes exact canonical historical registration only. It does not prove elapsed commit timing, window feasibility, V041 acceptance, readiness or command success. The public recovery snapshot includes the actual DB wall clock for effective governance/expiry inspection; it does not choose new timestamps or close the three time contracts. An expired recovered root is denied for fresh effects and is never treated as an absent binding.

Private-key custody ends immediately after local verification (last private operation: one SIGN). Normal cleanup is best-effort destruction/release of mutable buffers; process death ends governed custody. No restart path uses or recovers signer private material. This design does not assert forensic JVM/swap/heap erasure. Public original/signature/SPKI and existing immutable input context are sufficient for exact reconciliation; losing that nonsecret context causes HOLD, never guessed replacement identities.

Existing V040 governance is sufficient for cleanup without a private key. Authority DISABLED successor requires a distinct native signer_authority_id because V040 keys authority records by (organization_id,signer_authority_id); revision increments and supersedes points to the previous ID. This is required existing append-model data, not a recovery attempt UUID or new authority. No such ID is generated here. Key RETIRED revision keeps the same key identity/SPKI/fingerprint/valid_from and must be immediately effective at a proven DB clock time. Preserve both predecessor fingerprints and immutable authority window/scope. Ambiguous cleanup commit is queried before any append.

The chosen T_REG removes signer-only commit orphans. Legacy ACTIVE/ENABLED orphan exposure is real until trusted ADMIN locks and commits terminal cleanup; it is never claimed already neutralized. If accepted/command effects occurred before cleanup, retain them and use existing domain reconciliation; no retroactive undo or fresh root is inferred. V041 historical accepted-proof replay may retain original proof after later retirement, while V042 new effects require current ACTIVE/ENABLED governance. This distinction preserves evidence without granting fresh authority.

A positive binding commit does not permit immediate retirement when later authorized verification/consumption is planned. The earliest successful-path event is the final authorized decision/head/admission-consumption COMMIT with all new effects finished; a proven terminal abort/expiry/abandonment is the alternative. Existing ADMIN must reconcile/neutralize outstanding roots on normal completion, restart and before another preparation/admission. Finite window expiry denies future effects but is not evidence that retirement/disable was appended. No automatic scheduler or bounded cleanup latency is promised.

No timestamp mapping, window extension, fixture installation or watchdog qualification is supplied here. The three header time contracts and signing-window operational review remain prerequisites to a future signing/binding execution. The canonical disk V043 fence is intact, SHA256 `3301b254e883ae2ebf9e1d41036f15bc7839c1ae9e2404e692bc2ec864204109`; V001-V042 and all prior tracked evidence remain byte-identical. Previously installed disposable rehearsal code/state is historical provenance only.

Validation is source/static and deterministic design review: {"UUID_generated": 0, "adversarial_scenarios": 18, "crash_points": 17, "database_connections": 0, "database_writes": 0, "key_authority_eligibility_states": 4, "keys_generated": 0, "kind": "DETERMINISTIC_DESIGN_REVIEW_NOT_RUNTIME", "presence_scope_quiescence_cases": 6144, "prior_artifacts_read_and_preserved": 160, "result": "PASS_DESIGN", "safe_public_queries": 26, "selected_registration_commits": 1, "signatures": 0, "source_contract_checks": 12, "total_registration_plus_terminal_closure_commits": 2, "tracked_baseline_count": 1251}. The finite-state review enumerates all 2^11 row-presence combinations plus wrong-scope/quiescence variants; this is not a PostgreSQL transaction, crash, signing or performance test. Primary source files were read, checked against their prior SHA256 pins, and the existing functions/deferred cycles/verifier semantics inspected. All previous Package 0090 evidence was read and its immutable inventory is below.

Each retained mechanism has a concrete property: same-transaction composition removes signer-only commits; existing immutable public input binds recovery identity; existing transaction locks plus a fresh snapshot remove the absence race; canonical append-only terminal revisions deny fresh effects; external non-authoritative disposition evidence prevents mixed-root retries. No new coordinator, journal, table, column, role, attempt UUID or persisted state machine is needed.

Next gate: `G3F_4_FINAL_CEREMONY_TIME_CONTRACT_CLOSURE`, then `G3F_4_SIGNING_WINDOW_OPERATIONAL_REVIEW`; only after both and all required separate blockers close can a separately authorized `G3F_4_SIGNING_AND_BINDING_ATOMIC_CEREMONY_EXECUTION` occur. This PASS does not authorize it.

Complete requested RETURN (Git fields here describe the immutable reviewed baseline; resulting pushed checkpoint is reported separately):

```text
FINAL_CEREMONY_PHASES=A preflight; B entire identity allocation; C same-T_REG ephemeral/public governance; D manifest; E single sign/local public verification/destruction; F same-T_REG complete registration COMMIT; G query/terminal cleanup at proven end
FINAL_CEREMONY_PHASES_CLOSED=YES
DURABLE_COMMIT_BOUNDARY_COUNT=2
DURABLE_COMMIT_BOUNDARIES_CLOSED=YES
SIGNER_GOVERNANCE_MUST_PRECOMMIT=NO
PRIVATE_KEY_BIRTH_EVENT=After complete authorized A/B, at C inside the one live preparation; one process-local Ed25519 generation only
PRIVATE_KEY_LAST_REQUIRED_EVENT=The single SIGN call on exact canonical manifest preimage; local verification thereafter uses public SPKI only
PRIVATE_KEY_DESTRUCTION_EVENT=Immediately on E verification completion or any exception/abort, in finally, before F commit. C15 is a crash deviation, not permission to extend custody.
RECOVERY_DEPENDS_ON_PRIVATE_KEY_PERSISTENCE=NO
PRIVATE_KEY_RECOVERY_CONTRACT_CLOSED=YES
CRASH_POINT_MATRIX=PACKAGE-0090-G3F-4-CEREMONY-CRASH-POINT-MATRIX.json#C0-C16
POST_DURABLE_FAILURE_RETRY=QUERY_FIRST
AMBIGUOUS_COMMIT_RECOVERY_QUERY_SET=PACKAGE-0090-G3F-4-AMBIGUOUS-COMMIT-RECOVERY.json#Q1-Q26
AMBIGUOUS_COMMIT_RECOVERY_CLOSED=YES
COMMITTED_VALID_PREDICATE=PACKAGE-0090-G3F-4-AMBIGUOUS-COMMIT-RECOVERY.json#P1-P10
PARTIAL_COMMITTED_STATE_POLICY=FAIL_CLOSED_AND_ESCALATE
ORPHAN_SIGNER_KEY_RECOVERY=Query exact locked lineage; if ACTIVE append canonical next RETIRED revision with same key identity/public material/valid_from, immediate effective DB time and predecessor lineage hash; if already RETIRED/REVOKED/COMPROMISED effective now verify denial and no-op. No delete/update/reactivation.
ORPHAN_SIGNER_KEY_RECOVERY_AUTHORITY=EXISTING_TRUSTED_REVIEWED_ADMIN / PLAN_BINDING_ADMIN; existing approval-governance capability for canonical V040 appends
ORPHAN_SIGNER_KEY_RECOVERY_CLOSED=YES
ORPHAN_SIGNER_AUTHORITY_RECOVERY=Query exact locked scope leaf; append canonical next DISABLED successor with distinct native signer_authority_id, previous id as supersedes, revision+1, same institution/role/key/permission/window/source and previous fingerprint. Already DISABLED exact leaf -> verify/no-op.
ORPHAN_SIGNER_AUTHORITY_RECOVERY_AUTHORITY=EXISTING_TRUSTED_REVIEWED_ADMIN / PLAN_BINDING_ADMIN; existing approval-governance capability for canonical V040 appends
ORPHAN_SIGNER_AUTHORITY_RECOVERY_CLOSED=YES
ORPHAN_GOVERNANCE_CLEANUP_ORDER=Authority DISABLED first, key RETIRED second, shared T_CLOSE, then query/verify effective denial and record nonsecret evidence; only then fresh root.
FAILED_CEREMONY_SIGNATURE_REUSE=DENY
PARTIAL_ID_SET_REGENERATION=FORBIDDEN
ALLOCATION_ABANDONMENT_RULE=Existing immutable nonsecret preparation context + original writer quiescence + authoritative absence of all allocated registration/effects + verified terminal orphan governance if any. Document disposition as non-authoritative external evidence; no DB tombstone/table. Missing context or unknown result -> HOLD. A committed root is never abandoned as though absent.
ALLOCATION_ABANDONMENT_AUTHORITY=Existing PLAN_BINDING_ADMIN; existing approval-governance capability for orphan neutralization
PROCESS_CRASH_PRIVATE_KEY_POLICY=KEY_LOST_EXPECTED_FAIL_CLOSED
GOVERNANCE_CLEANUP_REQUIRES_PRIVATE_KEY=NO
WINDOW_EXPIRY_RECOVERY_POLICY=ABORT / QUERY_FIRST if outcome unknown / CLEAN_EXACT_ORPHAN_GOVERNANCE_IF_REQUIRED / PROVE_DISPOSITION / START_FRESH_AUTHORIZED_CEREMONY. Exact committed expired root remains historical success with execution denied; no extension, changed timestamp or stale signature reuse.
WINDOW_EXPIRY_RECOVERY_CLOSED=YES
PRE_DURABLE_FAILURE_RECOVERY=DROP_EPHEMERAL_STATE_AND_RETRY_WITH_FRESH_CEREMONY
POST_SIGNER_PRE_BINDING_RECOVERY=PASS_DESIGN
BINDING_TX_PARTIAL_DURABILITY=IMPOSSIBLE_BY_TRANSACTION_ATOMICITY
COMMITTED_BINDING_REPLAY=RETURN_EXISTING_EXACT_STATE
COMMITTED_BINDING_REPLAY_CLOSED=YES
BOUND_BINDING_DEPENDS_ON_PRIVATE_KEY_AFTER_COMMIT=NO
POST_SUCCESS_SIGNER_RETIREMENT_EARLIEST_EVENT=After the final independently authorized V042 decision/head and V043 admission-consumption effect COMMIT, with all new attestation/issuance/command mutations for this exact root finished; alternatively after independently proven terminal abort/expiry/abandonment with continuation denied.
RECOVERY_CLOSURE_DOES_NOT_CLOSE_WATCHDOG=PASS
RECOVERY_FAILS_CLOSED=PASS
NEW_RECOVERY_AUTHORITY_REQUIRED=NO
NEW_RECOVERY_TABLE_REQUIRED=NO
NEW_RECOVERY_JOURNAL_REQUIRED=NO
NEW_RECOVERY_COLUMN_REQUIRED=NO
UNJUSTIFIED_NEW_MECHANISM_COUNT=0
RECOVERY_ALGORITHM_DETERMINISTIC=YES
RECOVERY_ADVERSARIAL_MATRIX=PASS_DESIGN
EVIDENCE_BEFORE_RECOVERY_CLAIM=PASS
QUERY_FIRST_AFTER_DURABLE_WRITE=PASS
NO_BLIND_RETRY=PASS
NO_PRIVATE_KEY_PERSISTENCE=PASS
NO_SIGNATURE_REUSE_BY_DEFAULT=PASS
NO_IDENTITY_PARTIAL_REGENERATION=PASS
NO_HISTORY_DELETION=PASS
ORPHAN_AUTHORITY_FAIL_CLOSED=PASS
AMBIGUOUS_COMMIT_FAIL_CLOSED=PASS
NO_NEW_RECOVERY_AUTHORITY=PASS
NO_UNJUSTIFIED_RECOVERY_INFRASTRUCTURE=PASS
WATCHDOG_BOUNDARY_PRESERVED=PASS
DNA_REVIEW=PASS
FINAL_CEREMONY_RECOVERY_CLOSURE=PASS
WATCHDOG_DEPLOYMENT_HIGH=OPEN
G3F4_H01=OPEN
BLOCKER_COUNT=0
HIGH_COUNT=2
MEDIUM_COUNT=0
LOW_COUNT=0
LOCAL_HEAD=05fc44e474aa3a3ad1a461912d56b0196e7150d0
REMOTE_HEAD=05fc44e474aa3a3ad1a461912d56b0196e7150d0
LOCAL_EQUALS_REMOTE=YES
WORKTREE=CLEAN_AT_REVIEW_BASELINE
GIT_RETURN_SCOPE=These immutable evidence fields identify the reviewed pre-commit baseline. Actual resulting artifact commit/local-remote equality/clean state must be reported after push+fetch, outside this self-contained record; no self-hash claim.
NEXT_GATE=G3F_4_FINAL_CEREMONY_TIME_CONTRACT_CLOSURE
```

Primary source pins:

| Source | SHA256 |
| --- | --- |
| [docs/specifications/SPEC-0090-governed-offline-field-proof-exclusive-capability-composition.md](../../docs/specifications/SPEC-0090-governed-offline-field-proof-exclusive-capability-composition.md) | `d12acc86cbed8d56cd774f427b79dce26258a36ac65a7d78bf2cb1fb37fd9a92` |
| [applications/marketplace-operations-persistence-postgres/src/main/resources/db/migration/V043__create_governed_offline_field_proof_capability_composition.sql](../../applications/marketplace-operations-persistence-postgres/src/main/resources/db/migration/V043__create_governed_offline_field_proof_capability_composition.sql) | `3301b254e883ae2ebf9e1d41036f15bc7839c1ae9e2404e692bc2ec864204109` |
| [applications/command-authority-ceremony/src/main/kotlin/io/flooow/ceremony/OfflineFieldProofExecutionPlan.kt](../../applications/command-authority-ceremony/src/main/kotlin/io/flooow/ceremony/OfflineFieldProofExecutionPlan.kt) | `e1abfb285e59bd3d5926ecb0e9be1fd21a9eef363ef478120cb0fc40908dcd80` |
| [applications/marketplace-operations/src/main/kotlin/io/flooow/marketplace/operations/authorization/ApprovalAttestationCanonicalCodec.kt](../../applications/marketplace-operations/src/main/kotlin/io/flooow/marketplace/operations/authorization/ApprovalAttestationCanonicalCodec.kt) | `74763cd4b0c3ab49b3f2c882f724df3ec10561f9aaa452c7b29fd1d6a943b26d` |
| [applications/marketplace-operations-persistence-postgres/src/main/kotlin/io/flooow/marketplace/persistence/postgres/PostgresApprovalGovernance.kt](../../applications/marketplace-operations-persistence-postgres/src/main/kotlin/io/flooow/marketplace/persistence/postgres/PostgresApprovalGovernance.kt) | `442b9fe79b023e0d7a36134d9c7cf717335a5418c249af8ddcc42521ccb3863d` |
| [applications/marketplace-operations/src/main/kotlin/io/flooow/marketplace/operations/authorization/ApprovalGovernance.kt](../../applications/marketplace-operations/src/main/kotlin/io/flooow/marketplace/operations/authorization/ApprovalGovernance.kt) | `bb71114ceb00501499adefe1ce3a1418cdb2a0e36d71fdf5f44fa54773a246dc` |
| [applications/marketplace-operations-persistence-postgres/src/main/kotlin/io/flooow/marketplace/persistence/postgres/PostgresAcceptedAttestationVerifier.kt](../../applications/marketplace-operations-persistence-postgres/src/main/kotlin/io/flooow/marketplace/persistence/postgres/PostgresAcceptedAttestationVerifier.kt) | `0ae90611d56a8127379b33c9e29b67d9330391f531c2583e13860189ca76b3a4` |
| [applications/marketplace-operations-persistence-postgres/src/main/resources/db/migration/V040__create_s2a_approval_governance.sql](../../applications/marketplace-operations-persistence-postgres/src/main/resources/db/migration/V040__create_s2a_approval_governance.sql) | `58753e9d702169311f5ea74099f89e5068d982ef9c30d0e1da275b4e40b6bedd` |
| [applications/marketplace-operations-persistence-postgres/src/main/resources/db/migration/V041__create_s2a_accepted_attestation.sql](../../applications/marketplace-operations-persistence-postgres/src/main/resources/db/migration/V041__create_s2a_accepted_attestation.sql) | `3ff1421dd56de17270a9c44054055c0c1afc91f855d903697268088a53f1182d` |
| [applications/marketplace-operations-persistence-postgres/src/main/resources/db/migration/V042__create_s2a_attestation_consumption_and_attested_command_authority.sql](../../applications/marketplace-operations-persistence-postgres/src/main/resources/db/migration/V042__create_s2a_attestation_consumption_and_attested_command_authority.sql) | `3bfc5f7c95d235235ff8444453523a6a757980b464bff60ad5150e622d2f1ae1` |
| [docs/adr/ADR-0090-governed-offline-field-proof-exclusive-capability-composition.md](../../docs/adr/ADR-0090-governed-offline-field-proof-exclusive-capability-composition.md) | `e1c26d2f202684d5ace54408c83a0fcf100085864270f0c32cb077b9398566a9` |
| [applications/marketplace-operations/src/main/kotlin/io/flooow/marketplace/operations/authorization/ApprovalGovernanceFingerprint.kt](../../applications/marketplace-operations/src/main/kotlin/io/flooow/marketplace/operations/authorization/ApprovalGovernanceFingerprint.kt) | `54a036e9e738252127317525cfe0d6f1b138834a380dfac2927591e860175353` |
| [applications/marketplace-operations-persistence-postgres/src/main/resources/db/migration/V034__create_command_authorization.sql](../../applications/marketplace-operations-persistence-postgres/src/main/resources/db/migration/V034__create_command_authorization.sql) | `8745476ccc76d6d0b9b100489f317f6cead44afd0072998401d94c3b595bc5d9` |
| [applications/marketplace-operations-persistence-postgres/src/main/resources/db/migration/V035__create_explicit_transaction_identity.sql](../../applications/marketplace-operations-persistence-postgres/src/main/resources/db/migration/V035__create_explicit_transaction_identity.sql) | `697cb21228ceb0237462c59fa70db9d92e673c7e8b034dfc68964ccd01703030` |
| [applications/marketplace-operations-persistence-postgres/src/main/resources/db/migration/V037__add_controlled_command_authority_provisioning.sql](../../applications/marketplace-operations-persistence-postgres/src/main/resources/db/migration/V037__add_controlled_command_authority_provisioning.sql) | `c19a45d17774450747e1f4f6ad50745a085b37b621abbe1937f134bf688604ce` |

Preserved prior Package 0090 evidence inventory:

| Artifact | Bytes | SHA256 |
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
