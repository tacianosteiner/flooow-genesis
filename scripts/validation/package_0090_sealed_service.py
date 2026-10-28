"""Disposable TEST broker/native delegate. Not a production control plane.

No SQL, role, path, command or credential is accepted by the mutation API.
Bootstrap supplies private material once through an unlinked container FIFO.
"""
import ctypes
import hashlib
import hmac
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys
import threading
import time
import urllib.request
import uuid
from http.server import BaseHTTPRequestHandler, HTTPServer

MODULE = Path('/usr/lib/postgresql/18/lib/flooow_offline_mac32.so')
EXPECTED = '5aeedcdb693442b7738b6f33604e059094f584af29d1879bf35482ca06ef63b5'
CODE = '/opt/sealed/package_0090_sealed_service.py'
STATE = Path('/state')


def canonical(x):
    return json.dumps(x, sort_keys=True, separators=(',', ':')).encode()


def digest(x):
    return hashlib.sha256(x).hexdigest()


def secure_process():
    libc = ctypes.CDLL(None, use_errno=True)
    if libc.prctl(38, 1, 0, 0, 0) or libc.prctl(4, 0, 0, 0, 0):
        raise RuntimeError('Cannot set no_new_privs/non-dumpable')


def worker_seccomp():
    # Linux x86_64 only: immutable participant cannot exec, fork, signal its
    # controller, inspect memory, remount or enter another namespace.
    if os.uname().machine != 'x86_64':
        raise RuntimeError('Unsupported seccomp architecture')
    class Filter(ctypes.Structure):
        _fields_ = [('code', ctypes.c_ushort), ('jt', ctypes.c_ubyte), ('jf', ctypes.c_ubyte), ('k', ctypes.c_uint)]
    class Program(ctypes.Structure):
        _fields_ = [('len', ctypes.c_ushort), ('filter', ctypes.POINTER(Filter))]
    instructions = [Filter(0x20, 0, 0, 4), Filter(0x15, 1, 0, 0xc000003e), Filter(6, 0, 0, 0x80000000), Filter(0x20, 0, 0, 0),
                    Filter(0x35, 0, 1, 0x40000000), Filter(6, 0, 0, 0x80000000)]
    for number in [56, 57, 58, 59, 62, 101, 129, 155, 161, 165, 166, 200, 234, 272, 297, 308, 310, 311, 322, 424, 435]:
        instructions += [Filter(0x15, 0, 1, number), Filter(6, 0, 0, 0x50001)]
    instructions.append(Filter(6, 0, 0, 0x7fff0000))
    array = (Filter * len(instructions))(*instructions)
    program = Program(len(instructions), array)
    if ctypes.CDLL(None, use_errno=True).prctl(22, 2, ctypes.byref(program), 0, 0):
        raise RuntimeError('Cannot install participant seccomp')


def native_probes():
    before = digest(MODULE.read_bytes())
    results = []
    scratch = Path('/tmp/substitute-' + str(os.getpid()))
    scratch.write_bytes(b'not a module')
    operations = {
        'append': lambda: MODULE.open('ab').write(b'x'),
        'truncate': lambda: MODULE.open('wb').close(),
        'replace': lambda: MODULE.write_bytes(b'x'),
        'rename_over': lambda: os.replace(scratch, MODULE),
        'chmod': lambda: MODULE.chmod(0o777),
        'chown': lambda: os.chown(MODULE, os.getuid(), os.getgid()),
        'symlink_substitution': lambda: os.symlink('/tmp/substitute', MODULE),
        'loader_path_write': lambda: Path('/usr/lib/postgresql/18/lib/flooow_substitute.so').write_bytes(b'x'),
        'bind_mount': lambda: subprocess.run(['mount', '--bind', str(scratch), str(MODULE)], capture_output=True, check=True),
    }
    for name, operation in operations.items():
        try:
            operation()
            denied, error = False, None
        except Exception as exc:
            denied, error = True, type(exc).__name__ + ':' + str(exc)
        results.append(dict(operation=name, denied=denied, error=error))
    return dict(uid=os.getuid(), gid=os.getgid(), before=before, after=digest(MODULE.read_bytes()), cases=results,
                status={line.split(':')[0]: line.split(':', 1)[1].strip() for line in Path('/proc/self/status').read_text().splitlines() if line.startswith(('CapEff:', 'NoNewPrivs:', 'Seccomp:'))})


