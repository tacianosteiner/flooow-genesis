# Package 0090 G3F.3B autonomous execution evidence

Date: 2026-10-03 (America/Sao_Paulo). This records source work only.

## Superseding retained-evidence and internal-P checkpoints

The independent TTL approval and complete retained test-only evidence fixture
are recorded. Python/JVM agree on full policy/evidence/manifest/binding/slot,
history/eight conceptual ACL/preflight/HMAC bytes and digests. The missing
ML/Omie normative fixture boundary is resolved by the later explicit authority;
it is no longer a blocker or approval request. The report below is historical.

Current source adds only the exact internal P signature and its two EXECUTE
grants; bounded source/security/column/lock review passes.58 offline tests pass.
All42 frozen migrations remain unchanged. The four implementation categories
remain incomplete: public wrappers/Q/Z, full operational guards, wrapper/private
decision transport goldens and full transitive EXECUTE closure. No new authority
boundary is asserted for this ordinary remaining implementation work. V043's
first unconditional interlock is retained. No database/production mutation,
G3G,merge or main push occurred.

Evidence: [normative retained fixture](PACKAGE-0090-G3F-3B-NORMATIVE-EVIDENCE-CLOSURE.md),
[catalog/receipt goldens](PACKAGE-0090-G3F-3B-CATALOG-GOLDEN-CLOSURE.md),
[internal P source review](PACKAGE-0090-G3F-3B-INTERNAL-P-SOURCE-REVIEW.md).
NEXT_GATE=G3F.3B_REMAINING_Q_Z_AND_PUBLIC_WRAPPERS.

## Status and authority

Repository baseline: tacianosteiner/flooow-genesis.
Branch: checkpoint/package-0090-cloud-handoff.
Verified initial HEAD: 19131bb9cd655312252c8c83f0f78e7c0742274f.
Initial worktree: clean. The user's bounded V043 source implementation authority
was applied; historical ADR/SPEC statements about earlier implementation holds
were not reinterpreted as runtime authorization.

CURRENT_GATE=G3F.3B_FIXTURE_APPROVAL_AND_GOLDEN_CLOSURE_HOLD
GATES_COMPLETED=BASELINE_VERIFICATION,SOURCE_PREREQUISITE_ALIGNMENT,OFFLINE_SOURCE_VALIDATION,ISOLATED_REHEARSAL_PREPARATION
V043_IMPLEMENTATION_AND_CONTRACT_CLOSURE=HOLD
V043_IMPLEMENTED=PARTIAL_SOURCE_ONLY
V043_EXECUTED=NO
UNRESOLVED_BLOCKER_COUNT=5
PROTECTED_DATABASE_MUTATION=NO
DATABASE_CONNECTION_ATTEMPTED=NO
FIELD_PROOF_EXECUTION_AUTHORIZED=NO
REAL_FIELD_PROOF=HOLD
G3G_AUTHORIZED=NO
NEXT_GATE=G3F.3B_FIXTURE_APPROVAL_AND_GOLDEN_CLOSURE

These micro-gate names describe this bounded work; they introduce no new
architectural approval, subsystem or execution authority. Source prerequisite
alignment PASS is not full migration implementation or installed/catalog proof.

## Gate evidence

| Micro-gate | Exact finding/dependency | Authorized action | Validation/result | Determined next step |
| --- | --- | --- | --- | --- |
| Baseline verification | Exact requested branch/commit; clean worktree | Read repository and accepted amendments | PASS | Inspect draft against SPEC21-25 |
| Source prerequisite alignment | Draft creates ADMIN NOINHERIT; policy activation absent; Q preexisting approved crypto ACLs rejected; safe default-ACL ownership rejected | Correct those source representations, add incomplete-candidate execution fence and inspection-only prerequisites | PASS for the bounded source representation; no execution | Validate syntax and exact normative column ACL inventory |
| Offline source validation | Actual grant set and incomplete-source status must be proven rather than inferred | Add pinned parser/source checker and negative source tests | PASS: 1,094 SQL statements,11 PL/pgSQL blocks,14 controls,1,020 exact physical column grants;21 tests | Assess full closure dependencies and approved fixture evidence |
| Isolated rehearsal preparation | Full source closure and separate isolated prerequisites not satisfied | Record isolation/entry conditions, R01-R10 and source-only executable checks | PREPARED; execution HOLD | Fixture approval/golden closure handoff |

## Changed source scope

- V043 remains an **incomplete candidate**. Its first unconditional DO raises
  SQLSTATE55000 before any role, DDL, grant or other effect. It must not be run by
  Flyway; this fence can be removed only with recorded full source closure.
- ADMIN is a required separately provisioned NOLOGIN/INHERIT identity. Missing
  ADMIN or unsafe attributes/membership/ownership/ACLs deny; V043 neither creates
  nor repairs it. The only accepted preexisting application-schema grant is
  non-grantable public USAGE.
- Inspect actual creator and existing Package owner defaults across all six
  object kinds and every actual schema. Missing global defaults are evaluated
  using PostgreSQL hard-wired defaults, including the sequence-kind mapping
  from pg_default_acl S to acldefault s. Unsafe defaults deny; no default repair.
  Default-ACL ownership is exempted from the empty-owner adoption rejection only
  in this database and only after the separate default inspection. Unknown
  cross-database dependencies remain denied.
