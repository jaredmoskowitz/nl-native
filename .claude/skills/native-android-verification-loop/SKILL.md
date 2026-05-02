---
name: native-android-verification-loop
description: Use when building, verifying, or debugging a native Android Kotlin/Compose app — builds with Gradle, interacts via adb commands (no mouse stealing), captures screenshots, reads logcat, and iterates fixes until the feature works visually and functionally.
---

# Native Android Verification Loop

## Overview

Autonomous verification cycle for native Android Kotlin/Jetpack Compose apps. Build with Gradle, interact with the running emulator via `adb` commands (programmatic tap/type/swipe — no mouse stealing), capture state via screenshots, read logcat, fix, rebuild, repeat. Exit when the feature works end-to-end and looks correct.

**This is the Android counterpart to `native-ios-verification-loop`.** It targets pure native Android: Kotlin, Jetpack Compose, Gradle, JUnit 5, Espresso/Compose UI tests.

## When to Use

- Verifying a Compose screen renders correctly on a real emulator
- Debugging a bug you can reproduce in the emulator
- End-to-end flow validation before claiming a feature complete
- Verifying animations and transitions in Compose
- Testing across different screen sizes or API levels

## Prerequisites

- Android Studio installed with SDK tools
- Android emulator with API 34+ (or a connected device)
- `adb` accessible in PATH (comes with Android SDK platform-tools)
- `ANDROID_HOME` or `ANDROID_SDK_ROOT` set
- Gradle wrapper (`./gradlew`) in the project root

## Emulator Setup

### Boot an emulator

```bash
# List available AVDs
emulator -list-avds

# Boot (headless for CI, or with UI for visual verification)
emulator -avd Pixel_8_API_35 &

# Wait for boot to complete
adb wait-for-device
adb shell getprop sys.boot_completed  # should return "1"
```

### If no AVD exists

```bash
# Create one (requires sdkmanager)
sdkmanager "system-images;android-35;google_apis;arm64-v8a"
avdmanager create avd -n Pixel_8_API_35 -k "system-images;android-35;google_apis;arm64-v8a" -d pixel_8
```

### Multiple devices: always specify serial

```bash
# List connected devices/emulators
adb devices

# Use -s flag for all commands when multiple are running
adb -s emulator-5554 shell input tap 200 400
```

## Build Commands

### Standard build + install + launch

```bash
cd platforms/android

# Build debug APK
./gradlew assembleDebug

# Install on emulator
adb install -r app/build/outputs/apk/debug/app-debug.apk

# Launch main activity
adb shell am start -n <PACKAGE>/<PACKAGE>.MainActivity
```

### One-liner: clean build + install + launch

```bash
./gradlew assembleDebug && \
  adb install -r app/build/outputs/apk/debug/app-debug.apk && \
  adb shell am start -n <PACKAGE>/<PACKAGE>.MainActivity
```

### If build fails after adding dependencies

```bash
# Clean and rebuild
./gradlew clean assembleDebug

# If Gradle cache is corrupted
rm -rf ~/.gradle/caches/transforms-*
./gradlew assembleDebug --refresh-dependencies
```

## Interacting with the App (adb — preferred, no mouse stealing)

### Take a screenshot

```bash
# Capture to local file
adb exec-out screencap -p > /tmp/android_screen.png
# Then Read /tmp/android_screen.png with the Read tool
```

### Tap by coordinates

```bash
# Tap at (x, y) in device coordinates
adb shell input tap 540 960
```

**Finding coordinates:** Take a screenshot, read it with the Read tool, estimate the center of the target element. Standard Pixel emulator: 1080x2400 pixels.

### Type text

```bash
# Type into focused text field
adb shell input text "hello%sworld"  # %s = space

# For special characters, use keyevent or broadcast
adb shell input text "test@example.com"  # @ works directly

# Clear a field first
adb shell input keyevent KEYCODE_CTRL_LEFT KEYCODE_A
adb shell input keyevent KEYCODE_DEL
```

### Key events

```bash
# Back button
adb shell input keyevent KEYCODE_BACK

# Home
adb shell input keyevent KEYCODE_HOME

# Enter/Return
adb shell input keyevent KEYCODE_ENTER

# Tab (next field)
adb shell input keyevent KEYCODE_TAB
```