def participant():
    secure_process()
    worker_seccomp()
    identity = dict(pid=os.getpid(), start=Path('/proc/self/stat').read_text().split()[21], module=digest(MODULE.read_bytes()))
    print(json.dumps(identity), flush=True)
    for line in sys.stdin:
        request = json.loads(line)
        if request['op'] == 'challenge':
            result = dict(identity, nonce=request['nonce'], generation=request['generation'])
            result['proof'] = digest(canonical(result))
        elif request['op'] == 'probes':
            result = native_probes()
            try:
                os.execve('/usr/bin/python3', ['python3', '-c', 'raise SystemExit(99)'], {'LD_PRELOAD': '/tmp/substitute'})
                denied = False
            except OSError as exc:
                denied = exc.errno == 1
            result['cases'].append(dict(operation='exec_loader_substitution', denied=denied))
            libc = ctypes.CDLL(None, use_errno=True)
            for name, number, args in [('queued_signal_parent', 129, [os.getppid(), 0, 0]),
                                       ('queued_thread_signal_parent', 297, [os.getppid(), os.getppid(), 0, 0])]:
                ctypes.set_errno(0)
                answer = libc.syscall(number, *args)
                result['cases'].append(dict(operation=name, denied=answer == -1 and ctypes.get_errno() == 1, errno=ctypes.get_errno()))
        else:
            raise RuntimeError('Closed participant protocol')
        print(json.dumps(result), flush=True)


def db(sql, credential, host):
    environment = dict(os.environ, PGHOST=host, PGUSER='test_0090_broker', PGPASSWORD=credential, PGDATABASE='g3f4', PGCONNECT_TIMEOUT='5')
    return subprocess.run(['psql', '-X', '-w', '-At', '-v', 'ON_ERROR_STOP=1', '-v', 'VERBOSITY=verbose'], input=sql.encode(), capture_output=True, env=environment, timeout=20)


