# ADR-0090 — Governed raw evidence reference

Status: **design accepted for this research tranche; implementation blocked**. Date: 2026-10-12. Branch: `feature/room-v2-executive-product-evolution`. Baseline: `cbb9eca6ee56f4107f359a769b29c30d40d0cb75`.

## Problem

Room V2 can trace Decision Pressure to a loaded projected order or reconciliation case, but cannot identify the exact durable economic observation that supports a displayed claim. `sourceEvidenceVersion` is a subject-level version, not an observation identifier. The Room must not turn that version, an order ID, a case evidence-entry ID or a string reference into a fabricated raw-evidence link.

## Repository state and decision

The durable economic evidence model already has `MarketplaceEconomicEvidenceObservationId` (canonical lowercase UUID), an organization/order subject, evidence family, observation time and versioned update history. [V015](../../applications/marketplace-operations-persistence-postgres/src/main/resources/db/migration/V015__create_independent_marketplace_economic_evidence.sql) keys the identifier by `(organization_id, marketplace_order_id, observation_id)` and binds it to `evidence_version`; fact rows add family and observed time. [V018](../../applications/marketplace-operations-persistence-postgres/src/main/resources/db/migration/V018__create_marketplace_sales_intelligence_projection.sql) stores only current `source_evidence_version`, assembly policy, change checkpoint and state. The [Sales Intelligence API](../../applications/marketplace-operations-api/src/main/kotlin/io/flooow/marketplace/api/SalesIntelligenceApi.kt) serializes no observation IDs. [OpenAPI](../../applications/marketplace-operations-api/src/main/resources/openapi.json) documents order projection reads but no observation retrieval route. The repository exposes `evidenceEntryIds` for reconciliation; those are **financial ledger entry IDs**, a different namespace. `EconomicDecisionRoomProjection` also assembles string references, but they are not a validated raw-evidence retrieval contract.

**Decision:** define a future, typed, organization-bound `GovernedEconomicEvidenceReference` that identifies an existing durable observation and its exact evidence version, plus a separately verified claim-to-observation binding. Keep the Room's raw reference state `NOT_AVAILABLE` until the producer records exact lineage and a scoped retrieval contract is approved. A reference to a normalized durable observation does not assert that the original provider document or payload is retained.

No runtime, schema, API or UI implementation is authorized by this ADR. The design is specified in [SPEC-0090](../specifications/SPEC-0090-governed-raw-evidence-reference.md).

## Alternatives

- **Generic evidence URL or arbitrary string:** rejected. It lacks organization, subject, version, provenance and redaction semantics, and could become an SSRF, ID-enumeration or authority-confusion path.
- **Treat order ID + `sourceEvidenceVersion` as a raw link:** rejected. A version can contain multiple facts, attempts and corrections; it does not identify which observation supports a claim.
- **Reuse reconciliation `evidenceEntryIds`:** rejected for raw economic evidence. They identify financial ledger entries, not V015 observation IDs. A separately proven lineage may bridge them later.
- **Live provider refetch:** rejected for Room page load and historical evidence retrieval; it can change, fail, leak credentials and amplify provider calls. Existing governed reacquisition is a distinct operation.
- **Expose entire current evidence aggregate:** deferred. It would blur which facts support the displayed claim and can overexpose data.

## Boundaries and next gate

Organization must be derived from the authenticated service principal, never from a client-provided organization selector. Retrieval must match organization, order, observation ID, identifier kind and evidence version in durable local storage; compare the claim's frozen projection/assembly context before returning anything. Return bounded, redacted metadata by explicit rendering class; no provider token, external URL, raw sensitive field or arbitrary payload. Absence, redaction, stale revision and integrity conflict remain distinct fail-closed outcomes. An evidence reference is explanatory evidence, not Economic Truth, policy authorization, recovery authority or execution authority.

The future implementation gate requires an exact producer-side claim→observation lineage, proof of historical revision retrieval, organization-isolation and redaction tests, a reviewed read-only API seam, and a decision on whether original provider documents are persisted. Until then `IMPLEMENTATION_READY=NO`.
