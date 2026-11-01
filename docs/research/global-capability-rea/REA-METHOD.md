# FLOOOW Global Capability REA — Method

## 1. Objective

REA is a governed comparative reverse-engineering discipline.

It studies the capability architecture of external systems without
assuming that their implementation choices are correct for FLOOOW.

The unit of analysis is primarily the architectural primitive, not the
marketing feature.

## 2. Evidence classes

Evidence must be classified where possible as:

1. OFFICIAL_DOCUMENTATION
2. PUBLIC_API_OR_SDK
3. PUBLIC_SOURCE_CODE
4. PUBLIC_TECHNICAL_TALK
5. PUBLIC_PAPER_OR_PATENT
6. DIRECTLY_OBSERVED_PRODUCT_BEHAVIOR
7. TECHNICAL_REVERSE_ENGINEERING_EVIDENCE
8. THIRD_PARTY_REPORT
9. INFERENCE

Inference is never equivalent to directly observed implementation.

## 3. REA dimensions

Each platform should be examined across:

1. Reality Model
2. Truth Model
3. Evidence
4. Provenance
5. Unknown
6. Contradiction
7. Identity
8. Authority
9. Decision
10. Agent Governance
11. Execution
12. Reconciliation
13. Outcome
14. Learning
15. Economics
16. Simulation
17. Commerce Depth
18. Runtime Governance

## 4. Maturity scale

0 — not identified
1 — concept
2 — design
3 — productized
4 — production proven
5 — scale proven

## 5. Competitive classification

BEHIND
PARITY
DIFFERENT
AHEAD_BY_DESIGN
AHEAD_IF_IMPLEMENTED
AHEAD_PROVEN
DO_NOT_COPY
UNKNOWN

AHEAD_BY_DESIGN must never be represented as a superior product.

AHEAD_PROVEN requires evidence.

## 6. Decision classification

ADOPT
ADAPT
REJECT
MONITOR
DEFER

## 7. Required REA card

COMPANY
CAPABILITY
PROBLEM_SOLVED
ARCHITECTURAL_PRIMITIVE
HOW_IT_WORKS
EVIDENCE
MATURITY
FLOOOW_CURRENT_EQUIVALENT
COMPETITIVE_POSITION
WHAT_THEY_DO_BETTER
WHAT_FLOOOW_DOES_DIFFERENTLY
WHAT_FLOOOW_MAY_DO_BETTER
WHAT_WE_WOULD_DESTROY_IF_COPIED_EXACTLY
DECISION
PROPOSED_FLOOOW_EVOLUTION
MVP_IMPACT
ROADMAP
CONFIDENCE
OPEN_QUESTIONS

## 8. Anti-copy rule

The mandatory question is:

IF WE COPIED THIS EXACTLY, WHAT WOULD WE DESTROY IN FLOOOW?

A useful external capability can still receive REJECT if its
implementation violates FLOOOW invariants.

Example:

External capability:
dynamic operational query execution.

Possible FLOOOW decision:
ADOPT capability intent,
REJECT implementation,
rebuild with fixed callable surface,
bounded principal,
evidence lineage,
authority binding,
and reconciliation.

## 9. Epistemic rules

A missing public equivalent does not prove absence.

Therefore:

NOT_FOUND_IN_PUBLIC_RESEARCH
!=
COMPETITOR_DOES_NOT_HAVE_IT

Similarly:

FLOOOW_DESIGN_EXISTS
!=
FLOOOW_IMPLEMENTATION_EXISTS

and:

FLOOOW_IMPLEMENTATION_EXISTS
!=
PRODUCTION_PROVEN

## 10. Promotion rule

REA research cannot directly mutate:

- Package-0090
- Room critical path
- canonical V043
- production authority
- database authority
- execution authority

Promotion requires:

REA findings
→ cross-company synthesis
→ adversarial review
→ architecture delta
→ explicit roadmap promotion

## 11. Research branch rule

REA evidence belongs in a research branch.

The preferred structure is:

docs/research/global-capability-rea/

Research preservation does not imply implementation approval.