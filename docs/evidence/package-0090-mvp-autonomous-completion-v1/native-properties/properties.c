#define main original_fixture_main
#include "observer_fixture_tests.c"
#undef main
/* Deterministic source-mechanics mutation properties; never source acceptance. */
int main(void){unsigned tests=0,failed=0;for(unsigned role=1;role<=2;role++)for(unsigned field=0;field<36;field++)for(unsigned bit=0;bit<8;bit++){
 int pipes[2];if(!setup(role,pipes))return 2;unsigned mask=1u<<bit;unsigned slot=bit%S03_SOURCE_COUNT;
 switch(field){
 case 0:in.observer.principal.bytes[0]^=mask;break;case 1:in.observer.birth.bytes[0]^=mask;break;case 2:in.observer.context.bytes[0]^=mask;break;case 3:in.observer.session.bytes[0]^=mask;break;case 4:in.observer.channel.bytes[0]^=mask;break;
 case 5:in.target.context.bytes[0]^=mask;break;case 6:in.target.server_generation.bytes[0]^=mask;break;case 7:in.target.birth.bytes[0]^=mask;break;case 8:in.target.session.bytes[0]^=mask;break;case 9:in.target.registry_revision.bytes[0]^=mask;break;case 10:in.target.participant.bytes[0]^=mask;break;case 11:in.target.principal.bytes[0]^=mask;break;
 case 12:in.target.generation^=mask;break;case 13:in.target.database_oid^=mask;break;case 14:in.target.role_oid^=mask;break;case 15:in.target.pid^=mask;break;case 16:in.target.backend_start_pg_us^=mask;break;case 17:in.target.server_start_pg_us^=mask;break;case 18:in.target.role_name.bytes[0]^=mask;break;
 case 19:in.source[slot].source_id.bytes[0]^=mask;break;case 20:in.source[slot].source_authority.bytes[0]^=mask;break;case 21:in.source[slot].source_provenance.bytes[0]^=mask;break;case 22:in.source[slot].source_acceptance.bytes[0]^=mask;break;case 23:in.source[slot].integrity[0]^=mask;break;
 case 24:in.window.custody.bytes[0]^=mask;break;case 25:in.window.authentication.bytes[0]^=mask;break;case 26:in.window.policy.bytes[0]^=mask;break;case 27:in.window.challenge.bytes[0]^=mask;break;case 28:in.window.acquisition.bytes[0]^=mask;break;case 29:in.window.snapshot.bytes[0]^=mask;break;case 30:in.window.boot.bytes[0]^=mask;break;case 31:in.window.time_namespace.bytes[0]^=mask;break;case 32:in.window.barrier.bytes[0]^=mask;break;case 33:in.population_scope.bytes[0]^=mask;break;case 34:in.consumer_kind^=mask;break;case 35:in.requested_output_kind^=mask;break;
 }
 S03Evidence out={0};int rc=call(role,&out);tests++;if(rc==0&&out.status==S03_OBSERVED_MATCH){failed++;printf("UNSAFE_MATCH role=%u field=%u bit=%u\n",role,field,bit);}close(pipes[0]);close(pipes[1]);}
 printf("{\"property_cases\":%u,\"passing\":%u,\"failing\":%u,\"accepted_sources\":0}\n",tests,tests-failed,failed);return failed?1:0;}
