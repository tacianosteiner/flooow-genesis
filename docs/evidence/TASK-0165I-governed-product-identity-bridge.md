# TASK-0165I.1 — Typed Omie Product Identifier Evidence

## Decision

Omie transaction product references are preserved as typed source evidence:

| Provider field | Preserved kind |
|---|---|
| `codigo_produto` | `INTERNAL_PRODUCT_ID` |
| `codigo_produto_integracao` | `INTEGRATION_PRODUCT_CODE` |
| `codigo` | `DISPLAY_PRODUCT_CODE` |
| `cCodInt` | `INTEGRATION_PRODUCT_CODE` |
| `cCodigo` | `DISPLAY_PRODUCT_CODE` |

The compact aliases follow the same meanings already used by the durable Omie
product-cost connector: `cCodInt` is the integration reference and `cCodigo`
is the displayed product code. Multiple identifiers present on one transaction
line are retained; textual similarity never collapses their kinds.

New `product_refs` values use
`{"kind":"...","value":"...","quantity":"..."}`. Existing
`{"code":"...","quantity":"..."}` values remain immutable and readable as
`UNKNOWN_LEGACY`; they cannot produce exact within-provider identity. No schema
migration or historical rewrite is required because `product_refs` is JSONB.

When the same source order and fingerprint has both legacy and typed durable
revisions, selection deterministically prefers the semantically richer typed
revision, then the latest observation and durable progress coordinates. Source
fingerprints and old rows are unchanged.

## Two distinct identity graphs

### Graph A — cross-system candidate graph

```text
ML seller_sku
    |
    | exact text equality evidence only
    v
Omie transaction typed product identifier
    |
    | cross-system status remains CANDIDATE / SUGGESTED
    v
explicit cross-system confirmation required
```

The evidence name is
`EXACT_SELLER_SKU_TO_OMIE_PRODUCT_REFERENCE_TEXT`. It describes equality, not
seller-SKU semantics on the Omie side and not product identity.

### Graph B — within-Omie provider graph

```text
Omie transaction typed identifier
    |
    | same-kind provider-semantic resolution
    v
Omie catalog/cost typed identifier
    |
    v
Omie provider product identity
```

Graph B may resolve exactly within Omie only for a unique same-kind match.
Cross-kind equality and `UNKNOWN_LEGACY` remain unresolved. Duplicate provider
products are ambiguous; contradictory non-null identities on repeated
stock/date observations are retained and produce conflict. An exact Graph B
result never upgrades Graph A.

## Catalog boundary and isolation

The catalog reader is read-only and queries
`integration_omie_product_cost_source_observation` by both organization and a
bound Omie connection. It aggregates stock-location/date repetitions by
`source_product_ref` while preserving separately:

- `source_product_ref` as internal product identity;
- `source_integration_ref` as integration product code;
- `source_product_code` as displayed product code.

The transaction and catalog scopes must match exactly. Organization mismatch,
connection mismatch, or mixed Omie transaction connections fail closed.

## Diagnostic metrics

The recompute result now reports transaction reference totals and counts for
all four kinds, catalog product/identifier coverage when the catalog reader is
available, within-Omie exact/ambiguous/conflict/unresolved counts when catalog
evaluation is available, and the ML seller-SKU ↔ Omie reference candidate
count. Catalog and resolver metrics are omitted when that evidence dependency
is unavailable; missing is not reported as zero. Existing TASK-0165H
transaction health counts are unchanged.

## Runtime provenance incident

An apparent 0% TASK-0165H identity result was caused by ambiguity between the
source revision and the artifact/image actually running, not by defective
identity policy. A clean immutable diagnostic image proved the reader/resolver
path. A clean immutable main image then produced:

- `mlTransactionsInspected = 33`
- `omieTransactionsInspected = 133`
- `exactConfirmed = 4`
- `unresolved = 29`
- `coveragePercentage = 12.12`

Future runtime evidence must preserve this chain:

```text
source commit
    -> build artifact
    -> image digest
    -> runtime instance
    -> evaluation
    -> decision
```

That provenance capability is future governance work and does not widen the
current product-identity scope.

## Real-data evaluation

`REAL_EVALUATION_NOT_AVAILABLE` on 2026-09-11. The current process has no
`DATABASE_URL`, `DATABASE_USER`, `DATABASE_PASSWORD`,
`FLOOOW_OMIE_CONNECTION_ID`, or `FLOOOW_MERCADO_LIVRE_CONNECTION_ID`, so the
37-reference comparison and golden SKU research cannot be rerun without the
governed runtime/database context. No result is fabricated and no production
identifier is committed as a fixture.

## Safety boundary

This change is read-only. It introduces no provider write, Omie write-back,
Mercado Livre mutation, Economic Truth change, recovery execution, authority
escalation, fuzzy matching, causal assumption, or transitive confidence.
