"""Recompute present source capability inventory separately from column ACLs."""
import json
import package_0090_source_gate as gate
from package_0090_capability_source import strings


def inventory():
    source=(gate.ROOT/gate.V043).read_text(encoding='utf-8-sig')
    spec=(gate.ROOT/gate.SPEC).read_text(encoding='utf-8-sig')
    stmts,_=gate.parse(source)
    checks=gate.prerequisite_checks(source,spec)
    def function(obj):
        names=strings(obj['objname'])
        return dict(schema=names[0],name=names[1],input_types=['.'.join(strings(t['TypeName']['names'])) for t in obj['objargs']])
    functions=[];schemas=[];owners=[]
    for stmt in stmts:
        if 'AlterOwnerStmt' in stmt:
            owner=stmt['AlterOwnerStmt'];item=function(owner['object']['ObjectWithArgs'])
            item.update(owner=owner['newowner']['rolename'],implicit_owner_execute=True);owners.append(item)
        grant=stmt.get('GrantStmt',{})
        if not grant.get('is_grant'):continue
        if grant['objtype']=='OBJECT_FUNCTION':
            for obj in grant['objects']:
                for recipient in grant['grantees']:
                    item=function(obj['ObjectWithArgs']);item.update(grantee=recipient['RoleSpec']['rolename'],
                        privilege='EXECUTE',grant_option=bool(grant.get('grant_option')));functions.append(item)
        if grant['objtype']=='OBJECT_SCHEMA':
            for obj in grant['objects']:
                for recipient in grant['grantees']:
                    schemas.append(dict(schema=obj['String']['sval'],grantee=recipient['RoleSpec']['rolename'],
                        privilege='USAGE',grant_option=bool(grant.get('grant_option'))))
    return dict(gate='G3F.3B_V_BRIDGE_EXECUTE_SOURCE_INVENTORY',
                scope='ALL_PRESENT_SOURCE_EXPLICIT_GRANTS_AND_OWNERS_NOT_INSTALLED_EFFECTIVE_ACLS',
                exact_column_grants=checks['exact_column_grants'],
                function_execute_grant_count=len(functions),function_execute_grants=functions,
                schema_usage_grant_count=len(schemas),schema_usage_grants=schemas,
                function_owner_changes=owners,
                preinstalled_dependencies={
                    'offline_crypto.hmac(bytea,bytea,text)':'D_OWNER_Q_EXECUTE',
                    'offline_crypto.timing_safe_equal32(bytea,bytea)':'D_OWNER_Q_EXECUTE',
                    'offline_crypto.canonical_spki_ed25519_verify(bytea,bytea,bytea)':'D_OWNER_OWNER_ONLY_BEFORE_V_SOURCE_GRANT',
                    'offline_crypto_schema':'D_OWNER_Q_USAGE_BEFORE_V_NEW_SOURCE_GRANT'},
                public_native_crypto_execute=False,a_direct_native_crypto_execute=False,
                a_private_crypto_usage=False,v_hmac_or_mac32_execute=False,
                future_v041_v042_wrapper_closure='PENDING_UNIMPLEMENTED_WRAPPERS',
                runtime_effective_acl_proof=False,protected_database_mutation=False)


if __name__=='__main__':
    report=inventory()
    (gate.ROOT/'docs/evidence/PACKAGE-0090-V-BRIDGE-CAPABILITY-INVENTORY.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print('FUNCTION_EXECUTE_GRANTS='+str(report['function_execute_grant_count']))
    print('SCHEMA_USAGE_GRANTS='+str(report['schema_usage_grant_count']))
    print('PHYSICAL_COLUMN_GRANTS='+str(report['exact_column_grants']))
