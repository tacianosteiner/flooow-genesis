"""Distinguish pinned original metadata from actual bytes sent to crypto."""
import base64
def run(q):
    q.paused.set()
    with q.health_lock:
        original_preimage=base64.b64decode(q.ex('base64','-w','0','/run/flooow-external/preimage.bin',user='0').stdout)
        original_signature=base64.b64decode(q.ex('base64','-w','0','/run/flooow-external/signature.bin',user='0').stdout)
        # Valid fresh signature on wrong domain/payload, metadata still pinned original.
        q.rootfile('/run/flooow-external/preimage.bin',b'TEST_ONLY_NONCANONICAL_WRONG_DOMAIN_AND_MANIFEST')
        q.ex('openssl','pkeyutl','-sign','-inkey','/run/test-only-private/TEST_ONLY_NONCANONICAL.pem','-rawin','-in','/run/flooow-external/preimage.bin','-out','/run/flooow-external/signature.bin',user='0')
        eligible=q.observer_once();r=q.sql('SELECT 1;','test_verifier',ok=False)
        attack_signature=base64.b64decode(q.ex('base64','-w','0','/run/flooow-external/signature.bin',user='0').stdout)
        q.case('attestation','valid_crypto_material_substitution_must_deny',not eligible and r.returncode!=0,{'observer_eligible':eligible,'native_login_exit':r.returncode,'stderr':r.stderr,'attack':'valid signature on different actual preimage while original metadata/header/custody unchanged','actual_preimage_hex':b'TEST_ONLY_NONCANONICAL_WRONG_DOMAIN_AND_MANIFEST'.hex(),'actual_signature_hex':attack_signature.hex(),'synthetic_signing':'TEST_ONLY_NONCANONICAL','requires_exact_material_commitment':True})
        q.rootfile('/run/flooow-external/preimage.bin',original_preimage);q.rootfile('/run/flooow-external/signature.bin',original_signature);assert q.observer_once()
        # A different actual key cannot be accepted with the original key metadata.
        public=q.ex('cat','/run/flooow-external/public.pem',user='0').stdout
        q.ex('openssl','genpkey','-algorithm','ED25519','-out','/run/test-only-private/TEST_ONLY_NONCANONICAL-other.pem',user='0')
        q.ex('chmod','0600','/run/test-only-private/TEST_ONLY_NONCANONICAL-other.pem',user='0')
        q.ex('openssl','pkey','-in','/run/test-only-private/TEST_ONLY_NONCANONICAL-other.pem','-pubout','-out','/run/flooow-external/public.pem',user='0')
        eligible=q.observer_once();r=q.sql('SELECT 1;','test_verifier',ok=False)
        q.case('attestation','actual_wrong_public_key_rejected',not eligible and r.returncode!=0,{'observer_eligible':eligible,'stderr':r.stderr})
        q.rootfile('/run/flooow-external/public.pem',public);assert q.observer_once()
        q.ex('rm','-f','/run/test-only-private/TEST_ONLY_NONCANONICAL-other.pem',user='0')
        q.case('attestation','exact_original_restored_accepts',q.sql('SELECT 1;','test_verifier',ok=False).returncode==0,'exact independent original material restored; no self-approval of host identity')
    q.paused.clear()
