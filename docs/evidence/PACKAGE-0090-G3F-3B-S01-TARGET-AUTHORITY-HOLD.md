# Package 0090 — approved connection authority and next target boundary

Date: 2026-10-03 (America/Sao_Paulo).
Branch: checkpoint/package-0090-cloud-handoff.
Entry baseline: b3833920870975d85181b9f4f2961b58468a9ba5.
After fetch: LOCAL_HEAD=REMOTE_HEAD=expected_head; WORKTREE=CLEAN.

The user's technical governance approval closes the previous connection-read
hold. ADR/SPEC now authorize exactly six A SELECT columns on
public.integration_connection for S01_ONLY/BOUND_CONNECTION_READINESS, private
predicates only. Existing organization_id/status consumer traceability extends
to S01; no organization column is added. V043 has exactly those six new grants.
The actual parsed physical inventory equals the complete normative set: 1026,
with no missing/extra privilege. Q's embedded deployment column privilege and
projection inventories were regenerated and are independently checked as exact
sets by the source validator, including duplicate rejection.

The inline organization and two connection predicates are recorded in
[machine evidence](PACKAGE-0090-G3F-3B-S01-READINESS-AUTHORITY.json) and
[offline predicate review](../../scripts/validation/package_0090_s01_readiness.py).
They derive selectors from header_record only; exact identity cardinality and
provider/kind/ACTIVE/version predicates reject missing, foreign, suspended,
mismatched, null and ambiguous rows. Counting only eligible matches would hide
an ambiguous identity with one valid and one invalid row; these candidates count
the bound identity first and require its single row to satisfy all attributes.
The Q delegation candidate has seven explicitly cast original parameters plus
the exact empty bytea sentinel. It is not invoked or installed as a success stub.

## New genuine authority boundary

SPEC8/16 requires S01 to prove target readiness. SPEC253 requires preservation
of existing target joins. The current producer is
[PostgresCeremonyComposition.runtime.matchesTarget](../../applications/command-authority-ceremony/src/main/kotlin/io/flooow/ceremony/PostgresCeremonyComposition.kt).
It joins bound Omie base/V3 evidence, registry, promotion and Mercado Livre
source observation. A's existing target columns are limited to S03/RECON.evidence.
A has zero SELECT columns on the Mercado Livre source observation relation.
Neither the approved six connection columns nor the existing organization pair
provides the missing source-reference fact. Q has no target/economic read route;
P takes locks and provides no target proof; Z compares authority intent/receipts.
Frozen mutation functions are not a read-only S01 target oracle.

The machine audit extracts the exact producer SQL and its column references.
An explicitly synthetic differential witness changes only the ML source
external_order_ref. The original producer query changes true to false, while
every A-authorized row projection remains identical. This proves an observation
gap under the retained A inventory, not PostgreSQL runtime/noninterference.
The disposable in-memory SQLite evaluation is local test execution only;
it is not a protected database connection or PG18 semantic/ACL proof.

Exact proposed technical handoff, **not approved or granted**:

| Owner | Relation | Columns | Consumer/purpose | Projection |
| --- | --- | --- | --- | --- |
| A | public.integration_mercado_livre_order_source_observation | organization_id, connection_id, capability, input_progress_version, record_ordinal, external_order_ref | S01_ONLY / frozen matchesTarget bound join | Private predicates only |
| A | Existing registry/promotion/Omie base/V3 columns actually referenced by matchesTarget | Already granted; exact extracted producer references in machine audit | Extend S03 traceability to S01 bound target predicate | Private predicates only |

This would add six physical SELECT grants (1026 -> 1032) if independently
approved, plus narrowly scoped consumer traceability. No such amendment has
been made to ADR/SPEC and none of these grants has been added. No caller target
selectors, metadata output, whole-table grants, lock/write privilege or new
helper/service authority is proposed.

## Validation and limits

118 offline tests PASS: 96 retained, 18 S01 predicate/authority tests and four
new Q deployment-inventory negative tests. Both connection slots independently
instantiate every requested negative; SQL predicate behavior is checked against
an independent relational oracle. AST review confirms exact six-column reads,
header-only selectors, a single boolean projection and no lock/write clause.
Source parsing remains pglast 7.10 / PostgreSQL17 grammar, not PG18 runtime proof.
All42 immutable migration hashes pass; V043's first execution interlock remains.

Two retained-fixture limitations were exposed without rewriting its bytes:
the ML connection provider is `mercado-livre`, whereas the frozen production
producer uses `br.com.mercadolivre`; the retained target's external-order join
does not satisfy the existing matchesTarget query. The witness is explicitly
synthetic and does not promote the retained fixture to runtime-positive proof.
Connection version1 is the retained fixture's frozen expected version, not a
general live-version fallback or a new authority to adopt arbitrary versions.

S01_IMPLEMENTED=NO. PUBLIC_WRAPPERS_IMPLEMENTED=NO.
EXECUTOR_SIGNATURES_IMPLEMENTED=NO. S01_Q_SENTINEL_DELEGATION=CANDIDATE_ONLY.
UNRESOLVED_AUTHORITY_BLOCKER_COUNT=1; full source closure also retains its three
implementation categories (wrappers/guards, transports/goldens, EXECUTE closure).
No S01 readiness PASS or authenticated receipt is claimed. The authorized
connection amendment is checkpointable; dependent full S01 and remaining
wrappers stop at this genuine target authority boundary.

No V001-V042 mutation, interlock removal, protected PostgreSQL connection,
production policy/crypto/login provisioning, G3G, main merge/push or secret
exposure occurred. No unrelated catalog-compiler file was modified/staged.
NEXT_GATE=G3F.3B_S01_TARGET_CONSUMER_AUTHORITY.
