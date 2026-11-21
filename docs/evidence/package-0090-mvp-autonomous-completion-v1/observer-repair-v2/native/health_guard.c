#include "observer_internal.h"
/* purpose/observation_target/input/session_binding/output/failure_semantics:
 * JOIN_EXACT_TARGET_V1 + HEALTH_BOUND_LIVENESS_V1. No role-selected dispatch. */
int s03_health_guard_compute(const S03ProtectedContext *r,const S03Observation *in,S03Work *w,S03Evidence *out,uint8_t *frame,size_t cap){
 /* Prepared scope mask is shared by commitment, comparison and emission. */
 if(w->ready){
  if(w->coverage_snapshot!=1)s03_issue(w,S03_UNKNOWN,D_COVERAGE);
  if(w->payload_count==0)s03_issue(w,S03_MISSING,D_MISSING_MEMBER);
  else if(w->payload_count!=1)s03_issue(w,S03_AMBIGUOUS,D_DUPLICATE);
  else if(w->bridge_read_mask&1)s03_check_member(r,&in->members[0],&r->target,w,w->anchor_read_mask&1);else s03_issue(w,S03_UNKNOWN,D_SOURCE);
 }
 return s03_finish(r,in,w,out,frame,cap);
}
