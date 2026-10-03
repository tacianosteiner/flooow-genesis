"""Independent catalog/HMAC golden and negative projection tests, no database."""
import copy
import hashlib
import hmac
import json
import subprocess
import tempfile
import unittest

import package_0090_catalog_goldens as codec


class CatalogGoldenTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.data=codec.generate()

    def test_committed_complete_bytes_and_digests(self):
        self.assertEqual(json.loads(codec.OUTPUT.read_text(encoding='utf-8')),self.data)

    def test_independent_jvm_catalog_history_preflight_hmac(self):
        directory=codec.base.ROOT/'scripts/validation'
        with tempfile.TemporaryDirectory(prefix='flooow-0090-jvm-') as target:
            subprocess.run(['javac','-d',target,str(directory/'Package0090EvidenceFixture.java'),
                            str(directory/'Package0090CatalogGoldens.java')],check=True,capture_output=True,text=True)
            result=subprocess.run(['java','-cp',target,'Package0090CatalogGoldens',str(codec.base.ROOT)],
                                  check=True,capture_output=True,text=True)
        actual=dict(line.split('=',1) for line in result.stdout.splitlines())
        expected={}
        for label,key in (('HISTORY','history'),('NULL_HISTORY','null_history'),('PREFLIGHT','preflight'),('RECEIPT','preflight_receipt')):
            expected[label+'_HEX']=self.data[key]['hex'];expected[label+'_SHA256']=self.data[key]['sha256']
        for n,row in enumerate(self.data['acl_fixtures'],1):
            expected[f'ACL_V1_F{n}_HEX']=row['hex'];expected[f'ACL_V1_F{n}_SHA256']=row['sha256']
        expected['HMAC_SHA256']=self.data['hmac_sha256_hex']
        self.assertEqual(actual,expected)

    def test_full_history_order_null_preservation_and_duplicates(self):
        rows=codec.history_rows()
        self.assertEqual([r['installed_rank'] for r in rows],list(range(1,43)))
        self.assertEqual(codec.history_encode(rows),codec.history_encode(rows[::-1]))
        with self.assertRaises(ValueError):codec.history_encode(rows+[rows[0]])
        null_rows=self.data['null_history_rows'];zero=copy.deepcopy(null_rows);zero[-1]['checksum']=0
        self.assertNotEqual(codec.history_encode(null_rows),codec.history_encode(zero))
        self.assertNotEqual(codec.history_encode(rows),codec.history_encode(null_rows))
        for field,value in (('version','042'),('type','BASELINE'),('checksum',0),('success',False),('script','other.sql')):
            changed=copy.deepcopy(rows);changed[-1][field]=value
            self.assertNotEqual(codec.history_encode(rows),codec.history_encode(changed))

    def test_sets_unsigned_order_duplicates_and_ordered_lists(self):
        self.assertEqual(codec.collection([b'\xff',b'\x00'],True),codec.collection([b'\x00',b'\xff'],True))
        self.assertNotEqual(codec.collection([b'a',b'b']),codec.collection([b'b',b'a']))
        with self.assertRaises(ValueError):codec.collection([b'x',b'x'],True)
        self.assertNotEqual(codec.scalar(None),codec.scalar(codec.collection([])))
        self.assertNotEqual(codec.scalar(None),codec.scalar(''))
        self.assertNotEqual(codec.ref(None),codec.ref('PUBLIC'))

    def test_all_eight_acl_vectors_distinct_and_negative_expectations(self):
        fixtures=self.data['acl_fixtures']
        self.assertEqual(len(set(f['sha256'] for f in fixtures)),8)
        self.assertEqual([f['policy_result'] for f in fixtures],['PASS_CONCEPTUAL_ONLY']*4+['REJECT']*4)
        f4=codec.base.decode_frame(bytes.fromhex(fixtures[3]['hex']),codec.PREFIX+'ACL/V1',6)
        self.assertEqual(len(f4),6)
        self.assertFalse(self.data['readiness_approval'])
        self.assertFalse(self.data['installed_history_claim'])

    def test_authenticated_preflight_every_field_mutation_denied(self):
        frame=bytes.fromhex(self.data['preflight']['hex']);key=bytes.fromhex(self.data['synthetic_hmac_key_hex'])
        mac=bytes.fromhex(self.data['hmac_sha256_hex'])
        self.assertTrue(hmac.compare_digest(mac,hmac.digest(key,frame,'sha256')))
        payloads=codec.base.decode_frame(frame,codec.PREFIX+'PREFLIGHT/V1',9)
        for index in range(9):
            changed=payloads.copy();raw=bytearray(changed[index]);raw[-1]^=1;changed[index]=bytes(raw)
            mutated=codec.base.frame(codec.PREFIX+'PREFLIGHT/V1',[codec.base.present(v) for v in changed])
            with self.subTest(tag=index+1):self.assertFalse(hmac.compare_digest(mac,hmac.digest(key,mutated,'sha256')))
        self.assertEqual(bytes.fromhex(self.data['preflight_receipt']['hex']),frame+mac)
        self.assertFalse(hmac.compare_digest(mac,hmac.digest(bytes(32),frame,'sha256')))


if __name__=='__main__':unittest.main()
