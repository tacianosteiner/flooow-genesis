# Package 0090 — next original-input authority boundary

S02 is closed at the approved source/predicate scope; S03 source delegates its
original-input comparison to S02 within the same auditor read transaction.
The next boundary is S05/S06, before the registered binding's caller envelope
can become privileged verification/persistence input.

The approval forbids trusting caller signer/signature values or a stored row as
its own independent original expectation. The immutable original record is
private, with exactly eight A/S02 reads and `CONSUMER=S02_ONLY`. V/I/E have none.
The existing native verifier answers whether a signature is valid; it cannot
answer whether that signature is the independently registered original input.
The real SQL/native A/B witness demonstrates the distinction: both signatures
are valid over the same manifest and plan, but the cross-original pairs reject.

Calling S02 from a mutable wrapper is not an authorized solution. R requires
AUDITOR SESSION_USER, REPEATABLE READ and READ ONLY. M requires the authentic
effect session, READ COMMITTED and a mutable transaction. SECURITY DEFINER does
not change SESSION_USER or create a read-policy exception. The frozen V041/V042
dependencies predate the new original commitment and cannot compare it.
Passing an A-generated public projection is also insufficient: it is a read
classification, has no execution possession proof, and is not a new mutation
receipt. No such delegation/receipt subsystem is approved.

This is an authority/information-flow contradiction at the unimplemented mutable
boundary, **not an exploited deployed wrapper**. No S05 placeholder, extra
expected-column grant, R bypass or new mutation authority was introduced.
The existing accepted/native decisions and source guards provide the witness;
protected PostgreSQL and V043 were not executed.

The technically selected handoff is one private ADMIN-owned boolean predicate,
EXECUTE only to V, for S05/S06. It authenticates the exact bound VERIFIER session
and compares caller manifest/algorithm/key/fingerprint/signature against the
immutable original, recomputing canonical bytes/digest and header agreement.
It returns no original fields. ADMIN uses its existing implicit control reads;
V receives no table SELECT. PUBLIC and service direct access remain absent.
V must check it before frozen lookup/persistence; subsequent I/E progress is
permitted only from that verified bound stage lineage.

Proposed exact signature:
`public.offline_internal_matches_original_signed_attestation(uuid,bytea,uuid,text,text,text,uuid,text,bytea) RETURNS boolean`.
The first four inputs are the existing binding tuple; the remaining five are
manifest digest, algorithm, signer UUID, fingerprint and signature. STABLE,
SECURITY DEFINER, CALLED ON NULL INPUT, fixed search_path=pg_catalog,pg_temp,
no defaults/variadic. Wrong session/foreign scope uses uniform ACCESS_DENIED;
missing/corrupt/mismatched original cannot return true. This is a private
comparison dependency of already guarded V wrappers, not an execution proof.

This requires explicit narrow ADMIN function ownership, V EXECUTE and original
input consumer authority. It is not inferred from the S02_ONLY amendment.
After that authority closes: implement S05/S06, continue S07–S18, then complete
remaining guards, transports/goldens and EXECUTE source closure. The unconditional
V043 execution interlock remains throughout.
