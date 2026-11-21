#define _GNU_SOURCE
#include "observer_internal.h"
#include <openssl/sha.h>
_Static_assert(sizeof(SHA256_CTX)==112,"Pinned provider context ABI required");
_Static_assert(ATOMIC_INT_LOCK_FREE==2,"No hidden atomic runtime provider allowed");
#include <fcntl.h>
#include <sys/stat.h>
#include <time.h>
#include <unistd.h>
#include <limits.h>
#include "native_effects.h"
/* Implements input/context/session/principal/generation/custody/authentication,
 * temporal/provenance/integrity/output/failure/consumer boundaries. No source
 * acceptance, trusted-root construction, auth handshake or authority factory.
 */
static int bytes_equal(const uint8_t *a,const uint8_t *b,size_t n){unsigned diff=0;for(size_t i=0;i<n;i++)diff|=a[i]^b[i];return diff==0;}
static int nonzero(const uint8_t *p,size_t n){unsigned v=0;for(size_t i=0;i<n;i++)v|=p[i];return v!=0;}
int s03_ref_ok(const S03Ref *r){return r&&r->kind&&r->size&&r->size<=S03_REF_BYTES&&nonzero(r->bytes,r->size);}
int s03_ref_equal(const S03Ref *a,const S03Ref *b){return s03_ref_ok(a)&&s03_ref_ok(b)&&a->kind==b->kind&&a->size==b->size&&bytes_equal(a->bytes,b->bytes,a->size);}
static int name_ok(const S03Name *n){if(!n->size||n->size>=S03_NAME_BYTES)return 0;for(uint32_t i=0;i<n->size;i++)if(!n->bytes[i]||n->bytes[i]<32||n->bytes[i]==127)return 0;return 1;}
static int name_equal(const S03Name *a,const S03Name *b){return name_ok(a)&&name_ok(b)&&a->size==b->size&&bytes_equal(a->bytes,b->bytes,a->size);}
static int source_ok(const S03Source *s){return s03_ref_ok(&s->source_id)&&s03_ref_ok(&s->source_authority)&&s03_ref_ok(&s->source_provenance)&&s03_ref_ok(&s->source_acceptance)&&nonzero(s->integrity,32);}
static int source_equal(const S03Source *a,const S03Source *b){return source_ok(a)&&source_ok(b)&&s03_ref_equal(&a->source_id,&b->source_id)&&s03_ref_equal(&a->source_authority,&b->source_authority)&&s03_ref_equal(&a->source_provenance,&b->source_provenance)&&s03_ref_equal(&a->source_acceptance,&b->source_acceptance)&&bytes_equal(a->integrity,b->integrity,32);}
static int observer_ok(const S03Observer *o,uint32_t role){return o->role==role&&s03_ref_ok(&o->principal)&&s03_ref_ok(&o->birth)&&s03_ref_ok(&o->session)&&s03_ref_ok(&o->channel)&&s03_ref_ok(&o->context);}
static int target_ok(const S03Target *t){return s03_ref_ok(&t->context)&&s03_ref_ok(&t->server_generation)&&s03_ref_ok(&t->birth)&&s03_ref_ok(&t->session)&&s03_ref_ok(&t->registry_revision)&&s03_ref_ok(&t->participant)&&s03_ref_ok(&t->principal)&&t->generation&&t->database_oid&&t->role_oid&&t->pid&&name_ok(&t->role_name)&&t->backend_start_pg_us!=INT64_MIN&&t->backend_start_pg_us!=INT64_MAX&&t->server_start_pg_us!=INT64_MIN&&t->server_start_pg_us!=INT64_MAX;}
int s03_target_equal(const S03Target *a,const S03Target *b){return target_ok(a)&&target_ok(b)&&s03_ref_equal(&a->context,&b->context)&&s03_ref_equal(&a->server_generation,&b->server_generation)&&s03_ref_equal(&a->birth,&b->birth)&&s03_ref_equal(&a->session,&b->session)&&s03_ref_equal(&a->registry_revision,&b->registry_revision)&&s03_ref_equal(&a->participant,&b->participant)&&s03_ref_equal(&a->principal,&b->principal)&&a->generation==b->generation&&a->database_oid==b->database_oid&&a->role_oid==b->role_oid&&a->pid==b->pid&&a->backend_start_pg_us==b->backend_start_pg_us&&a->server_start_pg_us==b->server_start_pg_us&&name_equal(&a->role_name,&b->role_name);}
void s03_issue(S03Work *w,enum s03_status s,enum s03_diag d){w->issues|=UINT32_C(1)<<s;w->diagnostics|=UINT64_C(1)<<d;}
static int clock_us(uint64_t *v){struct timespec t;if(s03_clock_gettime(&t)||t.tv_sec<0||t.tv_nsec<0||t.tv_nsec>=1000000000L||(uint64_t)t.tv_sec>(UINT64_MAX-UINT64_C(999999))/UINT64_C(1000000))return 0;*v=(uint64_t)t.tv_sec*UINT64_C(1000000)+(uint64_t)t.tv_nsec/1000;return 1;}
static int window_refs_ok(const S03Window *a){return s03_ref_ok(&a->boot)&&s03_ref_ok(&a->time_namespace)&&s03_ref_ok(&a->barrier)&&s03_ref_ok(&a->acquisition)&&s03_ref_ok(&a->snapshot)&&s03_ref_ok(&a->custody)&&s03_ref_ok(&a->authentication)&&s03_ref_ok(&a->policy)&&s03_ref_ok(&a->challenge);}
/* ObservationWindow requires the entire original interval within the
 * independently approved source/context lease, not just the current clock. */
