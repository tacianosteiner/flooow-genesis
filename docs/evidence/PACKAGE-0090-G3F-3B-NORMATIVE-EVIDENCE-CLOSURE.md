# Package 0090 retained normative test evidence closure

Date: 2026-10-03 (America/Sao_Paulo).
Branch: checkpoint/package-0090-cloud-handoff.
Verified entry LOCAL_HEAD=REMOTE_HEAD=60f7bbe13f4c2b44d8e070a41d60dc5e28ae988d;
WORKTREE=CLEAN after fetch origin.

NORMATIVE_EVIDENCE_FIXTURE_CLOSED=YES_TEST_ONLY
ML_SELECTED_ROW_CLOSED=YES
OMIE_SELECTED_ROW_CLOSED=YES
V041_SELECTION_PARITY=FROZEN_SOURCE_MODEL_PASS_SQL_EXECUTION_HOLD
EVIDENCE_PREIMAGE_FROZEN=YES_REFERENCE_JVM
EVIDENCE_FINGERPRINT_FROZEN=YES_REFERENCE_JVM
MANIFEST_GOLDEN=PASS_REFERENCE_JVM_ALL_THREE_VECTORS
BINDING_GOLDEN=PASS_REFERENCE_JVM_ALL_THREE_VECTORS
VECTOR_1=PASS_CODEC_ONLY
VECTOR_2=PASS_NFC_AND_SLOT_ORDER_CODEC_ONLY
VECTOR_3=PASS_ENCODER_MUTATION_AND_COHERENT_ALTERNATE_NO_SIGNATURE
CODEC_GOLDENS=BINDING_SLOTS_POLICY_EVIDENCE_MANIFEST_PASS_REMAINING_PENDING
PACKAGE_0090_WRAPPER_IMPLEMENTED=NO
EXECUTOR_SIGNATURE_IMPLEMENTED=0_OF_6
EXECUTE_ACL_REVIEW=HOLD
STATIC_SQL_CONTRACT=PREREQUISITES_PASS_FULL_CLOSURE_HOLD
SECURITY_DEFINER_REVIEW=HOLD
MIGRATION_SAFETY_REVIEW=INTERLOCK_FROZEN_CHAIN_PASS_FULL_REVIEW_HOLD
TESTS=45_PASS_OFFLINE
UNRESOLVED_BLOCKER_COUNT=4
PROTECTED_DATABASE_MUTATION=NO
REAL_FIELD_PROOF=HOLD
NEXT_GATE=G3F.3B_DEPENDENT_GOLDENS_AND_V043_IMPLEMENTATION

The retained JSON specifies every physical column of nine prerequisite/evidence
tables,12 rows total. Frozen CREATE statements are parsed with pinned pglast7.10
to check exact column completeness, required values and every table-level FK.
The one-row selection model covers exact V041 scope/joins, admissible promotion,
registry/external/currency equality, base/V3/page/progress joins, count/ordinal/
progress bounds, version/hex validity, civil latest-revision availability/order,
integration/currency equality and absence of competing/equal-latest-conflicting
rows. This is source/model verification, not PostgreSQL execution parity.

Python reference reconstructs the exact frozen V041 preimage expression; a test
extracts every function-call operand and validates its frozen source order and
the framing/nullable/civil helpers. Independent Java builds all complete bytes
from the fixture constants without reading Python outputs or golden JSON. Both
agree on full bytes and SHA-256 for each preimage,manifest,binding,policy,slots
and encoder-only mutation. No source text, six-argument-only hash approximation,
opaque fingerprint approval or live data is substituted for retained evidence.

The tests reject missing/duplicate/competing/inconsistent rows and metadata,
non-NFC source, malformed binding frames and truncations, duplicate slots and
unchanged-manifest correlation mutation. Each of38 header payload mutations
changes its digest; semantic checks separately bind retained manifest identities,
references/correlation and policy hash. The coherent VECTOR_3 alternate has
re-encoded bytes but no invented signer/signature or signature proof.

The supplied Omie semantic hash is expressly a synthetic token; its original
provider semantic preimage is neither asserted nor needed by this frozen V041
codec experiment. Auxiliary amounts/timestamps/statuses satisfy physical row
shape and do not enter the V041 evidence preimage. No credential-binding secret
fixture or raw production data is created.

This supersedes only the missing-evidence-input boundary in the earlier
FIXTURE-CLOSURE report. TTL approval and fixture-1 policy remain unchanged.
The four source implementation categories remain pending and are not authority
requests. Next: independently complete remaining history/ACL/HMAC goldens, then
the authorized wrappers/guards/EXECUTE ACLs and static/security/migration reviews.
