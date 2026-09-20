plugins {
    id("flooow.kotlin-conventions")
}

dependencies {
    implementation(project(":platform:foundation:kernel"))
    implementation(project(":platform:foundation:organization-context"))
    implementation("org.jetbrains.kotlinx:kotlinx-serialization-json:1.9.0")
    testImplementation(kotlin("test"))
}
