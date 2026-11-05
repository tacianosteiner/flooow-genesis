# Package 0090 — R5N.2 resumed static closure

**BLOCKED: 2/12 static decisions closed; 10 exact residuals; no new blocker.**

This resumes existing R5N.2 files. It does not restart or discard the package. Independent review was rerun from final inputs after the prior infrastructure interruption; partial reviewer messages were not accepted as a gate result.

## Result

Closed: N1-CONFIG-SECRET-EXCLUSION and N1-CATALOG-CODEC-TYPE-TABLE. Configuration excludes raw secret values before export/log/hash and binds assertions to exact source-row keys. All 146 projected fields have deterministic codecs; privileges use 15 canonical semantic identities and the exact ALTER SYSTEM alias from frozen acl.c, without invented PostgreSQL native masks.

Label publication now separates NATIVE_REGISTRY_WRITER(10) from read-only HEALTH_GUARD(8), specifies complete signed sidejournal records, CAS, recovery, replay, generation/currentness and UNKNOWN. This closes the publication subcondition, but not original kernel-object label propagation/inspection; it remains under the same label blocker. The snapshot-byte preparse gate likewise does not silently remove the earlier SQL parse/type/planner effect boundary.

The denominator remains exactly 12. EPOCH, PARTITIONS, TEMPLATES, canonical source, fixtures, V043 and B02 are untouched. The latest graph has 12 NATIVE qualification edge kinds; it does not claim the complete global authority graph.

## Evidence levels and counters

Seven participants were independently evaluated on all ten components; none is fully designed. Identity/ABI/generation/registry and per-role completed-work anchor measurement contracts are statically complete with future values pending. UNRESOLVED_NATIVE_WORK_ANCHORS=0 counts missing anchor measurement contracts, not successful live work or fully qualified participants. Catalog/custody/isolation/input and 217 attack-witness decisions still prevent qualification. This refines the earlier aggregate completed-work NO rather than fabricating runtime evidence.

There are 350 preserved substitution cases: 133 have explicit typed tuple comparison contracts; 217 still need exact graph/receipt/mutation witness mappings. These counts describe static contracts, not attacks executed. The 240 carried syscall rows all still depend on backend argument/label decisions. Custody count7 means carried participant custody rows, not60 class field declarations; all7 remain unresolved. The three purpose classes provide60 field declarations but omit at least the proxy SQL authentication class. No exhaustive reference ledger exists: the unclassified-reference value is explicitly a lower bound, never assumed exact1.

Catalog counts:19 sources,146 fields,26 carried predicates,12 latest edge kinds. Five source-visibility fields remain unresolved; codec-unresolved fields=0 is distinct. Two predicate algorithm roots remain open, with additional transitively affected predicates; this count is not the earlier count of every affected predicate. Two missing callable/default field families remain explicit.

No binary/hash/PID/syscall-number/catalog snapshot/key/physical receipt absence was counted as a static failure. Implementation, build, runtime and physical instantiation remain pending future gates and were not executed.

## Twelve decisions

