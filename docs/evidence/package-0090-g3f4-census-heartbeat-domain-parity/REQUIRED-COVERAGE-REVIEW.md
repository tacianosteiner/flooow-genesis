# Required coverage review — no inherited runtime PASS

Status: HOLD. The selected corrected rounds are indexed in POST-ATTEMPT10-FULL-REGRESSION.json. All C/runtime header hashes must equal final source bytes; an older PASS is not used to fill a missing case. A successful round means its measured assertions passed, not that every normative case is implemented.

| Requirement | Final-byte witness / remaining gap |
|---|---|
| Frozen binding framing/typed encoding | Three independent native/JVM byte vectors, integer microseconds and actual stored synthetic header; full semantic relations remain HOLD |
| Frozen attestation/verifier | Public production JVM primitive replay and original material substitution regression; complete authority/source/evidence/consumption semantics remain HOLD |
| Independent census | Server pg_stat_activity enumeration independent of registry; pending pre-SCM witness; census runs inside receiver, not a separately qualified worker |
| Admission/census schedules | Pending witness fails closed through retained postmaster generation; exhaustive birth/death/duplicate/generation schedules remain NOT_RUN |
| Receiver/supervisor stalled | Retained-anchor SIGSTOP, emission-timestamp freshness loss, active-session stop, deny-new and fresh-generation recovery |
| Stale queued heartbeat | Kernel sender verified; actual fresh-at-emission frame waits 11s in queue and is denied without updating liveness; replay/future/expired/short/wrong-marker/missing-sender/EOF vectors |
| Participant dead / restart | Receiver/supervisor generation loss and rebootstrap; complete active-fault coverage for every required participant remains HOLD |
| Observer stalled / dead / source unavailable | Observer pause and custody failure cases; a separate dead observer/source/census/enforcer participant matrix remains NOT_RUN |
| Revocation and active enforcement | Exact retained backend cancel/terminate and independent catalog disappearance; full compound-fault architecture remains HOLD |
| Clone/restore | Actual logical dump/restore and cold physical copy cohorts rerun; their results must be read from final rounds, never inherited |
| Replay/socket | Owned path removal, mode/owner faults and same-UID fake receiver; complete stale-generation/replayed ACCEPT/SCM_RIGHTS/namespace matrix explicitly NOT_RUN |
| OID/tombstone | Actual disposable catalog OID reuse and recreated exact-name denial with old binding; fresh governed allocation and full allocation lineage remain NOT_RUN |
| Ownership/retry/release | Frozen table row-shapes and conservative UNKNOWN/OWNED fixtures; complete normative wrappers, terminal retries and ownership release remain NOT_RUN |
| Reconciliation | Rollback, failed/successful commit, discarded response and active write witnesses; precise loss during COMMIT, backend death during ambiguous COMMIT and postmaster crash after possible commit remain NOT_RUN |
| Postmaster control inconsistency | Generation restart tested; complete catalog-valid/anchor-invalid, anchor-valid/catalog-stale, stale receiver and unexpected census generation cases remain NOT_RUN |
| Cancel/terminate unavailable | Suppressed signal fixture rerun; independent unknown pending census can trigger coarse generation stop and invalidate the intended retained-quarantine witness; any resulting FAIL stays open |
| Post-attempt10 material substitution | Valid foreign material with unchanged original metadata and wrong public key denied; original restored accepted, rerun on final runtime |
| Load / timing | Final idle/load/recovery observations and bounded overlay fdatasync cohort; small N, incomplete cold/churn cohorts and no physical device identity prohibit numeric readiness |

## Open finding classes

1. HIGH — Full frozen verifier/domain/authority and ownership/retry/release parity is not established by reference codec and row-shape witnesses.
2. HIGH — Census, health and active enforcement are not exhaustively independent: serial receiver observation and missing independent retained-backend enforcer leave compound stalls unqualified.
3. HIGH — Broad regressions expose coarse generation shutdown during pending admission alongside active/quarantined governed backends. Fail-closed denial is not evidence of preserved availability or complete targeting semantics.
4. HIGH — Complete required replay, control-generation and COMMIT-ambiguity schedules are not executed; final regression cannot be promoted to complete PASS.
5. MEDIUM — Tombstone denial is selected old-binding evidence; complete fresh-allocation lineage is not qualified.
6. MEDIUM — Timing cohorts do not qualify tails, worst-case coverage or numeric candidate evidence.

These are successor rehearsal review classifications (B0/H4/M2/L0). They do not rewrite Room's previously frozen B0/H3/M0/L0 disposition. H01 remains OPEN; H02 complete deployment remains HOLD; H03 selected synthetic custody/consumption/clone assertions are not canonical readiness.

The next bounded engineering action is to resolve census/admission scheduling with explicit pending identity and independent retained-anchor coverage, then implement missing full-domain/replay/control/commit fixtures and rerun all affected cohorts under identical final hashes. Existing disposable authority covers that work; canonical and numeric boundaries remain closed. No additional authority is inferred.
