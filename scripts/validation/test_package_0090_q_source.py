"""Offline Q AST/negative contracts and generated SQL expression golden parity.

The tiny evaluator covers pure frame expressions only, never SQL queries/crypto.
"""
import hashlib
import hmac
import json
import struct
import unittest
import uuid

import package_0090_source_gate as gate
import package_0090_catalog_goldens as goldens


def evaluate(node, env):
    if 'A_Const' in node:
        c=node['A_Const']
        if c.get('isnull'):return None
        for k in ('sval','ival','fval','boolval'):
            if k in c:return c[k][k]
    if 'TypeCast' in node:
        cast=node['TypeCast']; value=evaluate(cast['arg'],env)
        if value is None:return None
        t=cast['typeName']['names'][-1]['String']['sval']
        if t=='bytea' and isinstance(value,str):return bytes.fromhex(value[2:])
        if t in ('int8','int4'):return int(value)
        return value
    if 'ParamRef' in node:return env['$'+str(node['ParamRef']['number'])]
    if 'ColumnRef' in node:
        return env['.'.join(f['String']['sval'] for f in node['ColumnRef']['fields'])]
    if 'NullTest' in node:
        c=node['NullTest']; null=evaluate(c['arg'],env) is None
        return null if c['nulltesttype']=='IS_NULL' else not null
    if 'CaseExpr' in node:
        c=node['CaseExpr']
        for raw in c['args']:
            when=raw['CaseWhen']
            if evaluate(when['expr'],env) is True:return evaluate(when['result'],env)
        return evaluate(c['defresult'],env)
    if 'A_Expr' in node:
        x=node['A_Expr']; a=evaluate(x['lexpr'],env); b=evaluate(x['rexpr'],env)
        if a is None or b is None:return None
        name=x['name'][-1]['String']['sval']
        if name=='||':return a+b
        if name=='+':return a+b
        if name=='-':return a-b
        if name=='*':return a*b
        if name=='<>':return a!=b
        if name=='=':return a==b
    if 'FuncCall' in node:
        x=node['FuncCall']; name=x['funcname'][-1]['String']['sval']
        args=[evaluate(a,env) for a in x.get('args',[])]
        if any(a is None for a in args):return None
        if name=='convert_to':return args[0].encode('utf-8')
        if name=='octet_length':return len(args[0])
        if name=='int4send':return struct.pack('>i',args[0])
        if name=='int8send':return struct.pack('>q',args[0])
        if name=='uuid_send':return args[0].bytes
        if name=='substring':return args[0][args[1]-1:args[1]-1+args[2]]
    raise ValueError('Unsupported pure AST '+repr(node))


def parse_receipt(receipt, key_version=1, now=1, ttl=1000000, scope=None):
    """Independent normative oracle; not execution of the PL/pgSQL function."""
    domain=b'FLOOOW/OFFLINE-FIELD-PROOF/PREFLIGHT/V1'
    cursor=4+len(domain)+2
    if receipt[:4]!=struct.pack('>I',len(domain)) or receipt[4:4+len(domain)]!=domain or receipt[cursor-2:cursor]!=b'\x00\x09':
        raise ValueError('ACCESS_DENIED')
    fields=[]
    lengths=(16,32,7,32,32,32,8,8,4)
    for tag,length in enumerate(lengths,1):
        if len(receipt)<cursor+6:raise ValueError('ACCESS_DENIED')
        actual,size=struct.unpack('>HI',receipt[cursor:cursor+6]);cursor+=6
        payload=receipt[cursor:cursor+size];cursor+=size
        if actual!=tag or size!=length+1 or len(payload)!=size or payload[:1]!=b'\x01':raise ValueError('ACCESS_DENIED')
        fields.append(payload[1:])
    if len(receipt)-cursor!=32 or struct.unpack('>I',fields[8])[0]!=key_version or key_version<=0:
        raise ValueError('ACCESS_DENIED')
    key=bytes(range(32))
    if not hmac.compare_digest(hmac.digest(key,receipt[:cursor],'sha256'),receipt[cursor:]):raise ValueError('ACCESS_DENIED')
    issued,expiry=(struct.unpack('>q',fields[n])[0] for n in (6,7))
    if expiry!=issued+ttl or expiry<=issued or not issued<=now<expiry:raise ValueError('ACCESS_DENIED')
    if scope is not None and fields[:6]!=scope:raise ValueError('ACCESS_DENIED')
    return receipt


class QSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source=(gate.ROOT/gate.V043).read_text(encoding='utf-8-sig')
        cls.spec=(gate.ROOT/gate.SPEC).read_text(encoding='utf-8-sig')
        cls.expected=gate.expected_column_grants(cls.spec)
        cls.statements,_=gate.parse(cls.source)
        cls.fn=next(s['CreateFunctionStmt'] for s in cls.statements if s.get('CreateFunctionStmt',{}).get('funcname')==
            [{'String':{'sval':'public'}},{'String':{'sval':'offline_internal_readiness'}}])
        cls.gold=goldens.generate()
        cls.receipt=bytes.fromhex(cls.gold['preflight_receipt']['hex'])

    def reject(self, before, after):
        import copy
        import package_0090_q_source as q
        fn=copy.deepcopy(self.fn)
        option=next(o['DefElem'] for o in fn['options'] if o['DefElem']['defname']=='as')
        body=option['arg']['List']['items'][0]['String']['sval']
        self.assertIn(before,body)
        option['arg']['List']['items'][0]['String']['sval']=body.replace(before,after,1)
        with self.assertRaises(ValueError):q.check(fn,self.expected)

    def test_exact_security_signature_and_reads(self):
        import package_0090_q_source as q
        self.assertEqual(q.check(self.fn,self.expected)['internal_q_source'],'BOUNDED_STATIC_PASS_NOT_RUNTIME_PROOF')

    def test_deployment_missing_connection_column(self):
        self.reject("('flooow_offline_audit_owner','integration_connection','status','SELECT'),",'')

    def test_deployment_extra_connection_column(self):
        self.reject("('flooow_offline_audit_owner','integration_connection','status','SELECT'),",
                    "('flooow_offline_audit_owner','integration_connection','status','SELECT'),('flooow_offline_audit_owner','integration_connection','secret_ref','SELECT'),")

    def test_deployment_duplicate_connection_column(self):
        row="('flooow_offline_audit_owner','integration_connection','status','SELECT'),"
        self.reject(row,row+row)

    def test_deployment_wrong_connection_privilege(self):
        self.reject("('flooow_offline_audit_owner','integration_connection','status','SELECT')",
                    "('flooow_offline_audit_owner','integration_connection','status','UPDATE')")

    def test_sentinel_only_auditor(self):self.reject('IF pg_catalog.octet_length($8)<>0','IF false')
    def test_executor_cannot_use_sentinel(self):self.reject('IF pg_catalog.octet_length($8)=0','IF false')
    def test_authenticated_route(self):self.reject('IF SESSION_USER=slot_names[4] THEN','IF CURRENT_USER=slot_names[4] THEN')
    def test_non_renewal(self):self.reject('RETURN $8;','RETURN receipt_frame||receipt_mac;')
    def test_no_key_projection(self):self.reject('RETURN $8;','RETURN key_record.key_material;')
    def test_active_key(self):self.reject("k.key_state='ACTIVE'","k.key_state='RETIRED'")
    def test_active_version(self):self.reject('IF mac_version<>key_record.key_version THEN','IF false THEN')
    def test_timing_safe_is_true(self):self.reject('cursor_position+1,32)::pg_catalog.bytea) IS NOT TRUE','cursor_position+1,32)::pg_catalog.bytea) IS FALSE')
    def test_original_expiry_derivation(self):self.reject('issued_us+policy_values[27]<>expires_us','false')
    def test_db_clock_only(self):self.reject('now_us := EXTRACT(EPOCH FROM pg_catalog.clock_timestamp())*1000000;','now_us := EXTRACT(EPOCH FROM pg_catalog.transaction_timestamp())*1000000;')
    def test_no_ttl_fallback(self):self.reject('expires_us := issued_us+policy_values[27];','expires_us := issued_us+COALESCE(policy_values[27],1000000);')
    def test_no_guc_policy(self):self.reject('expires_us := issued_us+policy_values[27];',"expires_us := issued_us+pg_catalog.current_setting('app.ttl')::pg_catalog.int8;")
    def test_history_is_live(self):self.reject('live_history<>ready_record.history_manifest OR pg_catalog.sha256(live_history)<>$5','false')
    def test_acl_is_live(self):self.reject('live_acl<>ready_record.acl_manifest OR pg_catalog.sha256(live_acl)<>$6','false')
    def test_no_write_lock(self):self.reject("WHERE k.incarnation_id=$3 AND k.key_state='ACTIVE';","WHERE k.incarnation_id=$3 AND k.key_state='ACTIVE' FOR UPDATE;")
    def test_no_domain_read(self):self.reject('h.valid_from,h.expires_at','h.organization_id,h.expires_at')
    def test_no_dml(self):self.reject('RETURN $8;','DELETE FROM public.offline_preflight_key; RETURN $8;')

    def test_sql_frame_matches_independent_python_jvm_golden(self):
        from pglast.parser import parse_sql_json
        body=next(o['DefElem']['arg']['List']['items'][0]['String']['sval'] for o in self.fn['options'] if o['DefElem']['defname']=='as')
        expression=body.rsplit('receipt_frame := ',1)[1].split(';',1)[0]
        ast=json.loads(parse_sql_json('SELECT '+expression))['stmts'][0]['stmt']['SelectStmt']['targetList'][0]['ResTarget']['val']
        frame=bytes.fromhex(self.gold['preflight']['hex'])
        fields=[];cursor=4+len(b'FLOOOW/OFFLINE-FIELD-PROOF/PREFLIGHT/V1')+2
        for _ in range(9):
            _,n=struct.unpack('>HI',frame[cursor:cursor+6]);cursor+=6;fields.append(frame[cursor+1:cursor+n]);cursor+=n
        env={'$3':uuid.UUID(bytes=fields[0]),'$2':fields[1],'$4':'0090-v1','$5':fields[3],'$6':fields[4],
             '$7':fields[5],'issued_us':1,'expires_us':1000001,'key_record.key_version':1}
        self.assertEqual(evaluate(ast,env),frame)
        self.assertEqual(hmac.digest(bytes(range(32)),evaluate(ast,env),'sha256').hex(),self.gold['hmac_sha256_hex'])

    def test_original_valid_receipt_unchanged(self):self.assertIs(parse_receipt(self.receipt),self.receipt)
    def test_expiry_equality_denied(self):
        with self.assertRaises(ValueError):parse_receipt(self.receipt,now=1000001)
    def test_future_issued_denied(self):
        with self.assertRaises(ValueError):parse_receipt(self.receipt,now=0)
    def test_stale_unknown_key_denied(self):
        for version in (0,2,4294967295):
            with self.subTest(version=version),self.assertRaises(ValueError):parse_receipt(self.receipt,key_version=version)
    def test_malformed_mac_frame_denied(self):
        for bad in (b'',self.receipt[:-1],self.receipt+b'\0',b'\0'+self.receipt,self.receipt[:-32]+b'\0'*32):
            with self.subTest(length=len(bad)),self.assertRaises(ValueError):parse_receipt(bad)
    def test_policy_drift_no_fallback(self):
        with self.assertRaises(ValueError):parse_receipt(self.receipt,ttl=1000001)
    def test_foreign_nonexistent_scope_same_denial(self):
        for scope in ([b'foreign']*6,[b'nonexistent']*6):
            with self.assertRaisesRegex(ValueError,'^ACCESS_DENIED$'):parse_receipt(self.receipt,scope=scope)

    def test_reordered_unknown_null_fields(self):
        cursor=4+len(b'FLOOOW/OFFLINE-FIELD-PROOF/PREFLIGHT/V1')+2
        for offset,value in ((cursor+1,2),(cursor+1,99),(cursor+6,0)):
            bad=bytearray(self.receipt);bad[offset]=value
            with self.subTest(offset=offset,value=value),self.assertRaises(ValueError):parse_receipt(bytes(bad))

    def test_exact_acl_owner_and_usage(self):
        signature='pg_catalog.uuid,pg_catalog.bytea,pg_catalog.uuid,pg_catalog.text,pg_catalog.bytea,pg_catalog.bytea,pg_catalog.bytea,pg_catalog.bytea'
        for bad in (
            self.source+'\nGRANT EXECUTE ON FUNCTION public.offline_internal_readiness('+signature+') TO flooow_offline_issuance_owner;',
            self.source.replace('ALTER FUNCTION public.offline_internal_readiness('+signature+') OWNER TO flooow_offline_readiness_owner;',
                'ALTER FUNCTION public.offline_internal_readiness('+signature+') OWNER TO flooow_offline_execution_owner;'),
            self.source.replace('GRANT USAGE ON SCHEMA public TO flooow_offline_readiness_owner;',''),
        ):
            with self.assertRaises(ValueError):gate.prerequisite_checks(bad,self.spec)


if __name__=='__main__':unittest.main()
