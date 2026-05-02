Build the active feature, boot the simulator, and walk through key flows visually — capturing screenshots at each state defined in the interaction spec. Use this during or after `/fan-out` to see what's actually been built before running `/verify`.

**Usage:** `/preview` or `/preview ios` or `/preview android`

---

## Pre-flight

1. Find the active change: `specs/changes/<name>/`
2. Load the interaction spec: `$CHANGE/specs/core/interactions/*.md`
3. Load the feature spec: `$CHANGE/specs/core/features/*.md`
4. Determine which platform to preview (default: iOS if available, or ask)

---

## iOS Preview

### Step 1 — Build and launch

Read `platforms/ios/AGENTS.md` for the scheme name, bundle ID, and build commands.

```bash
# Build for simulator
xcodebuild -scheme <SCHEME> \
  -destination "platform=iOS Simulator,name=iPhone 16" \
  -configuration Debug \
  -derivedDataPath ./build \
  build

# Install and launch
xcrun simctl install booted ./build/Build/Products/Debug-iphonesimulator/<APP>.app
xcrun simctl launch booted <BUNDLE_ID>
```

If build fails, report the error and stop — don't try to preview broken code.

### Step 2 — Walk through interaction spec states

For each **state** defined in the interaction spec, in order:

1. Navigate to the state (via deep link if available, or MCP taps)
2. Wait for the state to settle (1-2 seconds)
3. Take a screenshot: `mcp__ios-simulator__screenshot`
4. Compare what you see against the interaction spec:
   - Does the state match what's specified?
   - Are the correct elements visible?
   - Is the layout reasonable?
5. Log the result

### Step 3 — Walk through key transitions

For each **transition** in the interaction spec:

1. Start from the "from" state
2. Trigger the transition event (tap, swipe, type, etc. via MCP tools)
3. Take a screenshot of the "to" state
4. Confirm the transition occurred as specified

### Step 4 — Check error states and edge cases

For each **error case** and **edge case** in the interaction spec:

1. If the state can be triggered from the current app state, trigger it
2. Screenshot the result
3. Note whether the error presentation matches the spec

---

## Android Preview

### Step 1 — Build and launch

Read `platforms/android/AGENTS.md` for the build commands.

```bash
# Build debug APK
cd platforms/android
./gradlew assembleDebug

# Install on running emulator
adb install -r app/build/outputs/apk/debug/app-debug.apk

# Launch
adb shell am start -n <PACKAGE>/<MAIN_ACTIVITY>
```

If no emulator is running:
```bash
# List available AVDs
emulator -list-avds

# Boot one
emulator -avd <AVD_NAME> &
adb wait-for-device
```

### Step 2 — Capture states

For each state in the interaction spec:

```bash
# Screenshot
adb exec-out screencap -p > /tmp/android_screen.png
# Then Read /tmp/android_screen.png
```

Navigate via:
- Deep links: `adb shell am start -a android.intent.action.VIEW -d "<URI>"`
- Tap by coordinates: `adb shell input tap <X> <Y>`
- Type text: `adb shell input text "<TEXT>"`
- Swipe: `adb shell input swipe <X1> <Y1> <X2> <Y2> <DURATION_MS>`

### Step 3 — Walk through transitions and error states

Same logic as iOS — trigger each transition, screenshot the result.

---

## Preview Report

Present a summary to the user:

```
Preview: <change-name> on <platform>
════════════════════════════════════

STATES
  Loading:     ✓ Renders correctly
  Empty:       ✓ Empty state message visible
  Populated:   ~ Title truncation looks off on long titles
  Error:       ✓ Error banner appears with retry button

TRANSITIONS
  Loading → Populated:    ✓ Data appears after fetch
  Populated → Refreshing: ✓ Pull-to-refresh indicator shows
  Tap item → Detail:      ✓ Navigation works

EDGE CASES
  Very long title:   ~ Truncates but ellipsis position is awkward
  Offline:           ✗ No offline state shown (spec says show banner)

SCREENSHOTS
  [Screenshots are inline above — review them visually]

RECOMMENDATION
  2 items to address before /verify:
  1. Long title truncation (minor — cosmetic)
  2. Offline state missing (spec violation — needs implementation)

  Run `/steer` to redirect, or fix and re-run `/preview`.
════════════════════════════════════
```

---

## Rules

- Max 1 screenshot per state — don't flood context
- If build fails, stop immediately and report the error — don't try to navigate a broken app
- Prefer deep links over sequential tapping for navigation
- Use MCP tools (ios-simulator) over cliclick — no mouse stealing
- For Android, use adb commands — they don't steal focus
- If a state can't be triggered from the current app state (e.g., requires specific server state), skip it and note "Could not trigger — requires [condition]"
- Preview is read-only — never fix code during preview. Report findings and let the user decide whether to `/steer` or fix directly.
