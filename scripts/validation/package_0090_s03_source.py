"""Bounded S03 authority review; no new expected-input consumer or runtime claim."""
from build_package_0090_s03_source import NAME, TYPES, OWNER, GRANTS, build
from package_0090_s02_source import check as review

def check(fn,expected_columns,source):
    result=review(fn,expected_columns,source,generator=build,additional_calls={('public',n) for n in ('offline_inspect','transaction_identity_intent','transaction_identity_fingerprint')})
    body=next(o['DefElem']['arg']['List']['items'][0]['String']['sval'] for o in fn['options'] if o['DefElem']['defname']=='as')
    if 'public.offline_expected_signed_attestation' in body:raise ValueError('Only S02 may consume expected original input')
    return {'s03_source':'BOUNDED_STATIC_PASS_NOT_RUNTIME_PROOF','s03_read_columns':result['s02_read_columns'],
            's03_expected_input_consumption':'DELEGATED_TO_S02','s03_adapter_jca_required':True}