static int interval_in_lease(const S03Window *w,const S03ProtectedContext *r){return w->finished_us>=w->started_us&&w->started_us>=r->not_before_us&&w->finished_us<r->expires_us&&w->barrier_valid_until_us>=w->finished_us;}
static int interval_current(const S03Window *w,const S03ProtectedContext *r,uint64_t now){return interval_in_lease(w,r)&&now>=w->finished_us&&now-w->started_us<=r->max_age_us&&now>=r->not_before_us&&now<r->expires_us&&now<=w->barrier_valid_until_us;}
static int root_ok(const S03ProtectedContext *r,uint32_t role){
 if(!r||r->version!=1||!r->max_rows||r->max_rows>S03_MAX_MEMBERS||!r->max_bytes||r->max_bytes>S03_FRAME_LIMIT||!r->max_age_us||r->expires_us<=r->not_before_us||!r->expected_count||r->expected_count>r->max_rows||!observer_ok(&r->observer,role)||!observer_ok(&r->other_observer,role==1?2:1)||!target_ok(&r->target)||!window_refs_ok(&r->window)||!s03_ref_ok(&r->origin_channel_binding)||!s03_ref_ok(&r->creator_principal)||!s03_ref_ok(&r->verifier_principal)||!s03_ref_ok(&r->population_scope))return 0;
 if(!interval_in_lease(&r->window,r))return 0;
 if(s03_ref_equal(&r->creator_principal,&r->verifier_principal)||s03_ref_equal(&r->observer.principal,&r->target.principal)||s03_ref_equal(&r->observer.principal,&r->other_observer.principal)||s03_ref_equal(&r->observer.birth,&r->target.birth)||s03_ref_equal(&r->observer.birth,&r->other_observer.birth)||s03_ref_equal(&r->observer.session,&r->target.session)||s03_ref_equal(&r->observer.session,&r->other_observer.session)||s03_ref_equal(&r->observer.channel,&r->other_observer.channel))return 0;
 for(unsigned i=0;i<S03_SOURCE_COUNT;i++)if(!source_ok(&r->source[i]))return 0;
 for(uint32_t i=0;i<r->expected_count;i++){if(!target_ok(&r->expected[i]))return 0;for(uint32_t j=0;j<i;j++)if(s03_target_equal(&r->expected[i],&r->expected[j]))return 0;}
 uint32_t target_found=0;for(uint32_t i=0;i<r->expected_count;i++)if(s03_target_equal(&r->target,&r->expected[i]))target_found++;if(target_found!=1)return 0;
 return 1;
}
int s03_prepare(const S03ProtectedContext *r,const S03Observation *in,S03Work *w,uint32_t role){
 if(!w||!in||!root_ok(r,role))return -1;
 w->issues=0;w->diagnostics=0;w->ready=0;w->metadata_ready=0;w->origin_ready=0;w->public_ready=0;w->source_ready_mask=0;w->source_present_mask=0;w->bridge_read_mask=0;w->anchor_read_mask=0;w->payload_count=0;w->coverage_snapshot=0;w->role=role;w->finished=0;
 if(!clock_us(&w->started))return -2;
 if(!interval_current(&r->window,r,w->started))return -4;
 /* The protected source/context caller, not these comparisons, supplies
  * independently qualified origin. An untrusted root/data pair is never an
  * authenticated ingress. No public factory or bridge is created here. */
 if(!observer_ok(&in->observer,role))s03_issue(w,S03_BINDING_MISMATCH,D_ROLE);
 if(!s03_ref_equal(&in->observer.principal,&r->observer.principal))s03_issue(w,S03_BINDING_MISMATCH,D_PRINCIPAL);
 if(!s03_ref_equal(&in->observer.birth,&r->observer.birth))s03_issue(w,S03_BINDING_MISMATCH,D_BIRTH);
 if(!s03_ref_equal(&in->observer.context,&r->observer.context))s03_issue(w,S03_BINDING_MISMATCH,D_CONTEXT);
 if(!s03_ref_equal(&in->observer.session,&r->observer.session)||!s03_ref_equal(&in->observer.channel,&r->observer.channel))s03_issue(w,S03_BINDING_MISMATCH,D_SESSION);
 if(in->consumer_kind!=1)s03_issue(w,S03_BINDING_MISMATCH,D_CONSUMER);
 if(in->requested_output_kind!=1)s03_issue(w,S03_BINDING_MISMATCH,D_PROMOTION);
 if(w->issues)return 0; /* No out-of-scope source facts read after wrong origin. */
 w->origin_ready=1;
 uint32_t qualified_metadata=1;
 for(unsigned i=0;i<S03_SOURCE_COUNT;i++){
  /* PUBLIC payload absence does not suppress independently available
   * expected/bridge/native/auth/custody/generation/barrier metadata checks.
   * No PUBLIC/member payload is read by those checks. */
  w->source_state[i]=in->source_state[i];if(w->source_state[i]==S03_SOURCE_PRESENT)w->source_present_mask|=UINT32_C(1)<<i;
  if(w->source_state[i]==S03_SOURCE_PRESENT&&source_equal(&in->source[i],&r->source[i]))w->source_ready_mask|=UINT32_C(1)<<i;
  if(i!=S03_SRC_PUBLIC&&(w->source_state[i]!=S03_SOURCE_PRESENT||!source_equal(&in->source[i],&r->source[i])))qualified_metadata=0;
  switch(w->source_state[i]){case S03_SOURCE_PRESENT:if(!source_equal(&in->source[i],&r->source[i]))s03_issue(w,S03_INTEGRITY_FAILURE,D_INTEGRITY);break;case S03_SOURCE_MISSING:s03_issue(w,S03_MISSING,D_SOURCE);break;case S03_SOURCE_UNAVAILABLE:s03_issue(w,S03_UNAVAILABLE,D_SOURCE);break;case S03_SOURCE_UNKNOWN:s03_issue(w,S03_UNKNOWN,D_SOURCE);break;case S03_SOURCE_CONTRADICTED:s03_issue(w,S03_CONTRADICTED,D_SOURCE);break;case S03_SOURCE_INTEGRITY_FAILURE:s03_issue(w,S03_INTEGRITY_FAILURE,D_INTEGRITY);break;default:s03_issue(w,S03_MISSING,D_SOURCE);}
 }
 w->public_ready=(w->source_ready_mask&(UINT32_C(1)<<S03_SRC_PUBLIC))!=0;
 if(!qualified_metadata)return 0;
 w->metadata_ready=1;
 if(!s03_target_equal(&in->target,&r->target))s03_issue(w,S03_BINDING_MISMATCH,D_SESSION);
 if(!s03_ref_equal(&in->target.context,&r->target.context))s03_issue(w,S03_BINDING_MISMATCH,D_CONTEXT);
 if(!s03_ref_equal(&in->target.participant,&r->target.participant))s03_issue(w,S03_BINDING_MISMATCH,D_PARTICIPANT);
 if(!s03_ref_equal(&in->target.principal,&r->target.principal))s03_issue(w,S03_BINDING_MISMATCH,D_PRINCIPAL);
 if(in->target.generation!=r->target.generation||!s03_ref_equal(&in->target.server_generation,&r->target.server_generation))s03_issue(w,S03_BINDING_MISMATCH,D_GENERATION);
 if(!window_refs_ok(&in->window))s03_issue(w,S03_MISSING,D_TIME);
 if(!s03_ref_equal(&in->window.boot,&r->window.boot)||!s03_ref_equal(&in->window.time_namespace,&r->window.time_namespace)||!s03_ref_equal(&in->window.barrier,&r->window.barrier)||!s03_ref_equal(&in->window.acquisition,&r->window.acquisition)||!s03_ref_equal(&in->window.snapshot,&r->window.snapshot)||!s03_ref_equal(&in->window.policy,&r->window.policy)||!s03_ref_equal(&in->window.challenge,&r->window.challenge))s03_issue(w,S03_BINDING_MISMATCH,D_CONTEXT);
 if(!s03_ref_equal(&in->window.custody,&r->window.custody))s03_issue(w,S03_BINDING_MISMATCH,D_CUSTODY);
 if(!s03_ref_equal(&in->window.authentication,&r->window.authentication))s03_issue(w,S03_BINDING_MISMATCH,D_AUTH);
 if(!interval_current(&in->window,r,w->started)||!interval_current(&r->window,r,w->started))s03_issue(w,S03_STALE,D_TIME);
 if(w->public_ready){w->payload_count=in->count;w->coverage_snapshot=in->coverage;if(w->payload_count>r->max_rows||w->payload_count>S03_MAX_MEMBERS)s03_issue(w,S03_UNKNOWN,D_BOUND);}
 if(!s03_ref_equal(&in->population_scope,&r->population_scope))s03_issue(w,S03_BINDING_MISMATCH,D_POPULATION);
 if(!w->issues)w->ready=1;
 if(w->ready)for(uint32_t i=0;i<w->payload_count;i++)if(in->members[i].bridge_presence==1){w->bridge_read_mask|=UINT64_C(1)<<i;for(uint32_t j=0;j<r->expected_count;j++)if(s03_target_equal(&in->members[i].bridge,&r->expected[j]))w->anchor_read_mask|=UINT64_C(1)<<i;}
 return 0;
}
void s03_check_member(const S03ProtectedContext *r,const S03Member *m,const S03Target *expected,S03Work *w,uint32_t anchor_allowed){
 if(m->bridge_presence!=1){s03_issue(w,S03_UNKNOWN,D_SOURCE);return;}
 if(!target_ok(&m->bridge)){s03_issue(w,S03_MISSING,D_SOURCE);return;}
 if(!s03_target_equal(&m->bridge,expected)){s03_issue(w,S03_BINDING_MISMATCH,D_SESSION);return;}
 (void)r;
 if(!anchor_allowed){s03_issue(w,S03_UNKNOWN,D_BIRTH);return;}
 if(!s03_ref_ok(&m->native_birth)||!s03_ref_ok(&m->public_row.source_row)){s03_issue(w,S03_MISSING,D_SOURCE);return;}
 static const uint8_t client_backend[]={99,108,105,101,110,116,32,98,97,99,107,101,110,100};
 if(m->backend_type.size!=sizeof(client_backend)||!bytes_equal(m->backend_type.bytes,client_backend,sizeof(client_backend)))s03_issue(w,S03_UNKNOWN,D_SOURCE);
 if(!s03_ref_equal(&m->native_birth,&m->bridge.birth))s03_issue(w,S03_CONTRADICTED,D_BIRTH);
 if(m->public_row.database_oid!=m->bridge.database_oid||m->public_row.role_oid!=m->bridge.role_oid||m->public_row.pid!=m->bridge.pid||!name_equal(&m->public_row.role_name,&m->bridge.role_name))s03_issue(w,S03_CONTRADICTED,D_PRINCIPAL);
 if(m->liveness_before!=1||m->liveness_after!=1)s03_issue(w,S03_UNKNOWN,D_BIRTH);
}
/* Private deterministic candidate frame; fixed local field order and BE
 * scalars reuse existing S03/protocol encoding. Not a native message/tag or
 * change to canonical8/19/146. No raw C padding/pointers/credential bytes. */
