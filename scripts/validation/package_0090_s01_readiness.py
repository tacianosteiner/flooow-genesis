"""Offline S01 predicate/authority evidence. No DB connection or callable stub.

These are inline SQL candidates, not an authorized complete S01 entrypoint.
Target consumer authority must close before any readiness receipt is returned.
"""
import json
import copy
import re
from pathlib import Path
import package_0090_source_gate as gate

OWNER = gate.OWNERS['A']
COLUMNS = ('organization_id', 'connection_id', 'provider_key', 'credential_kind', 'status', 'binding_version')
EXPECTED = (
    ('mercado_livre_connection_id', 'br.com.mercadolivre', 'OAUTH2_AUTHORIZATION_CODE', 1),
    ('omie_connection_id', 'omie', 'STATIC_API_CREDENTIAL', 1),
)
ORGANIZATION_SQL = """SELECT pg_catalog.count(*)=1 AND pg_catalog.bool_and(o.status='ACTIVE') IS TRUE
FROM public.integration_organization o
WHERE o.organization_id=header_record.organization_id"""
CONNECTION_SQL = tuple("""SELECT pg_catalog.count(*)=1 AND pg_catalog.bool_and(
    c.provider_key='%s' AND c.credential_kind='%s'
    AND c.status='ACTIVE' AND c.binding_version=%d) IS TRUE
FROM public.integration_connection c
WHERE c.organization_id=header_record.organization_id
  AND c.connection_id=header_record.%s""" % (provider,kind,version,field)
    for field,provider,kind,version in EXPECTED)
Q_SENTINEL_SQL = """public.offline_internal_readiness(
    $1::pg_catalog.uuid,$2::pg_catalog.bytea,$3::pg_catalog.uuid,$4::pg_catalog.text,
    $5::pg_catalog.bytea,$6::pg_catalog.bytea,$7::pg_catalog.bytea,'\\x'::pg_catalog.bytea)"""


def target_query():
    producer = gate.ROOT/'applications/command-authority-ceremony/src/main/kotlin/io/flooow/ceremony/PostgresCeremonyComposition.kt'
    text = producer.read_text(encoding='utf-8-sig')
    return text.split('override fun matchesTarget',1)[1].split('"""',2)[1]


def target_columns():
    from pglast.parser import parse_sql_json
    number=iter(range(1,7))
    sql=re.sub(r'\?',lambda _: '$'+str(next(number)),target_query())
    ast=json.loads(parse_sql_json(sql))
    aliases={}; columns=set()
    def relations(node):
        if isinstance(node,list):
            for child in node: relations(child)
        elif isinstance(node,dict):
            if 'RangeVar' in node:
                r=node['RangeVar']; aliases[r['alias']['aliasname']]='public.'+r['relname']
            for child in node.values(): relations(child)
    def refs(node):
        if isinstance(node,list):
            for child in node: refs(child)
        elif isinstance(node,dict):
            if 'ColumnRef' in node:
                fields=[f['String']['sval'] for f in node['ColumnRef']['fields']]
                if len(fields)==2: columns.add((aliases[fields[0]],fields[1]))
            if 'JoinExpr' in node:
                # The frozen b/v USING identity join reads the five columns on both sides.
                j=node['JoinExpr']
                for field in j.get('usingClause',[]):
                    for relation in ('public.integration_omie_transaction_evidence','public.integration_omie_transaction_evidence_v3'):
                        columns.add((relation,field['String']['sval']))
            for child in node.values(): refs(child)
    relations(ast); refs(ast)
    return columns


def target_result(tables):
    """Run extracted producer SELECT on disposable in-memory test tables only."""
    import sqlite3
    from package_0090_evidence_fixture import uid
    db=sqlite3.connect(':memory:')
    for relation in sorted({r for r,c in target_columns()}):
        columns=sorted(c for r,c in target_columns() if r==relation)
        name=relation.split('.')[1]
        db.execute('CREATE TABLE '+name+'('+','.join(columns)+')')
        db.executemany('INSERT INTO '+name+' VALUES('+','.join('?' for c in columns)+')',
                       [tuple(row.get(c) for c in columns) for row in tables[name]])
    result=bool(db.execute(target_query(),(uid(10),uid(6),uid(9),'order-1','integration-1',uid(8))).fetchone()[0])
    db.close()
    return result


def target_witness(grants, tables):
    positive=copy.deepcopy(tables)
    # Explicit synthetic witness, never rewrite or promote the retained golden fixture.
    positive['marketplace_order_identity_registry'][0]['external_order_id']='integration-1'
    positive['integration_mercado_livre_order_source_observation'][0]['external_order_ref']='integration-1'
    negative=copy.deepcopy(positive)
    negative['integration_mercado_livre_order_source_observation'][0]['external_order_ref']='foreign-reference'
    def projection(rows):
        return {relation:[{c:row.get(c) for c in sorted(columns)} for row in items]
                for relation,items in rows.items()
                if (columns:={c for o,r,c,p in grants if o==OWNER and r=='public.'+relation and p=='select'})}
    return dict(scope='SYNTHETIC_DIFFERENTIAL_WITNESS_NOT_APPROVED_RUNTIME_FIXTURE',
                positive_target_result=target_result(positive),negative_target_result=target_result(negative),
                a_authorized_projection_identical=projection(positive)==projection(negative),
                retained_fixture_target_result=target_result(tables))