### Swipe / scroll

```bash
# Swipe up (scroll down) — duration in ms
adb shell input swipe 540 1800 540 600 300

# Swipe down (scroll up)
adb shell input swipe 540 600 540 1800 300

# Swipe left (next page)
adb shell input swipe 900 1200 180 1200 200

# Pull to refresh
adb shell input swipe 540 400 540 1200 500
```

### Deep link navigation (fastest)

```bash
# Open a deep link
adb shell am start -a android.intent.action.VIEW -d "myapp://notes/create"

# With specific package
adb shell am start -a android.intent.action.VIEW -d "myapp://notes" -n <PACKAGE>/<PACKAGE>.MainActivity
```

### Long press

```bash
# Long press at coordinates (swipe with 0 distance, long duration)
adb shell input swipe 540 960 540 960 1000
```

## Accessibility — Make Views Testable

Every interactive Compose element should have a `testTag` for deterministic interaction and Compose UI test matching:

```kotlin
Button(
    onClick = { /* ... */ },
    modifier = Modifier.testTag("sign-in-button")
) {
    Text("Sign In")
}

TextField(
    value = email,
    onValueChange = { email = it },
    modifier = Modifier.testTag("email-field")
)
```

**Convention:** `kebab-case-descriptive`. Match feature area: `note-list-item-{id}`, `note-editor-title`, `note-delete-confirm`.

### Find element bounds via UI dump

```bash
# Dump the view hierarchy (find testTags and their bounds)
adb shell uiautomator dump /sdcard/ui_dump.xml
adb pull /sdcard/ui_dump.xml /tmp/ui_dump.xml

# Search for a specific testTag
grep -i "sign-in-button" /tmp/ui_dump.xml
# Returns bounds like [270,1800][810,1920] → tap center: (540, 1860)
```

## Reading Logs

### Live logcat stream

```bash
# Stream app logs while running
adb logcat -s "YourAppTag:*" > /tmp/android.log 2>&1 &
LOGCAT_PID=$!

# ... trigger behaviors ...

# Check for errors
grep -iE "error|exception|fatal|crash" /tmp/android.log | tail -30

# Stop stream
kill $LOGCAT_PID
```

### Filter by package

```bash
# Get PID of running app
APP_PID=$(adb shell pidof <PACKAGE>)

# Stream only that PID's logs
adb logcat --pid=$APP_PID > /tmp/app.log 2>&1 &
```

### Recent logs (after the fact)

```bash
# Last 200 lines from the app
adb logcat -d -t 200 | grep -i "<PACKAGE_OR_TAG>"
```

### Crash logs

```bash
# Check for recent ANR (Application Not Responding)
adb shell ls /data/anr/ 2>/dev/null

# Pull tombstone (native crash)
adb shell ls /data/tombstones/ 2>/dev/null

# Check logcat for fatal exceptions
adb logcat -d | grep -A 10 "FATAL EXCEPTION"
```

## Compose UI Tests — Deterministic End-to-End

```kotlin
// app/src/androidTest/java/.../NoteFlowTest.kt
@HiltAndroidTest
class NoteFlowTest {
    @get:Rule
    val composeTestRule = createAndroidComposeRule<MainActivity>()

    @Test
    fun createNoteFlow() {
        composeTestRule
            .onNodeWithTag("create-note-fab")
            .performClick()

        composeTestRule
            .onNodeWithTag("note-editor-title")
            .performTextInput("My Test Note")

        composeTestRule
            .onNodeWithTag("note-editor-body")
            .performTextInput("This is the body")

        composeTestRule
            .onNodeWithTag("save-note-button")
            .performClick()

        composeTestRule
            .onNodeWithText("My Test Note")
            .assertIsDisplayed()
    }
}
```

Run:
```bash
./gradlew connectedAndroidTest \
  -Pandroid.testInstrumentationRunnerArguments.class=<PACKAGE>.NoteFlowTest
```

## Screen Recording (for animation verification)

