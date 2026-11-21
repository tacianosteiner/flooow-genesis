"""Static analysis of captured own-child vDSO bytes; never execute that ELF."""
import ast
import hashlib
import importlib.util
import json
import pathlib
import re
import subprocess
import sys

sys.dont_write_bytecode = True
directory = pathlib.Path(__file__).resolve().parent
repository = directory.parents[3]
antecedent = next((repository / "docs/evidence").glob("*realization-v1-continuation-v1"))
parser = repository / "docs/evidence/package-0090-c5v-s03-static-effect-closure-v1/elf_static.py"
spec = importlib.util.spec_from_file_location("frozen_elf_static", parser)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
elf = module.ELF(directory / "vdso.bin")
tree = ast.parse((antecedent / "static_provider_graph.py").read_text(encoding="utf-8"))
functions = ast.Module(body=[node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in ("parse", "expand")], type_ignores=[])
namespace = {"re": re}
exec(compile(functions, "frozen_static_functions_only", "exec"), namespace)
command = ["docker", "run", "--rm", "--pull", "never", "--network", "none", "--read-only",
           "--user", "65534:65534", "--cap-drop", "ALL", "--security-opt", "no-new-privileges",
           "--mount", f"type=bind,source={directory},target=/probe,readonly",
           "--entrypoint", "objdump", "sha256:07fc165de5bb569d822460e2df645c5489f99220fc2cb16c86596d39db394561", "-d", "-w", "/probe/vdso.bin"]
disassembly = subprocess.run(command, capture_output=True, encoding="utf-8", errors="replace", timeout=30)
assert disassembly.returncode == 0, disassembly.stderr
(directory / "vdso-disassembly.txt").write_text(disassembly.stdout, encoding="utf-8")
execution = json.loads((directory / "execution.json").read_text(encoding="utf-8"))
pointer_lines = [line for line in execution["stdout"].splitlines() if line.startswith("BOUND_POINTERS\t")]
assert len(pointer_lines) == 1
pointers = dict(part.split("=",1) for part in pointer_lines[0].split("\t")[1:])
assert pointers["ERRNO"] == "0"
relative_entry = int(pointers["CLOCK"],16)-int(pointers["VDSO_START"],16)
symbols = elf.exports("__vdso_clock_gettime")
assert len(symbols)==1 and symbols[0]["value"] == relative_entry
graph = namespace["expand"](namespace["parse"](directory / "vdso-disassembly.txt"), [relative_entry])
report = {"scope":"Captured runtime-selected clock vDSO entrypoint; no kernel/source/platform acceptance",
          "ELF_sha256":hashlib.sha256(elf.data).hexdigest(), "ELF_build_id":elf.build_id,
          "entry_rva":hex(relative_entry), "symbol":symbols[0], "graph":graph,
          "input_bindings": {str(path.relative_to(repository)).replace(chr(92),"/"):hashlib.sha256(path.read_bytes()).hexdigest()
                             for path in (parser, antecedent / "static_provider_graph.py", directory / "execution.json")},
          "remaining":"Syscall and vvar/CPU/timekeeping state, fallback/error/TLS semantics, exact argument feasibility, protected source/currentness remain separate obligations"}
(directory / "vdso-static-proof.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
print(json.dumps({"entry_rva":hex(relative_entry),"instructions":graph["instructions_reached"],
                  "indirect":len(graph["indirect_frontiers"]),"unmapped":len(graph["unmapped_instruction_addresses"]),
                  "syscalls":len(graph["syscall_instructions"]),"TLS":len(graph["TLS_instructions"]),"classification":graph["classification"]}))
