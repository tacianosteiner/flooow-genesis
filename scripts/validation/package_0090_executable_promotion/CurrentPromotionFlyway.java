import java.nio.file.*;
import java.security.MessageDigest;
import java.util.*;
import org.flywaydb.core.Flyway;
import org.flywaydb.core.api.ResourceProvider;
import org.flywaydb.core.api.resource.LoadableResource;
import java.io.*;
import java.nio.charset.StandardCharsets;

/** Complete artifact consumer. Python verifies live Docker endpoint before each invocation. */
public final class CurrentPromotionFlyway {
  record Verified(String name, String sql) {}
  static final class FrozenResource extends LoadableResource {
    final Verified v;
    FrozenResource(Verified v){this.v=v;}
    public Reader read(){return new StringReader(v.sql());}
    public String getAbsolutePath(){return "TEST_ONLY_NONCANONICAL/"+v.name();}
    public String getAbsolutePathOnDisk(){return getAbsolutePath();}
    public String getFilename(){return v.name();}
    public String getRelativePath(){return v.name();}
  }
  static String digest(Path p) throws Exception {
    return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(p)));
  }
  public static void main(String[] args) throws Exception {
    var p=new Properties();try(var in=Files.newBufferedReader(Path.of(args[0]))){p.load(in);}
    if(!p.getProperty("marker").equals("TEST_ONLY_NONCANONICAL"))throw new IllegalArgumentException("MARKER");
    if(!digest(Path.of(p.getProperty("manifest"))).equals(p.getProperty("manifest_sha256")))throw new IllegalArgumentException("MANIFEST_HASH");
    if(!digest(Path.of(p.getProperty("successor"))).equals(p.getProperty("successor_sha256")))throw new IllegalArgumentException("SUCCESSOR_HASH");
    if(!p.getProperty("url").matches("jdbc:postgresql://127\\.0\\.0\\.1:[0-9]+/promotion_fixture"))throw new IllegalArgumentException("NONCANONICAL_ENDPOINT");
    var resources=new ArrayList<LoadableResource>();
    try(var stream=Files.list(Path.of(p.getProperty("migrations")))){
      for(var file:stream.sorted().toList()){
        var bytes=Files.readAllBytes(file);var name=file.getFileName().toString();
        var actual=HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes));
        if(!actual.equals(p.getProperty("migration_sha256."+name)))throw new IllegalArgumentException("CONSUMED_RESOURCE_HASH "+name);
        if(name.startsWith("V043__")&&!actual.equals(p.getProperty("successor_sha256")))throw new IllegalArgumentException("CONSUMED_SUCCESSOR_HASH");
        resources.add(new FrozenResource(new Verified(name,new String(bytes,StandardCharsets.UTF_8))));
      }
    }
    if(resources.size()!=43)throw new IllegalArgumentException("COMPLETE_RESOURCE_SET");
    final var frozen=List.copyOf(resources);
    ResourceProvider provider=new ResourceProvider(){
      public LoadableResource getResource(String name){return frozen.stream().filter(r->r.getFilename().equals(name)).findFirst().orElse(null);}
      public Collection<LoadableResource> getResources(String prefix,String[] suffixes){return frozen.stream().filter(r->r.getFilename().startsWith(prefix)&&Arrays.stream(suffixes).anyMatch(s->r.getFilename().endsWith(s))).toList();}
    };
    System.out.println("CONSUMER_RESOURCE_SET=43_VERIFIED_IMMUTABLE_IN_MEMORY");
    Flyway.configure().dataSource(p.getProperty("url"),"postgres","").resourceProvider(provider).target(p.getProperty("target")).cleanDisabled(true).load().migrate();
  }
}
