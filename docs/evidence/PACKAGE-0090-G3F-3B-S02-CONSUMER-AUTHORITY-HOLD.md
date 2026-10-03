# Package 0090 — next bounded consumer authority gate

The S01 target milestone was committed and pushed on
checkpoint/package-0090-cloud-handoff. A fresh fetch proved local=remote at
746916ff623e899aa1e02e549623c0ce01f0e49c. Work then continued automatically.

S04 is implemented with the existing A/R identity, binding, canonical policy,
activation, READY/watchdog and bounded read-transaction checks. It returns every
history row's six declared fields ordered by installed_rank, preserving NULL
version/checksum, failed entries and extra rows as evidence. It does not truncate,
repair, lock, write or require mutation eligibility. Source/AST checks and
disposable SQLite tests cover empty/malformed/extra history and guard/projection
mutations. Its PUBLIC EXECUTE is revoked; live service-role grants remain separate
deployment administration and were not provisioned.

## Evidence for the next authority boundary

SPEC22.4 requires INSPECT/S02 to preserve the current
PostgresOfflineFieldProofReconciler.inspect predicates/counts. The actual frozen
producer's nonempty-authority branch calls accepted(connection,input), which
calls acceptedArtifact. That query requires current signer-key and signer-authority
joins, state, fingerprints/public-key lineage, approval source/action/role,
permission and verified-at windows. This dependency cannot be dropped without
weakening the required existing inspection semantics.

The machine audit extracts 27 signer columns from that exact producer query.
All are physically granted to A, but their normative consumer traceability is
RECON.acceptedArtifact/S03 only. None is authorized for S02. This is a consumer
scope conflict, not missing physical SELECT privileges. The current S01 approval
extends only the target relations' matchesTarget consumer and six ML observation
reads; it supplies no S02 signer-consumer authority.

A synthetic differential witness executes the exact signer join: an eligible
key produces one row; changing only its state to REVOKED produces zero rows.
Both worlds have identical S02-authorized row projections. This witness proves
the missing fact for that SQL predicate; it is not retained-fixture readiness,
JCA validation or PostgreSQL execution proof. The retained fixture is unchanged.

## Exact executable governance handoff

The next gate is G3F.3B_S02_ACCEPTED_ARTIFACT_CONSUMER_AUTHORITY. Independent
technical governance must resolve S02's required transitive acceptedArtifact
consumer scope. The narrow proposed amendment extends existing A signer-key and
signer-authority traceability to S02 only for the exact existing INSPECT predicate;
the 27 exact relation/column pairs are recorded in S02-CONSUMER-AUTHORITY.json.
No new columns or physical grants are proposed; expected count remains 1032.
Do not infer approval from this proposal, physical ownership or broad capability.

After recorded resolution, update that normative consumer inventory and source
scope checks, implement full S02, then continue S03 and S05-S18 with their existing
frozen codecs/guards. Executor wrappers are not implemented. No speculative
success/denial stubs or overloads were created to simulate implementation closure.

UNRESOLVED_AUTHORITY_BLOCKER_COUNT=1. Separate remaining source work categories
are public-wrapper completion, full transport/commitment golden evidence and
frozen/internal EXECUTE closure. Those are engineering work, not CEO decisions.
The retained mercado-livre/br.com.mercadolivre mismatch remains a separate
fixture/runtime alignment issue. No runtime-positive proof is claimed.

V001-V042 and all 1032 exact physical grants are preserved. V043's unconditional
interlock remains. No protected PostgreSQL, production policy, crypto install,
live service roles, G3G, main merge/push or secret output was attempted.
