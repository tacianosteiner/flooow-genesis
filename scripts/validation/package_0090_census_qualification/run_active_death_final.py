from pathlib import Path
import subprocess,sys,time,json
HERE=Path(__file__).parent;ROOT=HERE.resolve().parents[2];OUT=ROOT/'docs/evidence/package-0090-g3f4-census-heartbeat-domain-parity'
while True:
    try:rows=json.loads((OUT/'HUP-FINAL-ROUNDS.json').read_text());ready=len(rows)==12
    except (FileNotFoundError,json.JSONDecodeError):ready=False
    if ready:break
    time.sleep(2)
dest=OUT/'hup-final-40-participant_dead_probe';start=time.monotonic_ns()
r=subprocess.run([sys.executable,str(HERE/'build.py'),'--output',str(dest),'--scenario-module','participant_dead_probe'])
rows.append({'module':'participant_dead_probe','directory':str(dest.relative_to(ROOT)),'exit':r.returncode,'begin_ns':start,'end_ns':time.monotonic_ns()})
(OUT/'HUP-FINAL-ROUNDS.json').write_text(json.dumps(rows,indent=2)+'\n',encoding='utf-8')
print('ACTIVE_DEATH_FINAL_COMPLETE',r.returncode,flush=True)
