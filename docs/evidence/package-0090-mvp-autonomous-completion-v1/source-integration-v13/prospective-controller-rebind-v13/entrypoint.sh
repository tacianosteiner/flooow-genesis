#!/bin/sh
set -eu
# Existing external HOST manager controls this private preparation stdin.
# This is neither an observer/native message-purpose ABI nor policy approval.
printf 'MANAGED_PREPARATION_READY\n'
IFS= read -r command
if [ "$command" != 'START_BOUND_RAW_PREPARATION' ]; then
    printf 'MANAGED_PREPARATION_NOT_AUTHORIZED\n' >&2
    exit 76
fi
exec /bin/sh /probe/run_self_session_probe.sh
