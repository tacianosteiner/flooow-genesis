# FLOOOW — ARKOM Technical / Operating Model Research

Status: RESEARCH / INFERENCE BOUNDED
Captured: 2026-10-10

## What is publicly supported

ARKOM's terms describe AI-assisted operational applications including:
- customer service;
- SDR;
- advertising management;
- HR;
- finance;
- legal;
- analytical dashboards;
- third-party integrations.

The public website also describes a Genesis builder for creating AI/agents.

A documented construction-sector case states that an AI SDR/pre-service system was connected to the customer's historical data and CRM and used to receive, filter, answer and register leads.

## Operating architecture visible from public evidence

The public experience appears to contain four layers:

1. BUSINESS DIAGNOSTIC
   Choose a high-volume, standardized process with low initial decision risk.

2. PREBUILT AI SYSTEM
   Select a prepared operational system or use the builder/custom implementation.

3. IMPLEMENTATION SUPPORT
   Guidance, mentoring, training and human ownership.

4. OUTCOME MEASUREMENT
   Hours saved, process throughput and/or revenue-related results.

## Important design principle

ARKOM publicly recommends human review for early implementations and discourages beginning with high-risk decisions.

This is compatible with a staged autonomy model.

## Technical details not publicly proven

No conclusion should be made yet about exact:
- foundation models;
- orchestration framework;
- vector database;
- RAG stack;
- workflow engine;
- observability vendor;
- evaluation framework;
- hosting architecture;
- tenant isolation;
- secrets management;
- authorization architecture;
- model routing;
- prompt/version registry.

These require technical evidence, hiring signals, product inspection, public repositories, documentation or direct vendor discussion.

## Reverse-engineering questions for future research

- Is Genesis a low-code agent builder or a template configurator?
- Are operational systems isolated apps or a shared agent runtime?
- Is there a canonical business object layer?
- Is memory tenant-scoped and auditable?
- Can actions write into CRM/ERP automatically?
- What approvals protect high-risk actions?
- How are model/provider changes evaluated?
- Is there deterministic workflow support alongside agents?
- How are failures retried?
- How are tool permissions assigned?
- Is there a control plane for all deployed agents?
- Is ROI measured through first-party telemetry or customer self-report?

## FLOOOW lesson

Do not copy the unknown stack.

Copy the product principle:
make the first useful AI outcome simple enough for a normal company to implement.

Then improve the architecture with FLOOOW's stronger truth/authority/reconciliation model.
