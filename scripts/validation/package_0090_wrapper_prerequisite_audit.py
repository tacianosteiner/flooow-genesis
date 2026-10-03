"""Read-only offline audit of the S01 live-connection contract/grant conflict."""
import copy
import json
from pathlib import Path
import package_0090_source_gate as gate

OWNER='flooow_offline_audit_owner'
REQUIRED={(OWNER,'public.integration_connection',c,'select') for c in
          ('organization_id','connection_id','provider_key','credential_kind','status','binding_version')}


def audit():
    spec=(gate.ROOT/gate.SPEC).read_text(encoding='utf-8-sig')
    grants=gate.expected_column_grants(spec)
    missing=sorted(REQUIRED-grants)
    fixture=json.loads((gate.ROOT/'docs/evidence/PACKAGE-0090-G3F-3B-EVIDENCE-FIXTURE-001.json').read_text(encoding='utf-8-sig'))
    tables=fixture['tables']
    suspended=copy.deepcopy(tables)
    suspended['integration_connection'][0]['status']='SUSPENDED'

    def project(rows):
        result={}
        for relation,items in rows.items():
            columns={c for o,r,c,p in grants if o==OWNER and r=='public.'+relation and p=='select'}
            if columns:result[relation]=[{c:v for c,v in row.items() if c in columns} for row in items]
        return result

    producer=gate.ROOT/'applications/command-authority-ceremony/src/main/kotlin/io/flooow/ceremony/PostgresOfflineFieldProofSupport.kt'
    organization_query="SELECT status='ACTIVE' FROM public.integration_organization WHERE organization_id=?"
    if organization_query not in producer.read_text(encoding='utf-8-sig'):
        raise ValueError('Existing live organization predicate changed; audit must be re-reviewed')
    if 'Controls/catalog/history/org/connections/target reads; A/no locks' not in spec:
        raise ValueError('S01 contract changed; audit must be re-reviewed')
    from package_0090_s01_readiness import audit as readiness_audit
    readiness=readiness_audit() if not missing else None
    return {'gate':'G3F.3B_PUBLIC_WRAPPERS_AND_GUARDS','status':'HOLD_NEW_READ_AUTHORITY_REQUIRED' if missing else 'HOLD_TARGET_READ_AUTHORITY_REQUIRED',
        'blocker':'S01 live connection readiness requirement has no permitted A read path' if missing else readiness['blocker'],
        'missing_minimum_select':missing,'existing_live_predicate':organization_query,
        'approved_a_fixture_projection_unchanged_after_connection_suspension':project(tables)==project(suspended),
        'observation_scope':'retained offline fixture row projections, not SQL/function runtime proof',
        'required_a_integration_connection_grants':sorted(g for g in grants if g[0]==OWNER and g[1]=='public.integration_connection'),
        'unresolved_authority_blocker_count':1,
        'spec_amended':not missing,'grants_widened':not missing,'database_connection_attempted':False,
        'next_gate':'G3F.3B_S01_TARGET_CONSUMER_AUTHORITY' if not missing else 'G3F.3B_S01_CONNECTION_READ_AUTHORITY',
        'target_readiness_authority':readiness}


if __name__=='__main__':
    report=audit()
    target=gate.ROOT/'docs/evidence/PACKAGE-0090-G3F-3B-PUBLIC-WRAPPER-PREREQUISITES.json'
    target.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,indent=2))
