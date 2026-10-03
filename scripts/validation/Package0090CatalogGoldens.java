// TEST ONLY independent typed catalog projection, history and HMAC construction.
import java.io.*;
import java.nio.file.*;
import java.util.*;
import java.util.regex.*;
import javax.crypto.Mac;
import javax.crypto.spec.SecretKeySpec;

class Package0090CatalogGoldens {
    static byte[] utf(String s) throws Exception { return Package0090EvidenceFixture.utf(s); }
    static byte[] num(long n,int size) throws Exception { return Package0090EvidenceFixture.number(n,size); }
    static byte[] u8(int n) { return new byte[]{(byte)n}; }
    static byte[] ref(String s) throws Exception {
        if(s==null) return u8(0);
        var b=new ByteArrayOutputStream(); var o=new DataOutputStream(b); byte[] t=utf(s);
        o.writeByte(1); o.writeInt(t.length); o.write(t); return b.toByteArray();
    }
    static byte[] coll(List<byte[]> values,boolean set) throws Exception {
        var rows=new ArrayList<>(values);
        if(set) {
            rows.sort(Arrays::compareUnsigned);
            for(int i=1;i<rows.size();i++) if(Arrays.equals(rows.get(i-1),rows.get(i))) throw new IllegalArgumentException("Duplicate");
        }
        var b=new ByteArrayOutputStream(); var o=new DataOutputStream(b); o.writeInt(rows.size());
        for(byte[] r:rows) { o.writeInt(r.length); o.write(r); } return b.toByteArray();
    }
    static byte[] strings(List<String> strings) throws Exception {
        var v=new ArrayList<byte[]>(); for(String s:strings) v.add(utf(s)); return coll(v,false);
    }
    static byte[] row(String kind,Object... values) throws Exception {
        var b=new ByteArrayOutputStream(); var o=new DataOutputStream(b);
        byte[] domain=utf("FLOOOW/OFFLINE-FIELD-PROOF/"+kind+"/V1");
        o.writeInt(domain.length); o.write(domain); o.writeShort(values.length);
        for(int i=0;i<values.length;i++) {
            Object v=values[i]; byte[] raw=v==null ? new byte[0] : v instanceof String ? utf((String)v)
                : v instanceof Boolean ? u8((Boolean)v ? 1:0) : (byte[])v;
            o.writeShort(i+1); o.writeInt(raw.length+1); o.writeByte(v==null ? 0:1); o.write(raw);
        }
        return b.toByteArray();
    }
    static List<String> roles=new ArrayList<>(Arrays.asList(null,"v","i","e","a","ov","oi","oe","oa","op","oq","oz","admin"));
    static byte[] acl(int fixture) throws Exception {
        var identities=new ArrayList<byte[]>();
        for(int i=1;i<=12;i++) identities.add(row("ACL-IDENTITY",num(i,4),num(100+i,4),ref(roles.get(i)),
            i<=4 || i==12,false,false,false,false,false,false));
        var universe=new ArrayList<>(roles); if(fixture==6) universe.add("intruder");
        String owner=fixture==4 ? "admin":"oa", schema="public",name="fixture_scalar",ret="pg_catalog.bytea",variadic=null;
        int shape=1,vol=2; boolean definer=true,strict=false;
        List<String> inputs=List.of("pg_catalog.uuid"),all=inputs,names=Arrays.asList((String)null);
        List<String> config=List.of("search_path=pg_catalog, pg_temp");
        List<Integer> modes=List.of(1); var outputs=new ArrayList<byte[]>();
        if(fixture==2) {
            name="fixture_table";ret="pg_catalog.record";shape=2;
            List<String> on=List.of("installed_rank","version","type","script","checksum","success");
            List<String> ot=List.of("pg_catalog.int4","pg_catalog.text","pg_catalog.text","pg_catalog.text","pg_catalog.int4","pg_catalog.bool");
            all=new ArrayList<>(inputs);all.addAll(ot);names=new ArrayList<>(names);names.addAll(on);
            modes=List.of(1,5,5,5,5,5,5);
            for(int i=0;i<6;i++) outputs.add(row("ACL-OUTPUT",on.get(i),ot.get(i),u8(5)));
        } else if(fixture==3) {
            name="transaction_identity_hash";inputs=List.of("pg_catalog.text[]");all=inputs;names=List.of("fields");modes=List.of(4);
            ret="pg_catalog.text";vol=1;definer=false;variadic="pg_catalog.text";config=List.of("search_path=pg_catalog, public, pg_temp");
        } else if(fixture==4) {
            schema="offline_crypto";name="hmac";inputs=List.of("pg_catalog.bytea","pg_catalog.bytea","pg_catalog.text");all=inputs;
            modes=List.of(1,1,1);names=Arrays.asList(null,null,null);vol=1;definer=false;strict=true;config=null;
        } else if(fixture==7) config=null;
        var permissions=new ArrayList<byte[]>();
        for(String r:universe) {
            boolean owns=Objects.equals(r,owner);
            boolean effective=owns || Objects.equals(r,fixture==4 ? "oq":"a") || fixture==5 || (fixture==6 && Objects.equals(r,"intruder"));
            permissions.add(row("ACL-EXECUTE",ref(r),u8(1),effective,owns,owns));
        }
        var nm=new ArrayList<byte[]>(); for(String n:names) {
            if(n==null) nm.add(u8(0)); else {var b=new ByteArrayOutputStream();b.write(1);b.write(utf(n));nm.add(b.toByteArray());}
        }
        var md=new ArrayList<byte[]>();for(int m:modes) md.add(u8(m));
        byte[] function=row("ACL-FUNCTION",schema,name,strings(inputs),strings(all),coll(md,false),coll(nm,false),u8(shape),ret,
            coll(outputs,false),u8(vol),definer,ref(owner),config==null ? null:strings(config),num(0,4),variadic,strict,coll(permissions,true));
        var schemas=new ArrayList<byte[]>();
        List<String> objects=fixture==4 ? List.of("public","flooow_fixture","offline_crypto"):List.of("public","flooow_fixture");
        for(String object:objects) {
            int kind=object.equals("flooow_fixture") ? 2:1;
            for(String r:universe) for(int priv:new int[]{kind==1 ? 2:11,3}) {
                boolean owns=Objects.equals(r,"admin");
                boolean direct=owns || ((priv==2 || priv==11) && r!=null && roles.contains(r) && (!object.equals("offline_crypto") || r.equals("oq")))
                    || (fixture==8 && object.equals("public") && priv==3 && r==null);
                boolean effective=direct || (fixture==8 && object.equals("public") && priv==3);
                schemas.add(row("ACL-SCHEMA",u8(kind),object,ref("admin"),ref(r),u8(priv),direct,effective,owns,owns));
            }
        }
        var defaults=new ArrayList<byte[]>();
        List<String> scopes=fixture==4 ? Arrays.asList(null,"public","offline_crypto"):Arrays.asList(null,"public");
        for(String creator:List.of("admin","oa")) for(String scope:scopes) for(int kind=1;kind<=6;kind++)
            defaults.add(row("ACL-DEFAULT",ref(creator),scope,u8(kind),false,ref(null),u8(0),false));
        return row("ACL",coll(identities,true),coll(List.of(function),true),coll(List.of(),true),coll(List.of(),true),
            coll(schemas,true),coll(defaults,true));
    }
    static byte[] history(Path root,boolean nullRow) throws Exception {
        String source=Files.readString(root.resolve("applications/command-authority-ceremony/src/main/kotlin/io/flooow/ceremony/PostgresOfflineMigrationHistory.kt"));
        Matcher m=Pattern.compile("(\\d+) to \\(\"(V\\d+__[^\"]+\\.sql)\" to (-?\\d+)\\)").matcher(source);
        var rows=new TreeMap<Integer,byte[]>();
        while(m.find()) {
            int rank=Integer.parseInt(m.group(1));
            if(rows.put(rank,row("HISTORY-ROW",num(rank,4),m.group(1),"SQL",m.group(2),num(Integer.parseInt(m.group(3)),4),true))!=null)
                throw new IllegalArgumentException("Duplicate history rank");
        }
        if(rows.size()!=42) throw new IllegalStateException("Incomplete history fixture");
        if(nullRow) rows.put(43,row("HISTORY-ROW",num(43,4),null,"BASELINE","fixture-null.sql",null,false));
        return row("HISTORY",coll(new ArrayList<>(rows.values()),false));
    }
    public static void main(String[] args) throws Exception {
        Path root=Path.of(args[0]);byte[] history=history(root,false);
        Package0090EvidenceFixture.emit("HISTORY",history);Package0090EvidenceFixture.emit("NULL_HISTORY",history(root,true));
        for(int n=1;n<=8;n++) Package0090EvidenceFixture.emit("ACL_V1_F"+n,acl(n));
        byte[] evidence=Package0090EvidenceFixture.evidence("order-1");
        byte[] manifest=Package0090EvidenceFixture.manifest("order-1",15,evidence);
        byte[] binding=Package0090EvidenceFixture.binding("order-1",15,manifest,false);
        byte[] preflight=row("PREFLIGHT",Package0090EvidenceFixture.identity(3),Package0090EvidenceFixture.sha(binding),"0090-v1",
            Package0090EvidenceFixture.sha(history),Package0090EvidenceFixture.sha(acl(1)),Package0090EvidenceFixture.sha(Package0090EvidenceFixture.policy()),
            num(1,8),num(1000001,8),num(1,4));
        byte[] key=new byte[32];for(int i=0;i<32;i++) key[i]=(byte)i;
        Mac hmac=Mac.getInstance("HmacSHA256");hmac.init(new SecretKeySpec(key,"HmacSHA256"));byte[] mac=hmac.doFinal(preflight);
        Package0090EvidenceFixture.emit("PREFLIGHT",preflight);
        System.out.println("HMAC_SHA256="+Package0090EvidenceFixture.hex(mac));
        var receipt=new ByteArrayOutputStream();receipt.write(preflight);receipt.write(mac);
        Package0090EvidenceFixture.emit("RECEIPT",receipt.toByteArray());
    }
}