def predicate(rows, header, connection):
    """Independent relational oracle; exact cardinality, no identity fallback."""
    field, provider, kind, version = EXPECTED[connection]
    org, ident = header.get('organization_id'), header.get(field)
    if org is None or ident is None:
        return False
    bound = [row for row in rows if row.get('organization_id')==org and row.get('connection_id')==ident]
    return len(bound)==1 and all(bound[0].get(column)==value for column,value in zip(
        COLUMNS, (org, ident, provider, kind, 'ACTIVE', version)))


def audit():
    spec = (gate.ROOT/gate.SPEC).read_text(encoding='utf-8-sig')
    grants = gate.expected_column_grants(spec)
    source = (gate.ROOT/gate.V043).read_text(encoding='utf-8-sig')
    statements, _ = gate.parse(source)
    actual = gate.actual_column_grants(statements)
    if grants != actual:
        raise ValueError('Exact actual/normative ACL mismatch')
    required = {(OWNER, 'public.integration_connection', c, 'select') for c in COLUMNS}
    if {g for g in actual if g[0] == OWNER and g[1] == 'public.integration_connection'} != required:
        raise ValueError('S01 authority exceeds or lacks six-column approval')
    target_relations = ('public.marketplace_order_identity_registry',
                        'public.marketplace_order_occurrence_source_promotion',
                        'public.integration_omie_transaction_evidence',
                        'public.integration_omie_transaction_evidence_v3')
    target_rows = []
    for line in spec.splitlines():
        cells = [c.strip() for c in line.split('|')]
        if len(cells)>7 and cells[1]=='A' and cells[2] in target_relations:
            target_rows.append(dict(relation=cells[2],column=cells[3],consumer=cells[5],entrypoint=cells[6]))
    if not target_rows or any(row['entrypoint'] != 'S03' for row in target_rows):
        raise ValueError('Target boundary changed; independent review required')
    fixture = json.loads((gate.ROOT/'docs/evidence/PACKAGE-0090-G3F-3B-EVIDENCE-FIXTURE-001.json').read_text(encoding='utf-8-sig'))
    return {
        's01_connection_read_authority_approved': True,
        'spec_amended': True,
        'physical_grant_count': len(actual),
        'exact_actual_equals_normative': True,
        'a_connection_column_grants': sorted(required),
        'organization_predicate_candidate': ORGANIZATION_SQL,
        'connection_predicate_candidates': CONNECTION_SQL,
        'q_sentinel_delegation_candidate': Q_SENTINEL_SQL,
        'candidate_scope': 'OFFLINE_INLINE_PREDICATES_ONLY_NOT_CALLABLE_S01_IMPLEMENTATION',
        's01_implemented': False,
        's01_receipt_issuance_enabled': False,
        'next_gate': 'G3F.3B_S01_TARGET_CONSUMER_AUTHORITY',
        'unresolved_authority_blocker_count': 1,
        'blocker': 'SPEC8/16 requires S01 target proof; SPEC22.4 limits existing A target reads to S03/RECON.evidence and grants no A ML-source reads required by the frozen matchesTarget producer. Current approval extends only connections and organization, not target consumers or ML-source reads.',
        'target_consumer_inventory': target_rows,
        'a_ml_source_read_columns': sorted(c for o,r,c,p in actual if o==OWNER and r=='public.integration_mercado_livre_order_source_observation' and p=='select'),
        'target_producer': 'PostgresCeremonyComposition.runtime.matchesTarget',
        'target_producer_columns': sorted(target_columns()),
        'target_missing_select': sorted((OWNER,r,c,'select') for r,c in target_columns() if (OWNER,r,c,'select') not in actual),
        'target_witness': target_witness(actual,fixture['tables']),
        'retained_fixture_ml_provider': fixture['tables']['integration_connection'][0]['provider_key'],
        'frozen_producer_ml_provider': EXPECTED[0][1],
        'retained_fixture_modified': False,
        'database_connection_attempted': False,
        'runtime_proof': False,
    }


if __name__ == '__main__':
    import sys
    sys.path.insert(0, str(Path(sys.argv[1]).resolve()))
    report = audit()
    target = gate.ROOT/'docs/evidence/PACKAGE-0090-G3F-3B-S01-READINESS-AUTHORITY.json'
    target.write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print('S01_CONNECTION_ACL=PASS_EXACT; S01_FULL_READINESS=HOLD_TARGET_CONSUMER_AUTHORITY')
