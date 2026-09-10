# SPEC-0073 — Governed evidence reacquisition

The normal refresh capability and the explicit `reacquisition-v1` capability are
separate progress namespaces. A page committed in one namespace cannot block a
page in the other. Replaying the same namespace is idempotent through the
existing page commit key and integrity checks. New observations coexist with
historical observations and retain source fingerprints and observed timestamps.

Endpoints:

- `POST /v1/sales-intelligence/reacquire`
- `POST /v1/commerce-identity/omie/reacquire`

Both require the authenticated service principal, accept no body or query, and
resolve the configured connection server-side. Responses contain operational
counts and the generation identifier only.

The source failure category is bounded metadata (`AUTHENTICATION`,
`AUTHORIZATION`, `RATE_LIMIT`, provider, schema, budget, persistence, or
`UNKNOWN`). It never contains provider payloads or secrets.
