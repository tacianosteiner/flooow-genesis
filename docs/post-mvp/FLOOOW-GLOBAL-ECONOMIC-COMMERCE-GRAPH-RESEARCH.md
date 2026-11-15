# FLOOOW --- Global Economic Commerce Graph Research Pack

Status: POST_MVP_RESEARCH_ONLY Implementation: NOT AUTHORIZED Prepared:
2026-11-15

## Thesis

As discovery, checkout and agent execution become interoperable, FLOOOW
should not compete by merely accumulating catalog data. Its defensible
layer is governed economic interpretation across identity, evidence,
provenance, authority and outcomes.

Product Identity → Brand/Supplier/Factory/Merchant →
Offers/Inventory/Price → Search/Content/Creator/Demand →
Logistics/Duties/Tax/Ads/Returns → Economic Truth → Opportunity/Decision
→ Authority → Execution → Outcome.

## Industry seams to exploit

The 2026 W3C/GS1 workshop identifies exact product identity as
unresolved across agent protocols and stresses that similarity is not
identity. Protocol plurality is likely: UCP, ACP, MCP, A2A, AP2 and
WebMCP cover different layers. Authority is becoming first-class through
agent identity, delegation, confirmation and payment authorization.
Amazon is reportedly considering a World Product Graph. Agent Skills is
moving toward open governance with packaging, discovery, versioning and
security becoming explicit ecosystem concerns.

## Candidate graph layers

L0 Identity --- canonical product, variant, GTIN, SKU, ASIN and
platform/supplier/factory IDs. L1 Authority & provenance --- source,
issuer, validity, authority scope, digest, supersession, contradiction.
L2 Commerce topology --- brand, supplier, factory, merchant,
marketplace, geography, channel, creator. L3 Signals ---
search/content/creator velocity, sales estimates, reviews, ads, stock
and price. L4 Economics --- COGS, freight, duty, tax, fees, ads,
returns, working capital, margin, leakage, completeness. L5 Belief ---
probabilistic hypotheses; belief must not masquerade as Economic Truth.
L6 Decision --- opportunity, alternatives, expected value, risk and
evidence dependency. L7 Authority ---
publish/approve/execute/spend/change/contact permissions. L8 Execution
--- orders, ads, suppliers, pricing, inventory and payments. L9 Outcome
--- observed result with decision/action lineage. L10 Learning --- only
causally qualified admissible outcomes update beliefs.

## Contracts to prepare

CanonicalIdentityResolution: SAME / DISTINCT / POSSIBLE_MATCH / UNKNOWN.
POSSIBLE_MATCH never collapses to SAME without sufficient authority.

SourceAuthorityEnvelope: source_id, claim_type, object_identity,
authority_scope, provenance, integrity, freshness, validity, revocation,
supersession.

EconomicSignalEnvelope: signal, object_identity, source, observed_at,
method, coverage, uncertainty, provenance, admissibility.

ProtocolAdapterEnvelope: external_protocol, version, external_identity,
external_authorization, receipt, internal_mapping, mapping_evidence,
mapping_status. External authorization != internal Economic Truth
authority.

## Threat model seed

Identity collision; variant collapse; counterfeit/unauthorized seller
data; stale price/stock; synthetic demand; creator manipulation; review
fraud; source circularity; platform-estimate laundering; protocol
downgrade; agent impersonation; delegated-authority escalation; payment
replay; poisoned skill; registry takeover; dependency substitution;
schema drift; learning contamination.

## Evaluation program

Cross-market identity benchmark; source contradiction benchmark;
demand-signal lead-time benchmark; landed-cost completeness benchmark;
opportunity calibration; authority-bound execution; decision→outcome
attribution; protocol conformance; skill supply-chain adversarial suite.

## Promotion gate

Require operational/stable MVP, runtime evidence, identity benchmark,
adversarially reviewed source-authority model, reconciliation with
Economic Truth, storage chosen from query requirements rather than
fashion, no second truth ledger, and explicit project-authority
promotion.

## Research anchors

W3C/GS1: https://www.w3.org/2026/ecommerce-agents/report.html Google
UCP:
https://developers.googleblog.com/en/under-the-hood-universal-commerce-protocol-ucp/
OpenAI commerce:
https://developers.openai.com/commerce/guides/get-started OpenAI
controlled agentic commerce:
https://developers.openai.com/cookbook/examples/partners/aws/controlled_agentic_commerce_with_agentcore_payments/controlled_agentic_commerce
Anthropic Agent Skills:
https://www.anthropic.com/news/donating-agent-skills-to-the-agentic-ai-foundation
AAIF:
https://www.linuxfoundation.org/press/agentic-ai-foundation-announces-four-new-projects-agent-skills-open-responses-openenv-and-opensandbox

Research anchors are context, not implementation authority. Revalidate
before promotion.
