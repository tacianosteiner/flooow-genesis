# Independent disposable census / quarantine successor

Scope: TEST_ONLY_NONCANONICAL. Existing disposable implementation and test-only
Ed25519 signing grants only. No canonical deployment or numeric authority.

The predecessor source directory and its 548-file review inventory remain intact.
The successor lives in `scripts/validation/package_0090_quarantine_qualification`.
The final matrix freezes exact bytes of that directory before compilation and
checks the inventory between every cohort. Build input and compiler-copy hashes
are authoritative; end-of-round source snapshots alone are not compilation proof.

The independent observer is an atomic CLONE_PIDFD supervisor child. It retains
the supervisor/receiver/postmaster kernel objects and its own backend descriptors.
Native provisional registration uses exact connected-peer, kernel message-sender
and supplied self-pidfd equality plus server/catalog-derived session identity.
The provisional reply is an internal observation receipt, never an enrollment
ACCEPT. The approved V1 request and ACCEPT wire remain unchanged.

Successful PostgreSQL authentication records a provisional anchor before final
backend-status publication. LOGIN cross-checks that identity against the fully
initialized authenticated/session role and database, performs the protected
lookup and obtains the actual receiver ACCEPT. Only the receiver promotes the
observed entry. Mandatory executor and utility guards require the promoted
entry, current external gate, all retained generation participants alive, and
fresh original emission stamps. A disabled LOGIN event trigger cannot make a
provisional session usable in the tested client-backend paths.

The observer enumerates pg_stat_activity independently of registry discovery.
Numeric PID is corroboration, never a pidfd acquisition or signal selector.
Immutable identity entries are not reused within one observation generation.
Capacity exhaustion denies further registration. Generation quarantine uses an
atomic one-way latch. Known retained anchors are stopped before blocking catalog
observation. The frozen identity inventory and classification are logged before
termination. A late provisional anchor can add evidence about an unknown pending
backend; it cannot become eligible. An unknown backend without a retained anchor
does not yield a confirmed kernel outcome merely because its catalog row vanishes.

The observer survives receiver loss long enough to complete its independent
witness. Planned generation teardown follows confirmed kernel/catalog outcomes.
A dead/stalled observer takes a coarse fail-closed shutdown path with UNKNOWN
evidence. That fallback does not prove full independent enforcement or effects.
Same-generation quarantine never resets on approval restoration or fresh progress;
recovery requires a fresh bootstrap epoch and observation state.

All existing values, and the added observation cadence, injected pauses and
supervisor evidence-collection wait, are experimental harness controls. They do
not authorize, provision or select ACK/policy/health/resource/drain bounds.
PROCESS_ALIVE is distinct from PARTICIPANT_MAKING_PROGRESS. Emission timestamps
use CLOCK_BOOTTIME; queued receipt never replaces the emission instant.

Full frozen SQL semantic parity remains separate from native transport proof.
Exact JVM codec/JCA/immutable artifact verification executes on public disposable
inputs. Synthetic authority/lineage fingerprints do not execute the source,
authority, accepted-consumption, economic-evidence or ownership joins. V043's
55000 safety interlock remains frozen and intact. Its full source cannot be
installed as an executable reference while that interlock remains in force.
Selected exact row shapes and controlled transactions are not full wrapper,
retry-guard or ownership-release parity. No full-watchdog/production PASS follows.

Additional unqualified areas include all-interleaving coverage, complete pending
birth failure populations, hostile descriptor/namespace schedules, allocator
lineage, parallel execution workers, simultaneous participant faults and a complete
measurement population. These limits remain HOLD; they do not authorize widening
the disposable experiment or canonical execution.

PostgreSQL source inspected for ordering and ABI, without installation:

- [REL_18_4 postinit.c](https://raw.githubusercontent.com/postgres/postgres/REL_18_4/src/backend/utils/init/postinit.c): authentication precedes InitializeSessionUserId and final backend-status publication.
- [REL_18_4 auth.c](https://raw.githubusercontent.com/postgres/postgres/REL_18_4/src/backend/libpq/auth.c): ClientAuthentication_hook runs after authentication status is known and before authentication success is sent.
- [REL_18_4 libpq-be.h](https://raw.githubusercontent.com/postgres/postgres/REL_18_4/src/include/libpq/libpq-be.h): Port preserves pointer offsets when GSS is disabled. The experiment accesses no GSS API and adds no development dependency.

The snapshot fix passed the real PostgreSQL delayed-snapshot schedule in
snapshot-runtime-prequalification-01 and the independent frozen-anchor quarantine
path in snapshot-quarantine-prequalification-01. These are development cohorts;
the complete final matrix must rerun them on one immutable byte set.

Snapshot applicability is rechecked before classification, entry-state mutation,
arming, quarantine enforcement and outcome confirmation. The captured context
includes monotonic query start, sealed joint epoch, retained parent kernel inodes
and captured liveness, registry revision, each backend pidfd inode/liveness, phase
and enrollment revision/time. A stale result returns the explicit ignored state;
it cannot arm, manufacture absence, clear quarantine or erase promotion. Current
absence still acts through an expected-phase CAS and retained pidfd. A frozen
quarantined generation may observe its retained dead parents for reconciliation;
that cannot grant admission. Late native anchors reset only the outcome witness
and enforcement capture stage, never the quarantine latch. Their actual identity
is retained and logged before termination.
