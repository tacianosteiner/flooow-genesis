"""Generic UNIT data only. No canonical witness values or expected answers."""
import copy
import itertools

def proc(n=701,owner=2,sd=False):
    return {'oid':n,'proname':'UNIT_FUNCTION_'+str(n),'pronamespace':71,'proowner':owner,'prolang':12,'prokind':'f','prosecdef':sd,'proisstrict':False,'proretset':False,'provolatile':'v','proparallel':'u','pronargs':0,'pronargdefaults':0,'prorettype':23,'proargtypes':[],'proallargtypes':None,'proargmodes':None,'proargnames':None,'proconfig':None,'proacl':None,'prosrc_sha256':format(n,'064x'),'probin_sha256':None,'prosqlbody_sha256':None}
def identity(n=701):
    return {'projected_pg_proc':proc(n),'source_effect_manifest_identity':'a'*64,'source_capability_version':'UNIT_SOURCE_VERSION','qualification_context_identity':'b'*64}
def context(inherit=False):
    return {'roles':[{'oid':i,'rolname':'UNIT_ROLE_'+str(i),'rolsuper':False} for i in [1,2,3]],'inherit_edges':[{'member':1,'roleid':3,'source_row_oid':901,'source_kind':'EXPLICIT_INHERIT_OPTION'}] if inherit else []}
def grant(who,priv='EXECUTE',owner=2):return {'grantor':owner,'grantee':who,'privilege':priv,'is_grantable':False}
def defaults(global_acl,local_acl,inherit=False,allowed=False):
    rows=[]
    if global_acl is not None:rows.append({'oid':801,'defaclrole':2,'defaclnamespace':0,'defaclobjtype':'f','defaclacl':global_acl})
    if local_acl is not None:rows.append({'oid':802,'defaclrole':2,'defaclnamespace':71,'defaclobjtype':'f','defaclacl':local_acl})
    return {'role_context':context(inherit),'default_acl_rows':rows,'creator':2,'namespace':71,'grantee':1,'creation':{'creator':2,'namespace':71,'kind':'FUNCTION','callable_identity':identity()},'fixed_source_allowlist':[{'kind':'SQL_FUNCTION','identity':identity()}] if allowed else []}
def body(f,calls):
    return {'function_oid':f['oid'],'owner_oid':f['proowner'],'namespace_oid':f['pronamespace'],'body_binding':{k:f[k] for k in ['prosrc_sha256','probin_sha256','prosqlbody_sha256']},'calls':calls,'source_provenance':{'artifact_sha256':'c'*64,'pointer':'/UNIT/function/'+str(f['oid'])},'approved_callable_projection':copy.deepcopy(f)}
def sd_case(flag=False,execute=None,usage=None,policy='INVOKER_ONLY'):
    f=proc(sd=flag);f['proacl']=execute
    return {'role_context':context(),'namespaces':[{'oid':71,'nspname':'UNIT_NAMESPACE','nspowner':2,'nspacl':usage}],'functions':[f],'source_expanded_manifest':[body(f,[])],'entry_function_oid':701,'caller':1,'source_execution_semantics':policy}
def leaf(kind='FIXED_PROJECTION',callable_id='DESIGN/SOURCE_FIXED_PROJECT',op='S01',relation='pg_catalog.pg_roles'):
    return {'callable_id':callable_id,'operation_id':op,'kind':kind,'resource_relation':relation,'resource_oid':101 if relation=='pg_catalog.pg_roles' else 102,'projected_field_schema_ref':'CATALOG/'+relation}
def write_case():
    return {'entry':{'callable_id':'DESIGN/SOURCE_FIXED_PROJECT','operation_id':'S01','source_context_digest':'d'*64},'actor':1,'target_relation':'pg_catalog.pg_auth_members','resource_registry':{r:{'oid':v,'schema_ref':'CATALOG/'+r} for r,v in [('pg_catalog.pg_roles',101),('pg_catalog.pg_auth_members',102)]},'candidate_leaves':[leaf()],'expected_source_leaves':[leaf()]}

