// Verified working: Gradle 9.4.1, JDK 17, Kotlin Gradle plugin 2.1.0,
// kotlinx-coroutines-test 1.9.0, JUnit BOM 5.11.3.
// Gradle 9.x no longer puts the JUnit Platform launcher on the test runtime
// classpath automatically, so junit-platform-launcher must be added explicitly
// (testRuntimeOnly) or the test task fails with "Failed to load JUnit Platform."
plugins {
    kotlin("jvm") version "2.1.0"
}

repositories { mavenCentral() }

dependencies {
    testImplementation(platform("org.junit:junit-bom:5.11.3"))
    testImplementation("org.junit.jupiter:junit-jupiter")
    testRuntimeOnly("org.junit.platform:junit-platform-launcher")
    testImplementation("org.jetbrains.kotlinx:kotlinx-coroutines-test:1.9.0")
}

kotlin { jvmToolchain(17) }

tasks.test { useJUnitPlatform() }
