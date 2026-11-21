/* Synthetic structural guard tests only; never source/policy acceptance. */
#include "policy_candidate_custody.c"
int main(void){
    S03RawBootstrap expected={0};expected.magic=0x42505231;expected.version=1;expected.database_oid=5;expected.reader_oid=16384;expected.system_identifier=1234567;expected.time_namespace_inode=987;expected.started_us=100;expected.finished_us=101;expected.flags[0]=1;expected.boot_id[0]=1;memcpy(expected.reader_name,"flooow_reader",14);
    PolicyCandidate baseline={0};baseline.version=3;baseline.source_acceptance_state=1;baseline.activation_state=1;baseline.decision_state=2;baseline.proposed_max_age_us=S03_PROPOSED_MAX_AGE_US;baseline.proposed_lease_us=S03_PROPOSED_LEASE_US;baseline.max_rows=S03_PROPOSED_MAX_ROWS;baseline.max_frame_bytes=S03_PROPOSED_MAX_BYTES;baseline.held_started_us=102;baseline.held_finished_us=103;baseline.raw_context=expected;memcpy(baseline.policy_version,S03_PROPOSED_POLICY_VERSION,sizeof(S03_PROPOSED_POLICY_VERSION));memcpy(baseline.proposal_sha256,S03_POLICY_PROPOSAL_SHA256,65);
    assert(exact_unaccepted_projection(&baseline,&expected));
    for(unsigned test=0;test<15;++test){PolicyCandidate value=baseline;
        switch(test){
            case 0:value.version++;break;
            case 1:value.source_acceptance_state=2;break;
            case 2:value.activation_state=2;break;
            case 3:value.proposed_max_age_us++;break;
            case 4:value.proposed_lease_us++;break;
            case 5:value.max_rows++;break;
            case 6:value.max_frame_bytes++;break;
            case 7:value.proposal_sha256[0]^=1;break;
            case 8:value.policy_version[0]^=1;break;
            case 9:value.raw_context.database_oid++;break;
            case 10:value.raw_context.boot_id[15]^=1;break;
            case 11:value.held_started_us=100;break;
            case 12:value.held_finished_us=101;break;
            case 13:value.policy_version[63]=1;break;
            case 14:value.decision_state=1;break;
        }
        assert(!exact_unaccepted_projection(&value,&expected));
    }
    puts("PASS synthetic policy projection guard: baseline +15independent field/tag/context/time mutations; not qualification/acceptance/frozen33or66");
    return 0;
}
