"""Offline relational/SQL AST tests; neither PG execution nor S01 closure."""
import copy
import json
import unittest
from pglast.parser import parse_sql_json
import package_0090_s01_readiness as s01
import package_0090_source_gate as gate


class S01ReadinessTests(unittest.TestCase):
    def setUp(self):
        self.header = dict(organization_id='org-a',mercado_livre_connection_id='ml-a',omie_connection_id='omie-a')
        self.rows = [dict(zip(s01.COLUMNS,('org-a',self.header[field],provider,kind,'ACTIVE',version)))
                     for field,provider,kind,version in s01.EXPECTED]

    def assertDenied(self, mutate):
        # Instantiate each negative independently for both bound connections.
        for index in range(2):
            with self.subTest(connection=index):
                rows = copy.deepcopy(self.rows)
                mutate(rows,index)
                self.assertFalse(s01.predicate(rows,self.header,index))

    def test_both_bound_connections_positive(self):
        self.assertTrue(all(s01.predicate(self.rows,self.header,i) for i in range(2)))

    def test_suspended_connection(self):
        self.assertDenied(lambda rows,i: rows[i].update(status='SUSPENDED'))

    def test_wrong_provider(self):
        self.assertDenied(lambda rows,i: rows[i].update(provider_key='wrong'))

    def test_wrong_credential_kind(self):
        self.assertDenied(lambda rows,i: rows[i].update(credential_kind='wrong'))

    def test_wrong_binding_version(self):
        self.assertDenied(lambda rows,i: rows[i].update(binding_version=2))

    def test_foreign_organization(self):
        self.assertDenied(lambda rows,i: rows[i].update(organization_id='org-b'))

    def test_foreign_connection(self):
        self.assertDenied(lambda rows,i: rows[i].update(connection_id='connection-b'))

    def test_missing_connection(self):
        self.assertDenied(lambda rows,i: rows.pop(i))

    def test_duplicate_match(self):
        self.assertDenied(lambda rows,i: rows.append(copy.deepcopy(rows[i])))

    def test_ambiguous_identity_with_one_valid_match(self):
        def mutate(rows,i):
            other = copy.deepcopy(rows[i]); other['status']='SUSPENDED'; rows.append(other)
        self.assertDenied(mutate)

    def test_each_null_field(self):
        for column in s01.COLUMNS:
            with self.subTest(column=column):
                self.assertDenied(lambda rows,i: rows[i].update({column:None}))

    def test_missing_header_identity_denies(self):
        for field in ('organization_id','mercado_livre_connection_id','omie_connection_id'):
            header = dict(self.header); header[field]=None
            for index in range(2):
                if field=='organization_id' or s01.EXPECTED[index][0]==field:
                    self.assertFalse(s01.predicate(self.rows,header,index))

    def test_predicate_ast_exact_private_six_column_read(self):
        for index,sql in enumerate(s01.CONNECTION_SQL):
            statement = json.loads(parse_sql_json(sql))['stmts'][0]['stmt']['SelectStmt']
            self.assertFalse(statement.get('lockingClause') or statement.get('intoClause'))
            relation=statement['fromClause'][0]['RangeVar']
            self.assertEqual((relation['schemaname'],relation['relname']),('public','integration_connection'))
            columns=set(); calls=set(); headers=set()
            def walk(node):
                if isinstance(node,list):
                    for child in node: walk(child)
                elif isinstance(node,dict):
                    if 'ColumnRef' in node:
                        fields=tuple(f['String']['sval'] for f in node['ColumnRef']['fields'])
                        self.assertEqual(len(fields),2)
                        if fields[0]=='c': columns.add(fields[1])
                        else:
                            self.assertEqual(fields[0],'header_record'); headers.add(fields[1])
                    if 'ParamRef' in node: self.fail('Caller selector')
                    if 'FuncCall' in node:
                        calls.add(tuple(f['String']['sval'] for f in node['FuncCall']['funcname']))
                    for child in node.values(): walk(child)
            walk(statement)
            self.assertEqual(columns,set(s01.COLUMNS))
            self.assertEqual(headers,{'organization_id',s01.EXPECTED[index][0]})
            self.assertEqual(calls,{('pg_catalog','count'),('pg_catalog','bool_and')})
            # A single boolean expression is the entire projection, never raw metadata.
            self.assertEqual(len(statement['targetList']),1)
            self.assertEqual(set(statement['targetList'][0]['ResTarget']['val']),{'BoolExpr'})

    def test_sql_predicate_matches_independent_oracle(self):
        # Evaluate the actual generated SQL relationally in disposable in-memory SQLite.
        # This tests three-valued predicates/cardinality, not PostgreSQL/PLpgSQL semantics.
        import sqlite3
        db=sqlite3.connect(':memory:')
        class BoolAnd:
            def __init__(self): self.values=[]
            def step(self,v):
                if v is not None:self.values.append(bool(v))
            def finalize(self): return int(all(self.values)) if self.values else None
        db.create_aggregate('bool_and',1,BoolAnd)
        db.execute('CREATE TABLE integration_connection(organization_id TEXT,connection_id TEXT,provider_key TEXT,credential_kind TEXT,status TEXT,binding_version INTEGER)')
        cases=[self.rows,[],self.rows+[self.rows[0]],self.rows+[dict(self.rows[0],status='SUSPENDED')]]
        for column in s01.COLUMNS:
            for value in (None,'wrong',2):
                for index in range(2):
                    rows=copy.deepcopy(self.rows); rows[index][column]=value; cases.append(rows)
        for rows in cases:
            db.execute('DELETE FROM integration_connection')
            db.executemany('INSERT INTO integration_connection VALUES(?,?,?,?,?,?)',
                           [tuple(r[c] for c in s01.COLUMNS) for r in rows])
            for index,sql in enumerate(s01.CONNECTION_SQL):
                sql=sql.replace('pg_catalog.','').replace('public.','')
                sql=sql.replace('header_record.organization_id',':org').replace('header_record.'+s01.EXPECTED[index][0],':id')
                actual=db.execute(sql,dict(org=self.header['organization_id'],id=self.header[s01.EXPECTED[index][0]])).fetchone()[0]
                self.assertEqual(bool(actual),s01.predicate(rows,self.header,index))
        db.close()

    def test_organization_private_active_predicate(self):
        import sqlite3
        db=sqlite3.connect(':memory:')
        class BoolAnd:
            def __init__(self): self.values=[]
            def step(self,v):
                if v is not None:self.values.append(bool(v))
            def finalize(self): return int(all(self.values)) if self.values else None
        db.create_aggregate('bool_and',1,BoolAnd)
        db.execute('CREATE TABLE integration_organization(organization_id TEXT,status TEXT)')
        sql=s01.ORGANIZATION_SQL.replace('pg_catalog.','').replace('public.','').replace('header_record.organization_id','?')
        for rows,expected in (([('org-a','ACTIVE')],True),([],False),([('org-a','SUSPENDED')],False),
                              ([('org-b','ACTIVE')],False),([('org-a',None)],False),
                              ([('org-a','ACTIVE'),('org-a','SUSPENDED')],False)):
            db.execute('DELETE FROM integration_organization')
            db.executemany('INSERT INTO integration_organization VALUES(?,?)',rows)
            self.assertEqual(bool(db.execute(sql,('org-a',)).fetchone()[0]),expected)
        db.close()

    def test_q_sentinel_candidate_exact_signature(self):
        expression=json.loads(parse_sql_json('SELECT '+s01.Q_SENTINEL_SQL))['stmts'][0]['stmt']['SelectStmt']['targetList'][0]['ResTarget']['val']['FuncCall']
        self.assertEqual(tuple(n['String']['sval'] for n in expression['funcname']),('public','offline_internal_readiness'))
        self.assertEqual(len(expression['args']),8)
        sentinel=expression['args'][-1]['TypeCast']
        self.assertEqual(sentinel['arg']['A_Const']['sval']['sval'],'\\x')
        self.assertEqual(tuple(n['String']['sval'] for n in sentinel['typeName']['names']),('pg_catalog','bytea'))

    def test_exact_acl_and_target_boundary(self):
        report=s01.audit()
        self.assertEqual(report['physical_grant_count'],1040)
        self.assertEqual(report['unresolved_authority_blocker_count'],0)
        self.assertEqual(report['a_ml_source_read_columns'],sorted(('organization_id','connection_id','capability','input_progress_version','record_ordinal','external_order_ref')))
        self.assertTrue(report['s01_implemented'])
        self.assertEqual(len(report['target_missing_select']),0)
        self.assertEqual(report['target_witness']['positive_target_result'],True)
        self.assertEqual(report['target_witness']['negative_target_result'],False)
        self.assertFalse(report['target_witness']['a_authorized_projection_identical'])

    def test_each_missing_or_extra_connection_privilege_rejected(self):
        source=(gate.ROOT/gate.V043).read_text(encoding='utf-8-sig')
        spec=(gate.ROOT/gate.SPEC).read_text(encoding='utf-8-sig')
        for column in s01.COLUMNS:
            with self.subTest(missing=column):
                grant='GRANT SELECT ('+column+') ON TABLE public.integration_connection TO '+s01.OWNER+';'
                with self.assertRaisesRegex(ValueError,'Column ACL mismatch'):
                    gate.prerequisite_checks(source.replace(grant,''),spec)
        for privilege in ('SELECT (secret_ref)','SELECT (credential_binding)','UPDATE (connection_id)','SELECT'):
            with self.subTest(extra=privilege):
                with self.assertRaises(ValueError):
                    gate.prerequisite_checks(source+'\nGRANT '+privilege+' ON TABLE public.integration_connection TO '+s01.OWNER+';',spec)


if __name__=='__main__': unittest.main()
