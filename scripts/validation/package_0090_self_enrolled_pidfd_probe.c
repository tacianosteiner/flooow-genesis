/* TEST ONLY: controlled children, descriptor transfer, signal 0 only.
 * No PostgreSQL integration, SIGINT/SIGTERM, numeric kill or PID fallback.
 */
#define _GNU_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <poll.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/prctl.h>
#include <sys/socket.h>
#include <sys/stat.h>
#include <sys/syscall.h>
#include <sys/un.h>
#include <sys/utsname.h>
#include <sys/wait.h>
#include <unistd.h>
#ifndef SO_PASSPIDFD
#define SO_PASSPIDFD 76
#endif
#ifndef SO_PEERPIDFD
#define SO_PEERPIDFD 77
#endif
#ifndef SCM_PIDFD
#define SCM_PIDFD 4
#endif

struct metadata { int32_t pid, variant, forged_credentials_errno; };
static void require(int condition, const char *operation) {
    if (!condition) { perror(operation); exit(70); }
}
static int same_anchor(int a, int b) {
    struct stat sa, sb;
    return a >= 0 && b >= 0 && fstat(a, &sa) == 0 && fstat(b, &sb) == 0 &&
           sa.st_dev == sb.st_dev && sa.st_ino == sb.st_ino;
}
static int send_fds(int socket_fd, int fd, struct metadata *data, int duplicate,
                    int forged_pid) {
    union { struct cmsghdr align; char bytes[256]; } control = {0};
    struct iovec io = { .iov_base = data, .iov_len = sizeof(*data) };
    struct msghdr message = { .msg_iov = &io, .msg_iovlen = 1,
        .msg_control = control.bytes,
        .msg_controllen = CMSG_SPACE(sizeof(int) * (duplicate ? 2 : 1)) +
                          (forged_pid ? CMSG_SPACE(sizeof(struct ucred)) : 0) };
    struct cmsghdr *cm = CMSG_FIRSTHDR(&message);
    cm->cmsg_level = SOL_SOCKET; cm->cmsg_type = SCM_RIGHTS;
    cm->cmsg_len = CMSG_LEN(sizeof(int) * (duplicate ? 2 : 1));
    int fds[2] = { fd, fd };
    memcpy(CMSG_DATA(cm), fds, sizeof(int) * (duplicate ? 2 : 1));
    if (forged_pid) {
        cm = CMSG_NXTHDR(&message, cm);
        require(cm != NULL, "credential ancillary allocation");
        cm->cmsg_level = SOL_SOCKET; cm->cmsg_type = SCM_CREDENTIALS;
        cm->cmsg_len = CMSG_LEN(sizeof(struct ucred));
        struct ucred credential = { .pid = forged_pid, .uid = getuid(), .gid = getgid() };
        memcpy(CMSG_DATA(cm), &credential, sizeof(credential));
    }
    return sendmsg(socket_fd, &message, MSG_NOSIGNAL);
}
int main(void) {
    struct utsname kernel; require(uname(&kernel) == 0, "uname");
    printf("{\"kernel\":\"%s\",\"uid\":%u,\"seccomp\":%d,\"signal_numbers\":[0]}\n",
           kernel.release, getuid(), prctl(PR_GET_SECCOMP));
    char directory[] = "/tmp/0090-anchor-XXXXXX";
    require(mkdtemp(directory) != NULL, "private directory");
    require(chmod(directory, 0700) == 0, "directory mode");
    struct sockaddr_un address = { .sun_family = AF_UNIX };
    require(snprintf(address.sun_path, sizeof(address.sun_path), "%s/enroll", directory)
            < (int)sizeof(address.sun_path), "socket pathname");
    int listener = socket(AF_UNIX, SOCK_SEQPACKET | SOCK_CLOEXEC, 0);
    require(listener >= 0, "socket");
    int one = 1;
    require(setsockopt(listener, SOL_SOCKET, SO_PASSCRED, &one, sizeof(one)) == 0, "SO_PASSCRED");
    require(setsockopt(listener, SOL_SOCKET, SO_PASSPIDFD, &one, sizeof(one)) == 0, "SO_PASSPIDFD");
    mode_t old_umask = umask(0077);
    require(bind(listener, (struct sockaddr *)&address, sizeof(address)) == 0, "bind");
    umask(old_umask);
    require(chmod(address.sun_path, 0600) == 0, "socket mode");
    require(listen(listener, 4) == 0, "listen");
    for (int variant = 0; variant < 5; variant++) {
        int gate[2]; require(pipe2(gate, O_CLOEXEC) == 0, "ack pipe");
        pid_t parent = getpid(), subject = fork(); require(subject >= 0, "controlled fork");
        if (subject == 0) {
            close(listener); close(gate[1]);
            struct metadata data = { .pid = getpid(), .variant = variant };
            int self = syscall(SYS_pidfd_open, getpid(), 0);
            require(self >= 0, "self pidfd_open");
            int transport = socket(AF_UNIX, SOCK_SEQPACKET | SOCK_CLOEXEC, 0);
            require(transport >= 0 && connect(transport, (struct sockaddr *)&address, sizeof(address)) == 0, "connect");
            if (variant == 4) {
                errno = 0;
                int forged = send_fds(transport, self, &data, 0, parent);
                data.forged_credentials_errno = errno;
                require(forged == -1 && errno == EPERM, "forged PID rejected");
            }
            int supplied = self;
            if (variant == 2) {
                supplied = syscall(SYS_pidfd_open, parent, 0);
                require(supplied >= 0, "controlled wrong anchor");
            }
            require(send_fds(transport, supplied, &data, variant == 3, 0) == sizeof(data), "SCM_RIGHTS send");
            if (supplied != self) close(supplied);
            close(self); close(transport);
            if (variant != 1) { char ack; require(read(gate[0], &ack, 1) == 1, "ack"); }
            close(gate[0]); _exit(0);
        }
        close(gate[0]);
        int connected = accept4(listener, NULL, NULL, SOCK_CLOEXEC);
        require(connected >= 0, "accept");
        struct ucred peer; socklen_t length = sizeof(peer);
        require(getsockopt(connected, SOL_SOCKET, SO_PEERCRED, &peer, &length) == 0, "SO_PEERCRED");
        int kernel_peer = -1; length = sizeof(kernel_peer);
        require(getsockopt(connected, SOL_SOCKET, SO_PEERPIDFD, &kernel_peer, &length) == 0 && kernel_peer >= 0, "SO_PEERPIDFD");
        union { struct cmsghdr align; char bytes[512]; } control = {0};
        struct metadata data = {0};
        struct iovec io = { .iov_base = &data, .iov_len = sizeof(data) };
        struct msghdr message = { .msg_iov = &io, .msg_iovlen = 1,
            .msg_control = control.bytes, .msg_controllen = sizeof(control.bytes) };
        require(recvmsg(connected, &message, MSG_CMSG_CLOEXEC) == sizeof(data), "recvmsg");
        int rights[8], count = 0, kernel_sender = -1, credential_count = 0;
        struct ucred credentials = {0};
        for (struct cmsghdr *cm = CMSG_FIRSTHDR(&message); cm; cm = CMSG_NXTHDR(&message, cm)) {
            require(cm->cmsg_level == SOL_SOCKET, "ancillary family");
            if (cm->cmsg_type == SCM_RIGHTS) {
                size_t number = (cm->cmsg_len - CMSG_LEN(0)) / sizeof(int);
                require(number <= 8 && count + number <= 8, "bounded fd list");
                memcpy(rights + count, CMSG_DATA(cm), number * sizeof(int)); count += number;
            } else if (cm->cmsg_type == SCM_CREDENTIALS) {
                require(cm->cmsg_len == CMSG_LEN(sizeof(credentials)), "credential length");
                memcpy(&credentials, CMSG_DATA(cm), sizeof(credentials)); credential_count++;
            } else if (cm->cmsg_type == SCM_PIDFD) {
                require(kernel_sender < 0 && cm->cmsg_len == CMSG_LEN(sizeof(int)), "kernel pidfd length");
                memcpy(&kernel_sender, CMSG_DATA(cm), sizeof(kernel_sender));
            } else require(0, "unexpected ancillary type");
        }
        require(!(message.msg_flags & (MSG_CTRUNC | MSG_TRUNC)), "complete message");
        require(kernel_sender >= 0 && credential_count == 1, "kernel sender evidence");
        int peer_match = peer.pid == subject && peer.uid == getuid() &&
            credentials.pid == subject && credentials.uid == getuid() && data.pid == subject;
        require(peer_match, "peer binding");
        require(same_anchor(kernel_sender, kernel_peer), "connect and message anchor match");
        int fd_match = count == 1 && same_anchor(rights[0], kernel_sender);
        require((variant == 2 || variant == 3) ? !fd_match : fd_match, "anchor substitution decision");
        int status = 0;
        if (variant == 1) require(waitpid(subject, &status, 0) == subject, "reap early exit");
        int live_result = -2, live_errno = 0;
        if (fd_match) { errno = 0; live_result = syscall(SYS_pidfd_send_signal, rights[0], 0, NULL, 0); live_errno = errno; }
        if (variant != 1) {
            require(write(gate[1], "x", 1) == 1, "release subject");
            require(waitpid(subject, &status, 0) == subject, "reap subject");
        }
        require(WIFEXITED(status) && WEXITSTATUS(status) == 0, "normal controlled exit");
        close(gate[1]); close(connected);
        struct pollfd dead = { .fd = kernel_sender, .events = POLLIN };
        int readiness = poll(&dead, 1, 1000);
        errno = 0; int dead_result = syscall(SYS_pidfd_send_signal, kernel_sender, 0, NULL, 0), dead_errno = errno;
        require(readiness == 1 && (dead.revents & POLLIN) && dead_result == -1 && dead_errno == ESRCH, "dead anchor");
        int reused = 0;
        for (int index = 0; index < 128; index++) {
            pid_t churn = fork(); require(churn >= 0, "bounded churn");
            if (churn == 0) _exit(0);
            if (churn == subject) reused++;
            require(waitpid(churn, &status, 0) == churn, "churn reap");
            errno = 0;
            require(syscall(SYS_pidfd_send_signal, kernel_sender, 0, NULL, 0) == -1 && errno == ESRCH, "retained anchor after churn");
        }
        printf("{\"variant\":%d,\"subject_pid\":%d,\"peer_pid\":%d,\"message_pid\":%d,\"rights_count\":%d,\"same_anchor\":%s,\"decision\":\"%s\",\"live_signal_zero_result\":%d,\"live_errno\":%d,\"dead_poll\":%d,\"dead_signal_zero_result\":%d,\"dead_errno\":%d,\"churn_count\":128,\"numeric_pid_reuse_count\":%d,\"forged_credentials_errno\":%d}\n",
            variant, subject, peer.pid, credentials.pid, count, fd_match ? "true" : "false",
            fd_match ? "ANCHOR_MATCH" : "DENY_SUBSTITUTED_OR_EXTRA_FD", live_result, live_errno,
            readiness, dead_result, dead_errno, reused, data.forged_credentials_errno);
        for (int index = 0; index < count; index++) close(rights[index]);
        close(kernel_sender);
        close(kernel_peer);
    }
    close(listener); require(unlink(address.sun_path) == 0, "socket cleanup");
    require(rmdir(directory) == 0, "private directory cleanup");
    return 0;
}
