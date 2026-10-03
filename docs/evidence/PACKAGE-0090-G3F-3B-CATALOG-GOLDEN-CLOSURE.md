# Package 0090 catalog and receipt codec checkpoint

Date: 2026-10-03 (America/Sao_Paulo).
Branch: checkpoint/package-0090-cloud-handoff.

The complete byte corpus is PACKAGE-0090-G3F-3B-CATALOG-GOLDENS.json.
Python and JVM independently construct all42 frozen history rows, a separate
null-preserving43rd malformed row, the eight SPEC22.1 conceptual ACL fixtures,
the exact nine-field preflight and binary HMAC-SHA-256/receipt. Java constructs
typed projections without reading Python-produced fixture/golden bytes.
History inputs are independently extracted from the retained repository manifest;
these are codec fixtures, not installed history. Future V043 history requires
its eventual approved frozen checksum and remains separate from this corpus.

CATALOG_GOLDENS=PASS_REFERENCE_JVM
HISTORY_FULL_V001_V042_CODEC=PASS_REFERENCE_JVM
HISTORY_NULL_CHECKSUM_VERSION_CODEC=PASS_REFERENCE_JVM
ACL_EIGHT_CONCEPTUAL_FIXTURES=PASS_REFERENCE_JVM
PREFLIGHT_NINE_FIELD_CODEC=PASS_REFERENCE_JVM
HMAC_SYNTHETIC_KEY_VECTOR=PASS_REFERENCE_JVM
DEPLOYMENT_KEY_OR_RNG_PROOF=NO
LIVE_ACL_OR_READINESS_APPROVAL=NO
SQL_EXECUTION_PARITY=HOLD_NOT_EXECUTED
TESTS=51_PASS_OFFLINE
PROTECTED_DATABASE_MUTATION=NO
REAL_FIELD_PROOF=HOLD
NEXT_GATE=G3F.3B_V043_WRAPPERS_GUARDS_AND_EXECUTE_ACLS

The public synthetic HMAC key is bytes00..1f, explicitly test-only and never an
ACTIVE deployment key. It proves codec/HMAC implementation agreement, not
entropy, key provisioning, pgcrypto/comparator binary identity or live expiry
enforcement. The preflight uses the synthetic binding/policy and conceptual F1
ACL hashes; it cannot be presented as a deployment receipt.

The tests compare full bytes and digests, preserve signed checksums and nulls,
include all42 rows without filtering, reject duplicate ranks/set rows and show
list-order sensitivity. All eight ACL fixture digests differ; F5-F8 retain their
rejection expectations. NULL versus empty config and PUBLIC RoleRef versus the
named role PUBLIC remain distinct. Every preflight field mutation invalidates
the original MAC, and changing the synthetic key invalidates it. No missing SQL
parity or current-catalog result is inferred from these offline tests.

Private54-field decision-fact/20-field accepted-snapshot commitment coverage
remains part of the S17/S18 implementation gate; this checkpoint does not claim
those dataflow or installed cryptographic proofs. V043 remains interlocked.
