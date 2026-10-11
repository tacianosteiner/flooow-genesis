"""Fail-closed two-layer design gate; it never authorizes wrapper execution."""
def validate(fixture):
    required={'source_head','successor_sha256','SQL_AUTHORITY_FIXTURE','EXTERNAL_RUNTIME_AUTHORITY_FIXTURE'}
    if not isinstance(fixture,dict) or set(fixture)!=required:return {'eligible':False,'reason':'Missing/unknown two-layer fixture fields'}
    if fixture['source_head']!='526bc9840854f91b9c78ba2c204344e608a6cbf3' or fixture['successor_sha256']!='6ad78ba61d70e803d2a878034aa7988b69b6374568f96949b2ef6c8defc7a8c7':return {'eligible':False,'reason':'Current source/successor mismatch'}
    if not isinstance(fixture['SQL_AUTHORITY_FIXTURE'],dict) or not fixture['SQL_AUTHORITY_FIXTURE']:return {'eligible':False,'reason':'Missing SQL authority state/witnesses'}
    if not isinstance(fixture['EXTERNAL_RUNTIME_AUTHORITY_FIXTURE'],dict) or not fixture['EXTERNAL_RUNTIME_AUTHORITY_FIXTURE']:return {'eligible':False,'reason':'SQL state alone cannot establish external eligibility'}
    # SQL state plus a producer's boolean is not independent witness validation.
    return {'eligible':False,'reason':'Full typed predicate/operator/control-flow/source-span closure and independently acquired SQL/external witnesses are pending','FIXTURE_SQL_AUTHORITY_COMPLETE':False,'FIXTURE_EXTERNAL_AUTHORITY_COMPLETE':False}
