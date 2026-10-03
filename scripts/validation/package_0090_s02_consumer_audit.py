"""Offline next-boundary audit: S02 inspect transitive signer consumer scope."""
import copy
import json
import re
import sqlite3
import package_0090_source_gate as gate

PRODUCER=gate.ROOT/'applications/command-authority-ceremony/src/main/kotlin/io/flooow/ceremony/PostgresOfflineFieldProofSupport.kt'
SIGNERS={'public.s2a_signer_key_revision','public.s2a_signer_authority_revision'}


def query():
    text=PRODUCER.read_text(encoding='utf-8-sig')
    return text.split('private fun acceptedArtifact',1)[1].split('"""',2)[1]


def columns():
    from pglast.parser import parse_sql_json
    number=iter(range(1,4))
    ast=json.loads(parse_sql_json(re.sub(r'\?',lambda _: '$'+str(next(number)),query())))
    aliases={};columns=set()
    def bind(node):
        if isinstance(node,list):
            for c in node:bind(c)
        elif isinstance(node,dict):
            if 'RangeVar' in node:
                r=node['RangeVar'];aliases[r['alias']['aliasname']]=r['schemaname']+'.'+r['relname']
            for c in node.values():bind(c)
    def refs(node):
        if isinstance(node,list):
            for c in node:refs(c)
        elif isinstance(node,dict):
            if 'ColumnRef' in node:
                fields=node['ColumnRef']['fields']
                if not any('A_Star' in f for f in fields):
                    f=[f['String']['sval'] for f in fields]
                    if len(f)==2:columns.add((aliases[f[0]],f[1]))
            for c in node.values():refs(c)
    bind(ast);refs(ast)
    return columns


def s02_scope(entrypoint):
    if 'S02' in entrypoint:return True
    return any(int(a)<=2<=int(b) for a,b in re.findall(r'S(\d+)-S(\d+)',entrypoint))


def witness(rows):
    db=sqlite3.connect(':memory:')
    try:
        for relation in sorted({r for r,c in columns()}):
            names=sorted(c for r,c in columns() if r==relation);name=relation.split('.')[1]
            db.execute('CREATE TABLE '+name+'('+','.join(names)+')')
            db.executemany('INSERT INTO '+name+' VALUES('+','.join('?' for c in names)+')',
                           [tuple(row[c] for c in names) for row in rows[relation]])
        sql=query().replace('SELECT a.*','SELECT count(*)').replace('public.','')
        return db.execute(sql,('approval-source','organization','manifest')).fetchone()[0]
    finally:db.close()


def audit():
    text=PRODUCER.read_text(encoding='utf-8-sig')
    inspect=text.split('private fun inspect(',1)[1].split('override fun reconcile',1)[0]
    if 'else accepted(connection,input) && consumption(connection,input) && fingerprints(connection,input,authority.second)' not in inspect:
        raise ValueError('Existing inspect dependency changed; review required')
    if 'runCatching { acceptedArtifact(connection, input) }.getOrDefault(false)' not in text:
        raise ValueError('Existing acceptedArtifact dependency changed')
    spec=(gate.ROOT/gate.SPEC).read_text(encoding='utf-8-sig');grants=gate.expected_column_grants(spec)
    trace=[]; permitted=set()
    for line in spec.splitlines():
        cells=[c.strip() for c in line.split('|')]
        if len(cells)>7 and cells[1]=='A' and cells[4]=='READ_PRIVILEGE':
            if s02_scope(cells[6]):permitted.add((cells[2],cells[3]))
            if (cells[2],cells[3]) in columns() and cells[2] in SIGNERS:
                trace.append(dict(relation=cells[2],column=cells[3],consumer=cells[5],entrypoint=cells[6]))
    required={(r,c) for r,c in columns() if r in SIGNERS}
    missing=required-permitted
    physical_missing={(gate.OWNERS['A'],r,c,'select') for r,c in required}-grants
    # Explicit synthetic relational witness only; no retained runtime fixture.
    positive={r:[{c:c for rr,c in columns() if rr==r}] for r in {r for r,c in columns()}}
    a=positive['public.s2a_accepted_attestation'][0]
    k=positive['public.s2a_signer_key_revision'][0]
    g=positive['public.s2a_signer_authority_revision'][0]
    for row in (a,k,g):row['organization_id']='organization';row['signer_key_id']='key'
    a.update(manifest_id='manifest',signer_key_revision=1,signer_authority_revision=1,verified_at='5')
    k.update(revision=1,state='ACTIVE',valid_from='1',effective_at='1')
    g.update(revision=1,signer_key_revision=1,state='ENABLED',valid_from='1',valid_until='9',decided_at='1',
             approval_source_id='approval-source',signer_role='S2A_FIELD_PROOF_APPROVER',
             approval_action='S2A_FIELD_PROOF_APPROVAL',permission='TRANSACTION_IDENTITY_DECISION_WRITE')
    k['lineage_fingerprint']=a['signer_key_lineage_fingerprint']
    negative=copy.deepcopy(positive);negative['public.s2a_signer_key_revision'][0]['state']='REVOKED'
    def project(rows):return {r:[{c:v for c,v in row.items() if (r,c) in permitted} for row in items] for r,items in rows.items()}
    return dict(gate='G3F.3B_S02_ACCEPTED_ARTIFACT_CONSUMER_AUTHORITY',
        status='HOLD_CONSUMER_AUTHORITY' if missing else 'SOURCE_CONSUMER_AUTHORITY_CLOSED',
        dependency='S02 INSPECT -> PostgresOfflineFieldProofReconciler.inspect -> accepted -> acceptedArtifact',
        required_signer_columns=sorted(required),missing_s02_consumer_columns=sorted(missing),
        missing_physical_grants=sorted(physical_missing),current_signer_consumer_inventory=trace,
        witness=dict(scope='SYNTHETIC_SIGNER_JOIN_ONLY_NOT_JCA_OR_RUNTIME_FIXTURE',
            positive_eligible_rows=witness(positive),revoked_key_eligible_rows=witness(negative),
            s02_authorized_projection_identical=project(positive)==project(negative)),
        unresolved_authority_blocker_count=1 if missing else 0,
        proposed_resolution='Independent exact S02 consumer traceability for existing A signer-key/authority reads required by frozen inspect.acceptedArtifact; no new columns or grants.',
        physical_grant_count=len(grants),spec_amended=False,grants_widened=False,
        retained_fixture_modified=False,database_connection_attempted=False,runtime_proof=False)


if __name__=='__main__':
    report=audit()
    (gate.ROOT/'docs/evidence/PACKAGE-0090-G3F-3B-S02-CONSUMER-AUTHORITY.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,indent=2))
