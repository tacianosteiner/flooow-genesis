"""Run corrected witnesses after the primary owned-container sequence ends."""
from pathlib import Path
import json,subprocess,sys,time
HERE=Path(__file__).parent;ROOT=HERE.resolve().parents[2]
OUT=ROOT/'docs/evidence/package-0090-g3f4-census-heartbeat-domain-parity'
while True:
    try:ready=len(json.loads((OUT/'FINAL-ROUNDS.json').read_text()))==9
    except (FileNotFoundError,json.JSONDecodeError):ready=False
    if ready:break
    time.sleep(2)
results=[]
for i,module in enumerate(['census_probe','oid_probe','storage_probe','binding_encoding_probe'],10):
    dest=OUT/f'final-{i:02d}-{module}';start=time.monotonic_ns()
    r=subprocess.run([sys.executable,str(HERE/'build.py'),'--output',str(dest),'--scenario-module',module])
    results.append({'module':module,'directory':str(dest.relative_to(ROOT)),'exit':r.returncode,'begin_ns':start,'end_ns':time.monotonic_ns()})
    (OUT/'FOLLOWUP-ROUNDS.json').write_text(json.dumps(results,indent=2)+'\n',encoding='utf-8')
    print('FOLLOWUP_COMPLETE',module,r.returncode,flush=True)
