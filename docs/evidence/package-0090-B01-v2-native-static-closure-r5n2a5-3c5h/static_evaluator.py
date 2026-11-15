"""Evidence-only frozen predicate interpreter; no IO and no expected-result input.

This evaluates normalized typed inputs, not a PostgreSQL/native implementation.
Absent operands stay UNAVAILABLE, distinct from the domain string UNKNOWN.
Canonical fixture completeness and normalization provenance are caller gates.
"""
import collections
import re

class Unavailable(Exception):
    pass

def same(a,b):
    if type(a) is not type(b): raise Unavailable('Exact source types differ')
    if isinstance(a,dict):
        return a.keys()==b.keys() and all(same(a[k],b[k]) for k in a)
    if isinstance(a,list):
        return len(a)==len(b) and all(same(x,y) for x,y in zip(a,b))
    return a==b

def split_top(s,separator):
    depth=0; start=0; result=[]; i=0
    while i<len(s):
        c=s[i]
        if c in '([': depth+=1
        elif c in ')]': depth-=1
        if depth==0 and s.startswith(separator,i):
            result.append(s[start:i].strip());i+=len(separator);start=i;continue
        i+=1
    result.append(s[start:].strip())
    return result

def parse(s):
    for sep,op in [(' OR ','OR'),(' AND ','AND')]:
        parts=split_top(s,sep)
        if len(parts)>1:return {'op':op,'args':[parse(x) for x in parts]}
    if s.startswith('NOT '):return {'op':'NOT','args':[parse(s[4:].strip())]}
    match=re.fullmatch(r'([A-Z_]+)\((.*)\)',s)
    if match:
        op=match[1];parts=split_top(match[2],',')
        if op in ['REL','OID'] and len(parts)==1 and parts[0].startswith('pg_catalog.'):
            return {'op':op,'args':[{'literal':parts[0]}]}
        return {'op':op,'args':[parse(x) for x in parts]}
    for sep,op in [('<=','LE'),('=','EQ')]:
        parts=split_top(s,sep)
        if len(parts)==2:return {'op':op,'args':[parse(x) for x in parts]}
    parts=split_top(s,'-')
    if len(parts)==2:return {'op':'SUB','args':[parse(x) for x in parts]}
    if s in {'TRUE','FALSE','EMPTY','UNKNOWN','ACTIVE','PRE_ENROLLMENT_PROVISION','HOST_ROOT','INVOKER_ONLY','EXACT_FROZEN_IDENTITY','SET','INHERIT','FUNCTION','EXECUTE','UPDATE'}:
        return {'literal':{'TRUE':True,'FALSE':False,'EMPTY':[]}.get(s,s)}
    return {'input':s}

def require(env,k):
    if k not in env or env[k] is None:raise Unavailable(k)
    return env[k]

def truth(v):
    if type(v) is not bool:raise Unavailable('Not a boolean observation')
    return v

def closure(edges,kind,start):
    reached=[start];pending=[start]
    while pending:
        a=pending.pop()
        for e in edges:
            if e['kind']==kind and same(e['source'],a) and not any(same(e['target'],x) for x in reached):
                reached.append(e['target']);pending.append(e['target'])
    return reached

def reachable_roles(rows,kind,start):
    edges=[]
    for r in rows:
        # All projected fields must be supplied; preserve distinct options.
        for k in ['oid','roleid','member','grantor','admin_option','inherit_option','set_option']:r[k]
        if kind=='MEMBER' or truth(r[{'SET':'set_option','INHERIT':'inherit_option'}[kind]]):
            edges.append({'kind':kind,'source':r['member'],'target':r['roleid']})
    return closure(edges,kind,start)

def role(env,identity):
    rows=require(env,'catalog.pg_roles')
    matches=[r for r in rows if same(r['oid'],identity)]
    if len(matches)!=1:raise Unavailable('Exact role identity missing/duplicated')
    return matches[0]

def acl_has(rows,grantee,privilege):
    return any(same(r['grantee'],grantee) and same(r['privilege'],privilege) for r in rows)

