# Package 0090 ? mutation original-input authority closed

The 2026-10-04 governance approval at baseline d3f881c authorizes the exact
private ADMIN-owned boolean predicate, EXECUTE to V only. The earlier HOLD is
superseded by this explicit authority, not by a reinterpretation of S02_ONLY.

`public.offline_internal_matches_original_signed_attestation(uuid,bytea,uuid,text,text,text,uuid,text,bytea)`
authenticates the bound VERIFIER SESSION_USER and exact binding tuple, then
recomputes the independently registered original canonical bytes and commitment
and compares all five signed envelope fields exactly. It returns no original
values. No V/I/E original table reads were added. Column grants remain 1040.
PUBLIC, A, I, E and services receive no helper EXECUTE. V alone receives the new
non-grantable EXECUTE and public schema USAGE for its static dependency calls.

The actual helper passed the A/A=true, A/B=false, B/A=false, B/B=true matrix in
network-disabled disposable PostgreSQL, using the independently valid original
A/B fixture. Wrong session/binding/plan/incarnation/surface and every NULL
argument deny with sanitized P0017 ACCESS_DENIED. Envelope mismatches, missing,
duplicate and corrupted originals return false. Disposable effective ACL checks
prove no PUBLIC/service/A/I/E helper access or V original table SELECT.

This closes the helper boundary only. The next determined action is complete
S05/S06 implementation requiring helper TRUE before frozen lookup/persistence,
then S07-S18, remaining guards/transports/goldens and EXECUTE closure. Protected
PostgreSQL and V043 were not executed; the migration interlock remains intact.
