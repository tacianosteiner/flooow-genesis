"""Evidence-only normalized local operators. No IO or expected-result input.

Contracts assume source-authenticated/exhaustive normalized relations/manifests;
structural checks and digest equality do NOT authenticate them or prove SQL body
effects. Canonical binding and parent fixture proof remain separate gates.
"""
from collections import deque
import unicodedata

class Unavailable(Exception):pass
def require(ok,why):
    if not ok:raise Unavailable(why)
def oid(x,public=False):
    require(type(x) is int and (0 if public else 1)<=x<2**32,'Exact source OID required')
    return x
def text(x):
    require(type(x) is str and x and '\0' not in x and unicodedata.normalize('NFC',x)==x,'Canonical source text required')
    try:x.encode('utf-8','strict')
    except UnicodeError as exc:raise Unavailable('Invalid UTF8') from exc
def digest(x,nullable=False):
    if x is None and nullable:return
    require(type(x) is str and len(x)==64 and all(c in '0123456789abcdef' for c in x),'Normalized source bytes32 hex required')
def boolean(x):require(type(x) is bool,'Source boolean required')
def exact(obj,keys):require(type(obj) is dict and set(obj)==set(keys),'Exact normalized record keys required')
def rows(table,key='oid'):
    require(type(table) is list,'Duplicate-preserving source list required')
    found={}
    for r in table:
        require(type(r) is dict and key in r,'Source row missing key');v=oid(r[key]);require(v not in found,'Duplicate natural key, not silently deduplicated');found[v]=r
    return found

def role_context(data):
    exact(data,['roles','inherit_edges'])
    roles=rows(data['roles'])
    for r in roles.values():
        exact(r,['oid','rolname','rolsuper']);text(r['rolname']);boolean(r['rolsuper'])
    require(type(data['inherit_edges']) is list,'Normalized typed INHERIT edges missing')
    for edge in data['inherit_edges']:
        exact(edge,['member','roleid','source_row_oid','source_kind'])
        require(oid(edge['member']) in roles and oid(edge['roleid']) in roles,'Role endpoint missing')
        require(edge['source_kind'] in ['EXPLICIT_INHERIT_OPTION','IMPLICIT_CURRENT_DATABASE_OWNER'],'No merged edge type')
        if edge['source_kind']=='EXPLICIT_INHERIT_OPTION':oid(edge['source_row_oid'])
        else:require(edge['source_row_oid'] is None,'Implicit edge is not catalog membership row')
    return roles

def inherited(data,role):
    roles=role_context(data);require(oid(role) in roles,'Role not bound')
    result={role};pending=[role]
    while pending:
        current=pending.pop()
        for edge in data['inherit_edges']:
            if edge['member']==current and edge['roleid'] not in result:result.add(edge['roleid']);pending.append(edge['roleid'])
    return result

def acl(entries,role_ids,allowed):
    require(type(entries) is list,'Normalized exploded ACL list required')
    for entry in entries:
        exact(entry,['grantor','grantee','privilege','is_grantable'])
        require(oid(entry['grantor']) in role_ids,'Grantor reference missing');oid(entry['grantee'],True)
        require(entry['grantee']==0 or entry['grantee'] in role_ids,'ACL grantee reference missing')
        require(entry['privilege'] in allowed,'Privilege outside source object kind');boolean(entry['is_grantable'])
    return entries

def function_default(owner):
    return [{'grantor':owner,'grantee':g,'privilege':'EXECUTE','is_grantable':False} for g in [0,owner]]
def schema_default(owner):
    return [{'grantor':owner,'grantee':owner,'privilege':p,'is_grantable':False} for p in ['CREATE','USAGE']]

