plugins { id("flooow.kotlin-conventions") }
dependencies {
    implementation(project(":platform:foundation:organization-context"))
    implementation(project(":applications:marketplace-operations"))
    implementation(project(":applications:marketplace-operations-persistence-postgres"))
    testImplementation(kotlin("test"))
    testImplementation("org.testcontainers:testcontainers-postgresql:2.0.5")
    testImplementation("org.flywaydb:flyway-core:13.2.0")
    testImplementation("org.flywaydb:flyway-database-postgresql:13.2.0")
    testImplementation("org.postgresql:postgresql:42.7.12")
}
