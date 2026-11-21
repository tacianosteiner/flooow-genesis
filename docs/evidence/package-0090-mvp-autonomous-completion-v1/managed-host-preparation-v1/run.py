"""Bind actual local HOST manager -> immutable image -> fixed preparation.

No new authority/key/service is created. Managed launch and immutable code are
provenance facts, not approval, source acceptance or canonical qualification.
"""
import hashlib
import io
import json
import pathlib
import re
import subprocess
import tarfile
import time
import uuid

directory = pathlib.Path(__file__).resolve().parent
output = directory.parent
repository = directory.parents[3]
source = output / "source-integration-v5"
headers = repository / "docs/evidence/package-0090-B01-v2-native-static-closure-r5n2a5-3c5v/source-acquisition-v1/upstream/src"
base_image = "sha256:07fc165de5bb569d822460e2df645c5489f99220fc2cb16c86596d39db394561"
context = "desktop-linux"
label = "mvp-autonomous-completion-v1"
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
for name in ("immutable_export.c", "self_session_custody_probe.c", "bootstrap_expectation.c", "bootstrap_expectation.h", "run_self_session_probe.sh"):
    files["probe/" + name] = (source / name).read_bytes()
files["probe/managed-entrypoint.sh"] = (directory / "entrypoint.sh").read_bytes()
for name in ("interfaces/libpq/libpq-fe.h", "include/postgres_ext.h"):
    files["pgheaders/" + name] = (headers / name).read_bytes()
manifest = {name: sha(data) for name, data in sorted(files.items())}
files["probe/input-manifest.json"] = (json.dumps(manifest, sort_keys=True, indent=2) + "\n").encode()
buffer = io.BytesIO()
with tarfile.open(fileobj=buffer, mode="w", format=tarfile.USTAR_FORMAT) as archive:
    parents = set()
    for name in files:
        parents.update(str(path) for path in pathlib.PurePosixPath(name).parents if str(path) != ".")
    for name in sorted(parents, key=lambda value: (value.count("/"), value)):
        entry = tarfile.TarInfo(name)
        entry.type = tarfile.DIRTYPE
        entry.mode = 0o555
        archive.addfile(entry)
    for name, data in sorted(files.items()):
        entry = tarfile.TarInfo(name)
        entry.mode = 0o444
        entry.size = len(data)
        archive.addfile(entry, io.BytesIO(data))
bundle = buffer.getvalue()
(directory / "source-bundle.tar").write_bytes(bundle)
receipt = {
    "PARENT_AUTHORITY": "FLOOOW_MVP_AUTONOMOUS_COMPLETION_AUTHORITY_V1",
    "CHILD_AUTHORITY_ID": "PACKAGE_0090_EXISTING_HOST_MANAGED_IMMUTABLE_PREPARATION_V1",
    "PURPOSE": "Bind existing external local manager to exact immutable preparation image, launch, bootstrap birth and private control channel",
    "SCOPE": "One never-started image assembly container plus one NEW disposable raw preparation container; pinned local image; no policy/source acceptance",
    "INPUTS": {"base_image": base_image, "source_manifest": manifest, "source_bundle_sha256": sha(bundle), "docker_context": context, "controller_source_sha256": sha(pathlib.Path(__file__).read_bytes())},
    "PERMITTED_EFFECTS": ["local Docker metadata reads", "create stopped image-assembly container", "copy selected source tar to its own writable layer without executing", "commit local immutable image", "create/start one isolated readonly preparation container", "inspect own launch/birth/namespace and send one fixed private preparation stdin command", "raw bootstrap/public4/pidfd tests", "remove only label/ID-verified owned containers and their own anonymous volumes"],
    "PROHIBITED_EFFECTS": ["pull/push/network outside existing local Docker endpoint", "host Docker socket/namespace/mount exposure to candidate", "production/original/shared DB", "S03 registration/semantic entrypoints", "V043", "B02", "source/policy approval", "security-policy changes", "native participant/authority/key invention"],
    "PRECONDITIONS": "Actual local manager revalidated; source imageID exact; no host-code bind mounts in runtime; runtime rootfs readonly, networknone, private namespaces; only bootstrap SETUID/SETGID then roles drop to zero caps",
    "EXIT_CONDITIONS": "Record exact manager/image/launch/PID/namespace/control-origin chain and raw preparation outputs; cleanup owned containers; retain labeled immutable image as qualification candidate only",
    "EXPIRY_OR_TERMINATION": "Bounded command timeouts, manager stdin EOF, own completion or driver failure cleanup",
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
    ready = process.stdout.readline().decode("utf-8", "strict")
    assert ready == "MANAGED_PREPARATION_READY\n", ready
    live = inspect(runtime)
    assert live["State"]["Running"] and live["State"]["Pid"] > 0
    bootstrap = call(["exec", "--user", "0:0", runtime, "/bin/sh", "-c", "readlink /proc/1/ns/pid; readlink /proc/1/ns/time; cat /proc/1/stat"])
    assert manager() == before
    # Exact LF bytes: Windows text-mode stdin would translate to CRLF and is
    # correctly rejected by the fixed POSIX bootstrap command comparison.
    stdout_bytes, stderr_bytes = process.communicate(b"START_BOUND_RAW_PREPARATION\n", timeout=90)
    stdout, stderr = stdout_bytes.decode("utf-8", "replace"), stderr_bytes.decode("utf-8", "replace")
    result = {"classification": "MANAGER_TO_IMMUTABLE_IMAGE_LAUNCH_BOOTSTRAP_CHANNEL_OBSERVED_NOT_POLICY_ISSUER_TRUST_OR_SOURCE_ACCEPTANCE",
              "manager_before": before, "manager_after": manager(), "base_image": base_image,
              "immutable_image_id": image, "immutable_image_metadata": immutable_image,
              "runtime_container_id": runtime, "launch_inspect_before_start": launch,
              "launch_inspect_running": live, "bootstrap_pid1_namespace_birth": bootstrap,
              "private_control": {"ready": ready.strip(), "sent": "START_BOUND_RAW_PREPARATION", "via": "existing HOST Docker attach stdin; not an observer/native ABI"},
              "exit_code": process.returncode, "stdout": ready + stdout, "stderr": stderr,
              "policy_approval": "NOT_ESTABLISHED", "source_acceptance": "NOT_ESTABLISHED"}
    (directory / "managed-execution.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    assert result["manager_after"] == before and process.returncode == 0
    assert "PASS SELF_SESSION_PGSTAT_CUSTODY_PROBE" in stdout
    print(json.dumps({"image": image, "container": runtime, "manager_stable": True, "exit_code": process.returncode, "policy_approval": "NOT_ESTABLISHED"}))
finally:
    if process and process.poll() is None:
        process.kill()
        process.communicate(timeout=10)
    for identifier, name, expected_image in ((runtime, run_name, image), (builder, build_name, base_image)):
        if not identifier:
            continue
        actual = inspect(identifier)
        assert actual["Id"] == identifier and actual["Name"] == "/" + name
        assert actual["Image"] == expected_image and actual["Config"]["Labels"]["flooow.authority"] == label
        call(["rm", "--force", "--volumes", identifier])
