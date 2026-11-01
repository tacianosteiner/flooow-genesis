# REA-5 — Salesforce + UiPath

Status: RESEARCH
Decision authority: NONE
Implementation authority: NONE
MVP impact: NONE

## Executive finding

Salesforce and UiPath invalidate generic agent governance,
orchestration, observability, provenance and fail-closed execution as
standalone FLOOOW differentiation.

Both expose mature enterprise primitives around governed AI execution.

OVERALL_EXTERNAL_MATURITY = 5/5
THREAT_LEVEL = EXTREME
FLOOOW_POSITION_TODAY = BEHIND
AHEAD_PROVEN = 0

## Salesforce

Agentforce Session Tracing captures detailed runtime information
including:

- sessions
- participants
- interactions
- messages
- steps
- reasoning execution
- actions
- prompt/gateway inputs and outputs
- errors
- final responses
- references to LLM calls
- feedback and guardrail metrics

Therefore generic agent tracing and observability are not FLOOOW moats.

Data 360 also exposes source reconciliation and lineage concepts.

Reconciliation can use:

- most recent
- most frequent
- source priority

while retaining source data.

Therefore source priority, source reconciliation and provenance alone
are not FLOOOW moats.

Salesforce engineering material on trusted context describes a runtime
sequence:

RESOLVE
→ PLAN
→ RECONCILE
→ GOVERN
→ COMPILE
→ LEARN SELECTIVELY

The RECONCILE stage ranks evidence by:

- relevance
- authority
- freshness
- provenance

while keeping conflicts visible.

This invalidates weak claims that FLOOOW is differentiated merely
because it understands evidence authority, provenance or conflict.

## UiPath

UiPath Agents supports deterministic custom guardrails around tool
calls.

Guardrails can operate before and/or after execution.

Documented actions include:

LOG
FILTER
BLOCK
ESCALATE

Tool confirmations can also require user approval before external
side effects.

Therefore:

- deterministic guardrails
- FAIL CLOSED behavior
- human approval
- tool-level policies
- escalation
- trace visibility

are not sufficient FLOOOW differentiation.

## What REA-5 destroys

Do not claim standalone moat from:

- agent registry
- agent orchestration
- agent observability
- session tracing
- human-in-the-loop
- deterministic guardrails
- generic fail-closed behavior
- source lineage
- source priority
- source reconciliation
- evidence ranking
- authority-aware context
- conflict preservation alone
- deterministic versus probabilistic separation

## Authority over what?

The surviving architectural question is semantic.

Enterprise platforms can govern:

WHO MAY READ
WHO MAY ACCESS
WHO MAY REASON
WHO MAY CALL A TOOL
WHO MAY EXECUTE
WHO MAY APPROVE
WHICH DATA MAY ENTER CONTEXT

The candidate FLOOOW addition is:

WHAT MAY BE ASSERTED AS ECONOMICALLY TRUE

This leads to typed semantic authority.

## Typed Semantic Authority

Candidate chain:

SOURCE_AUTHORITY
→ EVIDENCE_ADMISSIBILITY
→ CONTEXT_AUTHORITY
→ CALCULATION_AUTHORITY
→ CLAIM_AUTHORITY
→ PUBLICATION_AUTHORITY
→ DECISION_AUTHORITY
→ ACTION_AUTHORITY

No authority type automatically implies the next.

Examples:

AUTHORIZED_TO_ACT
!=
AUTHORIZED_TO_CLAIM

AUTHORIZED_TO_CLAIM
!=
PROVEN_TRUE

AUTHORIZED_TO_CALCULATE
!=
AUTHORIZED_TO_PUBLISH

CONTEXT_AUTHORITY
!=
ECONOMIC_TRUTH_AUTHORITY

Classification:

DIFFERENT_CANDIDATE.

## Economic Epistemic Promotion

Candidate FLOOOW primitive:

RAW SIGNAL
→ EVIDENCE
→ ADMISSIBLE EVIDENCE
→ ECONOMIC CALCULATION
→ ECONOMIC CLAIM
→ PROOF-BEARING CLAIM
→ PUBLISHED ECONOMIC TRUTH
→ DECISION
→ ACTION
→ ACTUAL OUTCOME
→ REALIZED ECONOMIC TRUTH