def db_worker():
    secure_process()
    request = json.loads(sys.stdin.readline())
    if request['fault'] == 'pre':
        os._exit(77)
    environment = dict(os.environ, PGHOST=request['host'], PGUSER='test_0090_broker', PGPASSWORD=request['credential'], PGDATABASE='g3f4')
    p = subprocess.Popen(['psql', '-X', '-w', '-At', '-v', 'ON_ERROR_STOP=1'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=environment, text=True)
    p.stdin.write('BEGIN; SELECT pg_current_xact_id();\n'); p.stdin.flush()
    line = p.stdout.readline().strip()
    if line == 'BEGIN':
        line = p.stdout.readline().strip()
    print(json.dumps(dict(xid=line, pid=os.getpid())), flush=True)
    if sys.stdin.readline().strip() != 'PERMIT':
        os._exit(79)
    state = 'ENABLE' if request['enabled'] else 'DISABLE'
    p.stdin.write('SET ROLE flooow_offline_control_owner; ALTER TABLE public.offline_binding_header ' + state + ' ROW LEVEL SECURITY; COMMIT;\n\\q\n'); p.stdin.flush()
    p.stdin.close(); p.wait(timeout=15)
    if p.returncode:
        print(json.dumps(dict(error=p.stderr.read())), flush=True); os._exit(80)
    if request['fault'] == 'post':
        os._exit(78)
    print(json.dumps(dict(outcome='COMMITTED')), flush=True)


class Native:
    def __init__(self, config):
        self.token = config['native_token'].encode()
        self.epoch = config['epoch']
        self.generation = -1
        self.child = None
        self.proof = None
        self.lock = threading.Lock()

    def ask_child(self, message):
        self.child.stdin.write(json.dumps(message) + '\n'); self.child.stdin.flush()
        return json.loads(self.child.stdout.readline())

    def dispatch(self, request):
        with self.lock:
            if request == {'op': 'status'}:
                return dict(generation=self.generation, identity=self.proof, pid=os.getpid())
            if request == {'op': 'probes'}:
                return dict(agent=native_probes(), participant=self.ask_child(dict(op='probes')))
            signed = dict(request); signature = signed.pop('mac', '')
            if not hmac.compare_digest(signature, hmac.new(self.token, canonical(signed), hashlib.sha256).hexdigest()):
                raise RuntimeError('Unauthenticated native transition')
            if set(signed) != {'op', 'epoch', 'generation', 'transition_id', 'state', 'CLASS_ID', 'target'} or signed['op'] != 'replace' or signed['epoch'] != self.epoch or signed['state'] != 'TRANSITIONING' or signed['generation'] <= self.generation or signed['CLASS_ID'] != '0090/CURRENTNESS/native_participant' or signed['target'] != 'sealed-test-participant':
                raise RuntimeError('Invalid native transition binding')
            old = self.proof
            if self.child:
                self.child.terminate(); self.child.wait(timeout=5)
            self.child = subprocess.Popen(['/usr/bin/python3', '-I', '-B', CODE, 'participant'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env={'PATH': '/usr/bin:/bin'})
            identity = json.loads(self.child.stdout.readline())
            challenge = self.ask_child(dict(op='challenge', nonce=secrets.token_hex(32), generation=signed['generation']))
            proof = challenge.pop('proof')
            if identity['module'] != EXPECTED or challenge['module'] != EXPECTED or challenge['generation'] != signed['generation'] or digest(canonical(challenge)) != proof:
                raise RuntimeError('New enrollment proof failed')
            self.generation = signed['generation']; self.proof = dict(challenge, proof=proof)
            return dict(old=old, new=self.proof, delegate_pid=os.getpid(), module=EXPECTED,
                        scope='TEST process enrollment/file-identity challenge; not canonical native health or 100us proof')


class Broker:
    def __init__(self, config):
        self.config = config
        self.credential = config.pop('credential')
        self.lock = threading.Lock()
        self.epoch = config['epoch']; self.generation = 0; self.state = 'PREPARED'; self.tip = '0' * 64
        self.records = []; self.pending = None
        self.native_binding = None
        if (STATE / 'epoch').exists():
            raise RuntimeError('Existing epoch requires reconciliation, never automatic initialization')
        STATE.mkdir(exist_ok=True)
        self.write_file('epoch', self.epoch.encode())
        self.append('BOOTSTRAP_PREPARED')

    def write_file(self, name, data):
        with (STATE / name).open('wb') as f:
            f.write(data); f.flush(); os.fsync(f.fileno())
        fd = os.open(STATE, os.O_RDONLY | os.O_DIRECTORY)
        try: os.fsync(fd)
        finally: os.close(fd)

    def append(self, event, **details):
        row = dict(epoch_id=self.epoch, state=self.state, generation=self.generation, event=event,
                   previous_tip=self.tip, audit_writer_pid=os.getpid(), monotonic_ns=time.monotonic_ns(), **details)
        # Freeze nested binding/outcome objects before callers advance them.
        # Otherwise an in-memory mutation could disagree with the fsynced bytes.
        row = json.loads(canonical(row))
        row['terminal_tip'] = digest(canonical(row))
        with (STATE / 'journal').open('ab') as f:
            f.write(canonical(row) + b'\n'); f.flush(); os.fsync(f.fileno())
        self.write_file('generation', str(self.generation).encode())
        self.tip = row['terminal_tip']; self.records.append(row)

    def valid(self):
        try:
            return (STATE / 'epoch').read_text() == self.epoch and (STATE / 'generation').read_text() == str(self.generation) and json.loads((STATE / 'journal').read_bytes().splitlines()[-1])['terminal_tip'] == self.tip and (STATE / 'journal').read_bytes() == b''.join(canonical(r) + b'\n' for r in self.records)
        except Exception:
            return False

    def query(self, sql):
        if self.credential is None:
            raise RuntimeError('Credential lost; outcome UNKNOWN')
        r = db(sql, self.credential, self.config['host'])
        if r.returncode:
            raise RuntimeError(r.stderr.decode())
        return r.stdout.decode().strip()

    def native(self, message):
        message['mac'] = hmac.new(self.config['native_token'].encode(), canonical(message), hashlib.sha256).hexdigest()
        req = urllib.request.Request(self.config['native_url'], data=canonical(message), headers={'Content-Type': 'application/json'})
        return json.load(urllib.request.urlopen(req, timeout=15))

    def census(self):
        sql = "SELECT json_build_object('roles',(SELECT json_agg(row_to_json(r)) FROM (SELECT oid,rolname,rolcanlogin,rolsuper,rolcreaterole,rolcreatedb,rolreplication,rolbypassrls FROM pg_roles) r),'memberships',(SELECT json_agg(row_to_json(m)) FROM (SELECT pg_get_userbyid(roleid) AS owner,pg_get_userbyid(member) AS member,admin_option,inherit_option,set_option FROM pg_auth_members) m),'superuser_sessions',(SELECT count(*) FROM pg_stat_activity a JOIN pg_roles r ON r.oid=a.usesysid WHERE r.rolsuper AND a.backend_type='client backend'),'database_owner',(SELECT pg_get_userbyid(datdba) FROM pg_database WHERE datname=current_database()),'rls',(SELECT relrowsecurity FROM pg_class WHERE oid='public.offline_binding_header'::regclass));"
        # Readiness owner capability is private to this broker; no runtime identity.
        result = json.loads(self.query(sql).splitlines()[-1])
        result['ready'] = int(self.query('SET ROLE flooow_offline_control_owner; SELECT count(*) FROM public.offline_readiness;').splitlines()[-1])
        result['client_backends'] = json.loads(self.query("SELECT coalesce(json_agg(json_build_object('pid',pid,'role',usename,'backend_type',backend_type,'application_name',application_name)), '[]') FROM pg_stat_activity;").splitlines()[-1])
        result['ownership'] = json.loads(self.query("SELECT json_build_object('relations',(SELECT json_agg(json_build_object('schema',n.nspname,'name',c.relname,'owner',pg_get_userbyid(c.relowner),'acl',c.relacl)) FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname IN ('public','offline_crypto')),'functions',(SELECT json_agg(json_build_object('signature',p.oid::regprocedure::text,'owner',pg_get_userbyid(p.proowner),'acl',p.proacl,'definer',p.prosecdef,'config',p.proconfig)) FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace WHERE n.nspname IN ('public','offline_crypto')),'types',(SELECT json_agg(json_build_object('schema',n.nspname,'name',t.typname,'owner',pg_get_userbyid(t.typowner),'acl',t.typacl)) FROM pg_type t JOIN pg_namespace n ON n.oid=t.typnamespace WHERE n.nspname IN ('public','offline_crypto')),'schemas',(SELECT json_agg(json_build_object('schema',nspname,'owner',pg_get_userbyid(nspowner),'acl',nspacl)) FROM pg_namespace WHERE nspname IN ('public','offline_crypto')),'default_acls',(SELECT json_agg(row_to_json(d)) FROM pg_default_acl d),'role_settings',(SELECT json_agg(row_to_json(s)) FROM pg_db_role_setting s));").splitlines()[-1])
        result['ordinary_effective_paths'] = json.loads(self.query("SELECT json_agg(json_build_object('role',r.rolname,'owner_set_paths',(SELECT coalesce(json_agg(o.rolname),'[]') FROM pg_roles o WHERE (o.rolname LIKE 'flooow_offline_%_owner' OR o.rolsuper OR o.rolname IN ('test_0090_broker','pg_write_server_files','pg_execute_server_program')) AND pg_has_role(r.oid,o.oid,'SET')),'protected_dml',(SELECT coalesce(json_agg(c.relname),'[]') FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='public' AND c.relkind IN ('r','p') AND has_table_privilege(r.oid,c.oid,'INSERT,UPDATE,DELETE,TRUNCATE,TRIGGER')),'source_execute',(SELECT coalesce(json_agg(p.oid::regprocedure::text),'[]') FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace WHERE n.nspname='public' AND p.proname LIKE 'offline_%' AND has_function_privilege(r.oid,p.oid,'EXECUTE')))) FROM pg_roles r WHERE r.rolname IN ('test_0090_verification','test_0090_issuance','test_0090_execution','test_0090_audit');").splitlines()[-1])
        return result

    def snapshot(self):
        valid = self.valid()
        return dict(epoch=self.epoch, generation=self.generation, state=self.state if valid else 'UNKNOWN',
                    eligible=self.state == 'SEALED' and valid, terminal_tip=self.tip, pending=self.pending, pid=os.getpid(),
                    qualification_tuple=dict(epoch=self.epoch, generation=self.generation, native=self.native_binding))

    def dispatch(self, request):
        with self.lock:
            if request == {'op': 'status'}: return self.snapshot()
            if request == {'op': 'audit'}: return dict(records=self.records, snapshot=self.snapshot())
            if request == {'op': 'census'}: return self.census()
            if set(request) == {'op', 'tuple'} and request['op'] == 'validate_tuple':
                snapshot = self.snapshot()
                return dict(accepted=snapshot['eligible'] and request['tuple'] == snapshot['qualification_tuple'],
                            scope='TEST boundary tuple only; not operational T10/final observer/READY')
            if request == {'op': 'seal'}:
                if self.state != 'PREPARED' or self.generation != 0 or not self.valid():
                    raise RuntimeError('Only fresh bootstrap PREPARED can be sealed')
                census = self.census()
                if census['superuser_sessions'] != 0 or any(r['rolcanlogin'] for r in census['roles'] if r['rolname'].startswith('flooow_offline_') or r['rolsuper']):
                    raise RuntimeError('Unsafe DB census')
                self.state = 'TRANSITIONING'; self.generation += 1; self.append('INITIAL_ENROLLMENT_FENCE')
                native = self.native(dict(op='replace', epoch=self.epoch, generation=self.generation, transition_id=str(uuid.uuid4()), state=self.state, CLASS_ID='0090/CURRENTNESS/native_participant', target='sealed-test-participant'))
                self.native_binding = native['new']
                self.state = 'RECONCILING'; self.append('INITIAL_ENROLLMENT_PROVEN', native=native)
                self.state = 'SEALED'; self.append('SEALED'); return self.snapshot()
            if request == {'op': 'reconcile'}:
                if self.state != 'UNKNOWN' or not self.pending or not self.valid():
                    raise RuntimeError('No reconciliable pending outcome')
                if self.pending.get('xid'):
                    status = self.query("SELECT pg_xact_status('" + self.pending['xid'] + "'::xid8);").splitlines()[-1]
                    actual = self.query("SELECT relrowsecurity::text FROM pg_class WHERE oid='public.offline_binding_header'::regclass;").splitlines()[-1]
                    if status not in ['committed', 'aborted'] or (status == 'committed' and actual != str(self.pending['enabled']).lower()):
                        raise RuntimeError('Independent DB outcome not reconciled')
                elif self.pending.get('before_start'):
                    status = 'NO_MUTATOR_STARTED'
                else:
                    raise RuntimeError('Unknown native/DB outcome')
                self.state = 'RECONCILING'; self.append('INDEPENDENT_RECONCILIATION', outcome=status, binding=self.pending)
                self.generation += 1; self.state = 'SEALED'; self.append('RESEALED', binding=self.pending); self.pending = None
                return dict(outcome=status, snapshot=self.snapshot())
            if set(request) == {'op', 'fault'} and request['op'] == 'metadata_fault' and request['fault'] in ['delete', 'corrupt']:
                if self.state != 'SEALED' or not self.valid(): raise RuntimeError('Unsafe fault injection')
                self.state = 'PREPARED'; self.append('PREPARED_METADATA_FAULT'); self.generation += 1; self.state = 'UNKNOWN'; self.append('METADATA_FAULT_PENDING')
                if request['fault'] == 'delete': (STATE / 'journal').unlink()
                else: self.write_file('journal', b'corrupt\n')
                return self.snapshot()
            if set(request) != {'op', 'fault'} or request['op'] not in ['db_enable', 'db_disable', 'native_replace'] or request['fault'] not in ['none', 'pre', 'post', 'credential_loss']:
                raise RuntimeError('Closed broker API: operation/fields rejected')
            if self.state != 'SEALED' or not self.valid(): raise RuntimeError('Not eligible for mutation')
            native = request['op'] == 'native_replace'
            before = self.snapshot(); tid = str(uuid.uuid4())
            binding = dict(transition_id=tid, CLASS_ID='0090/CURRENTNESS/native_participant' if native else '0090/CURRENTNESS/relation',
                           target='sealed-test-participant' if native else 'public.offline_binding_header.relrowsecurity', actor='test_0090_broker',
                           capability='NATIVE_PROCESS_REPLACER' if native else 'SET_ROLE_OWNER', generation_before=self.generation)
            self.state = 'PREPARED'; self.append('PREPARED', binding=binding)
            self.generation += 1; self.state = 'TRANSITIONING'; binding['generation_after'] = self.generation
            self.append('INVALIDATED_BEFORE_MUTATOR', binding=binding)
            self.pending = dict(binding, before_start=True, enabled=request['op'] == 'db_enable')
            if native and request['fault'] != 'none':
                raise RuntimeError('Native fault mode not supported; no mutation started')
            if native:
                # Once a request can reach the native delegate, an exception is
                # an unknown outcome, never proof that no replacement started.
                self.pending.update(before_start=False, native_request_issued=True)
                self.append('NATIVE_REQUEST_BOUND', binding=self.pending)
                outcome = self.native(dict(op='replace', epoch=self.epoch, generation=self.generation, transition_id=tid, state=self.state, CLASS_ID=binding['CLASS_ID'], target=binding['target']))
                self.native_binding = outcome['new']
                self.append('NATIVE_OUTCOME', binding=binding, outcome=outcome)
            else:
                worker = subprocess.Popen(['/usr/bin/python3', '-I', '-B', CODE, 'db_worker'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env={'PATH': '/usr/bin:/bin'})
                worker.stdin.write(json.dumps(dict(credential=self.credential, host=self.config['host'], enabled=self.pending['enabled'], fault='post' if request['fault'] == 'credential_loss' else request['fault'])) + '\n'); worker.stdin.flush()
                line = worker.stdout.readline()
                if line:
                    xid = json.loads(line)
                    if not xid['xid'].isdigit(): raise RuntimeError('Invalid transaction identity')
                    self.pending.update(xid=xid['xid'], before_start=False, mutation_pid=xid['pid'])
                    self.append('TRANSACTION_BOUND', binding=self.pending)
                    worker.stdin.write('PERMIT\n'); worker.stdin.flush()
                worker.wait(timeout=20)
                outcome = dict(exit=worker.returncode, stdout=worker.stdout.read(), stderr=worker.stderr.read(), mutation_pid=worker.pid)
                if request['fault'] == 'credential_loss':
                    self.credential = None
                    self.state = 'UNKNOWN'; self.append('CREDENTIAL_LOSS_AFTER_WORKER_LOSS', binding=self.pending, outcome=outcome)
                    return dict(before=before, outcome=outcome, snapshot=self.snapshot())
                if worker.returncode:
                    self.state = 'UNKNOWN'; self.append('MUTATOR_CRASH_UNKNOWN', binding=self.pending, outcome=outcome); return dict(before=before, outcome=outcome, snapshot=self.snapshot())
                self.append('DB_OUTCOME', binding=self.pending, outcome=outcome)
                actual = self.query("SELECT relrowsecurity::text FROM pg_class WHERE oid='public.offline_binding_header'::regclass;").splitlines()[-1]
                status = self.query("SELECT pg_xact_status('" + self.pending['xid'] + "'::xid8);").splitlines()[-1]
                if actual != str(self.pending['enabled']).lower() or status != 'committed':
                    raise RuntimeError('DB outcome reconciliation failed')
            self.state = 'RECONCILING'; self.append('OUTCOME_RECONCILED', binding=self.pending, outcome=outcome)
            self.generation += 1; self.state = 'SEALED'; self.append('RESEALED', binding=self.pending); self.pending = None
            return dict(before=before, outcome=outcome, snapshot=self.snapshot(), old_generation_eligible=False)


def serve(kind):
    secure_process()
    Path('/private').mkdir(exist_ok=True)
    fifo = Path('/private/inbox'); os.mkfifo(fifo, 0o600)
    with fifo.open() as f: config = json.load(f)
    fifo.unlink()
    service = Broker(config) if kind == 'broker' else Native(config)
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args): pass
        def do_POST(self):
            try:
                if self.path != '/' or int(self.headers.get('Content-Length', '0')) > 16384: raise RuntimeError('Invalid request')
                value = service.dispatch(json.loads(self.rfile.read(int(self.headers['Content-Length']))))
                status = 200
            except Exception as exc:
                value, status = dict(error=type(exc).__name__ + ':' + str(exc)), 409
                if kind == 'broker' and service.state not in ['PREPARED', 'SEALED', 'UNKNOWN']:
                    service.state = 'UNKNOWN'
                    try: service.append('EXCEPTION_UNKNOWN')
                    except Exception: pass
            data = canonical(value); self.send_response(status); self.end_headers(); self.wfile.write(data)
    HTTPServer(('0.0.0.0', 8080), Handler).serve_forever()


if __name__ == '__main__':
    if sys.argv[1] == 'participant': participant()
    elif sys.argv[1] == 'db_worker': db_worker()
    elif sys.argv[1] == 'probe': print(json.dumps(native_probes()))
    elif sys.argv[1] in ['broker', 'native']: serve(sys.argv[1])
    else: raise SystemExit('Unknown TEST service')
