import java.nio.file.*;
import java.sql.*;
import java.util.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.*;
import java.lang.reflect.*;
import javax.sql.DataSource;
import org.postgresql.ds.PGSimpleDataSource;
import org.postgresql.PGConnection;
import com.fasterxml.jackson.databind.ObjectMapper;
import io.flooow.ceremony.*;

/** Real driver/Kotlin transactions. No new database capability or eligible readiness. */
public final class Package0090TransportReview {
    static final ObjectMapper JSON=new ObjectMapper();
    static final Map<String,Object> OUT=new LinkedHashMap<>();
    static final List<Map<String,Object>> WRITES=Collections.synchronizedList(new ArrayList<>());
    static final AtomicReference<Map<String,Object>> LATEST=new AtomicReference<>();
    static final AtomicLong SEQ=new AtomicLong();
    static Path output;
    static String incarnation;
    static TracedSource auditor;
    static GovernedSources sources;
    static Connection writer,observer;
    static double us(long n){return n/1000.0;}
    static Map<String,Object> map(Object... a){var r=new LinkedHashMap<String,Object>();for(int i=0;i<a.length;i+=2)r.put((String)a[i],a[i+1]);return r;}
    static void save() throws Exception {OUT.put("writer_commits",new ArrayList<>(WRITES));JSON.writerWithDefaultPrettyPrinter().writeValue(output.toFile(),OUT);}
    static PGSimpleDataSource ds(Properties p,String slot,String url){var d=new PGSimpleDataSource();d.setURL(url+"?connectTimeout=5&socketTimeout=10");d.setUser(p.getProperty(slot+".name"));d.setPassword(p.getProperty(slot+".password"));return d;}
    static final class TracedSource implements DataSource {
        final DataSource delegate; Connection raw; Map<String,Object> trace; List<Map<String,Object>> events;
        TracedSource(DataSource d){delegate=d;}
        public Connection getConnection() throws SQLException {
            trace=map("connection_start_utc",java.time.Instant.now().toString());events=new ArrayList<>();trace.put("events",events);
            long b=System.nanoTime();raw=delegate.getConnection();trace.put("connection_us",us(System.nanoTime()-b));trace.put("connection_end_utc",java.time.Instant.now().toString());trace.put("auditor_backend_pid",((PGConnection)raw).getBackendPID());
            return (Connection)Proxy.newProxyInstance(Connection.class.getClassLoader(),new Class[]{Connection.class},(proxy,m,args)->{
                boolean record=Set.of("setReadOnly","setTransactionIsolation","setAutoCommit","prepareStatement","createStatement","rollback","close").contains(m.getName());
                var e=map("method",m.getName(),"start_utc",java.time.Instant.now().toString());
                if(record&&args!=null&&m.getName().startsWith("set"))e.put("argument",args[0]);
                if(record&&m.getName().equals("prepareStatement"))e.put("sql",args[0]);
                try {return m.invoke(raw,args);}catch(InvocationTargetException x){throw x.getCause();}finally{if(record){e.put("end_utc",java.time.Instant.now().toString());events.add(e);}}
            });
        }
        public Connection getConnection(String u,String p){throw new UnsupportedOperationException();}
        public java.io.PrintWriter getLogWriter() throws SQLException{return delegate.getLogWriter();}
        public void setLogWriter(java.io.PrintWriter p) throws SQLException{delegate.setLogWriter(p);}
        public void setLoginTimeout(int n) throws SQLException{delegate.setLoginTimeout(n);}
        public int getLoginTimeout() throws SQLException{return delegate.getLoginTimeout();}
        public java.util.logging.Logger getParentLogger(){return java.util.logging.Logger.getGlobal();}
        public <T>T unwrap(Class<T> c) throws SQLException{return delegate.unwrap(c);}
        public boolean isWrapperFor(Class<?> c) throws SQLException{return delegate.isWrapperFor(c);}
    }
    static Map<String,Object> update() throws SQLException {
        synchronized(writer){
            Map<String,Object> row;
            try(var s=writer.prepareStatement("UPDATE public.offline_readiness SET watchdog_checked_at=clock_timestamp() WHERE incarnation_id=?::uuid AND state='NOT_READY' AND watchdog_healthy=false RETURNING watchdog_checked_at::text,xmin::text")){
                s.setString(1,incarnation);try(var r=s.executeQuery()){if(!r.next())throw new SQLException("NOT_READY_MARKER_REQUIRED");row=map("sequence",SEQ.incrementAndGet(),"heartbeat",r.getString(1),"xmin",r.getString(2));if(r.next())throw new SQLException("MARKER_CARDINALITY");}
            }
            row.put("commit_ack_utc",java.time.Instant.now().toString());WRITES.add(row);LATEST.set(row);return row;
        }
    }
    static Map<String,Object> activity() throws SQLException {
        try(var s=observer.prepareStatement("SELECT state,backend_xmin::text,xact_start::text,clock_timestamp()::text FROM pg_stat_activity WHERE pid=?")){
            s.setInt(1,((PGConnection)auditor.raw).getBackendPID());try(var r=s.executeQuery()){if(!r.next())throw new SQLException("BACKEND_NOT_OBSERVED");return map("state",r.getString(1),"backend_xmin",r.getString(2),"xact_start",r.getString(3),"observer_db_now",r.getString(4));}
        }
    }
    static Map<String,Object> snapshot() throws SQLException {
        var row=map("first_sql_start_utc",java.time.Instant.now().toString());
        // This is an explicit visibility probe, not the launcher's S01-first transaction.
        try(var s=auditor.raw.createStatement();var r=s.executeQuery("SELECT pg_export_snapshot(),pg_current_snapshot()::text,pg_current_xact_id_if_assigned()::text,clock_timestamp()::text,current_setting('transaction_isolation'),current_setting('transaction_read_only')")){
            r.next();row.put("exported_snapshot",r.getString(1));row.put("snapshot_identity",r.getString(2));row.put("transaction_id_if_assigned",r.getString(3));row.put("snapshot_db_timestamp_upper_bound",r.getString(4));row.put("isolation",r.getString(5));row.put("read_only",r.getString(6));
        }row.put("first_sql_end_utc",java.time.Instant.now().toString());return row;
    }
    static Map<String,Object> imported(Map<String,Object> snap) throws SQLException {
        String token=(String)snap.get("exported_snapshot");if(!token.matches("[a-fA-F0-9-]{1,100}"))throw new SQLException("SNAPSHOT_TOKEN_SHAPE");
        observer.setAutoCommit(false);observer.setTransactionIsolation(Connection.TRANSACTION_REPEATABLE_READ);observer.setReadOnly(true);
        try {
            try(var s=observer.createStatement()){s.execute("SET TRANSACTION SNAPSHOT '"+token+"'");}
            try(var s=observer.prepareStatement("WITH marker AS MATERIALIZED (SELECT watchdog_checked_at,xmin::text AS tuple_xmin FROM public.offline_readiness WHERE incarnation_id=?::uuid), instant AS MATERIALIZED (SELECT clock_timestamp() AS db_now) SELECT marker.watchdog_checked_at::text,marker.tuple_xmin,instant.db_now::text,EXTRACT(EPOCH FROM(instant.db_now-marker.watchdog_checked_at))*1000000 FROM marker CROSS JOIN instant")){
                s.setString(1,incarnation);try(var r=s.executeQuery()){if(!r.next())throw new SQLException("IMPORTED_MARKER_MISSING");return map("visible_heartbeat",r.getString(1),"visible_tuple_xmin",r.getString(2),"db_now_at_surrogate_predicate",r.getString(3),"visible_age_us",r.getDouble(4),"read_authority","EXISTING_POSTGRES_OBSERVER_IMPORTING_AUDITOR_SNAPSHOT");}
            }
        }finally{observer.rollback();observer.setAutoCommit(true);}
    }
    static Map<String,Object> global() throws SQLException {
        try(var s=observer.prepareStatement("SELECT watchdog_checked_at::text,xmin::text,clock_timestamp()::text FROM public.offline_readiness WHERE incarnation_id=?::uuid")){
            s.setString(1,incarnation);try(var r=s.executeQuery()){r.next();return map("heartbeat",r.getString(1),"xmin",r.getString(2),"db_now",r.getString(3));}
        }
    }
    static Map<String,Object> s01(GovernedTransaction tx){
        var result=map("invocation_start_utc",java.time.Instant.now().toString());long b=System.nanoTime();
        try{tx.call(GovernedCall.S01,Package0090RehearsalAdapter.args(GovernedCall.S01));result.put("outcome","UNEXPECTED_SUCCESS");throw new IllegalStateException("UNEXPECTED_S01_SUCCESS");}
        catch(Throwable denied){String state=Package0090RehearsalAdapter.state(denied);result.put("sqlstate",state);if(!"P0017".equals(state))throw new RuntimeException(denied);}
        finally{result.put("denied_call_roundtrip_us",us(System.nanoTime()-b));result.put("invocation_end_utc",java.time.Instant.now().toString());}
        return result;
    }
    static Map<String,Object> sample(boolean frozen,int index){
        Map<String,Object> before=LATEST.get();
        if(frozen)try{before=update();}catch(SQLException x){throw new RuntimeException(x);}
        final var markerBefore=before;
        var result=sources.transaction(GovernedSlot.AUDITOR,tx->{try{
            var snap=snapshot();var visible=imported(snap);var globally=global();
            return map("index",index,"marker_before_connect",markerBefore,"auditor_trace",auditor.trace,"snapshot",snap,"visible",visible,"global_after_import",globally,"s01_unbound_denial",s01(tx));
        }catch(SQLException x){throw new RuntimeException(x);}});
        return result;
    }
    static void edge() throws Exception {
        var a=update();var edge=new LinkedHashMap<String,Object>();edge.put("case_A_committed_before_snapshot",a);
        sources.transaction(GovernedSlot.AUDITOR,tx->{try{
            edge.put("after_jdbc_configuration_before_sql",activity());
            try(var s=auditor.raw.createStatement()){s.execute("BEGIN ISOLATION LEVEL REPEATABLE READ READ ONLY");}
            edge.put("after_explicit_begin_before_non_control_sql",activity());
            var snap=snapshot();edge.put("snapshot",snap);edge.put("after_first_non_control_sql",activity());edge.put("case_A_visible",imported(snap));
            var b=update();edge.put("case_B_committed_after_snapshot",b);var snap2=snapshot();edge.put("case_B_same_transaction_snapshot",snap2);edge.put("case_B_visible",imported(snap2));edge.put("trace",auditor.trace);return true;
        }catch(SQLException x){throw new RuntimeException(x);}});
        sources.transaction(GovernedSlot.AUDITOR,tx->{try{var snap=snapshot();edge.put("case_C_new_transaction_snapshot",snap);edge.put("case_C_visible",imported(snap));edge.put("case_C_trace",auditor.trace);return true;}catch(SQLException x){throw new RuntimeException(x);}});
        OUT.put("rr_edge",edge);save();
        if(!((Map<?,?>)edge.get("case_A_visible")).get("visible_tuple_xmin").equals(a.get("xmin")) || !((Map<?,?>)edge.get("case_B_visible")).get("visible_tuple_xmin").equals(a.get("xmin")) || !((Map<?,?>)edge.get("case_C_visible")).get("visible_tuple_xmin").equals(((Map<?,?>)edge.get("case_B_committed_after_snapshot")).get("xmin")))throw new IllegalStateException("RR_EDGE_FAILED");
    }
    public static void main(String[] argv) throws Exception {
        var p=new Properties();try(var r=Files.newBufferedReader(Path.of(argv[0]))){p.load(r);}output=Path.of(argv[1]);incarnation=p.getProperty("incarnation");String url=Package0090RehearsalEndpoint.require(p);
        var slots=new EnumMap<GovernedSlot,DataSource>(GovernedSlot.class);for(var slot:GovernedSlot.values()){var d=ds(p,slot.name(),url);slots.put(slot,slot==GovernedSlot.AUDITOR?(auditor=new TracedSource(d)):d);}sources=new GovernedSources(slots);
        var admin=ds(p,"ADMIN",url);OUT.put("scope","EXPORTED_AUDITOR_RR_SNAPSHOT_WITH_ADMIN_IMPORT; NOT_ELIGIBLE_S01_Q_TIMING");OUT.put("populations",new LinkedHashMap<String,Object>());
        try(var w=admin.getConnection();var o=admin.getConnection()){
            writer=w;observer=o;
            try(var s=observer.createStatement();var r=s.executeQuery("SELECT version(),pg_postmaster_start_time()::text,(SELECT count(*) FROM public.offline_binding_header),(SELECT state FROM public.offline_readiness),(SELECT watchdog_healthy FROM public.offline_readiness)")){r.next();OUT.put("server",map("version",r.getString(1),"postmaster_start",r.getString(2),"binding_count",r.getLong(3),"readiness",r.getString(4),"healthy",r.getBoolean(5)));if(r.getLong(3)!=0||!r.getString(4).equals("NOT_READY")||r.getBoolean(5))throw new IllegalStateException("UNBOUND_UNHEALTHY_REHEARSAL_REQUIRED");}
            edge();var normal=new ArrayList<Map<String,Object>>();
            for(int i=0;i<10;i++)normal.add(sources.transaction(GovernedSlot.AUDITOR,tx->{try{var b=activity();var denial=s01(tx);return map("before_first_sql",b,"s01",denial,"trace",auditor.trace,"after_failed_s01_before_rollback",activity());}catch(SQLException x){throw new RuntimeException(x);}}));OUT.put("production_s01_first_probes",normal);save();
            var populations=(Map<String,Object>)OUT.get("populations");
            var frozen=new ArrayList<Map<String,Object>>();populations.put("frozen",frozen);
            for(int i=0;i<1000;i++){frozen.add(sample(true,i));if(i%100==99)save();}save();System.out.println("FROZEN=1000");
            for(int cadence:new int[]{5,10,25,50}){
                var samples=new ArrayList<Map<String,Object>>();populations.put("continuous_"+cadence+"ms",samples);var failures=new AtomicReference<Throwable>();update();
                var executor=Executors.newSingleThreadScheduledExecutor();executor.scheduleWithFixedDelay(()->{try{update();}catch(Throwable x){failures.compareAndSet(null,x);}},0,cadence,TimeUnit.MILLISECONDS);
                try{for(int i=0;i<1000;i++){if(failures.get()!=null)throw new RuntimeException(failures.get());samples.add(sample(false,i));if(i%100==99)save();}}
                finally{executor.shutdown();if(!executor.awaitTermination(15,TimeUnit.SECONDS))throw new IllegalStateException("WRITER_NOT_STOPPED");}
                if(failures.get()!=null)throw new RuntimeException(failures.get());save();System.out.println("CONTINUOUS_"+cadence+"ms=1000");
            }
            OUT.put("completed",true);save();
        }catch(Throwable x){OUT.put("failure",Package0090TimingForensics.exception(x,new HashSet<>()));save();throw x;}
    }
}
