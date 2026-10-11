# Successor scope and evidence provenance

Input branch: checkpoint/package-0090-cloud-handoff.
Input HEAD: 0078290f79c8e6bcdc7b124ca0ae24963a915e2d.
No commit or push is authorized while this mission retains open findings or incomplete regression.

All runtime work is independently isolated TEST_ONLY_NONCANONICAL PostgreSQL 18.4 rehearsal. Containers use the pinned image, network none, no mounts/ports/volumes, bounded resources and a narrowly frozen seccomp profile. Fresh synthetic roles/database/UUIDs and test-only Ed25519 keys exist solely inside owned rehearsal containers. Host JVM work performs public encoding/verification only. No canonical V6, canonical identity, canonical key, T0, canonical ADMIN, TREG or final runner is accessed.

The successor directory contains copied predecessor harness files plus bounded new implementation. No predecessor file, canonical migration, runtime application or dependency is modified. The builder compiles current C directly; it does not invoke the historical source-generation transform. Never run evolve.py to regenerate over reviewed successor C.

## Heartbeat correction

The private socketpair carries the kernel sender pidfd and a nine-byte marker/emission timestamp frame. CLOCK_BOOTTIME is monotonic and includes suspension. Receipt validates exact framing, retained sender identity, kernel liveness, strictly increasing emission time, no future timestamp and experimental freshness. Invalid or old frames never update the last progress timestamp. Socket backpressure does not invent progress or imply a communication failure. EOF/invalid frames are fail-closed.

Receiver admission rechecks retained participants, root custody gate, original emission freshness and enrollment deadline after waiting for socket writability and immediately before constructing/sending ACCEPT. Standalone adversarial vectors include a frame fresh at emission, actually left queued beyond the experimental lease, then rejected without renewal. A process being alive is explicitly separate from its progress timestamp; SIGSTOP cases qualify selected stalled participants.

This is selected mechanism evidence, not a proof of every adversarial scheduling race or complete watchdog architecture. Serial receiver census/catalog queries and coarse postmaster generation shutdown remain material coverage/availability limitations.

## Frozen parity

The timestamp codec now uses integer epoch microseconds; historical floating-point truncation mismatches are retained, followed by corrected frozen JVM vectors. Independent native typed encoding matches three exact frozen JVM frames, and the actual stored synthetic header matches the Python fingerprint. Production JVM public primitives verify manifest decode/encode, signature preimage, original signature and tamper rejection. This does not qualify complete AcceptedAttestationVerifier semantics, source/consumption evidence joins, signer authority or the full ownership/retry wrappers. The frozen V043 execution interlock remains intact.

## Round provenance

Historical failed rounds are retained as historical evidence, never substituted as final PASS. HUP-FINAL-ROUNDS.json records the complete native reruns after the control-HUP race correction. FINAL-SELECTED-ROUNDS.json replaces only broad collection/preparation and drain error-handling cohorts on the identical frozen final native bytes. Superseded rounds remain linked; the known final-byte census/quarantine race remains OPEN even if a harness retry passes. Each build captures BUILD-INPUT-SHA256.json before copying and compiler-container C/header hashes in BUILD.json; RAW-QUALIFICATION.json records binary hashes and cleanup. The aggregate requires final runtime-source equality.

An intermediate broad regression found receiver control-channel HUP could bypass the next progress/alive check and exit without stopping its retained postmaster. The corrected HUP branch sends SIGINT through that exact retained anchor before exit; all runtime cohorts are rerun after this additional correction. Earlier heartbeat PASS is not reused across that change.

Earlier RAW source_hashes and SOURCE.json were collected at completion while successor host files evolved; these are not compilation provenance. Use explicit COMPILED-SOURCE snapshots, pre-build input hashes and inside-container copy hashes. Initial regression-main has a separate REGRESSION-COMPILED-SOURCE snapshot. Final aggregate excludes historical runtime results from its pass counts.

The scoped .gitattributes preserves public binary vectors and raw JSON/text/log snapshots without Git line-ending conversion. Raw logs retain intentional EOF blanks. Whitespace review accepts Windows CRLF while retaining trailing-space/editor checks; raw evidence is not rewritten to silence a formatting tool. Non-secret JVM helper binaries are preserved in public-helper-binaries and their temporary copies removed.

Ownership row-shape/rollback/query-first witnesses preserve UNKNOWN and OWNED without automatic retry/release. They are not full governed wrapper execution. OID reuse is directly forced only in the disposable catalog and old-binding tombstone denial is measured; fresh governed allocation lineage is not qualified. No stronger authority or full-domain PASS follows from these fixtures.
