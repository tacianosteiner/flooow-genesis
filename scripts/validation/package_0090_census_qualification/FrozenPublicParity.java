// Public material only. No key generation, private key, signing or DB access.
import java.nio.file.*;
import java.lang.reflect.*;
import java.util.*;
public final class FrozenPublicParity {
    public static void main(String[] args) throws Exception {
        byte[] manifest=Files.readAllBytes(Path.of(args[0]));
        byte[] preimage=Files.readAllBytes(Path.of(args[1]));
        byte[] spki=Files.readAllBytes(Path.of(args[2]));
        byte[] signature=Files.readAllBytes(Path.of(args[3]));
        Class<?> codec=Class.forName("io.flooow.marketplace.operations.authorization.ApprovalManifestCanonicalCodec");
        Object instance=codec.getField("INSTANCE").get(null);
        Object decoded=codec.getMethod("decodeCanonicalManifest",byte[].class).invoke(instance,(Object)manifest);
        byte[] encoded=(byte[])codec.getMethod("canonicalManifestBytes",decoded.getClass()).invoke(instance,decoded);
        if(!Arrays.equals(encoded,manifest))throw new AssertionError("Manifest differs");
        String digest=(String)codec.getMethod("manifestDigest",byte[].class).invoke(instance,(Object)manifest);
        String fingerprint=HexFormat.of().formatHex(java.security.MessageDigest.getInstance("SHA-256").digest(spki));
        Method pre=Arrays.stream(codec.getMethods()).filter(m->m.getName().startsWith("canonicalSignaturePreimageBytes-")).findFirst().orElseThrow();
        byte[] expected=(byte[])pre.invoke(instance,"Ed25519",UUID.fromString(args[4]),fingerprint,digest);
        if(!Arrays.equals(expected,preimage))throw new AssertionError("Preimage differs");
        Class<?> publicInfo=Class.forName("io.flooow.marketplace.operations.authorization.SignerPublicKeyInfo");
        Object companion=publicInfo.getField("Companion").get(null);
        Method factory=Arrays.stream(companion.getClass().getMethods()).filter(m->m.getParameterCount()==1&&m.getParameterTypes()[0]==byte[].class&&m.getReturnType()==publicInfo).findFirst().orElseThrow();
        Object info=factory.invoke(companion,(Object)spki);
        Class<?> verifier=Class.forName("io.flooow.marketplace.operations.authorization.Ed25519ApprovalSignatureVerifier");
        Object v=verifier.getField("INSTANCE").get(null);
        Method verify=verifier.getMethod("verify",publicInfo,byte[].class,byte[].class);
        if(!(Boolean)verify.invoke(v,info,preimage,signature))throw new AssertionError("Original signature rejected");
        byte[] bad=signature.clone();bad[0]^=1;
        if((Boolean)verify.invoke(v,info,preimage,bad))throw new AssertionError("Tamper accepted");
        System.out.println("FROZEN_MANIFEST_ROUNDTRIP=PASS");
        System.out.println("FROZEN_PREIMAGE_BYTE_PARITY=PASS");
        System.out.println("FROZEN_ED25519_ORIGINAL=PASS");
        System.out.println("FROZEN_ED25519_TAMPER_DENIED=PASS");
        System.out.println("FULL_ACCEPTED_PROOF_AND_AUTHORITY_VERIFIER=NOT_RUN");
    }
}
