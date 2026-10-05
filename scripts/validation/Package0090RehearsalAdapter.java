import java.nio.file.*;
import java.sql.*;
import java.time.Instant;
import java.util.*;
import javax.sql.DataSource;
import org.postgresql.ds.PGSimpleDataSource;
import io.flooow.ceremony.*;

/** Calls the actual governed Kotlin adapter and PostgreSQL driver, with four real logins. */
public final class Package0090RehearsalAdapter {
    static Object value(GovernedField f) {
        return switch(f.getType()) {
            case "uuid" -> UUID.randomUUID(); case "bytea" -> new byte[32];
            case "int8" -> 1L; case "int4" -> 1; case "text" -> "0090-v1";
            case "timestamptz" -> Instant.parse("2026-10-05T00:00:00Z");
            default -> throw new IllegalStateException();
        };
    }
    static Map<String,Object> args(GovernedCall call) {
        var a=new LinkedHashMap<String,Object>(); for(var f:call.getFields())a.put(f.getName(),value(f)); return a;
    }
    static String state(Throwable t) {
        for(var q=t;q!=null;q=q.getCause())if(q instanceof SQLException s)return s.getSQLState();
        return "LOCAL_"+t.getClass().getSimpleName();
    }
    static void direct(DataSource ds,GovernedCall call,String label,int nullIndex,boolean malformed) throws Exception {
        try(var c=ds.getConnection()) {
            c.setAutoCommit(false); c.setTransactionIsolation(call.getSlot()==GovernedSlot.AUDITOR?Connection.TRANSACTION_REPEATABLE_READ:Connection.TRANSACTION_READ_COMMITTED);
            c.setReadOnly(call.getSlot()==GovernedSlot.AUDITOR);
            try(var s=c.prepareStatement(call.getSql())) {
                int i=0;for(var f:call.getFields()) {
                    Object v=value(f); if(i==nullIndex)v=null; if(malformed&&f.getType().equals("bytea"))v=new byte[1];
                    if(v instanceof Instant x)v=Timestamp.from(x);
                    s.setObject(++i,v);
                }
                try(var r=s.executeQuery()){System.out.println(call.name()+"|"+label+"|UNEXPECTED_SUCCESS");}
            } catch(SQLException denied){System.out.println(call.name()+"|"+label+"|"+denied.getSQLState());}
            finally {c.rollback();}
        }
    }
    public static void main(String[] argv) throws Exception {
        var p=new Properties();try(var r=Files.newBufferedReader(Path.of(argv[0]))){p.load(r);}
        var url=Package0090RehearsalEndpoint.require(p);
        var map=new EnumMap<GovernedSlot,DataSource>(GovernedSlot.class);
        for(var slot:GovernedSlot.values()) {
            var ds=new PGSimpleDataSource();ds.setURL(url);ds.setUser(p.getProperty(slot.name()+".name"));ds.setPassword(p.getProperty(slot.name()+".password"));map.put(slot,ds);
        }
        var sources=new GovernedSources(map);
        if(argv.length>1 && argv[1].equals("type-probe")) {
            String[] queries={"SELECT ROW(1)::public.g3f4_acl_row_probe", "SELECT * FROM public.g3f4_acl_row_probe", "UPDATE public.g3f4_acl_row_probe SET v=1", "SELECT 'x'::public.g3f4_acl_enum_probe", "CREATE TEMP TABLE g3f4_type_dependency(v public.g3f4_acl_enum_probe)"};
            for(var slot:GovernedSlot.values())for(int i=0;i<queries.length;i++)try(var c=map.get(slot).getConnection()) {
                c.setAutoCommit(false);
                try(var s=c.createStatement()){boolean result=s.execute(queries[i]);String value="";if(result)try(var rows=s.getResultSet()){if(rows.next())value=rows.getString(1);}System.out.println("TYPE_PROBE|"+slot+"|"+i+"|SUCCESS|"+value);}
                catch(SQLException denied){System.out.println("TYPE_PROBE|"+slot+"|"+i+"|"+denied.getSQLState()+"|");}
                finally{c.rollback();}
            }
            return;
        }
        for(var call:GovernedCall.values()) {
            if(call==GovernedCall.S18)continue; // Actual adapter prevents S18 without a successful S17/JCA sequence.
            try {sources.transaction(call.getSlot(), tx->{
                var a=args(call);
                if(call==GovernedCall.S04)return tx.history(a);
                if(call==GovernedCall.S17)return tx.decision(a, envelope->{throw new IllegalStateException("NO_VERIFIED_ARTIFACT");});
                return tx.call(call,a);
            });System.out.println(call.name()+"|ACTUAL_KOTLIN_ADAPTER_NONEXISTENT_SCOPE|UNEXPECTED_SUCCESS");}
            catch(Throwable denied){System.out.println(call.name()+"|ACTUAL_KOTLIN_ADAPTER_NONEXISTENT_SCOPE|"+state(denied));}
        }
        for(var call:GovernedCall.values()) {
            direct(map.get(call.getSlot()),call,"NONEXISTENT_SCOPE",-1,false);
            direct(map.get(call.getSlot()),call,"MALFORMED_BYTEA",-1,true);
            for(int i=0;i<call.getFields().size();i++)direct(map.get(call.getSlot()),call,"NULL_"+call.getFields().get(i).getName(),i,false);
            for(var slot:GovernedSlot.values())if(slot!=call.getSlot())direct(map.get(slot),call,"WRONG_SLOT_"+slot,-1,false);
        }
    }
}
