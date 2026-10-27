"""Disposable TEST reference journal; never production or canonical authority.

This protects participants that actually acquire its OS lock. SQL/host actors
do not acquire that lock automatically. A separate complete mediation proof is
mandatory, and absent that proof eligibility always denies.
"""
import contextlib,hashlib,json,os,time,uuid
from pathlib import Path

class Denied(RuntimeError):pass

def require(condition,message):
    if not condition:raise Denied(message)

def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()
def digest(value):return hashlib.sha256(canonical(value)).hexdigest()

class Fence:
    STATES={'STABLE','PREPARED','APPLYING','COMMITTED_PENDING_RECONCILIATION','ROLLED_BACK','UNKNOWN'}
    def __init__(self,directory,deployment,incarnation):
        self.directory=Path(directory);self.directory.mkdir(exist_ok=True)
        self.journal=self.directory/'transition.jsonl';self.lockfile=self.directory/'decision.lock'
        self.context=dict(deployment=deployment,incarnation=incarnation)
        if not self.lockfile.exists():
            with self.lockfile.open('xb') as stream:stream.write(b'0');stream.flush();os.fsync(stream.fileno())
        with self.locked():
            if not self.journal.exists():self._append(dict(state='STABLE',generation=0,transition_id=None,decision_id='TEST_ONLY_REFERENCE_INITIALIZATION',CLASS_ID=None,target_object=None,actor='TEST_BOOTSTRAP',generation_before=0,generation_after=0,outcome='INITIALIZED'))
            self._read()

    @contextlib.contextmanager
    def locked(self):
        with self.lockfile.open('r+b',buffering=0) as stream:
            if os.name=='nt':
                import msvcrt
                while True:
                    try:stream.seek(0);msvcrt.locking(stream.fileno(),msvcrt.LK_NBLCK,1);break
                    except OSError:time.sleep(.005)
            else:
                import fcntl
                fcntl.flock(stream.fileno(),fcntl.LOCK_EX)
            try:yield
            finally:
                if os.name=='nt':stream.seek(0);msvcrt.locking(stream.fileno(),msvcrt.LK_UNLCK,1)
                else:fcntl.flock(stream.fileno(),fcntl.LOCK_UN)

    def _read(self):
        records=[];previous='0'*64;generation=-1
        for line in self.journal.read_bytes().splitlines():
            row=json.loads(line);payload={k:v for k,v in row.items() if k!='record_hash'}
            require(row['sequence']==len(records)+1 and row['previous_hash']==previous,'Audit sequence/chain mismatch')
            require(row['record_hash']==digest(payload),'Audit payload mismatch')
            require(all(row.get(k)==v for k,v in self.context.items()),'Deployment/incarnation mismatch')
            require(row['state'] in self.STATES and row['generation']>=generation,'State/generation rollback')
            generation=row['generation'];previous=row['record_hash'];records.append(row)
        require(bool(records),'Missing bootstrap');return records

    def _append(self,payload):
        records=self._read() if self.journal.exists() else []
        row=dict(payload,**self.context,sequence=len(records)+1,previous_hash=records[-1]['record_hash'] if records else '0'*64)
        row['record_hash']=digest(row)
        with self.journal.open('ab',buffering=0) as stream:
            require(stream.write(canonical(row)+b'\n')==len(canonical(row))+1,'Short journal append');os.fsync(stream.fileno())
        return row

    def snapshot(self):
        with self.locked():
            last=self._read()[-1]
            # Recovery never interprets a durable in-progress transition as
            # STABLE. Explicit reconciliation is required, without timeouts.
            return {k:last[k] for k in ['deployment','incarnation','generation','state','record_hash','transition_id']}

    def begin(self,class_id,target,actor,decision_id):
        with self.locked():
            last=self._read()[-1];require(last['state']=='STABLE','Transition already unresolved')
            return self._append(dict(state='PREPARED',generation=last['generation']+1,generation_before=last['generation'],generation_after=last['generation']+1,transition_id=str(uuid.uuid4()),decision_id=decision_id,CLASS_ID=class_id,target_object=target,actor=actor,outcome='PENDING'))

    def stage(self,transition_id,state):
        allowed={'PREPARED':{'APPLYING','UNKNOWN','ROLLED_BACK'},'APPLYING':{'COMMITTED_PENDING_RECONCILIATION','UNKNOWN','ROLLED_BACK'},'COMMITTED_PENDING_RECONCILIATION':{'UNKNOWN'},'UNKNOWN':set(),'ROLLED_BACK':set()}
        with self.locked():
            last=self._read()[-1];require(last['transition_id']==transition_id and state in allowed.get(last['state'],set()),'Illegal transition/replay')
            payload={k:v for k,v in last.items() if k not in ['sequence','previous_hash','record_hash','deployment','incarnation']};payload.update(state=state,outcome='UNRESOLVED' if state=='UNKNOWN' else 'PENDING');return self._append(payload)

    def reconcile(self,transition_id,evidence):
        with self.locked():
            last=self._read()[-1];require(last['transition_id']==transition_id and last['state']!='STABLE','Wrong/already reconciled transition')
            require(evidence.get('transition_id')==transition_id and evidence.get('deployment')==self.context['deployment'] and evidence.get('incarnation')==self.context['incarnation'],'Reconciliation binding mismatch')
            require(evidence.get('outcome') in ['COMMITTED','ROLLED_BACK'] and evidence.get('independent_evidence_identity'),'Unknown outcome remains blocked')
            payload={k:v for k,v in last.items() if k not in ['sequence','previous_hash','record_hash','deployment','incarnation']};payload.update(state='STABLE',outcome=evidence['outcome'],reconciliation=evidence);return self._append(payload)

    def decide(self,samples,tuple_value,coverage):
        with self.locked():
            current=self._read()[-1]
            same=all(s['state']=='STABLE' and s['generation']==current['generation'] and all(s[k]==self.context[k] for k in self.context) for s in samples)
            complete=len(coverage)==46 and all(v=='PROVEN' for v in coverage.values())
            # No caller boolean can replace the full class receipt. This is
            # still TEST-only, and no native/READY/S04 authority is conferred.
            result='DENY' if not complete or not same or current['state']!='STABLE' else 'CONDITIONAL_REFERENCE_MATCH_ONLY'
            return dict(decision_id=str(uuid.uuid4()),decision=result,generation=current['generation'],state=current['state'],tuple_digest=digest(tuple_value),audit_tip=current['record_hash'],T10_DECISION_monotonic_ns=time.monotonic_ns(),live_eligibility=False,complete_mediation=complete)
