#include "observer_internal.h"
/* participant_binding/provenance/allowed_effects/output/ambiguity_semantics:
 * CENSUS_BOUNDED_COVERAGE_V1; no population/authority mutation. */
int s03_census_observer_compute(const S03ProtectedContext *r,const S03Observation *in,S03Evidence *out,uint8_t *frame,size_t cap){
 S03Work w;int rc=s03_prepare(r,in,&w,S03_CENSUS_OBSERVER);if(rc)return rc;
 if(w.ready){
  if(in->coverage!=1)s03_issue(&w,S03_UNKNOWN,D_COVERAGE);
  if(in->count==0&&r->expected_count)s03_issue(&w,S03_UNKNOWN,D_MISSING_MEMBER);
  for(uint32_t i=0;i<in->count;i++){
   const S03Member *m=&in->members[i];
   for(uint32_t j=0;j<i;j++)if(s03_target_equal(&m->bridge,&in->members[j].bridge)||(m->public_row.pid==in->members[j].public_row.pid&&m->public_row.database_oid==in->members[j].public_row.database_oid))s03_issue(&w,S03_AMBIGUOUS,D_DUPLICATE);
   uint32_t found=0;for(uint32_t j=0;j<r->expected_count;j++)if(s03_target_equal(&m->bridge,&r->expected[j])){s03_check_member(r,m,&r->expected[j],&w);found++;}
   if(!found)s03_check_member(r,m,&m->bridge,&w);
   if(!found)s03_issue(&w,m->bridge_presence==1?S03_OBSERVED_MISMATCH:S03_UNKNOWN,D_EXTRA_MEMBER);
  }
  for(uint32_t j=0;j<r->expected_count;j++){uint32_t found=0;for(uint32_t i=0;i<in->count;i++)if(s03_target_equal(&in->members[i].bridge,&r->expected[j]))found++;if(!found)s03_issue(&w,S03_UNKNOWN,D_MISSING_MEMBER);if(found>1)s03_issue(&w,S03_AMBIGUOUS,D_DUPLICATE);}
 }
 return s03_finish(r,in,&w,out,frame,cap);
}
