import java.nio.file.*;
import java.sql.*;
import java.util.*;

/** Actual JDBC measurement; no fake transport, no policy alteration. */
public final class Package0090RehearsalTiming {
    public static void main(String[] args) throws Exception {
        var p = new Properties();
        try (var r=Files.newBufferedReader(Path.of(args[0]))) {p.load(r);}
        String url=Package0090RehearsalEndpoint.require(p);
        try (var admin=DriverManager.getConnection(url,"postgres",p.getProperty("password"));
             var audit=DriverManager.getConnection(url,p.getProperty("auditor"),p.getProperty("auditor_password"))) {
            audit.setAutoCommit(false); audit.setTransactionIsolation(Connection.TRANSACTION_REPEATABLE_READ); audit.setReadOnly(true);
            // Warm both real physical sessions before recording samples.
            try(var s=admin.createStatement()){s.execute("SELECT 1");}
            try(var s=audit.createStatement()){s.execute("SELECT 1");} audit.rollback();
            for (int i=0;i<40;i++) {
                String stamp;
                try(var s=admin.createStatement();var r=s.executeQuery("UPDATE public.offline_readiness SET watchdog_checked_at=clock_timestamp() RETURNING watchdog_checked_at::text")){if(!r.next())throw new IllegalStateException("READINESS_MISSING"); stamp=r.getString(1);}
                // Exact freshness predicate, timestamp returned by the real administrative update.
                try(var s=audit.prepareStatement("SELECT EXTRACT(EPOCH FROM(clock_timestamp()-?::timestamptz))*1000000, current_setting('transaction_isolation'), current_setting('transaction_read_only')")) {
                    s.setString(1,stamp); try(var r=s.executeQuery()){r.next(); System.out.println(r.getBigDecimal(1).toPlainString()+"|"+r.getString(2)+"|"+r.getString(3));}
                }
                audit.rollback();
            }
        }
    }
}