PROC_FIELDS=['oid','proname','pronamespace','proowner','prolang','prokind','prosecdef','proisstrict','proretset','provolatile','proparallel','pronargs','pronargdefaults','prorettype','proargtypes','proallargtypes','proargmodes','proargnames','proconfig','proacl','prosrc_sha256','probin_sha256','prosqlbody_sha256']
def proc_projection(value):
    exact(value,PROC_FIELDS)
    for k in ['oid','pronamespace','proowner','prolang','prorettype']:oid(value[k])
    text(value['proname'])
    require(value['prokind']=='f' and value['provolatile'] in ['i','s','v'] and value['proparallel'] in ['s','r','u'],'Frozen FUNCTION projection enums required')
    for k in ['prosecdef','proisstrict','proretset']:boolean(value[k])
    require(type(value['pronargs']) is int and 0<=value['pronargs']<2**15,'Source int2 argument count required')
    require(type(value['pronargdefaults']) is int and 0<=value['pronargdefaults']<=value['pronargs'],'Source default-argument count required')
    require(type(value['proargtypes']) is list and len(value['proargtypes'])==value['pronargs'],'Exact argument type vector required')
    for arg in value['proargtypes']:oid(arg)
    for k in ['proallargtypes','proargmodes','proargnames','proconfig']:
        require(value[k] is None or type(value[k]) is list,'NULL/array presence must be preserved')
    if value['proallargtypes'] is not None:
        for arg in value['proallargtypes']:oid(arg)
    if value['proargmodes'] is not None:
        require(all(x in ['i','o','b','v','t'] for x in value['proargmodes']),'Source argument modes required')
    for k in ['proargnames','proconfig']:
        if value[k] is not None:
            for x in value[k]:
                require(type(x) is str,'Exact source text array required')
                if x:text(x)
    digest(value['prosrc_sha256']);digest(value['probin_sha256'],True);digest(value['prosqlbody_sha256'],True)
    require(value['proacl'] is None or type(value['proacl']) is list,'Source ACL array/NULL required')
    if value['proacl'] is not None:
        for entry in value['proacl']:
            exact(entry,['grantor','grantee','privilege','is_grantable']);oid(entry['grantor']);oid(entry['grantee'],True)
            require(entry['privilege']=='EXECUTE','FUNCTION ACL privilege required');boolean(entry['is_grantable'])

FUNCTION_IDENTITY=['projected_pg_proc','source_effect_manifest_identity','source_capability_version','qualification_context_identity']
def function_identity(value):
    exact(value,FUNCTION_IDENTITY)
    proc_projection(value['projected_pg_proc']);digest(value['source_effect_manifest_identity']);text(value['source_capability_version']);digest(value['qualification_context_identity'])

def admission_entry(value):
    require(type(value) is dict and 'kind' in value,'Source-domain-tagged allowlist entry required')
    if value['kind']=='SOURCE_PRIMITIVE':
        exact(value,['kind','callable_id','source_capability_version']);text(value['callable_id']);text(value['source_capability_version'])
    elif value['kind']=='SQL_FUNCTION':
        exact(value,['kind','identity']);function_identity(value['identity'])
    else:raise Unavailable('Unknown source admission identity domain')

def ordinary_permission(context,role,owner,entries,privilege,kind):
    roles=role_context(context);require(oid(owner) in roles,'Owner reference missing')
    effective=inherited(context,role)
    if entries is None:entries=function_default(owner) if kind=='FUNCTION' else schema_default(owner)
    entries=acl(entries,roles,{'EXECUTE'} if kind=='FUNCTION' else {'CREATE','USAGE'})
    # Ownership grants implicit GRANT OPTIONS, not ordinary privileges after
    # an explicit-empty ACL. Provider object wrappers separately admit superuser.
    return roles[role]['rolsuper'] or any(e['privilege']==privilege and (e['grantee']==0 or e['grantee'] in effective) for e in entries)

def future_default(data):
    exact(data,['role_context','default_acl_rows','creator','namespace','grantee','creation','fixed_source_allowlist'])
    context=data['role_context'];roles=role_context(context);creator=oid(data['creator']);grantee=oid(data['grantee']);ns=oid(data['namespace'])
    require(creator in roles and grantee in roles,'Actual creator/Reader reference missing')
    require(not roles[grantee]['rolsuper'],'Frozen Reader default-path domain is nonsuperuser; a bypass is not a default-ACL path')
    exact(data['creation'],['creator','namespace','kind','callable_identity'])
    creation=data['creation'];oid(creation['creator']);oid(creation['namespace']);require(creation['creator']==creator and creation['namespace']==ns and creation['kind']=='FUNCTION','Only exact bound future FUNCTION creation constructor')
    function_identity(creation['callable_identity'])
    require(creation['callable_identity']['projected_pg_proc']['proowner']==creator and creation['callable_identity']['projected_pg_proc']['pronamespace']==ns,'Future object actual creator/namespace lineage mismatch')
    require(type(data['fixed_source_allowlist']) is list,'Independent fixed source allowlist missing')
    for item in data['fixed_source_allowlist']:admission_entry(item)
    by_oid=rows(data['default_acl_rows']);semantic_keys=set();global_acl=None;local_acl=[]
    for r in by_oid.values():
        exact(r,['oid','defaclrole','defaclnamespace','defaclobjtype','defaclacl'])
        require(oid(r['defaclrole']) in roles,'Default actual creator missing');oid(r['defaclnamespace'],True)
        require(r['defaclobjtype']=='f','FUNCTION-only source constructor scope')
        key=(r['defaclrole'],r['defaclnamespace'],r['defaclobjtype']);require(key not in semantic_keys,'Duplicate default semantic lookup key');semantic_keys.add(key)
        acl(r['defaclacl'],roles,{'EXECUTE'}) # NULL is not an absent default row.
        if r['defaclrole']==creator:
            if r['defaclnamespace']==0:global_acl=r['defaclacl']
            elif r['defaclnamespace']==ns:local_acl=r['defaclacl']
    if global_acl is None:global_acl=function_default(creator)
    effective=global_acl+local_acl
    has_default=ordinary_permission(context,grantee,creator,effective,'EXECUTE','FUNCTION')
    # Logical DESIGN/* source primitives are not pg_proc identities. No SQL
    # fallback or physical mapping is manufactured to compare these domains.
    outside={'kind':'SQL_FUNCTION','identity':creation['callable_identity']} not in data['fixed_source_allowlist']
    return {'value':has_default and outside,'default_execute':has_default,'outside_fixed_allowlist':outside,'effective_future_acl':effective,'current_object_acl_mutated':False}

