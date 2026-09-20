# TASK-0165O - Governed Economic Decision Room Projection

Date: 2026-09-13
Base: `a1e580d908a49cf093e7e1511a0bcd5c048cca68`

## Delivered

Added a read-only domain projection, authority and governed-assessment-candidate seams, a separate authenticated endpoint, fail-closed runtime wiring, OpenAPI contract, and focused domain/API tests. No schema, migration, provider integration, truth store, or reconciliation engine was added.

Production deliberately reports missing assessment and authority because the repository has no governed assessment-by-case lineage source. Durable financial variance remains visible for investigation but is never relabeled as leakage.

## Proven behavior

- missing authority is `NOT_ASSEMBLED`;
- missing assessment is `BLOCKED` and retains variance with null leakage;
- unresolved, contradictory, and stale authorities make leakage `UNQUANTIFIED`;
- governed negative variance becomes `UNFAVORABLE_LEAKAGE`;
- governed positive variance becomes `FAVORABLE_VARIANCE`, not quantified leakage;
- missing expected, missing actual, and unsupported stages remain unquantified;
- mismatched reconciliation context blocks interpretation;
- authority context carries and validates typed organization, subject/case, policy, currency, and revision coordinates;
- assessment binding validates declared case/revision plus assessment context coordinates before assembly; this proves contextual equivalence only, not immutable assessment identity;
- any unquantified stage forces aggregate leakage to null, so a subtotal is never labeled total;
- organization isolation is enforced before authority reads;
- provenance contains authority, trace, policy, and ledger entry references;
- the endpoint is GET-only/no-store and performs zero repository saves;
- `/v1/reconciliation/cases` remains unchanged.
- all public enums are closed and contract-tested against OpenAPI.

## Residual architectural dependency

Immutable assessment identity is intentionally not fabricated in this slice.
The residual binding finding is:

`BLOCKED BY UPSTREAM GOVERNED ASSESSMENT IDENTITY / REVISION LINEAGE`

The Decision Room may later consume and verify that upstream lineage, but it
must not mint, reconstruct, or self-attest the identity itself.

`Context equivalence != evidence identity`.

## Safety

`Financial variance != Economic leakage`. `Missing != zero`. No identity, currency, allocation, currentness, assessment, recommendation, action, authority, execution, or causality is inferred. No provider write or historical rewrite occurs.

## Validation

- focused Decision Room domain/API hardening gate: GREEN after OpenAPI effective-graph/nullability checks and adversarial repository, assessment-source, and authority-source organization-isolation coverage;
- final post-hardening repository command: `.\gradlew.bat build --no-daemon --console=plain`;
- final post-hardening repository result: `BUILD SUCCESSFUL in 24s`;
- Gradle summary: 100 actionable tasks, 1 executed, 1 from cache, 98 up-to-date;
- tracked whitespace integrity is verified separately with `git diff --check`;
- TASK-0165O untracked source/document files are checked separately for trailing whitespace, blank-at-EOF, space-before-tab, and unresolved conflict markers.

An earlier sandboxed full-build attempt could not discover the local Docker environment. Subsequent local validation succeeded; the final post-hardening build above is the authoritative repository build result for this slice.
