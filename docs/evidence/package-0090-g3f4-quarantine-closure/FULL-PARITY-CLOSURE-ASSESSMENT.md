# Frozen reference boundaries and residual qualification

Status: HOLD — TEST_ONLY_NONCANONICAL. This assessment grants no authority.

The source and kernel snapshot race has a deterministic pre-fix FAIL, a current
observer unit reproduction and a real PostgreSQL delayed-snapshot test. Final
qualification still requires their rerun in the complete immutable matrix.
That result cannot establish full frozen domain or watchdog parity by itself.

The exact frozen references are:

- `applications/marketplace-operations-persistence-postgres/src/main/resources/db/migration/V043__create_governed_offline_field_proof_capability_composition.sql`:
  header, allocation/tombstone, composed capabilities, lifecycle, retry and release.
- `applications/marketplace-operations/src/main/kotlin/io/flooow/marketplace/operations/authorization/AcceptedAttestationVerifier.kt`:
  manifest/preimage, signer/SPKI and immutable artifact verification.
- `applications/marketplace-operations-persistence-postgres/src/main/kotlin/io/flooow/marketplace/persistence/postgres/PostgresAcceptedAttestationVerifier.kt`:
  actual SQL begin/persist adapter and source/authority/consumption joins.
- The hash-pinned protocol V1 and VERSIONED_REHEARSAL_POLICY_CONTEXT structures in
  `docs/evidence/package-0090-g3f4-current-contract-reconciliation/`.

The actual compiled frozen JVM codec and immutable verifier execute on public,
disposable inputs. Native byte encodings, stored framing, actual container-generated
Ed25519 signatures and field mutations are compared. This qualifies selected byte
and artifact boundaries. The synthetic signer lineage/authority fixtures do not
execute the SQL authority, source, economic-evidence or accepted-consumption joins.
The immutable verifier's signer-subject join is an SQL boundary; changing an
unchecked field must not be labeled an integrity-vector PASS.

V043 explicitly states `MIGRATION_EXECUTABLE=NO`, raises SQLSTATE `55000` before DDL,
and says to remove that fence only at recorded implementation closure. Its positive
wrapper stack is not installed or silently extracted into an executable substitute.
Exact extracted table shapes and controlled transactions do not remove this source
execution boundary. Full binding, ownership, retry, release and domain parity remain
HOLD until the recorded source closure permits that exact executable reference.
This is a concrete reference-execution boundary, not a request to access canonical V6.

Actual catalog OID reuse, role recreation, tombstone denial, cold PGDATA clone,
logical dump/restore, retained-anchor enforcement, suppressed signals and query-first
durable-effect checks execute in isolated fixtures. OWNED retention, rollback and
committed/lost-response classifications are measured. They do not prove the entire
frozen claim/attempt/receipt/economic-effect/ownership-release API.

The qualified native enrollment wire covers client backends. The prototype's mandatory
executor guard explicitly excludes other PostgreSQL backend classes, and the census
filters `client backend`. Parallel-worker enrollment, simultaneous participant faults,
and a complete process-class population are not qualified. This is an explicit coverage
gap; COMPLETE_ENROLLED_BACKEND_COVERAGE and COMPLETE_PARTICIPANT_LIVENESS cannot receive
a full PASS. A later test must exercise these classes or deny unsupported governed
execution under an applicable protocol contract; a client-only result cannot imply it.

Actual old ACCEPT bytes and an actual transferred, subsequently dead backend pidfd
are replayed. Current context and native admission recover afterward. A second
concurrently valid trusted socket namespace is now exercised in the bounded protocol
case: a second isolated full synthetic bootstrap admits its own backend, whose exact
captured frame is sent unchanged to the first receiver using the native sender's own
live pidfd and correct kernel credentials. Context reason 3 must deny before catalog
or promotion. This neither transfers a foreign pidfd across namespaces nor qualifies
two fully valid successive SQL authority/consumption ceremonies. Invalid revisions,
malformed peers and old joint epochs cannot substitute for those full populations.

The 21 original NOT_RUN IDs must remain explicitly reconciled to current immutable
case evidence or a concrete full-case limitation. Cross-cohort coverage creates no
new assertions. All raw deferral rows remain preserved. No result is inherited from
the earlier source/binary sets.

All timing, capacity, injected delay, Docker CPU/memory, host awake and load values
are experimental controls. There is no approved numeric ACK/policy/health/resource/
drain authority, and no complete worst-case measurement population. Numerical
candidate readiness and full watchdog/deployment readiness remain HOLD.

Canonical V6, database, IDs, keys, T0, canonical SIGN/ADMIN, TREG, final runner and
production execution remain excluded. Synthetic signing stays inside disposable
container private tmpfs; only public evidence survives owned-resource cleanup.

The final immutable round is `namespace-fixed-final-08`: 16 primary cohorts and
one nested independently bootstrapped namespace cohort, 384 executed assertions,
384 PASS, zero FAIL and zero operational error. Every compiler-copy, input and
end-source inventory matches source set
`be96d53f85fea3ab791fe3575d015964f2dda10617e10b760329b079ae2d14f9`.
The four core binary maps are identical across all 17 actual cold compilations.
The deterministic current observer unit and real delayed PostgreSQL snapshot
case execute again in this round. No development or earlier final-round PASS is
inherited. All 885 historical checks pass.

Raw NOT_RUN rows remain 21. The original 21 exact-case IDs reconcile to 12 bounded
qualifications and nine unresolved full-case qualifications. All raw rows and
their scoped cross-cohort references remain in the final RECONCILIATION.json.
The socket cohort's boilerplate namespace deferral is retained as raw evidence;
it does not execute that test. The same-final-source replay cohort now executes
the bounded foreign-context case. It does not establish arbitrary cross-namespace
descriptor transfer or complete hostile socket populations. This distinction is
explicit in the exact-case disposition and FC-02 finding.

Full closure remains HOLD for the seven findings in CLOSURE-GATE-FINDINGS.md:
one blocker, five high and one medium qualification gap. No commit or push is
performed. The source fence, full process population and authority/consumption
ceremonies cannot be replaced by transport PASS claims.
