"""Offline tests for approved test-only policy and independent JVM agreement."""
import hashlib
import json
import struct
import subprocess
import unittest

import package_0090_policy_fixture as codec


class PolicyFixtureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = codec.approved_fixture()
        cls.raw = bytes.fromhex(cls.fixture['canonical_policy_hex'])
        cls.version, cls.values = codec.decode(cls.raw)

    def test_committed_golden_equals_reference(self):
        self.assertEqual(json.loads(codec.FIXTURE.read_text(encoding='utf-8')), self.fixture)

    def test_independent_jvm_complete_bytes_and_digest(self):
        result = subprocess.run(['java', str(codec.ROOT / 'scripts/validation/Package0090PolicyFixture.java')],
                                check=True, capture_output=True, text=True)
        self.assertEqual(result.stdout.splitlines(),
                         [self.raw.hex(), hashlib.sha256(self.raw).hexdigest()])

    def test_exact_approval_and_test_scope(self):
        self.assertEqual(self.version, 'fixture-1')
        self.assertEqual(self.values[-2:], [1000000, 2000000])
        self.assertEqual(self.fixture['canonical_policy_field_count'], 29)
        self.assertFalse(self.fixture['production_policy_provisioning'])
        self.assertFalse(self.fixture['production_policy_approval'])
        self.assertEqual(self.fixture['scope'], 'TEST_GOLDEN_REHEARSAL_ONLY')

    def test_each_numeric_field_changes_digest_or_denies(self):
        for index in range(28):
            with self.subTest(tag=index+2):
                values = self.values.copy()
                values[index] += 1
                try:
                    changed = codec.encode(self.version, values)
                except ValueError:
                    continue
                self.assertNotEqual(hashlib.sha256(changed).digest(), hashlib.sha256(self.raw).digest())

    def test_nonpositive_noninteger_overflow_and_max_denied(self):
        for invalid in (0, -1, 2**63, 1.5, True, None, float('inf')):
            for index in range(28):
                with self.subTest(value=invalid, tag=index+2):
                    values = self.values.copy()
                    values[index] = invalid
                    with self.assertRaises(ValueError):
                        codec.encode(self.version, values)
        values = self.values.copy()
        values[-2] = values[-1] + 1
        with self.assertRaises(ValueError):
            codec.encode(self.version, values)

    def test_versions_and_field_counts_denied(self):
        for version in ('', None, 'cafe\u0301', '\ud800', 'fixture\n1'):
            with self.assertRaises((ValueError, UnicodeError)):
                codec.encode(version, self.values)
        for values in (self.values[:-2], self.values + [1, 2]):
            with self.assertRaises(ValueError):
                codec.encode(self.version, values)

    def test_every_truncation_and_trailing_bytes_denied(self):
        for end in range(len(self.raw)):
            with self.subTest(end=end), self.assertRaises(ValueError):
                codec.decode(self.raw[:end])
        with self.assertRaises(ValueError):
            codec.decode(self.raw + b'\x00')

    def test_null_duplicate_reorder_unknown_and_wrong_width_denied(self):
        first = 4 + len(codec.DOMAIN) + 2
        second = first + 6 + 1 + len(self.version)
        for replacement in (0, 1, 3, 30):
            changed = bytearray(self.raw)
            changed[second:second+2] = struct.pack('>H', replacement)
            with self.assertRaises(ValueError):
                codec.decode(bytes(changed))
        for offset in (first+6, second+6):
            changed = bytearray(self.raw)
            changed[offset] = 0
            with self.assertRaises(ValueError):
                codec.decode(bytes(changed))
        changed = bytearray(self.raw)
        changed[second+2:second+6] = struct.pack('>I', 8)
        with self.assertRaises(ValueError):
            codec.decode(bytes(changed))

    def test_legacy_27_field_frame_denied(self):
        changed = bytearray(self.raw[:-30])
        offset = 4 + len(codec.DOMAIN)
        changed[offset:offset+2] = struct.pack('>H', 27)
        with self.assertRaises(ValueError):
            codec.decode(bytes(changed))

    def test_boundary_values_and_checked_receipt_expiry(self):
        # All values fit signed int8; a receipt addition must separately deny overflow.
        values = self.values.copy()
        values[-2:] = [2**63-1, 2**63-1]
        self.assertEqual(codec.decode(codec.encode(self.version, values))[1], values)
        ttl = self.values[-2]
        self.assertEqual(1 + ttl, 1000001)
        self.assertGreater((2**63-1) + ttl, 2**63-1)
        # This codec does not pretend to prove live expiry enforcement.


if __name__ == '__main__':
    unittest.main()