def run(node,env):
    if 'literal' in node:return node['literal']
    if 'input' in node:return require(env,node['input'])
    op=node['op'];args=node['args']
    # Never turn an absent operand into false, even if another conjunct decides.
    a=[run(x,env) for x in args]
    if op in ['EQ','NE']:return same(a[0],a[1]) == (op=='EQ')
    if op in ['LT','GT','LE','SUB']:
        if any(type(x) is not int for x in a):raise Unavailable('Integer operands required')
        return {'LT':lambda:a[0]<a[1],'GT':lambda:a[0]>a[1],'LE':lambda:a[0]<=a[1],'SUB':lambda:a[0]-a[1]}[op]()
    if op=='AND':return all([truth(x) for x in a])
    if op=='OR':return any([truth(x) for x in a])
    if op=='NOT':return not truth(a[0])
    if op=='IN':return any(same(a[0],x) for x in a[1])
    if op=='ALL_EQ':
        if not a[0]:raise Unavailable('No source collection identities')
        return all(same(a[0][0],x) for x in a[0])
    if op=='MISSING':
        evidence=a[0]
        # Must compare complete natural-key rows; no supplied 'missing' boolean.
        key=evidence['expected_key'];fields=evidence['key_fields']
        return not any(same([r[k] for k in fields],key) for r in evidence['rows'])
    if op=='BIJECTION':
        left,right=a
        return len(left)==len(right) and all(sum(same(x,y) for y in left)==1 and sum(same(x,y) for y in right)==1 for x in left+right)
    if op=='EXISTS_DUPLICATE_NATURAL_KEY':
        evidence=a[0];keys=[[r[k] for k in evidence['key_fields']] for r in evidence['rows']]
        return any(same(x,y) for i,x in enumerate(keys) for y in keys[i+1:])
    if op=='IS_EXPECTED_ROLE':return same(a[0]['oid'],a[1]['oid']) and same(a[0]['rolname'],a[1]['name'])
    if op in ['HAS_CREATEROLE','IS_SUPERUSER','HAS_BYPASSRLS']:
        return truth(role(env,a[0])[{'HAS_CREATEROLE':'rolcreaterole','IS_SUPERUSER':'rolsuper','HAS_BYPASSRLS':'rolbypassrls'}[op]])
    if op=='REACHABLE':
        # Provider implicit pg_database_owner edges must also be independently
        # normalized, even when pg_auth_members has no corresponding row.
        if 'normalized_implicit_database_owner_edges' not in env:raise Unavailable('Missing implicit database-owner edge normalization')
        if env['normalized_implicit_database_owner_edges']:raise Unavailable('Implicit owner graph composition not implemented')
        return any(same(a[2],x) for x in reachable_roles(require(env,'catalog.pg_auth_members'),a[0],a[1]))
    if op=='HAS_ADMIN_OPTION':
        member,target=a
        if same(member,target):return False
        if truth(role(env,member)['rolsuper']):return True
        if 'normalized_implicit_database_owner_edges' not in env or env['normalized_implicit_database_owner_edges']:raise Unavailable('Missing implicit owner MEMBER normalization')
        reach=reachable_roles(require(env,'catalog.pg_auth_members'),'MEMBER',member)
        return any(any(same(r['member'],x) for x in reach) and same(r['roleid'],target) and truth(r['admin_option']) for r in require(env,'catalog.pg_auth_members'))
    if op=='IS_OBJECT_OWNER':return same(role(env,a[0])['oid'],a[1]['owner_oid'])
    if op=='REL':return a[0]
    if op=='OID':return require(env,'frozen_object_oids')[a[0]]
    if op=='RESOLVED_OID':
        return a[0][{'EXACT_FROZEN_IDENTITY':'relation_oid','NAMESPACE_NAME_LOOKUP':'resolved_relation_oid'}[a[0]['kind']]]
    if op=='HAS_PUBLIC_PRIVILEGE':return acl_has(require(env,'object_acls')[a[1]],0,a[2])
    if op in ['FIXED_SOURCE_OPERATION_ALLOWS','FIXED_SOURCE_ALLOWS']:
        return any(same(a[0],x) for x in require(env,'fixed_source_operation_allowlist' if op=='FIXED_SOURCE_OPERATION_ALLOWS' else 'fixed_source_callable_allowlist'))
    if op=='EXISTS_EFFECTIVE_CREATOR_DEFAULT':
        creator,namespace,kind,grantee,priv=a
        rows=require(env,'catalog.pg_default_acl');global_rows=[r for r in rows if same(r['defaclrole'],creator) and r['defaclnamespace']==0 and same(r['object_kind'],kind)]
        schema_rows=[r for r in rows if same(r['defaclrole'],creator) and same(r['defaclnamespace'],namespace) and same(r['object_kind'],kind)]
        if len(global_rows)>1 or len(schema_rows)>1:raise Unavailable('Duplicate default natural key')
        # Explicit global rows or independently source-expanded hardwired defaults.
        global_acl=global_rows[0]['acl_entries'] if global_rows else require(env,'source_hardwired_defaults')[kind]
        schema_acl=schema_rows[0]['acl_entries'] if schema_rows else []
        if global_acl is None:raise Unavailable('NULL ACL needs source expansion')
        return same(creator,grantee) or acl_has(global_acl+schema_acl,grantee,priv) or acl_has(global_acl+schema_acl,0,priv)
    if op=='HAS_SECURITY_DEFINER_PATH':
        raise Unavailable('Requires full caller execute/schema usage, owner and verified body/effect graph; no prosecdef-only shortcut')
    if op=='HAS_UNEXPECTED_WRITE_PATH':
        raise Unavailable('Requires full source-expanded effect reachability and admission normalization; no direct-leaf shortcut')
    raise Unavailable('Unsupported frozen operator '+op)

