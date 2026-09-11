# TASK-0165I — Governed Product Identity Bridge Evidence

## Evidence matrix

| Source | Field | Provider semantic | Example shape | Current Genesis meaning | Canonical? | Identity-bearing? | Confidence | Proof |
|---|---|---|---|---|---|---|---|---|
| Mercado Livre order item | `item.id` | marketplace item identity | `MLB6190573804` | transaction evidence | No | Transaction only | Exact source observation | V021/V027 parser and schema |
| Mercado Livre order item | `item.seller_sku` | seller offer/SKU | `MKP-CONST-ELETR-TM11552-01` | typed product evidence | No | Product candidate feature | Exact source observation | V027 parser/schema and live evidence |
| Omie sales order detail | `det[].produto.codigo_produto_integracao` and supported aliases | provider product code | `SKU-1` | `OmieSalesOrderEvidence.productCodes` | No | Product candidate feature | Exact source observation | TASK-0165F parser tests/spec |
| Omie product cost | `nCodProd` | Omie product identity | numeric string | `source_product_ref` | No | Omie catalog/cost evidence | Exact source observation | V019 and Omie product connector |
| Omie product cost | `cCodInt` / `cCodigo` | integration/display product reference | text | `source_integration_ref` / `source_product_code` | No | Candidate feature only | Exact source observation | V019 and Omie product connector |

## Decision

Genesis now isolates the existing exact seller-SKU ↔ Omie transaction product-code
intersection behind `ProductIdentityBridge`. It emits only a suggested
`CANDIDATE` product relation. It does not equate SKU with Omie catalog identity,
does not infer from amount/date, and does not confirm mappings.

The current durable schemas provide no proven relation between the 37 Omie
transaction product references and the Omie product-cost `source_product_ref`,
nor a durable reader that can establish such a relation. Therefore no catalog
bridge is asserted by TASK-0165I. The golden SKU
`MKP-CONST-ELETR-TM11552-01` remains unresolved unless an exact provider-native
Omie product-code observation is present in the same organization.

Historical observations remain immutable; missing remains distinct from zero;
all relations remain organization-scoped and read-only. No provider, ledger,
Economic Truth, recovery, or authority mutation is introduced.
