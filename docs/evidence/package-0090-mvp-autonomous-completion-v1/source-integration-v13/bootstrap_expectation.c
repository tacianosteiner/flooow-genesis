#define _GNU_SOURCE
#include "bootstrap_expectation.h"
#include <assert.h>
#include <errno.h>
#include <fcntl.h>
#include <grp.h>
#include <libpq-fe.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <sys/wait.h>
#include <time.h>
#include <unistd.h>
int s03_publish_immutable(const void *,size_t);
static uint64_t tick(void){struct timespec t;assert(clock_gettime(CLOCK_BOOTTIME,&t)==0);return (uint64_t)t.tv_sec*1000000+(uint64_t)t.tv_nsec/1000;}
static uint64_t integer(PGresult *r,int field,Oid type,int size){
    assert(!PQgetisnull(r,0,field)&&PQftype(r,field)==type&&PQgetlength(r,0,field)==size);
    uint64_t value=0;const unsigned char *bytes=(const unsigned char *)PQgetvalue(r,0,field);
    for(int i=0;i<size;++i){value=(value<<8)|bytes[i];}
    return value;
}
static unsigned hex(char c){if(c>='0'&&c<='9')return (unsigned)(c-'0');if(c>='a'&&c<='f')return (unsigned)(c-'a'+10);assert(0);return 0;}
static void measure(S03RawBootstrap *b){
    memset(b,0,sizeof(*b));b->magic=0x42505231;b->version=1;b->started_us=tick();
    FILE *boot=fopen("/proc/sys/kernel/random/boot_id","r");assert(boot);char text[40];assert(fgets(text,sizeof(text),boot));fclose(boot);
    assert(strlen(text)==37&&text[8]=='-'&&text[13]=='-'&&text[18]=='-'&&text[23]=='-'&&text[36]=='\n');
    unsigned out=0;for(unsigned i=0;i<36;){if(text[i]=='-'){++i;continue;}assert(out<16&&i+1<36);b->boot_id[out++]=(uint8_t)((hex(text[i])<<4)|hex(text[i+1]));i+=2;}assert(out==16);
    struct stat ns;assert(stat("/proc/self/ns/time",&ns)==0&&ns.st_ino);b->time_namespace_inode=ns.st_ino;
    assert(clearenv()==0&&setenv("PATH","/usr/bin:/bin",1)==0&&setenv("LC_ALL","C",1)==0);
    PGconn *c=PQconnectdb("host=/tmp/s03-socket port=5432 dbname=postgres user=postgres passfile=/dev/null sslmode=disable gssencmode=disable require_auth=none options='' connect_timeout=5 application_name=s03_bootstrap_measurement");assert(PQstatus(c)==CONNECTION_OK);
    PGresult *begin=PQexec(c,"BEGIN READ ONLY");assert(PQresultStatus(begin)==PGRES_COMMAND_OK);PQclear(begin);
    const char *sql="SELECT (pg_catalog.pg_control_system()).system_identifier,d.oid,r.oid,r.rolname,pg_catalog.pg_postmaster_start_time(),r.rolcanlogin,r.rolsuper,r.rolinherit,r.rolcreaterole,r.rolcreatedb,r.rolreplication,r.rolbypassrls,(SELECT count(*) FROM pg_catalog.pg_auth_members WHERE member=r.oid),(SELECT count(*) FROM pg_catalog.pg_stat_activity WHERE usename='flooow_reader') FROM pg_catalog.pg_database d CROSS JOIN pg_catalog.pg_roles r WHERE d.datname=current_database() AND r.rolname='flooow_reader'";
    PGresult *r=PQexecParams(c,sql,0,NULL,NULL,NULL,NULL,1);assert(PQresultStatus(r)==PGRES_TUPLES_OK&&PQntuples(r)==1&&PQnfields(r)==14);
    b->system_identifier=integer(r,0,20,8);b->database_oid=(uint32_t)integer(r,1,26,4);b->reader_oid=(uint32_t)integer(r,2,26,4);
    assert(PQftype(r,3)==19&&!PQgetisnull(r,0,3)&&PQgetlength(r,0,3)==13&&!memcmp(PQgetvalue(r,0,3),"flooow_reader",13));memcpy(b->reader_name,PQgetvalue(r,0,3),13);
    uint64_t server=integer(r,4,1184,8);memcpy(&b->server_start_pg_us,&server,8);
    assert(b->server_start_pg_us!=INT64_MIN&&b->server_start_pg_us!=INT64_MAX);
    for(int i=0;i<7;++i){b->flags[i]=(uint8_t)integer(r,5+i,16,1);assert(b->flags[i]==(i==0?1:0));}
    b->memberships=integer(r,12,20,8);b->reader_sessions=integer(r,13,20,8);
    assert(b->system_identifier&&b->database_oid&&b->reader_oid&&!b->memberships&&!b->reader_sessions);
    PQclear(r);PQfinish(c);b->finished_us=tick();assert(b->started_us<=b->finished_us);
}
void s03_read_raw_bootstrap(int fd,S03RawBootstrap *b){
    assert((fcntl(fd,F_GETFL)&O_ACCMODE)==O_RDONLY&&(fcntl(fd,F_GETFD)&FD_CLOEXEC));
    assert(fcntl(fd,F_GET_SEALS)==(F_SEAL_WRITE|F_SEAL_GROW|F_SEAL_SHRINK|F_SEAL_SEAL));
    struct stat st;assert(fstat(fd,&st)==0&&st.st_size==(off_t)sizeof(*b));
    assert(pread(fd,b,sizeof(*b),0)==sizeof(*b));
    assert(b->magic==0x42505231&&b->version==1&&b->started_us<=b->finished_us&&b->database_oid&&b->reader_oid&&b->system_identifier&&b->time_namespace_inode&&!b->memberships&&!b->reader_sessions&&!memcmp(b->reader_name,"flooow_reader",14));
    for(unsigned i=0;i<7;++i)assert(b->flags[i]==(i==0?1:0));
}
int s03_prepare_raw_bootstrap(void){
    assert(getuid()==0);int pipes[2];assert(pipe2(pipes,O_CLOEXEC)==0);pid_t child=fork();assert(child>=0);
    if(!child){close(pipes[0]);assert(setgroups(0,NULL)==0&&setgid(10000)==0&&setuid(999)==0);S03RawBootstrap b;measure(&b);assert(write(pipes[1],&b,sizeof(b))==sizeof(b));close(pipes[1]);_exit(0);}
    close(pipes[1]);S03RawBootstrap b;size_t offset=0;
    while(offset<sizeof(b)){ssize_t n=read(pipes[0],(char *)&b+offset,sizeof(b)-offset);if(n<0&&errno==EINTR)continue;assert(n>0);offset+=(size_t)n;}
    close(pipes[0]);int status;assert(waitpid(child,&status,0)==child&&WIFEXITED(status)&&WEXITSTATUS(status)==0);
    int fd=s03_publish_immutable(&b,sizeof(b));assert(fd>=0);S03RawBootstrap checked;s03_read_raw_bootstrap(fd,&checked);
    return fd;
}