typedef struct {uint8_t *p;size_t used,cap;int bad;} Frame;
static void raw(Frame *b,const uint8_t *p,size_t n){if(b->bad||n>b->cap-b->used){b->bad=1;return;}for(size_t i=0;i<n;i++)b->p[b->used++]=p[i];}
static void u32(Frame *b,uint32_t n){uint8_t p[4];for(unsigned i=0;i<4;i++)p[i]=(uint8_t)(n>>(24-i*8));raw(b,p,4);}
static void u64(Frame *b,uint64_t n){uint8_t p[8];for(unsigned i=0;i<8;i++)p[i]=(uint8_t)(n>>(56-i*8));raw(b,p,8);}
static void refout(Frame *b,const S03Ref *r){if(!s03_ref_ok(r)){b->bad=1;return;}u32(b,r->kind);u32(b,r->size);raw(b,r->bytes,r->size);}
static void nameout(Frame *b,const S03Name *n){if(!name_ok(n)){b->bad=1;return;}u32(b,n->size);raw(b,n->bytes,n->size);}
static void targetout(Frame *b,const S03Target *t){refout(b,&t->context);refout(b,&t->server_generation);refout(b,&t->birth);refout(b,&t->session);refout(b,&t->registry_revision);refout(b,&t->participant);refout(b,&t->principal);u64(b,t->generation);u64(b,(uint64_t)t->server_start_pg_us);u64(b,(uint64_t)t->backend_start_pg_us);u32(b,t->database_oid);u32(b,t->role_oid);u32(b,t->pid);nameout(b,&t->role_name);}
static void sourceout(Frame *b,const S03Source *s){refout(b,&s->source_id);refout(b,&s->source_authority);refout(b,&s->source_provenance);refout(b,&s->source_acceptance);raw(b,s->integrity,32);}
/* Full typed key ordering, preserving duplicates and original source ordinal.
 * Invalid/missing keys remain distinct unavailable records, never PID identity. */
