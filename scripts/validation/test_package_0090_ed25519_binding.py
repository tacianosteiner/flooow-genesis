"""Native SQL binding/ACL source checks, never installed catalog proof."""
import unittest
from pathlib import Path
from pglast.parser import parse_sql_json
import json
from package_0090_capability_source import strings

PATH=Path(__file__).resolve().parents[2]/'applications/marketplace-operations-persistence-postgres/native/flooow_offline_mac32/flooow_offline_mac32--1.0.sql'
NAME=('offline_crypto','canonical_spki_ed25519_verify')


def check(source):
    stmts=[s['stmt'] for s in json.loads(parse_sql_json(source))['stmts']]
    defs=[s['CreateFunctionStmt'] for s in stmts if 'CreateFunctionStmt' in s]
    if len(defs)!=2 or {strings(f['funcname']) for f in defs}!={NAME,('offline_crypto','timing_safe_equal32')}:
        raise ValueError('Exact two-member native package')
    fn=next(f for f in defs if strings(f['funcname'])==NAME)
    params=[p['FunctionParameter'] for p in fn['parameters']]
    if fn.get('replace') or len(params)!=3 or any(p.get('name') or p.get('defexpr') or p['mode']!='FUNC_PARAM_DEFAULT'
            or strings(p['argType']['names'])!=('pg_catalog','bytea') for p in params):
        raise ValueError('Exact unnamed three-bytea signature')
    if strings(fn['returnType']['names'])!=('pg_catalog','bool') or fn['returnType'].get('setof'):
        raise ValueError('Exact scalar bool')
    opts={o['DefElem']['defname']:o['DefElem']['arg'] for o in fn['options']}
    expected={'language':{'String':{'sval':'c'}},'volatility':{'String':{'sval':'immutable'}},
              'strict':{'Boolean':{'boolval':True}},'security':{'Boolean':{'boolval':False}},
              'parallel':{'String':{'sval':'safe'}},'as':{'List':{'items':[
                  {'String':{'sval':'MODULE_PATHNAME'}},{'String':{'sval':NAME[1]}}]}}}
    if opts!=expected:raise ValueError('Exact native C properties and symbol')
    grants=[s['GrantStmt'] for s in stmts if 'GrantStmt' in s]
    if len(stmts)!=3 or len(grants)!=1:raise ValueError('No extra native binding effects')
    revoke=grants[0]
    if revoke.get('is_grant') or revoke.get('grant_option') or revoke.get('privileges') or revoke['objtype']!='OBJECT_FUNCTION':
        raise ValueError('Revoke all native PUBLIC privileges only')
    if revoke['grantees']!=[{'RoleSpec':{'roletype':'ROLESPEC_PUBLIC','location':revoke['grantees'][0]['RoleSpec']['location']}}]:
        raise ValueError('Exact PUBLIC revoke')
    if len(revoke['objects'])!=1:raise ValueError('Exact revoke object')
    obj=revoke['objects'][0]['ObjectWithArgs']
    if strings(obj['objname'])!=NAME or tuple(strings(t['TypeName']['names']) for t in obj['objargs'])!=(('pg_catalog','bytea'),)*3:
        raise ValueError('Exact native revoke signature')
    return True


class NativeBindingTests(unittest.TestCase):
    def test_exact_binding(self):self.assertTrue(check(PATH.read_text()))
    def test_public_grant_denied(self):
        with self.assertRaises(ValueError):check(PATH.read_text().replace('REVOKE ALL PRIVILEGES','GRANT ALL PRIVILEGES').replace('FROM PUBLIC','TO PUBLIC'))
    def test_a_direct_access_denied(self):
        with self.assertRaises(ValueError):check(PATH.read_text()+'\nGRANT EXECUTE ON FUNCTION offline_crypto.canonical_spki_ed25519_verify(bytea,bytea,bytea) TO flooow_offline_audit_owner;')
    def test_algorithm_selector_denied(self):
        with self.assertRaises(ValueError):check(PATH.read_text().replace('    pg_catalog.bytea\n)','    pg_catalog.text\n)'))
    def test_definer_native_denied(self):
        with self.assertRaises(ValueError):check(PATH.read_text().replace('SECURITY INVOKER','SECURITY DEFINER'))
    def test_null_and_mutability_changes_denied(self):
        for old,new in [('STRICT','CALLED ON NULL INPUT'),('IMMUTABLE','VOLATILE')]:
            with self.assertRaises(ValueError):check(PATH.read_text().replace(old,new))


if __name__=='__main__':unittest.main()
