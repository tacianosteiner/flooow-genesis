"""Independent disposable field storage, not executable frozen-domain SQL."""
def statements(codec):
    columns=[]
    for name in codec.FIELDS:
        kind=('integer' if name in codec.VERSIONS else 'timestamptz' if name in codec.TIMES else 'bytea' if name in codec.HASH or name=='identity_slots' else 'uuid' if name.endswith('_id') else 'text')
        columns.append(name+' '+kind+' NOT NULL')
    columns+=['canonical_manifest_bytes bytea NOT NULL','plan_fingerprint bytea NOT NULL','PRIMARY KEY(binding_id)']
    result=['CREATE TABLE offline_binding_header('+','.join(columns)+');',
            'CREATE TABLE offline_binding_lifecycle(binding_id uuid PRIMARY KEY,state text NOT NULL,revision bigint NOT NULL);',
            'CREATE TABLE offline_attempt_pointer(binding_id uuid PRIMARY KEY,attempt_id uuid,next_sequence bigint NOT NULL,occupied boolean NOT NULL,revision bigint NOT NULL);']
    result+=['REVOKE ALL ON '+name+' FROM PUBLIC;' for name in ['offline_binding_header','offline_binding_lifecycle','offline_attempt_pointer']]
    return result
