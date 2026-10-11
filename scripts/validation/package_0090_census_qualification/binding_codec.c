/* TEST_ONLY_NONCANONICAL independent native validator of frozen 38-tag framing. */
#include "protocol.h"
static uint32_t be32(const unsigned char *p){return ((uint32_t)p[0]<<24)|((uint32_t)p[1]<<16)|((uint32_t)p[2]<<8)|p[3];}
static int slots_valid(const unsigned char *p,size_t n){
    if(n<4||be32(p)!=4)return 0;size_t at=4;uint32_t ids[4]={0};char names[4][64]={{0}};
    for(unsigned i=0;i<4;i++){
        if(at+4>n)return 0;uint32_t size=be32(p+at);at+=4;
        if(size<10||at+size>n||p[at]!=i+1)return 0;
        ids[i]=be32(p+at+1);uint32_t len=be32(p+at+5);
        if(!ids[i]||len>63||size!=9+len||!text_nfc(p+at+9,len))return 0;
        memcpy(names[i],p+at+9,len);
        for(unsigned j=0;j<i;j++)if(ids[i]==ids[j]||!strcmp(names[i],names[j]))return 0;
        at+=size;
    }
    return at==n;
}
int main(int argc,char **argv){
    if(argc!=2)return 64;unsigned char b[16384];FILE *f=fopen(argv[1],"rb");if(!f)return 66;
    size_t n=fread(b,1,sizeof(b),f);int extra=fgetc(f);fclose(f);
    const char *domain="FLOOOW/OFFLINE-FIELD-PROOF/BINDING/V1";size_t dl=strlen(domain),at=4+dl+2;
    if(extra!=EOF||n<at||be32(b)!=dl||memcmp(b+4,domain,dl)||b[4+dl]!=0||b[5+dl]!=38)return 1;
    for(unsigned tag=1;tag<=38;tag++){
        if(at+6>n||b[at]!=0||b[at+1]!=tag)return 1;
        size_t size=be32(b+at+2);at+=6;if(!size||at+size>n||b[at]!=1)return 1;
        const unsigned char *p=b+at+1;size_t len=size-1;
        int uuid=(tag>=2&&tag<=6)||tag==8||tag==9||(tag>=13&&tag<=15)||(tag>=21&&tag<=28);
        if(uuid){if(len!=16)return 1;unsigned char any=0;for(unsigned i=0;i<16;i++)any|=p[i];if(!any)return 1;}
        else if(tag==1||tag==7||tag==12){if(len!=4||!be32(p))return 1;}
        else if(tag==10||tag==11||tag==35){if(len!=32)return 1;}
        else if(tag>=29&&tag<=31){if(len!=8)return 1;}
        else if(tag==32){if(!slots_valid(p,len))return 1;}
        else if(!text_nfc(p,len))return 1;
        at+=size;
    }
    if(at!=n)return 1;unsigned char digest[32];SHA256(b,n,digest);
    printf("BINDING_SHA256=");for(unsigned i=0;i<32;i++)printf("%02x",digest[i]);puts("");return 0;
}
