/* TEST ONLY: PostgreSQL transport mocked; actual native source included.
 * This proves native crypto parity/safety, never PostgreSQL runtime parity. */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <stdbool.h>
#include <setjmp.h>
#include <openssl/evp.h>
#include <openssl/err.h>
#include <openssl/x509.h>
static int injected_failure;
static EVP_MD_CTX *test_md_new(void) {
    return injected_failure==1 ? NULL : EVP_MD_CTX_new();
}
static int test_init(EVP_MD_CTX *ctx, EVP_PKEY_CTX **pctx, const EVP_MD *type, ENGINE *engine, EVP_PKEY *key) {
    return injected_failure==2 ? 0 : EVP_DigestVerifyInit(ctx,pctx,type,engine,key);
}
static int test_verify(EVP_MD_CTX *ctx,const unsigned char *sig,size_t siglen,const unsigned char *msg,size_t msglen) {
    if(injected_failure==3)return -1;
    if(injected_failure==4)return 2;
    if(injected_failure==8) { ERR_raise(ERR_LIB_EVP,ERR_R_MALLOC_FAILURE);ERR_raise(ERR_LIB_EVP,ERR_R_PASSED_INVALID_ARGUMENT);return 0; }
    if(injected_failure==10) { ERR_raise(ERR_LIB_EVP,ERR_R_INTERNAL_ERROR);return 0; }
    return EVP_DigestVerify(ctx,sig,siglen,msg,msglen);
}
static EVP_PKEY *test_parse(EVP_PKEY **key,const unsigned char **bytes,long length) {
    if(injected_failure==5) { ERR_raise(ERR_LIB_EVP,ERR_R_MALLOC_FAILURE);ERR_raise(ERR_LIB_EVP,ERR_R_PASSED_INVALID_ARGUMENT);return NULL; }
    return d2i_PUBKEY(key,bytes,length);
}
static int test_encode(const EVP_PKEY *key,unsigned char **bytes) {
    if((injected_failure==6 && !bytes)||(injected_failure==7 && bytes))return -1;
    if(injected_failure==9 && bytes)return 43;
    return i2d_PUBKEY(key,bytes);
}
static jmp_buf failure;
static int error_code;
typedef struct { int length; unsigned char bytes[]; } bytea;
typedef uintptr_t Datum;
static bytea *arguments[3];
#define PG_MODULE_MAGIC
#define PG_FUNCTION_INFO_V1(name)
#define PG_FUNCTION_ARGS void
#define VARHDRSZ 4
#define PG_GETARG_DATUM(n) ((Datum)arguments[n])
#define PG_GETARG_BYTEA_PP(n) arguments[n]
#define VARSIZE_ANY_EXHDR(p) ((p)->length)
#define VARDATA_ANY(p) ((p)->bytes)
#define toast_raw_datum_size(p) (((bytea *)(p))->length+4)
#define PG_FREE_IF_COPY(p,n) ((void)0)
#define PG_RETURN_BOOL(v) return (Datum)(v)
#define ERROR 1
#define ERRCODE_INVALID_PARAMETER_VALUE 1
#define ERRCODE_INTERNAL_ERROR 2
#define errcode(code) (error_code=(code))
#define errmsg(...) 0
#define ereport(level,detail) do { (void)(detail);longjmp(failure,1); } while(0)
#define EVP_MD_CTX_new test_md_new
#define EVP_DigestVerifyInit test_init
#define EVP_DigestVerify test_verify
#define d2i_PUBKEY test_parse
#define i2d_PUBKEY test_encode
#include "flooow_offline_mac32.c"
static bytea *decode(char *hex) {
    size_t length=strlen(hex)/2;
    bytea *result=malloc(sizeof(bytea)+length);
    if(!result)exit(2);
    result->length=(int)length;
    for(size_t i=0;i<length;i++) { unsigned value;if(sscanf(hex+2*i,"%2x",&value)!=1)exit(2);result->bytes[i]=(unsigned char)value; }
    return result;
}
int main(void) {
    char line[32768];
    while(fgets(line,sizeof(line),stdin)) {
        char *parts[5],*cursor=line;
        for(int i=0;i<4;i++) { parts[i]=cursor;cursor=strchr(cursor,'|');if(!cursor)return 2;*cursor++=0; }
        parts[4]=cursor;
        for(int i=0;i<3;i++)arguments[i]=decode(parts[i+1]);
        const char *result;
        if(setjmp(failure))result=error_code==1?"structural_error":"operational_error";
        else result=canonical_spki_ed25519_verify()?"true":"false";
        printf("%s|%s\n",parts[0],result);
        if(strcmp(parts[0],"valid")==0) {
            for(int mode=1;mode<=10;mode++) {
                injected_failure=mode;error_code=0;
                if(setjmp(failure)==0) { (void)canonical_spki_ed25519_verify();return 4; }
                if(error_code!=ERRCODE_INTERNAL_ERROR)return 5;
                fprintf(stderr,"OPERATIONAL_INJECTION_%d=XX000\n",mode);
            }
            injected_failure=0;
        }
        for(int i=0;i<3;i++)free(arguments[i]);
    }
    arguments[0]=decode("0000000000000000000000000000000000000000000000000000000000000000");
    arguments[1]=decode("0000000000000000000000000000000000000000000000000000000000000000");
    if(!timing_safe_equal32())return 3;
    arguments[1]->bytes[0]=1;if(timing_safe_equal32())return 3;
    free(arguments[0]);free(arguments[1]);
    return 0;
}