def security_definer(data):
    exact(data,['role_context','namespaces','functions','source_expanded_manifest','entry_function_oid','caller','source_execution_semantics'])
    context=data['role_context'];roles=role_context(context);caller=oid(data['caller']);require(caller in roles,'Caller reference missing')
    text(data['source_execution_semantics']) # compare supplied source datum, not an assumed expected answer
    nsmap=rows(data['namespaces']);functions=rows(data['functions'])
    for r in nsmap.values():
        exact(r,['oid','nspname','nspowner','nspacl']);text(r['nspname']);require(oid(r['nspowner']) in roles,'Schema owner missing')
        if r['nspacl'] is not None:acl(r['nspacl'],roles,{'CREATE','USAGE'})
    for r in functions.values():
        proc_projection(r);require(r['pronamespace'] in nsmap and r['proowner'] in roles,'Function namespace/owner missing')
        if r['proacl'] is not None:acl(r['proacl'],roles,{'EXECUTE'})
    manifest=rows(data['source_expanded_manifest'],'function_oid')
    require(set(manifest)==set(functions),'Complete source-expanded function coverage missing')
    for function_id,m in manifest.items():
        exact(m,['function_oid','owner_oid','namespace_oid','body_binding','calls','source_provenance','approved_callable_projection'])
        oid(m['owner_oid']);oid(m['namespace_oid'])
        f=functions[function_id];require(m['owner_oid']==f['proowner'] and m['namespace_oid']==f['pronamespace'],'Source-bound owner/namespace mismatch')
        proc_projection(m['approved_callable_projection'])
        require(all(m['approved_callable_projection'][k]==f[k] for k in PROC_FIELDS if k!='prosecdef'),'Source callable definition/config identity mismatch beyond intended proseсdef switch')
        exact(m['body_binding'],['prosrc_sha256','probin_sha256','prosqlbody_sha256'])
        require(all(m['body_binding'][k]==f[k] for k in m['body_binding']),'Body integrity mismatch')
        # A hash matches identity only. The supplied expanded calls come from
        # the independently authenticated manifest, never SQL guessed from it.
        exact(m['source_provenance'],['artifact_sha256','pointer']);digest(m['source_provenance']['artifact_sha256']);text(m['source_provenance']['pointer'])
        require(type(m['calls']) is list and len(m['calls'])==len(set(m['calls'])),'Complete duplicate-free exact call identities required')
        require(all(oid(child) in functions for child in m['calls']),'Call endpoint missing')
    root=oid(data['entry_function_oid']);require(root in functions,'Entry callable missing')
    pending=deque([(root,caller)]);visited=set();reached=[];found=False
    while pending:
        function_id,active_role=pending.popleft()
        if (function_id,active_role) in visited:continue
        visited.add((function_id,active_role));f=functions[function_id];ns=nsmap[f['pronamespace']]
        admitted=ordinary_permission(context,active_role,f['proowner'],f['proacl'],'EXECUTE','FUNCTION') and ordinary_permission(context,active_role,ns['nspowner'],ns['nspacl'],'USAGE','SCHEMA')
        reached.append({'function_oid':function_id,'caller':active_role,'admitted':admitted})
        if not admitted:continue
        body_role=f['proowner'] if f['prosecdef'] else active_role
        found=found or f['prosecdef']
        for child in manifest[function_id]['calls']:pending.append((child,body_role))
    return {'value':found and data['source_execution_semantics']=='INVOKER_ONLY','reachable_security_definer':found,'source_policy_invoker_only':data['source_execution_semantics']=='INVOKER_ONLY','visited_contexts':reached,'source_manifest_authentication_proven':False,'SQL_body_effects_inferred_from_hash':False}

