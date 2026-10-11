"""Final heartbeat and complete broad matrix on the final component bytes."""
from pathlib import Path
import subprocess,sys,time,json
HERE=Path(__file__).parent;ROOT=HERE.resolve().parents[2];OUT=ROOT/'docs/evidence/package-0090-g3f4-census-heartbeat-domain-parity'
while True:
    try:ready=len(json.loads((OUT/'FOLLOWUP-ROUNDS.json').read_text()))==4
    except (FileNotFoundError,json.JSONDecodeError):ready=False
    if ready:break
    time.sleep(2)
results=[]
for i,module in enumerate(['progress_probe','scenarios'],14):
    dest=OUT/f'final-{i:02d}-{module}';start=time.monotonic_ns()
    r=subprocess.run([sys.executable,str(HERE/'build.py'),'--output',str(dest),'--scenario-module',module])
    results.append({'module':module,'directory':str(dest.relative_to(ROOT)),'exit':r.returncode,'begin_ns':start,'end_ns':time.monotonic_ns()})
    (OUT/'LAST-ROUNDS.json').write_text(json.dumps(results,indent=2)+'\n',encoding='utf-8')
    print('LAST_ROUND_COMPLETE',module,r.returncode,flush=True)
