"""Retained evidence/selection/codec checks; never connects to PostgreSQL."""
import copy
import hashlib
import json
import re
import struct
import subprocess
import unittest

import package_0090_evidence_fixture as codec
import package_0090_source_gate as source_gate


class EvidenceFixtureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = codec.retained_fixture()
        cls.goldens = codec.goldens()

    def test_retained_fixture_and_goldens_are_frozen(self):
        self.assertEqual(json.loads(codec.OUTPUT.read_text(encoding='utf-8')), self.fixture)
        self.assertEqual(json.loads(codec.GOLDENS.read_text(encoding='utf-8')), self.goldens)

    def test_all_fixture_columns_and_foreign_keys_against_frozen_schema(self):
        from pglast.parser import parse_sql_json
        creates = {}
        for name in ('V004__create_integration_control_plane.sql', 'V006__create_inventory_source_ledger.sql',
                     'V021__create_mercado_livre_order_source_observation.sql',
                     'V022__create_marketplace_order_identity_and_occurrence_promotion.sql',
                     'V026__create_omie_transaction_evidence.sql',
                     'V033__create_omie_transaction_evidence_v3_source_evidence.sql'):
            raw = (codec.ROOT / source_gate.MIGRATIONS / name).read_text(encoding='utf-8-sig')
            for statement in json.loads(parse_sql_json(raw))['stmts']:
                create = statement['stmt'].get('CreateStmt')
                if create:
                    creates[create['relation']['relname']] = create
        for table, rows in self.fixture['tables'].items():
            columns = {e['ColumnDef']['colname']: e['ColumnDef'] for e in creates[table]['tableElts'] if 'ColumnDef' in e}
            for row in rows:
                self.assertEqual(set(row), set(columns), table)
                for name, column in columns.items():
                    kinds = {c['Constraint']['contype'] for c in column.get('constraints', [])}
                    if 'CONSTR_NOTNULL' in kinds or 'CONSTR_PRIMARY' in kinds:
                        self.assertIsNotNone(row[name], table+'.'+name)
                for element in creates[table]['tableElts']:
                    c = element.get('Constraint', {})
                    if c.get('contype') == 'CONSTR_FOREIGN':
                        local = [k['String']['sval'] for k in c['fk_attrs']]
                        remote = [k['String']['sval'] for k in c['pk_attrs']]
                        target = self.fixture['tables'][c['pktable']['relname']]
                        self.assertEqual(sum(all(row[a] == r[b] for a,b in zip(local,remote)) for r in target), 1)

    def test_exact_frozen_preimage_expression_order(self):
        source = (codec.ROOT / source_gate.MIGRATIONS / 'V041__create_s2a_accepted_attestation.sql').read_text(encoding='utf-8-sig')
        function = source.split('CREATE FUNCTION public.s2a_v041_evidence_fingerprint(',1)[1].split('END $$;',1)[0]
        expression = function.split('bytes:=',1)[1].split("RETURN encode(sha256(bytes),'hex');",1)[0]
        calls = re.findall(r'public\.s2a_v041_(text|nullable_text|local)\(([^)]*)\)', expression)
        self.assertEqual(calls, [('text',v) for v in (
            "'FLOOOW:S2A:EVIDENCE-BINDING:1'", 'p_organization_id::text', 'p_marketplace_order_id::text',
            'p_mercado_livre_connection_id::text', "'marketplace-economic.order-source'",
            'ml.source_input_progress_version::text', 'ml.source_record_ordinal::text', 'ml.marketplace_key',
            'ml.external_order_id', 'ml.currency', 'ml.outcome', 'p_omie_connection_id::text',
            "'marketplace-economic.omie-transaction-evidence.reacquisition-v3'",
            'omie.input_progress_version::text', 'omie.record_ordinal::text', 'p_source_order_reference')]
            + [('nullable_text','omie.source_integration_ref'), ('nullable_text','omie.currency'),
               ('text','omie.semantic_fingerprint_version::text'), ('text','omie.source_evidence_semantic_fingerprint'),
               ('local','omie.provider_revision')])
        self.assertIn("SELECT int4send(octet_length(v))||v", source)
        self.assertIn("public.s2a_v041_text('PRESENT')||public.s2a_v041_text(v)", source)
        self.assertIn("to_char(v,'YYYY-MM-DD\"T\"HH24:MI:SS.US')", source)

    def test_independent_jvm_full_bytes_and_digests(self):
        result = subprocess.run(['java', str(codec.ROOT/'scripts/validation/Package0090EvidenceFixture.java')],
                                check=True, capture_output=True, text=True)
        actual = dict(line.split('=',1) for line in result.stdout.splitlines())
        expected = {'POLICY_HEX': self.goldens['policy']['canonical_policy_hex'],
                    'POLICY_SHA256': self.goldens['policy']['canonical_policy_sha256'], 'NON_NFC': 'REJECT'}
        slots = codec.slots([(1,101,'v'),(2,102,'i'),(3,103,'e'),(4,104,'a')])
        expected.update(SLOTS_HEX=slots.hex(), SLOTS_SHA256=hashlib.sha256(slots).hexdigest())
        for v in self.goldens['vectors']:
            for key, suffix in (('evidence_preimage','EVIDENCE'),('manifest','MANIFEST'),('binding','BINDING')):
                expected[v['vector']+'_'+suffix+'_HEX'] = v[key]['hex']
                expected[v['vector']+'_'+suffix+'_SHA256'] = v[key]['sha256']
        v3 = self.goldens['vectors'][2]['encoder_only_mutation']
        expected.update(VECTOR_3_ENCODER_ONLY_HEX=v3['hex'], VECTOR_3_ENCODER_ONLY_SHA256=v3['sha256'])
        self.assertEqual(actual, expected)

    def test_selected_rows_and_integrity_positive(self):
        p, registry, b, v3, revision = codec.select_evidence(self.fixture)
        self.assertEqual((p['source_input_progress_version'], p['source_record_ordinal'], p['outcome']), (1,0,'PROMOTED'))
        self.assertEqual((b['input_progress_version'], b['record_ordinal'], revision), (1,0,codec.LOCAL))
        self.assertEqual(registry['currency'], b['currency'])
        self.assertEqual(v3['source_evidence_semantic_fingerprint'], '0'*63+'1')

    def test_missing_extra_duplicate_and_conflicting_rows_denied(self):
        for table in self.fixture['tables']:
            for action in ('delete','duplicate'):
                changed = copy.deepcopy(self.fixture)
                if action == 'delete': changed['tables'][table].pop()
                else: changed['tables'][table].append(copy.deepcopy(changed['tables'][table][0]))
                with self.subTest(table=table, action=action), self.assertRaises(ValueError):
                    codec.evidence_preimage(changed)
        changed = copy.deepcopy(self.fixture)
        conflict = copy.deepcopy(changed['tables']['integration_omie_transaction_evidence_v3'][0])
        conflict['source_evidence_semantic_fingerprint'] = 'f'*64
        changed['tables']['integration_omie_transaction_evidence_v3'].append(conflict)
        with self.assertRaises(ValueError): codec.evidence_preimage(changed)

    def test_selection_integrity_mutations_denied(self):
        cases = (
            ('marketplace_order_occurrence_source_promotion','source_record_ordinal',1),
            ('marketplace_order_occurrence_source_promotion','outcome','IDENTITY_CONFLICT'),
            ('marketplace_order_identity_registry','currency','USD'),
            ('integration_mercado_livre_order_source_observation','external_order_ref','other'),
            ('integration_omie_transaction_evidence','source_order_ref','other'),
            ('integration_omie_transaction_evidence','source_integration_ref','other'),
            ('integration_omie_transaction_evidence','currency','USD'),
            ('integration_omie_transaction_evidence','record_ordinal',-1),
            ('integration_omie_transaction_evidence_v3','semantic_fingerprint_version',2),
            ('integration_omie_transaction_evidence_v3','source_evidence_semantic_fingerprint','bad'),
            ('integration_omie_transaction_evidence_v3','provider_created_local',None),
            ('integration_omie_transaction_evidence_v3','provider_modified_local','1969-12-31T23:59:59.999999'),
            ('integration_connector_page_commit','record_count',0),
            ('integration_connector_progress','progress_version',1),
        )
        for table,field,value in cases:
            changed = copy.deepcopy(self.fixture)
            for row in changed['tables'][table]: row[field] = value
            with self.subTest(table=table,field=field), self.assertRaises(ValueError): codec.evidence_preimage(changed)

    def test_null_vs_empty_and_unicode(self):
        self.assertNotEqual(codec.nullable_frozen_text(None), codec.nullable_frozen_text(''))
        with self.assertRaises(ValueError): codec.derive('INVALID', source='cafe\u0301')
        for n in (1,6,7,8,9,10,999):
            self.assertEqual(codec.uuid.UUID(codec.uid(n).upper()).bytes, codec.uuid.UUID(int=n).bytes)

    def test_slot_set_shuffle_and_duplicate_rejection(self):
        records = [(1,101,'v'),(2,102,'i'),(3,103,'e'),(4,104,'a')]
        self.assertEqual(codec.slots(records), codec.slots(records[::-1]))
        self.assertEqual(codec.slots(records).hex(), '000000040000000a010000006500000001760000000a020000006600000001690000000a030000006700000001650000000a04000000680000000161')
        for changed in (records[:-1], records+[records[0]], records[:3]+[(4,101,'a')], records[:3]+[(4,104,'v')]):
            with self.assertRaises(ValueError): codec.slots(changed)

    def test_every_binding_field_mutation_changes_digest(self):
        v1 = self.goldens['vectors'][0]
        payloads = codec.binding_payloads(bytes.fromhex(v1['manifest']['sha256']),
                                         bytes.fromhex(self.goldens['policy']['canonical_policy_sha256']))
        domain = 'FLOOOW/OFFLINE-FIELD-PROOF/BINDING/V1'
        for index in range(38):
            changed = payloads.copy()
            mutated = bytearray(changed[index]); mutated[-1] ^= 1; changed[index] = bytes(mutated)
            with self.subTest(tag=index+1):
                self.assertNotEqual(hashlib.sha256(codec.frame(domain, changed)).hexdigest(), v1['binding']['sha256'])

    def test_derivatives_propagate_and_no_signature_claim(self):
        v1,v2,v3 = self.goldens['vectors']
        self.assertNotEqual(v1['evidence_fingerprint'],v2['evidence_fingerprint'])
        self.assertEqual(v1['evidence_fingerprint'],v3['evidence_fingerprint'])
        self.assertEqual(v1['manifest_fields'][20],codec.uid(15))
        self.assertEqual(v3['manifest_fields'][20],codec.uid(999))
        self.assertNotEqual(v3['encoder_only_mutation']['sha256'],v3['binding']['sha256'])
        for vector in (v1,v2,v3): self.assertFalse(vector['signed_acceptance_proof'])

    def test_semantic_validation_positive_and_encoder_only_rejection(self):
        policy = bytes.fromhex(self.goldens['policy']['canonical_policy_hex'])
        for v in self.goldens['vectors']:
            self.assertEqual(codec.validate_binding(bytes.fromhex(v['binding']['hex']),
                             bytes.fromhex(v['manifest']['hex']), policy), v['manifest_fields'])
        v1,v2,v3 = self.goldens['vectors']
        with self.assertRaises(ValueError):
            codec.validate_binding(bytes.fromhex(v3['encoder_only_mutation']['hex']),
                                   bytes.fromhex(v1['manifest']['hex']), policy)

    def test_binding_truncation_null_unknown_order_count_and_trailing_denied(self):
        v = self.goldens['vectors'][0]; raw = bytes.fromhex(v['binding']['hex'])
        domain = 'FLOOOW/OFFLINE-FIELD-PROOF/BINDING/V1'
        for end in range(len(raw)):
            with self.subTest(end=end), self.assertRaises(ValueError): codec.decode_frame(raw[:end],domain,38)
        first = 4+len(domain)+2
        for offset, replacement in ((first,b'\x00\x02'), (first+6,b'\x00'),
                                    (first+2,b'\xff\xff\xff\xff'), (4+len(domain),b'\x00\x25')):
            changed = bytearray(raw); changed[offset:offset+len(replacement)] = replacement
            with self.assertRaises(ValueError): codec.decode_frame(bytes(changed),domain,38)
        with self.assertRaises(ValueError): codec.decode_frame(raw+b'\x00',domain,38)


if __name__ == '__main__': unittest.main()
