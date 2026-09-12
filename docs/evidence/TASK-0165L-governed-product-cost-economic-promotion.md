# TASK-0165L - Governed Product-Cost Economic Promotion

Date: 2026-09-12
Base: `817df1f66bd4e2e14210bbe763315843eba5a48c`

## Delivered boundary

TASK-0165L composes current TASK-0165K identity authority with exact durable
economic authority and appends independent `PRODUCT_COST` evidence through the
existing `MarketplaceIndependentEconomicEvidenceRepository`. PostgreSQL uses
`PostgresMarketplaceIndependentEconomicEvidenceRepository` and the existing
`marketplace_economic_evidence_*` tables. No new table or parallel ledger was added.

Identity remains service-level through `CrossSystemProductIdentityConfirmationService`.
`PostgresGovernedProductCostPromotionAuthority` has no TASK-0165K dependency and
validates only durable source, subject, organization/connection scope, currency,
and allocation/quantity authority.

## Durable behavior proven

- Exact confirmed identity plus available durable authority promotes one
  `PRODUCT_COST` / `DEDUCTION` / `PARTIAL` / `CONFIRMED` component.
- `3.125 * 2.5` persists exactly as `7.8125`.
- Exact replay returns `GovernedProductCostPromotionResult.AlreadyPromoted`; the
  durable component count remains one.
- A newer Omie source version with `4.25 * 2.5` appends `10.625` as a second fact.
- The original `7.8125` fact remains equal and unchanged; no correction or update
  rewrites history.
- The source reference binds Omie connection/version/ordinal to the effective
  TASK-0165K decision ID. The durable decision supplies both connection scopes,
  ML item/SKU, Omie provider product, principal, provenance, correlation, revision,
  and decision time. Referenced source rows supply unit cost, quantity, and currency.
- Unconfirmed identity, rejected identity, missing cost, missing currency authority,
  and missing allocation authority produce zero durable `PRODUCT_COST` rows.

Omie `nCMC` supplies no currency. Currency is exact durable Mercado Livre evidence.
Missing `nCMC` is not zero; null is `CostMissing`, while numeric zero is valid
`GovernedProductCostSourceRead.Available`.

## Production defects found and fixed

1. The JDBC reader advanced the cursor to test cardinality before materializing the
   first row. The first row is now materialized before checking for a second;
   multiple rows still fail closed.
2. Missing `currencyAuthority` could be ignored. Explicit currency is now required
   and missing authority returns `CurrencyUnavailable`; BRL is never inferred.
3. Durable currency or quantity contradictions could be classified as ordinary
   unavailability. Contradictions now return `IntegrityFailure`.
4. PostgreSQL `numeric(24,6)` scale made exact multiplication such as
   `3.125000 * 2.5 = 7.8125000` appear to exceed six decimal places. Insignificant
   trailing zeros are now stripped before scale validation. The numeric value is
   unchanged and no rounding occurs.

## Canonical result types

The source defines `GovernedProductCostPromotionResult.Promoted`,
`AlreadyPromoted`, `IdentityUnconfirmed`, `IdentityRejected`, `IdentityConflict`,
`CostMissing`, `CurrencyUnavailable`, `SubjectUnresolved`,
`AllocationUnavailable`, `EvidenceStaleOrSuperseded`, and `IntegrityFailure`.

## Validation

Final focused gate:

- `PostgresGovernedProductCostPromotionAuthorityTest`: 12 passed, 0 failed;
- `GovernedProductCostPromotionTest`: 11 passed, 0 failed;
- `PostgresGovernedProductCostPromotionIntegrationTest`: 2 passed, 0 failed;
- total: 25 passed, 0 failed.

Canonical full repository command:

`./gradlew clean build --no-daemon --stacktrace`

Windows execution: `.\gradlew.bat clean build --no-daemon --stacktrace`

Result: `BUILD SUCCESSFUL in 10m 40s`; 124 actionable tasks, 66 executed and
58 from cache. The full build was run once.

## Safety conclusion

Seller-SKU text equality is not identity authority. Exact within-Omie identity does
not transitively confirm ML-to-Omie identity. No provider write, currency inference,
fuzzy identity, historical rewrite, Economic Truth completeness, reconciliation
completeness, decision readiness, recommendation authority, or execution authority
was introduced.

`SOURCE OBSERVATION != IDENTITY AUTHORITY != SUBJECT AUTHORITY != CURRENCY AUTHORITY != ALLOCATION AUTHORITY != PROMOTED ECONOMIC EVIDENCE != CANONICAL ECONOMIC TRUTH`

`PRODUCT_COST promotion != Economic Truth completeness != reconciliation completeness != decision readiness != recommendation authority != execution authority`