| Blocker | Status | Independent reason |
|---|---|---|
| N1-LABEL-IR-ATOMICITY | OPEN | Select race-safe enforcement backend and atomic kernel-object label creation/propagation/check/phase-transition algorithm for FD/path/socket/IPC; journal publication CAS is specified but does not implement this design decision. |
| N1-SCALAR-SYSCALL-IR | OPEN | Resolve the 240 symbolic syscall rule argument predicates, pointer inspection, FD identity checks and sealed quota fields to finite backend algorithms. Concrete target syscall numbers remain future measured. |
| N1-SOURCE-STATS-VISIBILITY | OPEN | Pin pg_stat_get_activity native visibility implementation and derive minimal-authority complete cross-role census for six selected columns. |
| N1-READER-PREPARSE-GATE | OPEN | Select earliest frontend packet enforcement entrypoint and exact fixed statement/parameter state machine before parse/type/planner effects. Snapshot byte preparse gate is separately specified. |
| N1-CATALOG-EFFECT-GRAPH | OPEN | Complete NATIVE-only source-to-edge callable/default/owner/effect constructors or finite rejection rule for unsupported type/default/body paths; keep 12 distinct edge kinds. |
| N1-READER-EFFECTIVE-ACL | OPEN | Enumerate exact reader CONNECT/USAGE/SELECT/EXECUTE effective allowlist with PUBLIC/default/owner/SET/INHERIT/ADMIN and bootstrap effects; prove no stronger reachable authority. |
| N1-CONFIG-SECRET-EXCLUSION | CLOSED | CLOSED: trusted adapter excludes raw values before transport/log/hash; finite safe assertions bind exact pg_proc.oid or (setdatabase,setrole) outer row, scope and NULL/empty identity; unknown setting is explicit and missing secret value is not failure. |
| N1-SNAPSHOT-MUTATION-BARRIER | OPEN | Define catalog mutator exclusion token owner/acquire/release/ABA/loss states and ordering with native registry publication plus independent witness. |
| N1-CREDENTIAL-CLASS-INVENTORY | OPEN | Classify dedicated READ_PROXY SQL authentication and bind purpose-specific delivery/custody/revocation references exhaustively; distinguish POSTMASTER endpoint from signing keys. |
| N1-QUALIFICATION-INPUT-RESOLUTION | OPEN | Replace whole-file pointers and repeated validation prose with exact schema field paths and comparisons for every Boolean qualification input. |
| N1-SUBSTITUTION-STATIC-WITNESSES | OPEN | Provide attack-specific typed baseline, mutation, witness field path and selected evaluation for remaining 217 substitution cases. |
| N1-CATALOG-CODEC-TYPE-TABLE | CLOSED | CLOSED: 146 unique relation/field tags resolve to 19 explicit canonical types, exact NULL/cell rules, BE integers and bounded UTF8/arrays; 15 semantic named privileges match frozen acl.c with sole ALTER SYSTEM alias. No PostgreSQL binary privilege masks. Source visibility/effect gaps remain assigned to their existing IDs. |

## Exact residual static decisions

### N1-LABEL-IR-ATOMICITY

**MISSING_STATIC_DECISION**: Select race-safe enforcement backend and atomic kernel-object label creation/propagation/check/phase-transition algorithm for FD/path/socket/IPC; journal publication CAS is specified but does not implement this design decision.

**SOURCE_DEPENDENCY**: execution-isolation.json#/IR_enforcement and /rules; decision-contracts.json#/contracts/N1-LABEL-IR-ATOMICITY

**WHY_STATIC**: The algorithm/authority/field comparison is not selected in current source-bound contract.

**WHY_NOT_IMPLEMENTATION_PROOF**: Writing code would require choosing the missing rule first.

**WHY_NOT_BUILD_PROOF**: Binary/hash/ABI measurements cannot choose the rule.

**WHY_NOT_RUNTIME_PROOF**: A runtime observation cannot establish an unspecified acceptance rule.

**MINIMUM_NEXT_ACTION**: Select race-safe enforcement backend and atomic kernel-object label creation/propagation/check/phase-transition algorithm for FD/path/socket/IPC; journal publication CAS is specified but does not implement this design decision.

### N1-SCALAR-SYSCALL-IR

**MISSING_STATIC_DECISION**: Resolve the 240 symbolic syscall rule argument predicates, pointer inspection, FD identity checks and sealed quota fields to finite backend algorithms. Concrete target syscall numbers remain future measured.

**SOURCE_DEPENDENCY**: execution-isolation.json#/rules and /resources; decision-contracts.json#/contracts/N1-SCALAR-SYSCALL-IR

**WHY_STATIC**: The algorithm/authority/field comparison is not selected in current source-bound contract.

**WHY_NOT_IMPLEMENTATION_PROOF**: Writing code would require choosing the missing rule first.

**WHY_NOT_BUILD_PROOF**: Binary/hash/ABI measurements cannot choose the rule.