static size_t memberkey(const S03Member *m,uint8_t *buf,uint32_t bridge_allowed){Frame k={buf,0,2048,0};uint32_t valid=bridge_allowed&&target_ok(&m->bridge);u32(&k,valid);if(valid)targetout(&k,&m->bridge);u32(&k,m->public_row.database_oid);u32(&k,m->public_row.role_oid);u32(&k,m->public_row.pid);if(name_ok(&m->public_row.role_name))nameout(&k,&m->public_row.role_name);if(s03_ref_ok(&m->public_row.source_row))refout(&k,&m->public_row.source_row);return k.bad?0:k.used;}
static int memberless(const S03Member *a,const S03Member *b,uint32_t allow_a,uint32_t allow_b){uint8_t x[2048],y[2048];size_t nx=memberkey(a,x,allow_a),ny=memberkey(b,y,allow_b),n=nx<ny?nx:ny;for(size_t i=0;i<n;i++){if(x[i]<y[i])return 1;if(x[i]>y[i])return 0;}return nx<ny;}
static uint32_t status(const S03Work *w){static const uint32_t priority[]={S03_INTEGRITY_FAILURE,S03_CONTRADICTED,S03_BINDING_MISMATCH,S03_AMBIGUOUS,S03_STALE,S03_UNAVAILABLE,S03_MISSING,S03_UNKNOWN,S03_OBSERVED_MISMATCH};for(size_t i=0;i<sizeof(priority)/sizeof(priority[0]);i++)if(w->issues&(UINT32_C(1)<<priority[i]))return priority[i];return S03_OBSERVED_MATCH;}
int s03_finish(const S03ProtectedContext *r,const S03Observation *in,S03Work *w,S03Evidence *out,uint8_t *frame,size_t cap){
 if(!out||!frame||cap<64||cap>S03_FRAME_LIMIT||cap>r->max_bytes)return -3;
 if(!clock_us(&w->finished))return -2;
 if(w->finished<w->started||!interval_current(&r->window,r,w->finished)||(w->metadata_ready&&!interval_current(&in->window,r,w->finished)))s03_issue(w,S03_STALE,D_TIME);
 out->role=w->role;out->status=status(w);out->evidence_only=1;out->diagnostics=w->diagnostics;out->observed_started_us=w->started;out->observed_finished_us=w->finished;out->frame_size=0;out->delivery_state=0;
 Frame b={frame,0,cap-32,0};raw(&b,(const uint8_t*)"S03OBSE2",8);u32(&b,2);u32(&b,w->role);u32(&b,1);u32(&b,out->status);u64(&b,w->diagnostics);
 /* Fixed binding vector: 1 MATCH,2 MISMATCH,3 NOT_ESTABLISHED. Missing
  * qualified inputs never yield MATCH. Exact global positive gates precede it. */
 const unsigned dimensions[]={D_CONTEXT,D_SESSION,D_PARTICIPANT,D_PRINCIPAL,D_GENERATION,D_CUSTODY,D_AUTH,D_SOURCE,D_TIME};
 for(unsigned i=0;i<9;i++)u32(&b,!w->ready?3:((w->diagnostics&(UINT64_C(1)<<dimensions[i]))?2:1));
 raw(&b,(const uint8_t*)"S03:DESIGN/AUTHENTICATED_SELF_IDENTITY",sizeof("S03:DESIGN/AUTHENTICATED_SELF_IDENTITY")-1);
 /* Expected identities are explicitly expected, never fabricated actuals. */
 targetout(&b,&r->target);refout(&b,&r->observer.principal);refout(&b,&r->observer.birth);refout(&b,&r->observer.context);refout(&b,&r->observer.session);refout(&b,&r->observer.channel);refout(&b,&r->origin_channel_binding);refout(&b,&r->window.policy);refout(&b,&r->window.challenge);refout(&b,&r->window.boot);refout(&b,&r->window.time_namespace);refout(&b,&r->window.barrier);refout(&b,&r->window.acquisition);refout(&b,&r->window.snapshot);refout(&b,&r->window.custody);refout(&b,&r->window.authentication);u64(&b,w->started);u64(&b,w->finished);u64(&b,r->window.started_us);u64(&b,r->window.finished_us);u64(&b,r->not_before_us);u64(&b,r->expires_us);u64(&b,r->max_age_us);u64(&b,r->window.barrier_valid_until_us);u32(&b,w->metadata_ready);if(w->metadata_ready){u64(&b,in->window.started_us);u64(&b,in->window.finished_us);u64(&b,in->window.barrier_valid_until_us);}
 for(unsigned i=0;i<S03_SOURCE_COUNT;i++){sourceout(&b,&r->source[i]);u32(&b,w->origin_ready);if(w->origin_ready){u32(&b,w->source_state[i]);uint32_t present=(w->source_present_mask&(UINT32_C(1)<<i))&&source_ok(&in->source[i]);u32(&b,present);if(present)sourceout(&b,&in->source[i]);}}
 /* PRESENT actual payload only after complete source/binding gates; an absent
  * payload is tagged NOT_ESTABLISHED, never an empty observed population. */
 u32(&b,w->ready?1:0);
 if(w->ready){targetout(&b,&in->target);refout(&b,&in->population_scope);u32(&b,w->coverage_snapshot);u32(&b,w->payload_count);
 uint32_t order[S03_MAX_MEMBERS];for(uint32_t i=0;i<w->payload_count;i++){order[i]=i;uint32_t j=i;while(j&&memberless(&in->members[order[j]],&in->members[order[j-1]],(w->bridge_read_mask>>order[j])&1,(w->bridge_read_mask>>order[j-1])&1)){uint32_t t=order[j];order[j]=order[j-1];order[j-1]=t;j--;}}
 for(uint32_t i=0;i<w->payload_count;i++){const S03Member *m=&in->members[order[i]];u32(&b,order[i]);
 uint32_t present=((w->bridge_read_mask>>order[i])&1)&&target_ok(&m->bridge);u32(&b,present);if(present)targetout(&b,&m->bridge);
 u32(&b,m->public_row.database_oid);u32(&b,m->public_row.role_oid);u32(&b,m->public_row.pid);
 u32(&b,name_ok(&m->public_row.role_name));if(name_ok(&m->public_row.role_name))nameout(&b,&m->public_row.role_name);
 u32(&b,s03_ref_ok(&m->public_row.source_row));if(s03_ref_ok(&m->public_row.source_row))refout(&b,&m->public_row.source_row);
 uint32_t anchor=(w->anchor_read_mask&(UINT64_C(1)<<order[i]))!=0;u32(&b,anchor);if(anchor){u32(&b,s03_ref_ok(&m->native_birth));if(s03_ref_ok(&m->native_birth))refout(&b,&m->native_birth);u32(&b,m->liveness_before);u32(&b,m->liveness_after);}
 u32(&b,present);if(present){u32(&b,name_ok(&m->backend_type));if(name_ok(&m->backend_type))nameout(&b,&m->backend_type);}}}

 if(b.bad||b.used>UINT32_MAX-32)return -3;
 SHA256_CTX hash;if(SHA256_Init(&hash)!=1||SHA256_Update(&hash,frame,b.used)!=1||SHA256_Final(out->content_digest,&hash)!=1)return -3;
 for(unsigned i=0;i<32;i++)frame[b.used+i]=out->content_digest[i];
 size_t total=b.used+32;out->frame_size=(uint32_t)total;
 /* Existing qualified private evidence channel only. Flags/stat equality do
  * NOT establish origin/custody; protected-context qualification must precede
  * use and prove descriptor continuity. No write when its identity differs. */
 struct stat st;long flags=s03_getfl(r->evidence_fd);if(flags<0||!(flags&O_NONBLOCK)||s03_fstat(r->evidence_fd,&st)||(!S_ISFIFO(st.st_mode)&&!S_ISSOCK(st.st_mode))||(uint64_t)st.st_dev!=r->evidence_device||(uint64_t)st.st_ino!=r->evidence_inode){out->delivery_state=2;return -2;}
 long sent=s03_write(r->evidence_fd,frame,total);if(sent<0||(size_t)sent!=total){out->delivery_state=2;return -2;}out->delivery_state=1;return 0;
}

