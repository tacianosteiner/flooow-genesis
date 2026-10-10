"""Disposable PG18.4 ADMIN syntax/rollback audit; never connects to the V6 root.

Negative gate tests materialize an enabled copy only in memory for this fixture.
Individual SQL statements are also resolved/executed in rolled-back transactions.
This does not qualify watchdog timing, host authority, or canonical activation.
"""
from pathlib import Path
import hashlib
import json
import re
import subprocess
import time
import uuid

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "scripts/operations/package-0090-v6/FLOOOW-G3F4-V6-ADMIN-AUTHORITY-BOUND-EXECUTABLE-R2.sql.txt"


def run(args, sql=None):
    return subprocess.run(args, input=sql, text=True, capture_output=True, timeout=45)


def main():
    raw = SOURCE.read_bytes()
    source = raw.decode("utf-8")
    name = "flooow-0090-v6-admin-audit-" + uuid.uuid4().hex[:12]
    image = run(["docker", "image", "inspect", "07fc165de5bb", "--format", "{{.Id}}"])
    assert image.returncode == 0, image.stderr
    result = {"source_sha256": hashlib.sha256(raw).hexdigest(), "image": image.stdout.strip(), "cases": {}}
    started = False
    try:
        created = run(["docker", "run", "--detach", "--name", name, "--network", "none",
                       "--tmpfs", "/tmp", "-e", "PGDATA=/tmp/pgdata",
                       "-e", "POSTGRES_HOST_AUTH_METHOD=trust", "--entrypoint",
                       "docker-entrypoint.sh", image.stdout.strip(), "postgres"])
        assert created.returncode == 0, created.stderr
        started = True
        def sql(text):
            return run(["docker", "exec", "-i", name, "psql", "-X", "-w", "-U", "postgres",
                        "-d", "postgres", "-At", "-v", "ON_ERROR_STOP=1"], text)
        for _ in range(30):
            if sql("SELECT 1;").returncode == 0:
                break
            time.sleep(0.5)
        assert sql("SHOW server_version_num;").stdout.strip() == "180004"
        setup = """
CREATE ROLE flooow_offline_control_owner NOLOGIN;
CREATE TABLE public.offline_binding_header(binding_id uuid, deployment_id uuid,
deployment_incarnation_id uuid, run_id uuid, plan_id uuid, manifest_id uuid,
deadline_policy_version text, deadline_policy_digest bytea);
CREATE TABLE public.offline_readiness(deployment_id uuid, incarnation_id uuid,
state text, watchdog_healthy boolean, policy_version text, policy_digest bytea,
watchdog_checked_at timestamptz);
CREATE TABLE public.offline_binding_lifecycle(binding_id uuid, state text, lock_token bigint);
CREATE TABLE public.offline_attempt_pointer(binding_id uuid, current_attempt_id uuid,
generation bigint, claim_permitted boolean, lock_token bigint);
ALTER TABLE public.offline_binding_header OWNER TO flooow_offline_control_owner;
ALTER TABLE public.offline_readiness OWNER TO flooow_offline_control_owner;
ALTER TABLE public.offline_binding_lifecycle OWNER TO flooow_offline_control_owner;
ALTER TABLE public.offline_attempt_pointer OWNER TO flooow_offline_control_owner;
"""
        assert sql(setup).returncode == 0
        declarations = dict(re.findall(r"(v_\w+) CONSTANT uuid := '([^']+)'", source))
        binding = declarations["v_binding_id"]
        deployment = declarations["v_deployment_id"]
        incarnation = declarations["v_incarnation_id"]
        digest = "e840fcadac2d5198a91cdb7b2345a31d4776cb3ead6e8b697391a4461a1a253d"
        seed = f"""
TRUNCATE offline_binding_header,offline_readiness,offline_binding_lifecycle,offline_attempt_pointer;
INSERT INTO offline_binding_header VALUES('{binding}','{deployment}','{incarnation}',
'b9afded4-5a03-4aa7-90f7-5a76ab29302a','3c58ebd5-f974-4d5e-b461-b5d61d487389',
'f6e4054f-a5ec-40e1-9f77-375f34d69993','fixture-1',decode('{digest}','hex'));
INSERT INTO offline_readiness VALUES('{deployment}','{incarnation}','NOT_READY',true,
'fixture-1',decode('{digest}','hex'),clock_timestamp()-interval '1 second');
INSERT INTO offline_binding_lifecycle VALUES('{binding}','REGISTERED',0);
INSERT INTO offline_attempt_pointer VALUES('{binding}',NULL,1,false,0);
"""
        snapshot = "SELECT row_to_json(t)::text FROM (SELECT * FROM offline_readiness) t; SELECT row_to_json(t)::text FROM (SELECT * FROM offline_binding_lifecycle) t; SELECT row_to_json(t)::text FROM (SELECT * FROM offline_attempt_pointer) t;"
        enabled = source.replace("v_complete_runner_authority_bound CONSTANT boolean := false;",
                                 "v_complete_runner_authority_bound CONSTANT boolean := true;")
        cases = {
            "default_hard_false": (source, "", "COMPLETE_RUNNER_AUTHORITY_ABSENT"),
            "header_missing": (enabled, "DELETE FROM offline_binding_header;", "HEADER_IDENTITY_MISMATCH"),
            "header_duplicate": (enabled, "INSERT INTO offline_binding_header SELECT * FROM offline_binding_header;", "HEADER_IDENTITY_MISMATCH"),
            "host_health_absent": (enabled, "UPDATE offline_readiness SET watchdog_healthy=false;", "INDEPENDENT_HOST_HEALTH_ABSENT"),
            "lifecycle_wrong": (enabled, "UPDATE offline_binding_lifecycle SET state='ACTIVE';", "LIFECYCLE_PRESTATE_MISMATCH"),
            "pointer_wrong": (enabled, "UPDATE offline_attempt_pointer SET generation=2;", "POINTER_PRESTATE_MISMATCH"),
            "host_health_stale": (enabled, "", "HOST_HEALTH_STALE_OR_CONFLICTING"),
            "host_health_future": (enabled, "UPDATE offline_readiness SET watchdog_checked_at=clock_timestamp()+interval '1 day';", "HOST_HEALTH_STALE_OR_CONFLICTING"),
            "host_health_infinite": (enabled, "UPDATE offline_readiness SET watchdog_checked_at='infinity';", "HOST_HEALTH_STALE_OR_CONFLICTING"),
            "host_policy_conflict": (enabled, "UPDATE offline_readiness SET policy_version='wrong';", "HOST_HEALTH_STALE_OR_CONFLICTING"),
        }
        for label, (body, mutation, expected) in cases.items():
            assert sql(seed + mutation).returncode == 0
            before = sql(snapshot).stdout
            executed = sql(body)
            assert executed.returncode != 0 and expected in executed.stderr, (label, executed.stderr)
            assert sql(snapshot).stdout == before, label
            result["cases"][label] = "PASS_REJECTED_WITH_ROLLBACK"
        # Resolve every embedded SQL against actual PG18.4 relations. This is not
        # an end-to-end positive activation test or timing-policy substitution.
        statements = re.findall(r"(?:SELECT count\(\*\).*?;|PERFORM 1.*?;|UPDATE public\..*?;)", source, re.S)
        assert len(statements) == 10, len(statements)
        for index, statement in enumerate(statements):
            statement = statement.replace("INTO STRICT v_count", "").replace("PERFORM 1", "SELECT 1")
            for variable, value in declarations.items():
                statement = re.sub(r"\b" + variable + r"\b", "'" + value + "'::uuid", statement)
            statement = re.sub(r"\bv_now\b", "pg_catalog.clock_timestamp()", statement)
            executed = sql(seed + "BEGIN; SET LOCAL ROLE flooow_offline_control_owner; SET LOCAL search_path=pg_catalog,pg_temp;" + statement + "ROLLBACK;")
            assert executed.returncode == 0, (index, executed.stderr)
        result["embedded_sql_resolved"] = len(statements)
        body = re.search(r"DO \$admin\$(.*?)\$admin\$", source, re.S).group(1)
        assert not re.search(r":(?:'|\")[A-Za-z_]+", body)
        assert not re.search(r"SET\s+(?:watchdog_checked_at|watchdog_healthy)\s*=", body, re.I)
        result["psql_variables_inside_do"] = 0
        result["health_writer"] = "NO_ADMIN_HEALTH_WRITES"
        result["positive_activation"] = "UNQUALIFIED_HOST_AND_TEMPORAL_GATES"
        result["canonical_runtime_access"] = "NONE"
    finally:
        if started:
            removed = run(["docker", "rm", "--force", "--volumes", name])
            assert removed.returncode == 0, removed.stderr
            result["disposable_container_removed"] = True
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
