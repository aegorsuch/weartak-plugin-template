# WearTAK Plugin App Template Docs

## Purpose

`weartak-plugin-app-teamplate` is the launcher-app companion to the WearTAK plugin
template. It uses the same shared plugin runtime as `weartak-plugin-template`, but adds
an on-device launcher activity so the plugin can be exercised without going through the
host UI for every action.

This repo exists to demonstrate the same consolidated plugin behavior in an APK that has:

- a visible launcher icon
- a main activity with action buttons
- a return-to-WearTAK button
- the same plugin service and runtime contract as the template repo

## What This Repo Ships

This repo ships one Wear OS APK with:

- a bound WearTAK plugin service
- a launcher activity
- hosted main UI support
- external main activity support
- signing for sideload / host-parity installation
- the WearTAK SDK consumed from the repo-local `libs/` directory

Unlike `weartak-plugin-template`, this APK is meant to be visible on the watch and
usable as a standalone app shell around the shared plugin runtime.

## Functional Coverage

This repo exposes the same consolidated plugin behaviors as the template repo:

### Settings

- hosted settings are enabled through the shared runtime
- settings validation and apply behavior is the same as Repo 1
- restart-required settings still drive the lifecycle transitions

### CEP

- `CEP Add` exercises `cep.run` with the default `operation=add`
- `CEP Remove` exercises `cep.run` with `operation=remove`
- the runtime maps remove to:
  - V2 `CepRuleStreamEventParcel(operation = REMOVE)`
  - V1 `unregisterCepRules(...)`
- the service loads a CEP template from `src/main/assets/plugin_rules.json` and renders the
  current plugin id and sensor key into it before add/register requests
- the `rulesJson` action argument still overrides that template when present
- if neither the argument nor the asset is available, `cep.run` fails explicitly instead of
  registering a stub payload

### Map

- `Map Show` exercises `map.run` with the default `operation=add`
- `Map Remove` exercises `map.run` with `operation=remove`
- the runtime uses map-layer commands when supported and marker publish otherwise

### Alerts

- `Alert` exercises the shared alert path
- the runtime still performs requestAlert / requestToast fallback handling

### Hello World

- `Hello World` exercises the shared toast path

### Return to WearTAK

- the launcher includes a `Return to WearTAK` button
- it resolves the host package from the current runtime snapshot
- it launches the host via the package manager launch intent

## Action Arguments

The launcher buttons call into the same action argument surface used by the shared runtime.

### `cep.run`

| Arg | Type | Default | Notes |
| --- | --- | --- | --- |
| `operation` | string | `add` | `add` registers CEP rules, `remove` unregisters them. Unknown values currently fall back to `add`. |
| `sensorKey` | string | `demo.sensor` | Stable sensor key used for registration and removal. |
| `ruleSetId` | string | `demo-rules` | Stable rule-set identifier for the stream. |
| `rulesJson` | string | asset-rendered JSON | Used for CEP add/register requests. If omitted, the service-loaded template is rendered with the current plugin id and sensor key. |

### `map.run`

| Arg | Type | Default | Notes |
| --- | --- | --- | --- |
| `operation` | string | `add` | `add` publishes / shows the map payload, `remove` removes it. Unknown values currently fall back to `add`. |
| `markerId` | string | `demo.marker` | Stable marker / layer identifier used by the demo action. |
| `title` | string | `Map Demo` | Marker title and layer payload label. |

### `alert.run`

| Arg | Type | Default | Notes |
| --- | --- | --- | --- |
| `title` | string | `WearTAK Alert` | Alert title shown to the host. |
| `message` | string | `Alert demo from plugin` | Alert body, and toast fallback message if alerts are unsupported. |
| `severity` | int | `1` | Passed through to the alert request parcel. |
| `channelId` | string | unset | Optional alert channel identifier. |

### `settings.run`

- No arguments are currently required.
- The action toggles `enable_stream` through the validated settings apply path.

### `hello.world`

- No arguments are currently required.
- The action emits the hello-world toast behavior directly.

## Main UI

This repo includes an actual launcher activity:

- vertical layout
- action buttons for each consolidated behavior
- separate add/remove buttons for CEP and map
- host status display
- last action display

The activity uses the shared runtime snapshot as the source of truth for:

- host package
- lifecycle state
- attachment state
- last action and message
- action counters

## Source Layout

Important source areas:

- `src/main/java/com/weartak/plugin/appteamplate/MainActivity.kt`
- `src/main/java/com/weartak/plugin/template/service/TemplatePluginRuntime.kt`
- `src/main/java/com/weartak/plugin/template/service/TemplatePluginBinder.kt`

The runtime package name remains shared on purpose so the two repos stay diffable and
behaviorally aligned.

## Plugin Contract

