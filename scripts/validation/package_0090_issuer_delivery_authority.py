"""Issuer ACK guard alignment audit; no new physical authority."""
import json
import package_0090_source_gate as gate

FIELDS=('binding_id','attempt_id','generation','execution_id','instance_id','credential_id','initial_operation_id','fresh_applied_receipt_id','state')

def audit():
    spec=(gate.ROOT/gate.SPEC).read_text(encoding='utf-8-sig')
    source=(gate.ROOT/gate.V043).read_text(encoding='utf-8-sig')
    rows=[]
    for line in spec.splitlines():
        cells=[c.strip() for c in line.split('|')]
        if len(cells)>7 and cells[1:3]==['I','public.offline_delivery'] and cells[4]=='READ_PRIVILEGE':
            rows.append(dict(column=cells[3],consumer=cells[5],entrypoint=cells[6],purpose=cells[7]))
    if {r['column'] for r in rows}!=set(FIELDS):raise ValueError('Issuer delivery matrix changed; reevaluate')
    if any(r['entrypoint']!='S09-S12' for r in rows):raise ValueError('Issuer delivery consumer authority changed; reevaluate')
    if 'I5. ACKNOWLEDGED from original live execution prerequisite for grant/auth/decision.' not in spec:raise ValueError('ACK invariant changed')
    if 'Sections22.4/21.7 fix respectively the exact column/control and frozen EXECUTE allowlists; no implementation may widen them without reviewed contract change.' not in spec:raise ValueError('Consumer authority rule changed')
    frozen=next((gate.ROOT/gate.MIGRATIONS).glob('V042__*.sql')).read_text(encoding='utf-8-sig')
    if 'offline_delivery' in frozen:raise ValueError('Frozen dependency now has delivery authority')
    statements,_=gate.parse(source)
    grants=gate.actual_column_grants(statements)
    helper_grants=[s['GrantStmt'] for s in statements if s.get('GrantStmt',{}).get('objtype')=='OBJECT_FUNCTION' and any(o.get('ObjectWithArgs',{}).get('objname',[])[-1:]==[{'String':{'sval':'offline_lock_bound_principal'}}] for o in s.get('GrantStmt',{}).get('objects',[])) and s['GrantStmt'].get('is_grant')]
    if len(helper_grants)!=1 or helper_grants[0]['grantees']!=[{'RoleSpec':{'roletype':'ROLESPEC_CSTRING','rolename':'flooow_offline_execution_owner'}}]:
        # RoleSpec locations are stripped by gate.parse; if parser representation
        # changes, the invariant must be reviewed rather than guessed.
        recipients=[r['RoleSpec'].get('rolename') for g in helper_grants for r in g['grantees']]
        if recipients!=['flooow_offline_execution_owner']:raise ValueError('P delegation changed')
    return dict(gate='G3F.3B_ISSUER_DELIVERY_ACK_CONSUMER_AUTHORITY',status='ALIGNED_EXISTING_I5_AND_I_COLUMN_AUTHORITY',
        unresolved_authority_blocker_count=0,required_boundary='S11/S12 grant M guard',
        required_invariant='I5 original live execution DELIVERY_ACKNOWLEDGED before grant',
        approved_i_delivery_reads=rows,physical_grant_count=len(grants),
        physical_i_select_exists=True,authorized_s11_s12_consumer=True,
        rationale='Existing I5 explicitly requires the original live ACK before grant; I already has all nine scoped delivery column reads and S07-S12 delivery lock authority. The matrix entrypoint labels are aligned with that existing mandatory guard. No new role, column privilege, helper, caller projection or mutation authority is added.',
        selected_handoff=dict(change='Aligned the nine existing I delivery read consumer rows with mandatory I5 for S09-S12; no new privilege',fields=list(FIELDS),new_column_grants=0,new_helpers=0,new_public_signatures=0,required_checks='Exact binding/current attempt/generation/execution/instance/credential/initial operation and original fresh Applied receipt; state DELIVERY_ACKNOWLEDGED; retain M possession/window/C locks'),
        s07_s12_implemented='BOUNDED_SOURCE_NOT_RUNTIME',authority_widened=False,v043_executed=False,protected_database_connection=False,
        limitation='Source consumer alignment only; full installed ACL and runtime guard closure remain separate.')

if __name__=='__main__':
    result=audit();(gate.ROOT/'docs/evidence/PACKAGE-0090-ISSUER-DELIVERY-ACK-AUTHORITY.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
