# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project intent

매트리스 점검 체크리스트 Android 앱 ("Mattress Inspection Checklist Android App"). Per the
README, the goal is to wrap an existing web checklist in an Android `WebView` so it can run
offline. Intended features (from README.md, none implemented yet — see below):
- Runs fully offline
- Auto-tallies yes/no responses
- Persists customer name, inspection date, and answers automatically
- Supports copying, printing, and resetting results
- Sends nothing to a server; no personal data leaves the device

## Current repository state (important)

This repository is currently a bare Gradle skeleton, not a working Android project. Before
writing "app" code, be aware:

- **There is no `app/` module on disk**, even though `settings.gradle` declares
  `include ':app'`. No `AndroidManifest.xml`, no Kotlin/Java source, no `res/`, and no WebView
  code or checklist HTML/JS/CSS exist anywhere in the repo yet.
- **The Gradle wrapper is incomplete.** `gradlew` / `gradlew.bat` are present, but
  `gradle/wrapper/gradle-wrapper.properties` and `gradle-wrapper.jar` are missing, so `./gradlew`
  will not run as-is. Root `build.gradle` only declares the AGP plugin (`com.android.application`
  8.5.2, not applied at root); there is no top-level `dependencies`/`repositories` setup beyond
  `settings.gradle`'s `pluginManagement`/`dependencyResolutionManagement` blocks.
- **`local.properties` is committed**, which is unusual (it's normally per-machine and
  gitignored). It currently hardcodes a Windows SDK path
  (`sdk.dir=C:\Users\USER\AppData\Local\Android\Sdk`) that will not resolve on other machines or
  in CI. There is no `.gitignore` in the repo at all.
- **The CI workflow does not actually build an APK.** `.github/workflows/build-apk.yml` (manual
  `workflow_dispatch` trigger only) just checks out the repo, runs `ls -R`, and uploads the
  entire working tree as a build artifact named `AndroidProject`. Despite the workflow's name and
  the README's "Build APK(s) in Android Studio" instructions, no `assembleDebug`/Gradle build
  step exists yet in CI.
- `SECURITY.md` is the default GitHub template with placeholder text (unfilled version table,
  "Use this section to tell people..." boilerplate) — not real project-specific policy.

**Implication for any task here:** creating the `app` module (manifest, a single WebView-hosting
Activity, `res/` for the app icon/theme, and the actual checklist as a local HTML/CSS/JS asset
under `app/src/main/assets/`), fixing the Gradle wrapper, and wiring a real `assembleDebug` CI
step are all still-open work, not existing code to navigate. Confirm scope with the user before
assuming a full Android app already exists to modify.

## Working with this repo today

There is no working build/lint/test command yet — do not fabricate one. If the current task is
to bootstrap the missing pieces:
- Regenerate the wrapper via `gradle wrapper` (or copy `gradle-wrapper.jar` +
  `gradle-wrapper.properties` from a known-good AGP 8.5.2-compatible Gradle version) before
  expecting `./gradlew` to work.
- Root `settings.gradle` already wires `google()`/`mavenCentral()`/`gradlePluginPortal()` via
  `dependencyResolutionManagement` with `FAIL_ON_PROJECT_REPOS`, so an `app/build.gradle` module
  should not redeclare its own `repositories {}` block.
- Once an `app` module exists, standard Android Gradle commands apply:
  `./gradlew assembleDebug` (build), `./gradlew lint` (lint), `./gradlew test` /
  `./gradlew connectedAndroidTest` (unit / instrumented tests) — but none of these currently
  work because the module doesn't exist and the wrapper jar is missing.
- If replacing `local.properties`, remember it is currently tracked in git (unusually) — check
  with the user before deleting or gitignoring it, since that's a deliberate-looking deviation
  from normal Android project convention.

## Repository layout

```
.
├── .github/workflows/build-apk.yml   # workflow_dispatch only; lists files & uploads repo, does not build
├── README.md                          # Korean; project description + Android Studio build steps
├── SECURITY.md                        # unfilled GitHub template
├── build.gradle                       # root: declares AGP 8.5.2 plugin only
├── settings.gradle                    # declares repos + `include ':app'` (module absent)
├── gradle.properties                  # JVM args + AndroidX flag
├── gradlew / gradlew.bat              # wrapper scripts (wrapper jar/properties missing)
└── local.properties                   # committed; hardcoded Windows SDK path
```
