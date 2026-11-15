"""Evidence-only typed role closure. No IO, expected outcome or witness input.

This is a local normalized operand calculation, NOT proof that a supplied table
is an exhaustive/authenticated live snapshot or that a runtime enforces policy.
ROLE_PG_DATABASE_OWNER=6171 is frozen pg_authid.dat, not a chosen principal.
Validation covers consumed graph fields and required column presence. Unused
datacl payload is preserved as NULL/array only; ACL element normalization, exact
source name byte limits and snapshot policy/provenance remain external gates.
Trace order is this helper's deterministic BFS, not provider-observed row order.
"""
from collections import deque
import unicodedata

DATABASE_OWNER_ROLE_OID=6171
ROLE_FIELDS={'oid','rolname','rolcanlogin','rolinherit','rolsuper','rolcreaterole','rolcreatedb','rolreplication','rolbypassrls'}
MEMBER_FIELDS={'oid','roleid','member','grantor','admin_option','inherit_option','set_option'}
DB_FIELDS={'oid','datname','datdba','datallowconn','datconnlimit','encoding','datacl'}

class Unavailable(Exception):pass

def oid(x):
    if type(x) is not int or not 0<x<2**32:raise Unavailable('Unbound/invalid OID; no boolean or zero identity coercion')
    return x

def text(x):
    if type(x) is not str or not x or '\x00' in x or unicodedata.normalize('NFC',x)!=x:raise Unavailable('Noncanonical source name')
    try:x.encode('utf-8',errors='strict')
    except UnicodeError as exc:raise Unavailable('Noncanonical UTF8 source name') from exc

def boolean(x):
    if type(x) is not bool:raise Unavailable('Exact source boolean required')

def table(rows,fields):
    if type(rows) is not list:raise Unavailable('Raw duplicate-preserving row list required')
    seen=set()
    for row in rows:
        if type(row) is not dict or set(row)!=fields:raise Unavailable('Missing/extra projected field')
        key=oid(row['oid'])
        if key in seen:raise Unavailable('Duplicate source natural-key OID; never silently deduplicate')
        seen.add(key)

def normalize(inputs):
    if type(inputs) is not dict or set(inputs)!={'roles','memberships','databases','database_context'}:raise Unavailable('Exact normalized input contract required')
    roles=inputs['roles'];members=inputs['memberships'];dbs=inputs['databases']
    table(roles,ROLE_FIELDS);table(members,MEMBER_FIELDS);table(dbs,DB_FIELDS)
    role_map={r['oid']:r for r in roles}
    for r in roles:
        text(r['rolname'])
        for k in ROLE_FIELDS-{'oid','rolname'}:boolean(r[k])
    if DATABASE_OWNER_ROLE_OID not in role_map or role_map[DATABASE_OWNER_ROLE_OID]['rolname']!='pg_database_owner':raise Unavailable('Builtin role reference not bound to frozen OID/name')
    for r in members:
        for k in ['roleid','member','grantor']:
            if oid(r[k]) not in role_map:raise Unavailable('Missing membership endpoint/grantor role proof')
        for k in ['admin_option','inherit_option','set_option']:boolean(r[k])
    for r in dbs:
        text(r['datname']);boolean(r['datallowconn'])
        if oid(r['datdba']) not in role_map:raise Unavailable('Database owner role not bound')
        for k in ['datconnlimit','encoding']:
            if type(r[k]) is not int or not -2**31<=r[k]<2**31:raise Unavailable('Exact source int4 required')
        if r['datacl'] is not None and type(r['datacl']) is not list:raise Unavailable('ACL array/NULL presence not preserved')
    ctx=inputs['database_context']
    if ctx=={'kind':'NO_DATABASE'}:owner=None
    elif type(ctx) is dict and set(ctx)=={'kind','database_oid'} and ctx['kind']=='DATABASE':
        key=oid(ctx['database_oid']);matches=[r for r in dbs if r['oid']==key]
        if len(matches)!=1:raise Unavailable('Current database exact row missing/duplicated')
        owner=matches[0]['datdba']
    else:raise Unavailable('No-current-database must be explicitly bound; absent context is not no database')
    return role_map,members,owner

def traverse(role_map,rows,owner,member,kind):
    if oid(member) not in role_map:raise Unavailable('Start role not bound')
    if kind not in {'MEMBER','SET','INHERIT'}:raise Unavailable('Unknown edge type')
    reached=[member];visited={member};pending=deque([member]);trace=[]
    while pending:
        current=pending.popleft()
        for row in rows:
            if row['member']!=current:continue
            admitted=kind=='MEMBER' or row['set_option' if kind=='SET' else 'inherit_option']
            trace.append({'row_oid':row['oid'],'grantor':row['grantor'],'member':current,'roleid':row['roleid'],'kind':kind,'admitted':admitted})
            if admitted and row['roleid'] not in visited:
                visited.add(row['roleid']);reached.append(row['roleid']);pending.append(row['roleid'])
        # The provider adds this for every reached database owner, regardless
        # of explicit membership flags. It is NOT an admin_option grant.
        if owner is not None and current==owner:
            trace.append({'implicit_edge':'CURRENT_DATABASE_OWNER','member':current,'roleid':DATABASE_OWNER_ROLE_OID,'kind':kind,'admin_option':'NOT_AN_AUTHMEMBERS_ROW'})
            if DATABASE_OWNER_ROLE_OID not in visited:
                visited.add(DATABASE_OWNER_ROLE_OID);reached.append(DATABASE_OWNER_ROLE_OID);pending.append(DATABASE_OWNER_ROLE_OID)
    return reached,trace

def observe(inputs,kind,member,target):
    """Return local predicate evidence; never a qualification/proof status."""
    try:
        roles,rows,owner=normalize(inputs)
        if oid(target) not in roles:raise Unavailable('Target role not bound')
        if kind=='PROJECT_HAS_ADMIN_OPTION':
            if member==target:raise Unavailable('Outside frozen canonical R!=A domain; provider/project self-superuser rules differ')
            if oid(member) not in roles:raise Unavailable('Start role not bound')
            if roles[member]['rolsuper']:
                value=True;reached=[member];trace=[{'source_superuser':member}]
            else:
                reached,trace=traverse(roles,rows,owner,member,'MEMBER')
                # Examine all explicit parallel rows; never infer ADMIN from
                # the implicit db-owner edge itself.
                value=any(r['member'] in reached and r['roleid']==target and r['admin_option'] for r in rows)
        else:
            reached,trace=traverse(roles,rows,owner,member,kind)
            value=target in reached
        return {'availability':'AVAILABLE','value':value,'reached_roles':reached,'trace':trace,'scope':'LOCAL_NORMALIZED_OPERAND_PROPERTY_ONLY','full_source_scalar_and_ACL_validation':False,'snapshot_exhaustiveness_proven':False,'canonical_qualification_observed':False,'trace_order_is_provider_observation':False}
    except (Unavailable,KeyError,TypeError) as exc:
        return {'availability':'UNAVAILABLE','value':None,'reason':str(exc),'domain_UNKNOWN_or_qualification_REJECT_emitted':False}