The plugin still binds through the same WearTAK SDK AIDL contract as the template repo.

Contract highlights:

- `initializePluginV2(...)` is the canonical initialization path
- `initializePlugin(...)` is legacy compatibility only
- the binder delegates feature work to the shared runtime
- the runtime handles all feature state, status snapshots, and action routing

## Capability Model

This repo truthfully declares the capabilities it actually supports.

It shares the same capability model as Repo 1, except for the launcher flag:

- `hostedSettingsUi = true`
- `hostedMainUi = true`
- `externalSettingsActivity = false`
- `externalMainActivity = true`
- `cotReadyEvents = false`
- `mapLayers = true`
- `deviceIntegration = false`
- `sharedMemory = false`

That `externalMainActivity` flag is the only intentional capability difference between
the two repos.

## Signing

Signing is included in-repo for deterministic sideload builds.

Signing expectations:

- debug and release builds use the repo-local sideload signing scripts
- the APK is intended to be co-installed with the WearTAK host
- signature compatibility matters because `BIND_PLUGIN` is signature-protected

Important constraint:

- if the host and plugins are not signed compatibly, Android can reject co-installation
  with a duplicate-permission error
- the checked-in keystores and plaintext passwords are development / sideload credentials
  only and are not intended for production distribution

## SDK Consumption

The WearTAK SDK is consumed from the repo-local `libs/` directory.

This repo uses the checked-in AAR artifacts rather than a network-fetched SDK dependency.
That keeps the launcher app and the plugin service aligned with the same contract surface.

## Build Notes

The repo is configured as a normal Android Gradle project with pinned plugin versions.

Key expectations:

- builds work from a clean checkout
- no machine-global Gradle plugin state is required
- the local SDK AARs are used consistently for both debug and release

Quickstart:

```bash
./gradlew assembleDebug
./gradlew testDebugUnitTest
```

The repo expects a local Android SDK and JDK 17.

## Testing

The repository includes unit tests that cover:

- launcher-capability exposure
- legacy init no-op behavior
- settings validation and restart-required handling
- `NOT_ATTACHED` behavior for map when the host control is absent
- CEP add/remove routing
- map add/remove routing
- shutdown immutability behavior
- host settings reflection into status and UI state

Repo 2 has one extra capability test because it is the launcher variant.

Known launcher limitations:

- action taps currently execute on a background thread per tap; rapid taps can interleave
  result messages
- the snapshot observer and action outcomes both write to `statusView`, so a fresh
  snapshot render can overwrite the last action message

## Intentional Waivers

The following original example behaviors were intentionally not preserved as separate
startup side effects:

- CEP startup sensor streaming loop
- CEP startup alert
- map startup marker publish
- map startup custom-item add
- map stop-time custom-item removal
- alert startup alert
- hello-world startup toast

The old `debug.*` action aliases were also intentionally replaced by the consolidated
action surface used by the shared runtime.

### Debug Alias Mapping

| Original alias | Consolidated action |
| --- | --- |
| `debug.register_cep` | `cep.run` with `operation=add` |
| `debug.unregister_cep` | `cep.run` with `operation=remove` |
| `debug.publish_marker` | `map.run` with `operation=add` |
| `debug.map_layer_add` | `map.run` with `operation=add` |
| `debug.map_layer_remove` | `map.run` with `operation=remove` |
| `debug.request_alert` | `alert.run` |
| `debug.request_toast` | `hello.world` |

Those behaviors are documented here so the launcher app stays a combined plugin demo
instead of drifting back into five separate example patterns.

### CEP Streaming Scope

This repo intentionally does not implement sustained periodic CEP streaming via
`PluginCepStreamSession`.

The V2 CEP contract is demonstrated as a single-shot mutation path through
`applyCepRuleEvent(...)`, and the V1 compatibility path uses
`registerCepRules(...)` / `unregisterCepRules(...)`.

## Parity Rule

The shared runtime is expected to remain identical between both repos unless a deliberate
exception is documented.

Current intentional Repo 2 difference:

- this repo exposes a launcher activity and sets `externalMainActivity = true`

Everything else in the runtime is intended to stay aligned with Repo 1.

Current enforcement status:

- parity is checked manually by comparing `TemplatePluginRuntime.kt` between repos
- an automated CI checksum guard is planned but not yet present

## Naming Notes

- `hello.world` is intentionally frozen, even though it does not follow the `*.run`
  naming pattern used by the other actions
- the repo name spelling `teamplate` is baked into the package / application identity and
  should not be normalized without a deliberate migration plan

## Current Repo Status

This repo is the launcher-app companion variant:

- launcher icon visible on the watch
- vertical action shell in the main activity
- return-to-host button included
- same plugin service contract as Repo 1
- same consolidated runtime behavior as Repo 1
