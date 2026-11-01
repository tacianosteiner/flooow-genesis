# ServiceNow REA Decisions

## SN-001 — AI Passport / runtime authority credential

DECISION=ADAPT_STRONGLY

Candidate FLOOOW evolution:

identity
+ authority revision
+ policy revision
+ bounded callable surface
+ context binding
+ expiry
+ revocation

Do not copy the implementation blindly.

---

## SN-002 — Fail-closed runtime authority

DECISION=ADOPT

Principle:

Unknown authorization state must never widen authority.

This does not by itself establish Economic Truth.

---

## SN-003 — Precision revocation / containment

DECISION=ADOPT

Revocation must be architected from authority creation rather than added
after execution architecture is complete.

---

## SN-004 — Context Engine

DECISION=ADAPT

Preserve useful patterns around:

- decision context
- identity
- policy
- relationships
- history
- workflow state

Invariant:

CONTEXT != ECONOMIC TRUTH

---

## SN-005 — Knowledge Graph

DECISION=ADAPT

A graph is a useful substrate for context and relationships.

Invariant:

GRAPH_RELATION != TRUTH_AUTHORITY

---

## SN-006 — Process Mining closed loop

DECISION=ADAPT

Potential future relevance:

- Commerce Observability
- diagnostic intelligence
- process deviation
- root cause
- operational improvement

NO_MVP_IMPLEMENTATION_AUTHORITY

---

## SN-007 — Source reconciliation

DECISION=ADAPT

Preserve the strict distinction:

SOURCE_AUTHORITY
!=
ECONOMIC_TRUTH_AUTHORITY

---

## SN-008 — Value Intelligence / Value Management

DECISION=ADAPT

Calculated business value must not automatically become reconciled Economic
Truth.

---

## SN-009 — Generic AI Control Tower as Economic Truth authority

DECISION=REJECT

Reason:

CONTROL_OVER_AN_AGENT
!=
CONTROL_OVER_REALITY

An agent's authority to execute or assert does not establish the economic
truth of the assertion.

---

## Promotion rule

REA ADOPT / ADAPT decisions are research decisions.

They are not implementation authority.

Promotion requires:

SYNTHESIS
+
ADVERSARIAL REVIEW
+
EXPLICIT ROADMAP PROMOTION
