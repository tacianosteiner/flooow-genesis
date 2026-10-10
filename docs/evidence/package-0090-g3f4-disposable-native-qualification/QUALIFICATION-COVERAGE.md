# Recorded qualification coverage

Status: bounded disposable observations only. Full gate HOLD.

Rounds overlap; repeated cases are not additional unique coverage. A case PASS means its recorded assertion held in that run. R3 harness failure remains a failure.

## package-0090-g3f4-disposable-native-qualification

| Case | Recorded result |
|---|---|
| native_login_test_verifier | PASS |
| native_login_test_issuer | PASS |
| native_login_test_executor | PASS |
| native_login_test_auditor | PASS |
| no_direct_SQL_enrollment | PASS |
| no_service_trigger_disable | PASS |
| no_service_replication_role_disable | PASS |
| no_service_header_write | PASS |
| missing_header_login | PASS |
| role_name_mismatch | PASS |
| role_attribute_mismatch | PASS |
| lost_ACK | PASS |
| late_ACK | PASS |
| backend_exit_invalidates_anchor | PASS |
| postmaster_restart_invalidates_generation | PASS |
| fresh_physical_login_after_rebootstrap | PASS |

## round2

| Case | Recorded result |
|---|---|
| native_login_test_verifier | PASS |
| native_login_test_issuer | PASS |
| native_login_test_executor | PASS |
| native_login_test_auditor | PASS |
| pure_frame_parser | PASS |
| same_anchor_idempotent | PASS |
| wrong-deployment | PASS |
| wrong-incarnation | PASS |
| stale-epoch | PASS |
| wrong-database | PASS |
| wrong-slot | PASS |
| bad-version | PASS |
| partial-frame | PASS |
| socket_absent | PASS |
| unsafe_namespace_permissions | PASS |
| unguarded_database_connect_denied | PASS |
| distinct_live_anchors_same_slot | PASS |
| role_membership_mismatch | PASS |
| no_direct_SQL_enrollment | PASS |
| no_service_trigger_disable | PASS |
| no_service_replication_role_disable | PASS |
| no_service_header_write | PASS |
| missing_header_login | PASS |
| role_name_mismatch | PASS |
| role_attribute_mismatch | PASS |
| lost_ACK | PASS |
| late_ACK | PASS |
| role_recreation_OID_mismatch | PASS |
| backend_exit_invalidates_anchor | PASS |
| postmaster_restart_invalidates_generation | PASS |
| fresh_physical_login_after_rebootstrap | PASS |
| receiver_crash_drains_live_backend | PASS |
| receiver_restart_exclusion | PASS |
| receiver_restart_fresh_rebootstrap | PASS |

## round3

| Case | Recorded result |
|---|---|
| native_login_test_verifier | PASS |
| native_login_test_issuer | PASS |
| native_login_test_executor | PASS |
| native_login_test_auditor | PASS |
| pure_frame_parser | PASS |
| same_anchor_idempotent | PASS |
| wrong-deployment | PASS |
| wrong-incarnation | PASS |
| stale-epoch | PASS |
| wrong-database | PASS |
| wrong-slot | PASS |
| bad-version | PASS |
| partial-frame | PASS |
| socket_absent | PASS |
| unsafe_namespace_permissions | PASS |
| receiver_impersonation_anchor_mismatch | PASS |
| SPI_lock_wait_bounded | PASS |
| receiver_catalog_wait_bounded | PASS |
| unguarded_database_connect_denied | PASS |
| distinct_live_anchors_same_slot | PASS |
| role_membership_mismatch | PASS |
| no_direct_SQL_enrollment | PASS |
| no_service_trigger_disable | PASS |
| no_service_replication_role_disable | PASS |
| no_service_header_write | PASS |
| missing_header_login | PASS |
| role_name_mismatch | PASS |
| role_attribute_mismatch | PASS |
| lost_ACK | PASS |
| late_ACK | PASS |
| role_recreation_OID_mismatch | PASS |
| backend_exit_invalidates_anchor | PASS |
| postmaster_restart_invalidates_generation | PASS |
| fresh_physical_login_after_rebootstrap | PASS |
| receiver_crash_drains_live_backend | PASS |
| receiver_restart_exclusion | PASS |
| receiver_restart_fresh_rebootstrap | PASS |

## measurement

| Case | Recorded result |
|---|---|
| native_login_test_verifier | PASS |
| native_login_test_issuer | PASS |
| native_login_test_executor | PASS |
| native_login_test_auditor | PASS |
| service_startup_trigger_bypass_denied | PASS |

## Unqualified closure

Full V043/original-attestation binding, general UTF-8 NFC, current approval custody, continuing independent freshness enforcement, complete effect/transaction/ownership drain reconciliation, sustained-load timing guarantees and canonical readiness remain unqualified. Numeric ACK/policy/health/resource/drain authority remains absent. H01/H02/H03 runtime HOLD persists.
