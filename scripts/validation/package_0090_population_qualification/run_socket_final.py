from pathlib import Path
import subprocess,sys,time,json
HERE=Path(__file__).parent;ROOT=HERE.resolve().parents[2];OUT=ROOT/'docs/evidence/package-0090-g3f4-census-heartbeat-domain-parity'
while True:
    try:rows=json.loads((OUT/'CORRECTED-FINAL-ROUNDS.json').read_text());ready=len(rows)==11
    except (FileNotFoundError,json.JSONDecodeError):ready=False
    if ready:break
    time.sleep(2)
dest=OUT/'corrected-27-socket_probe';start=time.monotonic_ns()
r=subprocess.run([sys.executable,str(HERE/'build.py'),'--output',str(dest),'--scenario-module','socket_probe'])
rows.append({'module':'socket_probe','directory':str(dest.relative_to(ROOT)),'exit':r.returncode,'begin_ns':start,'end_ns':time.monotonic_ns()})
(OUT/'CORRECTED-FINAL-ROUNDS.json').write_text(json.dumps(rows,indent=2)+'\n',encoding='utf-8')
print('SOCKET_FINAL_COMPLETE',r.returncode,flush=True)
