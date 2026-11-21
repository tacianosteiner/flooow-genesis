#ifndef FLOOOW_PRIVATE_RAW_BOOTSTRAP_EXPECTATION
#define FLOOOW_PRIVATE_RAW_BOOTSTRAP_EXPECTATION
#include <stdint.h>
/* Private preparation snapshot of actual measured fields only. NOT canonical
 * bootstrap encoding, approved manifest, active policy, generation, enrollment,
 * issuer authentication, source acceptance or source-root membership. */
typedef struct {
    uint32_t magic,version,database_oid,reader_oid;
    uint64_t system_identifier,time_namespace_inode,started_us,finished_us;
    int64_t server_start_pg_us;
    uint64_t memberships,reader_sessions;
    uint8_t boot_id[16],flags[7];
    char reader_name[64];
} S03RawBootstrap;
int s03_prepare_raw_bootstrap(void);
void s03_read_raw_bootstrap(int fd,S03RawBootstrap *value);
#endif
