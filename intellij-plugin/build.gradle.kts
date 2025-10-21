plugins {
    id("java")
    id("org.jetbrains.intellij") version "1.16.0"
    id("org.jetbrains.kotlin.jvm") version "1.9.0"
}

group = "com.reviewr"
version = "1.0.0"

repositories {
    mavenCentral()
}

dependencies {
    implementation("com.google.code.gson:gson:2.10.1")
    implementation("org.apache.httpcomponents:httpclient:4.5.14")
    testImplementation("junit:junit:4.13.2")
}

// Configure Gradle IntelliJ Plugin
intellij {
    version.set("2023.2")
    type.set("IC") // IntelliJ IDEA Community Edition
    
    plugins.set(listOf(
        "com.intellij.java",
        "org.jetbrains.plugins.go",
        "JavaScript",
        "org.rust.lang"
    ))
}

tasks {
    // Set the JVM compatibility versions
    withType<JavaCompile> {
        sourceCompatibility = "17"
        targetCompatibility = "17"
    }
    
    patchPluginXml {
        sinceBuild.set("232")
        untilBuild.set("242.*")
        
        pluginDescription.set("""
            <h1>Reviewr - AI-Powered Code Review</h1>
            <p>
            Reviewr brings world-class AI-powered code review directly into your IDE.
            Get instant feedback on security, performance, correctness, and code quality
            as you write code.
            </p>
            <h2>Features:</h2>
            <ul>
                <li>Real-time code analysis with 21 specialized analyzers</li>
                <li>Support for Python, JavaScript/TypeScript, Go, Rust, and Java</li>
                <li>Security vulnerability detection</li>
                <li>Performance optimization suggestions</li>
                <li>Code quality and maintainability checks</li>
                <li>AI-powered auto-fix capabilities</li>
                <li>Inline warnings and quick fixes</li>
                <li>Comprehensive metrics and reporting</li>
            </ul>
        """.trimIndent())
        
        changeNotes.set("""
            <h2>Version 1.0.0</h2>
            <ul>
                <li>Initial release</li>
                <li>Support for Python, JavaScript/TypeScript, Go, Rust, Java</li>
                <li>21 specialized code analyzers</li>
                <li>Real-time inline diagnostics</li>
                <li>Quick fix actions</li>
                <li>Tool window for review results</li>
                <li>Configurable settings</li>
            </ul>
        """.trimIndent())
    }
    
    signPlugin {
        certificateChain.set(System.getenv("CERTIFICATE_CHAIN"))
        privateKey.set(System.getenv("PRIVATE_KEY"))
        password.set(System.getenv("PRIVATE_KEY_PASSWORD"))
    }
    
    publishPlugin {
        token.set(System.getenv("PUBLISH_TOKEN"))
    }
}

