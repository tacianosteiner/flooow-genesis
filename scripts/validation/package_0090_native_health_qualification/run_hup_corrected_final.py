"""Complete rerun after retained-postmaster control-HUP race correction."""
from pathlib import Path
import subprocess,sys,time,json
HERE=Path(__file__).parent;ROOT=HERE.resolve().parents[2];OUT=ROOT/'docs/evidence/package-0090-g3f4-census-heartbeat-domain-parity'
while True:
    try:ready=len(json.loads((OUT/'CORRECTED-FINAL-ROUNDS.json').read_text()))==12
    except (FileNotFoundError,json.JSONDecodeError):ready=False
    if ready:break
    time.sleep(2)
results=[]
for i,module in enumerate(['binding_encoding_probe','progress_probe','census_probe','oid_probe','domain_probe','scenarios','supplement','restart_probe','drain_probe','crypto_material_probe','storage_probe','socket_probe'],28):
    dest=OUT/f'hup-final-{i:02d}-{module}';start=time.monotonic_ns()
    r=subprocess.run([sys.executable,str(HERE/'build.py'),'--output',str(dest),'--scenario-module',module])
    results.append({'module':module,'directory':str(dest.relative_to(ROOT)),'exit':r.returncode,'begin_ns':start,'end_ns':time.monotonic_ns()})
    (OUT/'HUP-FINAL-ROUNDS.json').write_text(json.dumps(results,indent=2)+'\n',encoding='utf-8')
    print('HUP_FINAL_COMPLETE',module,r.returncode,flush=True)
