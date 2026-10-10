"""Synthetic reference codec derived from SPEC0090 section4, not new authority."""
import hashlib,struct,uuid,unicodedata,datetime
FIELDS='binding_schema_version binding_id deployment_id deployment_incarnation_id run_id plan_id execution_plan_version organization_id manifest_id manifest_digest canonical_manifest_hash canonical_manifest_encoding_version mercado_livre_connection_id omie_connection_id marketplace_order_id source_order_reference integration_reference permission reason provenance principal_id credential_id grant_id decision_id correlation_id principal_operation_id credential_operation_id grant_operation_id issued_at valid_from expires_at identity_slots offline_surface_version deadline_policy_version deadline_policy_digest admission_contract_version delivery_contract_version reconciliation_contract_version'.split()
HASH={'manifest_digest','canonical_manifest_hash','deadline_policy_digest'}
VERSIONS={'binding_schema_version','execution_plan_version','canonical_manifest_encoding_version'}
TIMES={'issued_at','valid_from','expires_at'}
def sha(b):return hashlib.sha256(b).hexdigest()
def text(s):
    if not isinstance(s,str) or not s or unicodedata.normalize('NFC',s)!=s or any(ord(c)<32 or ord(c)==127 for c in s):raise ValueError('Noncanonical text')
    return s.encode('utf-8','strict')
def unhex(s):return bytes.fromhex(s.removeprefix('\\x'))
def micros(s):return int(datetime.datetime.fromisoformat(s.replace('Z','+00:00')).timestamp()*1000000)
def typed(name,v):
    if v is None:raise ValueError('Null header field')
    if name in HASH:return unhex(v)
    if name in VERSIONS:return struct.pack('>I',v)
    if name in TIMES:return struct.pack('>q',micros(v))
    if name=='identity_slots':return unhex(v)
    if name.endswith('_id'):return uuid.UUID(v).bytes
    return text(v)
def fingerprint(h):
    domain=b'FLOOOW/OFFLINE-FIELD-PROOF/BINDING/V1'
    b=struct.pack('>I',len(domain))+domain+struct.pack('>H',38)
    for tag,name in enumerate(FIELDS,1):
        p=b'\1'+typed(name,h[name]);b+=struct.pack('>HI',tag,len(p))+p
    return sha(b)
def slots(roles):
    b=struct.pack('>I',4)
    for i,(oid,name) in enumerate(roles,1):
        s=text(name);p=struct.pack('>BII',i,oid,len(s))+s;b+=struct.pack('>I',len(p))+p
    return b
def frozen_frames(values):
    out=b''
    for value in values:
        b=text(str(value));out+=struct.pack('>I',len(b))+b
    return out
def signature_preimage(keyid,spki,manifest):
    return frozen_frames(['FLOOOW:S2A:APPROVAL-SIGNATURE:1','Ed25519',keyid,sha(spki),sha(manifest)])
