"""Real later B bootstrap accepts B and rejects authentic earlier A public inputs."""
import os,json
from pathlib import Path
def run(q):
    path=Path(os.environ['FLOOOW_TEST_OLD_CEREMONY_PUBLIC']).resolve();assert path.parent==q.OUT.parent and path.name=='CEREMONY-A-PUBLIC.json'
    old=json.loads(path.read_text());assert old['scope']=='TEST_ONLY_NONCANONICAL'
    assert old['approval']['binding_id']!=q.expected_approval['binding_id']
    assert old['attestation']['key_fingerprint']!=q.expected_bundle['key_fingerprint']
    q.mutate_external('/run/flooow-external/approval.json',old['approval'],'actual_valid_older_approval_A_rejected_under_B','successive_ceremony')
    q.mutate_external('/run/flooow-external/attestation.json',old['attestation'],'actual_valid_older_attestation_A_rejected_under_B','successive_ceremony')
    mixed=dict(q.expected_bundle);mixed['authority']=old['attestation']['authority']
    q.mutate_external('/run/flooow-external/attestation.json',mixed,'mixed_A_B_authority_context_rejected','successive_ceremony')
    q.case('successive_ceremony','actual_current_B_accepted',q.sql('SELECT 42;','test_verifier',ok=False).returncode==0,'Fresh B native anchors, actual signature and independent root custody; full SQL accepted-consumption remains fenced')
    q.rootfile('/run/flooow-watchdog/TEST_ONLY_NONCANONICAL-foreign-frame.bin',bytes.fromhex(old['frame_hex']),'0600');q.ex('chown','999:999','/run/flooow-watchdog/TEST_ONLY_NONCANONICAL-foreign-frame.bin',user='0')
    q.ex('gcc','-D_GNU_SOURCE','-std=c11','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','/usr/local/src-full/namespace_replay.c','-o','/usr/local/bin/namespace-replay','-lcrypto','-ldl',user='0')
    r=q.ex('/usr/local/bin/namespace-replay',ok=False)
    q.case('successive_ceremony','actual_earlier_A_frame_rejected_under_B',r.returncode==0,{'stdout':r.stdout,'stderr':r.stderr,'scope':'actual unmodified earlier accepted frame + sender own live self anchor; context reason 3','SQL_authority_join_parity':False})