**WHY_NOT_RUNTIME_PROOF**: A runtime observation cannot establish an unspecified acceptance rule.

**MINIMUM_NEXT_ACTION**: Resolve the 240 symbolic syscall rule argument predicates, pointer inspection, FD identity checks and sealed quota fields to finite backend algorithms. Concrete target syscall numbers remain future measured.

### N1-SOURCE-STATS-VISIBILITY

**MISSING_STATIC_DECISION**: Pin pg_stat_get_activity native visibility implementation and derive minimal-authority complete cross-role census for six selected columns.

**SOURCE_DEPENDENCY**: provider/system_views.sql pg_stat_activity; provider/pg_proc.dat; native implementation body absent from frozen provider

**WHY_STATIC**: The algorithm/authority/field comparison is not selected in current source-bound contract.

**WHY_NOT_IMPLEMENTATION_PROOF**: Writing code would require choosing the missing rule first.

**WHY_NOT_BUILD_PROOF**: Binary/hash/ABI measurements cannot choose the rule.

**WHY_NOT_RUNTIME_PROOF**: A runtime observation cannot establish an unspecified acceptance rule.

**MINIMUM_NEXT_ACTION**: Pin pg_stat_get_activity native visibility implementation and derive minimal-authority complete cross-role census for six selected columns.

### N1-READER-PREPARSE-GATE

**MISSING_STATIC_DECISION**: Select earliest frontend packet enforcement entrypoint and exact fixed statement/parameter state machine before parse/type/planner effects. Snapshot byte preparse gate is separately specified.

**SOURCE_DEPENDENCY**: catalog-reader.json#/SQL_transport; scripts/validation/package_0090_native_health_qualification/login.c:56-57,91-92

**WHY_STATIC**: The algorithm/authority/field comparison is not selected in current source-bound contract.

**WHY_NOT_IMPLEMENTATION_PROOF**: Writing code would require choosing the missing rule first.

**WHY_NOT_BUILD_PROOF**: Binary/hash/ABI measurements cannot choose the rule.

**WHY_NOT_RUNTIME_PROOF**: A runtime observation cannot establish an unspecified acceptance rule.

**MINIMUM_NEXT_ACTION**: Select earliest frontend packet enforcement entrypoint and exact fixed statement/parameter state machine before parse/type/planner effects. Snapshot byte preparse gate is separately specified.

### N1-CATALOG-EFFECT-GRAPH

**MISSING_STATIC_DECISION**: Complete NATIVE-only source-to-edge callable/default/owner/effect constructors or finite rejection rule for unsupported type/default/body paths; keep 12 distinct edge kinds.

**SOURCE_DEPENDENCY**: catalog-security-predicates.json; catalog-projection.json pg_proc/pg_type; provider/acl.c and aclchk.c

**WHY_STATIC**: The algorithm/authority/field comparison is not selected in current source-bound contract.

**WHY_NOT_IMPLEMENTATION_PROOF**: Writing code would require choosing the missing rule first.

**WHY_NOT_BUILD_PROOF**: Binary/hash/ABI measurements cannot choose the rule.

**WHY_NOT_RUNTIME_PROOF**: A runtime observation cannot establish an unspecified acceptance rule.

**MINIMUM_NEXT_ACTION**: Complete NATIVE-only source-to-edge callable/default/owner/effect constructors or finite rejection rule for unsupported type/default/body paths; keep 12 distinct edge kinds.

### N1-READER-EFFECTIVE-ACL

**MISSING_STATIC_DECISION**: Enumerate exact reader CONNECT/USAGE/SELECT/EXECUTE effective allowlist with PUBLIC/default/owner/SET/INHERIT/ADMIN and bootstrap effects; prove no stronger reachable authority.

**SOURCE_DEPENDENCY**: catalog-reader.json#/grants; catalog-security-predicates.json; provider/acl.c and aclchk.c

**WHY_STATIC**: The algorithm/authority/field comparison is not selected in current source-bound contract.

