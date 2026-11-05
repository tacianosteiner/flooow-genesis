# Package 0090 B01 — R5N.1 static evidence

**BLOCKED — independent review FAIL_STATIC_DESIGN; 0/7 fully designed.**

Only new design/evidence files were created. No implementation, native build, SQL, database contact, V043, B02, network qualification, staging, commit, push or PR occurred. No prior source/evidence was changed.

## Accounting

Three original proof families remain accounted for: ISOLATION_CUSTODY and CATALOG_WORK_WITNESS remain open; PUBLICATION_GENERATION_BINDING was CLOSED_BY_R5N. Thus 3 − 1 = 2 historical families. This review exposes 12 atomic decisions within those same two families; it does not manufacture twelve original roots. The 490 non-native R5 failures are unchanged.

## Candidate design and independent result

Seven distinct participants retain the byte-identical approved message ABI, generation/registry and identity codecs. Candidate additions describe 240 syscall policy rows, seven authority profiles, 189 custody field declarations, 21 pairwise independence relations, 19 catalog relations, 146 projected fields, 26 named predicates and 21 graph edge types. These are inventory counts, not counts of proven rules.

Independent per-participant evaluation records all ten components in independent-review.json. Identity, ABI, generation and registry retain complete static design with future measured evidence pending. Isolation, custody, catalog, completed work, independence and substitution rejection fail static design for every participant. Future binary hashes/PIDs/installed-policy measurements are not counted as static blockers.

The 168 prior substitution rows and 182 new rows (26 per participant) are preserved. A calculated static attack rerun is NOT proven: expected-outcome declarations do not establish rejection. This deficiency is N1-SUBSTITUTION-STATIC-WITNESSES. Completed-work NO is not solely custody: catalog visibility, reader effects, snapshot barrier and exact qualification bindings are independently necessary.

## Atomic residuals

### N1-LABEL-IR-ATOMICITY

**PARTICIPANT**: POSTMASTER, SUPERVISOR, RECEIVER, CENSUS_OBSERVER, APPROVAL_PRODUCER, APPROVAL_CONSUMER, ENFORCEMENT_WORKER

**MISSING_DECISION**: Atomic FD/path/socket/IPC label propagation and phase transition enforcement are unnamed backend operations.

**MISSING_SOURCE**: execution-isolation.json#/IR_enforcement and /rules: FD_LABEL_IN, ALL_PATHS_LABEL_IN, IPC_NAMESPACE_LABEL_ONLY, ENGINE_OWNED_DESCRIPTOR_ONLY

**WHY_STATIC**: Naming seccomp plus immutable LSM does not specify a decision procedure for SCM_RIGHTS, rename/symlink races or shared labels.

**MINIMUM_NEXT_ACTION**: Pin one enforcement backend and exact atomic label creation, propagation, checks and transition rules; deny ambiguous races.

### N1-SCALAR-SYSCALL-IR

**PARTICIPANT**: POSTMASTER, SUPERVISOR, RECEIVER, CENSUS_OBSERVER, APPROVAL_PRODUCER, APPROVAL_CONSUMER, ENFORCEMENT_WORKER

**MISSING_DECISION**: Exact scalar syscall argument semantics for 240 proposed rules remain incomplete.

**MISSING_SOURCE**: execution-isolation.json#/rules: PROCESS_LOCAL_MEMORY_CLOCK_SIGNAL_HANDLER_OR_IDENTITY_ONLY, SEALED_RESOURCE_QUOTAS, EVERY_POLLED_FD_IN and other_arguments

**WHY_STATIC**: Several predicates hide pointer-array checks, signal handler behavior, architecture/ABI numbers, clock IDs and quota schemas under prose. This is missing policy, not missing compiled filters.

**MINIMUM_NEXT_ACTION**: Give every rule a typed architecture-specific argument predicate and scalar/pointer inspection algorithm, including explicit resource quota schema and finite defaults.

### N1-SOURCE-STATS-VISIBILITY

