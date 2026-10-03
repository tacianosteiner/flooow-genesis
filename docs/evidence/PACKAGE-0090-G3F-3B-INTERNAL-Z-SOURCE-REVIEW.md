# Package 0090 internal Z source checkpoint

Date: 2026-10-03 (America/Sao_Paulo).

Internal Z is implemented in the interlocked V043 candidate with the exact
four-input, two-boolean TABLE signature. It uses the bound AUDITOR identity,
read-only REPEATABLE READ, current READY incarnation, bound policy activation,
full 29-field policy framing/bounds and read/watchdog wall-clock limits.
Historical mutation expiry does not prevent the authorized read route.

Private canonical operation comparisons preserve the frozen intent/receipt
functions, joins and effect-time predicates. Operation IDs, organization,
manifest, principal, connections, credential and grant derive from the header.
Credential/grant principal joins are checked before private recomputation.
Missing canonical operations return false. Query failures remain sanitized
INDETERMINATE errors. Only two aggregate booleans leave Z; the verifier is not
projected. Z takes no write locks and executes no semantic DML.

The exact six Z-related EXECUTE grants comprise A->Z and Z->the five approved
frozen helpers. PUBLIC EXECUTE is revoked, and ownership belongs exclusively to
the intent audit owner. The source gate validates definition, ownership, grants,
column reads, privileged calls, settings, output and lock boundaries independently
of the unchanged normative column matrix. Internal P review remains passing.

Validation: 68 offline tests pass, including ten Z boundary cases; SQL and
PL/pgSQL parse with pinned pglast 7.10. All 42 frozen migrations match baseline;
1,020 column grants and 14 controls remain exact. No PostgreSQL connection or
execution occurred. This is bounded static source evidence, not PostgreSQL 18
runtime, installed ACL, or full G3F.3B closure proof. Q, public wrappers, dependent
transport goldens and complete transitive authority review remain pending.

V043's first unconditional interlock remains. No production policy, live service
role, G3G, protected mutation, field proof, merge or main push is authorized or
performed. The next determined source action is internal Q readiness and its
preflight issuance/validation route.
