/* Pure wire-parser adversarial tests; not runtime authority or identity proof. */
#include "protocol.h"
int main(void){
    request_fields r={.slot=1,.role=1,.db=2,.postmaster_start=3,.backend_start=4},out;
    unsigned char b[FRAME_MAX],copy[FRAME_MAX];strcpy(r.role_name,"test_verifier");strcpy(r.db_name,"native_fixture");
    size_t n=encode_request(b,&r);unsigned total=0;
    if(!decode_request(b,n,&out))return 70;total++;
    for(size_t i=0;i<n;i++){if(decode_request(b,i,&out))return 70;total++;}
    memcpy(copy,b,n);copy[n]=0;if(decode_request(copy,n+1,&out))return 70;total++;
    for(int i=0;i<12;i++){memcpy(copy,b,n);copy[i]^=0xff;if(decode_request(copy,n,&out))return 70;total++;}
    memcpy(copy,b,n);copy[28]=0;if(decode_request(copy,n,&out))return 70;total++;
    memset(copy,0,sizeof(copy));if(decode_request(copy,sizeof(copy),&out))return 70;total++;
    printf("{\"frame_parser_cases\":%u,\"result\":\"PASS\",\"scope\":\"ASCII_FIXTURE_SUBSET\"}\n",total);return 0;
}
