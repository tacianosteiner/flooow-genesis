# Disposable host component qualification — complete component evidence, runtime HOLD

Source: `scripts/validation/package_0090_host_projection_qualification.py`.
Exact image/PG18.4, newly named factory-owned containers, tmpfs data, no published
TCP port, no canonical mounts/access. Three containers removed in finally.
No keys, cryptographic SIGN, credentials/password files, ADMIN artifact or
canonical native event were created/executed. Physical backup bytes streamed
between owned disposable containers, never persisted on the workstation.

Existing unchanged C self-enrolled probe compiled with -Wall/-Wextra/-Werror:
5 kernel/socket cases passed; only signal0. Own self anchor/kernel peer/message
agreement, substituted/extra fd rejection, sender death, forged-credential denial
and retained dead anchors tested.128 controlled children per variant; no numeric
PID reuse observed. This is not SIGINT/SIGTERM enforcement or PostgreSQL enrollment.

| Case | Result | Evidence type / exact limit |
|---|---|---|
|correct_deployment_and_incarnation|PASS|SYNTHETIC_SQL_PREDICATE_NOT_AUTHENTICATED_HOST_PROOF|
|wrong_deployment|PASS|SYNTHETIC_SQL_PREDICATE_NOT_AUTHENTICATED_HOST_PROOF|
|wrong_incarnation|PASS|SYNTHETIC_SQL_PREDICATE_NOT_AUTHENTICATED_HOST_PROOF|
|fresh_99us|PASS|SYNTHETIC_SQL_PREDICATE_NOT_AUTHENTICATED_HOST_PROOF|
|fresh_exact_100us|PASS|SYNTHETIC_SQL_PREDICATE_NOT_AUTHENTICATED_HOST_PROOF|
|stale_101us|PASS|SYNTHETIC_SQL_PREDICATE_NOT_AUTHENTICATED_HOST_PROOF|
|future_observation|PASS|SYNTHETIC_SQL_PREDICATE_NOT_AUTHENTICATED_HOST_PROOF|
|replayed_receiver_generation|PASS|SYNTHETIC_SQL_PREDICATE_NOT_AUTHENTICATED_HOST_PROOF|
|watchdog_false|PASS|SYNTHETIC_SQL_PREDICATE_NOT_AUTHENTICATED_HOST_PROOF|
|clone_incarnation|PASS|SYNTHETIC_SQL_PREDICATE_NOT_AUTHENTICATED_HOST_PROOF|
|missing_projection|PASS|ACTUAL_PROTECTED_PROJECTION|
|consumer_cannot_insert|PASS|ACTUAL_PEER_AUTHENTICATED_SQL_ACL_BOUNDARY|
|consumer_cannot_update|PASS|ACTUAL_PEER_AUTHENTICATED_SQL_ACL_BOUNDARY|
|consumer_cannot_change_expected_context|PASS|ACTUAL_PEER_AUTHENTICATED_SQL_ACL_BOUNDARY|
|consumer_cannot_set_observer_role|PASS|ACTUAL_PEER_AUTHENTICATED_SQL_ACL_BOUNDARY|
|consumer_cannot_set_observer_session_authorization|PASS|ACTUAL_PEER_AUTHENTICATED_SQL_ACL_BOUNDARY|
|consumer_cannot_replace_consumer|PASS|ACTUAL_PEER_AUTHENTICATED_SQL_ACL_BOUNDARY|
|consumer_cannot_disable_login_event_setting|PASS|ACTUAL_PEER_AUTHENTICATED_SQL_ACL_BOUNDARY|
|consumer_cannot_authenticate_as_observer|PASS|ACTUAL_PEER_AUTHENTICATION|
|trusted_superuser_can_author_projection_outside_threat_model|PASS|ACTUAL_FIXTURE_COUNTEREXAMPLE_TO_HOSTILE_ADMIN_PROTECTION_ROLLED_BACK|
|actual_stale_projection|PASS|ACTUAL_PROTECTED_PROJECTION|
|receiver_restart_old_projection|PASS|INJECTED_TRUSTED_EXPECTED_GENERATION|
|restore_copied_system_context|PASS|INJECTED_SYSTEM_CONTEXT_NOT_REAL_CLONE|
|actual_logical_restore_new_system_id|PASS|ACTUAL_LOGICAL_RESTORE_NOT_PHYSICAL_CLONE|
|actual_logical_restore_old_projection_denied|PASS|ACTUAL_LOGICAL_RESTORE_STALE_AND_WRONG_SYSTEM_CONTEXT|
|actual_physical_clone_copies_system_identifier|PASS|ACTUAL_PHYSICAL_CLONE_COUNTEREXAMPLE_TO_SYSTEM_ID_UNIQUENESS|
|actual_physical_clone_old_projection_denied|PASS|ACTUAL_PHYSICAL_CLONE_OLD_TIMESTAMP_DENIAL_ONLY|
|discarded_ack_join_writer_fresh_query_first|PASS|ACTUAL_UNSIGNED_COMMIT_ACK_DISCARD_NOT_08006|

Positive fresh/context cases use injected instants in a private SQL predicate.
They are NOT independently authenticated live host proof. The real consumer uses
stored protected context/observation and its own fresh DB clock, accepting no caller
time or predicate arguments. Ten real writer→consumer reads all denied freshness:
min age 218042.0us, maximum 427686.0us, actual bound100us unchanged.
No synthetic positive is relabeled end-to-end proof.

Private OS-peer mapping lets postgres OS identity act as the fixture observer and
nobody act as a restricted consumer. The consumer cannot authenticate as observer,
SET ROLE/SESSION AUTHORIZATION, change protected fields/context, replace the consumer
function or disable event_triggers. No fixture login name/OID/grant is canonical.
The trusted superuser counterexample **passes as a counterexample**: it can write
projection fields, then rolls back. Hostile-admin inability to manufacture a row
was never promised by existing SPEC1. Procedural independent authorship remains
required for the actual trusted PLAN_BINDING_ADMIN path.

Logical restore into another actual cluster denied copied old projection. Physical
basebackup into another actual container retained system_identifier and denied the
old timestamp. This is stronger than an injected UUID case, but proves only old
projection denial: native reincarnation, strong receiver epoch and prevention of
fresh privileged reauthorship remain unqualified. Current-incarnation/receiver
binding cannot be inferred from copied DB metadata.

One actual unsigned transaction discarded its psql output/ACK, joined the writer,
then found exactly one row on a fresh connection. This is controlled ACK discard,
not a real JDBC08006, ambiguous delivery proof or signed-root recovery qualification.
No retry/re-sign or whole-runner inference follows from it.

Preparation attempts exposed tmpfs noexec and physical data-directory/socket setup
requirements; corrected source passed all28 SQL/ACL/restore/commit cases. Failed
attempts were not counted as passing evidence; all owned containers were removed.
Source/binary hashes and raw non-secret observations are retained in the JSON.

WATCHDOG_COMPONENT_CASES=28_PASS_PLUS_5_KERNEL_CASES
WATCHDOG_PROOF=HOLD_NATIVE_ADMISSION_GENERATION_ACK_CONTINUOUS_ENFORCEMENT_UNQUALIFIED
ADMIN_SELF_AUTHORSHIP=NO_PERMITTED_PATH_NOT_HOSTILE_SUPERUSER_PROTECTION
