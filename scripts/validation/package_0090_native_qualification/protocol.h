/* TEST ONLY. Approved wire structure, synthetic context; no production authority. */
#ifndef FLOOOW_TEST_PROTOCOL_H
#define FLOOOW_TEST_PROTOCOL_H
#ifndef _GNU_SOURCE
#define _GNU_SOURCE
#endif
#include <errno.h>
#include <fcntl.h>
#include <poll.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <sys/stat.h>
#include <sys/syscall.h>
#include <linux/memfd.h>
#include <sys/un.h>
#include <time.h>
#include <unistd.h>
#include <openssl/sha.h>
#ifndef SO_PASSPIDFD
#define SO_PASSPIDFD 76
#endif
#ifndef SO_PEERPIDFD
#define SO_PEERPIDFD 77
#endif
#ifndef SCM_PIDFD
#define SCM_PIDFD 4
#endif
#define TEST_SOCKET "/run/flooow-watchdog/enrollment-v1.sock"
#define TEST_DIR "/run/flooow-watchdog"
#define FRAME_MAX 1024
typedef struct {
    uint32_t magic, db_oid, role_oid[4];
    char db_name[64], role_name[4][64];
    unsigned char binding[16], deployment[16], incarnation[16], epoch[32], fingerprint[32], policy[32];
    uint64_t experimental_abort_us; /* harness only, not an approved ACK limit */
} test_context;
typedef struct {
    unsigned char binding[16],deployment[16],incarnation[16],epoch[32],fingerprint[32],policy[32];
    uint8_t slot; uint32_t role,db;
    char role_name[64],db_name[64];
    int64_t postmaster_start,backend_start;
} request_fields;
static inline uint64_t tick_us(void) {
    struct timespec t; if(clock_gettime(CLOCK_BOOTTIME,&t))abort();
    return (uint64_t)t.tv_sec*1000000+(uint64_t)t.tv_nsec/1000;
}
static inline int alive(int fd) {
    struct pollfd p={.fd=fd,.events=POLLIN}; return fd>=0 && poll(&p,1,0)==0;
}
static inline int anchor_equal(int a,int b) {
    struct stat x,y; return a>=0 && b>=0 && !fstat(a,&x) && !fstat(b,&y) && x.st_dev==y.st_dev && x.st_ino==y.st_ino;
}
static inline int wait_fd(int fd,short events,uint64_t until) {
    for(;;){uint64_t n=tick_us(); if(n>=until)return 0;
        struct pollfd p={.fd=fd,.events=events}; uint64_t ms=(until-n+999)/1000;
        int r=poll(&p,1,(int)(ms>1000?1000:ms));
        if(r>0)return (p.revents&events)!=0;
        if(r<0 && errno!=EINTR)return 0;
    }
}
static inline void put32(unsigned char **p,uint32_t v){for(int i=3;i>=0;i--)*(*p)++=(unsigned char)(v>>(i*8));}
static inline uint32_t get32(const unsigned char **p){uint32_t v=0;for(int i=0;i<4;i++)v=(v<<8)|*(*p)++;return v;}
static inline void put64(unsigned char **p,uint64_t v){for(int i=7;i>=0;i--)*(*p)++=(unsigned char)(v>>(i*8));}
static inline uint64_t get64(const unsigned char **p){uint64_t v=0;for(int i=0;i<8;i++)v=(v<<8)|*(*p)++;return v;}
static inline void header(unsigned char *b,unsigned type,unsigned payload){memcpy(b,"G3F4",4);b[4]=0;b[5]=1;b[6]=(unsigned char)type;b[7]=0;unsigned char *p=b+8;put32(&p,payload);}
static inline void putstr(unsigned char **p,const char *s){size_t n=strlen(s);*(*p)++=0;*(*p)++=(unsigned char)n;memcpy(*p,s,n);*p+=n;}
static inline int getstr(const unsigned char **p,const unsigned char *end,char *out){
    if(end-*p<2)return 0;
    unsigned n=(*p)[0]*256+(*p)[1];*p+=2;
    if(!n||n>63||end-*p<(int)n)return 0;
    /* Conservative ASCII fixture subset: non-ASCII denied, no normalization. */
    for(unsigned i=0;i<n;i++)if((*p)[i]<32||(*p)[i]>126)return 0;
    memcpy(out,*p,n);out[n]=0;*p+=n;return 1;
}
static inline size_t encode_request(unsigned char *b,const request_fields *r){
    unsigned char *p=b+12;memcpy(p,r->binding,16);p+=16;*p++=r->slot;put32(&p,r->role);putstr(&p,r->role_name);put32(&p,r->db);putstr(&p,r->db_name);
    memcpy(p,r->deployment,16);p+=16;memcpy(p,r->incarnation,16);p+=16;memcpy(p,r->epoch,32);p+=32;
    put64(&p,(uint64_t)r->postmaster_start);put64(&p,(uint64_t)r->backend_start);
    memcpy(p,r->fingerprint,32);p+=32;memcpy(p,r->policy,32);p+=32;header(b,1,(unsigned)(p-b-12));return (size_t)(p-b);
}
static inline int decode_request(const unsigned char *b,size_t n,request_fields *r){
    if(n<185||n>311||memcmp(b,"G3F4",4)||b[4]||b[5]!=1||b[6]!=1||b[7])return 0;
    const unsigned char *p=b+8,*end=b+n;if(get32(&p)!=n-12)return 0;
    memcpy(r->binding,p,16);p+=16;r->slot=*p++;r->role=get32(&p);
    if(!getstr(&p,end,r->role_name)||end-p<4)return 0;
    r->db=get32(&p);if(!getstr(&p,end,r->db_name)||end-p!=144)return 0;
    memcpy(r->deployment,p,16);p+=16;memcpy(r->incarnation,p,16);p+=16;memcpy(r->epoch,p,32);p+=32;
    r->postmaster_start=(int64_t)get64(&p);r->backend_start=(int64_t)get64(&p);
    memcpy(r->fingerprint,p,32);p+=32;memcpy(r->policy,p,32);p+=32;
    return p==end && r->slot>=1 && r->slot<=4 && r->role && r->db && r->postmaster_start!=INT64_MAX && r->postmaster_start!=INT64_MIN && r->backend_start!=INT64_MAX && r->backend_start!=INT64_MIN;
}
static inline int context_matches(const test_context *c,const request_fields *r){
    unsigned i=r->slot-1;return i<4 && r->role==c->role_oid[i] && r->db==c->db_oid && !strcmp(r->role_name,c->role_name[i]) && !strcmp(r->db_name,c->db_name)
    && !memcmp(r->binding,c->binding,16) && !memcmp(r->deployment,c->deployment,16) && !memcmp(r->incarnation,c->incarnation,16)
    && !memcmp(r->epoch,c->epoch,32) && !memcmp(r->fingerprint,c->fingerprint,32) && !memcmp(r->policy,c->policy,32);
}
static inline int send_anchor(int fd,const unsigned char *b,size_t n,int anchor){
    union{struct cmsghdr align;char bytes[CMSG_SPACE(sizeof(int))];} ctrl={0};
    struct iovec iov={.iov_base=(void *)b,.iov_len=n};struct msghdr m={.msg_iov=&iov,.msg_iovlen=1,.msg_control=ctrl.bytes,.msg_controllen=sizeof(ctrl.bytes)};
    struct cmsghdr *x=CMSG_FIRSTHDR(&m);x->cmsg_level=SOL_SOCKET;x->cmsg_type=SCM_RIGHTS;x->cmsg_len=CMSG_LEN(sizeof(int));memcpy(CMSG_DATA(x),&anchor,sizeof(int));
    return sendmsg(fd,&m,MSG_NOSIGNAL|MSG_DONTWAIT)==(ssize_t)n;
}
#endif
