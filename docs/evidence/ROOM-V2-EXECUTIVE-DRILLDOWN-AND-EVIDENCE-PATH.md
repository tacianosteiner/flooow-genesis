# Room V2 — Executive drilldown and evidence path

Date: 2026-10-12. Branch: `feature/room-v2-executive-product-evolution`. Baseline: `75ebf03095ff3a7b39d91f4cf76d0575b3455d4e`.

Decision Pressure now offers a read-only evidence path. An unresolved or incomplete pressure opens only matching orders in the loaded projection, with exact order ID, state, source evidence version, assembly policy version, available reasons/components, and explicit missing economic result. Open reconciliation cases and systemic signals show their own IDs and existing policy/evidence references. Order-to-case linkage uses exact `marketplaceOrderId`; a signal lists only the case IDs already present in its source. No relationship is inferred from proximity or status.

The path displays projection scope and optional source availability. It remains `DERIVED / NON-CANONICAL`, `NOT ORGANIZATION-WIDE`, and grants neither execution nor recovery authority. `ROOM_OPERATIONAL` stays false. No backend contract, API endpoint, economic amount, materiality, or canonical truth was added. A missing optional source remains `UNAVAILABLE`, not an empty green result.

Regression tests cover unresolved and incomplete drilldown, evidence/policy versions, loaded-record isolation, derived boundary, blocked execution, unavailable optional sources and existing V2 behavior. Validation: `npm.cmd test -- --run` and `npm.cmd run build` from `applications/economic-decision-room-web`; both must succeed before commit. `git diff --check` and staged diff check are required.

Limitation: the path can cite only fields currently returned by the read-only projection and optional source APIs. It does not claim to expose underlying raw evidence documents or organization-wide case coverage. A future backend evidence-reference contract would need separate governance.