**PARTICIPANT**: POSTMASTER, SUPERVISOR, RECEIVER, CENSUS_OBSERVER, APPROVAL_PRODUCER, APPROVAL_CONSUMER, ENFORCEMENT_WORKER

**MISSING_DECISION**: Ordinary reader visibility and completeness of cross-role backend census cannot be derived.

**MISSING_SOURCE**: Frozen system_views.sql/pg_proc.dat identify pg_stat_get_activity but frozen provider inventory lacks src/backend/utils/adt/pgstatfuncs.c::pg_stat_get_activity.

**WHY_STATIC**: Visibility/redaction affects required backend_start/backend_type and census completeness independently of actual future PIDs.

**MINIMUM_NEXT_ACTION**: Pin the approved PG18 implementation and prove exact minimal field visibility; do not adopt superuser or pg_read_all_stats implicitly.

### N1-READER-PREPARSE-GATE

**PARTICIPANT**: POSTMASTER, SUPERVISOR, RECEIVER, CENSUS_OBSERVER, APPROVAL_PRODUCER, APPROVAL_CONSUMER, ENFORCEMENT_WORKER

**MISSING_DECISION**: Exact no-generic-SQL ingress enforcement before parse/type/planner effects is unspecified.

**MISSING_SOURCE**: catalog-reader.json#/SQL_transport; login.c guarded_executor_start and guarded_utility are later execution hooks.

**WHY_STATIC**: Fixed builder prose and an ExecutorStart hook are not a unique earlier effect boundary.

**MINIMUM_NEXT_ACTION**: Specify fixed frontend packet state machine and earliest enforcement entrypoint, exact allowed statement bytes/parameters and source proof of no prior unapproved effects.

### N1-CATALOG-EFFECT-GRAPH

**PARTICIPANT**: POSTMASTER, SUPERVISOR, RECEIVER, CENSUS_OBSERVER, APPROVAL_PRODUCER, APPROVAL_CONSUMER, ENFORCEMENT_WORKER

**MISSING_DECISION**: Authority graph construction/effect closure is not a deterministic source-to-edge algorithm.

**MISSING_SOURCE**: catalog-security-predicates.json: EXISTS_EFFECTIVE_CREATOR_DEFAULT, EXISTS_REACHABLE_FUNCTION(verified_body_effect_graph), EXISTS_REACHABLE_EFFECT_OUTSIDE_ALLOWLIST; catalog-projection omits proargdefaults and pg_type function edges.

**WHY_STATIC**: Generic BFS is deterministic only after edge construction. Source hashes/dependencies do not prove function body effects or default/type parser execution effects.

**MINIMUM_NEXT_ACTION**: Define per-edge typed constructors, complete callable/effect allowlists and exact PG18 ACL/default/SD semantics; extend projection or explicitly reject unsupported callable/type/default paths.

### N1-READER-EFFECTIVE-ACL

**PARTICIPANT**: POSTMASTER, SUPERVISOR, RECEIVER, CENSUS_OBSERVER, APPROVAL_PRODUCER, APPROVAL_CONSUMER, ENFORCEMENT_WORKER

**MISSING_DECISION**: Exact effective minimum reader authority is not defined by desired column grants.

**MISSING_SOURCE**: catalog-reader.json#/grants and catalog-projection.json#/sources/*/REQUIRED_READ_PRIVILEGE

**WHY_STATIC**: PUBLIC table/function/schema privileges, built-in callable paths and default ACLs can survive zero memberships. The contract states targets but no complete effective ACL plan.

**MINIMUM_NEXT_ACTION**: Enumerate exact CONNECT/USAGE/column SELECT/function EXECUTE authority including PUBLIC/default/ownership paths; prove all stronger authority inaccessible without silently widening scope.

### N1-CONFIG-SECRET-EXCLUSION

**PARTICIPANT**: POSTMASTER, SUPERVISOR, RECEIVER, CENSUS_OBSERVER, APPROVAL_PRODUCER, APPROVAL_CONSUMER, ENFORCEMENT_WORKER

