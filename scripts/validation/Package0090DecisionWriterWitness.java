// TEST ONLY. Actual current writer/JCA over deterministic mock JDBC transports.
// No connection, production credential or provider request is made.
import io.flooow.ceremony.*;
import io.flooow.marketplace.operations.authorization.*;
import io.flooow.marketplace.operations.identity.*;
import io.flooow.marketplace.persistence.postgres.*;
import java.lang.reflect.*;
import java.nio.file.*;
import java.sql.*;
import java.time.*;
import java.util.*;

class Package0090DecisionWriterWitness {
    static Properties facts=new Properties();
    static Map<String,Object> accepted;
    static final List<Object> applied=new ArrayList<>();
    static String f(int n) { return facts.getProperty("ARG_"+n); }
    static UUID u(int n) { return UUID.fromString(f(n)); }
    static Object proxy(Class<?> type,InvocationHandler h) {
        return Proxy.newProxyInstance(type.getClassLoader(),new Class<?>[]{type},h);
    }
    static Map<Object,Object> row(Object... pairs) {
        var r=new HashMap<Object,Object>();
        for(int i=0;i<pairs.length;i+=2)r.put(pairs[i],pairs[i+1]);
        return r;
    }
    static ResultSet result(Map<?,?> values) {
        int[] cursor={0};
        return (ResultSet)proxy(ResultSet.class,(p,m,a)-> {
            switch(m.getName()) {
                case "next":return values!=null && cursor[0]++==0;
                case "close":return null;
                case "wasNull":return false;
                default:
                    if(m.getName().startsWith("get")) {
                        Object value=values.get(a[0]);
                        if(m.getName().equals("getString"))return value==null?null:value.toString();
                        if(m.getName().equals("getInt"))return value==null?0:((Number)value).intValue();
                        if(m.getName().equals("getLong"))return value==null?0L:((Number)value).longValue();
                        if(m.getName().equals("getBoolean"))return Boolean.TRUE.equals(value);
                        return value;
                    }
                    throw new UnsupportedOperationException(m.getName());
            }
        });
    }
    static Map<?,?> response(String sql,List<Object> arguments) {
        if(sql.contains("command_authorization_organization_lock"))return row(1,true);
        if(sql.contains("FROM command_principal"))return row("mercado_livre_connection_id",u(10),"omie_connection_id",u(3));
        if(sql.contains("FROM command_credential_revision"))return row("revision",1,"state","ENABLED");
        if(sql.contains("FROM command_permission_grant"))return row("organization_id",u(1),"principal_id",u(21),"grant_id",u(24),"revision",1,"permission",f(26),"state","ENABLED","supersedes_grant_id",null,"reason","fixture-grant","provenance","isolated","correlation_id",u(32),"decided_at",accepted.get("verified_at"));
        if(sql.contains("pg_advisory_xact_lock") || sql.contains("transaction_identity_locks"))return row(1,true);
        if(sql.contains("FROM marketplace_transaction_identity_decision") || sql.contains("FROM marketplace_transaction_identity_head"))return null;
        if(sql.contains("FROM marketplace_order_identity_registry"))return row(1,f(14),2,f(15),3,1L,4,0);
        if(sql.contains("FROM integration_omie_transaction_evidence b"))return row("input_progress_version",1L,"record_ordinal",0,"source_integration_ref",f(14),"currency",f(15),"provider_created_local",LocalDateTime.parse(f(20)),"provider_modified_local",null,"source_evidence_semantic_fingerprint",f(19),"semantic_fingerprint_version",1,"record_count",1,"page_complete",true);
        if(sql.contains("s2a_v042_begin_attested_decision_verification")) {
            var r=new HashMap<Object,Object>();
            accepted.forEach((k,v)->r.put("result_"+k,v));
            r.put("result_signature_preimage_bytes",accepted.get("canonical_signature_preimage_bytes"));
            r.put("result_signer_subject_id",new UUID(0,300));
            r.put("result_signed_evidence_binding_fingerprint",f(54));
            r.put("outcome","READY");r.put("result_decision_id",u(2));r.put("result_manifest_id",u(34));
            return r;
        }
        if(sql.contains("s2a_v042_apply_attested_decision")) {
            applied.addAll(arguments);
            return row("outcome","APPLIED","result_decision_id",u(2),"result_decision_semantic_fingerprint",f(30));
        }
        throw new AssertionError("Unrecognized current writer query: "+sql);
    }
    static Connection connection() {
        return (Connection)proxy(Connection.class,(p,m,a)-> {
            switch(m.getName()) {
                case "getAutoCommit":return false;
                case "getTransactionIsolation":return Connection.TRANSACTION_READ_COMMITTED;
                case "prepareStatement":
                    String sql=(String)a[0];var arguments=new ArrayList<Object>();
                    return proxy(PreparedStatement.class,(q,n,b)-> {
                        if(n.getName().startsWith("set")) {
                            int index=(Integer)b[0];while(arguments.size()<index)arguments.add(null);
                            arguments.set(index-1,b[1]);return null;
                        }
                        if(n.getName().equals("close"))return null;
                        if(n.getName().equals("executeQuery"))return result(response(sql,arguments));
                        throw new UnsupportedOperationException(n.getName());
                    });
                default:throw new UnsupportedOperationException(m.getName());
            }
        });
    }
    static String encode(Object value) {
        if(value==null)return "NULL";
        if(value instanceof byte[] bytes)return HexFormat.of().formatHex(bytes);
        if(value instanceof Timestamp timestamp)return timestamp.toInstant().toString();
        return value.toString();
    }
    public static void main(String[] args) throws Exception {
        try(var reader=Files.newBufferedReader(Path.of(args[1]))) { facts.load(reader); }
        var input=OfflineFieldProofInputLoader.INSTANCE.load(Path.of(args[0]));
        var signed=Package0090S02ExpectedAttestationWitness.signed(input.getAttestation().getManifest(),1);
        accepted=Package0090S02ExpectedAttestationWitness.row(signed,1);
        var ctor=Arrays.stream(AuthenticatedCommand.class.getDeclaredConstructors()).filter(c->c.getParameterCount()==6).findFirst().orElseThrow();
        ctor.setAccessible(true);
        var actor=(AuthenticatedCommand)ctor.newInstance(u(1),new CommandPrincipalId(u(21)),u(10),u(3),u(22),1);
        var command=new TransactionIdentityCommand(u(2),f(4),u(5),TransactionIdentityKind.CONFIRMED,ExplicitTransactionIdentityReason.EXPLICIT_CONFIRMATION,f(31),u(32),null);
        Object outcome=new PostgresTransactionIdentityWriter().recordAttested(connection(),actor,command,signed.getManifest());
        if(!(outcome instanceof TransactionIdentityWriteResult.Applied) || applied.size()!=73)throw new AssertionError("Actual writer/JCA did not reach exact73 APPLY vector");
        var lines=new ArrayList<String>();
        for(int i=0;i<applied.size();i++)lines.add("ARG_"+(i+1)+"="+encode(applied.get(i)));
        Files.write(Path.of(args[2]),lines);
    }
}
