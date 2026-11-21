#!/bin/sh
set -eu
umask 077
gosu 999:10000 /bin/sh -c 'umask 007; mkdir /tmp/s03-socket; mkdir -m 0700 /tmp/s03-data'
gcc -std=c11 -O2 -Wall -Wextra -Werror -I/pgheaders/interfaces/libpq -I/pgheaders/include /probe/self_session_custody_probe.c /probe/bootstrap_expectation.c /probe/immutable_export.c /probe/policy_candidate_custody.c /probe/private_credential.c -l:libpq.so.5 -lcrypto -o /tmp/self-session-probe
chmod 0555 /tmp/self-session-probe
gosu 999:10000 initdb -D /tmp/s03-data --auth-local=trust --auth-host=reject --no-locale > /tmp/initdb.log
gosu 999:10000 pg_ctl -D /tmp/s03-data -l /tmp/s03-data/postgres.log -o "-k /tmp/s03-socket -c listen_addresses='' -c unix_socket_permissions=0770" -w start
trap 'gosu 999:10000 pg_ctl -D /tmp/s03-data -m immediate -w stop' EXIT
gosu 999:10000 psql -X -v ON_ERROR_STOP=1 -h /tmp/s03-socket -U postgres -d postgres <<'SQL'
SET password_encryption='scram-sha-256';
CREATE ROLE flooow_reader LOGIN NOSUPERUSER NOINHERIT NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS;
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
# Prospective raw bootstrap measurements BEFORE the Reader/child program starts.
# No approval manifest, policy, generation/highwater or acceptance is invented.
printf 'BOOTSTRAP_OS_BOOT_ID|'
cat /proc/sys/kernel/random/boot_id
printf 'BOOTSTRAP_TIME_NAMESPACE_INODE|'
stat -Lc '%i' /proc/self/ns/time
gosu 999:10000 psql -X -A -t -v ON_ERROR_STOP=1 -h /tmp/s03-socket -U postgres -d postgres <<'SQL'
SELECT 'BOOTSTRAP_PG|' || json_build_object(
  'database_system_identifier_sql_int64',(pg_catalog.pg_control_system()).system_identifier::text,
  'database_system_identifier_wire_hex',encode(pg_catalog.int8send((pg_catalog.pg_control_system()).system_identifier),'hex'),
  'database_oid',(SELECT oid::text FROM pg_catalog.pg_database WHERE datname=current_database()),
  'reader_role_oid',oid::text,
  'reader_role_name',rolname,
  'server_start_pg_us',(extract(epoch FROM (pg_catalog.pg_postmaster_start_time()-TIMESTAMPTZ '2000-01-01 00:00:00+00'))*1000000)::bigint::text,
  'server_start_pg_wire_hex',encode(pg_catalog.timestamptz_send(pg_catalog.pg_postmaster_start_time()),'hex'),
  'reader_flags',json_build_object('login',rolcanlogin,'superuser',rolsuper,'inherit',rolinherit,'create_role',rolcreaterole,'create_db',rolcreatedb,'replication',rolreplication,'bypass_rls',rolbypassrls),
  'reader_memberships',(SELECT count(*) FROM pg_catalog.pg_auth_members WHERE member=pg_roles.oid),
  'reader_sessions_before_candidate',(SELECT count(*) FROM pg_catalog.pg_stat_activity WHERE usename='flooow_reader')
)::text FROM pg_catalog.pg_roles WHERE rolname='flooow_reader';
SQL
/tmp/self-session-probe
