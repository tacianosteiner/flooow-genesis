# SPEC-0049: Live Omie Economic Evidence Ingestion - Slice A

Status: Accepted

Date: 2026-09-06

Governing ADR: ADR-0050

Implementation task: TASK-0149

## Objective

Implement the smallest production-capable, read-only Omie connector slice that
can translate explicit Omie product-cost data into the existing independent
marketplace economic evidence contract without changing economic truth,
persistence, Connector Runtime semantics, or organization/credential authority.

## Capability

Freeze one capability:

```text
marketplace-economic.product-cost
```

Provider key:

```text
omie
```

The capability processes at most one bounded Omie page per Connector Runtime
invocation.

## Credential contract

Slice A uses the existing Integration Control Plane credential custody.

The connector receives opaque credential bytes from Connector Runtime.

Inside the provider module, those bytes decode to a versioned Omie credential
envelope containing exactly:

```text
schemaVersion = 1
appKey
appSecret
```

Rules:

- blank values are invalid;
- values are never included in `toString`, logs, exceptions, telemetry, records,
  progress, or evidence;
- owned temporary byte arrays must be cleared when practical;
- the connector does not persist credentials;
- the connector does not rotate credentials;
- repository source contains no real credential.

## HTTP contract

Use HTTPS only.

Default Omie product endpoint for this slice:

```text
https://app.omie.com.br/api/v1/geral/produtos/
```

Endpoint override is allowed only through explicit constructor/configuration
injection for deterministic tests and controlled environments; it is not
accepted from provider payload or progress.

One invocation performs one provider request/page.

No internal automatic retry loop.

Connector Runtime deadlines, record budget, response-byte budget, and
cancellation remain authoritative.

## Pagination

Progress is opaque to Connector Runtime.

The Omie adapter encodes only the minimum deterministic continuation state
required for the next numbered page.

The adapter validates progress before network use.

Progress must not contain:

- credentials;
- source payload;
- economic amounts;
- organization identity;
- internal order identity.

A page cannot exceed ConnectorBudget.maxRecords.

A response cannot exceed ConnectorBudget.maxResponseBytes.

## Connector record

Define a closed Slice A record representing explicit provider evidence input.

Minimum fields:

```text
marketplace economic evidence subject
Omie product reference
Omie page/source reference
unit CMC when explicitly present
currency when explicitly supported
provider observed/source time when explicitly available
connector observedAt
```

A connector record is not canonical economic truth.

A record with no valid cost is not converted into zero cost.

## Association rule

Slice A does not invent Omie-to-marketplace identity.

A record may create PRODUCT_COST evidence only when its
`MarketplaceEconomicEvidenceSubject` is already explicit in the input/record
boundary.

Title similarity, SKU guessing, product-name matching, price matching, and fuzzy
identity are forbidden.

Historical MGI identity-resolution knowledge may be used later as candidate
evidence, never as implicit canonical association in this slice.

## Committer

Create one ConnectorPageCommitter for this capability.

It must:

1. validate organization, capability, and record type;
2. load/use the existing durable connector progress contract;
3. convert each eligible record to an existing independent economic evidence
   update;
4. call the existing evidence repository with optimistic version semantics;
5. accept existing deterministic duplicate/no-op behavior;
6. fail closed on identifier/source-fact conflicts;
7. advance connector progress only after every required evidence update for the
   page is durably handled;
8. never create a second checkpoint.

The existing evidence repository and its change-sequence allocation remain the
only durable economic evidence write authority.

## Economic mapping

For an explicit Omie unit CMC accepted as order product-cost evidence:

```text
family = PRODUCT_COST
source.kind = ERP
source.systemKey = "omie"
```

The component type must be one already accepted for PRODUCT_COST by the current
economic evidence contract.

Money uses exact decimal parsing and the existing MarketplaceMoney rules.

Binary floating-point canonicalization is forbidden.

Coverage may be COMPLETE or PARTIAL only when justified by the explicit record.

Missing/ambiguous values generate no invented component.

## Deterministic identifiers

Observation identifiers used for provider facts must be deterministic from
stable source identity plus subject/fact identity, or otherwise satisfy replay
idempotency through the existing repository rules.

Repeated delivery of the same provider fact must converge without duplicate
economic meaning.

