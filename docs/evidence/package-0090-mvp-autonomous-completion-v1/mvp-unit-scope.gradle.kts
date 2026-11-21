allprojects {
    tasks.withType<org.gradle.api.tasks.testing.Test>().configureEach {
        exclude("**/CommandAuthorityCeremonyPostgresTest*")
        exclude("**/OfflineFieldProofLauncherTest*")
    }
}
