/* One controlled impersonator fixture. No process signaling. */
#include "protocol.h"
int main(void){
    int fd=socket(AF_UNIX,SOCK_SEQPACKET,0);struct sockaddr_un a={.sun_family=AF_UNIX};strcpy(a.sun_path,TEST_SOCKET);umask(0077);
    if(fd<0||bind(fd,(struct sockaddr *)&a,sizeof(a))||listen(fd,1))return 70;
    int client=accept(fd,NULL,NULL);if(client<0)return 70;close(client);close(fd);unlink(TEST_SOCKET);return 0;
}