Each semantic transition is a governed promotion.

No integrated public Salesforce or UiPath equivalent to this complete
economic chain was established.

Classification:

DIFFERENT_CANDIDATE.

## Contradiction example

Suppose:

Amazon COGS = 80
ERP COGS = 91
Supplier invoice = 94
Landed cost = 103

Source lineage and source reconciliation are useful.

But for a material economic claim FLOOOW may need:

COGS = CONTRADICTED
→ MARGIN = NOT_ASSEMBLED
→ PROFITABILITY_PUBLICATION = DENIED
→ MARGIN_DEPENDENT_ACTION = BLOCKED

rather than silently resolving the contradiction through source
priority.

This is an economic truth semantic, not merely data unification.

## Anti-copy analysis

IF WE COPIED THIS EXACTLY, WHAT WOULD WE DESTROY IN FLOOOW?

A direct clone could collapse:

context authority
into
truth authority,

or:

tool authorization
into
economic claim authority.

FLOOOW should adapt enterprise governance and observability primitives
without allowing operational authority to become epistemic authority.

## Evidence register

### S5-001
Class: OFFICIAL_DOCUMENTATION
Source:
https://help.salesforce.com/s/articleView?id=ai.generative_ai_session_trace.htm&language=en_US&type=5

Supports:
Detailed Agentforce session tracing.

Limit:
Observability does not itself establish economic truth semantics.

### S5-002
Class: OFFICIAL_DOCUMENTATION
Source:
https://help.salesforce.com/s/articleView?id=ai.generative_ai_session_trace_data_model.htm&language=en_US&type=5

Supports:
Session/participant/interaction/message/step data model and references
to LLM calls and guardrail/feedback metrics.

Limit:
Runtime trace semantics, not economic claim authority.

### S5-003
Class: OFFICIAL_DOCUMENTATION
Source:
https://help.salesforce.com/s/articleView?id=data.c360_a_omni_reconciliation.htm&language=en_US&type=5

Supports:
Source-priority reconciliation for unified data.

Limit:
Data reconciliation is not automatically Economic Truth reconciliation.

### S5-004
Class: OFFICIAL_DOCUMENTATION
Source:
https://architect.salesforce.com/docs/architect/fundamentals/guide/data-360-architecture

Supports:
Reconciliation while source records remain available.

Limit:
Unified profile semantics differ from canonical economic truth.

### S5-005
Class: PUBLIC_TECHNICAL_TALK
Source:
https://engineering.salesforce.com/how-data-360-builds-trusted-context-the-enduring-layer-for-enterprise-ai/

Supports:
Resolve, Plan, Reconcile, Govern, Compile and Learn Selectively;
evidence ranked by relevance, authority, freshness and provenance while
conflicts remain visible.

Limit:
Engineering description of trusted AI context; no complete public
economic claim authority chain established.

### U5-001
Class: OFFICIAL_DOCUMENTATION
Source:
https://docs.uipath.com/agents/automation-cloud/latest/user-guide/tool-guardrails

Supports:
Deterministic tool guardrails before/after execution with Log, Filter,
Block and Escalate.

Limit:
Tool governance is not economic truth governance.

### U5-002
Class: OFFICIAL_DOCUMENTATION
Source:
https://docs.uipath.com/agents/automation-cloud/latest/user-guide/conversational-agents-agent-builder-design

Supports:
Tool-call confirmations and user approval before external side effects.

Limit:
Action approval does not imply claim/publication authority.

## Epistemic conclusion

PUBLIC_EQUIVALENT_TO_TYPED_SEMANTIC_ECONOMIC_AUTHORITY =
NOT_ESTABLISHED

PUBLIC_EQUIVALENT_TO_ECONOMIC_EPISTEMIC_PROMOTION =
NOT_ESTABLISHED

PUBLIC_EQUIVALENT_TO_ECONOMIC_PUBLICATION_AUTHORITY =
NOT_ESTABLISHED

PUBLIC_EQUIVALENT_TO_CANONICAL_ECONOMIC_RECONCILIATION =
NOT_ESTABLISHED

AHEAD_PROVEN = 0
