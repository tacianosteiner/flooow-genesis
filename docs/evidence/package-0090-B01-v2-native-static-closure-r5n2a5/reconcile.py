"""Reconcile inherited decisions; do not execute forbidden final recomputation when B is OPEN."""
from qualification import O,E,N,N1,N2,A2,A3,B,ACL,rd,put,ref
def main():
    phase_a=rd(O/'qualification-closure.json');phase_b=rd(O/'substitution-closure.json');assert phase_a['N1_QUALIFICATION_INPUT_RESOLUTION']=='CLOSED' and phase_b['N1_SUBSTITUTION_STATIC_WITNESSES']=='OPEN'
    foundation=E/'package-0090-B01-v2-native-static-closure-r5n2a';refs={
      'N1-LABEL-IR-ATOMICITY':(foundation/'FOUNDATION-GATE.json','/N1_LABEL_IR_ATOMICITY'),
      'N1-SCALAR-SYSCALL-IR':(A2/'FOUNDATION-GATE.json','/N1_SCALAR_SYSCALL_IR'),
      'N1-SOURCE-STATS-VISIBILITY':(A3/'SOURCE-IDENTITY-GATE.json','/N1_SOURCE_STATS_VISIBILITY'),
      'N1-READER-PREPARSE-GATE':(foundation/'FOUNDATION-GATE.json','/N1_READER_PREPARSE_GATE'),
      'N1-CATALOG-EFFECT-GRAPH':(B/'gate.json','/N1_CATALOG_EFFECT_GRAPH'),
      'N1-READER-EFFECTIVE-ACL':(ACL/'gate.json','/N1_READER_EFFECTIVE_ACL'),
      'N1-CONFIG-SECRET-EXCLUSION':(foundation/'preserved-closures.json','/closed/N1-CONFIG-SECRET-EXCLUSION'),
      'N1-SNAPSHOT-MUTATION-BARRIER':(A2/'FOUNDATION-GATE.json','/N1_SNAPSHOT_MUTATION_BARRIER'),
      'N1-CREDENTIAL-CLASS-INVENTORY':(A3/'SOURCE-IDENTITY-GATE.json','/N1_CREDENTIAL_CLASS_INVENTORY'),
      'N1-QUALIFICATION-INPUT-RESOLUTION':(O/'qualification-closure.json','/N1_QUALIFICATION_INPUT_RESOLUTION'),
      'N1-SUBSTITUTION-STATIC-WITNESSES':(O/'substitution-closure.json','/N1_SUBSTITUTION_STATIC_WITNESSES'),
      'N1-CATALOG-CODEC-TYPE-TABLE':(foundation/'preserved-closures.json','/closed/N1-CATALOG-CODEC-TYPE-TABLE')}
    records=[]
    for original in rd(N2/'twelve-blocker-register.json')['records']:
        bid=original['BLOCKER_ID'];path,pointer=refs[bid];closed=bid!='N1-SUBSTITUTION-STATIC-WITNESSES'
        records.append(dict(BLOCKER_ID=bid,ORIGINAL_FAILURE=original['ORIGINAL_FAILURE'],REQUIRED_DECISION=original['REQUIRED_DECISION'],STATUS='CLOSED' if closed else 'OPEN',closure_lineage=ref(path,pointer),open_reason=None if closed else phase_b['derived_gap'],proof_scope='STATIC_ONLY',new_top_level_blocker=False))
    assert len(records)==12 and len({r['BLOCKER_ID'] for r in records})==12
    put('original-12-decision-reconciliation.json',dict(required=12,closed=sum(r['STATUS']=='CLOSED' for r in records),open=sum(r['STATUS']=='OPEN' for r in records),records=records))
    roots=[]
    for old in rd(N1/'root-cause-accounting.json')['original_roots']:
        closed=old['exact_previous_verdict']['closed']
        roots.append(dict(FAMILY=old['family'],ORIGINAL_INDEX=old['original_index'],STATUS='CLOSED_CARRIED' if closed else 'OPEN_PENDING_FINAL_RECOMPUTATION',original_verdict=old['exact_previous_verdict'],original_lineage=old['evidence'],current_disposition='Accepted publication/generation closure preserved' if closed else 'No final V2-native/root closure promotion while required substitution witness is OPEN; prior root closure not silently inferred from sub-decisions'))
    put('original-root-cause-reconciliation.json',dict(original=3,closed=sum(r['STATUS']=='CLOSED_CARRIED' for r in roots),open=sum(r['STATUS']!='CLOSED_CARRIED' for r in roots),ROOT_CAUSE_ACCOUNTING_RECONCILED='YES',count_scope='CARRY_FORWARD_ORIGINAL_ROOT_VERDICTS_WITH_EXPLICIT_FINAL_RECOMPUTATION_FENCE',roots=roots,final_recomputation_executed=False))
    put('v2-native-recomputation.json',dict(executed=False,reason='User §19 permits full recomputation only after BOTH target blockers CLOSED; substitution remains OPEN',qualification=phase_a['N1_QUALIFICATION_INPUT_RESOLUTION'],substitution=phase_b['N1_SUBSTITUTION_STATIC_WITNESSES'],V2_NATIVE_STATIC_DESIGN_PROOF='FAIL',V2_NATIVE_STATUS='BLOCKED',NATIVE_PARTICIPANTS_FULLY_QUALIFIED='NOT_RECOMPUTED_DEPENDENCY_OPEN',native_implementation_proof='FUTURE',native_build_proof='FUTURE',native_runtime_proof='FUTURE',native_physical_privilege_proof='FUTURE',next_gate=phase_b['derived_gap'],root_reconciliation=ref(O/'original-root-cause-reconciliation.json'),decision_reconciliation=ref(O/'original-12-decision-reconciliation.json')))
if __name__=='__main__':main()