**WHY_NOT_IMPLEMENTATION_PROOF**: Writing code would require choosing the missing rule first.

**WHY_NOT_BUILD_PROOF**: Binary/hash/ABI measurements cannot choose the rule.

**WHY_NOT_RUNTIME_PROOF**: A runtime observation cannot establish an unspecified acceptance rule.

**MINIMUM_NEXT_ACTION**: Enumerate exact reader CONNECT/USAGE/SELECT/EXECUTE effective allowlist with PUBLIC/default/owner/SET/INHERIT/ADMIN and bootstrap effects; prove no stronger reachable authority.

### N1-SNAPSHOT-MUTATION-BARRIER

**MISSING_STATIC_DECISION**: Define catalog mutator exclusion token owner/acquire/release/ABA/loss states and ordering with native registry publication plus independent witness.

**SOURCE_DEPENDENCY**: snapshot-consistency.json#/CATALOG_REVISION_OR_EQUIVALENT_RULE and /SNAPSHOT_BEGIN_RULE

**WHY_STATIC**: The algorithm/authority/field comparison is not selected in current source-bound contract.

**WHY_NOT_IMPLEMENTATION_PROOF**: Writing code would require choosing the missing rule first.

**WHY_NOT_BUILD_PROOF**: Binary/hash/ABI measurements cannot choose the rule.

**WHY_NOT_RUNTIME_PROOF**: A runtime observation cannot establish an unspecified acceptance rule.

**MINIMUM_NEXT_ACTION**: Define catalog mutator exclusion token owner/acquire/release/ABA/loss states and ordering with native registry publication plus independent witness.

### N1-CREDENTIAL-CLASS-INVENTORY

**MISSING_STATIC_DECISION**: Classify dedicated READ_PROXY SQL authentication and bind purpose-specific delivery/custody/revocation references exhaustively; distinguish POSTMASTER endpoint from signing keys.

**SOURCE_DEPENDENCY**: credential-classes.json; credential-custody.json; catalog-reader.json#/SQL_transport

**WHY_STATIC**: The algorithm/authority/field comparison is not selected in current source-bound contract.

**WHY_NOT_IMPLEMENTATION_PROOF**: Writing code would require choosing the missing rule first.

**WHY_NOT_BUILD_PROOF**: Binary/hash/ABI measurements cannot choose the rule.

**WHY_NOT_RUNTIME_PROOF**: A runtime observation cannot establish an unspecified acceptance rule.

**MINIMUM_NEXT_ACTION**: Classify dedicated READ_PROXY SQL authentication and bind purpose-specific delivery/custody/revocation references exhaustively; distinguish POSTMASTER endpoint from signing keys.

### N1-QUALIFICATION-INPUT-RESOLUTION

**MISSING_STATIC_DECISION**: Replace whole-file pointers and repeated validation prose with exact schema field paths and comparisons for every Boolean qualification input.

**SOURCE_DEPENDENCY**: qualification-inputs.json#/participants; participant-qualification.json#/matrix

**WHY_STATIC**: The algorithm/authority/field comparison is not selected in current source-bound contract.

**WHY_NOT_IMPLEMENTATION_PROOF**: Writing code would require choosing the missing rule first.

**WHY_NOT_BUILD_PROOF**: Binary/hash/ABI measurements cannot choose the rule.

**WHY_NOT_RUNTIME_PROOF**: A runtime observation cannot establish an unspecified acceptance rule.

**MINIMUM_NEXT_ACTION**: Replace whole-file pointers and repeated validation prose with exact schema field paths and comparisons for every Boolean qualification input.

### N1-SUBSTITUTION-STATIC-WITNESSES

**MISSING_STATIC_DECISION**: Provide attack-specific typed baseline, mutation, witness field path and selected evaluation for remaining 217 substitution cases.

**SOURCE_DEPENDENCY**: substitution-witnesses.json#/cases

