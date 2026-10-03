"""Offline actual-S01 predicate and authority negatives; no PostgreSQL proof."""
import copy
import json
import sqlite3
import unittest
from pglast.parser import parse_sql_json, ParseError
import package_0090_source_gate as gate
import package_0090_s01_readiness as readiness
import package_0090_s01_source as review
from build_package_0090_s01_source import bound_target, build
from package_0090_evidence_fixture import uid


class S01SourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source=(gate.ROOT/gate.V043).read_text(encoding='utf-8-sig')
        cls.spec=(gate.ROOT/gate.SPEC).read_text(encoding='utf-8-sig')
        cls.fixture=json.loads((gate.ROOT/'docs/evidence/PACKAGE-0090-G3F-3B-EVIDENCE-FIXTURE-001.json').read_text(encoding='utf-8-sig'))
        cls.positive=copy.deepcopy(cls.fixture['tables'])
        cls.positive['marketplace_order_identity_registry'][0]['external_order_id']='integration-1'
        cls.positive['integration_mercado_livre_order_source_observation'][0]['external_order_ref']='integration-1'

    def result(self,tables):
        """Execute actual generated predicates with disposable SQLite relations.

        Only dialect/schema/header substitutions; no provider/retained-fixture edit.
        """
        db=sqlite3.connect(':memory:')
        try:
            for relation in sorted({r for r,c in readiness.target_columns()}):
                columns=sorted(c for r,c in readiness.target_columns() if r==relation)
                name=relation.split('.')[1]
                db.execute('CREATE TABLE '+name+'('+','.join(columns)+')')
                db.executemany('INSERT INTO '+name+' VALUES('+','.join('?' for c in columns)+')',
                               [tuple(row.get(c) for c in columns) for row in tables[name]])
            sql=bound_target().replace('public.','').replace('header_record.',':')
            params=dict(marketplace_order_id=uid(10),organization_id=uid(6),omie_connection_id=uid(9),
                        source_order_reference='order-1',integration_reference='integration-1',mercado_livre_connection_id=uid(8))
            frozen=bool(db.execute(sql,params).fetchone()[0])
            cardinality=sql.replace('SELECT EXISTS(SELECT 1','SELECT count(*)=1',1).rstrip()[:-1]
            return frozen and bool(db.execute(cardinality,params).fetchone()[0])
        finally:db.close()

    def test_synthetic_target_only_positive_and_retained_gap(self):
        self.assertTrue(self.result(self.positive))
        self.assertFalse(self.result(self.fixture['tables']))
        self.assertEqual(self.fixture['tables']['integration_connection'][0]['provider_key'],'mercado-livre')
        self.assertEqual(readiness.EXPECTED[0][1],'br.com.mercadolivre')

    def test_every_ml_identity_dimension_denies(self):
        for column in ('external_order_ref','capability','input_progress_version','record_ordinal','connection_id','organization_id'):
            with self.subTest(column=column):
                tables=copy.deepcopy(self.positive)
                tables['integration_mercado_livre_order_source_observation'][0][column]='foreign'
                self.assertFalse(self.result(tables))

    def test_missing_observation_denies(self):
        tables=copy.deepcopy(self.positive);tables['integration_mercado_livre_order_source_observation']=[]
        self.assertFalse(self.result(tables))

    def test_ambiguous_multiple_eligible_rows_denies(self):
        for relation in ('integration_mercado_livre_order_source_observation','marketplace_order_occurrence_source_promotion',
                         'integration_omie_transaction_evidence','integration_omie_transaction_evidence_v3'):
            with self.subTest(relation=relation):
                tables=copy.deepcopy(self.positive);tables[relation].append(copy.deepcopy(tables[relation][0]))
                self.assertTrue(readiness.target_result(tables)) # frozen EXISTS stays intact
                self.assertFalse(self.result(tables)) # independent readiness rejects ambiguity

    def test_inconsistent_registry_promotion_omie_join_denies(self):
        columns=readiness.target_columns()
        for relation in ('marketplace_order_identity_registry','marketplace_order_occurrence_source_promotion',
                         'integration_omie_transaction_evidence','integration_omie_transaction_evidence_v3'):
            for column in sorted(c for r,c in columns if r=='public.'+relation):
                with self.subTest(relation=relation,column=column):
                    tables=copy.deepcopy(self.positive);tables[relation][0][column]='foreign'
                    self.assertFalse(self.result(tables))

    def test_complete_grant_inventory_and_each_missing_extra_ml_grant(self):
        statements,_=gate.parse(self.source)
        expected=gate.expected_column_grants(self.spec)
        self.assertEqual(gate.actual_column_grants(statements),expected)
        self.assertEqual(len(expected),1032)
        relation='public.integration_mercado_livre_order_source_observation'
        approved={(review.OWNER,relation,c,'select') for c in ('organization_id','connection_id','capability','input_progress_version','record_ordinal','external_order_ref')}
        self.assertEqual({g for g in expected if g[0]==review.OWNER and g[1]==relation},approved)
        for _,_,column,_ in approved:
            grant='GRANT SELECT ('+column+') ON TABLE '+relation+' TO '+review.OWNER+';'
            with self.subTest(missing=column),self.assertRaisesRegex(ValueError,'Column ACL mismatch'):
                gate.prerequisite_checks(self.source.replace(grant,''),self.spec)
        for privilege in ('SELECT','SELECT (payload)','UPDATE (record_ordinal)','INSERT (record_ordinal)'):
            with self.subTest(extra=privilege),self.assertRaises(ValueError):
                gate.prerequisite_checks(self.source+'\nGRANT '+privilege+' ON TABLE '+relation+' TO '+review.OWNER+';',self.spec)

    def test_source_effect_scope_and_guard_mutations_denied(self):
        for old,new in (('slot_number=4','slot_number=3'),('predicate_ready IS NOT TRUE','false'),
                        ('s.external_order_ref=i.external_order_id','true'),('pg_catalog.count(*)=1','pg_catalog.count(*)>=1'),
                        ("'br.com.mercadolivre'","'mercado-livre'"),('h.marketplace_order_id','NULL AS marketplace_order_id'),
                        ("'\\x'::pg_catalog.bytea)","'\\x01'::pg_catalog.bytea)"),
                        ('FROM public.integration_connection c','FROM public.integration_connection c FOR UPDATE')):
            generated=build(self.source)
            self.assertIn(old,generated)
            mutation=self.source.split('-- Public S01:',1)[0]+generated.replace(old,new)
            with self.subTest(mutation=old),self.assertRaises((ValueError,ParseError)):
                gate.prerequisite_checks(mutation,self.spec)


if __name__=='__main__':unittest.main()
