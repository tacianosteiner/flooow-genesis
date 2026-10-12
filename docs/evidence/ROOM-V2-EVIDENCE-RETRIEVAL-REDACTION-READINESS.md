# Room V2 — retrieval and redaction readiness

Date: 2026-10-12. Status: **design-only; retrieval not ready**. The producer snapshot in [ADR-0091](../adr/ADR-0091-economic-projection-consumed-evidence-lineage.md) is not implemented. This document audits actual V015/V017 fields and narrows the later rendering gate; it creates no API or payload authorization.

## Proposed server-selected read path

Room → loaded order or case and its **server-owned historical claim context** → authenticated, organization-derived API → immutable claim revision/member manifest → exact V015 identifier/version/kind under the same org/order → allowlisted rendering. The client never supplies an arbitrary observation ID or external URL as authority. The API must not call a provider. Without an exact historical claim revision, the response is `NOT_AVAILABLE` rather than a guessed link.

The existing [Sales Intelligence OpenAPI](../../applications/marketplace-operations-api/src/main/resources/openapi.json) provides current order projection reads, not a historical observation read. Reconciliation case reads expose ledger entry IDs; [V032](../../applications/marketplace-operations-persistence-postgres/src/main/resources/db/migration/V032__create_financial_ledger_materialization_lineage.sql) can bridge only its materialized component subset. No route is selected or implemented here.

## Field classification from V015/V017

| Stored field family | Classification | Future treatment to test |
|---|---|---|
| Organization/order UUID, observation UUID, evidence version, identifier kind, family, correction IDs | `SAFE_OPERATOR_METADATA` **only after authorization** | Server may show a scoped, bounded identifier and supersession relation; executive view can use opaque claim context instead. UUID is not an access token. |
| `observed_at`, `occurred_at`, `attempted_at`, committed version/time, correction reason, attempt outcome | `SAFE_EXECUTIVE_METADATA` subject to policy | Distinguish observation from occurrence and attempt; never imply a missing value is zero or a completed fact. |
| Source kind and system key | `SAFE_OPERATOR_METADATA` subject to provider/tenant policy | Source attribution can be displayed only from exact stored record. |
| Component type, coverage, quality, direction, currency, magnitude | `SENSITIVE_BUSINESS` | Executive aggregate may already show governed economic results; raw component amount requires a separate role/field allowlist. |
| Marketplace key, external order ID, source external reference, anchor/linked references | `PROVIDER_REFERENCE`; potentially `PII` depending on actual identifier content | Default redact. V015 syntax constraints do not prove these values contain no personal or confidential data. No arbitrary URL passthrough. |
| Provider token, credential, secret URL, raw provider payload | `SECRET_OR_CREDENTIAL` / `NOT_PUBLICLY_RENDERABLE` | Not present as approved V015 evidence payload fields; never add them to this contract. Original provider document retention is unproven. |

Suggested future presentation classes `EXECUTIVE_SUMMARY`, `EVIDENCE_METADATA` and `OPERATOR_DETAIL` are **not current permissions**. Each needs a reviewed allowlist by evidence family/kind, tenant role, field, size and purpose. An operator view cannot be inferred from the current Room's service bearer alone.

## Failure and adversarial gates

- Derive organization from authenticated principal, verify full claim revision/order/observation/version tuple and avoid cross-tenant existence leakage. Guessed IDs and malformed UUIDs never bypass the server claim binding.
- Bound record count, size, cursor and fan-out; never render entire historical aggregate or follow URLs. Timeouts and unavailable storage are not `MISSING`.
- A corrected/superseded observation remains historical and is labeled as such; current value must not replace what an old claim consumed. Wrong family/kind/version is `CONFLICTING` internally and yields no payload.
- Redact external references and business-sensitive fields before serialization or logging; test nested/exception paths as well as successful response.
- Do not present a reference as canonical Economic Truth or as policy, recovery or execution authority.

`REDACTION_POLICY=DESIGN_INCOMPLETE`, `RETRIEVAL_ENDPOINT_READY=NO`, `PROVIDER_LIVE_CALL_REQUIRED=NO`. The current Room may say `RAW EVIDENCE = NOT AVAILABLE` without a dead link; no UI change was necessary for this design tranche.
