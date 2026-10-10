import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.security.*;
import java.sql.*;
import java.sql.Timestamp;
import java.util.Date;
import java.time.*;
import java.util.*;
import org.flywaydb.core.Flyway;

/** Alternate-database mechanical profiling only. Never a V6 runner or policy approval.
 * Full eligibility, supervision, domain evidence and service ACLs are NOT qualified.
 * Each fixture creates a fresh memory-only key and invokes SIGN once. No private export.
 */
public final class Package0090CeremonyMechanics {
    static final String PERMISSION="TRANSACTION_IDENTITY_DECISION_WRITE";
    static final String[] PHASES={"transaction_setup","advisory_locks","t0_capture","ed25519_key_generation",
        "spki_fingerprint","v040_staging","manifest_encoding","plan_fingerprint","pre_sign_guard",
        "sign","jca_verify","postgresql_verify","v043_staging","consistency_queries",
        "pre_commit_guard","commit","query_first"};
    static byte[] utf(String s){return s.getBytes(StandardCharsets.UTF_8);}
    static byte[] sha(byte[] b)throws Exception{return MessageDigest.getInstance("SHA-256").digest(b);}
    static String hex(byte[] b){return HexFormat.of().formatHex(b);}
    static byte[] frame(Object... xs)throws Exception{
        var bytes=new ByteArrayOutputStream(); var out=new DataOutputStream(bytes);
        for(Object x:xs){byte[] b=x instanceof byte[] ? (byte[])x:utf(x.toString());out.writeInt(b.length);out.write(b);}
        return bytes.toByteArray();
    }
    static byte[] atom(Object x)throws Exception{
        if(x instanceof UUID u){var b=new ByteArrayOutputStream();var o=new DataOutputStream(b);o.writeLong(u.getMostSignificantBits());o.writeLong(u.getLeastSignificantBits());return b.toByteArray();}
        if(x instanceof Integer v){var b=new ByteArrayOutputStream();new DataOutputStream(b).writeInt(v);return b.toByteArray();}
        if(x instanceof Long v){var b=new ByteArrayOutputStream();new DataOutputStream(b).writeLong(v);return b.toByteArray();}
        return x instanceof byte[] ? (byte[])x:utf(x.toString());
    }
    static byte[] tagged(String domain,Object... values)throws Exception{
        var b=new ByteArrayOutputStream();var out=new DataOutputStream(b);byte[] d=utf(domain);
        out.writeInt(d.length);out.write(d);out.writeShort(values.length);
        for(int i=0;i<values.length;i++){byte[] v=atom(values[i]);out.writeShort(i+1);out.writeInt(v.length+1);out.writeByte(1);out.write(v);}
        return b.toByteArray();
    }
    static String instant(Timestamp t){return String.format(Locale.ROOT,"%tFT%<tT.%sZ",Date.from(t.toInstant()),String.format(Locale.ROOT,"%06d",t.getNanos()/1000));}
    static long micros(Timestamp t){Instant i=t.toInstant();return Math.addExact(Math.multiplyExact(i.getEpochSecond(),1000000L),i.getNano()/1000);}
    static PreparedStatement bind(Connection c,String sql,Object... args)throws Exception{
        var s=c.prepareStatement(sql);
        for(int i=0;i<args.length;i++){Object a=args[i];if(a instanceof byte[] b)s.setBytes(i+1,b);else s.setObject(i+1,a);}
        return s;
    }
    static void update(Connection c,String sql,Object...args)throws Exception{try(var s=bind(c,sql,args)){if(s.executeUpdate()!=1)throw new IllegalStateException("EXACT_ROWCOUNT");}}
    static String scalar(Connection c,String sql,Object...args)throws Exception{try(var s=bind(c,sql,args);var r=s.executeQuery()){if(!r.next())throw new IllegalStateException("NO_ROW");String v=r.getString(1);if(r.next())throw new IllegalStateException("MULTIPLE_ROWS");return v;}}
    static void execute(Connection c,String sql)throws Exception{try(var s=c.createStatement()){s.execute(sql);}}
    static void guard(Connection c,Timestamp t0,Timestamp end)throws Exception{
        if(!"t".equals(scalar(c,"SELECT clock_timestamp()>=?::timestamptz AND clock_timestamp()<?::timestamptz",t0,end)))throw new IllegalStateException("FIXTURE_EXPIRED");
    }
    static Connection connect(String url,String system)throws Exception{
        if(!url.matches("jdbc:postgresql://127\\.0\\.0\\.1:[0-9]+/benchmark_0090"))throw new IllegalArgumentException("ALTERNATE_DATABASE_REQUIRED");
        Connection c=DriverManager.getConnection(url,"postgres",(String)null);
        if(!"benchmark_0090|180004".equals(scalar(c,"SELECT current_database()||'|'||current_setting('server_version_num')")) ||
           !system.equals(scalar(c,"SELECT system_identifier::text FROM pg_control_system()"))){c.close();throw new IllegalStateException("FIXTURE_IDENTITY_MISMATCH");}
        return c;
    }
    static int exact(Connection c,UUID binding,UUID key,UUID authority,byte[] expectedHash,byte[] planHash)throws Exception{
        execute(c,"SET CONSTRAINTS ALL IMMEDIATE");
        int n=Integer.parseInt(scalar(c,"SELECT (SELECT count(*) FROM s2a_signer_key_revision WHERE signer_key_id=?)+(SELECT count(*) FROM s2a_signer_authority_revision WHERE signer_authority_id=?)+(SELECT count(*) FROM offline_binding_header WHERE binding_id=? AND plan_fingerprint=?)+(SELECT count(*) FROM offline_expected_signed_attestation WHERE binding_id=? AND commitment_digest=?)+(SELECT count(*) FROM offline_binding_lifecycle WHERE binding_id=? AND state='REGISTERED' AND lock_token=0)+(SELECT count(*) FROM offline_attempt_pointer WHERE binding_id=? AND current_attempt_id IS NULL AND generation=1 AND NOT claim_permitted AND lock_token=0)+(SELECT count(*) FROM offline_delivery WHERE binding_id=? AND state='NOT_CREATED' AND generation=1 AND attempt_id IS NULL AND execution_id IS NULL AND instance_id IS NULL)+(SELECT count(*) FROM offline_reconciliation WHERE binding_id=? AND state='NOT_STARTED' AND evidence_digest IS NULL AND recorded_at IS NULL)+(SELECT count(*) FROM offline_ceremony_result WHERE binding_id=? AND result='NONE' AND evidence_digest IS NULL AND recorded_at IS NULL)",key,authority,binding,planHash,binding,expectedHash,binding,binding,binding,binding,binding));
        if(n!=9)throw new IllegalStateException("FIXTURE_NINE_ROW_PROJECTION_MISMATCH");return n;
    }
    public static void main(String[] args)throws Exception{
        TimeZone.setDefault(TimeZone.getTimeZone("UTC"));
        String mode=args[0],url=args[1],system=args[2];
        try(var c=connect(url,system)){
            if(mode.equals("migrate")){
                Flyway.configure().dataSource(url,"postgres",null).locations("filesystem:"+args[3]).target("042").cleanDisabled(true).load().migrate();return;
            }
            if(!mode.equals("bench"))throw new IllegalArgumentException("MODE");
            int iterations=Integer.parseInt(args[4]),warmups=10;
            if(iterations<100 || iterations>1000)throw new IllegalArgumentException("FINITE_SAMPLE_REQUIRED");
            UUID org=UUID.randomUUID(),subject=UUID.randomUUID(),institution=UUID.randomUUID(),source=UUID.randomUUID();
            UUID deployment=UUID.randomUUID(),incarnation=UUID.randomUUID();
            byte[] policy=Files.readAllBytes(Path.of(args[3]));byte[] policyHash=sha(policy);
            c.setAutoCommit(false);
            update(c,"INSERT INTO integration_organization VALUES (?,'ACTIVE',clock_timestamp(),clock_timestamp())",org);
            update(c,"INSERT INTO offline_deadline_policy VALUES ('fixture-1',?,?,clock_timestamp())",policyHash,policy);
            update(c,"INSERT INTO offline_readiness VALUES (?,?,'NOT_READY',1,'fixture-1',?,decode('01','hex'),decode('01','hex'),clock_timestamp(),false)",deployment,incarnation,policyHash);
            update(c,"INSERT INTO offline_preflight_key VALUES (?,?,1,'RETIRED',NULL,sha256(decode('01','hex')))",incarnation,UUID.randomUUID());
            c.commit();c.setAutoCommit(true);
            var slotBuffer=new ByteArrayOutputStream();var slotOut=new DataOutputStream(slotBuffer);slotOut.writeInt(4);
            for(int slot=1;slot<=4;slot++){
                String name="bench_slot_"+slot;byte[] nameBytes=utf(name);int oid=Integer.parseInt(scalar(c,"SELECT oid FROM pg_roles WHERE rolname=?",name));
                slotOut.writeInt(9+nameBytes.length);slotOut.writeByte(slot);slotOut.writeInt(oid);slotOut.writeInt(nameBytes.length);slotOut.write(nameBytes);
            }
            byte[] slots=slotBuffer.toByteArray();
            System.out.println("iteration,"+String.join(",",PHASES)+",total_us");
            for(int i=-warmups;i<iterations;i++){
                double[] times=new double[PHASES.length];int step=0;long total=System.nanoTime(),start=total;
                c.setAutoCommit(false);execute(c,"SET LOCAL TIME ZONE 'UTC'");
                times[step++]=(System.nanoTime()-start)/1000.0;start=System.nanoTime();
                UUID binding=UUID.randomUUID(),key=UUID.randomUUID(),authority=UUID.randomUUID(),manifestId=UUID.randomUUID(),correlation=UUID.randomUUID();
                scalar(c,"SELECT pg_advisory_xact_lock(hashtextextended(?,0))", "MECHANICS_ONLY:"+binding);
                times[step++]=(System.nanoTime()-start)/1000.0;start=System.nanoTime();
                Timestamp t0;try(var s=c.createStatement();var r=s.executeQuery("SELECT transaction_timestamp()")){r.next();t0=r.getTimestamp(1);}
                Timestamp end=Timestamp.from(t0.toInstant().plusSeconds(60));
                times[step++]=(System.nanoTime()-start)/1000.0;start=System.nanoTime();
                KeyPair pair=KeyPairGenerator.getInstance("Ed25519").generateKeyPair();
                times[step++]=(System.nanoTime()-start)/1000.0;start=System.nanoTime();
                byte[] spki=pair.getPublic().getEncoded();String keyFp=hex(sha(spki));
                times[step++]=(System.nanoTime()-start)/1000.0;start=System.nanoTime();
                String lineage=scalar(c,"SELECT s2a_signer_key_lineage_fingerprint(?,?,1,?,'Ed25519',?,?,'ACTIVE',?,?,NULL,NULL)",org,key,subject,spki,keyFp,t0,t0);
                if(!"APPLIED".equals(scalar(c,"SELECT outcome FROM s2a_append_signer_key_revision(?,?,1,?,'Ed25519',?,?,'ACTIVE',?,?,NULL,?,'benchmark','MECHANICS_ONLY',?)",org,key,subject,spki,keyFp,t0,t0,lineage,correlation)))throw new IllegalStateException("KEY_STAGE");
                String authFp=scalar(c,"SELECT s2a_signer_authority_fingerprint(?,?,1,?,?,'S2A_FIELD_PROOF_APPROVER',?,1,?,'S2A_FIELD_PROOF_APPROVAL',?,?,?,'ENABLED',?,NULL,NULL)",org,authority,subject,institution,key,keyFp,PERMISSION,t0,end,source);
                if(!"APPLIED".equals(scalar(c,"SELECT outcome FROM s2a_append_signer_authority_revision(?,?,1,?,?,'S2A_FIELD_PROOF_APPROVER',?,1,?,'S2A_FIELD_PROOF_APPROVAL',?,?,?,'ENABLED',NULL,?,'benchmark','MECHANICS_ONLY',?,?)",org,authority,subject,institution,key,keyFp,PERMISSION,t0,end,authFp,source,correlation)))throw new IllegalStateException("AUTH_STAGE");
                times[step++]=(System.nanoTime()-start)/1000.0;start=System.nanoTime();
                UUID ml=UUID.randomUUID(),omie=UUID.randomUUID(),order=UUID.randomUUID();
                byte[] manifest=frame("FLOOOW:S2A:APPROVAL-MANIFEST:1",1,manifestId,org,ml,omie,order,"fixture-order","fixture-link",hex(sha(frame("MECHANICS_ONLY"))),PERMISSION,"benchmark","MECHANICS_ONLY",instant(t0),instant(end),UUID.randomUUID(),source,UUID.randomUUID(),UUID.randomUUID(),UUID.randomUUID(),"PROTECTED_TTY_ONE_TIME","SEPARATE_APPROVAL_REQUIRED",correlation);
                byte[] digest=sha(manifest);
                times[step++]=(System.nanoTime()-start)/1000.0;start=System.nanoTime();
                Object[] header={1,binding,deployment,incarnation,UUID.randomUUID(),UUID.randomUUID(),1,org,manifestId,digest,digest,1,ml,omie,order,"fixture-order","fixture-link",PERMISSION,"benchmark","MECHANICS_ONLY",UUID.randomUUID(),UUID.randomUUID(),UUID.randomUUID(),UUID.randomUUID(),correlation,UUID.randomUUID(),UUID.randomUUID(),UUID.randomUUID(),micros(t0),micros(t0),micros(end),slots,"0090-v1","fixture-1",policyHash,"1","1","1"};
                byte[] planHash=sha(tagged("FLOOOW/OFFLINE-FIELD-PROOF/BINDING/V1",header));
                byte[] preimage=frame("FLOOOW:S2A:APPROVAL-SIGNATURE:1","Ed25519",key,keyFp,hex(digest));
                times[step++]=(System.nanoTime()-start)/1000.0;start=System.nanoTime();
                guard(c,t0,end);
                times[step++]=(System.nanoTime()-start)/1000.0;start=System.nanoTime();
                Signature signer=Signature.getInstance("Ed25519");signer.initSign(pair.getPrivate());signer.update(preimage);byte[] signature=signer.sign();
                times[step++]=(System.nanoTime()-start)/1000.0;start=System.nanoTime();
                Signature verifier=Signature.getInstance("Ed25519");verifier.initVerify(pair.getPublic());verifier.update(preimage);if(!verifier.verify(signature))throw new IllegalStateException("JCA_REJECT");
                pair=null;signer=null;
                times[step++]=(System.nanoTime()-start)/1000.0;start=System.nanoTime();
                if(!"t".equals(scalar(c,"SELECT bench_canonical_spki_ed25519_verify(?,?,?)",spki,preimage,signature)))throw new IllegalStateException("PG_REJECT");
                times[step++]=(System.nanoTime()-start)/1000.0;start=System.nanoTime();
                byte[] expected=tagged("FLOOOW/OFFLINE-FIELD-PROOF/EXPECTED-SIGNED-ATTESTATION/V1",binding,hex(digest),"Ed25519",key,keyFp,signature);
                Object[] stored=new Object[40];System.arraycopy(header,0,stored,0,38);stored[28]=t0;stored[29]=t0;stored[30]=end;stored[38]=planHash;stored[39]=manifest;
                update(c,"INSERT INTO offline_binding_header VALUES ("+String.join(",",Collections.nCopies(40,"?"))+")",stored);
                update(c,"INSERT INTO offline_expected_signed_attestation VALUES (?,?,'Ed25519',?,?,?,?,?)",binding,hex(digest),key,keyFp,signature,expected,sha(expected));
                update(c,"INSERT INTO offline_binding_lifecycle VALUES (?,'REGISTERED',0)",binding);
                update(c,"INSERT INTO offline_attempt_pointer VALUES (?,NULL,1,false,0)",binding);
                update(c,"INSERT INTO offline_delivery(binding_id,generation,state,lock_token) VALUES (?,1,'NOT_CREATED',0)",binding);
                update(c,"INSERT INTO offline_reconciliation VALUES (?,'NOT_STARTED',NULL,NULL)",binding);
                update(c,"INSERT INTO offline_ceremony_result VALUES (?,'NONE',NULL,NULL)",binding);
                times[step++]=(System.nanoTime()-start)/1000.0;start=System.nanoTime();
                exact(c,binding,key,authority,sha(expected),planHash);
                times[step++]=(System.nanoTime()-start)/1000.0;start=System.nanoTime();
                guard(c,t0,end);
                times[step++]=(System.nanoTime()-start)/1000.0;start=System.nanoTime();
                c.commit();c.setAutoCommit(true);
                times[step++]=(System.nanoTime()-start)/1000.0;start=System.nanoTime();
                try(var fresh=connect(url,system)){
                    fresh.setAutoCommit(false);scalar(fresh,"SELECT binding_id FROM offline_binding_header WHERE binding_id=? FOR UPDATE",binding);
                    exact(fresh,binding,key,authority,sha(expected),planHash);fresh.rollback();
                }
                times[step++]=(System.nanoTime()-start)/1000.0;
                if(step!=17)throw new IllegalStateException("PHASE_COUNT");
                double totalUs=(System.nanoTime()-total)/1000.0;
                System.out.print(i);for(double value:times)System.out.printf(Locale.ROOT,",%.3f",value);
                System.out.printf(Locale.ROOT,",%.3f%n",totalUs);
            }
        }
    }
}
