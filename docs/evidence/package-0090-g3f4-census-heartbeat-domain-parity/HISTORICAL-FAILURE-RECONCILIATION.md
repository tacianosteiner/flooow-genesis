# Historical failures — preserved, never inherited as PASS

Final-byte reruns are selected exclusively by HUP-FINAL-ROUNDS.json. A correction is verified only by the corresponding final assertion; this table records diagnosis, not an automatic PASS override. Read POST-ATTEMPT10-FULL-REGRESSION.json for current results.

| Historical observation | Diagnosis / correction | Required final witness |
|---|---|---|
| Initial role UPDATE privilege checks failed without permission-denied evidence | Preparation expired the old experimental gate lease; denial was fail-closed but did not prove ACL. Experimental preparation lease separated; numeric authority remains NONE | scenarios health/ACL cases |
| Supervisor stall deny-new asserted too early | Harness checked before the experimental progress detector fired; wait for the actual detector event | progress_probe detector, active drain, deny-new and recovery |
| Receiver stall lacked expected detector event | Socket backpressure EAGAIN was incorrectly treated as communication loss; send is now sent/backpressure/failure, never synthetic progress | progress_probe receiver stall |
| Census witness raised bytes/string TypeError | Decode captured subprocess output explicitly; preserve original error | census_probe |
| OID tests denied the wrong role | Old shared denial helper always used test_verifier; probe now logs into the tombstoned auditor identity | oid_probe actual OID reuse and old-binding denial |
| Frozen JVM binding vectors disagreed by microseconds | Floating-point timestamp conversion truncated a microsecond; successor uses integer timedelta arithmetic | independent native/JVM frames and integer Python fingerprint |
| CPU/tmpfs load and subsequent clone cases failed after discarded response | Killing Docker client left the SQL backend executing pg_sleep; independent server catalog quiescence is required before another case | scenarios harness quiescence plus CPU/IO overlap and clone cases |
| First persistent-overlay request lacked overlap marker | Generator was launched but had not created its active marker; bounded preparation now waits for independently observed readiness | storage_probe all four before/after overlap samples |
| Supervisor death left old PostgreSQL generation alive | Receiver control HUP could exit before progress/alive checks, without signaling retained postmaster; HUP path now drains that exact kernel anchor | scenarios supervisor restart, restart_probe supervisor loss, drain_probe final restart |
| Cached PostgreSQL header download failed before setup | Unnecessary re-download suffered HTTP reset; builder now uses the existing exact pinned header and verifies SHA256 | final builders compile pinned header; setup failure remains preserved |

Old failed rounds can also reflect sources copied before a later correction. BUILD-INPUT-SHA256.json and compiler-container source hashes determine which bytes were evaluated. RAW end-of-round source snapshots are not used to rewrite compilation history.

Remaining full-domain/worker/enforcer/replay/control/commit ambiguity/timing/allocation gaps are explicit HOLD/NOT_RUN findings, independently of whether all selected final assertions pass. No complete watchdog, production or canonical readiness PASS is claimed.
