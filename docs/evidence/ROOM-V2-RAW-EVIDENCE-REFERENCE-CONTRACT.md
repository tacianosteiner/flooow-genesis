# Room V2 — raw evidence reference contract audit

Date: 2026-10-12. Branch: `feature/room-v2-executive-product-evolution`. Input HEAD: `cbb9eca6ee56f4107f359a769b29c30d40d0cb75`. Scope: repository audit and governed design only.

## Source audit

The Room [API client](../../applications/economic-decision-room-web/src/api.ts) reads Sales Intelligence orders, reconciliation cases, systemic divergences and identity health. The [current evidence path](../../applications/economic-decision-room-web/src/App.tsx) displays only loaded order/case/signal fields. `ROOM_OPERATIONAL=false`. [Sales Intelligence API](../../applications/marketplace-operations-api/src/main/kotlin/io/flooow/marketplace/api/SalesIntelligenceApi.kt) returns order ID, aggregate `sourceEvidenceVersion`, projected time, assembly/calculation policy and state; no raw observation ID. Its [projection record](../../applications/marketplace-operations/src/main/kotlin/io/flooow/marketplace/operations/economics/sales/MarketplaceSalesIntelligenceProjection.kt) includes organization, order, aggregate version and change sequence, but no contributing observation set. [V018](../../applications/marketplace-operations-persistence-postgres/src/main/resources/db/migration/V018__create_marketplace_sales_intelligence_projection.sql) matches that shape.

[Independent economic evidence](../../applications/marketplace-operations/src/main/kotlin/io/flooow/marketplace/operations/economics/evidence/MarketplaceIndependentEconomicEvidence.kt) and [V015 persistence](../../applications/marketplace-operations-persistence-postgres/src/main/resources/db/migration/V015__create_independent_marketplace_economic_evidence.sql) have organization/order, observation UUID, update version, family, source on applicable facts, observation/occurrence times and correction links. [Reconciliation cases API](../../applications/marketplace-operations-api/src/main/kotlin/io/flooow/marketplace/api/ReconciliationCasesApi.kt) returns financial ledger `evidenceEntryIds`, case revision and policy, not V015 observation IDs. [Decision Room projection](../../applications/marketplace-operations/src/main/kotlin/io/flooow/marketplace/operations/economics/reconciliation/EconomicDecisionRoomProjection.kt) forms typed-prefix strings such as `financial-ledger-entry:...`; they are not a raw observation retrieval primitive. [OpenAPI](../../applications/marketplace-operations-api/src/main/resources/openapi.json) has scoped projection/case reads and no V015 observation retrieval path. Existing governed reacquisition is a separate write/refresh operation, not historical read.

ADR/SPEC numbering audit found highest existing pair 0089; 0090 is unused in `docs/adr` and `docs/specifications`. No Kotlin, SQL, OpenAPI or runtime file was changed.

## Required element classification

Each row identifies the strongest evidenced state **for the Room claim→raw evidence path**; existing lower-layer facts are described without promoting them to an exposed reference.

| Element | Classification | Evidence and gap |
|---|---|---|
| Evidence identity | `EXISTING_BUT_NOT_EXPOSED` | V015 `observation_id` and typed observation UUID exist; Sales Intelligence projection/Room omit it. |
| Provider/source identity | `EXISTING_BUT_NOT_EXPOSED` | Applicable fact rows have source kind/system key/reference; attempt and correction semantics differ; source fields are not in Room projection. |
| Evidence family/type | `EXISTING_BUT_NOT_EXPOSED` | V015 fact family/kind persisted; no claim-level family binding in Room. |
| Organization boundary | `EXISTING_CANONICAL` | V015/V018 keys and authenticated API reads are organization-scoped. A future endpoint must recheck the boundary. |
| Subject identity | `EXISTING_CANONICAL` | Marketplace order UUID is shared by projection and durable economic evidence, but subject equality alone is not contribution lineage. |
| Source occurrence identity/time | `UNSAFE_TO_INFER` | Fact `occurred_at` and external reference may exist. Observation UUID is not a provider occurrence ID; attempts have attempted time instead. |
| Observation time | `EXISTING_BUT_NOT_EXPOSED` | Fact/correction `observed_at` exists; not serialized in Sales Intelligence. |
| Evidence version/revision | `EXISTING_BUT_NOT_EXPOSED` | V015 exact evidence version exists; exposed `sourceEvidenceVersion` identifies a subject aggregate, not one observation. |
| Projection/assembly version | `EXISTING_CANONICAL` | V018 stores assembly policy, source version, change checkpoint and projected time; API exposes only a subset. |
| Retrieval eligibility | `MISSING_CONTRACT` | No scoped observation read route, caller authorization matrix or claim-binding authorization. |
| Redaction/rendering boundary | `MISSING_CONTRACT` | No approved field allowlist or payload class for Room raw evidence rendering. |
| Availability state | `MISSING_CONTRACT` | Domain has read-result variants, but no claim-level raw-reference state. Room must currently show `NOT_AVAILABLE`. |

Producer-side exact claim→observation lineage is `MISSING_PERSISTENCE` for a durable historical claim binding. Retention of original provider documents is `UNSAFE_TO_INFER`; V015 stores normalized observations, not proof of original raw document storage.

## Finding register

These are future implementation blockers and threat cases, not claims that the current read-only Room exposes a vulnerability.

| Severity | Count | Finding and required control |
|---|---:|---|
| `BLOCKER` | 3 | Exact projection/assessment-to-observation lineage absent; no historical binding persistence/atomicity contract; no approved organization-scoped, redacted observation retrieval endpoint. |
| `HIGH` | 6 | Cross-organization access and ID enumeration; provider secret/PII leakage; wrong subject/case bridge; wrong or stale revision/correction; frontend-crafted ID or arbitrary URL injection; raw payload/provider live-call amplification. All require deny-by-default handler and tests. |
| `MEDIUM` | 3 | Deleted/unavailable observation ambiguity; reference confused with canonical truth; evidence reference confused with execution/recovery authority. Require explicit states and UI boundary. |
| `LOW` | 0 | No low-priority finding used to weaken a gate. |

## Decision and validation

`EXISTING_CANONICAL_REFERENCE=NO` for an end-to-end Room claim reference. Durable observation identity exists, but the exact claim bridge and retrieval contract do not. `IMPLEMENTATION_READY=NO`. The correct current Room status is `RAW_EVIDENCE_REFERENCE=NOT_AVAILABLE`; no ID or link should be inferred from an order, source version or ledger entry. [ADR-0090](../adr/ADR-0090-governed-raw-evidence-reference.md) and [SPEC-0090](../specifications/SPEC-0090-governed-raw-evidence-reference.md) describe the future contract and acceptance tests.

Validation for this documentation-only tranche: `git diff --check`, staged diff check, path/number audit and scope review. An unrelated full Kotlin/Java build is not required. No migration, database, provider call, port or executable route was used. Main, Package 0090 and Global Commerce research were not modified.