- Q's exact preinstalled binary HMAC/comparator EXECUTE and private-schema USAGE
  are accepted only without grant option. Other Q ownership/application ACLs
  remain denied. Inspect required extension versions, postgres ownership,
  member-function namespace/current ACLs and exact two function properties;
  never install, relocate, repair or grant crypto. This inspection does **not**
  prove approved binary hashes/provenance or a complete independently approved
  member inventory; those remain separate deployment evidence.
- Add a trusted transaction-local search path, direct postgres/PG18/UTF8
  prerequisites and denial of PUBLIC CREATE on public. No persistent runtime
  setting or global schema/default privilege is changed by this source.
- Add `offline_deadline_policy.effective_from timestamptz(6) NOT NULL`, no DEFAULT,
  finite-instant CHECK and exactly seven read-only activation column grants.
  No policy/TTL/version/activation/readiness/service-login values are seeded.
  The complete29-tag validator and operational policy guards remain unimplemented.
- ADR/SPEC and V001-V042 were not amended. No launcher/domain/shared-role change.

## Validation and its limits

[Machine-readable source evidence](PACKAGE-0090-G3F-3B-SOURCE-VALIDATION.json)
records the source/SPEC hashes, all42 immutable migration hashes, grant counts
and five unresolved closure requirements. Hashes compare canonical Git file
bytes with line endings normalized; they are not a new Flyway runtime manifest.

The source checker independently extracts the accepted SPEC22.4 column matrix
and compares it with parsed SQL, including all seven SPEC25 activation reads.
Negative tests reject PUBLIC/whole-table/grant-option/extra/duplicate/missing
grants, auditor possession reads and activation writes, policy seeding,
crypto installation, unauthorized ADMIN creation/attributes, implicit or wrong
precision activation, live roles/domain effects hidden in DO, dynamic SQL,
frozen-table DDL and removal of the first unconditional interlock.

Parser: isolated pglast7.10, using PostgreSQL17 grammar. Both outer SQL and
PL/pgSQL syntax were parsed, including embedded precondition SQL. This is **not**
PostgreSQL18 semantic, execution, lock, ACL/current-catalog or installed proof.
The21 source tests are not the required18-signature/two-organization runtime
test suite. No application build/runtime test was represented as SQL proof.
`git diff --check` passes. No database connection, extension installation,
role/privilege mutation, G3G, field proof, merge or main push occurred.

Technical reference checks used primary PostgreSQL documentation/source:
[PG18 default ACL catalog](https://www.postgresql.org/docs/18/catalog-pg-default-acl.html),
[PG18 ACL functions](https://www.postgresql.org/docs/18/functions-info.html),
and [pgcrypto frozen HMAC definition](https://raw.githubusercontent.com/postgres/postgres/REL_18_STABLE/contrib/pgcrypto/pgcrypto--1.3.sql).
These support mechanics only; the repository ADR/SPEC supplies authority.

## Five unresolved closure requirements

1. The18 public wrappers and three existing P/Q/Z capabilities are absent.
2. Operational bound-policy/activation/29-field and remaining R/M/C guards are
   absent; schema/column grants alone cannot enforce them.
3. Complete canonical codecs and independently agreeing full golden evidence
   are absent; the inline slot bytes are not the full required evidence set.
4. Exact frozen/internal capability EXECUTE ACL closure is absent. Column ACL
   equality does not prove owner transitive authority.
5. SPEC21.2 explicitly says historical fixtures **“require an explicitly
   approved fixture TTL/maximum before generating new golden evidence.”** The
   amended fixture has no approved tag28/tag29 numbers in this checkout. Neither
   existing deadlines, production defaults, old27-tag vectors nor model-selected
   values supply that approval.

Requirements1-4 are pending implementation/evidence, not requests for CEO
technical decisions. Requirement5 is the immediate non-deterministic approval
dependency for the mandatory replacement golden fixture. Multiple bounded
values satisfy the architecture; no single pair follows from the existing
invariants. Selecting/approving one autonomously would exceed the permitted
deterministic ADR/SPEC clarification. The work stops at this explicit evidence
boundary without choosing values, widening authority or claiming closure.
Production numeric policy provisioning is a later separate requirement, **not**
a blocker to permitted schema creation under SPEC25.

## Determined next gate and handoff

G3F.3B_FIXTURE_APPROVAL_AND_GOLDEN_CLOSURE requires the existing independent
technical governance process to record the exact synthetic fixture pair,
approval identity/provenance and newly derived complete fixture bytes/digests.
No business/product choice or production policy is requested here. Do not
reinterpret this handoff as an approval or infer a fixture from the live server.

After that evidence is accepted, resume the authorized V043 implementation and
review; retain the interlock until complete source closure. The
[isolated rehearsal handoff](PACKAGE-0090-G3F-3B-ISOLATED-REHEARSAL-HANDOFF.md)
records exact entry conditions, isolation evidence and required R01-R10 outputs.
It remains preparation only. Protected databases and G3G remain excluded.
