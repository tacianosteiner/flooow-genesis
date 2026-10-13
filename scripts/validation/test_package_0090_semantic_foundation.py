"""Mutation tests for fail-closed ledger/fixture foundation; no false semantic PASS."""
import copy
import argparse
import json
from pathlib import Path
import sys
import unittest
from package_0090_semantic_validator import validate
from package_0090_semantic_ledger import fixture_manifest, locate
from package_0090_active_foundation import quote


class SemanticFoundationTest(unittest.TestCase):
    def setUp(self):
        self.ledger = {'records': [{'shape_id': 'shape-1', 'occurrence_ids': ['site-1'], 'call_count': 1,
            'source_functions': ['public.helper(text)'], 'consumer_trace_ids': ['site-1'], 'semantic_status': 'UNBOUND'}]}
        self.sites = [{'occurrence_id': 'site-1'}]
        self.contexts = [{'signature': 'public.helper(text)'}]
        self.traces = {'site-1': {'semantic_proven': False}}

    def check(self, closure=False):
        return validate(self.ledger, self.sites, self.contexts, self.traces, closure)

    def test_structural_integrity_does_not_close_semantics(self):
        self.assertTrue(self.check()['pass'])
        self.assertFalse(self.check(True)['pass'])

    def test_omitted_occurrence_denied(self):
        self.ledger['records'][0]['occurrence_ids'] = []
        self.assertFalse(self.check()['pass'])

    def test_duplicate_assignment_denied(self):
        r = copy.deepcopy(self.ledger['records'][0]); r['shape_id'] = 'shape-2'
        self.ledger['records'].append(r)
        self.assertIn('OCCURRENCE_ASSIGNED_MULTIPLE_TIMES', self.check()['issues'])

    def test_unknown_source_signature_denied(self):
        self.ledger['records'][0]['source_functions'] = ['public.unapproved()']
        self.assertFalse(self.check()['pass'])

    def test_missing_consumer_denied(self):
        self.traces.clear()
        self.assertFalse(self.check()['pass'])

    def test_forged_bound_flag_denied(self):
        r = self.ledger['records'][0]; r['semantic_status'] = 'BOUND'
        r.update(grouping_equivalence_proven=False, runtime_resolution_status='UNPROVEN')
        self.assertFalse(self.check()['pass'])

    def test_golden_policy_is_not_ACTIVE_fixture(self):
        f = fixture_manifest()
        self.assertEqual(f['canonical_policy_sha256'], 'e840fcadac2d5198a91cdb7b2345a31d4776cb3ead6e8b697391a4461a1a253d')
        self.assertFalse(f['active_fixture_contract_ready'])
        self.assertFalse(f['full_fixture_ready'])
        self.assertEqual(f['components_required'], f['components_present'] + f['components_missing'])
        self.assertFalse(f['production_authority'])

    def test_only_redundant_setop_type_wrapper_relocated(self):
        node = {'SelectStmt': {'larg': {'op': 'SETOP_NONE', 'targetList': [1]}}}
        actual, path = locate(node, ['SelectStmt', 'larg', 'SelectStmt', 'targetList', 0])
        self.assertEqual(actual, 1)
        self.assertEqual(path, ['SelectStmt', 'larg', 'targetList', 0])
        with self.assertRaises(KeyError):
            locate({'SelectStmt': {}}, ['SelectStmt', 'arbitrary_missing_wrapper'])

    def test_literal_SQL_escaping(self):
        self.assertEqual(quote("x'); SELECT true;--"), "'x''); SELECT true;--'")
        self.assertEqual(quote(None), 'NULL')
        self.assertEqual(quote(False), 'FALSE')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--evidence-directory')
    args, remaining = parser.parse_known_args()
    if args.evidence_directory:
        folder = Path(args.evidence_directory)
        suite = unittest.defaultTestLoader.loadTestsFromTestCase(SemanticFoundationTest)
        with (folder / 'unit-tests.txt').open('w', encoding='utf-8') as output:
            result = unittest.TextTestRunner(stream=output, verbosity=2).run(suite)
        (folder / 'unit-tests.json').write_text(json.dumps({'tests_run': result.testsRun, 'failures': len(result.failures),
            'errors': len(result.errors), 'skipped': len(result.skipped)}, indent=2) + '\n', encoding='utf-8')
        print('UNIT_TESTS=' + str(result.testsRun) + '; PASS=' + str(result.wasSuccessful()))
        raise SystemExit(int(not result.wasSuccessful()))
    unittest.main(argv=[sys.argv[0]] + remaining)
