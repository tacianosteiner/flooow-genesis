#ifndef FLOOOW_S03_OBSERVER_INTERNAL_H
#define FLOOOW_S03_OBSERVER_INTERNAL_H
#include "observer.h"
enum s03_diag {D_SCOPE=0,D_ROLE=1,D_PRINCIPAL=2,D_CONTEXT=3,D_SESSION=4,D_PARTICIPANT=5,D_GENERATION=6,D_SOURCE=7,D_INTEGRITY=8,D_TIME=9,D_CUSTODY=10,D_AUTH=11,D_COVERAGE=12,D_DUPLICATE=13,D_CONSUMER=14,D_PROMOTION=15,D_BIRTH=16,D_POPULATION=17,D_BOUND=18,D_MISSING_MEMBER=19,D_EXTRA_MEMBER=20};
typedef struct {uint32_t issues,ready,metadata_ready;uint64_t diagnostics,started,finished;uint32_t role;} S03Work;
__attribute__((visibility("hidden"))) int s03_ref_ok(const S03Ref*);
__attribute__((visibility("hidden"))) int s03_ref_equal(const S03Ref*,const S03Ref*);
__attribute__((visibility("hidden"))) int s03_target_equal(const S03Target*,const S03Target*);
__attribute__((visibility("hidden"))) void s03_issue(S03Work*,enum s03_status,enum s03_diag);
__attribute__((visibility("hidden"))) int s03_prepare(const S03ProtectedContext*,const S03Observation*,S03Work*,uint32_t);
__attribute__((visibility("hidden"))) void s03_check_member(const S03ProtectedContext*,const S03Member*,const S03Target*,S03Work*);
__attribute__((visibility("hidden"))) int s03_finish(const S03ProtectedContext*,const S03Observation*,S03Work*,S03Evidence*,uint8_t*,size_t);
__attribute__((visibility("hidden"))) int s03_health_guard_compute(const S03ProtectedContext*,const S03Observation*,S03Evidence*,uint8_t*,size_t);
__attribute__((visibility("hidden"))) int s03_census_observer_compute(const S03ProtectedContext*,const S03Observation*,S03Evidence*,uint8_t*,size_t);
#endif
