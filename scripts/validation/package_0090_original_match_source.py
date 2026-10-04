"""Exact approved helper review, separately from table grant inventory."""
import json
from build_package_0090_original_match_source import NAME,TYPES,OWNER,GRANTS,build

def check(fn,source):
    from pglast.parser import parse_sql_json
    reference=json.loads(parse_sql_json(build(source)))['stmts'][0]['stmt']['CreateFunctionStmt']
    def clean(node):
        if isinstance(node,list):return [clean(v) for v in node]
        if isinstance(node,dict):return {k:clean(v) for k,v in node.items() if k!='location'}
        return node
    if clean(fn)!=clean(reference):raise ValueError('Exact original-match capability differs')
    body=next(o['DefElem']['arg']['List']['items'][0]['String']['sval'] for o in fn['options'] if o['DefElem']['defname']=='as')
    import re
    if re.search(r'\b(INSERT|UPDATE|DELETE|TRUNCATE|EXECUTE|COMMIT|ROLLBACK)\b',body,re.I):raise ValueError('Original-match effects forbidden')
    if 'slot_number=1 AND slot_name <> SESSION_USER' not in body:raise ValueError('Verifier identity guard missing')
    return {'mutation_original_match':'PASS_BOUNDED_SOURCE_NOT_RUNTIME'}