LEAF_FIELDS=['callable_id','operation_id','kind','resource_relation','resource_oid','projected_field_schema_ref']
def primitive_write(data):
    exact(data,['entry','actor','target_relation','resource_registry','candidate_leaves','expected_source_leaves'])
    exact(data['entry'],['callable_id','operation_id','source_context_digest'])
    text(data['entry']['callable_id']);text(data['entry']['operation_id']);digest(data['entry']['source_context_digest']);oid(data['actor'])
    registry=data['resource_registry'];require(type(registry) is dict,'Independently bound resource roster missing')
    resource_oids=set()
    for relation,r in registry.items():
        text(relation);exact(r,['oid','schema_ref']);oid(r['oid']);require(r['schema_ref']=='CATALOG/'+relation,'Exact source schema reference mismatch')
        require(r['oid'] not in resource_oids,'Ambiguous source relation OID/name roster');resource_oids.add(r['oid'])
    require(data['target_relation'] in registry,'Target natural-key resource unbound')
    for collection in [data['candidate_leaves'],data['expected_source_leaves']]:
        require(type(collection) is list,'Full leaf collection missing')
        keys=set()
        for leaf in collection:
            exact(leaf,LEAF_FIELDS);text(leaf['callable_id']);text(leaf['operation_id']);require(leaf['kind'] in ['FIXED_PROJECTION','WRITE_RESOURCE'],'Unfrozen EffectLeaf kind')
            relation=leaf['resource_relation'];require(relation in registry,'Unknown resource identity')
            oid(leaf['resource_oid'])
            require(leaf['resource_oid']==registry[relation]['oid'] and leaf['projected_field_schema_ref']==registry[relation]['schema_ref'],'Resource OID/name/schema mismatch')
            key=(leaf['callable_id'],leaf['operation_id'],relation);require(key not in keys,'Duplicate exact leaf selector');keys.add(key)
    # This is the frozen closed primitive tree domain. Other callable/op leaves
    # are disconnected, not implicit SQL callbacks. No raw UPDATE ACL is needed
    # to observe a forbidden primitive write effect.
    entry=data['entry'];expected=[l for l in data['expected_source_leaves'] if l['callable_id']==entry['callable_id'] and l['operation_id']==entry['operation_id']]
    require(expected,'Authenticated expected entry manifest binding missing')
    require(all(l['kind']=='FIXED_PROJECTION' for l in expected),'Expected source mutation authority contradicts frozen fixed primitive')
    normalized=[]
    for leaf in data['candidate_leaves']:
        if leaf['callable_id']!=entry['callable_id'] or leaf['operation_id']!=entry['operation_id']:continue
        if leaf['kind']=='WRITE_RESOURCE':normalized.append({'source_actor':data['actor'],'target_relation':leaf['resource_relation'],'target_oid':leaf['resource_oid'],'edge_type':'WRITE_RESOURCE','source_leaf':leaf})
    return {'value':any(e['target_relation']==data['target_relation'] and e['source_leaf'] not in expected for e in normalized),'normalized_candidate_write_edges':normalized,'raw_SQL_privilege_inferred':False,'scope':'Closed source primitive EffectLeaf domain; no arbitrary SQL/callback/body inference','manifest_authentication_proven':False}

def observe(operator,data):
    try:
        require(operator in ['FUTURE_FUNCTION_DEFAULT','SECURITY_DEFINER_PATH','FIXED_PRIMITIVE_WRITE_PATH'],'Unknown local operator')
        result={'FUTURE_FUNCTION_DEFAULT':future_default,'SECURITY_DEFINER_PATH':security_definer,'FIXED_PRIMITIVE_WRITE_PATH':primitive_write}[operator](data)
        return {'availability':'AVAILABLE','value':result['value'],'trace':result,'canonical_binding_or_proof_claimed':False}
    except (Unavailable,KeyError,TypeError,ValueError) as exc:
        return {'availability':'UNAVAILABLE','value':None,'reason':str(exc),'domain_UNKNOWN_or_qualification_REJECT_emitted':False}
