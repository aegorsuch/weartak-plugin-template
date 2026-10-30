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

## Forge release pipeline

`.gitlab-ci.yml` runs publisher/checklist tests and unsigned debug tests for merge requests,
the default branch, and version tags. Protected default-branch pushes also build a
production-signed APK, verify its WearTAK production certificate, and publish it to a
GitHub rolling release. A verified publish dispatches the GitHub workflow, which creates
one release-testing issue per GitLab pipeline.

Before enabling protected default-branch publishing, a project owner must configure these
GitLab CI/CD variables:

| Variable | Value |
| --- | --- |
| `WEARTAK_RELEASE_KEYSTORE_B64` | Base64-encoded WearTAK production keystore |
| `RELEASE_STORE_PASSWORD` | Production keystore password |
| `RELEASE_KEY_ALIAS` | Production key alias |
| `RELEASE_KEY_PASSWORD` | Production key password |
| `GITHUB_RELEASE_REPOSITORY` | GitHub destination as `owner/repository` |
| `GITHUB_RELEASE_TOKEN` | Masked, protected GitHub token with Contents read/write and repository-dispatch access |
| `GITHUB_RELEASE_TAG` | Existing fixed tag on the GitHub destination; publisher never creates or moves tags |
| `GITHUB_RELEASE_APPLICATION_ID` | `applicationId` from `app/build.gradle.kts` |
| `GITHUB_RELEASE_ASSET_PREFIX` | Short plugin identifier used in published APK names |

Protect the GitLab default branch and the fixed GitHub release tag. The GitHub repository
must define `RELEASE_TESTER` as a username with permission to be assigned issues and
`GITHUB_RELEASE_TAG` with the same tag value used by GitLab for manual checklist runs.
Keep signing and GitHub tokens in protected/masked CI variables; never commit them.

New plugin authors must set the APK application ID, choose a unique asset prefix, configure
the GitHub mirror/release variables above, and provide production signing variables before
enabling publish jobs. `settings.gradle.kts` uses TAK Artifactory when token-service
credentials are available and falls back to Google Maven Central and the Gradle plugin
portal for local builds.

## Notes

- Debug builds use the standard Android debug keystore when no custom signing values are supplied.
- GitLab or local custom signing can be supplied with the `WEARTAK_DEBUG_*` and `WEARTAK_RELEASE_*`
  environment variables. A root-level `signing.properties` file using the corresponding short
  property names is supported for local builds and must not be committed.
- The WearTAK SDK is consumed from the repo-local `app/libs/` directory.
- Keystore directories are intentionally not included in this template. Shared signing backups
  are retained centrally under `WT-Plugin-Docs/signing-backups/`.
- More detailed behavior notes live in [`docs/Docs.md`](docs/Docs.md).
