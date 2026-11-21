#define _GNU_SOURCE
#include <stdlib.h>
#define main unused_original_main
#include "observer_fixture_tests.c"
#undef main
int main(int argc,char **argv){unsigned role=argc==2?(unsigned)atoi(argv[1]):0;if(role!=1&&role!=2)return 2;int pipes[2];if(!setup(role,pipes))return 3;r.max_age_us=10000000;r.expires_us+=9000000;r.window.barrier_valid_until_us+=9000000;in.window.barrier_valid_until_us=r.window.barrier_valid_until_us;
 printf("EXPECTED %u %llu %llu %llu %llu %llu %llu\n",role,(unsigned long long)r.window.started_us,(unsigned long long)r.window.finished_us,(unsigned long long)r.not_before_us,(unsigned long long)r.expires_us,(unsigned long long)r.max_age_us,(unsigned long long)r.window.barrier_valid_until_us);fflush(stdout);
 S03Evidence out={0};int rc=call(role,&out);if(rc||out.status)return 4;printf("FRAME ");for(uint32_t i=0;i<out.frame_size;i++)printf("%02x",frame[i]);printf("\nUSE_TIME %llu\n",(unsigned long long)now_us());close(pipes[0]);close(pipes[1]);return 0;}