def validate_new(module):
    observations=[];controls=[]
    def compare(name,op,data,reference):
        before=copy.deepcopy(data);result=module.observe(op,data)
        assert data==before,'Local operator mutated input'
        assert result['availability']=='AVAILABLE' and result['value']==reference,(name,result,reference)
        observations.append({'test':name,'operator':op,'value':result['value']})
    choices=[None,[],[grant(0)],[grant(1)],[grant(3)]]
    for g,l,inh,allowed in itertools.product(choices,choices,[False,True],[False,True]):
        data=defaults(g,l,inh,allowed)
        # Separate direct constructor oracle, not the implementation's ACL code.
        grants=([grant(0),grant(2)] if g is None else g)+(l or [])
        effective_roles={1,3} if inh else {1}
        reference=any(x['privilege']=='EXECUTE' and (x['grantee']==0 or x['grantee'] in effective_roles) for x in grants) and not allowed
        compare('default-constructor-grid','FUTURE_FUNCTION_DEFAULT',data,reference)
    # Actual creator rows never substituted by a role whose privileges R inherits.
    data=defaults([],None,True);data['default_acl_rows'].append({'oid':803,'defaclrole':3,'defaclnamespace':71,'defaclobjtype':'f','defaclacl':[grant(1,owner=3)]})
    compare('actual-creator-not-membership-defaults','FUTURE_FUNCTION_DEFAULT',data,False)
    data=defaults([],None);data['grantee']=2
    compare('owner-empty-ACL-has-no-ordinary-execute','FUTURE_FUNCTION_DEFAULT',data,False)
    data=defaults([],[grant(1)],allowed=True);data['creation']['callable_identity']['projected_pg_proc']['proconfig']=['UNIT_SETTING=1']
    compare('full-admission-identity-includes-config','FUTURE_FUNCTION_DEFAULT',data,True)
    data=defaults([],[grant(1)]);data['fixed_source_allowlist']=[{'kind':'SOURCE_PRIMITIVE','callable_id':'DESIGN/SOURCE_FIXED_PROJECT','source_capability_version':'UNIT_SOURCE_VERSION'}]
    compare('logical-source-primitive-is-not-SQL-fallback','FUTURE_FUNCTION_DEFAULT',data,True)
    for flag,exec_acl,usage_acl,policy in itertools.product([False,True],[None,[],[grant(0)],[grant(1)]],[None,[],[grant(0,'USAGE')],[grant(1,'USAGE')]],['INVOKER_ONLY','UNIT_OTHER_POLICY']):
        data=sd_case(flag,exec_acl,usage_acl,policy)
        executable=exec_acl is None or any(g['grantee'] in [0,1] for g in exec_acl)
        usable=usage_acl is not None and any(g['grantee'] in [0,1] for g in usage_acl)
        compare('SD-entry-access-policy-grid','SECURITY_DEFINER_PATH',data,flag and executable and usable and policy=='INVOKER_ONLY')
    for root_flag,child_acl in itertools.product([False,True],[[grant(1)],[grant(2)]]):
        data=sd_case(root_flag,None,[grant(0,'USAGE')]);child=proc(702,sd=True);child['proacl']=child_acl
        data['functions'].append(child);data['source_expanded_manifest'][0]['calls']=[702];data['source_expanded_manifest'].append(body(child,[]))
        compare('nested-SD-active-role','SECURITY_DEFINER_PATH',data,root_flag or child_acl[0]['grantee']==1)
        result=module.observe('SECURITY_DEFINER_PATH',data)
        reached=result['trace']['visited_contexts'];assert reached[1]['caller']==(2 if root_flag else 1)
    data=sd_case(False,None,[grant(0,'USAGE')]);child=proc(702,sd=True)
    data['functions'].append(child);data['source_expanded_manifest'][0]['calls']=[702];data['source_expanded_manifest'].append(body(child,[701]))
    compare('cyclic-call-role-context-pairs','SECURITY_DEFINER_PATH',data,True)
    assert len(module.observe('SECURITY_DEFINER_PATH',data)['trace']['visited_contexts'])==4
    for kind,same_callable,same_op,same_target in itertools.product(['FIXED_PROJECTION','WRITE_RESOURCE'],[False,True],[False,True],[False,True]):
        data=write_case();data['candidate_leaves'].append(leaf(kind,'DESIGN/SOURCE_FIXED_PROJECT' if same_callable else 'UNIT_DISCONNECTED','S01' if same_op else 'UNIT_OTHER_OP','pg_catalog.pg_auth_members' if same_target else 'pg_catalog.pg_roles'))
        # Replace duplicate exact selector when the changed leaf uses root pg_roles.
        if same_callable and same_op and not same_target:data['candidate_leaves']=data['candidate_leaves'][1:]
        compare('primitive-root-and-resource-reachability','FIXED_PRIMITIVE_WRITE_PATH',data,kind=='WRITE_RESOURCE' and same_callable and same_op and same_target)
    def unavailable(name,op,data):
        result=module.observe(op,data);assert result['availability']=='UNAVAILABLE',(name,result);controls.append({'test':name,'observation':result})
    for key in ['fixed_source_allowlist','creation']:
        data=defaults([],[grant(1)]);data.pop(key);unavailable('missing-independent-default-input-'+key,'FUTURE_FUNCTION_DEFAULT',data)
    data=defaults([],None);data['default_acl_rows'][0]['defaclacl']=None;unavailable('NULL-default-row-not-absent','FUTURE_FUNCTION_DEFAULT',data)
    data=defaults([],None);data['default_acl_rows'].append(copy.deepcopy(data['default_acl_rows'][0]));unavailable('duplicate-default-row','FUTURE_FUNCTION_DEFAULT',data)
    data=defaults([],None);data['creation']['creator']=True;unavailable('nested-creator-bool-not-OID','FUTURE_FUNCTION_DEFAULT',data)
    data=sd_case(True,None,[grant(0,'USAGE')]);data.pop('source_execution_semantics');unavailable('missing-independent-policy-input','SECURITY_DEFINER_PATH',data)
    data=sd_case(True,None,[grant(0,'USAGE')]);data['source_expanded_manifest']=[];unavailable('flag-alone-no-body-effect-manifest','SECURITY_DEFINER_PATH',data)
    data=sd_case(True,None,[grant(0,'USAGE')]);data['source_expanded_manifest'][0]['body_binding']['prosrc_sha256']='e'*64;unavailable('body-identity-mismatch','SECURITY_DEFINER_PATH',data)
    data=sd_case(True,None,[grant(0,'USAGE')]);data['source_expanded_manifest'][0]['owner_oid']=True;unavailable('manifest-owner-bool-not-OID','SECURITY_DEFINER_PATH',data)
    data=write_case();data['candidate_leaves'][0]['resource_oid']=True;unavailable('leaf-OID-bool-rejected','FIXED_PRIMITIVE_WRITE_PATH',data)
    data=write_case();data['expected_source_leaves'][0]['kind']='WRITE_RESOURCE';unavailable('expected-manifest-cannot-mint-write-authority','FIXED_PRIMITIVE_WRITE_PATH',data)
    return {'observations':observations,'negative_controls':controls,'unit_only':True,'canonical_witnesses_or_attacks':0}
