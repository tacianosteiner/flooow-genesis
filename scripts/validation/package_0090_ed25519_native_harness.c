/* TEST ONLY: PostgreSQL transport mocked; actual native source included.
 * This proves native crypto parity/safety, never PostgreSQL runtime parity. */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <setjmp.h>
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
        for(int i=0;i<3;i++)free(arguments[i]);
    }
    arguments[0]=decode("0000000000000000000000000000000000000000000000000000000000000000");
    arguments[1]=decode("0000000000000000000000000000000000000000000000000000000000000000");
    if(!timing_safe_equal32())return 3;
    arguments[1]->bytes[0]=1;if(timing_safe_equal32())return 3;
    free(arguments[0]);free(arguments[1]);
    return 0;
}
