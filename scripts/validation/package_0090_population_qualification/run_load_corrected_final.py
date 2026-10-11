"""Only broad harness changed; native final bytes remain frozen."""
from pathlib import Path
import subprocess,sys,time,json
HERE=Path(__file__).parent;ROOT=HERE.resolve().parents[2];OUT=ROOT/'docs/evidence/package-0090-g3f4-census-heartbeat-domain-parity'
while True:
    try:rows=json.loads((OUT/'HUP-FINAL-ROUNDS.json').read_text());ready=len(rows)==13
    except (FileNotFoundError,json.JSONDecodeError):ready=False
    if ready:break
    time.sleep(2)
dest=OUT/'hup-final-41-scenarios-load-preparation';start=time.monotonic_ns()
r=subprocess.run([sys.executable,str(HERE/'build.py'),'--output',str(dest),'--scenario-module','scenarios'])
replacement={'module':'scenarios','directory':str(dest.relative_to(ROOT)),'exit':r.returncode,'begin_ns':start,'end_ns':time.monotonic_ns()}
superseded=[row for row in rows if row['module']=='scenarios']
selected=[replacement if row['module']=='scenarios' else row for row in rows]
(OUT/'FINAL-SELECTED-ROUNDS.json').write_text(json.dumps({'rounds':selected,'superseded_broad_harness_rounds':superseded,'reason':'Collector timeout30s expired during CPU preparation; only collection controls changed to90s/stop20s. No native/lease/ACK/policy change.'},indent=2)+'\n',encoding='utf-8')
print('LOAD_CORRECTED_FINAL_COMPLETE',r.returncode,flush=True)
