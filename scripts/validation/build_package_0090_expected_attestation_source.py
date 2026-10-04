"""Governed original-input commitment; generates source, never executes SQL."""
import package_0090_source_gate as gate

MARKER = '-- Original signed-attestation commitment: approved 2026-10-03.'
END = '-- End original signed-attestation commitment.'
NAME = 'offline_internal_expected_attestation_guard'
OWNER = 'flooow_offline_control_owner'
TYPES = ()
FIELDS = ('binding_id','manifest_digest','algorithm_id','signer_key_id',
          'signer_key_fingerprint','signature_bytes','canonical_expected_attestation','commitment_digest')
DOMAIN = 'FLOOOW/OFFLINE-FIELD-PROOF/EXPECTED-SIGNED-ATTESTATION/V1'

def canonical(alias):
    payloads = [f'pg_catalog.uuid_send({alias}.binding_id)',
                f"pg_catalog.convert_to({alias}.manifest_digest,'UTF8')",
                f"pg_catalog.convert_to({alias}.algorithm_id,'UTF8')",
                f'pg_catalog.uuid_send({alias}.signer_key_id)',
                f"pg_catalog.convert_to({alias}.signer_key_fingerprint,'UTF8')",
                f'{alias}.signature_bytes']
    domain = f"pg_catalog.convert_to('{DOMAIN}','UTF8')"
    value = f'pg_catalog.int4send(pg_catalog.octet_length({domain}))||{domain}||pg_catalog.int2send(6::pg_catalog.int2)'
    for tag, payload in enumerate(payloads, 1):
        value += f"||pg_catalog.int2send({tag}::pg_catalog.int2)||pg_catalog.int4send(1+pg_catalog.octet_length({payload}))||pg_catalog.decode('01','hex')||{payload}"
    return value

def build():
    return MARKER + '''
CREATE TABLE public.offline_expected_signed_attestation (
    binding_id pg_catalog.uuid NOT NULL PRIMARY KEY REFERENCES public.offline_binding_header(binding_id),
    manifest_digest pg_catalog.text NOT NULL CHECK (manifest_digest ~ '^[0-9a-f]{64}$'),
    algorithm_id pg_catalog.text NOT NULL CHECK (algorithm_id='Ed25519'),
    signer_key_id pg_catalog.uuid NOT NULL CHECK (signer_key_id<>'00000000-0000-0000-0000-000000000000'::pg_catalog.uuid),
    signer_key_fingerprint pg_catalog.text NOT NULL CHECK (signer_key_fingerprint ~ '^[0-9a-f]{64}$'),
    signature_bytes pg_catalog.bytea NOT NULL CHECK (pg_catalog.octet_length(signature_bytes)=64),
    canonical_expected_attestation pg_catalog.bytea NOT NULL,
    commitment_digest pg_catalog.bytea NOT NULL CHECK (commitment_digest=pg_catalog.sha256(canonical_expected_attestation))
);
ALTER TABLE public.offline_expected_signed_attestation OWNER TO flooow_offline_control_owner;
REVOKE ALL ON TABLE public.offline_expected_signed_attestation FROM PUBLIC;
-- Deferred reverse FK makes a committed header without its original input impossible.
-- Registration inserts the original header then its independently supplied signed input
-- in ONE transaction. Duplicate registration uses plain INSERT, never UPSERT.
ALTER TABLE public.offline_binding_header ADD CONSTRAINT offline_header_original_input_required
    FOREIGN KEY(binding_id) REFERENCES public.offline_expected_signed_attestation(binding_id)
    DEFERRABLE INITIALLY DEFERRED;
CREATE FUNCTION public.offline_internal_expected_attestation_guard() RETURNS pg_catalog.trigger
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp
AS $offline_expected_guard$
BEGIN
    IF TG_OP<>'INSERT' OR TG_TABLE_SCHEMA<>'public'
       OR TG_TABLE_NAME<>'offline_expected_signed_attestation' THEN
        RAISE EXCEPTION USING ERRCODE='55000',MESSAGE='Original binding input is immutable';
    END IF;
    IF NOT EXISTS (SELECT 1 FROM public.offline_binding_header h
                   WHERE h.binding_id=NEW.binding_id
                     AND pg_catalog.encode(h.manifest_digest,'hex')=NEW.manifest_digest)
       OR NEW.canonical_expected_attestation IS DISTINCT FROM ''' + canonical('NEW') + ''' THEN
        RAISE EXCEPTION USING ERRCODE='22023',MESSAGE='Invalid original signed-attestation commitment';
    END IF;
    RETURN NEW;
END;
$offline_expected_guard$;
ALTER FUNCTION public.offline_internal_expected_attestation_guard() OWNER TO flooow_offline_control_owner;
REVOKE ALL ON FUNCTION public.offline_internal_expected_attestation_guard() FROM PUBLIC;
CREATE TRIGGER offline_expected_original_input_guard BEFORE INSERT OR UPDATE OR DELETE
    ON public.offline_expected_signed_attestation FOR EACH ROW
    EXECUTE FUNCTION public.offline_internal_expected_attestation_guard();
CREATE TRIGGER offline_header_original_input_immutable BEFORE UPDATE OR DELETE
    ON public.offline_binding_header FOR EACH ROW
    EXECUTE FUNCTION public.offline_internal_expected_attestation_guard();
CREATE TRIGGER offline_expected_original_input_no_truncate BEFORE TRUNCATE
    ON public.offline_expected_signed_attestation FOR EACH STATEMENT
    EXECUTE FUNCTION public.offline_internal_expected_attestation_guard();
CREATE TRIGGER offline_header_original_input_no_truncate BEFORE TRUNCATE
    ON public.offline_binding_header FOR EACH STATEMENT
    EXECUTE FUNCTION public.offline_internal_expected_attestation_guard();
''' + ''.join(f'GRANT SELECT ({field}) ON TABLE public.offline_expected_signed_attestation TO flooow_offline_audit_owner;\n' for field in FIELDS) + END + '\n'

def install():
    path=gate.ROOT/gate.V043
    source=path.read_text(encoding='utf-8-sig')
    if MARKER in source:
        start=source.index(MARKER); end=source.index(END,start)+len(END)
        source=source[:start]+build().rstrip()+source[end:]
    else:
        point=source.index('-- Internal P:')
        source=source[:point]+build()+'\n'+source[point:]
    path.write_text(source,encoding='utf-8')

if __name__=='__main__': install()
