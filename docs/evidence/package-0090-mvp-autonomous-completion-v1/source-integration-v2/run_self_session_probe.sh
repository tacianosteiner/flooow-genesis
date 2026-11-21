#!/bin/sh
set -eu
umask 077
gosu 999:10000 /bin/sh -c 'umask 007; mkdir /tmp/s03-socket; mkdir -m 0700 /tmp/s03-data'
gcc -std=c11 -O2 -Wall -Wextra -Werror -I/pgheaders/interfaces/libpq -I/pgheaders/include /probe/self_session_custody_probe.c /probe/immutable_export.c -l:libpq.so.5 -lcrypto -o /tmp/self-session-probe
chmod 0555 /tmp/self-session-probe
gosu 999:10000 initdb -D /tmp/s03-data --auth-local=trust --auth-host=reject --no-locale > /tmp/initdb.log
gosu 999:10000 pg_ctl -D /tmp/s03-data -l /tmp/s03-data/postgres.log -o "-k /tmp/s03-socket -c listen_addresses='' -c unix_socket_permissions=0770" -w start
trap 'gosu 999:10000 pg_ctl -D /tmp/s03-data -m immediate -w stop' EXIT
gosu 999:10000 psql -X -v ON_ERROR_STOP=1 -h /tmp/s03-socket -U postgres -d postgres <<'SQL'
SET password_encryption='scram-sha-256';
CREATE ROLE flooow_reader LOGIN NOSUPERUSER NOINHERIT NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS PASSWORD 'PUBLIC_SYNTHETIC_PROBE_ONLY';
SQL
# Bootstrap trust is removed before the Reader/probe starts. No host/TCP path.
gosu 999:10000 /bin/sh -c 'cat > /tmp/s03-data/pg_hba.conf' <<'HBA'
local all postgres peer
local postgres flooow_reader scram-sha-256
local all all reject
host all all all reject
HBA
gosu 999:10000 pg_ctl -D /tmp/s03-data reload
gosu 999:10000 psql -X -v ON_ERROR_STOP=1 -h /tmp/s03-socket -U postgres -d postgres -c 'SELECT type,database,user_name,address,auth_method,error FROM pg_hba_file_rules ORDER BY rule_number;'
/tmp/self-session-probe
