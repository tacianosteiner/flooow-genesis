#!/bin/sh
set -eu

LIBPQ="$(find /usr/lib /lib -name 'libpq.so.5*' -print 2>/dev/null | head -n 1)"

if [ -z "$LIBPQ" ]; then
  echo LIBPQ_NOT_FOUND >&2
  exit 41
fi

echo "LIBPQ=$LIBPQ"

gcc -std=c11 -O2 -Wall -Wextra \
  -I/src \
  -I/usr/include/postgresql \
  /src/self_session_custody_probe.c \
  /src/bootstrap_expectation.c \
  /src/immutable_export.c \
  /src/policy_candidate_custody.c \
  /src/private_credential.c \
  "$LIBPQ" \
  -lcrypto \
  -o /out/self-session-probe-v13

chmod 755 /out/self-session-probe-v13
test -x /out/self-session-probe-v13

echo V13_RUNTIME_BUILD_PASS
