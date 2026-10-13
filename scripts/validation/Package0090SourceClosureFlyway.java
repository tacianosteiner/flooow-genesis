import java.nio.file.*;
import java.util.Properties;
import tools.jackson.databind.ObjectMapper;
import org.flywaydb.core.Flyway;

/** V001-V042 only. Verifies the fresh isolated endpoint again immediately before JDBC. */
public final class Package0090SourceClosureFlyway {
    public static void main(String[] args) throws Exception {
        var p = new Properties();
        try (var r = Files.newBufferedReader(Path.of(args[0]))) { p.load(r); }
        String project=p.getProperty("project"), volume=p.getProperty("volume"), container=p.getProperty("container");
        if (!project.matches("flooow-0090-g3f4-[a-f0-9]{12}") || !volume.equals(project+"-data") || !container.equals(project+"-postgres") || !p.getProperty("target").equals("042")) throw new IllegalArgumentException("DISPOSABLE_042_ONLY");
        var process=new ProcessBuilder("docker","inspect",container).redirectError(ProcessBuilder.Redirect.DISCARD).start();
        var data=process.getInputStream().readAllBytes();
        if (process.waitFor()!=0) throw new IllegalStateException("ENDPOINT_UNVERIFIED");
        var root=new ObjectMapper().readTree(data).get(0);
        if (!root.path("Config").path("Labels").path("com.docker.compose.project").asText().equals(project) || !root.path("Image").asText().equals("sha256:07fc165de5bb569d822460e2df645c5489f99220fc2cb16c86596d39db394561") || !root.path("State").path("Running").asBoolean()) throw new IllegalStateException("ENDPOINT_UNVERIFIED");
        int volumes=0,binds=0;
        for (var mount:root.path("Mounts")) {
            if (mount.path("Type").asText().equals("volume") && mount.path("Name").asText().equals(volume) && mount.path("Destination").asText().equals("/var/lib/postgresql")) volumes++;
            else if (mount.path("Type").asText().equals("bind") && mount.path("Destination").asText().equals("/review") && !mount.path("RW").asBoolean()) binds++;
            else throw new IllegalStateException("UNAPPROVED_MOUNT");
        }
        if (volumes!=1 || binds!=1) throw new IllegalStateException("UNAPPROVED_MOUNT");
        var binding=root.path("NetworkSettings").path("Ports").path("5432/tcp");
        if (binding.size()!=1 || !binding.get(0).path("HostIp").asText().equals("127.0.0.1")) throw new IllegalStateException("UNAPPROVED_BINDING");
        String url="jdbc:postgresql://127.0.0.1:"+binding.get(0).path("HostPort").asText()+"/g3f4";
        if (!url.equals(p.getProperty("url"))) throw new IllegalStateException("STALE_ENDPOINT");
        try (var files=Files.list(Path.of(p.getProperty("migrations")))) {
            var paths=files.toList();
            if (paths.size()!=42 || paths.stream().anyMatch(f -> !f.getFileName().toString().matches("V0(?:0[1-9]|[1-3][0-9]|4[0-2])__.+\\.sql"))) throw new IllegalStateException("ONLY_FROZEN_042_RESOURCES");
        }
        Flyway.configure().dataSource(url,"postgres",p.getProperty("password"))
            .locations("filesystem:"+p.getProperty("migrations")).target("042")
            .outOfOrder(false).cleanDisabled(true).load().migrate();
    }
}
