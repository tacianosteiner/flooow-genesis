#define _GNU_SOURCE
#include <assert.h>
#include <errno.h>
#include <fcntl.h>
#include <stdio.h>
#include <string.h>
#include <sys/mman.h>
#include <sys/wait.h>
#include <unistd.h>
int s03_publish_immutable(const void *, size_t);
int main(void) {
    const char payload[] = "private unaccepted source snapshot";
    assert(s03_publish_immutable(NULL, 1) == -1);
    assert(s03_publish_immutable(payload, 0) == -1);
    assert(s03_publish_immutable(payload, 1048577) == -1);
    int fd = s03_publish_immutable(payload, sizeof(payload)); assert(fd >= 0);
    assert((fcntl(fd, F_GETFL) & O_ACCMODE) == O_RDONLY);
    assert(fcntl(fd, F_GETFD) & FD_CLOEXEC);
    assert(write(fd, "X", 1) == -1 && errno == EBADF);
    char path[64]; snprintf(path, sizeof(path), "/proc/self/fd/%d", fd);
    /* Even reopening as writable must not recover a mutable capability. */
    int attacker = open(path, O_RDWR | O_CLOEXEC); assert(attacker >= 0);
    assert(pwrite(attacker, "X", 1, 0) == -1 && errno == EPERM);
    assert(ftruncate(attacker, 0) == -1 && errno == EPERM);
    assert(ftruncate(attacker, sizeof(payload) + 1) == -1 && errno == EPERM);
    assert(fcntl(attacker, F_ADD_SEALS, F_SEAL_WRITE) == -1 && errno == EPERM);
    assert(mmap(NULL, sizeof(payload), PROT_READ | PROT_WRITE, MAP_SHARED,
                attacker, 0) == MAP_FAILED && errno == EPERM);
    pid_t child = fork(); assert(child >= 0);
    if (!child) {
        char actual[sizeof(payload)];
        assert(pread(fd, actual, sizeof(actual), 0) == sizeof(actual));
        assert(!memcmp(actual, payload, sizeof(actual)));
        assert(pwrite(attacker, "Y", 1, 0) == -1 && errno == EPERM);
        _exit(0);
    }
    int status; assert(waitpid(child, &status, 0) == child);
    assert(WIFEXITED(status) && WEXITSTATUS(status) == 0);
    char actual[sizeof(payload)];
    assert(pread(fd, actual, sizeof(actual), 0) == sizeof(actual));
    assert(!memcmp(actual, payload, sizeof(actual)));
    close(attacker); close(fd);
    puts("PASS sealed snapshot: bounds, read-only descriptor, cloexec, reopened writes, truncate/grow, reseal, shared writable mapping, child mutation, exact bytes");
    puts("NOT_ESTABLISHED: source acceptance, issuer origin, unique owner, SQL custody, global replay");
    return 0;
}
