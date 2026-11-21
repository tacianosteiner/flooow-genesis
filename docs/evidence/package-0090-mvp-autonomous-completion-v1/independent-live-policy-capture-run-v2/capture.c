#define _GNU_SOURCE
#include <sys/stat.h>
#include <sys/prctl.h>
#include <sys/syscall.h>
#include <linux/capability.h>
#include <fcntl.h>
#include <unistd.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
#include <openssl/sha.h>
static void fail(void){fputs("bounded capture refused\n",stderr);exit(78);}
static uint64_t number(const char *s){char *end;errno=0;unsigned long long n=strtoull(s,&end,10);if(!*s||*s=='-'||errno||*end)fail();return n;}
static uint64_t birth(unsigned pid){char path[80],line[4096];snprintf(path,sizeof(path),"/proc/%u/stat",pid);FILE *f=fopen(path,"re");if(!f)fail();if(!fgets(line,sizeof(line),f))fail();fclose(f);char *p=strrchr(line,')'),*save=NULL;if(!p||p[1]!=' ')fail();p=strtok_r(p+2," ",&save);for(unsigned i=3;i<22;++i){if(!p)fail();p=strtok_r(NULL," ",&save);}if(!p)fail();return number(p);}
static void readonly_original(unsigned pid,unsigned fd){char path[80],line[512];snprintf(path,sizeof(path),"/proc/%u/fdinfo/%u",pid,fd);FILE *f=fopen(path,"re");if(!f)fail();int found=0;while(fgets(line,sizeof(line),f)){if(!strncmp(line,"flags:\t",7)){char *end;errno=0;unsigned long flags=strtoul(line+7,&end,8);if(errno||(*end!='\n'&&*end)||((flags&O_ACCMODE)!=O_RDONLY))fail();found++;}}fclose(f);if(found!=1)fail();}
static void check(int fd,uint64_t device,uint64_t inode,uint64_t size){struct stat st;if(fstat(fd,&st)||!S_ISREG(st.st_mode)||st.st_uid!=10003||st.st_size<1||st.st_size>4096||(uint64_t)st.st_dev!=device||(uint64_t)st.st_ino!=inode||(uint64_t)st.st_size!=size)fail();if((fcntl(fd,F_GETFL)&O_ACCMODE)!=O_RDONLY||fcntl(fd,F_GET_SEALS)!=(F_SEAL_SEAL|F_SEAL_SHRINK|F_SEAL_GROW|F_SEAL_WRITE))fail();}
int main(int argc,char **argv){if(argc!=8)fail();uint64_t p=number(argv[1]),d=number(argv[2]),started=number(argv[3]),device=number(argv[4]),inode=number(argv[5]),size=number(argv[6]);if(!p||p>2147483647||d>63||!started||size<1||size>4096||strlen(argv[7])!=64)fail();for(unsigned i=0;i<64;++i)if(!((argv[7][i]>='0'&&argv[7][i]<='9')||(argv[7][i]>='a'&&argv[7][i]<='f')))fail();if(birth((unsigned)p)!=started)fail();readonly_original((unsigned)p,(unsigned)d);char path[80];snprintf(path,sizeof(path),"/proc/%u/fd/%u",(unsigned)p,(unsigned)d);int fd=open(path,O_RDONLY|O_CLOEXEC|O_NONBLOCK);if(fd<0)fail();check(fd,device,inode,size);if(birth((unsigned)p)!=started)fail();
/* Privileged access ends immediately after opening the exact record. */
struct __user_cap_header_struct h={.version=_LINUX_CAPABILITY_VERSION_3,.pid=0};struct __user_cap_data_struct zero[2]={{0},{0}};if(syscall(SYS_capset,&h,zero)||prctl(PR_SET_NO_NEW_PRIVS,1,0,0,0))fail();
unsigned char bytes[4096],digest[32];size_t offset=0;while(offset<size){ssize_t n=pread(fd,bytes+offset,(size_t)size-offset,(off_t)offset);if(n<=0)fail();offset+=(size_t)n;}check(fd,device,inode,size);if(!SHA256(bytes,(size_t)size,digest))fail();char hash[65];for(unsigned i=0;i<32;++i)snprintf(hash+i*2,3,"%02x",digest[i]);if(strcmp(hash,argv[7]))fail();close(fd);
/* No payload interpretation or approval. PID identity after open is checked by
 * the external exact-container manager; opened sealed inode is already pinned. */
printf("{\"kind\":\"INDEPENDENT_READONLY_POLICY_CAPTURE\",\"pid\":%llu,\"fd\":%llu,\"start_ticks\":%llu,\"uid\":10003,\"device\":%llu,\"inode\":%llu,\"size\":%llu,\"seals\":15,\"sha256\":\"%s\",\"hex\":\"",(unsigned long long)p,(unsigned long long)d,(unsigned long long)started,(unsigned long long)device,(unsigned long long)inode,(unsigned long long)size,hash);for(size_t i=0;i<size;++i)printf("%02x",bytes[i]);puts("\",\"qualification\":\"NOT_PERFORMED\",\"acceptance\":\"NOT_ISSUED\"}");return 0;}
