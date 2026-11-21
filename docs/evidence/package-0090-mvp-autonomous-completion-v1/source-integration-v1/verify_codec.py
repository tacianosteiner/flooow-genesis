import pathlib,subprocess,json,sys
R=pathlib.Path.cwd();O=R/'docs/evidence/package-0090-mvp-autonomous-completion-v1';D=pathlib.Path(__file__).resolve().parent;C=O/'observer-repair-v2';A=next((R/'docs/evidence').glob('*realization-v1-continuation-v1'));image='sha256:07fc165de5bb569d822460e2df645c5489f99220fc2cb16c86596d39db394561'
base=['docker','run','--rm','--pull','never','--network','none','--read-only','--user','65534:65534','--cap-drop','ALL','--security-opt','no-new-privileges','--tmpfs','/tmp:rw,exec,size=64m','--mount',f'type=bind,source={D},target=/probe','--mount',f'type=bind,source={C / "native"},target=/src,readonly','--mount',f'type=bind,source={C / "build"},target=/out,readonly','--mount',f'type=bind,source={A / "harness"},target=/harness,readonly']
p=subprocess.run(base+['--entrypoint','/bin/sh',image,'-c','gcc -std=c11 -O2 -Wall -Wextra -Werror -I/src -I/harness -L/out -Wl,-rpath,/out -o /probe/capture_codec /probe/capture_codec.c -l:observer-candidate.so -ldl'],capture_output=True,text=True);assert p.returncode==0,p.stderr
rows=[];frames=[];expected={};now=0
for role in [1,2]:
 p=subprocess.run(base+['--entrypoint','/probe/capture_codec',image,str(role)],capture_output=True,text=True,timeout=30);rows.append({'role':role,'exit_code':p.returncode,'stdout':p.stdout,'stderr':p.stderr});assert p.returncode==0,p.stdout+p.stderr
 lines=p.stdout.splitlines();header=next(x for x in lines if x.startswith('EXPECTED ')).split();values=[int(x) for x in header[2:]];frames.append(bytes.fromhex(next(x[6:] for x in lines if x.startswith('FRAME '))));now=max(now,int(next(x[9:] for x in lines if x.startswith('USE_TIME '))))
 def ref(seed):return 1,bytes(seed+i for i in range(4))
 target=(tuple(ref(x) for x in [40,41,50,51,52,53,54]),1,1,2,(1,2,3),b'test');seed=1 if role==1 else 21
 expected[role]={'target':target,'observer':tuple(ref(x) for x in [seed,seed+1,40,seed+2,seed+3]),'origin':ref(60),'domain':tuple(ref(x) for x in [77,78,70,71,72,73,74,75,76]),'root_interval':tuple(values[:2]),'lease':tuple(values[2:]),'sources':tuple((tuple(ref(x+i) for x in [80,90,100,110]),bytes([i+1])*32) for i in range(8)),'population':ref(63),'members':(target,)}
sys.dont_write_bytecode=True;sys.path.insert(0,str(D));from pair_consumer import reconstruct_pair_constraints
result=reconstruct_pair_constraints(expected,tuple(frames),now);assert result['matching_under_independently_supplied_expectations'],result
(D/'actual-codec-interoperability.json').write_text(json.dumps({'scope':'Compiled C private codec intoPython consumer, separate PRECALL expected inputs; synthetic SourceRefs only, not source acceptance/authentication','executions':rows,'result':result},indent=2)+'\n');print(json.dumps(result))
