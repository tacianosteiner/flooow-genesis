// TEST/REHEARSAL ONLY. Independent construction; no Python/JSON golden inputs.
import java.io.*;
import java.nio.charset.*;
import java.security.*;
import java.text.Normalizer;
import java.util.*;

class Package0090EvidenceFixture {
    static final String ML = "marketplace-economic.order-source";
    static final String OMIE = "marketplace-economic.omie-transaction-evidence.reacquisition-v3";
    static final String INSTANT = "1970-01-01T00:00:00.000001Z";
    static byte[] utf(String s) throws Exception {
        if (!Normalizer.isNormalized(s, Normalizer.Form.NFC)) throw new IllegalArgumentException("NFC required");
        var b = StandardCharsets.UTF_8.newEncoder().onMalformedInput(CodingErrorAction.REPORT)
            .onUnmappableCharacter(CodingErrorAction.REPORT).encode(java.nio.CharBuffer.wrap(s));
        byte[] out = new byte[b.remaining()]; b.get(out); return out;
    }
    static String uuid(int n) { return new UUID(0, n).toString(); }
    static byte[] number(long n, int size) throws Exception {
        var b = new ByteArrayOutputStream(); var o = new DataOutputStream(b);
        if (size == 4) o.writeInt((int)n); else o.writeLong(n);
        return b.toByteArray();
    }
    static byte[] identity(int n) throws Exception {
        var b = new ByteArrayOutputStream(); var o = new DataOutputStream(b);
        o.writeLong(0); o.writeLong(n); return b.toByteArray();
    }
    static byte[] sha(byte[] bytes) throws Exception { return MessageDigest.getInstance("SHA-256").digest(bytes); }
    static String hex(byte[] bytes) { return HexFormat.of().formatHex(bytes); }
    static void frozen(DataOutputStream out, String s) throws Exception {
        byte[] raw = utf(s); out.writeInt(raw.length); out.write(raw);
    }
    static byte[] evidence(String source) throws Exception {
        var b = new ByteArrayOutputStream(); var o = new DataOutputStream(b);
        String[] fields = {"FLOOOW:S2A:EVIDENCE-BINDING:1",uuid(6),uuid(10),uuid(8),ML,
            "1","0","mercado-livre","order-1","BRL","PROMOTED",uuid(9),OMIE,"1","0",source,
            "PRESENT","integration-1","PRESENT","BRL","1","0".repeat(63)+"1","1970-01-01T00:00:00.000001"};
        for (String s : fields) frozen(o,s);
        return b.toByteArray();
    }
    static byte[] manifest(String source, int correlation, byte[] evidence) throws Exception {
        var b = new ByteArrayOutputStream(); var o = new DataOutputStream(b);
        String[] fields = {"FLOOOW:S2A:APPROVAL-MANIFEST:1","1",uuid(7),uuid(6),uuid(8),uuid(9),source,
            "integration-1",uuid(10),"TRANSACTION_IDENTITY_DECISION_WRITE",uuid(19),uuid(20),INSTANT,
            "1970-01-01T00:00:01.000001Z",uuid(21),uuid(22),"PROTECTED_TTY_ONE_TIME",uuid(23),
            "SEPARATE_APPROVAL_REQUIRED","reason","fixture",uuid(correlation),hex(sha(evidence))};
        for (String s : fields) frozen(o,s);
        return b.toByteArray();
    }
    static byte[] frame(String domain, List<byte[]> values) throws Exception {
        var b = new ByteArrayOutputStream(); var o = new DataOutputStream(b);
        byte[] d = utf(domain); o.writeInt(d.length); o.write(d); o.writeShort(values.size());
        for (int i=0; i<values.size(); i++) {
            o.writeShort(i+1); o.writeInt(values.get(i).length+1); o.writeByte(1); o.write(values.get(i));
        }
        return b.toByteArray();
    }
    static byte[] policy() throws Exception {
        var values = new ArrayList<byte[]>(); values.add(utf("fixture-1"));
        for (int tag=2; tag<=29; tag++) {
            long n = tag==26 ? 1 : tag==27 ? 2 : tag>=22 && tag<=25 ? (tag%2==0 ? 100 : 200)
                : tag%2==0 ? 1000000 : 2000000;
            values.add(number(n,8));
        }
        return frame("FLOOOW/OFFLINE-FIELD-PROOF/DEADLINE-POLICY/V1",values);
    }
    static byte[] slots(boolean shuffled) throws Exception {
        var records = new ArrayList<byte[]>();
        int[] order = shuffled ? new int[]{4,2,1,3} : new int[]{1,2,3,4};
        for (int p : order) {
            var b = new ByteArrayOutputStream(); var o = new DataOutputStream(b);
            o.writeByte(p); o.writeInt(100+p); byte[] name = utf(new String[]{"v","i","e","a"}[p-1]);
            o.writeInt(name.length); o.write(name); records.add(b.toByteArray());
        }
        records.sort(Arrays::compareUnsigned);
        var b = new ByteArrayOutputStream(); var o = new DataOutputStream(b); o.writeInt(4);
        for (byte[] r : records) { o.writeInt(r.length); o.write(r); }
        return b.toByteArray();
    }
    static byte[] binding(String source, int correlation, byte[] manifest, boolean shuffled) throws Exception {
        var v = new ArrayList<byte[]>(); v.add(number(1,4));
        for (int n=1; n<=5; n++) v.add(identity(n));
        v.add(number(1,4)); v.add(identity(6)); v.add(identity(7));
        v.add(sha(manifest)); v.add(sha(manifest)); v.add(number(1,4));
        for (int n=8; n<=10; n++) v.add(identity(n));
        for (String s : new String[]{source,"integration-1","TRANSACTION_IDENTITY_DECISION_WRITE","reason","fixture"}) v.add(utf(s));
        for (int n : new int[]{11,12,13,14,correlation,16,17,18}) v.add(identity(n));
        for (int n : new int[]{1,1,1000001}) v.add(number(n,8));
        v.add(slots(shuffled)); v.add(utf("0090-v1")); v.add(utf("fixture-1")); v.add(sha(policy()));
        for (int n=0; n<3; n++) v.add(utf("1"));
        if (v.size()!=38) throw new IllegalStateException();
        return frame("FLOOOW/OFFLINE-FIELD-PROOF/BINDING/V1",v);
    }
    static void emit(String name, byte[] raw) throws Exception {
        System.out.println(name+"_HEX="+hex(raw)); System.out.println(name+"_SHA256="+hex(sha(raw)));
    }
    public static void main(String[] args) throws Exception {
        emit("POLICY",policy()); emit("SLOTS",slots(false));
        for (int n=1; n<=3; n++) {
            String source = n==2 ? "caf\u00e9" : "order-1"; int correlation = n==3 ? 999 : 15;
            byte[] ev = evidence(source), m = manifest(source,correlation,ev);
            emit("VECTOR_"+n+"_EVIDENCE",ev); emit("VECTOR_"+n+"_MANIFEST",m);
            emit("VECTOR_"+n+"_BINDING",binding(source,correlation,m,n==2));
        }
        emit("VECTOR_3_ENCODER_ONLY",binding("order-1",999,manifest("order-1",15,evidence("order-1")),false));
        try { evidence("cafe\u0301"); throw new IllegalStateException("NFC negative failed"); }
        catch (IllegalArgumentException expected) { System.out.println("NON_NFC=REJECT"); }
    }
}
