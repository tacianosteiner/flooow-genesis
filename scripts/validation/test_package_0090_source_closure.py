"""Adversarial checks for the qualification boundary, not migration semantics."""
import argparse
import json
import sys
import unittest
import package_0090_source_closure as q

ap = argparse.ArgumentParser()
ap.add_argument('--parser-path', required=True)
args, rest = ap.parse_known_args()
sys.path.insert(0, args.parser_path)
from pglast.parser import parse_sql_json

SOURCE = q.git('show', 'HEAD:' + q.V043.relative_to(q.ROOT).as_posix())


class QualificationBoundaryTest(unittest.TestCase):
    def test_exact_fence_only_byte_change(self):
        candidate, tree, proof = q.derive(SOURCE, parse_sql_json)
        self.assertEqual(len(tree), 1235)
        self.assertEqual(candidate[:proof['offset']] + q.FENCE + candidate[proof['offset']:], SOURCE)
        self.assertEqual(len(SOURCE) - len(candidate), 159)
        self.assertTrue(proof['ast_equivalence'])
        self.assertEqual(proof['candidate_sha256'], '50620e0a64da25c2c33a1060d5e8b632c34f04fbd67636eebf203f9b859c5d70')

    def test_unreviewed_source_change_denied(self):
        with self.assertRaisesRegex(ValueError, 'source hash mismatch'):
            q.derive(SOURCE + b'\nSELECT true;', parse_sql_json)

    def test_duplicate_or_relocated_fence_denied(self):
        for hostile in [q.FENCE + SOURCE, b'SELECT 1;\n' + SOURCE, SOURCE.replace(q.FENCE, b'')]:
            with self.assertRaises(ValueError):
                q.derive(hostile, parse_sql_json)

    def test_other_semantic_ast_change_denied(self):
        def hostile_parser(s):
            tree = json.loads(parse_sql_json(s))
            if 'implementation closure is incomplete' not in s:
                tree['stmts'][0]['stmt']['VariableSetStmt']['name'] = 'role'
            return json.dumps(tree)
        with self.assertRaisesRegex(ValueError, 'Remaining SQL AST differs'):
            q.derive(SOURCE, hostile_parser)

    def test_security_guard_survives_optimized_python(self):
        with self.assertRaisesRegex(RuntimeError, 'guard required'):
            q.require(False, 'guard required')


if __name__ == '__main__':
    unittest.main(argv=[sys.argv[0]] + rest)
