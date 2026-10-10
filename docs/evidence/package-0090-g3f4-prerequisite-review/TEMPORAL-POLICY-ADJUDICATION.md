# Temporal policy adjudication — D / HOLD

Branch `checkpoint/package-0090-cloud-handoff`; accepted inspection checkpoint
`f9dc0c9abddfc23f33a795f50c45472f06e02b2a`. No ADMIN promotion, policy provisioning,
V6 T0/key/SIGN, TREG R3, runner, new authority or main merge. All source pins are in
[SOURCE-SHA256.json](SOURCE-SHA256.json). Canonical V6 projection matches f9; all nine registration rows absent.
This is a prerequisite review, not a closure claim for operational readiness.


The values did not originate in the same experiment. SPEC21.2 VECTOR_1 (line596)
defines issued/valid_from=epoch+1us and expiry=epoch+1000001us: an exact1s synthetic
binding/manifest interval, with actual/max pairs1s/2s except separate margin and watchdog values.
The fixture encoder reproduces those values. The ADR/SPEC independent technical fixture approval
of2026-10-03 adds only missing preflight tags28/29 at the same1s/2s scale. It is explicitly
TEST_GOLDEN_REHEARSAL_ONLY, not production approval. It does not originate a60s binding policy.
Rehearsal evidence subsequently retains the exact29-tag digest
`e840fcadac2d5198a91cdb7b2345a31d4776cb3ead6e8b697391a4461a1a253d`.

The prior user registration-input request section18 fixes a DB transaction timestamp and
60-second nonrenewable approval window, while explicitly forbidding assumed header equality.
The accepted time-contract review later selects issued_at=valid_from=signed start and
expires_at=signed end (lines47/82/86). Its POLICY_COMPATIBILITY rule (line60) explicitly
requires that60s header lifetime fit the approved BINDING_VALIDITY actual/maximum.
The current continuation accepts this requirement. No general ADR/SPEC numeric60s production
TTL authority was found; its authority is the bounded rehearsal instruction and accepted local profile.

| Value | Source | Semantic name | Start event | End event | Security purpose | Mutable / immutable | Authority | Current consumers |
|---|---|---|---|---|---|---|---|---|
|60,000,000us|Prior request section18; accepted time contract47/60/82/86|Signed approval envelope; deliberately mapped to header lifetime|T_REG transaction opening, T0 read after locks|T0+60s, exclusive|Finite nonrenewable signature/approval/binding eligibility|Original tuple immutable after capture; mapping frozen|Rehearsal approval + PLAN_BINDING_ADMIN profile; not clock/benchmark authority|Manifest22 fields12/13, signature digest, header tags29-31, future composer/JCA/recovery |
|1,000,000us|SPEC21.2 VECTOR_1; FIXTURE-001 tag14; independent Python/JVM encoders|BINDING_VALIDITY actual|Binding valid_from|Permitted valid_from+actual bound|Bound lifetime and nesting of attempts/executions/admission/delivery|Policy version immutable|Synthetic technical fixture authority; separately retained rehearsal row|Policy decoders, nesting checks, header/profile compatibility |
|2,000,000us|Same vector/fixture tag15|BINDING_VALIDITY approved maximum|No separate issuance event; ceiling on actual|Upper bound for independently approved actual|Prevent silent policy widening; NOT runtime grace|Policy version immutable|Same bounded test/rehearsal authority|Actual<=maximum validation, provisioning/profile gate |
|100us /200us|VECTOR_1 tags24/25|WATCHDOG_HEALTH_MAX_AGE actual/max|Last host-qualified checked_at, DB wall time|Fresh DB observation: age<=actual; future denied|Limit stale observer authority|Immutable policy; mutable projection timestamp|Independent trusted host observer + policy governance|Readiness guards; R2 pre/post checks |
|1s /2s|ADR preflight expiry amendment; SPEC approval tags28/29|PREFLIGHT_RECEIPT_TTL actual/max|Q server clock issuance|issued_at+TTL, exclusive|Expire/replay-fence authenticated receipt|Original receipt times immutable|Independent approved policy; Q derives issuance|S01/Q/S13, never signer key lifetime |
|1s /2s|VECTOR_1 transaction pair tags2/3|TRANSACTION_TIMEOUT actual/max|DB transaction opening|Finite transaction wall-time allowance|Bound stalled JVM/transaction, independent of caller SET|Policy immutable|Policy + trusted watchdog|Mutation clock guards and independent enforcement |
|Not separately assigned here|No credential-lifetime tag in this14-pair vector|Credential/private-key process lifetime|Separate governed creation/delivery event|Its own approval/execution destruction boundary|Secret custody/delivery and revocation|Separate contract|Existing credential/signing governance|Cannot substitute for BINDING_VALIDITY or preflight TTL |

SEMANTIC_EQUIVALENCE=CONDITIONAL_BY_EXPLICIT_ACCEPTED_HEADER_EQUALITY,
not equality of all durations or a units-based inference. Actual and maximum are different
kinds of quantities but constrain the same binding interval under that equality.
Numerically equal preflight/transaction TTLs protect different events; watchdog freshness is separate.
The2s maximum is not an extra2s of runtime or a direct timestamp.

Adjudication A is not proven:2s is correct for its original1s vector, not demonstrated obsolete.
B is not proven: fast mechanics do not authorize shortening the signed window or prove it unnecessary.
C is rejected for this accepted profile: the contracts deliberately identify approval/header endpoints.
**D holds for the current frozen combination**:60,000,000 >1,000,000 and >2,000,000.
This is not a theorem that the architecture can never support another separately approved policy/profile.

V043 storage is version/digest/canonical bytes/effective_from; header storage is issued_at/valid_from/expires_at.
Header DDL ck3 checks finite/nonempty intervals; it does not by itself prove the chosen60s profile.
Representative runtime checks consume absolute header expiry, transaction wall time, policy nesting and freshness.
Successful raw staging/crypto in the mechanical fixture cannot override the explicit normative compatibility gate.
No C reinterpretation, max-only increase, min()/clamp, mutable GUC, receipt renewal or fixture substitution is adopted.
