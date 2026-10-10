#include <stdio.h>
#include <time.h>
int main(void){struct timespec t;if(clock_gettime(CLOCK_BOOTTIME,&t))return 1;printf("%llu\n",(unsigned long long)t.tv_sec*1000000+t.tv_nsec/1000);return 0;}
