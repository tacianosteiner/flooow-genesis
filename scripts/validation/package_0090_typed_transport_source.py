"""Inline closed typed transports; creates no PostgreSQL helper capability."""
import re
from build_package_0090_q_source import frame, nullable, raw, deny

ALIASES={'integer':'int4','bigint':'int8','timestamptz(6)':'timestamptz'}

def frozen_tuple(spec,stage,direction):
    section=spec.split('**'+stage+' frozen tuple contract**:',1)[1].split('**S',1)[0]
    text=section.split(direction+': ',1)[1].split('\n',1)[0].rstrip('.')
    fields=[(name,ALIASES.get(kind,kind)) for _,name,kind in re.findall(r'(\d+)=([a-z_]+) ([a-z0-9()]+)',text)]
    if not fields:raise ValueError('Missing closed frozen tuple')
    return fields

DECLARATIONS='''    codec_cursor pg_catalog.int4;
    codec_length pg_catalog.int8;
    codec_number pg_catalog.numeric;
    codec_byte pg_catalog.int4;
    codec_raw pg_catalog.bytea;
'''

def bound(name,kind):
    if kind=='uuid':return (16,16)
    if kind=='int4':return (4,4)
    if kind in ('int8','timestamptz'):return (8,8)
    if kind=='bytea':
        if 'signature_preimage' in name:return (222,222)
        if 'subject_public_key_info' in name:return (44,44)
        if name in ('p_signature_bytes','p_expected_signature_bytes'):return (64,64)
        if name=='p_secret_verifier':return (32,32)
        if 'canonical_manifest' in name:return (1,4096)
        raise ValueError('Unbounded bytea '+name)
    if kind=='text':
        if 'fingerprint' in name or name.endswith('manifest_digest'):return (64,64)
        if name=='p_source_order_reference':return (1,256)
        if name=='p_integration_reference':return (1,60)
        if name=='p_reason':return (1,512)
        if name=='p_provenance':return (1,1024)
        enums={'p_permission':'TRANSACTION_IDENTITY_DECISION_WRITE','p_credential_delivery_method':'PROTECTED_TTY_ONE_TIME','p_immediate_revocation_policy':'SEPARATE_APPROVAL_REQUIRED','p_algorithm_id':'Ed25519'}
        if name=='p_expected_algorithm_id':return (7,7)
        if name=='outcome':return (1,17)
        if name in enums:return (len(enums[name]),len(enums[name]))
        # Output fields are never accepted as arbitrary request text except the
        # explicitly frozen expected fingerprints handled above.
        raise ValueError('Unbounded text '+name)
    raise ValueError('Unknown transport type '+kind)

def declarations(fields,prefix='input_'):
    return ''.join('    '+prefix+name+' pg_catalog.'+kind+';\n' for name,kind in fields)

def decode(expression,stage,fields,prefix='input_',direction='INPUT'):
    domain='FLOOOW/OFFLINE-FIELD-PROOF/'+stage+'/'+direction+'/V1'
    domain_bytes=domain.encode();head=(len(domain_bytes).to_bytes(4,'big')+domain_bytes+len(fields).to_bytes(2,'big')).hex()
    total=6+len(domain_bytes)+sum(7+bound(n,t)[1] for n,t in fields)
    code=deny('pg_catalog.octet_length('+expression+')>'+str(total)+' OR pg_catalog.substring('+expression+',1,'+str(len(domain_bytes)+6)+")<>pg_catalog.decode('"+head+"','hex')")
    code+='    codec_cursor := '+str(len(domain_bytes)+6)+';\n'
    for tag,(name,kind) in enumerate(fields,1):
        var=prefix+name;lower,upper=bound(name,kind)
        code+=deny('pg_catalog.get_byte('+expression+',codec_cursor)<>'+str(tag//256)+' OR pg_catalog.get_byte('+expression+',codec_cursor+1)<>'+str(tag%256))
        code+='    codec_length := 0;\n    FOR codec_byte IN 0..3 LOOP\n        codec_length := codec_length*256+pg_catalog.get_byte('+expression+',codec_cursor+2+codec_byte);\n    END LOOP;\n'
        code+=deny('codec_length NOT BETWEEN '+str(lower+1)+' AND '+str(upper+1)+' OR codec_length>pg_catalog.octet_length('+expression+')-codec_cursor-6 OR pg_catalog.get_byte('+expression+',codec_cursor+6)<>1')
        code+='    codec_raw := pg_catalog.substring('+expression+',codec_cursor+8,(codec_length-1)::pg_catalog.int4);\n'
        if kind=='uuid':
            code+='    '+var+" := pg_catalog.encode(codec_raw,'hex')::pg_catalog.uuid;\n"+deny(var+"='00000000-0000-0000-0000-000000000000'::pg_catalog.uuid")
        elif kind=='text':
            code+='    '+var+" := pg_catalog.convert_from(codec_raw,'UTF8');\n"+deny(var+" IS NOT NFC NORMALIZED OR "+var+" ~ '[[:cntrl:]]|^[[:space:]]|[[:space:]]$'")
        elif kind=='bytea':code+='    '+var+' := codec_raw;\n'
        else:
            size=4 if kind=='int4' else 8
            code+='    codec_number := 0;\n    FOR codec_byte IN 0..'+str(size-1)+' LOOP\n        codec_number := codec_number*256+pg_catalog.get_byte(codec_raw,codec_byte);\n    END LOOP;\n'
            code+='    IF codec_number>='+str(2**(size*8-1))+' THEN codec_number := codec_number-'+str(2**(size*8))+'; END IF;\n'
            if kind=='timestamptz':
                # Exact split avoids a lossy binary-float cast of epoch microseconds.
                code+='    '+var+" := '1970-01-01 00:00:00+00'::pg_catalog.timestamptz+(pg_catalog.trunc(codec_number/1000000)::pg_catalog.text||' seconds')::pg_catalog.interval+((codec_number%1000000)::pg_catalog.text||' microseconds')::pg_catalog.interval;\n"+deny('NOT pg_catalog.isfinite('+var+') OR EXTRACT(EPOCH FROM '+var+')*1000000<>codec_number')
            else:code+='    '+var+' := codec_number::pg_catalog.'+kind+';\n'
        code+='    codec_cursor := codec_cursor+6+codec_length::pg_catalog.int4;\n'
    return code+deny('codec_cursor<>pg_catalog.octet_length('+expression+')')

def encode(stage,fields,prefix='result.'):
    payloads=[]
    for name,kind in fields:
        value=prefix+name
        if kind=='uuid':value='pg_catalog.uuid_send('+value+')'
        elif kind=='text':value=raw(value)
        elif kind in ('int4','int8'):value='pg_catalog.'+kind+'send('+value+')'
        elif kind=='timestamptz':value='pg_catalog.int8send((EXTRACT(EPOCH FROM '+value+')*1000000)::pg_catalog.int8)'
        elif kind!='bytea':raise ValueError(kind)
        payloads.append(nullable(value))
    return frame(stage+'/OUTPUT',payloads)
