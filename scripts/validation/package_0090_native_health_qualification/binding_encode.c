/* TEST_ONLY_NONCANONICAL independent encoder from typed textual header values.
 * No Python framing or typed byte conversions enter this native component.
 */
#define main validate_frame_main
#include "binding_codec.c"
#undef main
static int nibble(char c){return c>='0'&&c<='9'?c-'0':c>='a'&&c<='f'?c-'a'+10:c>='A'&&c<='F'?c-'A'+10:-1;}
static size_t hex_decode(const char *s,unsigned char *out,size_t max){
    if(s[0]=='\\'&&s[1]=='x')s+=2;size_t n=strlen(s);if(n%2||n/2>max)return 0;
    for(size_t i=0;i<n;i+=2){int a=nibble(s[i]),b=nibble(s[i+1]);if(a<0||b<0)return 0;out[i/2]=(unsigned char)(a*16+b);}return n/2;
}
static int uuid_bytes(const char *s,unsigned char *out){
    if(strlen(s)!=36)return 0;char hex[33];unsigned at=0;
    for(unsigned i=0;i<36;i++){if(i==8||i==13||i==18||i==23){if(s[i]!='-')return 0;}else hex[at++]=s[i];}
    hex[32]=0;return hex_decode(hex,out,16)==16;
}
static int instant_bytes(const char *s,unsigned char *out){
    struct tm tm={0};char *end=strptime(s,"%Y-%m-%dT%H:%M:%S",&tm);if(!end)return 0;
    long micro=0;unsigned digits=0;if(*end=='.'){end++;while(*end>='0'&&*end<='9'){if(++digits>6)return 0;micro=micro*10+*end++-'0';}if(!digits)return 0;while(digits++<6)micro*=10;}
    if(strcmp(end,"Z")&&strcmp(end,"+00:00"))return 0;
    int64_t value=(int64_t)timegm(&tm)*1000000+micro;
    for(unsigned i=0;i<8;i++)out[i]=(unsigned char)((uint64_t)value>>(56-i*8));return 1;
}
int main(int argc,char **argv){
    if(argc!=3)return 64;FILE *in=fopen(argv[1],"r");if(!in)return 66;
    unsigned char b[16384],*at=b;const char *domain="FLOOOW/OFFLINE-FIELD-PROOF/BINDING/V1";
    put32(&at,(uint32_t)strlen(domain));memcpy(at,domain,strlen(domain));at+=strlen(domain);*at++=0;*at++=38;
    char *line=NULL;size_t cap=0;ssize_t len;
    for(unsigned tag=1;tag<=38;tag++){
        len=getline(&line,&cap,in);if(len<0){free(line);fclose(in);return 1;}
        if(len&&line[len-1]=='\n')line[--len]=0;if(len&&line[len-1]=='\r')line[--len]=0;
        char *v=strchr(line,'\t');if(!v||strtoul(line,NULL,10)!=tag){free(line);fclose(in);return 1;}*v++=0;
        unsigned char payload[4096],*p=payload;size_t size=0;
        int uuid=(tag>=2&&tag<=6)||tag==8||tag==9||(tag>=13&&tag<=15)||(tag>=21&&tag<=28);
        if(uuid){if(!uuid_bytes(v,p)){free(line);fclose(in);return 1;}size=16;}
        else if(tag==1||tag==7||tag==12){char *tail;unsigned long number=strtoul(v,&tail,10);if(*tail||!number||number>UINT32_MAX){free(line);fclose(in);return 1;}put32(&p,(uint32_t)number);size=4;}
        else if(tag==10||tag==11||tag==35||tag==32){size=hex_decode(v,payload,sizeof(payload));if(!size){free(line);fclose(in);return 1;}}
        else if(tag>=29&&tag<=31){if(!instant_bytes(v,payload)){free(line);fclose(in);return 1;}size=8;}
        else {size=strlen(v);if(size>sizeof(payload)||!text_nfc((unsigned char *)v,size)){free(line);fclose(in);return 1;}memcpy(payload,v,size);}
        if((size_t)(at-b)+7+size>sizeof(b)){free(line);fclose(in);return 1;}
        *at++=0;*at++=(unsigned char)tag;put32(&at,(uint32_t)size+1);*at++=1;memcpy(at,payload,size);at+=size;
    }
    int extra=fgetc(in);free(line);fclose(in);if(extra!=EOF)return 1;
    FILE *out=fopen(argv[2],"wb");if(!out)return 66;size_t n=(size_t)(at-b);if(fwrite(b,1,n,out)!=n){fclose(out);return 74;}fclose(out);
    char *validate[]={argv[0],argv[2],NULL};return validate_frame_main(2,validate);
}
