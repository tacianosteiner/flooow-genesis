# Package 0090 isolated rehearsal handoff — preparation only

Date: 2026-10-03 (America/Sao_Paulo).

Superseding fixture status: independent TTL approval, complete retained normative
ML/Omie evidence and policy/manifest/binding/catalog/preflight Python/JVM golden
agreement are recorded in
[normative fixture closure](PACKAGE-0090-G3F-3B-NORMATIVE-EVIDENCE-CLOSURE.md) and
[catalog golden closure](PACKAGE-0090-G3F-3B-CATALOG-GOLDEN-CLOSURE.md).
Entry condition1 below is satisfied. Internal P has bounded source review;
Q/Z/public wrappers/private decision transport/full EXECUTE closure remain
incomplete. The immediate gate is G3F.3B_REMAINING_Q_Z_AND_PUBLIC_WRAPPERS.
The earlier fixture-approval hold wording below is historical. No rehearsal
execution authority or complete implementation is inferred from this update.

REHEARSAL_PREPARED=YES. REHEARSAL_EXECUTION_AUTHORIZED=NO_BY_THIS_ARTIFACT.
REAL_FIELD_PROOF=HOLD. G3G_AUTHORIZED=NO.

This is the exact downstream rehearsal boundary. It does not authorize execution
of the incomplete V043 candidate, extension installation, role provisioning or
any protected database mutation. The current immediate next gate is
G3F.3B_FIXTURE_APPROVAL_AND_GOLDEN_CLOSURE, not database rehearsal.

## Entry conditions

1. Record the explicit independent approval required by SPEC 21.2 for the
   replacement normative fixture's tag28 `preflight_receipt_ttl` and tag29 maximum,
   both positive int8 microseconds with actual <= maximum. This approval concerns
   synthetic codec fixtures only; no production policy value or provisioning is
   inferred. Preserve all original fixture fields and negative-test semantics.
2. Implement the 18 exact public signatures and P/Q/Z, complete canonical codecs,
   R/M/C/state/deadline/policy guards and exact frozen/internal EXECUTE grants.
   Do not introduce another function/helper or widen the authorized surface.
3. Produce independently agreeing JVM/reference complete bytes and digests for
   binding, slots, 29-field policy, history, ACL and nine-field preflight/HMAC.
   Include malformed/null/duplicate/order/overflow/expiry and all38-field binding
   mutations. Record approval/provenance; the current single-source column ACL
   checker is not that independent codec evidence.
4. Review source and record V043_IMPLEMENTATION_AND_CONTRACT_CLOSURE=PASS.
   Remove the incomplete-source interlock only in that recorded closure change.
5. Obtain separate bounded isolated-rehearsal execution authorization and the
   existing approved crypto/admin/default/schema prerequisites. No authorization
   is inferred from this document or from a source PASS.

## Isolation requirements

Use a newly created disposable PostgreSQL18 cluster with a unique package-run
identity, no protected volume, no restored data, no host database/socket access,
no protected endpoint or credentials and no provider/network field execution.
Validate those properties before any SQL. A host-supplied connection string or an
unverified existing container is insufficient isolation evidence. Do not reuse
production role credentials. No secret or proof material enters the repository
or captured logs.

Administrative fixtures/extension installation must be separately authorized
only for that disposable cluster. Version-pin pgcrypto1.4 and mac32 extension1.0;
verify the approved comparator binary identity and independent pgcrypto binary
provenance, postgres ownership, private schema, exact Q-only grants and safe
actual-creator/ADMIN defaults. Installation alone never establishes READY.

## Exact rehearsal sequence and outputs

| Step | Experiment | Required result |
| --- | --- | --- |
| R01 | Build/replay immutable V001-V042 under the approved isolated migration identity; retain complete Flyway six-field manifest | Chain PASS; frozen checksums unchanged |
| R02 | Run V043 with missing/wrong ADMIN, unsafe attributes/membership/defaults, missing/mismatched crypto, PUBLIC grants and unsafe schema in separate disposable transactions | Every mismatch denied with no committed partial DDL |
| R03 | Run the complete approved V043 with all prerequisites; policy storage remains empty | Atomic schema PASS; zero policy rows, zero service logins/readiness activation created by V043 |
| R04 | Verify all14 controls, exact21 function signatures/owners/ACLs/proconfig/volatility/input/output vectors, seven activation SELECT grants and complete creator/member inventories | Exact approved scope; no PUBLIC, raw service access, generic DML, extra helper, membership or grant option |
| R05 | Attempt all18 operational signatures and P/Q/Z with missing/invalid/not-yet-effective policy | Deny; no effect or partial receipt |
| R06 | Separately provision only approved isolated synthetic policy/binding/identity fixtures; record exact commit/audit evidence | Exact immutable row/references; no production authority or READY inferred |
| R07 | Exercise all18 two-organization/four-slot cases, NULL/shape/cast/overload/PUBLIC and wrong-identity cases | Uniform foreign-scope denial before disclosure/effect |
| R08 | Exercise exact original receipt expiry, future issuance, policy/key/ACL/history/incarnation drift and lost-ack claim retry | No renewal, expiry bypass, live drift adoption or ownership sharing |
| R09 | Exercise one delivery attempt, acknowledgment-loss/restart/report repeats, durable admission, operation-time possession, generation fencing and expiry/revocation/JCA rollback | No redelivery, inferred possession, revived admission, partial canonical effect or autonomous recovery |
| R10 | Auditor read-only terminal/revoked/expired inspection/reconciliation plus complete history/null metadata; separate administrative outcome recording | No auditor DML; exact structural outcomes remain distinct from ceremony success |

Capture sanitized step results, SQLSTATE/category, catalog/ACL inventories,
complete history and independently checked fixture digests. Record the isolated
cluster identity and absence of protected mutations. An unknown/missing result is
HOLD, never PASS. Do not run G3G or field proof as part of this rehearsal.

## Executable offline entry check available now

These commands parse/check source only and never connect to a database. Use an
isolated parser dependency directory, not an application dependency installation:

```powershell
$package0090Parser = Join-Path $env:TEMP 'flooow-0090-parser'
python -m pip install --target $package0090Parser pglast==7.10
python scripts/validation/package_0090_source_gate.py --parser-path $package0090Parser
python scripts/validation/package_0090_source_gate.py --parser-path $package0090Parser --closure
```

The prerequisite invocation currently succeeds. `--closure` currently exits1
and reports HOLD; it is a denial check, not a closure certification mechanism.
There is intentionally no database execution command while entry conditions
remain unsatisfied. The implementation/review gate must supply the exact isolated
runner only after all entry conditions are recorded; no broad production runner
is reused.
