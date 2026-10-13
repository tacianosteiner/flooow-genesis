"""Mutation checks against unsupported source coverage and authority promotion."""
import copy
import argparse
import io
import json
import unittest
from pathlib import Path
import package_0090_activation_authority_audit as audit


class AuditMutationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = json.loads((audit.q.ROOT / audit.OUTPUT / 's04-source-addendum.json').read_text())

    def rejects(self, mutate):
        value = copy.deepcopy(self.fixture); mutate(value)
        with self.assertRaises((ValueError, RuntimeError, AssertionError)):
            audit.validate_static_addendum(value)

    def test_source_paths_and_coverage(self):
        audit.validate_static_addendum(self.fixture)

    def test_missing_call_is_denied(self):
        self.rejects(lambda v: v['call_sites'].pop())

    def test_duplicate_group_membership_is_denied(self):
        self.rejects(lambda v: v['candidate_contexts'][0]['site_indices'].append(0))

    def test_static_runtime_promotion_is_denied(self):
        self.rejects(lambda v: v['call_sites'][0].update(status='BOUND', runtime_oid=42))

    def test_global_promotion_is_denied(self):
        self.rejects(lambda v: v.update(global_bound=1, global_unbound=v['global_unbound'] - 1))

    def test_changed_operator_is_denied(self):
        self.rejects(lambda v: v['operator_and_implicit_expression_sites'][0].update(ast={}))

    def test_proposal_and_boolean_do_not_supply_independent_approval(self):
        self.assertFalse(audit.authority_gate({'independent_activation_approval': True, 'approved_recipe': 'PROPOSED'}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--evidence-directory')
    args = parser.parse_args()
    output = io.StringIO()
    result = unittest.TextTestRunner(stream=output, verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(AuditMutationTests))
    print(output.getvalue())
    if args.evidence_directory:
        folder = Path(args.evidence_directory)
        (folder / 'unit-tests.txt').write_text(output.getvalue(), encoding='utf-8')
        audit.ledger.write(folder, 'unit-tests.json', {'tests': result.testsRun, 'failures': len(result.failures),
            'errors': len(result.errors), 'skipped': len(result.skipped), 'all_pass': result.wasSuccessful(),
            'scope': 'STATIC_MUTATION_COVERAGE_ONLY_NOT_ACTIVATION_NATIVE_READINESS_OR_S04_RUNTIME'})
    raise SystemExit(0 if result.wasSuccessful() else 1)