A changed provider meaning under an already-used source identity must fail
closed unless an explicit correction workflow is authorized.

Slice A does not invent automatic source correction.

## Provider failure translation

At minimum:

- invalid/missing credential -> AUTHENTICATION_REQUIRED;
- provider authorization denial -> AUTHORIZATION_DENIED;
- HTTP/provider rate limit -> RATE_LIMITED with bounded Retry-After when present;
- provider 5xx/transient transport -> REMOTE_TEMPORARY;
- permanent unsupported request -> REMOTE_PERMANENT;
- malformed economic/provider payload -> REMOTE_DATA_INVALID;
- budget overflow -> BUDGET_EXCEEDED;
- cancellation -> CANCELLED.

No adapter exception, response body, secret, endpoint credential material, or
raw provider payload crosses the public Connector Runtime result boundary.

## Required tests

Module tests must prove at minimum:

- valid credential decoding without secret leakage;
- malformed credential fails before network use;
- HTTPS enforcement;
- one invocation performs at most one page request;
- numbered pagination/progress round trip;
- malformed progress fails before network use;
- record budget enforced;
- response byte budget enforced;
- cancellation before/during work;
- explicit unit_cmc parses exactly;
- absent unit_cmc does not synthesize zero;
- malformed monetary value fails closed;
- no fuzzy identity association;
- correct ERP/omie provenance;
- deterministic replay of the same record;
- duplicate provider delivery does not duplicate economic meaning;
- conflict blocks progress advancement;
- evidence persistence failure blocks progress advancement;
- all evidence durability precedes page progress commit;
- organization isolation;
- connector failure taxonomy mapping;
- secrets absent from public strings/errors.

Existing regression gates must remain green.

## Performance/safety characterization

The test suite must include a representative bounded page near the accepted
record maximum for this capability and prove linear page handling without
unbounded accumulation beyond ConnectorBudget.

No load-test framework or partitioning is authorized.

## Exact authorized implementation paths

TASK-0149 may modify/create exactly these ten paths:

1. MODIFY
   `settings.gradle.kts`

2. CREATE
   `applications/marketplace-economic-provider-ingestion/build.gradle.kts`

3. CREATE
   `applications/marketplace-economic-provider-ingestion/src/main/kotlin/io/flooow/marketplace/operations/economics/provider/ProviderEconomicEvidenceRecords.kt`

4. CREATE
   `applications/marketplace-economic-provider-ingestion/src/main/kotlin/io/flooow/marketplace/operations/economics/provider/MarketplaceEconomicEvidencePageCommitter.kt`

5. CREATE
   `applications/marketplace-economic-provider-ingestion/src/main/kotlin/io/flooow/marketplace/operations/economics/provider/omie/OmieEconomicEvidenceConnector.kt`

6. CREATE
   `applications/marketplace-economic-provider-ingestion/src/test/kotlin/io/flooow/marketplace/operations/economics/provider/ProviderEconomicEvidenceRecordsTest.kt`

7. CREATE
   `applications/marketplace-economic-provider-ingestion/src/test/kotlin/io/flooow/marketplace/operations/economics/provider/MarketplaceEconomicEvidencePageCommitterTest.kt`

8. CREATE
   `applications/marketplace-economic-provider-ingestion/src/test/kotlin/io/flooow/marketplace/operations/economics/provider/omie/OmieEconomicEvidenceConnectorTest.kt`

9. MODIFY only as TASK-0149 implementation evidence
   `docs/evidence/TASK-0149-live-omie-economic-evidence-ingestion.md`

10. APPEND exactly one TASK-0149 implementation entry
    `docs/journal/MGI-EXECUTIVE-JOURNAL.md`

No eleventh implementation path is authorized.

## Frozen outside Slice A

- `applications:connector-runtime` production code;
- `applications:integration-control-plane` production code;
- PostgreSQL migrations/repositories;
- Marketplace Economic Evidence domain semantics;
- Economic Truth assembler/calculator;
- Sales Intelligence projection;
- Mercado Livre adapter;
- OAuth;
- provider credential rotation execution bridge;
- API/UI;
- scheduler/worker;
- retries/backpressure/circuit breaker;
- identity adjudication;
- MGI domain model port;
- Kernel.

If implementation requires any frozen path, TASK-0149 stops and governance must
be amended before code continues.