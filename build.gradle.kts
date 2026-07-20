plugins {
    id("com.android.application") version "8.7.2"
    id("org.jetbrains.kotlin.android") version "2.0.21"
}

android {
    namespace = "com.weartak.plugin.appteamplate"
    compileSdk = 34

    defaultConfig {
        applicationId = "com.weartak.plugin.appteamplate"
        minSdk = 30
        targetSdk = 34
        versionCode = 1
        versionName = "0.1.0-app-template"
        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
    }

    buildTypes {
        debug {
            isMinifyEnabled = false
        }
        release {
            isMinifyEnabled = false
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    kotlinOptions {
        jvmTarget = "17"
    }

    buildFeatures {
        buildConfig = true
    }

    testOptions {
        unitTests.isIncludeAndroidResources = true
    }
}

apply(from = rootProject.file("gradle/weartak-sideload-debug.gradle"))
apply(from = rootProject.file("gradle/weartak-sideload-production.gradle"))

dependencies {
    implementation(files("libs/weartak-plugin-sdk-debug.aar"))
    implementation("androidx.core:core-ktx:1.13.1")
    implementation("androidx.appcompat:appcompat:1.7.0")
    testImplementation("junit:junit:4.13.2")
    testImplementation("org.robolectric:robolectric:4.13")
}
