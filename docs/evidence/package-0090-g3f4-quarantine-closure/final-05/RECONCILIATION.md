# Final disposable regression reconciliation

Status: HOLD — TEST_ONLY_NONCANONICAL; no Room or full-watchdog readiness.

Final immutable batch: `final-05`. Executed assertions: 368; PASS: 368; FAIL: 0; operational error cohorts: 2.

Raw NOT_RUN rows: 13. Original exact cases: 21. Unresolved original full-case qualifications: 10. Raw cross-cohort deferrals are preserved, not silently discarded. Coverage aliases never create duplicate assertions.

| Previous exact ID | Disposition | Concrete scope / reason |
|---|---|---|
| census/all_birth_death_duplicate_generation_races | HOLD | All interleavings cannot be exhausted by a finite runtime population. Bounded census, quarantine and ten injected schedules are rerun; simultaneous faults, capacity/duplicate/birth/death combinations are not a complete schedule model. |
| tombstone/explicit_fresh_allocation_entire_new_binding | HOLD | The protected tombstone and reuse denials execute. A new legitimate allocation ceremony with its own complete new binding/authority lineage is not provisioned; direct synthetic row replacement cannot substitute for that ceremony. |
| full_normative_parity/frozen_wrappers_authority_consumption_terminal_retry_release | HOLD | Frozen V043 has an explicit executable safety interlock (55000). Installing its positive wrappers would bypass that interlock. Exact extracted DDL and actual JVM artifact verification do not execute its authority, source, accepted-consumption, retry or release joins. |
| remaining/forced_oid_reuse | QUALIFIED_BOUNDED | Actual disposable catalog OID reuse is injected and old allocation remains denied. This tests protection, not PostgreSQL allocator behavior. |
| remaining/full_physical_clone | QUALIFIED_BOUNDED | Actual cold PGDATA copy cannot bootstrap without the retained external context. This is bootstrap denial, not all restore or storage failure populations. |
| remaining/full_logical_restore | QUALIFIED_BOUNDED | Actual pg_dump/restore copies the header into a distinct database and denies governed login. |
| remaining/terminate_failure | QUALIFIED_BOUNDED | Both selected signals are suppressed; admission remains denied, the participant remains quarantined, and restored termination drains without releasing ownership. |
| remaining/full_transaction_ownership_contract | HOLD | Synthetic OWNED rows, real transaction rollback and query-first reconciliation execute. Full frozen claim/attempt/execution/receipt/economic-effect wrappers remain behind the V043 safety interlock. |
| remaining/postmaster_control_inconsistency | HOLD | Joint epoch restart, retained participant deaths and old postmaster identity execute. Full simultaneous control-channel loss and PostgreSQL parallel-worker populations are not qualified; selected restart proof is not complete postmaster consistency. |
| remaining/all_timeout_state_signal_invariants | HOLD | Actual caller PostgreSQL timer, SIGALRM handler/mask/flags and ITIMER snapshots execute with SPI failure and recovery. Exhaustive asynchronous signal-delivery schedules and timer drift cannot be inferred from these selected snapshots. |
| remaining/complete_watchdog_worstcase_coverage | HOLD | No approved numeric health/resource/drain bounds exist in the structural authority. Bounded CPU, I/O and stall samples cannot establish complete worst-case coverage or a policy candidate population. Numeric adoption remains forbidden. |
| remaining/independent_JVM_reference_binding_vectors | QUALIFIED_BOUNDED | Independently compiled actual frozen JVM vectors are compared with the current native codec; no historical native PASS is inherited. |
| replay/stale_enrollment_frame | QUALIFIED_BOUNDED | A frame with an actual old joint generation and original server-derived backend identity is rejected; selected transfer/catalog/response delays also deny usability past the native deadline. |
| replay/old_receiver_generation_frame | QUALIFIED_BOUNDED | The approved V1 wire uses one jointly bootstrapped immutable epoch. An actual previous receiver epoch is replayed into a newly bootstrapped generation. Hot individual replacement is not a legal V1 generation. |
| replay/old_supervisor_generation_frame | QUALIFIED_BOUNDED | Same actual previous joint epoch test. Supervisor and receiver do not have independently replaceable wire epochs; this alias adds no assertion to the denominator. |
| replay/old_postmaster_generation_frame | QUALIFIED_BOUNDED | Actual old joint epoch plus stale postmaster-start identity are rejected. This alias adds no assertion to the denominator. |
| replay/old_approval_generation_frame | HOLD | Current-custody revocation and revision tampering deny admission. A previously valid older signed approval ceremony followed by a newly valid complete replacement ceremony is not reconstructed. Invalid revision bytes are not proof of this full case. |
| replay/old_attestation_bundle_frame | HOLD | Actual foreign test-key material substitution and original pinned recovery execute, plus authority revision tampering. This does not reconstruct two fully valid sequential authority/consumption ceremonies behind the frozen contract. |
| replay/replayed_ACCEPT | QUALIFIED_BOUNDED | The exact previously accepted 76-byte reply is captured and replayed after a real joint generation restart; the current native login rejects it. |
| replay/replayed_SCM_RIGHTS | QUALIFIED_BOUNDED | An actual backend transfers its own live pidfd and valid frame to a separate native sender. After backend death that retained descriptor is replayed and rejected with kernel-identity reason 6. No foreign PID is opened. |
| replay/valid_protocol_wrong_namespace | HOLD | The qualified infrastructure has network=none, mount isolation and one trusted bootstrap/socket namespace per disposable container. A second concurrently valid complete bootstrap plus an explicit cross-namespace descriptor injection channel is absent. Wrong path/owner/peer and old joint context tests do not substitute for that population. |

Exact case-level evidence, all raw NOT_RUN rows, compiler-copy checks, immutable source and core binary maps are in [RECONCILIATION.json](RECONCILIATION.json).

Historical preservation: 885 checks, 0 mismatch. All 16 rounds record owned container removal and private-key erasure. No frozen interlock, canonical material or numeric policy was changed.
