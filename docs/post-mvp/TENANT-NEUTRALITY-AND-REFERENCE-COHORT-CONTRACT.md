# FLOOOW — Tenant Neutrality & Reference Cohort Contract

Status: ARCHITECTURAL INVARIANT
Version: 1.0
Date: 2026-10-10
Scope: FLOOOW Genesis core, post-MVP capabilities, benchmarks, pilots and future commercial deployments

## 1. Decision

FLOOOW Genesis is a general-purpose governed economic intelligence platform.

No operating company, brand, marketplace, retailer, vertical, supplier network or current user business may become a mandatory core dependency unless the concept has been generalized and independently justified as a reusable platform primitive.

This includes REDMOTO.

Canonical declaration:

```text
REDMOTO_IS_PRODUCT_DEPENDENCY=NO
REDMOTO_IS_DOMAIN_PRIMITIVE=NO
REDMOTO_IS_PLATFORM_IDENTITY=NO
REDMOTO_IS_REFERENCE_IMPLEMENTATION=YES
REDMOTO_IS_INITIAL_VALIDATION_COHORT=YES
PLATFORM_GENERALIZATION_REQUIRED=YES
```

## 2. Redmoto role

Redmoto is:
- one brand/business among the user's operating businesses;
- a convenient real-world laboratory;
- a source of governed product/economic evidence;
- an initial validation cohort for Product Intelligence and Opportunity Intelligence;
- a reference implementation candidate.

Redmoto is NOT:
- the FLOOOW product;
- a tenant assumed by the core;
- a required dataset;
- a hardcoded taxonomy;
- a mandatory marketplace or channel;
- a platform-wide identity;
- a permanent benchmark bias.

## 3. Core abstraction rule

Core code and contracts should use reusable primitives such as:

```text
Organization
BusinessUnit
Brand
Product
ProductFamily
Catalog
Supplier
Channel
Marketplace
Retailer
Store
Evidence
EconomicTruth
Opportunity
Decision
Policy
Authority
Execution
CapitalAllocation
Outcome
Reconciliation
```

Brand-specific concepts must remain configuration/data unless promoted through an explicit generalization review.

Forbidden pattern:

```text
RedmotoProduct
RedmotoOpportunity
RedmotoSupplier
RedmotoCapitalDecision
RedmotoCompatibilityRule
```

Preferred pattern:

```text
Product
Opportunity
Supplier
CapitalDecision
CompatibilityRule

scoped by:
organization_id
business_unit_id
brand_id
tenant/policy context
```

## 4. Commercial deployment requirement

A future FLOOOW customer must be able to operate without any Redmoto-specific configuration, data or code.

A new customer may provide different:
- categories;
- products;
- taxonomies;
- channels;
- marketplaces;
- suppliers;
- KPIs;
- evidence sources;
- policies;
- decision thresholds;
- economic models;
- operating processes.

The platform must preserve core semantics while allowing these tenant-specific extensions.

## 5. Benchmark naming rule

The platform benchmark is:

```text
FLOOOW Product Intelligence Benchmark v1
```

Redmoto may appear only as a cohort:

```text
COHORT_ID=REDMOTO_INITIAL_REAL_WORLD_COHORT
COHORT_ROLE=REFERENCE_VALIDATION
CORE_DEPENDENCY=NO
```

Future cohorts may include:

```text
PREMIUM_BEVERAGE_COHORT
INDUSTRIAL_PARTS_COHORT
ELECTRONICS_COHORT
HOME_GOODS_COHORT
AUTO_PARTS_COHORT
OTHER_CUSTOMER_COHORTS
```

No single cohort defines platform semantics.

## 6. Generalization gate

Before promoting a cohort-specific concept into FLOOOW core, require:

```text
CROSS_TENANT_RELEVANCE=PASS
DOMAIN_GENERALIZATION=PASS
NAMING_NEUTRALITY=PASS
DATA_MODEL_NEUTRALITY=PASS
POLICY_NEUTRALITY=PASS
NO_REFERENCE_CUSTOMER_DEPENDENCY=PASS
```

If any gate fails, the concept remains:
- tenant configuration;
- vertical adapter;
- experimental extension;
- research artifact.

## 7. Anti-overfitting rule

Product Intelligence, Opportunity Intelligence and future Foresight must be tested across multiple cohorts before claiming generalized capability.

A model may perform well on Redmoto and still fail globally.

Therefore track:

```text
GLOBAL_METRICS
COHORT_METRICS
CROSS_COHORT_VARIANCE
OUT_OF_DOMAIN_PERFORMANCE
ABSTENTION_RATE
FALSE_MATCH_RATE
```

Promotion must not rely only on the initial reference cohort.

## 8. Reference cohort lifecycle

A cohort moves through:

```text
PROPOSED
DATA_QUALIFIED
BENCHMARK_READY
ACTIVE_REFERENCE
CROSS_COHORT_COMPARED
RETIRED_REFERENCE
```

Cohort retirement must not affect core platform operation.

## 9. Vertical adapters

Where a vertical needs special semantics, prefer:

```text
FLOOOW CORE
     ↓
VERTICAL ADAPTER
     ↓
TENANT CONFIGURATION
```

Examples:

```text
motorcycle-products adapter
premium-beverage adapter
industrial-parts adapter
retail adapter
```

Adapters may specialize:
- attributes;
- compatibility rules;
- category ontologies;
- external data sources;
- evaluation suites.

They must not redefine canonical truth or authority semantics.

## 10. Product Intelligence implication

The initial Product Intelligence program must distinguish:

```text
PLATFORM TAXONOMY
vs
COHORT-SPECIFIC ATTRIBUTES
```

Example:

Platform relation:
COMPATIBLE_WITH

Redmoto-specific evidence:
motorcycle model/year/fitment

The relation is generic.
The evidence schema may be vertical-specific.

## 11. Opportunity Intelligence implication

The Opportunity Engine must compare opportunities generically.

It may consume:
- Redmoto evidence;
- beverage evidence;
- retailer evidence;
- future customer evidence.

But the primitive remains:

```text
Opportunity
```

not:

```text
RedmotoOpportunity
```

## 12. Room implication

Room V1 and future Room versions remain tenant-neutral.

Future projections may render tenant-specific context, but Room contracts must not assume a particular brand or operating company.

## 13. Engineering review checklist

Every new post-MVP feature must answer:

```text
DOES_THIS_REQUIRE_REDMOTO=NO
DOES_THIS_REQUIRE_A_SPECIFIC_BRAND=NO
DOES_THIS_REQUIRE_A_SPECIFIC_MARKETPLACE=NO
DOES_THIS_REQUIRE_A_SPECIFIC_VERTICAL=NO
CAN_A_NEW_TENANT_USE_THE_CORE_WITHOUT_REFERENCE_DATA=YES
TENANT_SCOPING_EXPLICIT=YES
GENERALIZATION_REVIEW_COMPLETED=YES
```

If not, implementation must remain outside core.

## 14. Architectural principle

Reference businesses exist to make FLOOOW stronger.

FLOOOW does not exist to encode the reference businesses.

The platform must learn from real operating companies without becoming structurally dependent on any one of them.
