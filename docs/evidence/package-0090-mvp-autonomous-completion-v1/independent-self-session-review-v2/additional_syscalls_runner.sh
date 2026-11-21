#!/bin/sh
set -eu
umask 077
mkdir /tmp/s03-socket /tmp/s03-data
gcc -std=c11 -O2 -Wall -Wextra -Werror -I/pgheaders/interfaces/libpq -I/pgheaders/include /review/additional_syscalls_variant.c /probe/immutable_export.c -l:libpq.so.5 -o /tmp/self-session-probe
initdb -D /tmp/s03-data --auth-local=trust --auth-host=reject --no-locale > /tmp/initdb.log
pg_ctl -D /tmp/s03-data -l /tmp/postgres.log -o "-k /tmp/s03-socket -c listen_addresses='' -c unix_socket_permissions=0700" -w start
trap 'pg_ctl -D /tmp/s03-data -m immediate -w stop' EXIT
psql -X -v ON_ERROR_STOP=1 -h /tmp/s03-socket -U postgres -d postgres <<'SQL'
SET password_encryption='scram-sha-256';
CREATE ROLE flooow_reader LOGIN NOSUPERUSER NOINHERIT NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS PASSWORD 'PUBLIC_SYNTHETIC_PROBE_ONLY';
SQL
# Bootstrap trust is removed before the Reader/probe starts. No host/TCP path.
cat > /tmp/s03-data/pg_hba.conf <<'HBA'
local all postgres peer
local postgres flooow_reader scram-sha-256
local all all reject
host all all all reject
HBA
pg_ctl -D /tmp/s03-data reload
psql -X -v ON_ERROR_STOP=1 -h /tmp/s03-socket -U postgres -d postgres -c 'SELECT type,database,user_name,address,auth_method,error FROM pg_hba_file_rules ORDER BY rule_number;'
PGSERVICE=nonexistent PGHOST=203.0.113.1 PGPASSFILE=/nonexistent PGOPTIONS="-c invalid_parameter=1" /tmp/self-session-probe
