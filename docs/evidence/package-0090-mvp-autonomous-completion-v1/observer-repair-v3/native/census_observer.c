#include "observer_internal.h"
/* participant_binding/provenance/allowed_effects/output/ambiguity_semantics:
 * CENSUS_BOUNDED_COVERAGE_V1; no population/authority mutation. */
int s03_census_observer_compute(const S03ProtectedContext *r,const S03Observation *in,S03Work *w,S03Evidence *out,uint8_t *frame,size_t cap){
 /* Prepared scope mask is shared by commitment, comparison and emission. */
 if(w->ready){
  if(w->coverage_snapshot!=1)s03_issue(w,S03_UNKNOWN,D_COVERAGE);
  if(w->payload_count==0&&r->expected_count)s03_issue(w,S03_UNKNOWN,D_MISSING_MEMBER);
  for(uint32_t i=0;i<w->payload_count;i++){
   const S03Member *m=&in->members[i];
   if(!((w->bridge_read_mask>>i)&1)){s03_issue(w,S03_UNKNOWN,D_SOURCE);continue;}
   for(uint32_t j=0;j<i;j++)if((((w->bridge_read_mask>>j)&1)&&s03_target_equal(&m->bridge,&in->members[j].bridge))||(m->public_row.pid==in->members[j].public_row.pid&&m->public_row.database_oid==in->members[j].public_row.database_oid))s03_issue(w,S03_AMBIGUOUS,D_DUPLICATE);
   uint32_t found=0;for(uint32_t j=0;j<r->expected_count;j++)if(s03_target_equal(&m->bridge,&r->expected[j])){s03_check_member(r,m,&r->expected[j],w,(w->anchor_read_mask>>i)&1);found++;}
   if(!found)s03_check_member(r,m,&m->bridge,w,0);
   if(!found)s03_issue(w,m->bridge_presence==1?S03_OBSERVED_MISMATCH:S03_UNKNOWN,D_EXTRA_MEMBER);
  }
  for(uint32_t j=0;j<r->expected_count;j++){uint32_t found=0;for(uint32_t i=0;i<w->payload_count;i++)if(((w->bridge_read_mask>>i)&1)&&s03_target_equal(&in->members[i].bridge,&r->expected[j]))found++;if(!found)s03_issue(w,S03_UNKNOWN,D_MISSING_MEMBER);if(found>1)s03_issue(w,S03_AMBIGUOUS,D_DUPLICATE);}
 }
 return s03_finish(r,in,w,out,frame,cap);
}