/* Prospective private invocation edge: existing S03 one-use/result pattern.
 * Canonical commitment contains semantic fields, no padding or pointers.
 * This does not authenticate the owner or make a protected context exist. */
static void rawref(Frame *b,const S03Ref *r){u32(b,r->kind);u32(b,r->size);raw(b,r->bytes,r->size>S03_REF_BYTES?S03_REF_BYTES:r->size);}
static void rawname(Frame *b,const S03Name *r){u32(b,r->size);raw(b,r->bytes,r->size>S03_NAME_BYTES?S03_NAME_BYTES:r->size);}
static void rawsource(Frame *b,const S03Source *s){rawref(b,&s->source_id);rawref(b,&s->source_authority);rawref(b,&s->source_provenance);rawref(b,&s->source_acceptance);raw(b,s->integrity,32);}
static void rawobserver(Frame *b,const S03Observer *o){u32(b,o->role);rawref(b,&o->principal);rawref(b,&o->birth);rawref(b,&o->session);rawref(b,&o->channel);rawref(b,&o->context);}
static void rawtarget(Frame *b,const S03Target *t){rawref(b,&t->context);rawref(b,&t->server_generation);rawref(b,&t->birth);rawref(b,&t->session);rawref(b,&t->registry_revision);rawref(b,&t->participant);rawref(b,&t->principal);u64(b,t->generation);u64(b,(uint64_t)t->server_start_pg_us);u64(b,(uint64_t)t->backend_start_pg_us);u32(b,t->database_oid);u32(b,t->role_oid);u32(b,t->pid);rawname(b,&t->role_name);}
static void rawwindow(Frame *b,const S03Window *w){rawref(b,&w->boot);rawref(b,&w->time_namespace);rawref(b,&w->barrier);rawref(b,&w->acquisition);rawref(b,&w->snapshot);rawref(b,&w->custody);rawref(b,&w->authentication);rawref(b,&w->policy);rawref(b,&w->challenge);u64(b,w->started_us);u64(b,w->finished_us);u64(b,w->barrier_valid_until_us);}
static int invocation_digest(const S03ProtectedContext *r,const S03Observation *in,const S03Work *w,uint32_t role,uint8_t *frame,size_t cap,uint8_t digest[32]){
 Frame b={frame,0,cap,0};raw(&b,(const uint8_t*)"S03-ONE-CHALLENGE-V2",20);u32(&b,role);u32(&b,r->version);u32(&b,r->max_rows);u32(&b,r->max_bytes);u64(&b,r->not_before_us);u64(&b,r->expires_us);u64(&b,r->max_age_us);rawobserver(&b,&r->observer);rawobserver(&b,&r->other_observer);rawtarget(&b,&r->target);rawref(&b,&r->origin_channel_binding);rawref(&b,&r->creator_principal);rawref(&b,&r->verifier_principal);rawref(&b,&r->population_scope);rawwindow(&b,&r->window);u32(&b,r->expected_count);for(uint32_t i=0;i<r->expected_count;i++)rawtarget(&b,&r->expected[i]);u32(&b,(uint32_t)r->evidence_fd);u64(&b,r->evidence_device);u64(&b,r->evidence_inode);
 rawobserver(&b,&in->observer);u32(&b,in->consumer_kind);u32(&b,in->requested_output_kind);u32(&b,w->origin_ready);
 for(unsigned i=0;i<S03_SOURCE_COUNT;i++){rawsource(&b,&r->source[i]);if(w->origin_ready){u32(&b,w->source_state[i]);uint32_t present=(w->source_present_mask>>i)&1;u32(&b,present);if(present)rawsource(&b,&in->source[i]);}}
 u32(&b,w->metadata_ready);if(w->metadata_ready){rawtarget(&b,&in->target);rawwindow(&b,&in->window);rawref(&b,&in->population_scope);u32(&b,w->public_ready);if(w->public_ready){u32(&b,w->coverage_snapshot);u32(&b,w->payload_count);}}
 u32(&b,w->ready);if(w->ready)for(uint32_t i=0;i<w->payload_count;i++){const S03Member *m=&in->members[i];uint32_t bridge=(w->bridge_read_mask>>i)&1;u32(&b,bridge);if(bridge){rawtarget(&b,&m->bridge);rawname(&b,&m->backend_type);}u32(&b,m->public_row.database_oid);u32(&b,m->public_row.role_oid);u32(&b,m->public_row.pid);rawname(&b,&m->public_row.role_name);rawref(&b,&m->public_row.source_row);uint32_t anchor=(w->anchor_read_mask&(UINT64_C(1)<<i))!=0;u32(&b,anchor);if(anchor){rawref(&b,&m->native_birth);u32(&b,m->liveness_before);u32(&b,m->liveness_after);}}
 SHA256_CTX hash;return !b.bad&&SHA256_Init(&hash)==1&&SHA256_Update(&hash,frame,b.used)==1&&SHA256_Final(digest,&hash)==1;
}
static int invoke_once(const S03ProtectedContext *r,const S03Observation *in,S03Evidence *out,uint8_t *frame,size_t cap,uint32_t role){
 if(!out)return -1;
 S03Evidence denied={0};denied.status=S03_UNKNOWN;denied.evidence_only=1;*out=denied;
 if(!in||!frame||!root_ok(r,role)||!r->terminal||cap<64||cap>r->max_bytes||cap>S03_FRAME_LIMIT)return -1;
 S03Work w;int prepared=s03_prepare(r,in,&w,role);if(prepared)return prepared;
 if(atomic_load_explicit(&r->terminal->state,memory_order_acquire)!=0&&w.metadata_ready&&!interval_current(&in->window,r,w.started))return -4;
 uint8_t digest[32];if(!invocation_digest(r,in,&w,role,frame,cap,digest))return -3;
 S03Terminal *t=r->terminal;unsigned expected=0;
 if(!atomic_compare_exchange_strong_explicit(&t->state,&expected,1,memory_order_acq_rel,memory_order_acquire)){
  if(expected!=2)return -5; /* in progress/invalid owner state; never retry internally */
  if(!bytes_equal(digest,t->input_digest,32))return -6; /* immutable identity conflict */
  uint64_t now;if(!clock_us(&now))return -2;
  if(!interval_current(&r->window,r,now)||(w.metadata_ready&&!interval_current(&in->window,r,now)))return -4;
  if(t->result.frame_size>cap||t->result.frame_size>S03_FRAME_LIMIT)return -3;
  *out=t->result;for(uint32_t i=0;i<out->frame_size;i++)frame[i]=t->frame[i];return t->result_code; /* no re-observe/re-emit/renew */
 }
 for(unsigned i=0;i<32;i++)t->input_digest[i]=digest[i];
 *out=denied;
 int rc=role==S03_HEALTH_GUARD?s03_health_guard_compute(r,in,&w,out,frame,cap):s03_census_observer_compute(r,in,&w,out,frame,cap);
 t->result=*out;t->result_code=rc;
 if(out->frame_size<=cap&&out->frame_size<=S03_FRAME_LIMIT){for(uint32_t i=0;i<out->frame_size;i++)t->frame[i]=frame[i];}else{t->result.frame_size=0;t->result_code=-3;}
 atomic_store_explicit(&t->state,2,memory_order_release);return t->result_code;
}
int s03_health_guard_observe(const S03ProtectedContext *r,const S03Observation *in,S03Evidence *out,uint8_t *frame,size_t cap){return invoke_once(r,in,out,frame,cap,S03_HEALTH_GUARD);}
int s03_census_observer_observe(const S03ProtectedContext *r,const S03Observation *in,S03Evidence *out,uint8_t *frame,size_t cap){return invoke_once(r,in,out,frame,cap,S03_CENSUS_OBSERVER);}
