import java.nio.file.*;
import java.util.*;
import org.flywaydb.core.Flyway;

/** Receives disposable connection details through a private file, never command arguments. */
public final class Package0090RehearsalFlyway {
    public static void main(String[] args) throws Exception {
        Properties p = new Properties();
        try (var r = Files.newBufferedReader(Path.of(args[0]))) { p.load(r); }
        String url = Package0090RehearsalEndpoint.require(p);
        try {
            Flyway.configure().dataSource(url, "postgres", p.getProperty("password"))
                .locations("filesystem:" + p.getProperty("migrations"))
                .target(p.getProperty("target")).cleanDisabled(true).load().migrate();
        } catch (Exception failure) {
            for (Throwable t = failure; t != null; t = t.getCause()) {
                if (t instanceof java.sql.SQLException sql)
                    System.err.println("REHEARSAL_SQLSTATE=" + sql.getSQLState());
            }
            throw failure;
        }
    }
}