**MISSING_DECISION**: Raw configuration arrays have no safe value selection/redaction rule.

**MISSING_SOURCE**: catalog-projection.json: pg_db_role_setting.setconfig and pg_proc.proconfig are FIELD expressions, not hashes.

**WHY_STATIC**: Custom GUC values may contain credentials. No-secret observation requires a deterministic projection rule before reading/exporting them.

**MINIMUM_NEXT_ACTION**: Define exact non-secret key/value schema with forbidden secret names/value handling or hash-only safe verification; unknown settings fail closed, never export raw values by default.

### N1-SNAPSHOT-MUTATION-BARRIER

**PARTICIPANT**: POSTMASTER, SUPERVISOR, RECEIVER, CENSUS_OBSERVER, APPROVAL_PRODUCER, APPROVAL_CONSUMER, ENFORCEMENT_WORKER

**MISSING_DECISION**: Trusted TEST admin/DDL exclusion and native observation barrier have no exact acquisition/ownership/invalidation protocol.

**MISSING_SOURCE**: snapshot-consistency.json#/CATALOG_REVISION_OR_EQUIVALENT_RULE and /SNAPSHOT_BEGIN_RULE

**WHY_STATIC**: REPEATABLE READ plus before/after equality does not prove volatile census coherence or prevent authority changes between observation and publication.

**MINIMUM_NEXT_ACTION**: Specify exact barrier owner/token/state transitions, all mutator coverage, ordering with registry publication, loss/ABA invalidation and independent witness; no live demonstration required.

### N1-CREDENTIAL-CLASS-INVENTORY

**PARTICIPANT**: POSTMASTER, SUPERVISOR, RECEIVER, CENSUS_OBSERVER, APPROVAL_PRODUCER, APPROVAL_CONSUMER, ENFORCEMENT_WORKER

**MISSING_DECISION**: Seven generic TEST_GENERATION_TRANSPORT rows do not enumerate purpose-specific custody or dedicated READ_PROXY SQL credential custody.

**MISSING_SOURCE**: credential-custody.json#/credentials; preserved-native-identity-codec.json#/credential_purpose_enum; catalog-reader.json#/SQL_transport

**WHY_STATIC**: Future measured key bytes are allowed; missing mappings from each required credential purpose/class to issuer/custodian/channel/use bound are static omissions.

**MINIMUM_NEXT_ACTION**: Enumerate each purpose/key/SQL-authentication class including proxy custody, exact delivery and revocation observer inputs; distinguish server public identity from participant private signing custody.

### N1-QUALIFICATION-INPUT-RESOLUTION

**PARTICIPANT**: POSTMASTER, SUPERVISOR, RECEIVER, CENSUS_OBSERVER, APPROVAL_PRODUCER, APPROVAL_CONSUMER, ENFORCEMENT_WORKER

**MISSING_DECISION**: Qualification INPUT names are typed categories but do not resolve to exact receipt field predicates.

**MISSING_SOURCE**: participant-qualification.json#/matrix/*/qualification and /input_types

**WHY_STATIC**: ALL_KNOWN_TRUE over abstract CUSTODY_ATTESTATION/STATIC_ISOLATION_IR labels does not specify verifiable field paths, schemas, expected bindings or allowed authority effects.

**MINIMUM_NEXT_ACTION**: Bind every Boolean input per participant to exact preserved/new schema paths, canonical commitments and deterministic comparison/invalidation rules; no prose-valued qualification fields.

### N1-SUBSTITUTION-STATIC-WITNESSES

**PARTICIPANT**: POSTMASTER, SUPERVISOR, RECEIVER, CENSUS_OBSERVER, APPROVAL_PRODUCER, APPROVAL_CONSUMER, ENFORCEMENT_WORKER

**MISSING_DECISION**: 182 new substitution rows repeat one generic expected predicate; no deterministic altered-input witness/evaluation is provided.

**MISSING_SOURCE**: substitution-matrix.json#/new_cases; preserved_cases are unchanged contract expectations.

