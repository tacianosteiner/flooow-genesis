"""Sequential isolated experiments. Failures are retained; no PASS aggregation."""
from pathlib import Path
import subprocess,sys,json,time
HERE=Path(__file__).parent;ROOT=HERE.resolve().parents[2]
OUT=ROOT/'docs/evidence/package-0090-g3f4-census-heartbeat-domain-parity'
modules=['progress_probe','census_probe','oid_probe','domain_probe','scenarios','supplement','restart_probe','drain_probe','crypto_material_probe']
results=[]
for i,module in enumerate(modules,1):
    dest=OUT/f'final-{i:02d}-{module}';begin=time.monotonic_ns()
    r=subprocess.run([sys.executable,str(HERE/'build.py'),'--output',str(dest),'--scenario-module',module])
    results.append({'module':module,'directory':str(dest.relative_to(ROOT)),'exit':r.returncode,'begin_ns':begin,'end_ns':time.monotonic_ns()})
    (OUT/'FINAL-ROUNDS.json').write_text(json.dumps(results,indent=2)+'\n',encoding='utf-8')
    print('ROUND_COMPLETE',module,r.returncode,flush=True)