def observe(program,inputs):
    """Predicate observation only. Never emits a witness PROVEN classification."""
    try:return {'availability':'AVAILABLE','value':run(program,inputs)}
    except (Unavailable,KeyError,TypeError,ValueError,IndexError) as exc:
        return {'availability':'UNAVAILABLE','value':None,'reason':str(exc)}

def inputs_for(program):
    if 'input' in program:return [program['input']]
    return sorted({k for x in program.get('args',[]) for k in inputs_for(x)})

def dependencies_for(program):
    hidden={
        'HAS_CREATEROLE':['catalog.pg_roles'],
        'IS_SUPERUSER':['catalog.pg_roles'],
        'HAS_BYPASSRLS':['catalog.pg_roles'],
        'IS_OBJECT_OWNER':['catalog.pg_roles'],
        'REACHABLE':['catalog.pg_auth_members','normalized_implicit_database_owner_edges'],
        'HAS_ADMIN_OPTION':['catalog.pg_roles','catalog.pg_auth_members','normalized_implicit_database_owner_edges'],
        'OID':['frozen_object_oids'],
        'HAS_PUBLIC_PRIVILEGE':['object_acls'],
        'FIXED_SOURCE_OPERATION_ALLOWS':['fixed_source_operation_allowlist'],
        'FIXED_SOURCE_ALLOWS':['fixed_source_callable_allowlist'],
        'EXISTS_EFFECTIVE_CREATOR_DEFAULT':['catalog.pg_default_acl','source_hardwired_defaults'],
        'HAS_SECURITY_DEFINER_PATH':['catalog.pg_proc','catalog.pg_namespace','catalog.pg_auth_members','verified_call_effect_graph','full_caller_execute_schema_usage_owner_proof'],
        'HAS_UNEXPECTED_WRITE_PATH':['verified_source_expanded_effect_graph','expected_effect_allowlist','effect_reachability_and_admission_proof']}
    return sorted(set(inputs_for(program))|{k for op in operators_for(program) for k in hidden.get(op,[])})

def operators_for(program):
    return sorted({program['op']}|{k for x in program['args'] for k in operators_for(x)}) if 'op' in program else []