**WHY_STATIC**: A required REJECT string does not show the resulting contract rejects a wrong-reader/default/SD/reconnect case. This is absent static analysis, not absent runtime attack execution.

**MINIMUM_NEXT_ACTION**: For each applicable participant/case define typed baseline input, exact mutation, selected predicate and calculated REJECT/UNKNOWN result; preserve all 168 old cases and rerun statically.

### N1-CATALOG-CODEC-TYPE-TABLE

**PARTICIPANT**: POSTMASTER, SUPERVISOR, RECEIVER, CENSUS_OBSERVER, APPROVAL_PRODUCER, APPROVAL_CONSUMER, ENFORCEMENT_WORKER

**MISSING_DECISION**: Catalog canonical frame lacks an exact source/type/tag mapping for all projected PostgreSQL types.

**MISSING_SOURCE**: catalog-encoding.json#/frame and /numeric and /arrays; catalog-projection includes oidvector, _char, _oid, pg_node_tree-derived hashes

**WHY_STATIC**: Field order is explicit but tags are only ascending-contiguous, source framing/type IDs and oidvector versus nullable array conventions are not uniquely assigned.

**MINIMUM_NEXT_ACTION**: Give a closed source/domain/tag/type table and exact encodings for every projected type including oidvector/arrays/byte hashes and null elements, with valid/invalid static vectors.

## Integrity and limits

Preflight verified all 72 pre-existing untracked paths in authorized R5/R5N scopes, branch/HEAD/remote tracking identity, tracked/staged zero, old manifests and canonical V043 integrity. REMOTE_HEAD is the existing remote tracking ref; no network refresh was performed. Negative execution statements describe actions of this task and immutable prior records, not forensic knowledge of unobserved actors.

Canonical V043 Git-LF SHA256: `007ab786c417c41e2b1702ebf3852cb70ff5c142fa3fde195385e04c6dde8b4a`; Flyway signed CRC32: `1279591798`. The 55000 fence remains before search_path.

Run `python -B docs/evidence/package-0090-B01-v2-native-static-closure-r5n1/verify.py`. Checks validate frozen bytes, Git-LF identities, scope, inventories, review hashes and manifest. Passing these checks does not close the design predicates. derive.py is the candidate derivation only; final reviewed metadata is produced by finalize.py and supersedes its draft gate. Do not rerun derive.py alone and treat its draft status as accepted.

Unresolved catalog inventory: five known field/roster issues, two additional missing field families, ten named predicates. Unresolved isolation: two decision families; custody: one decision family; all 21 independence pairs remain unproven. Exact lists and metric granularity are in independent-review.json.

## Receipt

