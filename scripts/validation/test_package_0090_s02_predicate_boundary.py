"""Frozen signer-query negatives; deliberately not S02 or JCA runtime proof."""
import copy
import unittest
import package_0090_s02_consumer_audit as consumer


class FrozenSignerPredicateTests(unittest.TestCase):
    def test_exact_frozen_join_negative_matrix(self):
        positive = consumer.synthetic_rows()
        self.assertEqual(consumer.witness(positive), 1)
        mutations = [
            ('s2a_signer_key_revision', 'state', 'REVOKED'),
            ('s2a_signer_key_revision', 'signer_key_fingerprint', 'wrong'),
            ('s2a_signer_key_revision', 'lineage_fingerprint', 'wrong'),
            ('s2a_signer_key_revision', 'subject_public_key_info_der', 'wrong'),
            ('s2a_signer_key_revision', 'algorithm_id', 'wrong'),
            ('s2a_signer_authority_revision', 'state', 'DISABLED'),
            ('s2a_signer_authority_revision', 'signer_authority_fingerprint', 'wrong'),
            ('s2a_signer_authority_revision', 'approval_source_id', 'wrong'),
            ('s2a_signer_authority_revision', 'approval_action', 'wrong'),
            ('s2a_signer_authority_revision', 'signer_role', 'wrong'),
            ('s2a_signer_authority_revision', 'permission', 'wrong'),
            ('s2a_signer_key_revision', 'valid_from', '6'),
            ('s2a_signer_key_revision', 'effective_at', '6'),
            ('s2a_signer_authority_revision', 'valid_from', '6'),
            ('s2a_signer_authority_revision', 'valid_until', '5'),
            ('s2a_signer_authority_revision', 'decided_at', '6'),
        ]
        for relation, column, value in mutations:
            with self.subTest(relation=relation, column=column):
                rows = copy.deepcopy(positive)
                rows['public.' + relation][0][column] = value
                self.assertEqual(consumer.witness(rows), 0)

    def test_foreign_or_absent_organization_has_no_eligible_row(self):
        for foreign in (True, False):
            rows = consumer.synthetic_rows()
            for items in rows.values():
                if foreign:
                    for row in items:
                        row['organization_id'] = 'foreign'
                else:
                    items.clear()
            self.assertEqual(consumer.witness(rows), 0)

    def test_ambiguous_rows_cannot_satisfy_single_row_cardinality(self):
        for relation in ('s2a_accepted_attestation', 's2a_signer_key_revision',
                         's2a_signer_authority_revision'):
            with self.subTest(relation=relation):
                rows = consumer.synthetic_rows()
                items = rows['public.' + relation]
                items.append(copy.deepcopy(items[0]))
                self.assertEqual(consumer.witness(rows), 2)


if __name__ == '__main__':
    unittest.main()
