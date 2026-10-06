# Package 0090 — independently enrolled process anchor, Phase A

**Kernel/socket sub-proof PASS; complete design HOLD.** Self-creation and transfer close the acquisition/redirection problem for the controlled process. They do not establish a PostgreSQL role/slot/incarnation authorization or an authorized server enrollment entrypoint. No destructive signal, PostgreSQL enrollment extension, SQL function, grant, binding row, watchdog deployment or checkpoint was installed. The nine incoming uncommitted files, including the original five, remain byte-identical.

## Process anchor proof

A running, ordinary single-process backend executing `pidfd_open(getpid(),0)` cannot continue executing that call as a later process after its own death. The fd holds the kernel pid object obtained for the caller. Later signal delivery resolves that object from the fd, not by looking up the numeric PID again. Exit does not redirect it. Numeric PID is metadata/index only; backend_start is database corroboration, not the signal target. This property applies to a backend-self-created fd; it does not rehabilitate external observe/open/revalidate acquisition. [pidfd_open](https://man7.org/linux/man-pages/man2/pidfd_open.2.html), [pidfd_send_signal](https://man7.org/linux/man-pages/man2/pidfd_send_signal.2.html), [Linux v6.18 pid.c](https://raw.githubusercontent.com/torvalds/linux/v6.18/kernel/pid.c), [Linux v6.18 signal.c](https://raw.githubusercontent.com/torvalds/linux/v6.18/kernel/signal.c).

SCM_RIGHTS carries a reference to the same file object; receive installs an independent descriptor referencing it. Closing the sender's descriptor does not close the receiver's descriptor or cause numeric reacquisition. The kernel validates explicit credentials and constructs sender evidence. [Linux v6.18 scm.c, scm_fp_copy and scm_pidfd_recv](https://raw.githubusercontent.com/torvalds/linux/v6.18/net/core/scm.c), [scm_recv_one_fd](https://raw.githubusercontent.com/torvalds/linux/v6.18/include/net/scm.h).

SO_PEERCRED is connect-time identity, not an assertion of who subsequently sends on a transferred connection. SCM_CREDENTIALS is message identity. Neither a numeric credential PID nor UID alone is the durable anchor. The reviewed stronger receiver requires SO_PEERPIDFD for the connected peer, SO_PASSPIDFD-generated SCM_PIDFD for the message sender, and the supplied SCM_RIGHTS pidfd to reference the same process object. Thus an inherited/transferred connection cannot turn stale numeric connect credentials into a new authorized process. The proof uses the actual x86_64 pidfs inode comparison for retained descriptors; a generic anon-inode comparison or unverified platform is forbidden. [Linux v6.18 socket peer handle](https://raw.githubusercontent.com/torvalds/linux/v6.18/net/core/sock.c), [pidfs process-handle comparison](https://raw.githubusercontent.com/torvalds/linux/v6.18/fs/pidfs.c).

These requirements pin a stronger Linux ABI than basic pidfd_open alone. The tested kernel was `6.18.33.2-microsoft-standard-WSL2`; SO_PASSPIDFD, SO_PEERPIDFD, SCM_PIDFD and pidfs comparison all worked under seccomp 2 and UID/GID 999. A companion process-security observation had CapPrm/CapEff zero. That observation is not a complete production isolation audit. Unsupported socket options, missing/truncated ancillary data, unexpected descriptors or unverified handle comparison must deny enrollment and close received descriptors. No alternate numeric PID path is allowed. [Pinned option constants](https://raw.githubusercontent.com/torvalds/linux/v6.18/include/uapi/asm-generic/socket.h).

## Actual bounded experiment

The standalone C harness ran inside the exact existing disposable PG18.4 image, as OS user postgres. It created a private filesystem socket, forked only controlled subjects, and used signal 0 exclusively. Compilation passed `-std=c11 -Wall -Wextra -Werror -O2`. Source, binary SHA-256, disassembly and complete runtime records were preserved privately; the lossless record archive is in the runtime JSON.

| Variant | Actual observation |
| --- | --- |
| Self fd, sender closes local copy | Receiver's fd remained usable while subject lived; peer/message/supplied anchors matched |
| Subject exits before validation | After waitpid reaping, retained anchor returned ESRCH |
| Sender supplies parent-process pidfd | Rejected: supplied anchor differed from kernel sender anchor |
| Two supplied descriptors | Rejected: exact-one-descriptor condition failed |
| Sender attempts to claim parent's credential PID | sendmsg failed EPERM; subsequent genuine self-enrollment matched |

All five subjects produced exit readability and ESRCH after reaping. Each retained kernel sender anchor remained ESRCH across 128 subsequently forked/reaped children: 640 total. Numeric PID reuse was not observed. This is bounded runtime corroboration; the no-redirection guarantee follows from kernel object references, not non-reproduction. A kernel-produced sender descriptor remains a reference to the sender even after the queued message outlives it.

Death readability must take precedence over a successful signal-0 result. A zombie can still produce syscall success before reaping, as the preceding Phase-A evidence observed. Receiver admission and pre-action checks must reject a readable/dead anchor; ESRCH maps to TARGET_ALREADY_GONE. Sending a signal successfully is never proof of cancellation or termination. No such destructive action was tested here.

## Private socket boundary

Choose a pathname AF_UNIX SOCK_SEQPACKET socket, not an abstract socket. Proposed production placement is a private runtime directory such as `/run/flooow-watchdog`, owned by the trusted PostgreSQL runtime UID/GID, directory 0700 and socket 0600. The trusted receiver needs signal permission for PostgreSQL targets; sharing the PostgreSQL OS UID avoids adding CAP_KILL. Socket placement must be fixed by trusted deployment configuration, never caller-selected. Parent path ownership, no symlink substitution, mount isolation and receiver identity require deployment verification before release.

Application containers/processes must receive no mount of that runtime directory and no socket descriptor. The socket is not published to the host or unrelated containers; untrusted host users receive no Docker administrative access. Trusted root/host/DB administration remains outside the existing operational attacker model. OS UID is a prerequisite, not a database-role proof. The standalone `/tmp` directory/socket exercised 0700/0600 ownership and was removed after the run; it was not a deployed watchdog endpoint. Linux pathname permissions support this choice, whereas abstract sockets have no filesystem permission control. [unix(7)](https://man7.org/linux/man-pages/man7/unix.7.html).

## Server identity and unresolved entrypoint

The candidate SQL API, **not installed**, is zero-argument `offline_watchdog_enroll_self() RETURNS text`, with a closed typed-result vocabulary. No PID, database, role, socket path, deployment UUID or incarnation UUID is accepted from the caller. A reviewed implementation would assert getpid()==MyProcPid, MyProc exists, ordinary client backend, current postmaster membership and non-superuser authenticated identity; create its own pidfd; send one bounded enrollment frame/descriptor; close its local copies; return only an enrollment status. CANCEL/SIGINT and TERMINATE/SIGTERM belong exclusively to the trusted receiver's later closed action API.

| Field | Server source | Caller-controlled authority | Immutability/required validation |
| --- | --- | --- | --- |
| PID | MyProcPid corroborated with getpid() | NO | Running backend identity; numeric reuse is handled by fd |
| Database OID | MyDatabaseId | NO | Fixed per backend after initialization; exact allowed DB |
| Authenticated login | GetAuthenticatedUserId() | NO | Authenticate once; verify catalog OID/name and attributes |
| Session role | GetSessionUserId() | NO for ordinary governed login | Must equal authenticated identity; reject proxy/SET ROLE ambiguity |
| Effective role | GetUserId() | Not an enrollment identity source | SECURITY DEFINER can change it; never substitute it for authenticated login |
| Backend type | MyBackendType/B_BACKEND | NO | Exclude auxiliary/worker/autovacuum/walsender/postmaster |
| Backend start | MyStartTimestamp | NO | Match live backend status; not an OS generation token |
| Postmaster PID | PostmasterPid | NO | Numeric field alone does not prove a postmaster epoch |
| Server generation | ADMIN fresh pg_postmaster_start_time plus trusted receiver epoch | NO when validated | Complete native generation binding remains unproved |
| Deployment/incarnation/slot | Validated immutable header identity_slots + protected readiness + approved host incarnation | NO when validated | Missing, ambiguous or mismatched mapping denies |

Native field sources are pinned PostgreSQL REL_18_4. Authentication, session and effective user IDs are distinct. A function must finish initialization and use authenticated/session identity before treating database fields as evidence. [miscadmin.h](https://raw.githubusercontent.com/postgres/postgres/REL_18_4/src/include/miscadmin.h), [miscinit.c](https://raw.githubusercontent.com/postgres/postgres/REL_18_4/src/backend/utils/init/miscinit.c).

Existing canonical sources are SPEC sections 3/4/5/18 and V043 offline_binding_header/offline_readiness. The immutable header binds deployment/incarnation and the four exact role OID/name slots. Readiness alone does not bind an arbitrary service PID to one slot. Services have no raw control-table reads and only the exact assigned EXECUTE surface. A SQL-callable enrollment function adds service EXECUTE authority; it cannot silently be added to S01–S18 or inferred from socket semantics.

Current disposable observation: binding_header_count=0; readiness NOT_READY; watchdog_healthy=false. Therefore **the current canonically bound caller set is empty**, and no positive Package0090 enrollment authorization was manufactured. Existing populated headers could be read by the already-trusted ADMIN receiver without a new persistence schema, but they were not present here. Provisioning a new header/role-incarnation authority is outside this proof. The native sender's exact privilege route to derive that binding is also unclosed.

SPEC18 requires monitoring all bound service backends: auditor bounded reads and verifier/issuer/executor work all require coverage. This derives the future caller set from exact validated immutable slots; it does not authorize grants to four existing rehearsal logins merely because their names resemble those slots. A passive server-startup enrollment hook might avoid a SQL EXECUTE delta, but its initialization timing, authenticated identity availability, pre-BEGIN coverage and canonical binding have not been proved. It remains an alternative design hypothesis, not a deployed narrower mechanism.

Under request sections 8/19/23, the required additional authority or unproved alternative keeps the complete design HOLD. The PostgreSQL test-only positive enrollment prototype was **not installed/run**: that would require an entrypoint/binding privilege route that this review has not established. Standalone kernel/socket PASS is not reported as PostgreSQL runtime PASS.

## Receiver validation and freshness requirements

Require one complete versioned bounded frame, one rights fd, kernel credentials and sender pidfd; compare all retained anchors, UID and declared PID. Reject any mismatch/truncation or dead anchor before database binding. Use the exact ADMIN connection to the allowed database. New short READ COMMITTED transactions, no long-lived REPEATABLE READ snapshot, clear backend-statistics local snapshots before each observation, and a fresh exact pg_stat_activity lookup are required. Match native metadata to database OID, authenticated role OID/name, backend type and backend_start; independently decode/validate canonical slots and exact protected deployment/incarnation evidence. Check anchor death again after observation. No activity label is authority. Cached statistics cannot be relied on to establish a currently live backend. [PG18 backend_status.c](https://raw.githubusercontent.com/postgres/postgres/REL_18_4/src/backend/utils/activity/backend_status.c).

Only the retained descriptor selects a later signal target. Pre-action authorization is a separate obligation: fresh incarnation, managed-slot state, policy/watchdog authority and recovery supersession must be revalidated under the existing administrative serialization contract. No proven action-time authorization serialization was implemented here. A changed/unknown authority closes/inactivates the enrollment and denies action; a fresh DB row never causes reacquisition by numeric PID.

## Race and lifecycle requirements

| Boundary | Required safe outcome | Evidence level |
| --- | --- | --- |
| A: death before self-open | Dead caller cannot execute/open later PID owner | Kernel/source reasoning |
| B: death after open, before send | No valid enrollment; local fd closes on exit | Source/design |
| C: death during transfer | Queued references still point to A; reject dead anchor | Source; early-exit runtime corroboration |
| D: death after receive | Mark gone, remove membership, close fd; never reacquire PID | Runtime reaping/ESRCH |
| E: reuse before DB validation | Retained A handle remains A; dead check rejects | Kernel contract; actual reuse not observed |
| F: reuse after DB validation | Descriptor action can only address A or fail | Kernel contract; no destructive test |
| G: reconnect/replay | New receiver epoch/challenge and exact peer/message anchors; no payload-only replay | Design requirement, not exercised |
| H: same-backend duplicate | Idempotent same-anchor registration; close extra descriptors, retain original | Policy proposed, not exercised |
| I: same-slot different backend | Maintain bounded set of distinct live anchors; never overwrite another live backend | Policy proposed, not exercised |
| J: incarnation change | Invalidate all prior-epoch enrollments, deny action and close handles | Policy proposed, not exercised |

An ephemeral receiver-generated connection challenge may correlate one enrollment attempt; it is not canonical authority and must not be treated as a persisted secret. Complete replay/epoch implementation is not proven by the current harness. Multiple physical connections for the same slot are legitimate until the authority model says otherwise; slot uniqueness must not silently suppress monitoring.

Application physical connections are on demand and closed after use. Required enrollment lifecycle is one anchor per physical backend, confirmed before governed work, invalidated on backend exit; reconnect requires a new anchor. No transaction-by-transaction reuse of a previous process descriptor is allowed. The canonical adapter connection paths were not changed. A startup hook is the narrower prospective integration; a service SQL call would require an explicit new capability. Production overhead and PostgreSQL enrollment latency were not measured; the standalone proof's five transfers are not a pooling/performance benchmark. Pooling is not required for identity correctness and was not introduced; operational necessity remains unmeasured.

## Disposition

The socket bridge is a proposed implementation of SPEC18's existing trusted independent watchdog boundary, not authority to alter business/domain data. However its server entrypoint and canonical enrollment authorization remain unclosed. Kernel safety PASS is retained; overall DESIGN_SECURITY_REVIEW=HOLD. This does not retract the preceding rejection of observe/open/revalidate or promote socket UID into a governed-role certificate.

Both non-secret authority fingerprints are `d697579bb78f8ecffbeb1407a100a2ef400bebd761967bfa6af8059c1379632c`. All roles, attributes, memberships, ownership, ACL/default ACLs, policy and migration state were identical. Tracked files and nine incoming artifacts were unchanged. No password rotation; plaintext startup file erased; disposable container stopped; fixture/bounds unchanged. G3F.4 remains HOLD: BLOCKER=0/HIGH=2/MEDIUM=0/LOW=0, H01 and watchdog deployment HIGH OPEN.

No commit/push: request section24 permits the checkpoint after complete security proof PASS. Next bounded gate is the governed enrollment entrypoint and deployment/slot/incarnation authority review, including the zero-EXEC passive-hook alternative and exact existing-source binding. Only after that closes can the PostgreSQL enrollment proof and identity-signal primitive gate proceed.
