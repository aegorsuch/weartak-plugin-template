# WearTAK Plugin App Template

`weartak-plugin-app-template` is a Wear OS plugin app for WearTAK. It includes the same combined
plugin behavior as the template repo, but packages it with a visible launcher activity so the
plugin can be exercised directly on the watch.

## What it includes

- hosted settings support
- CEP rule add/remove behavior
- map marker and map-layer actions
- alert requests with toast fallback
- hello-world toast behavior
- a launcher `MainActivity`
- a return-to-WearTAK action
- a bound WearTAK plugin service
- repo-local SDK artifacts under `app/libs/`

This repo is intended for testing the plugin behavior in an app shell with on-device controls.

## Build and test

```bash
./gradlew :app:assembleDebug
./gradlew :app:testDebugUnitTest
```

The project expects a local Android SDK and JDK 17.

## Project layout

This repository uses the conventional Android application structure:

- `build.gradle.kts` — project-level plugin declarations
- `settings.gradle.kts` — project settings and `:app` module inclusion
- `app/build.gradle.kts` — Android application configuration, dependencies, and build types
- `app/src/` — plugin source, manifest, resources, assets, and tests
- `app/libs/` — bundled WearTAK SDK AAR artifacts

## Notes

- Debug builds use the standard Android debug keystore when no custom signing values are supplied.
- GitLab or local custom signing can be supplied with the `WEARTAK_DEBUG_*` and `WEARTAK_RELEASE_*`
  environment variables. A root-level `signing.properties` file using the corresponding short
  property names is supported for local builds and must not be committed.
- The WearTAK SDK is consumed from the repo-local `app/libs/` directory.
- Keystore directories are intentionally not included in this template. Shared signing backups
  are retained centrally under `WT-Plugin-Docs/signing-backups/`.
- More detailed behavior notes live in [`docs/Docs.md`](docs/Docs.md).
