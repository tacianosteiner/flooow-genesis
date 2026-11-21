"""Prospective candidate build/regressions; never qualification or acceptance."""
import hashlib
import json
import pathlib
import subprocess

directory=pathlib.Path(__file__).resolve().parent
output=directory.parent
repository=directory.parents[3]
antecedent=next((repository/'docs/evidence').glob('*realization-v1-continuation-v1'))
image='sha256:07fc165de5bb569d822460e2df645c5489f99220fc2cb16c86596d39db394561'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
receipt={
 'PARENT_AUTHORITY':'FLOOOW_MVP_AUTONOMOUS_COMPLETION_AUTHORITY_V1',
 'CHILD_AUTHORITY_ID':'PACKAGE_0090_S03_FIXED_FOUR_EFFECT_ADAPTER_CANDIDATE_V1',
 'PURPOSE':'Reduce four already-declared candidate effects to fixed Linux x86_64 syscalls; retain error failclosed semantics',
 'SCOPE':'Prospective private observer candidate only; original/v2 unchanged; no new ABI/source acceptance',
 'INPUTS':{p.name:sha(p) for p in (directory/'native').iterdir() if p.is_file()},
 'PERMITTED_EFFECTS':['compile/link/static inspect','64 synthetic cases','576 deterministic mutations','8 own-child syscall-error cases','4 before-call/after-publication deferred cancellation cases'],
 'PROHIBITED_EFFECTS':['DB','network','V043','B02','accepted observer/source claims','historical mutation','new syscall selectors'],
 'PRECONDITIONS':'Pinned offline image, uid65534, no capabilities; no generic external syscall API; same BOOTTIME/F_GETFL/fstat/bounded nonblocking write',
 'EXIT_CONDITIONS':'Preserve failures; record exact native/provider imports and regressions; await independent review/cancellation qualification',
 'EXPIRY_OR_TERMINATION':'Own container completion or60second timeouts',
 'PARENT_BOUNDARY_HASH_OR_REFERENCE':{'path':'../authority-receipt.json','sha256':sha(output/'authority-receipt.json')},
 'CANCELLATION_LIMIT':'Raw write has no libc pthread cancellation point; equivalence not claimed. Before/during/after cancellation/owner integration still require qualification.'
}
(directory/'authority-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
base=['docker','run','--rm','--pull','never','--network','none','--read-only','--user','65534:65534','--cap-drop','ALL','--security-opt','no-new-privileges','--tmpfs','/tmp:rw,noexec,size=16m']
compile_command='gcc -std=c11 -O2 -Wall -Wextra -Werror -Wno-deprecated-declarations -fPIC -fvisibility=hidden -fno-builtin -fno-tree-loop-distribute-patterns -shared -nostartfiles -Wl,-z,now,-z,relro /src/observer_common.c /src/health_guard.c /src/census_observer.c -lcrypto -lc -o /out/observer-candidate.so && gcc -std=c11 -O2 -Wall -Wextra -Werror -I/src /harness/observer_fixture_tests.c -L/out -Wl,-rpath,/out -l:observer-candidate.so -ldl -o /out/observer-fixture-tests && gcc -std=c11 -O2 -Wall -Wextra -Werror -I/src -I/harness /properties/properties.c -L/out -Wl,-rpath,/out -l:observer-candidate.so -ldl -o /out/properties && gcc -std=c11 -O2 -Wall -Wextra -Werror -I/src -I/harness /probe/error_cases.c -L/out -Wl,-rpath,/out -l:observer-candidate.so -ldl -o /out/error-cases && readelf -Ws /out/observer-candidate.so && objdump -d -w /out/observer-candidate.so'
compile_command += ' && gcc -std=c11 -O2 -Wall -Wextra -Werror -I/src -I/harness /probe/cancellation_cases.c -L/out -Wl,-rpath,/out -l:observer-candidate.so -ldl -pthread -o /out/cancellation-cases'
command=base+['--mount',f'type=bind,source={directory / "native"},target=/src,readonly','--mount',f'type=bind,source={directory / "build"},target=/out','--mount',f'type=bind,source={antecedent / "harness"},target=/harness,readonly','--mount',f'type=bind,source={output / "native-properties"},target=/properties,readonly','--mount',f'type=bind,source={directory},target=/probe,readonly','--entrypoint','/bin/sh',image,'-c',compile_command]
p=subprocess.run(command,capture_output=True,encoding='utf-8',errors='replace',timeout=60)
(directory/'build-execution.json').write_text(json.dumps({'command':command,'exit_code':p.returncode,'stdout':p.stdout,'stderr':p.stderr},indent=2)+'\n',encoding='utf-8')
assert p.returncode==0,p.stderr
rows=[]
for executable in ('observer-fixture-tests','properties','error-cases','cancellation-cases'):
 command=base+['--mount',f'type=bind,source={directory / "build"},target=/out,readonly','--entrypoint',f'/out/{executable}',image]
 p=subprocess.run(command,capture_output=True,encoding='utf-8',errors='replace',timeout=60)
 rows.append({'executable':executable,'command':command,'exit_code':p.returncode,'stdout':p.stdout,'stderr':p.stderr})
 (directory/'regression.json').write_text(json.dumps({'candidate_sha256':sha(directory/'build/observer-candidate.so'),'scope':'Synthetic/error mechanics only; not fixed33/66 or acceptance','executions':rows},indent=2)+'\n',encoding='utf-8')
 assert p.returncode==0,p.stdout+p.stderr
 print(json.dumps({'executable':executable,'exit_code':p.returncode,'output_lines':len(p.stdout.splitlines())}))
