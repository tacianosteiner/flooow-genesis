import java.nio.charset.StandardCharsets;
import java.util.Properties;
import com.fasterxml.jackson.databind.ObjectMapper;

/** Refuses stale/reassigned localhost ports before any JDBC connection. */
public final class Package0090RehearsalEndpoint {
    public static String require(Properties p) throws Exception {
        String project=p.getProperty("project"), volume=p.getProperty("volume"), container=p.getProperty("container");
        if(project==null || !project.matches("flooow-0090-g3f4-[a-f0-9]{12}") || !volume.equals(project+"-data") || !container.equals(project+"-postgres")) throw new IllegalArgumentException("DISPOSABLE_IDENTITY_REQUIRED");
        var process=new ProcessBuilder("docker","inspect",container).redirectError(ProcessBuilder.Redirect.DISCARD).start();
        byte[] data=process.getInputStream().readAllBytes();
        if(process.waitFor()!=0)throw new IllegalStateException("DISPOSABLE_ENDPOINT_UNVERIFIED");
        var root=new ObjectMapper().readTree(data).get(0);
        if(!root.path("Config").path("Labels").path("com.docker.compose.project").asText().equals(project) || !root.path("Image").asText().equals("sha256:07fc165de5bb569d822460e2df645c5489f99220fc2cb16c86596d39db394561") || !root.path("State").path("Running").asBoolean())throw new IllegalStateException("DISPOSABLE_ENDPOINT_UNVERIFIED");
        int volumes=0,binds=0;
        for(var mount:root.path("Mounts")) {
            if(mount.path("Type").asText().equals("volume") && mount.path("Name").asText().equals(volume) && mount.path("Destination").asText().equals("/var/lib/postgresql"))volumes++;
            else if(mount.path("Type").asText().equals("bind") && mount.path("Destination").asText().equals("/review") && !mount.path("RW").asBoolean())binds++;
            else throw new IllegalStateException("UNAPPROVED_DISPOSABLE_MOUNT");
        }
        if(volumes!=1 || binds!=1)throw new IllegalStateException("UNAPPROVED_DISPOSABLE_MOUNT");
        var binding=root.path("NetworkSettings").path("Ports").path("5432/tcp");
        if(binding.size()!=1 || !binding.get(0).path("HostIp").asText().equals("127.0.0.1"))throw new IllegalStateException("DISPOSABLE_ENDPOINT_UNVERIFIED");
        String expected="jdbc:postgresql://127.0.0.1:"+binding.get(0).path("HostPort").asText()+"/g3f4";
        if(!expected.equals(p.getProperty("url")))throw new IllegalStateException("STALE_DISPOSABLE_PORT");
        return expected;
    }
}
