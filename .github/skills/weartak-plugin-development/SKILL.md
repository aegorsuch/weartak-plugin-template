---
name: weartak-plugin-development
description: Implement, modify, and validate features in this WearTAK Android plugin app template. Use for plugin service, binder, lifecycle, settings, host integration, UI, and Gradle test/build work.
---

# WearTAK plugin development

Use this skill when changing the WearTAK plugin app in this repository.

## Repository constraints

- Treat this as a standalone Wear OS app and plugin. Keep on-watch operation usable without ATAK Companion; host integration is optional.
- Check the existing implementation before changing behavior. Plugin service and manifest are under `app/src/main`; binder and runtime live in `com.weartak.plugin.template.service`.
- Use the WearTAK SDK AARs already in `app/libs` and existing SDK contract, validation, lifecycle, and binder-guard APIs. Do not recreate SDK types or invent host APIs.
- Follow existing Kotlin and Android patterns. Keep changes focused; avoid new dependencies unless necessary.
- Preserve debug and release SDK variants and the existing signing/build setup. Never expose or modify signing credentials.
- Java and Kotlin target 17. The project needs a local Android SDK.

## Implementing changes

1. Trace the relevant flow from manifest/service through binder and runtime before editing.
2. Keep lifecycle transitions valid and route host operations through the provided control interfaces. Check host capabilities and handle unavailable or detached hosts explicitly.
3. Keep settings schema, validation, persisted values, derived status/UI state, and host notifications consistent when changing settings behavior.
4. Add or update focused Robolectric unit tests in `app/src/test` for changed behavior. Prefer existing test helpers and assert observable results and host calls.
5. Do not claim device behavior is verified unless it was tested on a device.

## Validation

Run relevant tests, then build when changes affect app code, resources, manifest, or build configuration:

```powershell
.\gradlew.bat testDebugUnitTest
.\gradlew.bat assembleDebug
```

On macOS/Linux, use `./gradlew` with the same task names. Report commands that could not run and their concrete blocker; do not treat an unverified build as successful.
