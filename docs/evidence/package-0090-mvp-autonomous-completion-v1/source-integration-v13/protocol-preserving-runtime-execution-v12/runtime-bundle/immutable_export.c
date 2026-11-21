#define _GNU_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <stdint.h>
#include <stdio.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <unistd.h>

/* Private snapshot publication primitive, not an issuer or source acceptance.
 * Caller must separately qualify provenance and sole-owner/session custody.
 * On success the returned CLOEXEC descriptor is read-only and the underlying
 * object cannot be changed, grown, shrunk or stripped of its seals. */
int s03_publish_immutable(const void *bytes, size_t count) {
    if (!bytes || !count || count > 1048576) { errno = EINVAL; return -1; }
    int writer = memfd_create("s03-private-export", MFD_CLOEXEC | MFD_ALLOW_SEALING);
    if (writer < 0) return -1;
    size_t offset = 0;
    while (offset < count) {
        ssize_t n = write(writer, (const char *)bytes + offset, count - offset);
        if (n < 0 && errno == EINTR) continue;
        if (n <= 0) goto fail;
        offset += (size_t)n;
    }
    const int seals = F_SEAL_WRITE | F_SEAL_GROW | F_SEAL_SHRINK | F_SEAL_SEAL;
    if (fcntl(writer, F_ADD_SEALS, seals) < 0 ||
        fcntl(writer, F_GET_SEALS) != seals) goto fail;
    char path[64];
    int length = snprintf(path, sizeof(path), "/proc/self/fd/%d", writer);
    if (length < 0 || (size_t)length >= sizeof(path)) goto fail;
    int reader = open(path, O_RDONLY | O_CLOEXEC);
    if (reader < 0) goto fail;
    struct stat before, after;
    if (fstat(writer, &before) || fstat(reader, &after) ||
        before.st_dev != after.st_dev || before.st_ino != after.st_ino ||
        after.st_size != (off_t)count || fcntl(reader, F_GET_SEALS) != seals) {
        int saved = errno ? errno : EIO;
        close(reader); close(writer); errno = saved; return -1;
    }
    close(writer);
    return reader;
fail: {
    int saved = errno ? errno : EIO;
    close(writer); errno = saved; return -1;
}}
