// TEST/REHEARSAL ONLY: independently encode the approved SPEC21.2 policy.
// No database, fixture-file input, deployment defaults or production policy.
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.HexFormat;

class Package0090PolicyFixture {
    public static void main(String[] args) throws Exception {
        var buffer = new ByteArrayOutputStream();
        var out = new DataOutputStream(buffer);
        byte[] domain = "FLOOOW/OFFLINE-FIELD-PROOF/DEADLINE-POLICY/V1".getBytes(StandardCharsets.UTF_8);
        out.writeInt(domain.length); out.write(domain); out.writeShort(29);
        byte[] version = "fixture-1".getBytes(StandardCharsets.UTF_8);
        out.writeShort(1); out.writeInt(1 + version.length); out.writeByte(1); out.write(version);
        for (int tag = 2; tag <= 29; tag++) {
            long value;
            if (tag == 26 || tag == 27) value = tag == 26 ? 1 : 2;
            else if (tag >= 22 && tag <= 25) value = tag % 2 == 0 ? 100 : 200;
            else value = tag % 2 == 0 ? 1000000 : 2000000;
            out.writeShort(tag); out.writeInt(9); out.writeByte(1); out.writeLong(value);
        }
        byte[] bytes = buffer.toByteArray();
        System.out.println(HexFormat.of().formatHex(bytes));
        System.out.println(HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes)));
    }
}
