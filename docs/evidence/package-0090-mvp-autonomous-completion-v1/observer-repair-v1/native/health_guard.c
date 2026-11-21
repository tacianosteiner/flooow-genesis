#include "observer_internal.h"
/* purpose/observation_target/input/session_binding/output/failure_semantics:
 * JOIN_EXACT_TARGET_V1 + HEALTH_BOUND_LIVENESS_V1. No role-selected dispatch. */
int s03_health_guard_compute(const S03ProtectedContext *r,const S03Observation *in,S03Evidence *out,uint8_t *frame,size_t cap){
 S03Work w;int rc=s03_prepare(r,in,&w,S03_HEALTH_GUARD);if(rc)return rc;
 if(w.ready){
  if(in->coverage!=1)s03_issue(&w,S03_UNKNOWN,D_COVERAGE);
  if(in->count==0)s03_issue(&w,S03_MISSING,D_MISSING_MEMBER);
  else if(in->count!=1)s03_issue(&w,S03_AMBIGUOUS,D_DUPLICATE);
  else s03_check_member(r,&in->members[0],&r->target,&w);
 }
 return s03_finish(r,in,&w,out,frame,cap);
}
