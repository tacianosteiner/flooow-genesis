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
public final class Package0090TimingForensics {
    static final int WARM_COUNT=2000, COLD_COUNT=500, LOAD_COUNT=5000;
    static final long WORKLOAD_DELAY_MS=10;
    final Properties config;
    final String url;
    final UUID incarnation;
    final AtomicReference<Throwable> backgroundFailure=new AtomicReference<>();
    final AtomicReference<Map<String,Object>> backgroundContext=new AtomicReference<>();
    final Map<String,Object> result=new LinkedHashMap<>();
    Package0090TimingForensics(Properties p) throws Exception {
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
        long begin=System.nanoTime();Throwable primary=null;
        try(var s=audit.prepareStatement("SELECT EXTRACT(EPOCH FROM(clock_timestamp()-?::timestamptz))*1000000,pg_backend_pid(),current_setting('transaction_isolation'),current_setting('transaction_read_only'),clock_timestamp()::text")) {
            s.setString(1,heartbeat.timestamp());
            try(var rows=s.executeQuery()) {
                if(!rows.next())throw new IllegalStateException("TIMING_CARDINALITY");
                BigDecimal age=rows.getBigDecimal(1);int pid=rows.getInt(2);
                if(age.signum()<0 || pid==heartbeat.backend())throw new IllegalStateException("CLOCK_OR_PHYSICAL_SESSION_INVALID");
                if(!rows.getString(3).equals("repeatable read") || !rows.getString(4).equals("on"))throw new IllegalStateException("AUDITOR_TRANSACTION_SETTINGS");
                var m=new LinkedHashMap<String,Object>();
                m.put("index",index);m.put("age_us",age);m.put("total_authoritative_age_us",age);
                m.put("admin_backend",heartbeat.backend());m.put("auditor_backend",pid);
                m.put("heartbeat_db_timestamp",heartbeat.timestamp());m.put("observation_db_timestamp",rows.getString(5));
                m.put("query_execution_us",(System.nanoTime()-begin)/1000.0);return m;
            }
        } catch(Exception failure){primary=failure;throw failure;}
        finally {try{audit.rollback();}catch(Exception rollback){if(primary!=null)primary.addSuppressed(rollback);else throw rollback;}}
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
                    var c=source(slot.name()).getConnection();final long backgroundBorn=System.nanoTime();connections.add(c);c.setAutoCommit(false);
                    c.setTransactionIsolation(slot==GovernedSlot.AUDITOR?Connection.TRANSACTION_REPEATABLE_READ:Connection.TRANSACTION_READ_COMMITTED);
                    c.setReadOnly(slot==GovernedSlot.AUDITOR);
                    try(var s=c.createStatement();var rows=s.executeQuery("SELECT pg_backend_pid(),session_user")) {
                        rows.next();identities.add(Map.of("slot",slot.name(),"backend",rows.getInt(1),"session_user",rows.getString(2)));
                    }c.rollback();
                    final int backgroundPid=c.unwrap(org.postgresql.PGConnection.class).getBackendPID();
                    var first=new AtomicBoolean(true);
                    futures.add(executor.scheduleWithFixedDelay(()-> {
                        if(backgroundFailure.get()!=null)return;
                        var tx=new GovernedTransaction(c,slot);
                        try {
                            tx.call(call,Package0090RehearsalAdapter.args(call));
                            backgroundFailure.compareAndSet(null,new IllegalStateException("UNEXPECTED_SCOPE_SUCCESS"));
                        } catch(Throwable failure) {
                            if(!"P0017".equals(sqlstate(failure))){backgroundContext.compareAndSet(null,Map.of("slot",slot.name(),"backend",backgroundPid,"connection_lifetime_us",(System.nanoTime()-backgroundBorn)/1000.0,"timestamp_utc",java.time.Instant.now().toString()));backgroundFailure.compareAndSet(null,failure);}
                        } finally {
                            tx.close();try {c.rollback();}catch(Throwable failure){backgroundFailure.compareAndSet(null,failure);}
                            calls.increment();if(first.getAndSet(false))ready.countDown();
                        }
                    },0,WORKLOAD_DELAY_MS,TimeUnit.MILLISECONDS));
                }
                if(!ready.await(15,TimeUnit.SECONDS))throw new IllegalStateException("WORKLOAD_START_TIMEOUT");
                if(backgroundFailure.get()!=null)throw new IllegalStateException("WORKLOAD_FAILURE",backgroundFailure.get());
            } catch(Exception failed) {try{close();}catch(Exception cleanup){failed.addSuppressed(cleanup);}throw failed;}
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
    final Map<Connection,Long> births=new IdentityHashMap<>();
    final Map<Connection,Integer> pids=new IdentityHashMap<>();
    final List<Map<String,Object>> failures=new ArrayList<>();
    final Map<String,Object> populations=new LinkedHashMap<>();
    Connection connect(String slot) throws Exception {
        var c=source(slot).getConnection();births.put(c,System.nanoTime());return c;
    }
    int pid(Connection c) throws Exception {
        int p=c.unwrap(org.postgresql.PGConnection.class).getBackendPID();pids.put(c,p);return p;
    }
    Connection openAudit(Map<String,Object> phases) throws Exception {
        long t1=System.nanoTime();var c=connect("AUDITOR");long t2=System.nanoTime();
        try {
            int backend=pid(c);long t3=System.nanoTime();
            c.setAutoCommit(false);c.setTransactionIsolation(Connection.TRANSACTION_REPEATABLE_READ);c.setReadOnly(true);long t4=System.nanoTime();
            phases.put("connect_start_mono_ns",t1);phases.put("setup_end_mono_ns",t4);
            phases.put("jdbc_connect_us",(t2-t1)/1000.0);phases.put("authentication_and_backend_us",(t3-t2)/1000.0);
            phases.put("session_setup_us",(t4-t3)/1000.0);phases.put("auditor_backend",backend);
            return c;
        } catch(Exception e){try{c.close();}catch(Exception x){e.addSuppressed(x);}throw e;}
    }
    Map<String,Object> telemetry() {
        var m=new LinkedHashMap<String,Object>();var gc=new ArrayList<Map<String,Object>>();
        for(var b:java.lang.management.ManagementFactory.getGarbageCollectorMXBeans())gc.add(Map.of("name",b.getName(),"collections",b.getCollectionCount(),"collection_time_ms",b.getCollectionTime()));
        m.put("gc",gc);m.put("monotonic_ns",System.nanoTime());m.put("timestamp_utc",java.time.Instant.now().toString());
        var cpu=ProcessHandle.current().info().totalCpuDuration();
        m.put("process_cpu_time_ns",cpu.isPresent()?cpu.get().toNanos():null);
        m.put("process_cpu_snapshot_source","ProcessHandle totalCpuDuration; no native CPU load/performance-counter getter");
        m.put("thread_interrupted",Thread.currentThread().isInterrupted());return m;
    }
    Object serverSnapshot(Connection admin) throws Exception {
        String query="SELECT json_build_object('database_timestamp',clock_timestamp(),'postmaster_start',pg_postmaster_start_time(),'sessions',(SELECT json_agg(json_build_object('pid',pid,'user',usename,'state',state,'wait_event_type',wait_event_type,'wait_event',wait_event,'xact_start',xact_start,'backend_start',backend_start,'query_start',query_start,'state_change',state_change,'backend_type',backend_type,'query',query) ORDER BY pid) FROM pg_stat_activity WHERE datname=current_database()))";
        try(var st=admin.createStatement();var rows=st.executeQuery(query)){rows.next();return new ObjectMapper().readValue(rows.getString(1),Object.class);}
    }
    static Map<String,Object> exception(Throwable t,Set<Throwable> seen) {
        var m=new LinkedHashMap<String,Object>();if(t==null)return m;
        if(!seen.add(t)){m.put("cycle",true);return m;}
        m.put("class",t.getClass().getName());m.put("message",t.getMessage());
        if(t instanceof SQLException e){m.put("sqlstate",e.getSQLState());m.put("vendor_error_code",e.getErrorCode());if(e.getNextException()!=null)m.put("nextException",exception(e.getNextException(),seen));}
        if(t.getCause()!=null)m.put("cause",exception(t.getCause(),seen));
        var suppressed=new ArrayList<Map<String,Object>>();for(var q:t.getSuppressed())suppressed.add(exception(q,seen));m.put("suppressed",suppressed);
        var stack=new ArrayList<String>();for(var f:t.getStackTrace())stack.add(f.toString());m.put("stack",stack);return m;
    }
    void captureFailure(Throwable e,String population,int index,Connection admin,Connection audit,Object before,long begin,long last) {
        var m=new LinkedHashMap<String,Object>();m.put("population",population);m.put("index",index);m.put("telemetry",telemetry());
        m.put("exception",exception(e,Collections.newSetFromMap(new IdentityHashMap<>())));m.put("server_before",before);
        m.put("elapsed_iteration_us",(System.nanoTime()-begin)/1000.0);m.put("connection_idle_before_iteration_us",(begin-last)/1000.0);
        if(audit!=null){m.put("known_auditor_pid",pids.get(audit));m.put("auditor_lifetime_us",(System.nanoTime()-births.getOrDefault(audit,System.nanoTime()))/1000.0);try{m.put("auditor_closed_before_harness_cleanup",audit.isClosed());}catch(Exception x){m.put("is_closed_error",exception(x,Collections.newSetFromMap(new IdentityHashMap<>())));}}
        try{if(admin!=null)m.put("server_after",serverSnapshot(admin));}catch(Exception x){m.put("server_after_failure",exception(x,Collections.newSetFromMap(new IdentityHashMap<>())));}
        if(backgroundFailure.get()!=null)m.put("background_exception",exception(backgroundFailure.get(),Collections.newSetFromMap(new IdentityHashMap<>())));
        if(backgroundContext.get()!=null)m.put("background_context",backgroundContext.get());
        failures.add(m);
    }
    void diagnostic(String name,int count,int mode,int concurrent) throws Exception {
        System.out.println("START_DIAGNOSTIC="+name);System.out.flush();
        var samples=new ArrayList<Map<String,Object>>();var pop=new LinkedHashMap<String,Object>();pop.put("samples",samples);pop.put("requested_count",count);pop.put("mode",mode);
        populations.put(name,pop);checkpoint();Load load=null;Connection admin=null,audit=null;Object before=null;long last=System.nanoTime();
        try {
            if(concurrent>0)load=new Load(concurrent);
            if(mode!=3)admin=connect("ADMIN");
            if(mode==0 || mode==4)audit=openAudit(new LinkedHashMap<>());
            for(int i=0;i<count;i++) {
                long begin=System.nanoTime();var phases=new LinkedHashMap<String,Object>();var beforeTelemetry=telemetry();
                try {
                    if(backgroundFailure.get()!=null)throw new IllegalStateException("WORKLOAD_FAILURE",backgroundFailure.get());
                    if(mode==3)admin=connect("ADMIN");
                    if(mode==2 || mode==3)audit=openAudit(phases);
                    if(concurrent>0)before=serverSnapshot(admin);
                    Heartbeat stamp=heartbeat(admin);pids.put(admin,stamp.backend());long commitAck=System.nanoTime();
                    if(mode==1)audit=openAudit(phases);
                    long queryBegin=System.nanoTime();var sample=read(audit,stamp,i);
                    sample.putAll(phases);sample.put("heartbeat_commit_ack_mono_ns",commitAck);sample.put("query_begin_mono_ns",queryBegin);
                    sample.put("heartbeat_to_connect_start_us",mode==1?(((Number)phases.get("connect_start_mono_ns")).longValue()-commitAck)/1000.0:null);
                    sample.put("reconnect_phase_inside_freshness_interval",mode==1);
                    sample.put("pre_query_gap_us",(queryBegin-Math.max(commitAck,((Number)phases.getOrDefault("setup_end_mono_ns",commitAck)).longValue()))/1000.0);
                    for(String k:List.of("jdbc_connect_us","authentication_and_backend_us","session_setup_us"))sample.putIfAbsent(k,0.0);
                    sample.put("telemetry_before",beforeTelemetry);sample.put("telemetry_after",telemetry());
                    sample.put("auditor_lifetime_us",(System.nanoTime()-births.get(audit))/1000.0);
                    sample.put("idle_since_previous_iteration_us",(begin-last)/1000.0);
                    double age=((BigDecimal)sample.get("age_us")).doubleValue();
                    if(age>50000) {
                        sample.put("thresholds_exceeded",List.of(age>50000,age>100000,age>200000));sample.put("server_after_outlier",serverSnapshot(admin));sample.put("server_before",before);
                    }
                    samples.add(sample);if(samples.size()%100==0)checkpoint();
                    if(mode==1 || mode==2 || mode==3){audit.close();audit=null;}
                    if(mode==3){admin.close();admin=null;}
                    last=System.nanoTime();
                } catch(Throwable e){captureFailure(e,name,i,admin,audit,before,begin,last);pop.put("status","STOP_FIRST_FAILURE");return;}
            }
            pop.put("status","COMPLETE_NO_FAILURE");
        } finally {
            if(audit!=null)try{audit.close();}catch(Exception e){failures.add(Map.of("cleanup_exception",exception(e,Collections.newSetFromMap(new IdentityHashMap<>()))));}
            if(admin!=null)try{admin.close();}catch(Exception e){failures.add(Map.of("cleanup_exception",exception(e,Collections.newSetFromMap(new IdentityHashMap<>()))));}
            if(load!=null){try{load.close();}catch(Exception e){failures.add(Map.of("load_cleanup_exception",exception(e,Collections.newSetFromMap(new IdentityHashMap<>()))));}pop.put("background_wrapper_attempts",load.calls.sum());pop.put("background_sessions",load.identities);}
            checkpoint();
            System.out.println("FINISH_DIAGNOSTIC="+name+";N="+samples.size()+";STATUS="+pop.get("status"));System.out.flush();
        }
    }
    void checkpoint() throws Exception {
        new ObjectMapper().writerWithDefaultPrettyPrinter().writeValue(Path.of(config.getProperty("output.path")).toFile(),result);
    }
    void run() throws Exception {
        result.put("populations",populations);result.put("failures",failures);result.put("diagnosis_only",true);
        result.put("phase_limitations","JDBC getConnection includes TCP/protocol/authentication; no distinct TCP-established event is exposed. authentication_and_backend_us measures only a local driver backend PID lookup; authentication is included in jdbc_connect_us and its actual server-side duration is separately correlated from PG18 setup_durations logs. Session setters may be lazy; first freshness query includes BEGIN/SET work. Heartbeat_to_connect_start is relative to local commit acknowledgment, not an invented DB/client clock subtraction. Query timer includes network/driver/result decoding, not server-only execution.");
        result.put("sampling","A2000 B500 C500 D500 E1000; B also supplies Section4 cold diagnostic N500. No fixture-bound PASS/FAIL or positive wrapper invocation.");
        diagnostic("A_warm_persistent",2000,0,0);
        diagnostic("B_cold_after_heartbeat",500,1,0);
        diagnostic("C_cold_before_heartbeat",500,2,0);
        diagnostic("D_both_setup_before_heartbeat",500,3,0);
        diagnostic("E_idle_physical_reuse",1000,4,0);
        diagnostic("load4_diagnostic",5000,0,4);
    }
    public static void main(String[] args) throws Exception {
        var properties=new Properties();try(var reader=Files.newBufferedReader(Path.of(args[0]))){properties.load(reader);}
        properties.setProperty("output.path",args[1]);
        var study=new Package0090TimingForensics(properties);
        try{study.run();}catch(Throwable t){study.result.put("run_failure",study.exception(t,Collections.newSetFromMap(new IdentityHashMap<>())));}
        new ObjectMapper().writerWithDefaultPrettyPrinter().writeValue(Path.of(args[1]).toFile(),study.result);
    }
}
