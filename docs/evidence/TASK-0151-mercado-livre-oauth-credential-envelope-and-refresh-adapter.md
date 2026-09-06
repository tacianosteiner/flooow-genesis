# TASK-0151: Mercado Livre OAuth Credential Envelope and Refresh Adapter

Status: Authorized
Date: 2026-09-06
Governing ADR: ADR-0052
Specification: SPEC-0051

## Objective

Implement the real Mercado Livre OAuth envelope and one-attempt refresh adapter
over TASK-0150 without changing Connector Runtime or creating a second credential
authority.

## Acceptance

- exact `br.com.mercadolivre` descriptor;
- strict bounded redacted envelope;
- expiry from provider `expires_in`, never hard-coded;
- single-use refresh uncertainty -> INDETERMINATE;
- malformed successful response never blind-retries;
- invalid_grant -> authentication-required;
- no real token/secret committed;
- no live provider call in tests;
- all SPEC-0051 gates pass;
- exactly eight implementation paths change;
- CI/review/merge complete.

No callback, provider data read, migration, scheduler, UI, or provider write is
part of TASK-0151.