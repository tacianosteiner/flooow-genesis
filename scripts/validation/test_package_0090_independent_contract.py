"""Independent normative contract regressions; no generator maps imported."""
import contextlib
import io
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
import package_0090_independent_review as independent
from package_0090_s10_transport import decode

class IndependentContractTests(unittest.TestCase):
    def test_spec_ast_manifest_and_frozen_casts_reject_reviewed_bad_baseline(self):
        with tempfile.TemporaryDirectory() as temp, contextlib.redirect_stdout(io.StringIO()):
            independent.main(output=Path(temp)/'current.json',require=True)
            path=next(independent.MIGRATIONS.glob('V043*')).relative_to(independent.ROOT).as_posix()
            old=subprocess.check_output(['git','show','8729f4b96f50bf7292770c93a58f6ebc60f3b67a:'+path],cwd=independent.ROOT).decode('utf-8-sig')
            with self.assertRaises(ValueError):independent.main(source_override=old,output=Path(temp)/'old.json',require=True)

    def test_actual_s10_outer_fresh_and_replay_and_reject_old_frozen_tuple(self):
        artifact=json.loads((independent.ROOT/'docs/evidence/PACKAGE-0090-S07-S18-TRANSPORT-GOLDENS.json').read_text())['goldens']['S10']
        fresh=decode(bytes.fromhex(artifact['output_hex']))
        replay=decode(bytes.fromhex(artifact['replay_output_hex']))
        self.assertIsNotNone(fresh['fresh_applied_receipt_id'])
        self.assertIsNone(replay['fresh_applied_receipt_id'])
        self.assertEqual(fresh['operation_id'],replay['operation_id'])
        with self.assertRaises(ValueError):decode(fresh['frozen_receipt'])
        with self.assertRaises(ValueError):decode(bytes.fromhex(artifact['output_hex'])+b'\x00')

if __name__=='__main__':unittest.main()
