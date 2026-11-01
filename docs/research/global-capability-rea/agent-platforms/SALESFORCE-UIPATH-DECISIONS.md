# REA-5 — Salesforce + UiPath Decisions

Status: RESEARCH
Implementation authority: NONE

## SU-001 — Agent observability

Decision: ADAPT

Do not rebuild generic observability as a proprietary moat.

## SU-002 — Session tracing

Decision: ADAPT

Preserve decision/action/evidence linkage but reuse industry tracing
patterns where appropriate.

## SU-003 — Deterministic tool guardrails

Decision: ADOPT_INTENT

Deterministic bounded enforcement strongly aligns with FLOOOW.

## SU-004 — Human approval

Decision: ADOPT_WHERE_REQUIRED

Human approval is a control mechanism, not Economic Truth authority.

## SU-005 — Source reconciliation

Decision: ADAPT

SOURCE_RECONCILIATION
!=
ECONOMIC_TRUTH_RECONCILIATION

## SU-006 — Provenance

Decision: ADOPT

Provenance is necessary but insufficient.

## SU-007 — Trusted context

Decision: ADAPT_HEAVILY

Context may include evidence, authority and conflict.

CONTEXT_AUTHORITY
!=
ECONOMIC_TRUTH_AUTHORITY

## SU-008 — Economic Epistemic Promotion

Decision: DEVELOP_AS_CORE_RESEARCH_PRIMITIVE

No MVP promotion through this REA.

## SU-009 — Typed Semantic Authority

Decision: DEVELOP_AS_CORE_RESEARCH_PRIMITIVE

Candidate types:

SOURCE_AUTHORITY
EVIDENCE_AUTHORITY
CONTEXT_AUTHORITY
CALCULATION_AUTHORITY
CLAIM_AUTHORITY
PUBLICATION_AUTHORITY
DECISION_AUTHORITY
ACTION_AUTHORITY

## SU-010 — Publication Authority

Decision: PRESERVE_AND_GENERALIZE

Valid calculation does not imply permission to publish a stronger
economic claim.

## SU-011 — Economic contradiction propagation

Decision: PRESERVE_AND_GENERALIZE

Material contradictions must remain capable of blocking dependent
economic claims and actions.

## SU-012 — Generic Salesforce/UiPath clone

Decision: REJECT

Borrow enterprise governance primitives.

Do not inherit an architecture where operational authorization could
silently substitute for economic truth authority.

AHEAD_PROVEN = 0.
