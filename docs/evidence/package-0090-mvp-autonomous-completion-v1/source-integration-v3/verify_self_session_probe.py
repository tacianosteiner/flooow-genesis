"""Real disposable PG engineering experiment, never S02/S03 acceptance."""
import hashlib
import json
import pathlib
import subprocess

directory = pathlib.Path(__file__).resolve().parent
repository = directory.parents[3]
headers = repository / "docs/evidence/package-0090-B01-v2-native-static-closure-r5n2a5-3c5v/source-acquisition-v1/upstream/src"
image = "sha256:07fc165de5bb569d822460e2df645c5489f99220fc2cb16c86596d39db394561"
names = ("self_session_custody_probe.c", "immutable_export.c", "run_self_session_probe.sh")
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
(directory / "self-session-probe-authority.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
command = ["docker", "run", "--rm", "--pull", "never", "--network", "none",
           "--read-only", "--user", "0:0", "--cap-drop", "ALL", "--cap-add", "SETUID", "--cap-add", "SETGID",
           "--security-opt", "no-new-privileges", "--tmpfs", "/tmp:rw,exec,size=256m,mode=1777",
           "--mount", f"type=bind,source={directory},target=/probe,readonly",
           "--mount", f"type=bind,source={headers},target=/pgheaders,readonly",
           "--entrypoint", "/bin/sh", image, "/probe/run_self_session_probe.sh"]
execution = subprocess.run(command, capture_output=True, encoding="utf-8", errors="replace", timeout=90)
observations = [json.loads(line) for line in execution.stdout.splitlines() if line.startswith('{"kind":')]
raw = [row for row in observations if row["kind"].startswith("RAW_PUBLIC4_")]
anchors = [row for row in observations if row["kind"].startswith("KERNEL_PIDFD_")]
checks = {"three_public_observations": len(raw) == 3, "five_kernel_observations": len(anchors) == 5}
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
