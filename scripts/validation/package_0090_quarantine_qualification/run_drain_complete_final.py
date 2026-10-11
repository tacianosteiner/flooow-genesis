"""Finish all drain assertions while preserving any failed old-generation witness."""
from pathlib import Path
import subprocess,sys,time,json
HERE=Path(__file__).parent;ROOT=HERE.resolve().parents[2];OUT=ROOT/'docs/evidence/package-0090-g3f4-census-heartbeat-domain-parity'
while True:
    try:bundle=json.loads((OUT/'FINAL-SELECTED-ROUNDS.json').read_text());ready=len(bundle['rounds'])==13
    except (FileNotFoundError,json.JSONDecodeError):ready=False
    if ready:break
    time.sleep(2)
dest=OUT/'hup-final-42-drain-complete';start=time.monotonic_ns()
r=subprocess.run([sys.executable,str(HERE/'build.py'),'--output',str(dest),'--scenario-module','drain_probe'])
replacement={'module':'drain_probe','directory':str(dest.relative_to(ROOT)),'exit':r.returncode,'begin_ns':start,'end_ns':time.monotonic_ns()}
bundle['superseded_drain_rounds']=[row for row in bundle['rounds'] if row['module']=='drain_probe']
bundle['rounds']=[replacement if row['module']=='drain_probe' else row for row in bundle['rounds']]
bundle['drain_handling']='Unavailable original catalog is FAIL/UNKNOWN. Fresh preparation only finishes remaining cases and does not force PASS.'
(OUT/'FINAL-SELECTED-ROUNDS.json').write_text(json.dumps(bundle,indent=2)+'\n',encoding='utf-8')
(OUT/'FINAL-SELECTION-COMPLETE.json').write_text(json.dumps({'complete':True,'selected_rounds':len(bundle['rounds']),'drain_exit':r.returncode},indent=2)+'\n',encoding='utf-8')
print('DRAIN_COMPLETE_FINAL',r.returncode,flush=True)