```bash
# Start recording (max 180 seconds)
adb shell screenrecord /sdcard/recording.mp4 &
RECORD_PID=$!

# ... trigger the animation ...
sleep 3

# Stop recording
adb shell kill -INT $(adb shell ps | grep screenrecord | awk '{print $2}')

# Pull to local
adb pull /sdcard/recording.mp4 /tmp/android_recording.mp4
adb shell rm /sdcard/recording.mp4
```

### Extract frames

```bash
mkdir -p /tmp/android_frames
ffmpeg -i /tmp/android_recording.mp4 -vf "fps=10" /tmp/android_frames/frame_%03d.png -y 2>/dev/null
ls /tmp/android_frames/ | head -10
```

## Direct API Testing (Skip UI for Backend Bugs)

Same as iOS — test the backend directly with curl when the bug is server-side. Don't waste emulator time on API issues.

```bash
# See the backend testing section in the ios-simulator-debug-loop or
# the /connect command for API testing patterns
```

## The Loop

```
loop:
  1. Build: ./gradlew assembleDebug
  2. If build fails → read error → fix code → restart loop
  3. Install + launch on emulator
  4. Stream logcat in background to /tmp/android.log
  5. Interact: deep link → adb tap → adb input text
  6. Capture state:
       - screenshot (adb exec-out screencap -p > /tmp/screen.png)
       - OR screen recording if verifying animation
  7. Analyze:
       - Read screenshot → does UI match intent?
       - grep /tmp/android.log for "error|exception|fatal"
  8. If issue found:
       - Fix the code
       - Restart loop from step 1
  9. If UI correct AND logs clean AND flow completes → EXIT
```

## Context Hygiene

**CRITICAL:** Same as iOS — screenshots are large. Rules:
- **Max 1 screenshot per loop iteration**
- **Prefer logcat / curl / Compose UI tests** for logic verification
- **Screenshot only when visual state actually matters**
- **Delete old screenshots**: `rm /tmp/android_screen*.png`

## Checklist Before Claiming "Fixed" or "Complete"

- [ ] `./gradlew assembleDebug` → `BUILD SUCCESSFUL`
- [ ] `./gradlew test` → all unit tests pass
- [ ] `./gradlew connectedAndroidTest` → relevant UI tests pass (if applicable)
- [ ] Logcat shows no `FATAL EXCEPTION`, `error`, or crash entries for the feature
- [ ] Screenshot of final state matches design intent
- [ ] For animations: screen recording shows smooth transitions
- [ ] testTag modifiers on interactive elements (future-proofs Compose UI tests)
- [ ] Content descriptions on interactive elements (accessibility)

## Common Build Failures + Fixes

| Error | Likely cause | Fix |
|---|---|---|
| `Could not resolve dependency` | Missing or outdated dependency | `./gradlew --refresh-dependencies` |
| `Execution failed for task ':app:compileDebugKotlin'` | Kotlin compilation error | Read the error above the summary |
| `No connected devices` | Emulator not running | Boot with `emulator -avd <name>` |
| `INSTALL_FAILED_UPDATE_INCOMPATIBLE` | Signature mismatch with existing install | `adb uninstall <PACKAGE>` then reinstall |
| `Out of memory: GC overhead limit exceeded` | Gradle needs more heap | Add `org.gradle.jvmargs=-Xmx4g` to `gradle.properties` |
| `Duplicate class` | Dependency version conflict | Check dependency tree: `./gradlew dependencies` |

## Compose-Specific Verification Notes

- **Preview rendering** — Use `@Preview` in Android Studio for fast component iteration; emulator for full-screen flows
- **Dark mode** — Test both: `adb shell cmd uimode night yes` / `adb shell cmd uimode night no`
- **Font scale** — Test large text: `adb shell settings put system font_scale 1.5`
- **RTL layout** — Test: `adb shell settings put global debug.force_rtl 1`
- **Recomposition debugging** — Enable Layout Inspector in Android Studio or add `Modifier.debugInspectorInfo`

## Integration with NL Native

- **Pair with `/preview`** — this loop is what `/preview android` uses under the hood
- **Pair with `/steer`** — see something wrong in the screenshot, steer immediately
- **After checkpoint completion** — run this loop to verify the checkpoint before proceeding
- **Pair with `superpowers:systematic-debugging`** when a bug reproduces in emulator but root cause is unknown
