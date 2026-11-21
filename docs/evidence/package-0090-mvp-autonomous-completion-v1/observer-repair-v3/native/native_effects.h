#ifndef FLOOOW_S03_FIXED_NATIVE_EFFECTS_H
#define FLOOOW_S03_FIXED_NATIVE_EFFECTS_H
#if !defined(__linux__) || !defined(__x86_64__) || defined(__ILP32__)
#error "Fixed observer effect adapter requires the pinned Linux x86_64 ABI"
#endif
#include <stddef.h>
#include <stdint.h>
#include <sys/stat.h>
#include <sys/syscall.h>
#include <time.h>
#include <unistd.h>
#include <fcntl.h>
_Static_assert(sizeof(long)==8&&sizeof(void *)==8,"LP64 required");
_Static_assert(sizeof(struct timespec)==16&&offsetof(struct timespec,tv_nsec)==8,"Kernel timespec ABI required");
_Static_assert(sizeof(struct stat)==144&&offsetof(struct stat,st_dev)==0&&offsetof(struct stat,st_ino)==8&&offsetof(struct stat,st_mode)==24,"Kernel x86_64 stat ABI required");
/* Same four already declared effects, no externally callable syscall dispatch.
 * Negative kernel errno is deliberately not published to TLS: all callers
 * require zero/success or exact write length and fail closed on any error.
 * This does not prove kernel/platform authority or qualify the caller/FD. */
static inline long s03_fixed_call3(long number,long first,long second,long third) {
    long result;
    __asm__ volatile("syscall" : "=a"(result) : "a"(number),"D"(first),"S"(second),"d"(third) : "rcx","r11","memory");
    return result;
}
static inline long s03_clock_gettime(struct timespec *value) {
    return s03_fixed_call3(SYS_clock_gettime,CLOCK_BOOTTIME,(long)(uintptr_t)value,0);
}
static inline long s03_getfl(int fd) {
    return s03_fixed_call3(SYS_fcntl,fd,F_GETFL,0);
}
static inline long s03_fstat(int fd,struct stat *value) {
    return s03_fixed_call3(SYS_fstat,fd,(long)(uintptr_t)value,0);
}
static inline long s03_write(int fd,const void *bytes,size_t count) {
    return s03_fixed_call3(SYS_write,fd,(long)(uintptr_t)bytes,(long)count);
}
#endif