```text
BRANCH=checkpoint/package-0090-cloud-handoff
BASELINE_HEAD=cbc284f62d9bd09b7169b55c8d66a3c51a68c6cb
R5_NATIVE_ROOT_CAUSES_ORIGINAL=3
R5_NATIVE_ROOT_CAUSE_1=NATIVE/ISOLATION_CUSTODY:STILL_OPEN
R5_NATIVE_ROOT_CAUSE_2=NATIVE/CATALOG_WORK_WITNESS:STILL_OPEN
R5_NATIVE_ROOT_CAUSE_3=NATIVE/PUBLICATION_GENERATION_BINDING:CLOSED_BY_R5N
ROOT_CAUSE_ACCOUNTING_RECONCILED=YES
R5_NATIVE_TRUE_STATIC_DESIGN_FAILURES_BEFORE=2
R5_NATIVE_TRUE_STATIC_DESIGN_FAILURES_REMAINING=2
R5N_STATIC_ISOLATION=BLOCKED
R5N_STATIC_CATALOG=BLOCKED
NATIVE_PARTICIPANTS_REQUIRED=7
NATIVE_PARTICIPANTS_FULLY_DESIGNED=0
UNRESOLVED_NATIVE_WORK_ANCHORS=7
GENERIC_PROCESS_SUBSTITUTIONS=0
NATIVE_MESSAGE_ABI_COMPLETE=YES
NATIVE_GENERATION_PROTOCOL_COMPLETE=YES
NATIVE_REGISTRY_PROTOCOL_COMPLETE=YES
NATIVE_COMPLETED_WORK_PROTOCOL_COMPLETE=NO
NATIVE_INDEPENDENCE_MODEL_COMPLETE=NOT_PROVEN
NATIVE_CUSTODY_MODEL_COMPLETE=NO
NATIVE_CATALOG_MODEL_COMPLETE=NO
NATIVE_SUBSTITUTION_MATRIX_COMPLETE=NOT_PROVEN
CATALOG_SOURCE_RELATIONS_TOTAL=19
CATALOG_PROJECTED_FIELDS_TOTAL=146
CATALOG_SECURITY_PREDICATES_TOTAL=26
CATALOG_GRAPH_EDGE_TYPES_TOTAL=21
CATALOG_UNRESOLVED_FIELDS=5
CATALOG_UNRESOLVED_PREDICATES=10
NATIVE_ISOLATION_RULES_TOTAL=240
NATIVE_CUSTODY_RULES_TOTAL=189
NATIVE_INDEPENDENCE_RELATIONS_TOTAL=21
NATIVE_UNRESOLVED_ISOLATION_RULES=2
NATIVE_UNRESOLVED_CUSTODY_RULES=1
NATIVE_UNRESOLVED_INDEPENDENCE_RELATIONS=21
IMPLEMENTATION_PERFORMED=NO
NATIVE_BUILD_PERFORMED=NO
NATIVE_RUNTIME_EXECUTED=NO
SQL_EXECUTED=NO
DATABASE_CONTACTED=NO
V043_EXECUTED=NO
B02_EXECUTED=NO
NATIVE_INDEPENDENT_REVIEW=FAIL_STATIC_DESIGN
V2_NATIVE_STATUS=BLOCKED
BLOCKER_COUNT_FOR_V2_NATIVE=12
RESIDUAL_NATIVE_BLOCKERS=['N1-LABEL-IR-ATOMICITY', 'N1-SCALAR-SYSCALL-IR', 'N1-SOURCE-STATS-VISIBILITY', 'N1-READER-PREPARSE-GATE', 'N1-CATALOG-EFFECT-GRAPH', 'N1-READER-EFFECTIVE-ACL', 'N1-CONFIG-SECRET-EXCLUSION', 'N1-SNAPSHOT-MUTATION-BARRIER', 'N1-CREDENTIAL-CLASS-INVENTORY', 'N1-QUALIFICATION-INPUT-RESOLUTION', 'N1-SUBSTITUTION-STATIC-WITNESSES', 'N1-CATALOG-CODEC-TYPE-TABLE']
NEXT_EXECUTED=False
NEXT_GATE=CLOSE_TWELVE_ENUMERATED_STATIC_DECISIONS_NO_LIVE_EXECUTION
CATALOG_MISSING_FIELD_FAMILIES=2
NATIVE_ISOLATION_SYSCALL_ROWS=240
NATIVE_ISOLATION_PROPOSED_CLAUSES_INCLUDING_FIELD_DECLARATIONS=597
NATIVE_CUSTODY_DECLARATIONS_TOTAL=189
CURRENT_HEAD=cbc284f62d9bd09b7169b55c8d66a3c51a68c6cb
REMOTE_HEAD=cbc284f62d9bd09b7169b55c8d66a3c51a68c6cb
LOCAL_EQUALS_REMOTE=YES
TRACKED_DIRTY_COUNT=0
STAGED_COUNT=0
UNTRACKED_BEFORE=72
UNAUTHORIZED_UNTRACKED_COUNT=0
REMAINING_ATOMIC_DECISIONS=12
UNTRACKED_AFTER=99
TESTS_DISTINCT=5039
TEST_FAILURES=0
```

Next action: close the twelve enumerated static decisions and repeat independent review. No live gate is authorized by this receipt.
