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
- repo-local SDK artifacts under `libs/`

This repo is intended for testing the plugin behavior in an app shell with on-device controls.

## Build and test

```bash
./gradlew assembleDebug
./gradlew testDebugUnitTest
```

The project expects a local Android SDK and JDK 17.

## Notes

- Signing is checked into the repo for deterministic sideload builds.
- The WearTAK SDK is consumed from the repo-local `libs/` directory.
- More detailed behavior notes live in [`docs/Docs.md`](docs/Docs.md).
