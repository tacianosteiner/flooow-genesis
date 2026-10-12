# Room V2 — raw-evidence UX and adversarial gate

Date: 2026-10-12. Status: **read-only review; raw retrieval blocked**. Reviewed the current `EvidencePath` in `applications/economic-decision-room-web/src/App.tsx`, its tests, ADR/SPEC-0091 and the retrieval/redaction readiness audit. No runtime code, API, OpenAPI, migration or database changed in this review.

## Present UI claim

The current `EvidencePath` renders **loaded projection context**: order state, source evidence version, assembly policy and reasons, missing/partial component types, whether an economic result is present, loaded reconciliation case count, case ledger-entry IDs and systemic case IDs. It labels the path `READ ONLY · DERIVED / NON-CANONICAL`, states the loaded scope and says `ROOM_OPERATIONAL = NO` for execution authority. It does not render an economic-observation UUID, immutable claim revision, provider document or raw payload, and contains no raw-evidence navigation link. The existing drilldown is useful but must not be described as claim→observation proof. No new placeholder is required for this design gate; a future raw-evidence affordance must stay absent or explicitly `NOT AVAILABLE` until the backend contract is proven.

Future view semantics must distinguish `OBSERVED`, `DERIVED`, `CANONICAL`, `RECONCILED`, `SUPERSEDED`, `MISSING`, `NOT_AVAILABLE` and `REDACTED`. `MISSING` is a conclusion from a complete, policy-bound scope; `NOT_AVAILABLE` means retrieval/coverage failed or was never established; `REDACTED` is an authorization outcome. Current source-evidence version is not an immutable historical claim revision. Case ledger-entry IDs are not V015 observation IDs. A click must begin from a server-owned claim context, never a frontend-composed URL or free observation UUID.

## Adversarial review of the proposed read contract

| Attack / failure | Required proof before any endpoint or UI link | Current gate |
|---|---|---|
| Tenant escape; guessed ID; wrong order/family/kind/version | Derive organization from principal, resolve the historical claim revision server-side, bind every V015 tuple to that organization/order and fail without cross-tenant existence detail. | **BLOCKER** — endpoint and immutable revision absent. |
| Frontend-crafted ID; arbitrary URL; wrong ledger/evidence namespace | Accept only a scoped claim handle. Ledger-entry ID can enter only the separately proven V032 materialization bridge; never cast to observation UUID or follow a provider URL. | **BLOCKER** — no retrieval contract. |
| Stale revision, superseded correction, missing or deleted observation | Return the exact recorded revision/member set with historical status. Integrity mismatch is a failure, not a fallback to current evidence or a silent empty list. | **BLOCKER** — no persisted claim snapshot. |
| Duplicate delivery, replay, concurrent ingestion, partial DB failure | Equal manifest for idempotent retry; reject divergent retry; atomic projection/revision/member transaction and a tested evidence-read boundary. | **BLOCKER** — current V018 upsert is one mutable row. |
| Malformed/oversized UUID or evidence version, oversized response | Typed parsing, strict limits, bounded pagination/fan-out and no full aggregate expansion; adversarial API tests needed. | **HIGH** — design gate, no new route to test. |
| Sensitive reference or payload leak, exception logging | Server allowlist by role and family, redact external references and amounts as required, test error/log paths; raw provider documents remain outside the current contract. | **HIGH** — redaction policy incomplete. |
| Claim text confused with domain key, causal overstatement | Server issues typed claim key/outcome; UI label is presentation. Snapshot membership means consumed context, not per-observation causal support. | **MEDIUM** — taxonomy designed, not exercised. |

The review found no newly introduced runtime code to execute. Existing Room UI tests verify loaded-scope drilldown only; they cannot prove historical claim lineage or raw-evidence security. `ROOM_OPERATIONAL=NO`, `RAW_EVIDENCE_RETRIEVAL_READY=NO`. The next executable test campaign belongs with an implemented producer snapshot and server read contract, not this document.
