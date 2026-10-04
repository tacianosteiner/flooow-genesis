// TEST ONLY: actual frozen accepted() with mock JDBC transport, never a DB.
import io.flooow.ceremony.*;
import io.flooow.marketplace.operations.authorization.*;
import java.lang.reflect.*;
import java.nio.file.*;
import java.security.*;
import java.security.spec.*;
import java.sql.*;
import java.time.*;
import java.util.*;
import javax.sql.DataSource;
import java.io.*;
import java.nio.charset.StandardCharsets;

class Package0090S02ExpectedAttestationWitness {
    static final HexFormat HEX=HexFormat.of();
    static Object invoke(Object target,String prefix,Object... arguments) throws Exception {
        var method=Arrays.stream(target.getClass().getMethods()).filter(m->m.getName().startsWith(prefix)
            && m.getParameterCount()==arguments.length).findFirst().orElseThrow();
        return method.invoke(target,arguments);
    }
    static byte[] sha(byte[] bytes) throws Exception { return MessageDigest.getInstance("SHA-256").digest(bytes); }
    static Object proxy(Class<?> type,InvocationHandler handler) {
        return Proxy.newProxyInstance(type.getClassLoader(),new Class<?>[]{type},handler);
    }
    static ResultSet rows(Map<String,Object> row,boolean count) {
        int[] next={0};
        return (ResultSet)proxy(ResultSet.class,(p,m,a)-> {
            if(m.getName().equals("next"))return next[0]++==0;
            if(m.getName().equals("close"))return null;
            if(m.getName().equals("wasNull"))return false;
            if(count && m.getName().equals("getInt"))return 1;
            if(m.getName().startsWith("get"))return row.get((String)a[0]);
            throw new UnsupportedOperationException(m.getName());
        });
    }
    static Connection connection(Map<String,Object> row) {
        return (Connection)proxy(Connection.class,(p,m,a)-> {
            if(m.getName().equals("prepareStatement")) {
                String sql=(String)a[0];
                return proxy(PreparedStatement.class,(pp,mm,aa)-> {
                    if(mm.getName().equals("executeQuery"))return rows(row,sql.startsWith("SELECT count(*)"));
                    if(mm.getName().startsWith("set")||mm.getName().equals("close"))return null;
                    throw new UnsupportedOperationException(mm.getName());
                });
            }
            throw new UnsupportedOperationException(m.getName());
        });
    }
    static SignedApprovalAttestation signed(ApprovalManifest manifest,int keyNumber) throws Exception {
        // Public RFC 8032 test seeds only, never production private keys.
        String seed=keyNumber==1?"9d61b19deffd5a60ba844af492ec2cc44449c5697b326919703bac031cae7f60":
            "4ccd089b28ff96da9db6c346ec114e0f5b8a319f35aba624da8cf6ed4fb8a6fb";
        String raw=keyNumber==1?"d75a980182b10ab7d54bfed3c964073a0ee172f3daa62325af021a68f707511a":
            "3d4017c3e843895a92b70aa74d1b7ebc9c982ccf2ec4968cc0cd55f12af4660c";
        byte[] spki=HEX.parseHex("302a300506032b6570032100"+raw);
        String fp=HEX.formatHex(sha(spki));UUID id=new UUID(0,100+keyNumber);
        var codec=ApprovalManifestCanonicalCodec.INSTANCE;
        byte[] canonical=codec.canonicalManifestBytes(manifest);
        byte[] preimage=(byte[])invoke(codec,"canonicalSignaturePreimageBytes","Ed25519",id,fp,codec.manifestDigest(canonical));
        var privateKey=KeyFactory.getInstance("Ed25519").generatePrivate(new EdECPrivateKeySpec(NamedParameterSpec.ED25519,HEX.parseHex(seed)));
        var signer=Signature.getInstance("Ed25519");signer.initSign(privateKey);signer.update(preimage);
        return (SignedApprovalAttestation)invoke(SignedApprovalAttestation.Companion,"parse",manifest,"Ed25519",id,fp,
            Base64.getUrlEncoder().withoutPadding().encodeToString(signer.sign()));
    }
    static Map<String,Object> row(SignedApprovalAttestation signed,int keyNumber) throws Exception {
        var m=signed.getManifest();var codec=ApprovalManifestCanonicalCodec.INSTANCE;
        byte[] canonical=codec.canonicalManifestBytes(m);String digest=codec.manifestDigest(canonical);
        UUID id=(UUID)invoke(signed,"getSignerKeyId");String fp=(String)invoke(signed,"getSignerKeyFingerprint");
        byte[] preimage=(byte[])invoke(codec,"canonicalSignaturePreimageBytes","Ed25519",id,fp,digest);
        String raw=keyNumber==1?"d75a980182b10ab7d54bfed3c964073a0ee172f3daa62325af021a68f707511a":
            "3d4017c3e843895a92b70aa74d1b7ebc9c982ccf2ec4968cc0cd55f12af4660c";
        byte[] spki=HEX.parseHex("302a300506032b6570032100"+raw);
        var verifiedAt=m.getApprovalWindowStart().plusSeconds(1);
        var proof=(AcceptedAttestationProof)invoke(AcceptedAttestationProof.Companion,"create",1,1,canonical,digest,
            preimage,"Ed25519",id,1,fp,"a".repeat(64),spki,signed.signatureBytes(),new UUID(0,200+keyNumber),1,
            "b".repeat(64),verifiedAt);
        var values=new HashMap<String,Object>();
        values.put("artifact_version",1);values.put("schema_version",1);values.put("canonicalization_version",1);
        values.put("canonical_manifest_bytes",canonical);values.put("manifest_digest",digest);
        values.put("canonical_signature_preimage_bytes",preimage);values.put("algorithm_id","Ed25519");
        values.put("signer_key_id",id);values.put("signer_key_revision",1);values.put("signer_key_fingerprint",fp);
        values.put("signer_key_lineage_fingerprint","a".repeat(64));values.put("subject_public_key_info_der",spki);
        values.put("signature_bytes",signed.signatureBytes());values.put("signer_authority_id",new UUID(0,200+keyNumber));
        values.put("signer_authority_revision",1);values.put("signer_authority_fingerprint","b".repeat(64));
        values.put("verified_at",java.sql.Timestamp.from(verifiedAt));values.put("recorded_at",java.sql.Timestamp.from(verifiedAt));
        values.put("accepted_proof_fingerprint",AcceptedAttestationFingerprintCodec.INSTANCE.fingerprint(proof));
        return values;
    }
    static byte[] acceptedSnapshot(SignedApprovalAttestation original,int number) throws Exception {
        var values=row(original,number);var manifest=original.getManifest();
        values.put("organization_id",invoke(manifest,"getOrganizationId"));values.put("manifest_id",manifest.getManifestId());
        String[] names={"organization_id","manifest_id","artifact_version","schema_version","canonicalization_version",
            "canonical_manifest_bytes","manifest_digest","canonical_signature_preimage_bytes","algorithm_id","signer_key_id",
            "signer_key_revision","signer_key_fingerprint","signer_key_lineage_fingerprint","subject_public_key_info_der",
            "signature_bytes","signer_authority_id","signer_authority_revision","signer_authority_fingerprint",
            "verified_at","accepted_proof_fingerprint","recorded_at"};
        var buffer=new ByteArrayOutputStream();var out=new DataOutputStream(buffer);
        byte[] domain="FLOOOW/OFFLINE-FIELD-PROOF/RECONCILE-ACCEPTED/V1".getBytes(StandardCharsets.UTF_8);
        out.writeInt(domain.length);out.write(domain);out.writeShort(names.length);
        for(int index=0;index<names.length;index++) {
            Object value=values.get(names[index]);var payloadBuffer=new ByteArrayOutputStream();var payload=new DataOutputStream(payloadBuffer);
            payload.writeByte(1);
            if(value instanceof UUID id) {payload.writeLong(id.getMostSignificantBits());payload.writeLong(id.getLeastSignificantBits());}
            else if(value instanceof Integer integer)payload.writeInt(integer);
            else if(value instanceof byte[] bytes)payload.write(bytes);
            else if(value instanceof java.sql.Timestamp timestamp) {var instant=timestamp.toInstant();payload.writeLong(Math.addExact(Math.multiplyExact(instant.getEpochSecond(),1000000),instant.getNano()/1000));}
            else payload.write(value.toString().getBytes(StandardCharsets.UTF_8));
            byte[] bytes=payloadBuffer.toByteArray();out.writeShort(index+1);out.writeInt(bytes.length);out.write(bytes);
        }
        return buffer.toByteArray();
    }
    public static void main(String[] args) throws Exception {
        var base=OfflineFieldProofInputLoader.INSTANCE.load(Path.of(args[0]));
        var first=signed(base.getAttestation().getManifest(),1);var second=signed(first.getManifest(),2);
        var input1=new OfflineFieldProofInput(first,base.getTarget(),base.getCommand(),base.getPlan());
        var input2=new OfflineFieldProofInput(second,base.getTarget(),base.getCommand(),base.getPlan());
        var reconciler=new PostgresOfflineFieldProofReconciler((DataSource)proxy(DataSource.class,(p,m,a)-> {throw new UnsupportedOperationException();}));
        var accepted=PostgresOfflineFieldProofReconciler.class.getDeclaredMethod("accepted",Connection.class,OfflineFieldProofInput.class);
        accepted.setAccessible(true);
        boolean a=(Boolean)accepted.invoke(reconciler,connection(row(first,1)),input1);
        boolean b=(Boolean)accepted.invoke(reconciler,connection(row(first,1)),input2);
        boolean c=(Boolean)accepted.invoke(reconciler,connection(row(second,2)),input1);
        boolean d=(Boolean)accepted.invoke(reconciler,connection(row(second,2)),input2);
        if(!a||b||c||!d)throw new AssertionError("Frozen expected-attestation witness failed");
        if(!first.getManifest().equals(second.getManifest())||!input1.getPlan().equals(input2.getPlan()))throw new AssertionError();
        System.out.println("CANONICAL_MANIFEST_EQUAL=true");
        System.out.println("PLAN_EQUAL=true");
        System.out.println("STORED_A_EXPECTED_A="+a);
        System.out.println("STORED_A_EXPECTED_B="+b);
        System.out.println("STORED_B_EXPECTED_A="+c);
        System.out.println("STORED_B_EXPECTED_B="+d);
        System.out.println("MANIFEST_DIGEST="+ApprovalManifestCanonicalCodec.INSTANCE.manifestDigest(
            ApprovalManifestCanonicalCodec.INSTANCE.canonicalManifestBytes(first.getManifest())));
        if(args.length==2) {
            var lines=new ArrayList<String>();
            for(int number=1;number<=2;number++) {
                var original=number==1?first:second;
                String label=number==1?"A":"B";
                // ORIGINAL comes directly from signed(), before any database row.
                lines.add("ORIGINAL_"+label+"_algorithm_id="+original.getAlgorithmId());
                lines.add("ORIGINAL_"+label+"_signer_key_id="+invoke(original,"getSignerKeyId"));
                lines.add("ORIGINAL_"+label+"_signer_key_fingerprint="+invoke(original,"getSignerKeyFingerprint"));
                lines.add("ORIGINAL_"+label+"_signature_bytes="+HEX.formatHex(original.signatureBytes()));
                lines.add("ORIGINAL_"+label+"_manifest_digest="+ApprovalManifestCanonicalCodec.INSTANCE.manifestDigest(
                    ApprovalManifestCanonicalCodec.INSTANCE.canonicalManifestBytes(original.getManifest())));
                lines.add("S03_ACCEPTED_"+label+"_SNAPSHOT="+HEX.formatHex(acceptedSnapshot(original,number)));
                for(var entry:new TreeMap<>(row(original,number)).entrySet()) {
                    Object value=entry.getValue();
                    String encoded=value instanceof byte[] bytes?HEX.formatHex(bytes):
                        value instanceof java.sql.Timestamp timestamp?timestamp.toInstant().toString():value.toString();
                    lines.add("ROW_"+label+"_"+entry.getKey()+"="+encoded);
                }
            }
            Files.write(Path.of(args[1]),lines);
        }
    }
}
