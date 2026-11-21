"""Bind actual local HOST manager -> immutable image -> fixed preparation.

No new authority/key/service is created. Managed launch and immutable code are
provenance facts, not approval, source acceptance or canonical qualification.
"""
import hashlib
import argparse
import io
import json
import pathlib
import re
import queue
import subprocess
import struct
import tarfile
import time
import threading
import uuid

directory = pathlib.Path(__file__).resolve().parent
output = directory.parent
repository = directory.parents[4]
source = output / "prospective-controller-rebind-v13/execution-source"
headers = repository / "docs/evidence/package-0090-B01-v2-native-static-closure-r5n2a5-3c5v/source-acquisition-v1/upstream/src"
base_image = "sha256:07fc165de5bb569d822460e2df645c5489f99220fc2cb16c86596d39db394561"
context = "desktop-linux"
label = "mvp-autonomous-completion-v1"
options = argparse.ArgumentParser()
options.add_argument("--review-complete-path")
arguments = options.parse_args()
nonce = uuid.uuid4().hex[:12]
build_name = "flooow-mvp-image-" + nonce
run_name = "flooow-mvp-managed-" + nonce
docker = ["docker", "--context", context]
executions = []
sha = lambda value: hashlib.sha256(value).hexdigest()

def call(args, *, data=None, timeout=30, required=True):
    command = docker + args
    result = subprocess.run(command, input=data, capture_output=True, timeout=timeout)
    row = {"command": command, "exit_code": result.returncode,
           "stdout": result.stdout.decode("utf-8", "replace"),
           "stderr": result.stderr.decode("utf-8", "replace")}
    if data is not None:
        row["stdin_bytes"] = len(data)
        row["stdin_sha256"] = sha(data)
    executions.append(row)
    (directory / "executions.json").write_text(json.dumps(executions, indent=2) + "\n", encoding="utf-8")
    if required and result.returncode:
        raise RuntimeError(json.dumps(row))
    return row

def inspect(identifier):
    return json.loads(call(["inspect", identifier])["stdout"])[0]

def manager():
    host = call(["context", "inspect", "--format", "{{json .Endpoints.docker.Host}}", context])["stdout"].strip()
    actual = json.loads(call(["info", "--format", "{{json .ID}}"]) ["stdout"])
    assert json.loads(host) == "npipe:////./pipe/dockerDesktopLinuxEngine"
    return {"context": context, "endpoint": json.loads(host), "daemon_id": actual}

files = {}
for name in ("immutable_export.c", "self_session_custody_probe.c", "bootstrap_expectation.c", "bootstrap_expectation.h", "policy_candidate_custody.c", "policy_candidate_custody.h", "policy_projection_tests.c", "run_self_session_probe.sh", "private_credential.c", "private_credential.h"):
    files["probe/" + name] = (source / name).read_bytes()
files["probe/managed-entrypoint.sh"] = (directory / "entrypoint.sh").read_bytes()
proposal_bytes = (output / "prospective-observation-policy-candidate-v1/policy-proposal.json").read_bytes()
proposal = json.loads(proposal_bytes)
assert proposal["classification"] == "PROSPECTIVE_PROVISIONING_DATA_PROPOSAL_NOT_APPROVED_NOT_ACCEPTED_NOT_ACTIVE"
values = proposal["proposed_values"]
assert all(type(values[key]) is int and 0 < values[key] < 2**64 for key in values)
version_literal = json.dumps(proposal["proposed_policy_version"], ensure_ascii=True)
assert len(proposal["proposed_policy_version"].encode("ascii")) < 64
generated_header = ("#include <stdint.h>\n" +
    f"#define S03_PROPOSED_MAX_AGE_US UINT64_C({values['original_source_max_age_us']})\n" +
    f"#define S03_PROPOSED_LEASE_US UINT64_C({values['challenge_lease_us']})\n" +
    f"#define S03_PROPOSED_MAX_ROWS UINT64_C({values['max_rows']})\n" +
    f"#define S03_PROPOSED_MAX_BYTES UINT64_C({values['max_private_frame_bytes']})\n" +
    f"#define S03_PROPOSED_POLICY_VERSION {version_literal}\n" +
    f'#define S03_POLICY_PROPOSAL_SHA256 "{sha(proposal_bytes)}"\n' +
    f'#define S03_MVP_PARENT_RECEIPT_SHA256 "{sha((output / "authority-receipt.json").read_bytes())}"\n').encode()
