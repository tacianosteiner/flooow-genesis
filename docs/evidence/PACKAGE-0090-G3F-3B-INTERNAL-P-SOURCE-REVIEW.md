# Package 0090 internal P source checkpoint

Date: 2026-10-03 (America/Sao_Paulo).
Branch: checkpoint/package-0090-cloud-handoff.

INTERNAL_P_IMPLEMENTED=YES_SOURCE_ONLY
INTERNAL_P_STATIC_REVIEW=BOUNDED_PASS_NOT_RUNTIME_PROOF
INTERNAL_P_EXECUTE_ACL=EXACT_SOURCE_MANIFEST_PASS
INTERNAL_P_SECURITY_DEFINER=EXACT_OPTIONS_SOURCE_PASS
TESTS=58_PASS_OFFLINE
V043_IMPLEMENTATION_AND_CONTRACT_CLOSURE=HOLD
PROTECTED_DATABASE_MUTATION=NO
REAL_FIELD_PROOF=HOLD
NEXT_GATE=G3F.3B_REMAINING_Q_Z_AND_PUBLIC_WRAPPERS

V043 now contains only the already specified9-argument P capability, returns
one bool, VOLATILE/SECURITY DEFINER/CALLED ON NULL INPUT, fixed local
search_path=pg_catalog,pg_temp, owned by the exact P owner. PUBLIC EXECUTE is
revoked and only E receives its exact signature. P receives only the frozen
organization-lock signature, which must return true before proceeding.
No service grant, helper, role, table, membership or policy value is added.
The unconditional migration execution interlock remains the first statement.

P authenticates session_user against the canonical four-slot allocation and live
OID/name/role attributes with zero incident membership. Scope/fingerprint/
incarnation/surface must match before private principal lookup. It reads the
exact bound immutable policy row and checks full29-tag domain/count/order/
presence/type/positive-int8/maximum/nesting/overflow/trailing constraints, hash
and version agreement, effective_from and READY/watchdog eligibility. Policy
values are decoded from the approved row; no fixture TTL, GUC policy source,
session fallback or caller-selected duration is embedded in migration SQL.
Transaction isolation is inspected only to require READ COMMITTED.

The source retains lifecycle -> pointer -> attempt -> execution locks before
the existing organization FOR SHARE lock and exact bound principal FOR UPDATE.
Current generation/attempt/execution/instance/executor, OWNED, fresh possession
digest, ACTIVE lifecycle, EFFECTS_IN_PROGRESS, original ACK lineage, NOT_STARTED
reconciliation and NONE ceremony are required. Database wall clock and current
readiness/watchdog are checked again after blocking domain locks; no deadline
is changed. Errors are uniformly sanitized and no proof/digest is returned.

The pinned parser review checks all1,099 outer SQL statements and12 PL/pgSQL
blocks, preserves the full1,020-column manifest and all42 frozen migrations.
The independent source checker inspects P's embedded query ASTs: all60 observed
application read columns must be in the normative P allowlist; projections have
no wildcard, privileged calls have a closed builtin/frozen allowlist, dynamic
SQL and semantic DML/DDL are denied, lock order is exact, function ownership/
types/options/grants are exact. Negative tests reject broader reads, extra
privileged calls, GUC mutation, wrong volatility/security/strict/defaults,
dynamic SQL,DML,wildcards,PUBLIC/service grants and foreign ownership changes.

This parser/static review does not establish PostgreSQL18 operator/catalog
semantics, installed ownership/ACLs, current role identity, concurrency/time
behavior or the18-signature runtime matrix. Full explicit operator qualification,
the remaining wrappers/Q/Z, private decision commitment transport and complete
transitive EXECUTE closure remain part of full source/security review. No bounded
P result is promoted to full Package0090 closure or isolated SQL execution proof.
