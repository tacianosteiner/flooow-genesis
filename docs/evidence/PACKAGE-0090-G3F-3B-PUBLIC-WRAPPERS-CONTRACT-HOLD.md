# Package 0090 public-wrapper prerequisite authority hold

Date: 2026-10-03 (America/Sao_Paulo).
Gate entered automatically: G3F.3B_PUBLIC_WRAPPERS_AND_GUARDS.
Status: HOLD_NEW_READ_AUTHORITY_REQUIRED. One new authority/contract blocker.

The completed Q milestone was committed as
3aa393795a32c3b964a86d6a016cb55be041cb7e, pushed to
checkpoint/package-0090-cloud-handoff, then fetched. LOCAL_HEAD=REMOTE_HEAD at
that milestone. Q remains PASS_BOUNDED_STATIC with96 passing offline tests.
This hold does not retract the fixture/golden/P/Z/Q bounded evidence.

## Exact conflict

SPEC8 assigns S01 to AUDITOR/A and requires
"Controls/catalog/history/org/connections/target reads; A/no locks". SPEC16
requires preflight to prove org/connections/target before claim/effects. The
closed retained fixture explicitly includes ACTIVE organization and ACTIVE
connections/binding_version1. Current connection facts are independent of
retained evidence rows and immutable binding IDs.

SPEC22.4 is the exhaustive per-column authority set. It gives A zero SELECT
columns on public.integration_connection. Q has no economic/connection reads;
its exhaustive capabilities are qualified catalog/encoding/crypto primitives.
A can invoke Q/Z and the four listed pure identity helpers, which do not
provide a current connection-status read. Frozen authority-producing/effect
functions are not an authorized A preflight route and would violate the
read-only/no-lock boundary.

A does already have integration_organization.organization_id/status for
S02 admission validity. Thus organization *column authority* is not missing;
its S01 consumer traceability would need to be recorded. The initial search
missed those S02 rows; the machine audit corrected that finding before any
grant change or hold evidence was committed.

[Machine audit](PACKAGE-0090-G3F-3B-PUBLIC-WRAPPER-PREREQUISITES.json)
extracts the actual normative grant set. Changing one retained connection
from ACTIVE to SUSPENDED leaves every A-authorized fixture row projection
identical. This is an offline information-gap demonstration, not SQL runtime
or a full function noninterference proof. Foreign keys/historical target rows
can establish identities/existence but cannot supply current connection state.
Stored binding equality, a fresh HMAC and a policy/watchdog PASS cannot fill
that missing fact. No zero/identity/completeness is inferred from absent reads.

## Concrete technical handoff — proposed, not approved or executed

The determined narrow resolution is a SPEC22.4 consumer/column amendment:

| Owner | Relation | Columns | Privilege | Consumer | Projection |
| --- | --- | --- | --- | --- | --- |
| A | public.integration_connection | organization_id, connection_id, provider_key, credential_kind, status, binding_version | READ_PRIVILEGE | S01 preflight bound connection readiness | Private predicates only; never service/raw connection rows |
| A | public.integration_organization | organization_id, status (already granted) | READ_PRIVILEGE | Extend existing S02 consumer traceability to S01 | Private ACTIVE predicate only |

At minimum, scoped current status needs organization_id/connection_id/status.
The six-column proposal also supports exact provider/kind/version readiness
from the retained connection contract. Technical governance must approve the
exact predicates/consumer scope and this explicit extension to A's read
authority; it is not inferred from an owner appearing capable. No new helper,
role, schema, whole-table grant, service SELECT, write, lock privilege,
credential binding/secret_ref read, caller selector or returned connection
metadata is proposed. Use header-derived organization/connection IDs only.

After recorded approval: add only the approved per-column grants, update the
normative/source ACL inventory and independent deployment ACL expectations,
implement S01 with full A/R binding/policy guard and scoped live predicates,
delegate sentinel issuance to Q, validate negatives and continue the remaining
public wrappers/guards. Expected source physical-grant count would rise from
1,020 to1,026 if all six proposed new A reads are approved; no current count
or golden is silently changed. Production provisioning remains excluded.

Current action: stop at the user's expressly permitted new-authority/contract
boundary. No speculative S01 success stub, authority widening, SPEC amendment,
DB connection, protected mutation, crypto installation, production policy,
live service role, G3G or main merge/push was performed. V043's interlock stays.
The other three full-closure implementation categories remain incomplete;
they are work categories, distinct from this one new authority blocker.
