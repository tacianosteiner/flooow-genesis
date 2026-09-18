# ADR-0084 — Explicit governed transaction identity writer

Status: Design frozen; infrastructure technically selectable

Date: 2026-09-18

Source: ADR-0082 Revision 9 and ADR/SPEC-0083

## Decision

S2A is a dedicated explicit durable-evidence writer, independent of binding
policy. Implement domain/persistence only under SPEC-0084 and TASK-0165S2A.
No operational route is needed while legitimate provisioning is absent.
S2B automatic policy, policy tables/runtime, S3/C2 and real activation remain HOLD.

Rejection is of one exact stable-subject/canonical-target relation, never of the
whole Omie subject. Rejected A can coexist with confirmed B. Correction retains
the relation and supersedes its current leaf; moving a confirmed subject to a
new target first explicitly rejects the old relation. No hidden target rewrite.

Compare ledger-only + locks against ledger + controlled head projection. A
ledger-only query needs every current/future writer to maintain global exclusion
correctly and cannot express leaf-filtered uniqueness as a simple SQL index.
Choose immutable ledger plus a small head projection maintained exclusively by
the ledger insert trigger. Partial unique indexes enforce both organization-wide
confirmed reservations even under application error/direct insertion. History
remains audit truth; direct projection mutation is rejected; append and head
advance roll back atomically. This is stronger enforcement, not convenience.

Choose canonical marketplaceOrderId intent over externalOrderId. It avoids
re-resolving ambiguous marketplace names and directly references V022 identity.
Connection is not part of canonical ML identity. Select exact promotion/source
only within the authenticated principal's server-bound ML connection; among
equivalent PROMOTED/DUPLICATE lineages choose lowest progress/ordinal. A registry
allocated through A can be used through a proven B promotion, retaining exact B
lineage without creating a second identity. Missing selected-connection proof
is unavailable, not permission to choose an arbitrary other connection.

Historical provider connections may be SUSPENDED/REVOKED: online usability does
not determine governance of already durable evidence. Require ACTIVE organization,
exact retained provider identities, current valid dedicated credential/grant and
exact durable joins. Requiring live provider credentials would wrongly erase
historical governance; no provider call is made. DRAFT with no evidence remains
unavailable; state never substitutes for exact proof.

Currentness fence is the actual integration_connector_progress row keyed by
(organization, Omie connection, V3 capability), FOR UPDATE. Existing V3 committer
uses PostgresConnectorProgressStore.commitPage/lockProgress before base/sidecar
inserts. Reusing this row interoperates with ingestion without modifying S1.
No separate advisory currentness namespace. Identity advisory keys only serialize
decision IDs and shared global subject/target reservations. No batched writes.

## Review disposition

SPEC-0084 closes schema, null semantics, fingerprints, joins, privilege boundary,
locks, API/typed failures and tests. Internal adversarial review found no remaining
BLOCKER or authority-corrupting HIGH for this infrastructure slice. Tests still
must pass on the final code/schema; selectable design is not field proof.
Runtime DB DDL/trigger/TRUNCATE/projection-write privileges must remain withheld
before activation. Owner/superuser and compromised application server remain
outside the database/application trust boundary. No authority is provisioned.
