"""Independent SPEC21.1 S10 public decoder; no generator imports or DB lookups."""
import re
import struct
import uuid

DOMAIN='FLOOOW/OFFLINE-FIELD-PROOF/S10/OUTPUT/V1'

def frame(data, count):
    if not isinstance(data,bytes) or len(data)>65536:raise ValueError('Invalid frame')
    cursor=0
    def take(n):
        nonlocal cursor
        if n<0 or cursor+n>len(data):raise ValueError('Truncated frame')
        out=data[cursor:cursor+n];cursor+=n;return out
    n=struct.unpack('>I',take(4))[0]
    if take(n)!=DOMAIN.encode() or struct.unpack('>H',take(2))[0]!=count:raise ValueError('Wrong domain/count')
    out=[]
    for tag in range(1,count+1):
        if struct.unpack('>H',take(2))[0]!=tag:raise ValueError('Wrong tag')
        n=struct.unpack('>I',take(4))[0];v=take(n)
        if v==b'\x00':out.append(None)
        elif v and v[0]==1:out.append(v[1:])
        else:raise ValueError('Wrong presence')
    if cursor!=len(data):raise ValueError('Trailing bytes')
    return out

def identifier(value):
    if value is None or len(value)!=16:raise ValueError('Required UUID')
    result=uuid.UUID(bytes=value)
    if result.int==0:raise ValueError('Nil UUID')
    return result

def decode(data):
    # SPEC21.1 overriding S10 envelope, not the frozen OUTPUT line alone.
    receipt,fresh,execution,instance,state=frame(data,5)
    if receipt is None or state is None:raise ValueError('Missing outer field')
    outcome,operation,intent,fingerprint,effect=frame(receipt,5)
    if outcome not in (b'APPLIED',b'ALREADY_APPLIED'):raise ValueError('Invalid frozen outcome')
    if any(v is None or re.fullmatch(b'[0-9a-f]{64}',v) is None for v in (intent,fingerprint)):raise ValueError('Invalid fingerprint')
    if effect is None or len(effect)!=8:raise ValueError('Invalid effect time')
    if (outcome==b'APPLIED')!=(fresh is not None):raise ValueError('Fresh/replay UUID mismatch')
    if state not in (b'CREATED_NOT_DELIVERABLE',b'DELIVERY_ATTEMPTED',b'DELIVERY_ACKNOWLEDGED',b'DELIVERY_FAILED_REVIEW_REQUIRED',b'DELIVERY_OUTCOME_UNKNOWN'):raise ValueError('Invalid delivery state')
    return dict(frozen_receipt=receipt,outcome=outcome.decode(),operation_id=identifier(operation),
        fresh_applied_receipt_id=None if fresh is None else identifier(fresh),
        execution_id=identifier(execution),instance_id=identifier(instance),delivery_state=state.decode())

def caller_decoder_sql():
    # Test-only SECURITY INVOKER codec over its supplied bytes, with zero table
    # access. psql transports its UUID as a client variable into S14.
    return """CREATE FUNCTION public.test_s10_caller_decode(data bytea) RETURNS uuid
LANGUAGE plpgsql SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $codec$
DECLARE c integer; n integer; i integer; t integer; v bytea; result uuid;
BEGIN
 c:=4+octet_length(convert_to('FLOOOW/OFFLINE-FIELD-PROOF/S10/OUTPUT/V1','UTF8'));
 IF substring(data,1,c)<>int4send(c-4)||convert_to('FLOOOW/OFFLINE-FIELD-PROOF/S10/OUTPUT/V1','UTF8') OR substring(data,c+1,2)<>int2send(5::smallint) THEN RAISE EXCEPTION 'Wrong S10 frame'; END IF;
 c:=c+2;
 FOR t IN 1..5 LOOP
  IF substring(data,c+1,2)<>int2send(t::smallint) THEN RAISE EXCEPTION 'Wrong S10 tag'; END IF;
  n:=0; FOR i IN 0..3 LOOP n:=n*256+get_byte(data,c+2+i); END LOOP;
  IF n<1 OR n>octet_length(data)-c-6 THEN RAISE EXCEPTION 'Wrong S10 length'; END IF;
  v:=substring(data,c+7,n);
  IF t=2 AND v=decode('00','hex') THEN result:=NULL;
  ELSE
   IF get_byte(v,0)<>1 THEN RAISE EXCEPTION 'Wrong presence'; END IF;
   IF t IN (2,3,4) AND n<>17 THEN RAISE EXCEPTION 'Wrong UUID'; END IF;
   IF t=2 THEN result:=encode(substring(v,2,16),'hex')::uuid; END IF;
  END IF;
  c:=c+6+n;
 END LOOP;
 IF c<>octet_length(data) THEN RAISE EXCEPTION 'Trailing S10 bytes'; END IF;
 RETURN result;
END $codec$;
"""
