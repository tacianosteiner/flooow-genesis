"""Approved private V original-input comparison; source generation only."""
import package_0090_source_gate as gate
from build_package_0090_expected_attestation_source import canonical, FIELDS

NAME='offline_internal_matches_original_signed_attestation'
OWNER='flooow_offline_control_owner'
TYPES=('uuid','bytea','uuid','text','text','text','uuid','text','bytea')
NAMES=('binding_id','plan_fingerprint','incarnation_id','surface','manifest_digest','algorithm_id','signer_key_id','signer_key_fingerprint','signature_bytes')
GRANTS={('public',NAME,TYPES,'flooow_offline_verification_owner')}
MARKER='-- Private mutation original-input comparison: approved 2026-10-04.'
END='-- End private mutation original-input comparison.'

def build(source):
    p=source.split('AS $offline_p$',1)[1].split('$offline_p$;',1)[0]
    slots=p.split('    -- Decode exact canonical slots;',1)[1].split('    SELECT p.policy_version',1)[0]
    slots=slots.replace('slot_number=3','slot_number=1')
    declarations='DECLARE\n    header_record record;\n    original_record record;\n    canonical_bytes pg_catalog.bytea;\n    caller_record record;\n'
    for line in p.split('BEGIN',1)[0].splitlines():
        if line.strip().startswith(('slot_','byte_number ')):
            declarations+=line+'\n'
    signature=','.join('pg_catalog.'+t for t in TYPES)
    nulls=' OR '.join('$'+str(i)+' IS NULL' for i in range(1,10))
    body='''BEGIN
    IF '''+nulls+'''
       OR $1='00000000-0000-0000-0000-000000000000'::pg_catalog.uuid
       OR $3='00000000-0000-0000-0000-000000000000'::pg_catalog.uuid
       OR pg_catalog.octet_length($2)<>32 OR $4<>'0090-v1' THEN
        RAISE EXCEPTION USING ERRCODE='P0017',MESSAGE='ACCESS_DENIED';
    END IF;
    SELECT h.binding_id,h.plan_fingerprint,h.deployment_incarnation_id,
           h.offline_surface_version,h.identity_slots,h.manifest_digest
      INTO STRICT header_record FROM public.offline_binding_header h
     WHERE h.binding_id=$1 AND h.plan_fingerprint=$2
       AND h.deployment_incarnation_id=$3 AND h.offline_surface_version=$4;
    -- Decode exact canonical slots;'''+slots+'''
    BEGIN
        SELECT '''+','.join('o.'+field for field in FIELDS)+'''
          INTO STRICT original_record FROM public.offline_expected_signed_attestation o
         WHERE o.binding_id=$1;
        canonical_bytes := '''+canonical('original_record')+''';
        RETURN (original_record.canonical_expected_attestation=canonical_bytes
            AND pg_catalog.octet_length(original_record.commitment_digest)=32
            AND original_record.commitment_digest=pg_catalog.sha256(canonical_bytes)
            AND original_record.manifest_digest ~ '^[0-9a-f]{64}$'
            AND original_record.manifest_digest=pg_catalog.encode(header_record.manifest_digest,'hex')
            AND original_record.algorithm_id='Ed25519'
            AND original_record.signer_key_id<>'00000000-0000-0000-0000-000000000000'::pg_catalog.uuid
            AND original_record.signer_key_fingerprint ~ '^[0-9a-f]{64}$'
            AND pg_catalog.octet_length(original_record.signature_bytes)=64
            AND original_record.manifest_digest=$5 AND original_record.algorithm_id=$6
            AND original_record.signer_key_id=$7 AND original_record.signer_key_fingerprint=$8
            AND original_record.signature_bytes=$9) IS TRUE;
    EXCEPTION WHEN OTHERS THEN
        RETURN false;
    END;
EXCEPTION WHEN OTHERS THEN
    RAISE EXCEPTION USING ERRCODE='P0017',MESSAGE='ACCESS_DENIED';
END;
'''
    return MARKER+'\nCREATE FUNCTION public.'+NAME+'(\n    '+',\n    '.join(n+' pg_catalog.'+t for n,t in zip(NAMES,TYPES))+'''
) RETURNS pg_catalog.bool
LANGUAGE plpgsql STABLE SECURITY DEFINER CALLED ON NULL INPUT
SET search_path=pg_catalog,pg_temp
AS $offline_original_match$
'''+declarations+body+'$offline_original_match$;\nALTER FUNCTION public.'+NAME+'('+signature+') OWNER TO '+OWNER+';\nREVOKE ALL ON FUNCTION public.'+NAME+'('+signature+') FROM PUBLIC;\nGRANT EXECUTE ON FUNCTION public.'+NAME+'('+signature+') TO flooow_offline_verification_owner;\n'+'GRANT USAGE ON SCHEMA public TO flooow_offline_verification_owner;\n'+END+'\n'

def install():
    path=gate.ROOT/gate.V043;source=path.read_text(encoding='utf-8-sig')
    if MARKER in source:
        start=source.index(MARKER);end=source.index(END,start)+len(END)
        source=source[:start]+build(source).rstrip()+source[end:]
    else:source+='\n'+build(source)
    path.write_text(source,encoding='utf-8')

if __name__=='__main__':install()