**WHY_STATIC**: The algorithm/authority/field comparison is not selected in current source-bound contract.

**WHY_NOT_IMPLEMENTATION_PROOF**: Writing code would require choosing the missing rule first.

**WHY_NOT_BUILD_PROOF**: Binary/hash/ABI measurements cannot choose the rule.

**WHY_NOT_RUNTIME_PROOF**: A runtime observation cannot establish an unspecified acceptance rule.

**MINIMUM_NEXT_ACTION**: Provide attack-specific typed baseline, mutation, witness field path and selected evaluation for remaining 217 substitution cases.

## Recovery and verification

Original preflight:99 authorized pre-existing untracked files. First resume:113 total/14 partial files. Latest resume:115 total/16 R5N.2 artifacts, including recovery audit and fresh independent review. Every existing artifact was read; Python syntax and JSON were parsed before execution. No unauthorized path, tracked change or staged file was found. Original hashes and full path classification are preserved in recovery-audit.json. Three existing files were repaired; no file was deleted/rejected.

Canonical V043 SHA256(Git LF): `007ab786c417c41e2b1702ebf3852cb70ff5c142fa3fde195385e04c6dde8b4a`; Flyway CRC32: `1279591798`; 55000 fence unchanged and before search_path. Negative execution statements describe this task and retained prior records; no forensic claim about unobserved actors.

REMOTE_TRACKING_REF_HEAD is local only; REMOTE_NETWORK_VERIFIED=NO. No network qualification was performed.

Read-only verifier: `python -B docs/evidence/package-0090-B01-v2-native-static-closure-r5n2/verify.py`. Integrity/static-vector checks validate bytes, scope, hashes and inventories; they do not approve architecture. derive.py creates candidate data; finalize.py applies the independently reviewed verdict. Re-running derive.py alone replaces final metadata with candidate defaults and must not be interpreted as accepted closure.

## Final receipt

