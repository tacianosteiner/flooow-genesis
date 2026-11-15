"""Pure local functional revalidation of frozen C5H subpredicate programs.

UNIT_* data are interpreter unit vectors, never canonical fixture identities,
catalog facts, witnesses, or attacks. Canonical expected outcomes are not read.
"""
import copy

def vectors(program,inputs):
    env={k:'UNIT_A' for k in inputs}
    for k in inputs:
        if k in {'supplied_generation','current_independent_high_water','source_attestation.generation','claimed_target_generation','supplied_generation_revision','independently_current_generation_revision','candidate.journal_sequence','independently_durable_sequence'}:env[k]=10
    env.update({
        'phase':'ACTIVE','old_work_state':'UNKNOWN','explicit_bootstrap_delivery':False,
        'attempt_new_channel_admission':True,'attempt_to_adopt_old_enrollment_with_new_birth':True,
        'authorization_consumed':True,'request_requires_new_authority':True,
        'challenge_work_consumed':True,'sequence':2,'last_accepted':1,
        'target_qualification_receipts':[],'irreversible_retired_generation_set':[9],
        'T_NOW':20,'captured_boottime':10,'MAX_AGE':5,
        'R':1,'claim.caller':1,'claim.phase':'ACTIVE','claim.operation':'PRE_ENROLLMENT_PROVISION',
        'claim.authority_origin':'HOST_ROOT','authorized_HOST_PLATFORM_pre_enrollment_provisioner':2,
        'candidate_resolution.kind':'NAMESPACE_NAME_LOOKUP',
        'candidate_resolution':{'kind':'NAMESPACE_NAME_LOOKUP','namespace_oid':31,'resolved_relation_oid':21},
        'frozen_object_oids':{'pg_catalog.pg_roles':20},
        'actual_authenticated_SQL_role':{'oid':1,'rolname':'unit_reader'},
        'expected_Reader_role':{'oid':1,'name':'unit_reader'},
        'protected_catalog_relation':{'owner_oid':1},
        'catalog.pg_roles':[{'oid':1,'rolname':'unit_reader','rolcanlogin':True,'rolinherit':False,'rolsuper':False,'rolcreaterole':False,'rolcreatedb':False,'rolreplication':False,'rolbypassrls':False}],
        'object_acls':{'pg_catalog.pg_auth_members':[{'grantor':2,'grantee':0,'privilege':'UPDATE','is_grantable':False}]},
        'fixed_source_operation_allowlist':[],
        'expected_reader_identity_row':{'expected_key':[1],'key_fields':['oid'],'rows':[{'oid':1,'rolname':'unit_reader'}]},
        'observed_rows':{'key_fields':['oid'],'rows':[{'oid':1}]},
        'source_collection_snapshot_identities':[[1],[1]],
        'observed_protected_rows_selected_by_expected_OID_OR_NAME':[[1,'unit_reader']],
        'expected_protected_OID_name_roster':[[1,'unit_reader']]})
    # Keep only declared operands/dependencies: no hidden expected-answer input.
    env={k:env[k] for k in inputs}
    result=[env]
    for k,v in env.items():
        e=copy.deepcopy(env)
        if type(v) is bool:e[k]=not v
        elif type(v) is int:e[k]=v+1
        elif type(v) is str:e[k]='UNIT_B'
        else:continue
        result.append(e)
    special=[{'T_NOW':15},{'irreversible_retired_generation_set':[9,10]},
        {'expected_reader_identity_row':{'expected_key':[1],'key_fields':['oid'],'rows':[]}},
        {'observed_rows':{'key_fields':['oid'],'rows':[{'oid':1},{'oid':1}]}},
        {'source_collection_snapshot_identities':[[1],[2]]},
        {'observed_protected_rows_selected_by_expected_OID_OR_NAME':[[1,'unit_reader'],[1,'unit_reader']]},
        {'actual_authenticated_SQL_role':{'oid':2,'rolname':'unit_other'}},
        {'protected_catalog_relation':{'owner_oid':2}},
        {'object_acls':{'pg_catalog.pg_auth_members':[]}},
        {'fixed_source_operation_allowlist':['UPDATE']},
        {'candidate_resolution.kind':'EXACT_FROZEN_IDENTITY','candidate_resolution':{'kind':'EXACT_FROZEN_IDENTITY','relation_oid':20,'namespace_oid':30}}]
    for flag in ['rolsuper','rolcreaterole','rolbypassrls']:
        rows=copy.deepcopy(env.get('catalog.pg_roles',[]))
        if rows:rows[0][flag]=True;special.append({'catalog.pg_roles':rows})
    for change in special:
        if set(change)<=env.keys():
            e=copy.deepcopy(env);e.update(change);result.append(e)
    return result

def validate(programs,observe,dependencies):
    rows=[]
    for p in programs:
        if p['status']!='DERIVED_C5H':continue
        candidates=vectors(p['program'],dependencies(p['program']))
        actual=[];available=[]
        for env in candidates:
            observation=observe(p['program'],env)
            if observation['availability']=='AVAILABLE':
                assert type(observation['value']) is bool
                actual.append({'input':env,'output':observation});available.append(observation['value'])
        assert True in available and False in available,(p['PREDICATE_ID'],p['expression'],available)
        # Missing input must stay unavailable, even for deciding boolean branches.
        empty=observe(p['program'],{})
        assert empty['availability']=='UNAVAILABLE',(p['PREDICATE_ID'],empty)
        rows.append({'PREDICATE_ID':p['PREDICATE_ID'],'both_boolean_branches_observed':True,'missing_inputs_preserved':empty,'unit_observations':actual,'canonical_witness_or_attack':False})
    assert len(rows)==43
    return rows
