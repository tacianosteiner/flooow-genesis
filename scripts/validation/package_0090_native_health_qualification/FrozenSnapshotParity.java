// Public disposable input only. No key generation, private keys, signing or DB.
import java.nio.file.*;
import java.lang.reflect.*;
import java.time.*;
import java.util.*;
public final class FrozenSnapshotParity {
  static Object verify(Object manifest,Object[] values,Constructor<?> ctor,Object verifier,Method method) throws Exception {
    return method.invoke(verifier,manifest,ctor.newInstance(values));
  }
  public static void main(String[] args) throws Exception {
    byte[] manifest=Files.readAllBytes(Path.of(args[0])),preimage=Files.readAllBytes(Path.of(args[1])),spki=Files.readAllBytes(Path.of(args[2])),signature=Files.readAllBytes(Path.of(args[3]));
    Class<?> codec=Class.forName("io.flooow.marketplace.operations.authorization.ApprovalManifestCanonicalCodec");Object c=codec.getField("INSTANCE").get(null);
    Object decoded=codec.getMethod("decodeCanonicalManifest",byte[].class).invoke(c,(Object)manifest);
    String digest=(String)codec.getMethod("manifestDigest",byte[].class).invoke(c,(Object)manifest),keyfp=HexFormat.of().formatHex(java.security.MessageDigest.getInstance("SHA-256").digest(spki));
    UUID key=UUID.fromString(args[4]),authority=UUID.fromString(args[5]);Instant verified=Instant.parse(args[6]);
    Class<?> proofClass=Class.forName("io.flooow.marketplace.operations.authorization.AcceptedAttestationProof");
    Constructor<?> proofCtor=Arrays.stream(proofClass.getDeclaredConstructors()).filter(x->x.getParameterCount()==16).findFirst().orElseThrow();proofCtor.setAccessible(true);
    Object proof=proofCtor.newInstance(1,1,manifest,digest,preimage,"Ed25519",key,1,keyfp,"c".repeat(64),spki,signature,authority,1,"b".repeat(64),verified);
    Class<?> fingerprintClass=Class.forName("io.flooow.marketplace.operations.authorization.AcceptedAttestationFingerprintCodec");Object fingerprintCodec=fingerprintClass.getField("INSTANCE").get(null);
    String proofFingerprint=(String)fingerprintClass.getMethod("fingerprint",proofClass).invoke(fingerprintCodec,proof);
    Class<?> snapshotClass=Class.forName("io.flooow.marketplace.persistence.postgres.ImmutableAcceptedAttestationSnapshot");Constructor<?> ctor=Arrays.stream(snapshotClass.getDeclaredConstructors()).filter(x->x.getParameterCount()==20).findFirst().orElseThrow();ctor.setAccessible(true);
    Class<?> verifierClass=Class.forName("io.flooow.marketplace.persistence.postgres.ImmutableAcceptedAttestationVerifier");Object verifier=verifierClass.getField("INSTANCE").get(null);Method method=Arrays.stream(verifierClass.getMethods()).filter(x->x.getName().equals("verify")).findFirst().orElseThrow();
    Object[] values={1,1,1,manifest,digest,preimage,"Ed25519",UUID.randomUUID(),key,1,keyfp,"c".repeat(64),spki,signature,authority,1,"b".repeat(64),verified,proofFingerprint,"a".repeat(64)};
    if(verify(decoded,values,ctor,verifier,method)!=null)throw new AssertionError("Original public snapshot rejected");
    System.out.println("snapshot_original=PASS");
    for(int index=0;index<values.length;index++) {
      if(index==7)continue; // Subject is a SQL authority join, outside this verifier boundary.
      Object[] changed=values.clone();Object v=changed[index];
      if(v instanceof Integer)changed[index]=((Integer)v)+1;
      else if(v instanceof byte[]) {byte[] bytes=((byte[])v).clone();bytes[0]^=1;changed[index]=bytes;}
      else if(v instanceof UUID)changed[index]=UUID.randomUUID();
      else if(v instanceof Instant)changed[index]=((Instant)v).plusSeconds(1);
      else changed[index]=((String)v).equals("Ed25519")?"RSA":((String)v).equals("a".repeat(64))?"d".repeat(64):"e".repeat(64);
      if(verify(decoded,changed,ctor,verifier,method)==null)throw new AssertionError("Tamper accepted: "+index);
      System.out.println("snapshot_field_"+index+"_tamper=PASS");
    }
    System.out.println("ASSERTIONS=20");System.out.println("SQL_AUTHORITY_SOURCE_CONSUMPTION_JOINS=NOT_EXECUTED");
  }
}
