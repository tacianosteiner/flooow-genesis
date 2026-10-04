"""Exact, narrow original-input table/trigger source review."""
import json
from build_package_0090_expected_attestation_source import build, NAME, OWNER, TYPES

def check(statements, source):
    from pglast.parser import parse_sql_json
    def clean(value):
        if isinstance(value,dict): return {k:clean(v) for k,v in value.items() if k not in ('location','stmt_location','stmt_len')}
        if isinstance(value,list): return [clean(v) for v in value]
        return value
    expected=[x['stmt'] for x in json.loads(parse_sql_json(build()))['stmts']]
    def relevant(s):
        if 'CreateFunctionStmt' in s:
            return s['CreateFunctionStmt']['funcname']==[{'String':{'sval':'public'}},{'String':{'sval':NAME}}]
        if 'CreateTrigStmt' in s: return s['CreateTrigStmt']['trigname'].startswith(('offline_expected_original_input_', 'offline_header_original_input_'))
        if 'CreateStmt' in s: return s['CreateStmt']['relation']['relname']=='offline_expected_signed_attestation'
        if 'AlterTableStmt' in s:
            a=s['AlterTableStmt']
            return a['relation']['relname']=='offline_expected_signed_attestation' or any(c.get('AlterTableCmd',{}).get('def',{}).get('Constraint',{}).get('conname')=='offline_header_original_input_required' for c in a.get('cmds',[]))
        return False
    observed=[s for s in statements if relevant(s)]
    reference=[s for s in expected if relevant(s)]
    if clean(observed)!=clean(reference): raise ValueError('Original-input table/atomicity/immutability guard changed')
    triggers=[s['CreateTrigStmt'] for s in statements if 'CreateTrigStmt' in s]
    if clean(triggers)!=clean([s['CreateTrigStmt'] for s in expected if 'CreateTrigStmt' in s]):
        raise ValueError('Unapproved trigger capability')
    return {'expected_attestation_source':'BOUNDED_STATIC_PASS_NOT_RUNTIME_PROOF',
            'expected_attestation_atomicity':'DEFERRED_REVERSE_FK',
            'expected_attestation_immutability':'UPDATE_DELETE_TRUNCATE_DENIED'}
