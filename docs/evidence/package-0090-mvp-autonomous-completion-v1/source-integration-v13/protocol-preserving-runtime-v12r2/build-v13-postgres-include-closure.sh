#!/bin/sh
set -eu

LIBPQ="$(find /usr/lib /lib -name 'libpq.so.5*' -print 2>/dev/null | head -n 1)"

if [ -z "$LIBPQ" ]; then
  echo LIBPQ_RUNTIME_NOT_FOUND >&2
  exit 41
fi

test -f /pg-libpq/libpq-fe.h
test -f /pg-ext/postgres_ext.h

echo "LIBPQ=$LIBPQ"
echo "LIBPQ_FE=/pg-libpq/libpq-fe.h"
echo "POSTGRES_EXT=/pg-ext/postgres_ext.h"

gcc -std=c11 -O2 -Wall -Wextra \
  -I/src \
  -I/pg-libpq \
  -I/pg-ext \
  -I/pg-core \
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

echo V13_RUNTIME_BUILD_INCLUDE_CLOSURE_PASS
