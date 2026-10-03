"""TEST ONLY history, conceptual ACL, and synthetic preflight/HMAC codecs."""
import hashlib
import hmac
import json
import re
import struct

import package_0090_evidence_fixture as base

OUTPUT = base.ROOT / 'docs/evidence/PACKAGE-0090-G3F-3B-CATALOG-GOLDENS.json'
PREFIX = 'FLOOOW/OFFLINE-FIELD-PROOF/'
HISTORY_SOURCE = base.ROOT / 'applications/command-authority-ceremony/src/main/kotlin/io/flooow/ceremony/PostgresOfflineMigrationHistory.kt'
ROLES = [None, 'v','i','e','a','ov','oi','oe','oa','op','oq','oz','admin']


def collection(elements, unordered=False):
    elements = list(elements)
    if unordered:
        if len(set(elements)) != len(elements): raise ValueError('Duplicate set member')
        elements.sort()
    return struct.pack('>I',len(elements)) + b''.join(struct.pack('>I',len(e))+e for e in elements)


def ref(name):
    if name is None: return b'\x00'
    raw=base.text(name); return b'\x01'+struct.pack('>I',len(raw))+raw


def scalar(value):
    if value is None: return b'\x00'
    if type(value) is bool: raw=bytes([value])
    elif isinstance(value,str): raw=base.text(value)
    else: raw=value
    return base.present(raw)


def row(kind, values):
    return base.frame(PREFIX+kind+'/V1',[scalar(v) for v in values])


def u8(n): return bytes([n])
def i4(n): return struct.pack('>i',n)
def u4(n): return struct.pack('>I',n)


def history_rows():
    matches=re.findall(r'(\d+) to \("(V\d+__[^"]+\.sql)" to (-?\d+)\)',HISTORY_SOURCE.read_text(encoding='utf-8-sig'))
    if len(matches)!=42: raise ValueError('Frozen complete V001-V042 history fixture missing')
    return [dict(installed_rank=int(v),version=v,type='SQL',script=s,checksum=int(c),success=True) for v,s,c in matches]


def history_encode(rows):
    if len({r['installed_rank'] for r in rows}) != len(rows) or any(r['installed_rank']<=0 for r in rows):
        raise ValueError('Invalid or duplicate history rank')
    frames=[row('HISTORY-ROW',[i4(r['installed_rank']),r['version'],r['type'],r['script'],
                             None if r['checksum'] is None else i4(r['checksum']),r['success']])
            for r in sorted(rows,key=lambda r:r['installed_rank'])]
    return row('HISTORY',[collection(frames)])