```text
TWELVE_BLOCKERS_REQUIRED=12
TWELVE_BLOCKERS_CLOSED=2
TRUE_STATIC_DESIGN_FAILURES_REMAINING=10
NEW_BLOCKER_DISCOVERED=NO
NATIVE_PARTICIPANTS_REQUIRED=7
NATIVE_PARTICIPANTS_FULLY_DESIGNED=0
UNRESOLVED_NATIVE_WORK_ANCHORS=0
GENERIC_PROCESS_SUBSTITUTIONS=0
NATIVE_MESSAGE_ABI_COMPLETE=YES
NATIVE_GENERATION_PROTOCOL_COMPLETE=YES
NATIVE_REGISTRY_PROTOCOL_COMPLETE=YES
NATIVE_COMPLETED_WORK_PROTOCOL_COMPLETE=YES
NATIVE_INDEPENDENCE_MODEL_COMPLETE=NO
NATIVE_CUSTODY_MODEL_COMPLETE=NO
NATIVE_CATALOG_MODEL_COMPLETE=NO
NATIVE_SUBSTITUTION_MATRIX_COMPLETE=NO
CATALOG_SOURCE_RELATIONS_TOTAL=19
CATALOG_PROJECTED_FIELDS_TOTAL=146
CATALOG_FIELDS_WITH_CODEC=146
CATALOG_SECURITY_PREDICATES_TOTAL=26
CATALOG_GRAPH_EDGE_TYPES_TOTAL=12
CATALOG_UNRESOLVED_FIELDS=5
CATALOG_UNRESOLVED_PREDICATES=2
CATALOG_MISSING_FIELD_FAMILIES=2
CREDENTIAL_CLASSES_TOTAL=3
UNCLASSIFIED_CREDENTIAL_REFERENCES=AT_LEAST_1_NOT_EXHAUSTIVELY_ENUMERATED
SUBSTITUTION_CASES_TOTAL=350
SUBSTITUTION_CASES_WITH_STATIC_WITNESS_CONTRACT=133
UNRESOLVED_SUBSTITUTION_CASES=217
NATIVE_ISOLATION_RULES_TOTAL=240
NATIVE_CUSTODY_RULES_TOTAL=7
NATIVE_INDEPENDENCE_RELATIONS_TOTAL=21
NATIVE_UNRESOLVED_ISOLATION_RULES=240
NATIVE_UNRESOLVED_CUSTODY_RULES=7
NATIVE_UNRESOLVED_INDEPENDENCE_RELATIONS=21
NATIVE_INDEPENDENT_REVIEW=FAIL
V2_NATIVE_STATUS=BLOCKED
BLOCKER_COUNT_FOR_V2_NATIVE=10
RESIDUAL_NATIVE_BLOCKERS=['N1-LABEL-IR-ATOMICITY', 'N1-SCALAR-SYSCALL-IR', 'N1-SOURCE-STATS-VISIBILITY', 'N1-READER-PREPARSE-GATE', 'N1-CATALOG-EFFECT-GRAPH', 'N1-READER-EFFECTIVE-ACL', 'N1-SNAPSHOT-MUTATION-BARRIER', 'N1-CREDENTIAL-CLASS-INVENTORY', 'N1-QUALIFICATION-INPUT-RESOLUTION', 'N1-SUBSTITUTION-STATIC-WITNESSES']
NEXT_EXECUTED=False
NEXT_GATE=R5N.2 exact residual static decisions
IMPLEMENTATION_PERFORMED=NO
NATIVE_BUILD_PERFORMED=NO
NATIVE_RUNTIME_EXECUTED=NO
SQL_EXECUTED=NO
DATABASE_CONTACTED=NO
V043_EXECUTED=NO
B02_EXECUTED=NO
N1_LABEL_IR_ATOMICITY=OPEN
N1_SCALAR_SYSCALL_IR=OPEN
N1_SOURCE_STATS_VISIBILITY=OPEN
N1_READER_PREPARSE_GATE=OPEN
N1_CATALOG_EFFECT_GRAPH=OPEN
N1_READER_EFFECTIVE_ACL=OPEN
N1_CONFIG_SECRET_EXCLUSION=CLOSED
N1_SNAPSHOT_MUTATION_BARRIER=OPEN
N1_CREDENTIAL_CLASS_INVENTORY=OPEN
N1_QUALIFICATION_INPUT_RESOLUTION=OPEN
N1_SUBSTITUTION_STATIC_WITNESSES=OPEN
N1_CATALOG_CODEC_TYPE_TABLE=CLOSED
BRANCH=checkpoint/package-0090-cloud-handoff
BASELINE_HEAD=cbc284f62d9bd09b7169b55c8d66a3c51a68c6cb
CURRENT_HEAD=cbc284f62d9bd09b7169b55c8d66a3c51a68c6cb
REMOTE_TRACKING_REF_HEAD=cbc284f62d9bd09b7169b55c8d66a3c51a68c6cb
REMOTE_NETWORK_VERIFIED=NO
TRACKED_DIRTY_COUNT=0
STAGED_COUNT=0
UNTRACKED_BEFORE_INTERRUPTION=99
UNTRACKED_AT_RESUME=115
UNAUTHORIZED_UNTRACKED_COUNT=0
PARTIAL_R5N2_FILES_RECOVERED=16
PARTIAL_R5N2_FILES_REPAIRED=3
PARTIAL_R5N2_FILES_REJECTED=0
CANONICAL_V043_MUTATED=NO
CANONICAL_V043_EXECUTED=NO
PRODUCTION_CONTACTED=NO
GIT_ADD=NO
COMMIT=NO
PUSH=NO
PR=NO
CATALOG_FIELDS_WITHOUT_CODEC=0
NATIVE_CUSTODY_CLASS_FIELD_DECLARATIONS=60
UNTRACKED_FINAL=121
TESTS_DISTINCT=5128
TEST_FAILURES=0
```

Next action: close only the ten exact static residuals above, then rerun independent review. No implementation/build/runtime/database gate is executed or authorized by this receipt.
