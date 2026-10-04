// Test-only deterministic inputs; calls the actual frozen Kotlin JCA classes.
import java.security.*;
import java.security.spec.*;
import java.util.*;
import io.flooow.marketplace.operations.authorization.SignerPublicKeyInfo;
import io.flooow.marketplace.operations.authorization.Ed25519ApprovalSignatureVerifier;

class Package0090Ed25519Vectors {
    static final HexFormat HEX = HexFormat.of();
    static final byte[] PREFIX = HEX.parseHex("302a300506032b6570032100");
    static void vector(String name, byte[] key, byte[] message, byte[] signature) {
        String result;
        try {
            var parsed = SignerPublicKeyInfo.Companion.parse(key);
            result = Ed25519ApprovalSignatureVerifier.INSTANCE.verify(parsed, message, signature) ? "true" : "false";
        } catch (IllegalArgumentException failure) { result = "structural_error"; }
        catch (Exception failure) { result = "key_error"; }
        System.out.println(name+"|"+HEX.formatHex(key)+"|"+HEX.formatHex(message)+"|"+HEX.formatHex(signature)+"|"+result);
    }
    static byte[] flip(byte[] bytes) { var out=bytes.clone();out[out.length-1]^=1;return out; }
    public static void main(String[] args) throws Exception {
        // RFC 8032 test key 1: public, deliberately non-production test material.
        var seed = HEX.parseHex("9d61b19deffd5a60ba844af492ec2cc44449c5697b326919703bac031cae7f60");
        var raw = HEX.parseHex("d75a980182b10ab7d54bfed3c964073a0ee172f3daa62325af021a68f707511a");
        var key = new byte[44];System.arraycopy(PREFIX,0,key,0,12);System.arraycopy(raw,0,key,12,32);
        var privateKey=KeyFactory.getInstance("Ed25519").generatePrivate(new EdECPrivateKeySpec(NamedParameterSpec.ED25519,seed));
        var message=HEX.parseHex("00010203ff00464c4f4f4f57");
        var signer=Signature.getInstance("Ed25519");signer.initSign(privateKey);signer.update(message);var signature=signer.sign();
        vector("valid",key,message,signature);
        vector("signature_bit",key,message,flip(signature));
        vector("message_bit",key,flip(message),signature);
        vector("wrong_key",flip(key),message,signature);
        var malformed=key.clone();malformed[0]=0x31;vector("malformed_spki",malformed,message,signature);
        var noncanonical=new byte[45];noncanonical[0]=0x30;noncanonical[1]=(byte)0x81;noncanonical[2]=0x2a;System.arraycopy(key,2,noncanonical,3,42);
        vector("noncanonical_der",noncanonical,message,signature);
        vector("trailing_der",Arrays.copyOf(key,45),message,signature);
        vector("truncated_der",Arrays.copyOf(key,43),message,signature);
        var mismatch=key.clone();mismatch[11]=1;vector("invalid_bit_string",mismatch,message,signature);
        mismatch=key.clone();mismatch[8]=0x6e;vector("x25519_algorithm",mismatch,message,signature);
        vector("empty_signature",key,message,new byte[0]);
        vector("truncated_signature",key,message,Arrays.copyOf(signature,63));
        vector("oversized_signature",key,message,Arrays.copyOf(signature,65));
        vector("altered_preimage",key,Arrays.copyOf(message,message.length+1),signature);
        signer.initSign(privateKey);var emptySignature=signer.sign();
        vector("valid_empty_message",key,new byte[0],emptySignature);
        vector("empty_message_wrong_signature",key,new byte[0],signature);
        // Adversarial encoded points and scalars, beyond the required vectors.
        for(int value:new int[]{0,1,255}) {
            var point=key.clone();Arrays.fill(point,12,44,(byte)value);
            var adversarial=new byte[64];Arrays.fill(adversarial,(byte)value);
            vector("point_scalar_"+value,point,message,adversarial);
        }
        var zeroPoint=key.clone();Arrays.fill(zeroPoint,12,44,(byte)0);
        for(int i=0;i<32;i++)vector("small_order_message_"+i,zeroPoint,new byte[]{(byte)i},new byte[64]);
    }
}
