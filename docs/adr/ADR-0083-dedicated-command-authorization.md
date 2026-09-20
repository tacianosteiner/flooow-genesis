# ADR-0083 — Dedicated command authorization

Status: Design frozen for the zero-authority infrastructure slice

Date: 2026-09-18

## Decision and authority

Introduce dedicated technical command principals, credential verification and
append-only permission grants under SPEC-0083. The CEO's current instruction
authorizes implementation with zero operational principals, credentials and
grants. It does not authorize provisioning, command route activation or a real
transaction decision. Authentication and authorization are separate operations.

SPEC-0005 explicitly has one privilege level and requires a new specification
for scopes/roles. SPEC-0010 excludes human users, permissions and delegated
authorization from its accepted scope. SPEC-0074 uses the coarse bearer for
product decisions; that is not authority for transaction decisions. Inspection
found no existing granular permission vocabulary to extend. Use the explicit
codes TRANSACTION_IDENTITY_DECISION_WRITE and TRANSACTION_IDENTITY_POLICY_ADMIN.
They are independent, exact permissions without wildcards or implication.

Keep this substrate outside the Kernel, in Marketplace Operations' command
boundary and its PostgreSQL adapter. No service-bearer adapter, runtime wiring,
bootstrap seed, provisioning endpoint or automatic policy is introduced.
An immutable principal binds one organization and exact provider connection
pair. Changing its scope requires a new principal; secret rotation retains the
existing principal identity. Grants bind that durable actor, not a token digest
or credential revision. Credential revocation and grant revocation remain
independent append-only operations.

## Provisioning and activation boundary

Choose an offline controlled operator ceremony, not a public grant API.
Before the first real principal/credential/grant, an accepted authority source
must identify the operator, exact organization/pair, permission, expiry/rotation
procedure, reason, provenance and correlation. The operator must explicitly
authorize each privilege. Store only the verifier, deliver the random secret
through a protected channel, and never include it in audit/checkpoints.
The ceremony/tool implementation and actual provisioning remain HOLD. No
currently authenticated service is presumed to be that authority source.
Schema presence and synthetic test fixtures create no operational authority.

## Consequences

Zero grants always denies writes. A stolen bearer credential can be replayed
until revoked: high entropy and constant-time verification do not solve theft.
TLS, protected delivery, operational rotation/revocation and ingress controls
are required before activation; credential possession is not human intent.
The selectable infrastructure has no network command surface. S2A wiring must
use the in-transaction adapter and capture exact authorization lineage. S2B
needs separate policy authority and its own temporal/field proof.
