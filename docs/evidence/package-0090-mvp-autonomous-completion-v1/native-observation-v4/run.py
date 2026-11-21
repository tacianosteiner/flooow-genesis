"""Bounded own-child observer provider/vDSO capture. No DB or acceptance."""
import hashlib
import json
import pathlib
import shutil
import subprocess

directory = pathlib.Path(__file__).resolve().parent
output = directory.parent
repository = directory.parents[3]
antecedent = next((repository / "docs/evidence").glob("*realization-v1-continuation-v1"))
candidate = output / "observer-repair-v2"
image = "sha256:07fc165de5bb569d822460e2df645c5489f99220fc2cb16c86596d39db394561"
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
receipt = {
    "PARENT_AUTHORITY": "FLOOOW_MVP_AUTONOMOUS_COMPLETION_AUTHORITY_V1",
    "CHILD_AUTHORITY_ID": "PACKAGE_0090_MVP_S03_EXACT_CHILD_VDSO_CAPTURE_V1",
    "PURPOSE": "Resolve remaining clock provider target bytes for current repaired observer candidate",
    "SCOPE": "One own disposable synthetic fixture child, max16threads/50000trace stops/65536vDSObytes; no host PID namespace",
    "INPUTS": {"tracer.c": sha(directory / "tracer.c"),
               "observer_fixture_tests.c": sha(antecedent / "harness/observer_fixture_tests.c"),
               "observer-candidate.so": sha(candidate / "build/observer-candidate.so"), "image": image},
    "PERMITTED_EFFECTS": ["compile bounded fixture/tracer", "ptrace own child and bounded threads", "read selected own-child provider pointers/maps/public vDSO bytes", "record stdout/disassembly"],
    "PROHIBITED_EFFECTS": ["DB", "network", "S03 semantic entrypoints", "V043", "B02", "host/other process inspection", "source acceptance", "frozen evidence mutation"],
    "PRECONDITIONS": "Pinned existing local image; candidate bytes copied unchanged; readonly execution inputs; private container PID namespace; minimal ptrace capability solely in disposable test",
    "EXIT_CONDITIONS": "Record exact64fixture outcomes, vDSO mapping/bytes/hash; leave effect scopes unclosed until independent reconstruction",
    "EXPIRY_OR_TERMINATION": "Own container exit, bounded trace stop limit or120second timeout",
    "PARENT_BOUNDARY_HASH_OR_REFERENCE": {"path": "../authority-receipt.json", "sha256": sha(output / "authority-receipt.json")},
}
(directory / "authority-receipt.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
shutil.copyfile(candidate / "build/observer-candidate.so", directory / "build/observer-candidate.so")
base = ["docker", "run", "--rm", "--pull", "never", "--network", "none", "--read-only",
        "--user", "65534:65534", "--cap-drop", "ALL", "--security-opt", "no-new-privileges"]
build = base + ["--tmpfs", "/tmp:rw,noexec,size=16m",
                "--mount", f"type=bind,source={directory},target=/probe",
                "--mount", f"type=bind,source={candidate / 'native'},target=/src,readonly",
                "--mount", f"type=bind,source={antecedent / 'harness'},target=/harness,readonly",
                "--entrypoint", "/bin/sh", image, "-c",
                "gcc -O2 -Wall -Wextra -Wno-misleading-indentation /probe/tracer.c -o /probe/tracer && gcc -std=c11 -O2 -Wall -Wextra -Werror -I/src /harness/observer_fixture_tests.c -L/probe/build -Wl,-rpath,/out -l:observer-candidate.so -ldl -o /probe/build/observer-fixture-tests"]
compiled = subprocess.run(build, capture_output=True, encoding="utf-8", errors="replace", timeout=60)
(directory / "build-execution.json").write_text(json.dumps({"command": build,"exit_code":compiled.returncode,"stdout":compiled.stdout,"stderr":compiled.stderr},indent=2)+"\n",encoding="utf-8")
assert compiled.returncode == 0, compiled.stderr
command = base + ["--cap-add", "SYS_PTRACE", "--security-opt", "seccomp=unconfined",
                  "--tmpfs", "/tmp:rw,noexec,size=16m",
                  "--mount", f"type=bind,source={directory},target=/probe,readonly",
                  "--mount", f"type=bind,source={directory / 'build'},target=/out,readonly",
                  "--entrypoint", "/probe/tracer", image]
execution = subprocess.run(command, capture_output=True, encoding="utf-8", errors="replace", timeout=120)
record = {"command":command,"exit_code":execution.returncode,"tracer_sha256":sha(directory / "tracer"),"stdout":execution.stdout,"stderr":execution.stderr}
(directory / "execution.json").write_text(json.dumps(record,indent=2)+"\n",encoding="utf-8")
assert execution.returncode == 0, execution.stderr[-1000:]
cases = [json.loads(line) for line in execution.stdout.splitlines() if line.startswith('{"role":')]
assert len(cases)==64 and all(row["pass"] for row in cases), cases
lines = [line for line in execution.stdout.splitlines() if line.startswith("VDSO_HEX\t")]
assert len(lines)==1
fields = dict(part.split("=",1) for part in lines[0].split("\t")[1:])
vdso = bytes.fromhex(fields["BYTES"])
assert len(vdso)==int(fields["END"],16)-int(fields["START"],16) and vdso.startswith(b"\x7fELF")
(directory / "vdso.bin").write_bytes(vdso)
result = {"scope":"Exact own-child runtime-selected vDSO ELF bytes only; not kernel/platform/source acceptance",
          "cases":len(cases),"passing":sum(row["pass"] for row in cases),"candidate_sha256":sha(directory / "build/observer-candidate.so"),
          "vdso_start":fields["START"],"vdso_end":fields["END"],"vdso_size":len(vdso),"vdso_sha256":sha(directory / "vdso.bin")}
(directory / "capture-result.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
print(json.dumps(result))
