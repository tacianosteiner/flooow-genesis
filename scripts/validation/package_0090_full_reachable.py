"""TEST-only result-tuple compatibility proof; never invokes S04 or creates READY."""
import json
import struct
import zipfile
import zlib
from pathlib import Path
import package_0090_source_closure as q

BASELINE='ca6c049567c8d1ed7f2ea75819788eaf862d42b9'
OUT=q.ROOT/'docs/evidence/package-0090-full-reachable-expectation-closure'
ADDENDUM=q.ROOT/'docs/evidence/package-0090-test-activation-native-health-first-positive/s04-source-addendum.json'
JAR_REL='org.flywaydb/flyway-database-postgresql/13.2.0/6e7e548a22ab462454469d86bc9e09b52601985f/flyway-database-postgresql-13.2.0.jar'


def save(name,value): (OUT/name).write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')


def constant_strings(data):
    q.require(data[:4]==b'\xca\xfe\xba\xbe','Java class signature differs')
    count=struct.unpack_from('>H',data,8)[0]; offset=10; index=1; strings=[]
    while index<count:
        tag=data[offset]; offset+=1
        if tag==1:
            length=struct.unpack_from('>H',data,offset)[0]; offset+=2
            strings.append(data[offset:offset+length].decode('utf-8',errors='strict')); offset+=length
        elif tag in [3,4,9,10,11,12,17,18]: offset+=4
        elif tag in [5,6]: offset+=8; index+=1
        elif tag in [7,8,16,19,20]: offset+=2
        elif tag==15: offset+=3
        else: raise RuntimeError('Unsupported Java constant tag '+str(tag))
        index+=1
    return strings


def prepare():
    OUT.mkdir(exist_ok=True)
    source=q.git('show',BASELINE+':'+q.V043.relative_to(q.ROOT).as_posix())
    q.require(q.sha(source)==q.SOURCE_HASH and source==q.V043.read_bytes().replace(b'\r\n',b'\n'),'Canonical source differs')
    add=json.loads(ADDENDUM.read_text()); sites=add['operator_and_implicit_expression_sites']
    q.require(len(sites)==190,'Existing denominator differs')
    rows=[]
    for i,s in enumerate(sites):
        rows.append(dict(SITE_ID='S04-EXPR-%03d'%i,SOURCE_LOCATION={k:s[k] for k in ['statement_ordinal','ast_path','control_path']},SOURCE_EXPRESSION=s['ast'],EXPRESSION_KIND=s['kind'],STATIC_INPUT_TYPES='PENDING_FULL_TYPED_ANALYSIS',EXPECTED_RESOLUTION_STATUS='NOT_CLOSED',source_site_sha256=q.sha(json.dumps(s,sort_keys=True,separators=(',',':')).encode())))
    save('expression-site-denominator.json',dict(complete=True,source_addendum_sha256=q.sha(ADDENDUM.read_bytes()),total=190,sites=rows,no_recalculation_or_reclassification=True,counts={k:sum(x['kind']==k for x in sites) for k in sorted({x['kind'] for x in sites})}))
    # Independently extract the pinned Flyway construction template from its
    # Java constant pool, before reading any runtime target.
    jar=Path.home()/'.gradle/caches/modules-2/files-2.1'/JAR_REL
    prior=q.ROOT/'docs/evidence/package-0090-effective-expectation-t10-fence/run-2/foundation-runtime.json'
    expected_hash=json.loads(prior.read_text())['jvm_input_hashes'][JAR_REL]
    q.require(q.sha(jar.read_bytes())==expected_hash,'Approved Flyway provider artifact differs')
    with zipfile.ZipFile(jar) as z:
        member='org/flywaydb/database/postgresql/PostgreSQLDatabase.class'; bytecode=z.read(member)
    templates=[s for s in constant_strings(bytecode) if 'CREATE TABLE' in s and 'VARCHAR(50)' in s and 'VARCHAR(1000)' in s]
    q.require(len(templates)==1,'History constructor template not unique')
    (OUT/'flyway-history-constructor-template.txt').write_text(templates[0]+'\n',encoding='utf-8')
    schema=[dict(name='installed_rank',type='int4',typmod=-1),dict(name='version',type='varchar',typmod=54),dict(name='type',type='varchar',typmod=24),dict(name='script',type='varchar',typmod=1004),dict(name='checksum',type='int4',typmod=-1),dict(name='success',type='bool',typmod=-1)]
    query='SELECT h.installed_rank,h.version,h.type,h.script,h.checksum,h.success FROM public.flyway_schema_history h ORDER BY h.installed_rank'
    canonical_text=source.decode()
    q.require('RETURN QUERY '+query.replace(' FROM','\n      FROM')+';' in canonical_text,'Return-query witness not exact source statement')
    q.require('RETURNS TABLE(installed_rank pg_catalog.int4,version pg_catalog.text,type pg_catalog.text,script pg_catalog.text,checksum pg_catalog.int4,success pg_catalog.bool)' in canonical_text,'Canonical return declaration differs')
    history=[]
    for rank,p in enumerate(sorted(p for p in q.MIGRATIONS.glob('V*.sql') if int(p.name.split('__')[0][1:])<=42),1):
        b=q.git('show',BASELINE+':'+p.relative_to(q.ROOT).as_posix()); q.require(b==q.git('show',q.FROZEN+':'+p.relative_to(q.ROOT).as_posix()),'Frozen migration differs')
        crc=0
        for line in b.decode('utf-8-sig').splitlines(): crc=zlib.crc32(line.encode(),crc)
        history.append(dict(installed_rank=rank,version=p.name.split('__')[0][1:],type='SQL',script=p.name,checksum=crc if crc<2**31 else crc-2**32,success=True))
    save('return-tuple-expectation.json',dict(canonical_declared_types=['int4','text','text','text','int4','bool'],independent_Flyway_projection=schema,source_query=query,query_sha256=q.sha(query.encode()),Flyway_jar_sha256=expected_hash,Flyway_class_member=member,Flyway_class_sha256=q.sha(bytecode),constructor_template_sha256=q.sha((OUT/'flyway-history-constructor-template.txt').read_bytes()),expected_history=history,expected_compatibility='MISMATCH_REQUIRES_CONTROLLED_POSTGRES_PROOF',canonical_S04_execution_forbidden=True))


