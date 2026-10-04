"""Exact V bridge and private grant source review; no installed ACL claim."""
import json
from build_package_0090_v_bridge_source import NAME,TYPES,OWNER,GRANTS,MARKER,END_MARKER,build
from package_0090_capability_source import strings


def check(fn, source):
    from pglast.parser import parse_sql_json
    reference=json.loads(parse_sql_json(build()))['stmts'][3]['stmt']['CreateFunctionStmt']
    def clean(node):
        if isinstance(node,list):return [clean(v) for v in node]
        if isinstance(node,dict):return {k:clean(v) for k,v in node.items() if k!='location'}
        return node
    if clean(fn)!=clean(reference):raise ValueError('Exact V bridge signature/properties/delegation')
    body=source.split(MARKER,1)[1].split(END_MARKER,1)[0]
    if body!=build().split(MARKER,1)[1].split(END_MARKER,1)[0]:
        raise ValueError('Exact V native dependency precondition and narrow grant path')
    return dict(internal_v_bridge='PASS_BOUNDED_SOURCE_NOT_RUNTIME',
                a_direct_native_access=False,a_private_crypto_usage=False,
                new_native_execute_grants=1,new_bridge_execute_grants=1)
