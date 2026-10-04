"""Offline history projection and next consumer authority boundary tests."""
import json
import sqlite3
import unittest
import pglast
from pglast.parser import parse_sql_json,ParseError
import package_0090_source_gate as gate
import package_0090_s02_consumer_audit as boundary
from build_package_0090_read_source import build,MARKER


class ReadSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source=(gate.ROOT/gate.V043).read_text(encoding='utf-8-sig')
        cls.spec=(gate.ROOT/gate.SPEC).read_text(encoding='utf-8-sig')

    def test_s04_complete_malformed_history_preserved_and_ordered(self):
        statements,_=gate.parse(self.source)
        fn=next(s['CreateFunctionStmt'] for s in statements if s.get('CreateFunctionStmt',{}).get('funcname')==[{'String':{'sval':'public'}},{'String':{'sval':'offline_read_history'}}])
        outputs=[p['FunctionParameter'] for p in fn['parameters'] if p['FunctionParameter']['mode']=='FUNC_PARAM_TABLE']
        self.assertEqual([p['name'] for p in outputs],['installed_rank','version','type','script','checksum','success'])
        queries=[]
        def walk(node):
            if isinstance(node,list):
                for c in node:walk(c)
            elif isinstance(node,dict):
                if 'PLpgSQL_stmt_return_query' in node:queries.append(node['PLpgSQL_stmt_return_query']['query']['PLpgSQL_expr']['query'])
                for c in node.values():walk(c)
        walk(pglast.parse_plpgsql(build(self.source)))
        self.assertEqual(len(queries),1)
        db=sqlite3.connect(':memory:')
        try:
            db.execute('CREATE TABLE flyway_schema_history(installed_rank,version,type,script,checksum,success)')
            rows=[(3,'3','SQL','extra',31,False),(1,None,'SQL','malformed',None,True),(2,'2','SQL','valid',22,True)]
            db.executemany('INSERT INTO flyway_schema_history VALUES(?,?,?,?,?,?)',rows)
            self.assertEqual(db.execute(queries[0].replace('public.','')).fetchall(),sorted(rows))
            db.execute('DELETE FROM flyway_schema_history')
            self.assertEqual(db.execute(queries[0].replace('public.','')).fetchall(),[])
        finally:db.close()

    def test_s04_denies_projection_guard_lock_or_return_changes(self):
        for old,new in (('ORDER BY h.installed_rank','ORDER BY h.installed_rank LIMIT 42'),
                        ('h.checksum,h.success','h.checksum,NULL::pg_catalog.bool'),
                        ('slot_number=4','slot_number=3'),("<>'on'","<>'off'"),
                        ('FROM public.flyway_schema_history h ORDER BY h.installed_rank','FROM public.flyway_schema_history h ORDER BY h.installed_rank FOR UPDATE'),
                        ('RETURN;','INSERT INTO public.offline_binding_lifecycle(binding_id) VALUES($1); RETURN;')):
            with self.subTest(mutation=old),self.assertRaises((ValueError,ParseError)):
                gate.prerequisite_checks(self.source.split(MARKER,1)[0]+build(self.source).replace(old,new),self.spec)

    def test_approved_exact_signer_consumer_scope(self):
        report=boundary.audit()
        self.assertEqual(report['unresolved_authority_blocker_count'],0)
        self.assertEqual(len(report['required_signer_columns']),27)
        self.assertEqual(report['missing_s02_consumer_columns'],[])
        self.assertEqual(report['missing_physical_grants'],[])
        self.assertEqual(report['witness']['positive_eligible_rows'],1)
        self.assertEqual(report['witness']['revoked_key_eligible_rows'],0)
        self.assertFalse(report['witness']['s02_authorized_projection_identical'])
        self.assertFalse(report['database_connection_attempted'])
        self.assertTrue(report['spec_amended'])
        self.assertEqual(report['physical_grant_count'],1040)
        self.assertFalse(report['grants_widened'])
        self.assertTrue(all(row['consumer']=='INSPECT.acceptedArtifact/RECON.acceptedArtifact'
                            and row['entrypoint']=='S02-S03'
                            for row in report['current_signer_consumer_inventory']))


if __name__=='__main__':unittest.main()
