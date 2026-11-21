"""Disposable offline kernel primitive proof; no source/owner acceptance."""
import hashlib
import json
import pathlib
import subprocess

directory = pathlib.Path(__file__).resolve().parent
parent = directory.parent / "authority-receipt.json"
image = "sha256:07fc165de5bb569d822460e2df645c5489f99220fc2cb16c86596d39db394561"
inputs = {name: hashlib.sha256((directory / name).read_bytes()).hexdigest()
          for name in ("immutable_export.c", "test_immutable_export.c")}
receipt = {
    "parent": "FLOOOW_MVP_AUTONOMOUS_COMPLETION_AUTHORITY_V1",
    "parent_receipt_sha256": hashlib.sha256(parent.read_bytes()).hexdigest(),
    "purpose": "Kernel-enforced immutable private export candidate",
    "scope": "Offline disposable own process/child; synthetic bytes only",
    "inputs": inputs,
    "effects": ["compile in disposable tmpfs", "memfd seals", "fork own child", "read own proc fd"],
    "prohibited": ["DB", "network", "V043", "B02", "source acceptance", "issuer creation"],
    "preconditions": "Pinned existing image; all input mounts read-only; no capabilities; no host process namespace",
    "exit": "Record test outcome; no owner, authentication or source acceptance claim",
    "termination": "Own disposable container exit",
}
(directory / "immutable-export-authority.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
command = ["docker", "run", "--rm", "--pull", "never", "--network", "none",
           "--read-only", "--user", "65534:65534", "--cap-drop", "ALL",
           "--security-opt", "no-new-privileges", "--tmpfs", "/tmp:rw,exec,size=64m",
           "--mount", f"type=bind,source={directory},target=/probe,readonly",
           "--entrypoint", "/bin/sh", image, "-c",
           "gcc -std=c11 -O2 -Wall -Wextra -Werror /probe/immutable_export.c /probe/test_immutable_export.c -o /tmp/test-export && /tmp/test-export"]
execution = subprocess.run(command, capture_output=True, encoding="utf-8", errors="replace", timeout=60)
result = {"authority": receipt, "command": command, "exit_code": execution.returncode,
          "stdout": execution.stdout, "stderr": execution.stderr,
          "classification": "KERNEL_PRIMITIVE_ONLY_NOT_QUALIFIED_OWNER_OR_ACCEPTED_SOURCE"}
(directory / "immutable-export-execution.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"exit_code": execution.returncode, "stdout": execution.stdout}))
raise SystemExit(execution.returncode)
