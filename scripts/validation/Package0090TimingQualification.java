import java.math.BigDecimal;
import java.nio.file.*;
import java.sql.*;
import java.util.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.*;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.postgresql.ds.PGSimpleDataSource;
import io.flooow.ceremony.*;

/** DB-clock transport qualification, not a substitute for positive S01 readiness. */
public final class Package0090TimingQualification {
    static final int WARM_COUNT=1000, COLD_COUNT=100, LOAD_COUNT=1000;
    static final long WORKLOAD_DELAY_MS=10;
    final Properties config;
    final String url;
    final UUID incarnation;
    final AtomicReference<Throwable> backgroundFailure=new AtomicReference<>();
    final Map<String,Object> result=new LinkedHashMap<>();
    Package0090TimingQualification(Properties p) throws Exception {
        config=p;url=Package0090RehearsalEndpoint.require(p);
        incarnation=UUID.fromString(p.getProperty("incarnation"));
    }
    PGSimpleDataSource source(String identity) {
        var ds=new PGSimpleDataSource();ds.setURL(url);ds.setUser(config.getProperty(identity+".name"));
        ds.setPassword(config.getProperty(identity+".password"));ds.setConnectTimeout(5);ds.setSocketTimeout(10);
        return ds;
    }
    Connection auditor() throws Exception {
        var c=source("AUDITOR").getConnection();
        c.setAutoCommit(false);c.setTransactionIsolation(Connection.TRANSACTION_REPEATABLE_READ);c.setReadOnly(true);
        return c;
    }
    static String sqlstate(Throwable t) {
        for(var q=t;q!=null;q=q.getCause())if(q instanceof SQLException s)return s.getSQLState();
        return "LOCAL_"+t.getClass().getSimpleName();
    }
    record Heartbeat(String timestamp,int backend) {}
    Heartbeat heartbeat(Connection admin) throws Exception {
        try(var s=admin.prepareStatement("UPDATE public.offline_readiness SET watchdog_checked_at=clock_timestamp() WHERE incarnation_id=? AND state='NOT_READY' AND NOT watchdog_healthy RETURNING watchdog_checked_at::text,pg_backend_pid()")) {
            s.setObject(1,incarnation);
            try(var r=s.executeQuery()) {
                if(!r.next())throw new IllegalStateException("INELIGIBLE_TIMING_ROW_REQUIRED");
                var stamp=new Heartbeat(r.getString(1),r.getInt(2));if(r.next())throw new IllegalStateException("CARDINALITY");return stamp;
            }
        }
    }
    Map<String,Object> read(Connection audit,Heartbeat heartbeat,int index) throws Exception {
        try(var s=audit.prepareStatement("SELECT EXTRACT(EPOCH FROM(clock_timestamp()-?::timestamptz))*1000000,pg_backend_pid(),current_setting('transaction_isolation'),current_setting('transaction_read_only')")) {
            s.setString(1,heartbeat.timestamp());
            try(var rows=s.executeQuery()) {
                if(!rows.next())throw new IllegalStateException("TIMING_CARDINALITY");
                BigDecimal age=rows.getBigDecimal(1);int auditorPid=rows.getInt(2);
                if(age.signum()<0)throw new IllegalStateException("DATABASE_CLOCK_ANOMALY");
                if(auditorPid==heartbeat.backend())throw new IllegalStateException("PHYSICAL_SESSION_REUSE");
                if(!rows.getString(3).equals("repeatable read") || !rows.getString(4).equals("on"))throw new IllegalStateException("AUDITOR_TRANSACTION_SETTINGS");
                return Map.of("index",index,"age_us",age,"admin_backend",heartbeat.backend(),"auditor_backend",auditorPid);
            }
        } finally {audit.rollback();}
    }
    void warm(Connection admin,Connection audit) throws Exception {
        for(int i=0;i<10;i++)read(audit,heartbeat(admin),-1);
    }
    final class Load implements AutoCloseable {
        final ScheduledThreadPoolExecutor executor;
        final List<Connection> connections=new ArrayList<>();
        final List<ScheduledFuture<?>> futures=new ArrayList<>();
        final LongAdder calls=new LongAdder();
        final CountDownLatch ready;
        final List<Map<String,Object>> identities=new ArrayList<>();
        Load(int count) throws Exception {
            executor=new ScheduledThreadPoolExecutor(count);ready=new CountDownLatch(count);
            try {
                for(int i=0;i<count;i++) {
                    var slot=GovernedSlot.values()[i%4];
                    var call=switch(slot){case AUDITOR->GovernedCall.S02;case VERIFIER->GovernedCall.S05;case ISSUER->GovernedCall.S07;case EXECUTOR->GovernedCall.S13;};
                    var c=source(slot.name()).getConnection();connections.add(c);c.setAutoCommit(false);
                    c.setTransactionIsolation(slot==GovernedSlot.AUDITOR?Connection.TRANSACTION_REPEATABLE_READ:Connection.TRANSACTION_READ_COMMITTED);
                    c.setReadOnly(slot==GovernedSlot.AUDITOR);
                    try(var s=c.createStatement();var rows=s.executeQuery("SELECT pg_backend_pid(),session_user")) {
                        rows.next();identities.add(Map.of("slot",slot.name(),"backend",rows.getInt(1),"session_user",rows.getString(2)));
                    }c.rollback();
                    var first=new AtomicBoolean(true);
                    futures.add(executor.scheduleWithFixedDelay(()-> {
                        var tx=new GovernedTransaction(c,slot);
                        try {
                            tx.call(call,Package0090RehearsalAdapter.args(call));
                            backgroundFailure.compareAndSet(null,new IllegalStateException("UNEXPECTED_SCOPE_SUCCESS"));
                        } catch(Throwable failure) {
                            if(!"P0017".equals(sqlstate(failure)))backgroundFailure.compareAndSet(null,failure);
                        } finally {
                            tx.close();try {c.rollback();}catch(Throwable failure){backgroundFailure.compareAndSet(null,failure);}
                            calls.increment();if(first.getAndSet(false))ready.countDown();
                        }
                    },0,WORKLOAD_DELAY_MS,TimeUnit.MILLISECONDS));
                }
                if(!ready.await(15,TimeUnit.SECONDS))throw new IllegalStateException("WORKLOAD_START_TIMEOUT");
                if(backgroundFailure.get()!=null)throw new IllegalStateException("WORKLOAD_FAILURE",backgroundFailure.get());
            } catch(Exception failed) {close();throw failed;}
        }
        public void close() throws Exception {
            for(var f:futures)f.cancel(false);executor.shutdown();
            if(!executor.awaitTermination(15,TimeUnit.SECONDS)){executor.shutdownNow();throw new IllegalStateException("WORKLOAD_DRAIN_TIMEOUT");}
            for(var c:connections)c.close();
        }
    }
    void population(String name,int count,boolean cold,int concurrent) throws Exception {
        System.out.println("START_POPULATION="+name);System.out.flush();
        var samples=new ArrayList<Map<String,Object>>();var population=new LinkedHashMap<String,Object>();
        population.put("samples",samples);population.put("requested_count",count);population.put("concurrent_governed_sessions",concurrent);
        ((Map<String,Object>)result.get("populations")).put(name,population);
        long start=System.nanoTime();Load load=null;
        try {
            if(concurrent>0)load=new Load(concurrent);
            if(cold) {
                for(int i=0;i<count;i++) {
                    try(var admin=source("ADMIN").getConnection()) {
                        var stamp=heartbeat(admin);
                        // Reconnection and JDBC setup deliberately occur after the DB heartbeat.
                        try(var audit=auditor()){samples.add(read(audit,stamp,i));}
                    }
                }
            } else {
                try(var admin=source("ADMIN").getConnection();var audit=auditor()) {
                    warm(admin,audit);
                    for(int i=0;i<count;i++) {
                        if(backgroundFailure.get()!=null)throw new IllegalStateException("WORKLOAD_FAILURE",backgroundFailure.get());
                        samples.add(read(audit,heartbeat(admin),i));
                    }
                }
            }
            population.put("status","COMPLETE");
        } finally {
            if(load!=null){load.close();population.put("background_wrapper_calls",load.calls.sum());population.put("background_sessions",load.identities);}
            population.put("duration_seconds",(System.nanoTime()-start)/1e9);
        }
        System.out.println("COMPLETE_POPULATION="+name+"; SUCCESSFUL_SAMPLES="+samples.size());System.out.flush();
    }
    void run() throws Exception {
        result.put("populations",new LinkedHashMap<String,Object>());
        try(var admin=source("ADMIN").getConnection()) {
            var meta=admin.getMetaData();var info=new LinkedHashMap<String,Object>();
            info.put("jdbc_driver_name",meta.getDriverName());info.put("jdbc_driver_version",meta.getDriverVersion());
            info.put("postgres_version",meta.getDatabaseProductVersion());
            info.put("jvm_version",System.getProperty("java.version"));info.put("jvm_vendor",System.getProperty("java.vendor"));
            info.put("host_os",System.getProperty("os.name"));info.put("host_os_version",System.getProperty("os.version"));info.put("host_architecture",System.getProperty("os.arch"));
            info.put("admin_autocommit",admin.getAutoCommit());info.put("admin_isolation",admin.getTransactionIsolation());
            info.put("auditor_autocommit",false);info.put("auditor_isolation","REPEATABLE_READ");info.put("auditor_read_only",true);
            info.put("pool","PGSimpleDataSource; no recording/fake JDBC; persistent physical sessions within each warm/load population; new ADMIN and AUDITOR physical sessions per cold sample");
            info.put("network_path","Windows JVM -> dynamically rediscovered 127.0.0.1 mapped port -> Docker Desktop Linux PostgreSQL");
            info.put("connect_timeout_seconds",5);info.put("socket_timeout_seconds",10);info.put("load_delay_after_completed_call_ms",WORKLOAD_DELAY_MS);
            info.put("load_scope","Actual Kotlin GovernedTransaction, four service identities; S02/S05/S07/S13 nonexistent-scope P0017 denials. This is representative transport/guard traffic, not positive full catalog/frozen-domain load.");
            info.put("background_sessions_are_additional_to_measurement_pair",true);
            result.put("configuration",info);
            if(!meta.getDatabaseProductVersion().startsWith("18.4"))throw new IllegalStateException("POSTGRES_VERSION_MISMATCH");
        }
        population("idle_warm",WARM_COUNT,false,0);
        population("cold_reconnect",COLD_COUNT,true,0);
        population("load4",LOAD_COUNT,false,4);
        population("load8",LOAD_COUNT,false,8);
        result.put("transport_status","PASS_BOUNDED_MEASUREMENT_ONLY");
    }
    public static void main(String[] args) throws Exception {
        var properties=new Properties();try(var reader=Files.newBufferedReader(Path.of(args[0]))){properties.load(reader);}
        var study=new Package0090TimingQualification(properties);
        int exit=0;
        try {study.run();}
        catch(Throwable failure){study.result.put("transport_status","STOP_FAILURE_OR_CLOCK_ANOMALY");study.result.put("failure_sqlstate",sqlstate(failure));study.result.put("failure_class",failure.getClass().getSimpleName());exit=1;}
        new ObjectMapper().writerWithDefaultPrettyPrinter().writeValue(Path.of(args[1]).toFile(),study.result);
        if(exit!=0)System.exit(exit);
    }
}
