"""Real disposable PG engineering experiment, never S02/S03 acceptance."""
import hashlib
import json
import pathlib
import subprocess
import uuid

directory = pathlib.Path(__file__).resolve().parent
repository = directory.parents[3]
headers = repository / "docs/evidence/package-0090-B01-v2-native-static-closure-r5n2a5-3c5v/source-acquisition-v1/upstream/src"
image = "sha256:07fc165de5bb569d822460e2df645c5489f99220fc2cb16c86596d39db394561"
names = ("self_session_custody_probe.c", "immutable_export.c", "bootstrap_expectation.c", "bootstrap_expectation.h", "run_self_session_probe.sh", "verify_self_session_probe.py")
receipt = {
    "parent": "FLOOOW_MVP_AUTONOMOUS_COMPLETION_AUTHORITY_V1",
    "parent_sha256": hashlib.sha256((directory.parent / "authority-receipt.json").read_bytes()).hexdigest(),
    "gate": "SELF_SESSION_PGSTAT_CUSTODY_PROBE",
    "purpose": "Prepare bounded real Reader/session export and two separately confined kernel pidfd liveness observations; no source acceptance",
    "inputs": {name: hashlib.sha256((directory / name).read_bytes()).hexdigest() for name in names},
    "existing_header_hashes": {name: hashlib.sha256((headers / name).read_bytes()).hexdigest() for name in ("interfaces/libpq/libpq-fe.h", "include/postgres_ext.h")},
    "scope": "NEW initdb in disposable tmpfs; private Unix socket; no host ports; no network",
    "effects": ["compile in tmpfs", "initdb", "bootstrap one synthetic Reader role", "SCRAM local login", "fixed read-only public4 self-row", "sealed memfd publication", "two own pre-execed child readers", "owner opens pidfd for own libpq backend PID", "children poll retained pidfd only", "owner closes own SQL session then children observe process exit"],
    "preconditions": "Pinned local image; root bootstrap has only SETUID/SETGID to separate OS principals; owner10000 and children10001/10002 verify zero capabilities; PG999; readonly inputs; no host namespaces or external volume",
    "bootstrap_caps": ["SETUID", "SETGID"],
    "prohibited": ["V043", "B02", "migrations", "S03 registration/entrypoint", "original/shared/production DB", "source acceptance", "semantic authority"],
    "exit": "Record exact bounded observations; destroy own cluster/container",
    "termination": "Container exit or 90-second timeout",
}
# Exact child-receipt fields required by the current mandate. Prior versions'
# direct-mandate experiment receipts remain unchanged; no historical backfill.
receipt = {
    "PARENT_AUTHORITY": receipt["parent"],
    "CHILD_AUTHORITY_ID": "PACKAGE_0090_S03_IMMUTABLE_RAW_BOOTSTRAP_PREPARATION_V1",
    "PURPOSE": "Measure nonsecret HOST/DEPLOYMENT bootstrap facts in separate stockPG admin child, publish sealed readonly raw expectations before Reader/observers; retain unestablished approval/policy/generation",
    "SCOPE": receipt["scope"],
    "INPUTS": {"candidate_sources": receipt["inputs"], "existing_headers": receipt["existing_header_hashes"], "image": image},
    "PERMITTED_EFFECTS": receipt["effects"] + ["read fixed boot UUID and own time namespace inode", "bootstrap admin reads fixed nonsecret PG system/database/Reader/server-start fields before Reader program"],
    "PROHIBITED_EFFECTS": receipt["prohibited"],
    "PRECONDITIONS": receipt["preconditions"],
    "EXIT_CONDITIONS": receipt["exit"],
    "EXPIRY_OR_TERMINATION": receipt["termination"],
    "PARENT_BOUNDARY_HASH_OR_REFERENCE": {"path": "../authority-receipt.json", "sha256": receipt["parent_sha256"]},
}
(directory / "self-session-probe-authority.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
command = ["docker", "run", "--rm", "--pull", "never", "--network", "none",
           "--read-only", "--user", "0:0", "--cap-drop", "ALL", "--cap-add", "SETUID", "--cap-add", "SETGID",
           "--security-opt", "no-new-privileges", "--tmpfs", "/tmp:rw,exec,size=256m,mode=1777",
           "--mount", f"type=bind,source={directory},target=/probe,readonly",
           "--mount", f"type=bind,source={headers},target=/pgheaders,readonly",
           "--entrypoint", "/bin/sh", image, "/probe/run_self_session_probe.sh"]
execution = subprocess.run(command, capture_output=True, encoding="utf-8", errors="replace", timeout=90)
capture_index = 1
capture_path = directory / f"raw-execution-capture-{capture_index}.json"
while capture_path.exists():
    capture_index += 1
    capture_path = directory / f"raw-execution-capture-{capture_index}.json"
capture_path.write_text(json.dumps({"command": command, "exit_code": execution.returncode,
                                   "stdout": execution.stdout, "stderr": execution.stderr}, indent=2) + "\n", encoding="utf-8")
if execution.returncode:
    print(json.dumps({"raw_capture": str(capture_path), "exit_code": execution.returncode,
                      "stderr": execution.stderr}))
    raise SystemExit(execution.returncode)
observations = [json.loads(line) for line in execution.stdout.splitlines() if line.startswith('{"kind":')]
lines = execution.stdout.splitlines()
def single(prefix):
    values = [line[len(prefix):] for line in lines if line.startswith(prefix)]
    if len(values) != 1:
        raise ValueError("EXACT_BOOTSTRAP_MEASUREMENT_REQUIRED:" + prefix)
    return values[0]
bootstrap = {"boot_id": str(uuid.UUID(single("BOOTSTRAP_OS_BOOT_ID|"))),
             "time_namespace_inode": int(single("BOOTSTRAP_TIME_NAMESPACE_INODE|")),
             "PG": json.loads(single("BOOTSTRAP_PG|"))}
pg = bootstrap["PG"]
assert 0 < bootstrap["time_namespace_inode"] < 2**64
system_wire = bytes.fromhex(pg["database_system_identifier_wire_hex"])
system_sql_int64 = int(pg["database_system_identifier_sql_int64"])
assert len(system_wire) == 8 and -(2**63) <= system_sql_int64 < 2**63
assert system_sql_int64.to_bytes(8, "big", signed=True) == system_wire
# Existing source returns unsigned system_identifier bits through signed int64
# SQL datum; retain all eight observed bytes, never a zero/sign/PID inference.
pg["database_system_identifier_u64"] = str(int.from_bytes(system_wire, "big", signed=False))
assert 0 < int(pg["database_system_identifier_u64"]) < 2**64
assert all(0 < int(pg[field]) < 2**32 for field in ("database_oid", "reader_role_oid"))
assert -(2**63) < int(pg["server_start_pg_us"]) < 2**63 - 1
server_wire = bytes.fromhex(pg["server_start_pg_wire_hex"])
assert len(server_wire) == 8 and int.from_bytes(server_wire, "big", signed=True) == int(pg["server_start_pg_us"])
assert pg["reader_role_name"] == "flooow_reader"
assert pg["reader_flags"] == {"login": True, "superuser": False, "inherit": False, "create_role": False, "create_db": False, "replication": False, "bypass_rls": False}
assert pg["reader_memberships"] == 0 and pg["reader_sessions_before_candidate"] == 0
raw = [row for row in observations if row["kind"].startswith("RAW_PUBLIC4_")]
anchors = [row for row in observations if row["kind"].startswith("KERNEL_PIDFD_")]
expected_reads = [row for row in observations if row["kind"].startswith("RAW_BOOTSTRAP_EXPECTATION_")]
checks = {"three_public_observations": len(raw) == 3, "five_kernel_observations": len(anchors) == 5}
checks["three_immutable_expected_bootstrap_reads"] = len(expected_reads) == 3
if len(expected_reads) == 3:
    identity_fields = ("device", "inode", "original_started_us", "original_finished_us", "database_oid", "reader_oid", "system_identifier_u64", "server_start_pg_us")
    checks["same_expected_object_original_interval_and_full_measured_facts"] = len({tuple(row[field] for field in identity_fields) for row in expected_reads}) == 1
    checks["original_bootstrap_not_renewed_by_read"] = all(row["original_started_us"] <= row["original_finished_us"] <= row["start_boottime_us"] <= row["finish_boottime_us"] for row in expected_reads)
    checks["independent_bootstrap_raw_fact_crosscheck"] = all(row["database_oid"] == int(pg["database_oid"]) and row["reader_oid"] == int(pg["reader_role_oid"]) and row["system_identifier_u64"] == pg["database_system_identifier_u64"] and row["server_start_pg_us"] == pg["server_start_pg_us"] for row in expected_reads)
    frozen = [row for row in expected_reads if row["kind"] == "RAW_BOOTSTRAP_EXPECTATION_FROZEN_BEFORE_CANDIDATE"]
    checks["expected_frozen_before_candidate_acquisition"] = len(frozen) == 1 and all(frozen[0]["finish_boottime_us"] <= row["start_boottime_us"] for row in raw)
if len(raw) == 3:
    sources = [row for row in observations if row["kind"] == "RAW_PUBLIC4_SELF_SESSION_ACQUISITION"]
    readers = [row for row in observations if row["kind"] == "RAW_PUBLIC4_EXPORT_CHILD_PROBE"]
    checks.update({"one_source_two_readers": len(sources) == 1 and len(readers) == 2,
                   "distinct_processes": len({row["pid"] for row in raw}) == 3,
                   "exact_payloads": len({row["payload_hex"] for row in raw}) == 1,
                   "reconstructed_digests": all(hashlib.sha256(bytes.fromhex(row["payload_hex"])).hexdigest() == row["sha256"] for row in raw),
                   "ordered_intervals": all(row["start_boottime_us"] <= row["finish_boottime_us"] for row in observations)})
    if len(sources) == 1:
        checks["source_before_readers"] = all(sources[0]["finish_boottime_us"] <= row["start_boottime_us"] for row in readers)
        payload = bytes.fromhex(sources[0]["payload_hex"])
        assert payload[0] == 4
        offset, fields = 1, []
        for _ in range(4):
            size = payload[offset]; offset += 1
            fields.append(payload[offset:offset+size].decode("ascii")); offset += size
        assert offset == len(payload)
        checks["bootstrap_principal_database_match_actual_public_row"] = fields[0] == pg["database_oid"] and fields[1] == pg["reader_role_oid"] and fields[3] == pg["reader_role_name"]
        checks["bootstrap_measurements_before_candidate_output"] = max(i for i,line in enumerate(lines) if line.startswith("BOOTSTRAP_")) < min(i for i,line in enumerate(lines) if line.startswith('{"kind":'))
if len(anchors) == 5:
    live = [row for row in anchors if row["kind"] == "KERNEL_PIDFD_CHILD_OBSERVATION"]
    dead = [row for row in anchors if row["kind"] == "KERNEL_PIDFD_CHILD_POST_SESSION_CLOSE"]
    checks.update({"same_retained_kernel_object": len({(row["device"], row["inode"]) for row in anchors}) == 1,
                   "two_live_independent_kernel_observations": len(live) == 2 and len({row["pid"] for row in live}) == 2 and all(row["kernel_liveness"] == "LIVE_BEFORE_AND_AFTER" for row in live),
                   "two_stale_after_session_close": len(dead) == 2 and {row["pid"] for row in dead} == {row["pid"] for row in live} and all(row["kernel_liveness"] == "STALE_PROCESS_EXITED" for row in dead),
                   "exit_observations_after_live": all(before["finish_boottime_us"] <= after["start_boottime_us"] for before in live for after in dead)})
result = {"authority": receipt, "command": command, "exit_code": execution.returncode,
          "stdout": execution.stdout, "stderr": execution.stderr,
          "observations": observations, "reconstruction_checks": checks,
          "bootstrap_raw_measurements": bootstrap,
          "bootstrap_approval_policy_generation": "NOT_ESTABLISHED; raw measurements are not approval manifest, active policy, generation highwater, enrollment or source acceptance",
          "classification": "REAL_DISPOSABLE_ENGINEERING_PROBE_ONLY_NO_SOURCE_ACCEPTANCE"}
path = directory / "self-session-probe-execution.json"
if path.exists():
    index = 1
    while path.with_name(f"self-session-probe-execution-attempt-{index}.json").exists(): index += 1
    path = path.with_name(f"self-session-probe-execution-attempt-{index}.json")
path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"record": str(path), "exit_code": execution.returncode,
                  "stdout": execution.stdout, "stderr": execution.stderr}))
raise SystemExit(execution.returncode or (0 if all(checks.values()) else 1))
