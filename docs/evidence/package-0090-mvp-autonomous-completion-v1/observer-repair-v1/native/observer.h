#ifndef FLOOOW_S03_OBSERVER_V1_H
#define FLOOOW_S03_OBSERVER_V1_H
#include <stddef.h>
#include <stdint.h>
#include <stdatomic.h>
struct S03Terminal;
/* Private candidate ABI for exactly two existing roles, not a native message
 * purpose, public ingress or source-acceptance format. Inputs are qualified
 * typed exports from the existing protected source/context seam. Arbitrary
 * callers cannot make those inputs trusted by constructing these C structs.
 * Production acquisition remains SourceUnavailable until independently bound.
 */
#define S03_REF_BYTES 96u
#define S03_NAME_BYTES 64u
#define S03_MAX_MEMBERS 64u
#define S03_FRAME_LIMIT 1048576u
#define S03_SOURCE_COUNT 8u
enum s03_role {S03_HEALTH_GUARD=1,S03_CENSUS_OBSERVER=2};
enum s03_status {S03_OBSERVED_MATCH=0,S03_OBSERVED_MISMATCH=1,S03_UNKNOWN=2,S03_MISSING=3,S03_UNAVAILABLE=4,S03_STALE=5,S03_AMBIGUOUS=6,S03_BINDING_MISMATCH=7,S03_CONTRADICTED=8,S03_INTEGRITY_FAILURE=9};
enum s03_source_state {S03_SOURCE_PRESENT=1,S03_SOURCE_MISSING=2,S03_SOURCE_UNAVAILABLE=3,S03_SOURCE_UNKNOWN=4,S03_SOURCE_CONTRADICTED=5,S03_SOURCE_INTEGRITY_FAILURE=6};
enum s03_source_slot {S03_SRC_EXPECTED=0,S03_SRC_PUBLIC=1,S03_SRC_BRIDGE=2,S03_SRC_NATIVE=3,S03_SRC_AUTH=4,S03_SRC_CUSTODY=5,S03_SRC_GENERATION=6,S03_SRC_BARRIER=7};
/* kind+size+bytes are the full already-validated canonical typed reference,
 * not a hash-only identity, pointer, PID or new authority record. Qualified
 * upstream text encoders enforce NFC; adapters do not decode untrusted wire.
 */
typedef struct {uint32_t kind,size;uint8_t bytes[S03_REF_BYTES];} S03Ref;
typedef struct {uint32_t size;uint8_t bytes[S03_NAME_BYTES];} S03Name;
typedef struct {S03Ref source_id,source_authority,source_provenance,source_acceptance;uint8_t integrity[32];} S03Source;
typedef struct {S03Ref principal,birth,session,channel,context;uint32_t role;} S03Observer;
typedef struct {S03Ref context,server_generation,birth,session,registry_revision,participant,principal;uint64_t generation;int64_t server_start_pg_us,backend_start_pg_us;uint32_t database_oid,role_oid,pid;S03Name role_name;} S03Target;
typedef struct {uint32_t database_oid,role_oid,pid;S03Name role_name;S03Ref source_row;} S03PublicRow;
typedef struct {S03Target bridge;S03Ref native_birth;S03PublicRow public_row;uint32_t bridge_presence,liveness_before,liveness_after;S03Name backend_type;} S03Member;
typedef struct {S03Ref boot,time_namespace,barrier,acquisition,snapshot,custody,authentication,policy,challenge;uint64_t started_us,finished_us,barrier_valid_until_us;} S03Window;
typedef struct {
 uint32_t version,max_rows,max_bytes;uint64_t not_before_us,expires_us,max_age_us;
 S03Observer observer,other_observer;S03Target target;
 S03Source source[S03_SOURCE_COUNT];S03Ref origin_channel_binding,creator_principal,verifier_principal,population_scope;
 S03Window window;uint32_t expected_count;S03Target expected[S03_MAX_MEMBERS];
 int evidence_fd;uint64_t evidence_device,evidence_inode;
 struct S03Terminal *terminal; /* Existing one-challenge result owner, never a ledger. */
} S03ProtectedContext;
typedef struct {
 S03Observer observer;S03Target target;S03Window window;
 uint32_t source_state[S03_SOURCE_COUNT];S03Source source[S03_SOURCE_COUNT];
 uint32_t consumer_kind,requested_output_kind,coverage,count;
 S03Ref population_scope;S03Member members[S03_MAX_MEMBERS];
} S03Observation;
typedef struct {uint32_t role,status,evidence_only,frame_size,delivery_state;uint64_t diagnostics,observed_started_us,observed_finished_us;uint8_t content_digest[32];} S03Evidence;
/* Owner is the existing protected S03 membrane; zero-initialize once before
 * publishing the frozen invocation. No reset/rebind API or production factory.
 * Distinct role processes own distinct cells. This mirrors S03 used/result.
 */
typedef struct S03Terminal {atomic_uint state;uint8_t input_digest[32];int result_code;S03Evidence result;uint8_t frame[S03_FRAME_LIMIT];} S03Terminal;
/* Return0 means only a bounded evidence frame was emitted (including failures).
 * It never means true/healthy/qualified/accepted. -1 invalid/unbound context;
 * -2 unavailable sink/clock; -3 resource/crypto failure; -4 stale replay;
 * -5 invocation busy/invalid terminal state; -6 conflicting replay.
 * No default activation. A nonzero return never establishes an output.
 */
__attribute__((visibility("default"))) int s03_health_guard_observe(const S03ProtectedContext*,const S03Observation*,S03Evidence*,uint8_t*,size_t);
__attribute__((visibility("default"))) int s03_census_observer_observe(const S03ProtectedContext*,const S03Observation*,S03Evidence*,uint8_t*,size_t);
#endif