def qualify(sql,run,container,folder,record,fixture,runtime_work):
    expected=json.loads((OUT/'return-tuple-expectation.json').read_text()); cases=[]
    def case(name,passed,detail):
        row=dict(name=name,passed=bool(passed),group='RETURN_TUPLE_COMPATIBILITY',details=detail)
        record['cases'].append(row); cases.append(row); q.require(passed,name)
    attributes=json.loads(sql("SELECT json_agg(json_build_object('name',a.attname,'type',t.typname,'typmod',a.atttypmod) ORDER BY array_position(ARRAY['installed_rank','version','type','script','checksum','success'],a.attname)) FROM pg_attribute a JOIN pg_type t ON t.oid=a.atttypid WHERE a.attrelid='public.flyway_schema_history'::regclass AND a.attname=ANY(ARRAY['installed_rank','version','type','script','checksum','success']);").stdout)
    case('runtime_history_types_match_pinned_Flyway_constructor',attributes==expected['independent_Flyway_projection'],attributes)
    actual_types=json.loads(sql("SELECT json_agg(t.typname ORDER BY x.ordinal) FROM pg_proc p CROSS JOIN LATERAL unnest(p.proallargtypes,p.proargmodes) WITH ORDINALITY AS x(oid,mode,ordinal) JOIN pg_type t ON t.oid=x.oid WHERE p.oid='public.offline_read_history(uuid,bytea,uuid,text)'::regprocedure AND x.mode='t';").stdout)
    case('S04_declared_output_types_match_canonical_source',actual_types==expected['canonical_declared_types'],actual_types)
    query=expected['source_query']
    # All helper functions live only in this psql session's pg_temp namespace.
    # The witness copies the exact RETURN QUERY and output declaration, excluding
    # S04 identity/policy/health logic. It is a PostgreSQL tuple-conversion test.
    script="""
CREATE FUNCTION pg_temp.test_0090_raw_shape() RETURNS TABLE(installed_rank int4,version text,type text,script text,checksum int4,success bool) LANGUAGE plpgsql AS $probe$ BEGIN RETURN QUERY QUERY_PLACEHOLDER; END $probe$;
CREATE FUNCTION pg_temp.test_0090_capture_shape_error() RETURNS jsonb LANGUAGE plpgsql AS $probe$ DECLARE state text; detail text; message text; BEGIN PERFORM * FROM pg_temp.test_0090_raw_shape(); RETURN jsonb_build_object('unexpected_success',true); EXCEPTION WHEN OTHERS THEN GET STACKED DIAGNOSTICS state=RETURNED_SQLSTATE,detail=PG_EXCEPTION_DETAIL,message=MESSAGE_TEXT; RETURN jsonb_build_object('sqlstate',state,'detail',detail,'message',message); END $probe$;
SELECT pg_temp.test_0090_capture_shape_error();
""".replace('QUERY_PLACEHOLDER',query)
    failure=json.loads(sql(script).stdout.decode().splitlines()[-1])
    case('exact_projection_text_return_contract_denied_42804',failure.get('sqlstate')=='42804' and 'character varying' in failure.get('detail','') and 'text' in failure.get('detail',''),failure)
    # A contrast helper changes only its own SELECT projections, never canonical
    # source or an approved function. Its 42-row control is NOT an S04 positive.
    contrast=query.replace('h.version,h.type,h.script','h.version::text,h.type::text,h.script::text')
    control_sql="CREATE FUNCTION pg_temp.test_0090_contrast_shape() RETURNS TABLE(installed_rank int4,version text,type text,script text,checksum int4,success bool) LANGUAGE plpgsql AS $probe$ BEGIN RETURN QUERY "+contrast+"; END $probe$; SELECT jsonb_agg(t ORDER BY installed_rank) FROM pg_temp.test_0090_contrast_shape() t;"
    actual=json.loads(sql(control_sql).stdout.decode().splitlines()[-1])
    case('TEST_ONLY_contrast_projection_exact_42_history_rows',actual==expected['expected_history'],dict(rows=len(actual),canonical_S04_executed=False,canonical_fix_not_applied=True))
    # Isolate each textual output position so one first-error does not hide the
    # other mismatched fields. Each probe is a different PostgreSQL contract.
    for column in ['version','type','script']:
        isolated="CREATE FUNCTION pg_temp.test_0090_one_shape() RETURNS TABLE(value text) LANGUAGE plpgsql AS $probe$ BEGIN RETURN QUERY SELECT h."+column+" FROM public.flyway_schema_history h; END $probe$; CREATE FUNCTION pg_temp.test_0090_capture() RETURNS text LANGUAGE plpgsql AS $probe$ BEGIN PERFORM * FROM pg_temp.test_0090_one_shape(); RETURN 'UNEXPECTED_SUCCESS'; EXCEPTION WHEN OTHERS THEN RETURN SQLSTATE; END $probe$; SELECT pg_temp.test_0090_capture();"
        error=sql(isolated).stdout.decode().splitlines()[-1]
        case('text_result_mismatch_'+column,error=='42804',dict(column=column,sqlstate=error))
    counts={name:int(sql('SELECT count(*) FROM public.'+name+';').stdout) for name in ['offline_readiness','offline_binding_header','offline_expected_signed_attestation']}
    case('no_eligibility_material_created',all(v==0 for v in counts.values()),counts)
    case('canonical_source_still_exact',q.sha(q.git('show',BASELINE+':'+q.V043.relative_to(q.ROOT).as_posix()))==q.SOURCE_HASH,dict(source_sha256=q.SOURCE_HASH,canonical_submitted=False))
    (folder/'return-tuple-runtime.json').write_text(json.dumps(dict(cases=cases,history_types=attributes,S04_declared_output_types=actual_types,isolated_error=failure,contrast_rows=actual,canonical_S04_executed=False,readiness_created=False,source_corrected=False,qualification_target=record['isolation']),indent=2)+'\n')


if __name__=='__main__': prepare()
