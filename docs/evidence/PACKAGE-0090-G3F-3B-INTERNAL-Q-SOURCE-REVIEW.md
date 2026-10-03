# Package 0090 internal Q bounded source review

Date: 2026-10-03 (America/Sao_Paulo).
Gate: G3F.3B_INTERNAL_Q_AND_PREFLIGHT_IMPLEMENTATION.
Result: PASS_BOUNDED_STATIC. This is not installed PostgreSQL/crypto proof.

Initial branch: checkpoint/package-0090-cloud-handoff. After fetching origin,
local and remote HEAD both equaled c2ecffec80e21af2734bb6f3ab1b84dc82519de6;
the initial worktree was clean.

Q has the exact eight mandatory SPEC21.3 inputs and scalar bytea output,
STABLE SECURITY DEFINER, CALLED ON NULL INPUT, fixed pg_catalog,pg_temp path,
and flooow_offline_readiness_owner ownership. PUBLIC is revoked; only A/E
receive non-owner EXECUTE. Exact public-schema USAGE for Q/A/E is authored.
Private crypto schema USAGE and the exact HMAC/comparator EXECUTE remain
inspection-only preinstalled prerequisites, never installed/repaired here.

The independent slot guard checks all four bound role OIDs/names, attributes
and zero memberships. session_user selects AUDITOR versus EXECUTOR; no route
argument exists. AUDITOR requires the empty sentinel and read-only repeatable
read. EXECUTOR requires a nonempty original receipt and read committed. Q
matches the immutable header binding tuple/fingerprint, as R defines in SPEC2;
it does not acquire forbidden domain columns to recompute the whole38-field
binding. The authorized full canonical consumers retain that responsibility.

Both routes validate the exact29-field active bound policy, digest, approved
bounds/nesting/activation, readiness/watchdog and current unique ACTIVE private
32-byte key/version/lineage. Full six-field history is encoded from live rows
without a version cap and compared byte-for-byte with the independent manifest
and expected digest. The six live ACL collections cover identities, function
metadata/types/modes/outputs/config/effective privileges, memberships, separate
whole/column grants, schemas/database and creator defaults. Protected access
to unlisted relations/columns/sequences, unsafe defaults and reachable function
extras cannot silently disappear. Actual manifests/digests are compared with
the separately approved bound expectations; no adoption of live drift occurs.

Issuance uses fresh clock_timestamp epoch microseconds and checked arithmetic
with policy tag28 (policy_values[27]); no fallback/clamp/renewal. Output is the
exact nine-field frame plus32-byte HMAC-SHA-256. Validation rejects malformed
framing/trailing bytes, stale/unknown/inactive versions, wrong MAC/scope/policy,
future issue times and expiry equality. It invokes only the approved fixed32
timing-safe comparator and accepts IS TRUE. Expiry is rederived from original
issued_at and the same policy TTL, and fresh DB time is checked again after
live readiness work. Success returns the original receipt unchanged. Claim
eligibility is independently checked without taking write locks. E must still
hold its C locks and repeat claim/time/ownership checks in S13.

Validation: 96 offline tests PASS (68 retained +28 Q tests). SQL and PL/pgSQL
parse: pglast7.10/PostgreSQL17 grammar, 1,116 statements/14 blocks. Parsed source
review finds95 Q read columns, all authorized; 1,020 exact physical column
grants and14 controls remain unchanged. Negative tests cover route, key,
MAC comparison, scope, policy/expiry, writes/locks, projections, signature
ownership and ACL/USAGE closure. A deliberately limited pure-expression AST
evaluator confirms Q's generated issuance frame against complete existing
Python/JVM preflight bytes and synthetic HMAC goldens. Receipt failure tests
use an independent normative oracle. Neither evaluator executes PL/pgSQL or
proves live ACL projection/catalog parity, timing behavior, locks or PG18
semantics. Those remain isolated runtime/deployment evidence requirements.

V001-V042 hashes are unchanged and V043's first unconditional execution
interlock remains. No DB connection, protected mutation, production policy,
live service role, crypto installation, G3G, main merge/push or field proof.

PRIMARY_GATE_UNRESOLVED_BLOCKER_COUNT=0.
Full V043 source closure still has three implementation categories: public
wrappers/guards; remaining wrapper/private commitment transport goldens; full
frozen/internal EXECUTE closure. NEXT_GATE=G3F.3B_PUBLIC_WRAPPERS_AND_GUARDS.

PostgreSQL mechanics checked against primary documentation:
[PG18 privilege inquiry functions](https://www.postgresql.org/docs/18/functions-info.html)
and [timestamp representation](https://www.postgresql.org/docs/18/datatype-datetime.html).
The repository ADR/SPEC supplies implementation authority.
