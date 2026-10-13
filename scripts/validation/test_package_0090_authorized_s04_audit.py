"""Adversarial tests of the external trusted audit reader and immutable tip."""
import copy
import io
import json
from pathlib import Path
import tempfile
import unittest
import package_0090_authorized_s04 as a


class AuditTests(unittest.TestCase):
    def setUp(self):
        self.folder = Path(tempfile.mkdtemp(prefix='flooow-0090-audit-unit-'))
        self.audit = a.Audit(self.folder / 'audit.jsonl')
        self.binding = {**a.identities(), 'deployment_id': 'TEST_ONLY_DEPLOYMENT',
                        'incarnation_id': 'TEST_ONLY_INCARNATION', 'transaction_identity': 'TEST_ONLY_TX',
                        'effective_from': '2026-10-13T00:00:00.000001+00:00'}
        self.audit.append(self.binding, 'PREPARED'); self.audit.append(self.binding, 'COMMITTED')

    def tearDown(self):
        self.audit.close()

    def test_actual_disk_chain_valid(self):
        rows = [json.loads(line) for line in self.audit.path.read_text().splitlines()]
        self.assertTrue(a.validate_audit(rows, self.audit.tip, self.binding))

    def test_missing_reconciliation_denied(self):
        with self.assertRaises(a.Denied):
            a.validate_audit(self.audit.records[:1], self.audit.records[0]['record_hash'], self.binding)

    def test_mutation_denied(self):
        rows = copy.deepcopy(self.audit.records); rows[1]['actor'] = 'FORGED'
        with self.assertRaises(a.Denied):
            a.validate_audit(rows, self.audit.tip, self.binding)

    def test_rehashed_chain_cannot_replace_trusted_tip(self):
        rows = copy.deepcopy(self.audit.records)
        rows[0]['audit_timestamp_utc'] = '2026-10-13T00:00:00.000002+00:00'
        previous = '0' * 64
        for row in rows:
            row['previous_hash'] = previous
            row['record_hash'] = a.q.sha(a.canonical({k:v for k,v in row.items() if k != 'record_hash'}))
            previous = row['record_hash']
        with self.assertRaises(a.Denied):
            a.validate_audit(rows, self.audit.tip, self.binding)

    def test_validly_hashed_UNKNOWN_is_denied(self):
        rows = copy.deepcopy(self.audit.records); rows[1]['status'] = 'UNKNOWN'
        rows[1]['record_hash'] = a.q.sha(a.canonical({k:v for k,v in rows[1].items() if k != 'record_hash'}))
        with self.assertRaises(a.Denied):
            a.validate_audit(rows, rows[1]['record_hash'], self.binding)

    def test_changed_approval_context_denied(self):
        candidate = a.identities(); candidate['change_id'] = candidate['approval_id']
        with self.assertRaises(a.Denied):
            a.validate_approval(candidate, a.identities())


if __name__ == '__main__':
    stream = io.StringIO()
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(AuditTests))
    print(stream.getvalue())
    a.save(a.OUT, 'audit-unit-tests.json', {'tests': result.testsRun, 'failures': len(result.failures),
        'errors': len(result.errors), 'skipped': len(result.skipped), 'pass': result.wasSuccessful()})
    (a.OUT / 'audit-unit-tests.txt').write_text(stream.getvalue(), encoding='utf-8')
    raise SystemExit(0 if result.wasSuccessful() else 1)
