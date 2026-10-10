"""Offline counterexample model, NOT an authenticated host-proof implementation.

No SQL, I/O channel, health writer, lease, codec, signaling or activation API.
Assertions characterize accepted contracts; simulated flags never attest reality.
"""
from dataclasses import dataclass, replace
import json
from package_0090_policy_fixture import decode, approved_fixture, NAMES

@dataclass(frozen=True)
class Observation:
    producer: str = 'INDEPENDENT_TRUSTED_HOST'
    deployment: str = 'fixture-deployment'
    incarnation: str = 'fixture-incarnation'
    receiver_epoch: str = 'live-fixture-epoch'
    sequence: int = 2
    database_now_us: int = 1000000
    prior_database_now_us: int = 999999
    checked_at_us: int = 999950
    maximum_observed_loop_gap_us: int = 50
    healthy_projection: bool = True
    host_marker_agrees: bool = True
    policy_history_catalog_agree: bool = True
    governed_roster_bound: bool = True
    header_absent_denied: bool = True
    mandatory_self_anchor_enrollment: bool = True
    receiver_current_and_live: bool = True
    identity_bound_signal_path: bool = True
    supervisor_and_drain_qualified: bool = True

def model_eligible(p: Observation) -> bool:
    """Fictional evidence assumptions, not verification of an actual observer."""
    complete = all((p.host_marker_agrees,p.policy_history_catalog_agree,p.governed_roster_bound,
        p.header_absent_denied,p.mandatory_self_anchor_enrollment,p.receiver_current_and_live,
        p.identity_bound_signal_path,p.supervisor_and_drain_qualified,p.healthy_projection))
    return (complete and p.producer=='INDEPENDENT_TRUSTED_HOST' and
        p.deployment=='fixture-deployment' and p.incarnation=='fixture-incarnation' and
        p.receiver_epoch=='live-fixture-epoch' and p.sequence>1 and
        p.database_now_us>=p.prior_database_now_us and
        0<=p.database_now_us-p.checked_at_us<=100 and
        0<=p.maximum_observed_loop_gap_us<=100)

def review():
    version,values=decode(bytes.fromhex(approved_fixture()['canonical_policy_hex']))
    actual,maximum=values[12:14]
    assert NAMES[6]=='BINDING_VALIDITY' and (actual,maximum)==(1000000,2000000)
    assert version=='fixture-1'
    tests={}
    def check(label,value,expected):
        assert value==expected,label
        tests[label]='PASS'
    check('frozen_60s_within_binding_actual',60000000<=actual,False)
    check('frozen_60s_within_approved_maximum',60000000<=maximum,False)
    check('fixture_1s_fits_actual',1000000<=actual,True)
    check('max_is_not_runtime_grace',1500000<=actual,False)
    check('raising_max_alone_cannot_fix_actual',60000000<=actual,False)
    check('freshness_is_not_binding_ttl',values[22]!=actual,True)
    check('preflight_is_distinct_even_when_numerically_equal',NAMES[13]!=NAMES[6] and values[26]==actual,True)
    positive=Observation()
    check('fictional_complete_model_positive',model_eligible(positive),True)
    for field in ('healthy_projection','host_marker_agrees','policy_history_catalog_agree','governed_roster_bound',
                  'header_absent_denied','mandatory_self_anchor_enrollment','receiver_current_and_live',
                  'identity_bound_signal_path','supervisor_and_drain_qualified'):
        check('missing_'+field,model_eligible(replace(positive,**{field:False})),False)
    for label,changes in {
        'self_authorship':{'producer':'PLAN_BINDING_ADMIN'},
        'untrusted_producer':{'producer':'CALLER'},
        'wrong_deployment':{'deployment':'other'},'wrong_incarnation':{'incarnation':'clone'},
        'replayed_receiver_epoch':{'receiver_epoch':'old-fixture-epoch'},
        'replayed_sequence':{'sequence':1},'zero_sequence':{'sequence':0},
        'future_timestamp':{'checked_at_us':1000001},
        'stale_timestamp':{'checked_at_us':999899},
        'loop_gap_exceeded':{'maximum_observed_loop_gap_us':101},
        'clock_rollback':{'database_now_us':999949},
        'rollback_still_after_marker':{'prior_database_now_us':1000001},
        'fresh_row_without_observer':{'checked_at_us':1000000,'mandatory_self_anchor_enrollment':False},
        'same_system_id_wrong_incarnation':{'incarnation':'restored-copy'},
    }.items():
        check(label,model_eligible(replace(positive,**changes)),False)
    check('freshness_exact_100us_boundary',model_eligible(replace(positive,checked_at_us=999900)),True)
    return {'scope':'OFFLINE_COUNTEREXAMPLES_NOT_HOST_AUTHENTICATION_OR_RUNTIME_PROOF',
        'adjudication':'D_FOR_CURRENT_FROZEN_PROFILE_NOT_GLOBAL_ARCHITECTURE_IMPOSSIBILITY',
        'test_count':len(tests),'tests':tests,'watchdog_runtime_gate':'HOLD',
        'policy_mutation':False,'health_write':False,'activation':False}

if __name__=='__main__':print(json.dumps(review(),indent=2))