files["probe/policy_proposal_values.h"] = generated_header
files["probe/policy-proposal.json"] = proposal_bytes
for name in ("interfaces/libpq/libpq-fe.h", "include/postgres_ext.h"):
    files["pgheaders/" + name] = (headers / name).read_bytes()
manifest = {name: sha(data) for name, data in sorted(files.items())}
files["probe/input-manifest.json"] = (json.dumps(manifest, sort_keys=True, indent=2) + "\n").encode()
def pack(values):
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w", format=tarfile.USTAR_FORMAT) as archive:
        parents = set()
        for name in values:
            parents.update(str(path) for path in pathlib.PurePosixPath(name).parents if str(path) != ".")
        for name in sorted(parents, key=lambda value: (value.count("/"), value)):
            entry = tarfile.TarInfo(name)
            entry.type = tarfile.DIRTYPE
            entry.mode = 0o555
            archive.addfile(entry)
        for name, data in sorted(values.items()):
            entry = tarfile.TarInfo(name)
            entry.mode = 0o555 if name == "probe/self-session-probe" else 0o444
            entry.size = len(data)
            archive.addfile(entry, io.BytesIO(data))
    return buffer.getvalue()
bundle = pack(files)
(directory / "source-bundle.tar").write_bytes(bundle)
receipt = {
    "PARENT_AUTHORITY": "FLOOOW_MVP_AUTONOMOUS_COMPLETION_AUTHORITY_V1",
    "CHILD_AUTHORITY_ID": "PACKAGE_0090_EXISTING_HOST_BOUND_PARAMETER_APPROVAL_AND_LIVE_REVIEW_V1",
    "PURPOSE": "Existing HOST custodian makes explicit positive parameter disposition for one actual bound test context, pending independent authority/qualification/sourceacceptance; provide readonly live review before Reader, never activate",
    "SCOPE": "Never-started image assembly, one disposable offline compiler container writing only a new build-output directory, one NEW readonly raw preparation container; no policy/source acceptance",
    "INPUTS": {"base_image": base_image, "source_manifest": manifest, "source_bundle_sha256": sha(bundle), "docker_context": context, "controller_source_sha256": sha(pathlib.Path(__file__).read_bytes()), "unaccepted_proposal_sha256": sha(proposal_bytes)},
    "PERMITTED_EFFECTS": ["local Docker metadata reads", "create stopped image-assembly container", "copy selected source tar to its own writable layer without executing", "commit local immutable source/runtime images", "offline gcc compilation in own readonly container with only new build-output bind", "create/start one isolated readonly preparation container without host binds", "inspect own launch/PID1 and real publisher/custodian birth/executable/namespace before fixed preparation commands", "external HOST explicitly requests bound parameter approval referencing current parent grant, exact proposal, actual manager/image/container/custodian birth/ns and exact4values", "separate zero-cap UID10003 checks ownbirth/ns/grant/proposal/exactvalues then issues positiveparameterapprovalCLAIM in sealedreadonlyrecord pending independent qualification/sourceacceptance; no operationalactivation", "verify actual sender SCM_CREDENTIALS and retainedpidfd plus exactrequest before consuming record as not-source-accepted data", "bounded livehandoff of exactnonsecretreadonlypolicyFD for independentHOSTreview, never SourceAccepted fromcapturecompletion", "raw bootstrap/public4/pidfd tests", "remove only label/ID-verified owned containers and their own anonymous volumes"],
    "PROHIBITED_EFFECTS": ["pull/push/network outside existing local Docker endpoint", "host Docker socket/namespace/mount exposure to candidate", "production/original/shared DB", "S03 registration/semantic entrypoints", "V043", "B02", "creator selfqualification/sourceacceptance or operationalpolicyactivation", "security-policy changes", "native participant/authority/key invention"],
    "PRECONDITIONS": "Actual local manager revalidated; source imageID exact; no host-code bind mounts in runtime; runtime rootfs readonly, networknone, private namespaces; only bootstrap SETUID/SETGID then roles drop to zero caps",
    "EXIT_CONDITIONS": "Record exact manager/image/launch/PID/namespace/control-origin chain and raw preparation outputs; cleanup owned containers; retain labeled immutable image as qualification candidate only",
    "EXPIRY_OR_TERMINATION": "Bounded command timeouts, max150second review wait (HOSTtestcontrol only, notsourceTTL), managerstdinEOF, owncompletion or driverfailurecleanup",
    "PARENT_BOUNDARY_HASH_OR_REFERENCE": {"path": "../authority-receipt.json", "sha256": sha((output / "authority-receipt.json").read_bytes())},
}
(directory / "authority-receipt.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
builder = runtime = image = process = None
try:
    before = manager()
    base = json.loads(call(["image", "inspect", base_image])["stdout"])[0]
    assert base["Id"] == base_image and base["Os"] == "linux" and base["Architecture"] == "amd64"
    builder = call(["create", "--pull", "never", "--name", build_name, "--label", "flooow.authority=" + label,
                    "--network", "none", "--cap-drop", "ALL", "--entrypoint", "/bin/true", base_image])["stdout"].strip()
    created = inspect(builder)
    assert not created["State"]["Running"] and created["Image"] == base_image
    call(["cp", "-", builder + ":/"], data=bundle)
    committed = call(["commit", "--no-pause", "--change", "ENTRYPOINT [\"/bin/sh\",\"/probe/managed-entrypoint.sh\"]",
                  "--change", "CMD []", "--change", "LABEL flooow.authority=" + label,
                  "--change", "LABEL flooow.scope=RAW_PREPARATION_NOT_ACCEPTED",
                  "--change", "LABEL flooow.input_manifest_sha256=" + sha(files["probe/input-manifest.json"]),
                  builder, "flooow-mvp-managed-preparation:" + nonce], timeout=60)["stdout"]
    identifiers = [line.strip() for line in committed.splitlines() if re.fullmatch(r"sha256:[0-9a-f]{64}", line.strip())]
    assert len(identifiers) == 1
    source_image = identifiers[0]
    build_output = directory / ("build-output-" + nonce)
    build_output.mkdir(exist_ok=False)
    compile_command = "gcc -std=c11 -O2 -Wall -Wextra -Werror -DS03_MANAGED_BIRTH_GATE=1 -I/pgheaders/interfaces/libpq -I/pgheaders/include /probe/self_session_custody_probe.c /probe/bootstrap_expectation.c /probe/policy_candidate_custody.c /probe/immutable_export.c /probe/private_credential.c -l:libpq.so.5 -lcrypto -o /build-out/self-session-probe"
    call(["run", "--rm", "--pull", "never", "--label", "flooow.authority=" + label, "--network", "none", "--read-only", "--user", "0:0", "--cap-drop", "ALL", "--security-opt", "no-new-privileges", "--tmpfs", "/tmp:rw,noexec,size=64m", "--mount", f"type=bind,source={build_output},target=/build-out", "--entrypoint", "/bin/sh", source_image, "-c", compile_command], timeout=60)
    guard_compile = "gcc -std=c11 -O2 -Wall -Wextra -Werror -I/pgheaders/interfaces/libpq -I/pgheaders/include /probe/policy_projection_tests.c /probe/bootstrap_expectation.c /probe/immutable_export.c -l:libpq.so.5 -lcrypto -o /tmp/policy-guard && /tmp/policy-guard"
    guard_result = call(["run", "--rm", "--pull", "never", "--label", "flooow.authority=" + label, "--network", "none", "--read-only", "--user", "65534:65534", "--cap-drop", "ALL", "--security-opt", "no-new-privileges", "--tmpfs", "/tmp:rw,exec,size=64m", "--entrypoint", "/bin/sh", source_image, "-c", guard_compile], timeout=60)
    elf = (build_output / "self-session-probe").read_bytes()
    assert elf.startswith(b"\x7fELF")
    runtime_script = files["probe/run_self_session_probe.sh"].decode("utf-8")
    runtime_script = "\n".join(line for line in runtime_script.splitlines() if not line.startswith("gcc ") and line != "chmod 0555 /tmp/self-session-probe") + "\n"
    runtime_script = runtime_script.replace("/tmp/self-session-probe", "/probe/self-session-probe")
    files["probe/run_self_session_probe.sh"] = runtime_script.encode()
    files["probe/self-session-probe"] = elf
    final_manifest = {name: sha(data) for name, data in sorted(files.items()) if name != "probe/input-manifest.json"}
    files["probe/input-manifest.json"] = (json.dumps(final_manifest, sort_keys=True, indent=2) + "\n").encode()
    final_bundle = pack(files)
    (directory / "runtime-bundle.tar").write_bytes(final_bundle)
    call(["cp", "-", builder + ":/"], data=final_bundle)
    final_commit = call(["commit", "--no-pause", "--change", "ENTRYPOINT [\"/bin/sh\",\"/probe/managed-entrypoint.sh\"]", "--change", "CMD []", "--change", "LABEL flooow.authority=" + label, "--change", "LABEL flooow.scope=RAW_PREPARATION_NOT_ACCEPTED", "--change", "LABEL flooow.input_manifest_sha256=" + sha(files["probe/input-manifest.json"]), builder, "flooow-mvp-managed-preparation:" + nonce + "-runtime"], timeout=60)["stdout"]
    identifiers = [line.strip() for line in final_commit.splitlines() if re.fullmatch(r"sha256:[0-9a-f]{64}", line.strip())]
    assert len(identifiers) == 1
    image = identifiers[0]
    immutable_image = json.loads(call(["image", "inspect", image])["stdout"])[0]
    assert immutable_image["Id"] == image
    create_args = ["create", "--pull", "never", "--name", run_name, "--label", "flooow.authority=" + label,
                   "--network", "none", "--read-only", "--user", "0:0", "--cap-drop", "ALL", "--cap-add", "SETUID", "--cap-add", "SETGID",
                   "--security-opt", "no-new-privileges", "--tmpfs", "/tmp:rw,exec,size=256m,mode=1777", "-i", image]
    runtime = call(create_args)["stdout"].strip()
    launch = inspect(runtime)
    assert launch["Image"] == image and launch["HostConfig"]["ReadonlyRootfs"] and launch["HostConfig"]["NetworkMode"] == "none"
    assert all(mount["Type"] != "bind" for mount in launch["Mounts"])
    assert launch["HostConfig"].get("PidMode", "") not in ("host", "container")
    process = subprocess.Popen(docker + ["start", "--attach", "--interactive", runtime], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout_lines, stderr_parts, line_queue = [], [], queue.Queue()
    def read_stdout():
        for line in iter(process.stdout.readline, b""):
            stdout_lines.append(line)
            line_queue.put(line)
        line_queue.put(None)
    def read_stderr():
        stderr_parts.append(process.stderr.read())
    stdout_thread = threading.Thread(target=read_stdout, daemon=True)
    stderr_thread = threading.Thread(target=read_stderr, daemon=True)
    stdout_thread.start(); stderr_thread.start()
    ready_bytes = line_queue.get(timeout=30)
    assert ready_bytes is not None
    ready = ready_bytes.decode("utf-8", "strict")
    assert ready == "MANAGED_PREPARATION_READY\n", ready
    live = inspect(runtime)
    assert live["State"]["Running"] and live["State"]["Pid"] > 0
    bootstrap = call(["exec", "--user", "0:0", runtime, "/bin/sh", "-c", "readlink /proc/1/ns/pid; readlink /proc/1/ns/time; cat /proc/1/stat"])
    assert manager() == before
    process.stdin.write(b"START_BOUND_RAW_PREPARATION\n");process.stdin.flush()
    deadline = time.monotonic() + 60
    while True:
        line = line_queue.get(timeout=max(0.01, deadline - time.monotonic()))
        assert line is not None, "Publisher exited before managed birth gate"
        match = re.fullmatch(rb"HOST_MANAGED_PUBLISHER_BIRTH_READY PID=([1-9][0-9]*)\n", line)
        if match:
            publisher_pid = int(match.group(1));assert publisher_pid <= 2147483647
            break
        assert time.monotonic() < deadline
    publisher = call(["exec", "--user", "0:0", runtime, "/bin/sh", "-c", f"readlink /proc/{publisher_pid}/exe; sha256sum /proc/{publisher_pid}/exe; cat /proc/{publisher_pid}/stat; cat /proc/{publisher_pid}/status; readlink /proc/{publisher_pid}/ns/pid; readlink /proc/{publisher_pid}/ns/time"])
    publisher_lines = publisher["stdout"].splitlines()
    assert publisher_lines[0] == "/probe/self-session-probe" and publisher_lines[1].split()[0] == sha(elf)
    external_process_membership = call(["top", runtime, "-eo", "pid,ppid,lstart,user,comm"])
    assert manager() == before
    process.stdin.write(b"AUTHORIZE_BOUND_RAW_BOOTSTRAP\n");process.stdin.flush()
    deadline = time.monotonic() + 60
    while True:
        line = line_queue.get(timeout=max(0.01, deadline - time.monotonic()))
        assert line is not None, "Custodian exited before managed birth gate"
        match = re.fullmatch(rb"HOST_POLICY_CANDIDATE_CUSTODIAN_BIRTH_READY PID=([1-9][0-9]*) UID=10003\n", line)
        if match:
            custodian_pid = int(match.group(1));assert custodian_pid <= 2147483647
            break
        assert time.monotonic() < deadline
    custodian = call(["exec", "--user", "10003:10003", runtime, "/bin/sh", "-c", f"readlink /proc/{custodian_pid}/exe; sha256sum /proc/{custodian_pid}/exe; cat /proc/{custodian_pid}/stat; cat /proc/{custodian_pid}/status; readlink /proc/{custodian_pid}/ns/pid; readlink /proc/{custodian_pid}/ns/time"])
    custodian_lines = custodian["stdout"].splitlines()
    assert custodian_lines[0] == "/probe/self-session-probe" and custodian_lines[1].split()[0] == sha(elf)
    custodian_membership = call(["top", runtime, "-eo", "pid,ppid,lstart,user,comm"])
    assert manager() == before
    stat_line = custodian_lines[2]
    assert int(stat_line.split(" ", 1)[0]) == custodian_pid
    start_ticks = int(stat_line.rsplit(")", 1)[1].split()[19])
    pid_namespace = int(re.fullmatch(r"pid:\[([0-9]+)\]", custodian_lines[-2]).group(1))
    time_namespace = int(re.fullmatch(r"time:\[([0-9]+)\]", custodian_lines[-1]).group(1))
    parent_reference = sha((output / "authority-receipt.json").read_bytes())
    request = struct.pack(">32s32s16s32s32sIQQQIQQQQ", bytes.fromhex(parent_reference), bytes.fromhex(sha(proposal_bytes)),
                          uuid.UUID(before["daemon_id"]).bytes, bytes.fromhex(image.removeprefix("sha256:")),
                          bytes.fromhex(runtime), custodian_pid, start_ticks, pid_namespace, time_namespace,
                          1, values["original_source_max_age_us"], values["challenge_lease_us"], values["max_rows"], values["max_private_frame_bytes"])
    assert len(request) == 208
    decision_control = b"APPROVE_BOUND_POLICY_VALUES_PENDING_SOURCE_ACCEPTANCE " + request.hex().encode("ascii") + b"\n"
    decision_request = {"scope":"Private existing HOST preparation control, not native observer ABI or source acceptance",
                        "action":"APPROVE_BOUND_POLICY_VALUES_PENDING_SOURCE_ACCEPTANCE", "positive_disposition_code":1, "exact_parameter_values":values, "parent_delegation_reference_sha256":parent_reference,
                        "proposal_sha256":sha(proposal_bytes), "manager":before, "image":image,"container":runtime,
                        "custodian_pid":custodian_pid,"custodian_start_ticks":start_ticks,"pid_namespace_inode":pid_namespace,
                        "time_namespace_inode":time_namespace,"request_hex":request.hex(),"control_bytes_sha256":sha(decision_control),
                        "qualification":"NOT_ESTABLISHED","acceptance":"NOT_ESTABLISHED","activation":"NOT_ESTABLISHED"}
    (directory / "explicit-scoped-decision-request.json").write_text(json.dumps(decision_request,indent=2)+"\n",encoding="utf-8")
    process.stdin.write(decision_control);process.stdin.flush()
    deadline = time.monotonic() + 60
    issued_record = None
    while True:
        line = line_queue.get(timeout=max(0.01, deadline - time.monotonic()))
        assert line is not None, "Custodian exited before live input review handoff"
        if line.startswith(b'{"kind":"POLICY_ISSUER_PARAMETER_APPROVAL_CLAIM_NOT_ACCEPTED"'):
            issued_record = json.loads(line)
        match = re.fullmatch(rb"HOST_POLICY_INPUT_REVIEW_READY PID=([1-9][0-9]*) FD=([0-9]+) SIZE=([1-9][0-9]*)\n", line)
        if match:
            assert issued_record is not None and int(match.group(1)) == custodian_pid
            assert int(match.group(2)) == issued_record["record_fd"] and int(match.group(3)) == issued_record["private_record_size"]
            break
        assert time.monotonic() < deadline
    live_handoff = {"classification":"LIVE_READONLY_REVIEW_NOT_SOURCE_ACCEPTANCE_OR_ACTIVATION", "context":context,
                    "daemon_id":before["daemon_id"],"container":runtime,"expected_image":image,"label":label,
                    "pid":custodian_pid,"fd":issued_record["record_fd"],"start_ticks":start_ticks,
                    "device":issued_record["device"],"inode":issued_record["inode"],"size":issued_record["private_record_size"],
                    "sha256":issued_record["private_record_sha256"],"expected_owner_uid":10003,
                    "decision_request":decision_request,"issuer_record":issued_record,
                    "completion_signal_is_only_test_synchronization_not_acceptance":True,"review_completion_path":arguments.review_complete_path}
    (directory / "live-handoff.json").write_text(json.dumps(live_handoff,indent=2)+"\n",encoding="utf-8")
    if arguments.review_complete_path:
        completion = pathlib.Path(arguments.review_complete_path)
        end_wait = time.monotonic()+150
        while not completion.exists():
            assert process.poll() is None and time.monotonic()<end_wait,"Independent capture not completed within bounded HOSTtestwait"
            time.sleep(0.25)
    assert manager() == before
    process.stdin.write(b"CONTINUE_WITHOUT_POLICY_ACCEPTANCE\n");process.stdin.flush();process.stdin.close()
    process.wait(timeout=90)
    stdout_thread.join(timeout=10);stderr_thread.join(timeout=10)
    assert not stdout_thread.is_alive() and not stderr_thread.is_alive()
    stdout, stderr = b"".join(stdout_lines).decode("utf-8", "replace"), b"".join(stderr_parts).decode("utf-8", "replace")
    result = {"classification": "MANAGER_TO_IMMUTABLE_IMAGE_LAUNCH_BOOTSTRAP_CHANNEL_OBSERVED_NOT_POLICY_ISSUER_TRUST_OR_SOURCE_ACCEPTANCE",
              "manager_before": before, "manager_after": manager(), "base_image": base_image,
              "immutable_image_id": image, "immutable_image_metadata": immutable_image,
              "compiler_source_image_id": source_image, "compiled_publisher_sha256": sha(elf), "runtime_file_manifest": final_manifest,
              "synthetic_policy_projection_guard_execution": guard_result,
              "runtime_container_id": runtime, "launch_inspect_before_start": launch,
              "launch_inspect_running": live, "bootstrap_pid1_namespace_birth": bootstrap,
              "actual_publisher_pid_in_managed_namespace": publisher_pid, "actual_publisher_birth_executable_namespace": publisher,
              "external_manager_process_membership": external_process_membership,
              "actual_policy_proposal_custodian_pid": custodian_pid, "actual_policy_proposal_custodian_birth_executable_namespace": custodian,
              "custodian_external_manager_membership": custodian_membership,
              "private_control": {"ready": ready.strip(), "sent": ["START_BOUND_RAW_PREPARATION", "AUTHORIZE_BOUND_RAW_BOOTSTRAP", "APPROVE_BOUND_POLICY_VALUES_PENDING_SOURCE_ACCEPTANCE", "CONTINUE_WITHOUT_POLICY_ACCEPTANCE"], "explicit_decision_request":decision_request, "live_review_handoff":live_handoff, "via": "existing HOST control; issuerpositiveparameterclaim is not independentlyqualified approval/sourceacceptance/activation or observer ABI"},
              "exit_code": process.returncode, "stdout": stdout, "stderr": stderr,
              "policy_approval": "NOT_ESTABLISHED", "source_acceptance": "NOT_ESTABLISHED"}
    (directory / "managed-execution.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    assert result["manager_after"] == before and process.returncode == 0
    assert "PASS SELF_SESSION_PGSTAT_CUSTODY_PROBE" in stdout
    print(json.dumps({"image": image, "container": runtime, "manager_stable": True, "exit_code": process.returncode, "policy_approval": "NOT_ESTABLISHED"}))
finally:
    if process and process.poll() is None:
        process.kill()
        process.wait(timeout=10)
    for identifier, name, expected_image in ((runtime, run_name, image), (builder, build_name, base_image)):
        if not identifier:
            continue
        actual = inspect(identifier)
        assert actual["Id"] == identifier and actual["Name"] == "/" + name
        assert actual["Image"] == expected_image and actual["Config"]["Labels"]["flooow.authority"] == label
        call(["rm", "--force", "--volumes", identifier])