def acl_fixture(number):
    identities=[row('ACL-IDENTITY',[u4(i),u4(100+i),ref(name), i<=4 or i==12,
                  False,False,False,False,False,False]) for i,name in enumerate(ROLES[1:],1)]
    roles=ROLES+(['intruder'] if number==6 else [])
    owner='admin' if number==4 else 'oa'
    configs=['search_path=pg_catalog, pg_temp']
    inputs=['pg_catalog.uuid']; all_types=inputs[:]; modes=[1]; names=[None]
    returns='pg_catalog.bytea'; shape=1; volatility=2; definer=True; strict=False; outputs=[]; variadic=None
    schema='public'; function='fixture_scalar'
    if number==2:
        function='fixture_table'; returns='pg_catalog.record'; shape=2
        output_names=['installed_rank','version','type','script','checksum','success']
        output_types=['pg_catalog.int4','pg_catalog.text','pg_catalog.text','pg_catalog.text','pg_catalog.int4','pg_catalog.bool']
        all_types=inputs+output_types; modes=[1]+[5]*6; names=[None]+output_names
        outputs=[row('ACL-OUTPUT',[n,t,u8(5)]) for n,t in zip(output_names,output_types)]
    elif number==3:
        function='transaction_identity_hash'; inputs=['pg_catalog.text[]']; all_types=inputs[:]
        modes=[4]; names=['fields']; returns='pg_catalog.text'; volatility=1; definer=False
        configs=['search_path=pg_catalog, public, pg_temp']; variadic='pg_catalog.text'
    elif number==4:
        schema='offline_crypto'; function='hmac'; inputs=['pg_catalog.bytea','pg_catalog.bytea','pg_catalog.text']
        all_types=inputs[:]; modes=[1]*3; names=[None]*3; volatility=1; definer=False; strict=True; configs=None
    elif number==7: configs=None
    execute=[row('ACL-EXECUTE',[ref(r),u8(1),
                 r==owner or r==('oq' if number==4 else 'a') or number==5 or (number==6 and r=='intruder'),
                 r==owner,r==owner]) for r in roles]
    function_row=row('ACL-FUNCTION',[schema,function,collection(base.text(t) for t in inputs),
        collection(base.text(t) for t in all_types),collection(u8(m) for m in modes),
        collection(b'\x00' if n is None else b'\x01'+base.text(n) for n in names),
        u8(shape),returns,collection(outputs),u8(volatility),definer,ref(owner),
        None if configs is None else collection(base.text(c) for c in configs),i4(0),variadic,strict,
        collection(execute,True)])
    schemas=[]
    for kind,name in [(1,'public'),(2,'flooow_fixture')]+([(1,'offline_crypto')] if number==4 else []):
        for r in roles:
            for priv in ([2,3] if kind==1 else [11,3]):
                owned=r=='admin'
                direct=(owned or (priv in (2,11) and r in ROLES[1:] and
                                  (name!='offline_crypto' or r=='oq')) or
                        (number==8 and name=='public' and priv==3 and r is None))
                effective=direct or (number==8 and name=='public' and priv==3)
                schemas.append(row('ACL-SCHEMA',[u8(kind),name,ref('admin'),ref(r),u8(priv),
                                                direct,effective,owned,owned]))
    defaults=[row('ACL-DEFAULT',[ref(creator),schema,u8(kind),False,ref(None),u8(0),False])
              for creator in ('admin','oa') for schema in ([None,'public','offline_crypto'] if number==4 else [None,'public'])
              for kind in range(1,7)]
    return row('ACL',[collection(identities,True),collection([function_row],True),collection([],True),
                      collection([],True),collection(schemas,True),collection(defaults,True)])


def generate():
    history=history_encode(history_rows()); acl=acl_fixture(1)
    vector=base.derive('VECTOR_1'); pol=base.policy.approved_fixture()
    preflight=row('PREFLIGHT',[base.uuid.UUID(int=3).bytes,bytes.fromhex(vector['binding']['sha256']),
        '0090-v1',hashlib.sha256(history).digest(),hashlib.sha256(acl).digest(),
        bytes.fromhex(pol['canonical_policy_sha256']),struct.pack('>q',1),struct.pack('>q',1000001),u4(1)])
    # Public synthetic test key. NEVER an active/private deployment key or RNG evidence.
    key=bytes(range(32)); mac=hmac.digest(key,preflight,'sha256')
    null_rows=history_rows()+[dict(installed_rank=43,version=None,type='BASELINE',script='fixture-null.sql',checksum=None,success=False)]
    return dict(scope='TEST_GOLDEN_REHEARSAL_ONLY',production_data=False,
        installed_history_claim=False,readiness_approval=False,sql_execution_parity='HOLD_NOT_EXECUTED',
        history_rows=history_rows(),history=base.digest_record(history),
        null_history_rows=null_rows,null_history=base.digest_record(history_encode(null_rows)),
        acl_fixtures=[dict(fixture=f'ACL-V1-F{n}',policy_result='PASS_CONCEPTUAL_ONLY' if n<=4 else 'REJECT',
                           **base.digest_record(acl_fixture(n))) for n in range(1,9)],
        preflight=base.digest_record(preflight),synthetic_hmac_key_hex=key.hex(),
        synthetic_key_scope='PUBLIC_TEST_VECTOR_ONLY_NOT_DEPLOYMENT_KEY_NOT_RNG_PROOF',
        hmac_sha256_hex=mac.hex(),preflight_receipt=base.digest_record(preflight+mac))


if __name__=='__main__':
    data=generate(); OUTPUT.write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')
    print('TEST_ONLY_HISTORY_SHA256='+data['history']['sha256'])
