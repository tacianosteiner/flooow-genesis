"""Precise fixture encoding/custody boundary tests; no ACTIVE success inference."""
import json
import argparse
import struct
import unittest
import sys
from pathlib import Path
import package_0090_first_positive as p


class FirstPositivePreparationTest(unittest.TestCase):
    def setUp(self):
        self.vectors = json.loads((p.ROOT / 'docs/evidence/PACKAGE-0090-G3F-3B-CODEC-GOLDENS.json').read_text())['vectors']

    def test_all_three_approved_binding_vectors_exact(self):
        for vector in self.vectors:
            header, codec = p.decode_binding(bytes.fromhex(vector['binding']['hex']))
            self.assertEqual(p.exact_fingerprint(header, codec), vector['binding']['sha256'])

    def test_one_microsecond_is_not_lost(self):
        vector = self.vectors[0]; header, codec = p.decode_binding(bytes.fromhex(vector['binding']['hex']))
        self.assertEqual(header['expires_at'], '1970-01-01T00:00:01.000001Z')
        self.assertEqual(p.exact_fingerprint(header, codec), '4731c0616a85f0beb6472309c9262382c7fe96e99fcb22129440b8ec9ad0c9f3')

    def test_changed_time_changes_binding(self):
        vector = self.vectors[0]; header, codec = p.decode_binding(bytes.fromhex(vector['binding']['hex']))
        expected = p.exact_fingerprint(header, codec)
        header['expires_at'] = '1970-01-01T00:00:01.000002Z'
        self.assertNotEqual(p.exact_fingerprint(header, codec), expected)

    def test_reordered_binding_tag_rejected(self):
        data = bytearray(bytes.fromhex(self.vectors[0]['binding']['hex']))
        offset = 4 + int.from_bytes(data[:4], 'big') + 2
        data[offset:offset+2] = struct.pack('>H', 2)
        with self.assertRaises(RuntimeError):
            p.decode_binding(bytes(data))

    def test_required_NULL_is_not_encoded_as_absence(self):
        with self.assertRaises(TypeError):
            p.frame(p.DOMAIN, [None])

    def test_commitment_tags_and_signature_bytes_preserved(self):
        values = [b'uuid16-bytes----!', b'a'*64, b'Ed25519', b'key16bytes------', b'b'*64, bytes(range(64))]
        data = p.frame(p.DOMAIN, values)
        offset = 4 + len(p.DOMAIN)
        self.assertEqual(int.from_bytes(data[offset:offset+2], 'big'), 6)
        offset += 2
        for tag, value in enumerate(values, 1):
            actual, size = struct.unpack('>HI', data[offset:offset+6]); offset += 6
            self.assertEqual(actual, tag)
            self.assertEqual(data[offset:offset+size], b'\x01' + value)
            offset += size
        self.assertEqual(offset, len(data))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--evidence-directory')
    args, remaining = parser.parse_known_args()
    if args.evidence_directory:
        folder = Path(args.evidence_directory)
        suite = unittest.defaultTestLoader.loadTestsFromTestCase(FirstPositivePreparationTest)
        with (folder / 'unit-tests.txt').open('w', encoding='utf-8') as output:
            result = unittest.TextTestRunner(stream=output, verbosity=2).run(suite)
        (folder / 'unit-tests.json').write_text(json.dumps({'tests_run': result.testsRun, 'failures': len(result.failures),
            'errors': len(result.errors), 'skipped': len(result.skipped)}, indent=2) + '\n', encoding='utf-8')
        print('UNIT_TESTS=' + str(result.testsRun) + '; PASS=' + str(result.wasSuccessful()))
        raise SystemExit(int(not result.wasSuccessful()))
    unittest.main(argv=[sys.argv[0]] + remaining)
