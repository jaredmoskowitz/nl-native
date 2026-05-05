# SwipeClean Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build SwipeClean — a cross-platform native Gmail inbox cleaner with Tinder-style swiping — using the nl-native harness.

**Architecture:** Fully independent native apps (SwiftUI + Jetpack Compose), no backend. Gmail API accessed directly from device via OAuth. nl-native specs keep both platforms in sync.

**Tech Stack:** Swift 6.0+/SwiftUI, Kotlin 2.x+/Jetpack Compose, SwipeCardsKit (iOS), LazyCardStack (Android), Gmail API, Google Sign-In

**Design Spec:** `docs/superpowers/specs/2026-05-05-swipeclean-design.md`

---

### Task 1: Create SwipeClean Project

**Files:**
- Create: `../swipeclean/` (new project directory, sibling to nl-native)

- [ ] **Step 1: Scaffold the project directory**

```bash
mkdir -p ~/workspace/swipeclean
cp -r ~/workspace/nl-native/.claude ~/workspace/nl-native/agents ~/workspace/nl-native/schemas ~/workspace/swipeclean/
mkdir -p ~/workspace/swipeclean/platforms/{ios,android}
mkdir -p ~/workspace/swipeclean/specs/{core,changes}
```

- [ ] **Step 2: Initialize git**

```bash
cd ~/workspace/swipeclean
git init
echo ".superpowers/" >> .gitignore
git add -A
git commit -m "Initialize SwipeClean with nl-native harness"
```

- [ ] **Step 3: Copy the design spec into the project**

```bash
mkdir -p ~/workspace/swipeclean/docs/superpowers/specs
cp ~/workspace/nl-native/docs/superpowers/specs/2026-05-05-swipeclean-design.md ~/workspace/swipeclean/docs/superpowers/specs/
git add docs/
git commit -m "Add SwipeClean design spec"
```

---

### Task 2: Configure Google Cloud OAuth

This is a manual prerequisite — the nl-native agents can't do this for you.

- [ ] **Step 1: Create a Google Cloud project**

Go to https://console.cloud.google.com/. Create a new project named "SwipeClean".

- [ ] **Step 2: Enable required APIs**

In the Google Cloud Console, navigate to APIs & Services → Library. Enable:
- Gmail API
- People API

- [ ] **Step 3: Configure OAuth consent screen**

Navigate to APIs & Services → OAuth consent screen.
- User type: External
- App name: SwipeClean
- Scopes: `gmail.readonly`, `gmail.modify`, `gmail.settings.basic`, `contacts.readonly`
- Test users: add your own Gmail address for development

- [ ] **Step 4: Create OAuth client IDs**

Navigate to APIs & Services → Credentials → Create Credentials → OAuth client ID.

Create two credentials:
1. **iOS:** Application type = iOS. Bundle ID = `com.swipeclean.app` (or your preferred bundle ID). Save the Client ID.
2. **Android:** Application type = Android. Package name = `com.swipeclean.app`. SHA-1 fingerprint from your debug keystore (`keytool -list -v -keystore ~/.android/debug.keystore -alias androiddebugkey -storepass android`). Save the Client ID.

- [ ] **Step 5: Record credentials**

Save the client IDs somewhere local (not committed to git). You'll reference them in the platform AGENTS.md files. Do NOT commit these to the repo.

---

### Task 3: Write iOS AGENTS.md

**Files:**
- Create: `platforms/ios/AGENTS.md`

- [ ] **Step 1: Write the iOS platform configuration**

Write `~/workspace/swipeclean/platforms/ios/AGENTS.md`:

```markdown
# iOS: AGENTS.md

## Platform

**Minimum deployment target:** iOS 17.0
**Swift version:** 6.0+
**UI framework:** SwiftUI (no UIKit except for haptics via UIImpactFeedbackGenerator)
**Architecture:** MVVM with @Observable

## Project Structure

platforms/ios/SwipeClean/
├── App/
│   └── SwipeCleanApp.swift
├── Features/
│   ├── Welcome/
│   │   └── WelcomeView.swift
│   ├── Auth/
│   │   ├── AuthViewModel.swift
│   │   └── AuthView.swift
│   ├── Scanning/
│   │   ├── ScanningViewModel.swift
│   │   └── ScanningView.swift
│   ├── SwipeDeck/
│   │   ├── SwipeDeckViewModel.swift
│   │   ├── SwipeDeckView.swift
│   │   ├── EmailCardView.swift
│   │   └── StampOverlayView.swift
│   └── Stats/
│       ├── StatsViewModel.swift
│       └── StatsView.swift
├── Services/
│   ├── GmailService.swift          # Protocol + real implementation
│   ├── MockGmailService.swift      # Mock for fan-out phase
│   ├── ContactsService.swift       # People API for contacts check
│   ├── UnsubscribeService.swift    # List-Unsubscribe handler
│   └── SuspicionScorer.swift       # Email scoring logic
├── Models/
│   ├── EmailSender.swift
│   ├── EmailCard.swift
│   ├── SwipeDecision.swift
│   └── ScanSession.swift
├── Storage/
│   ├── DecisionStore.swift         # Persisted sender decisions
│   └── SessionHistoryStore.swift
└── Utilities/
    ├── HapticManager.swift
    └── KeychainHelper.swift

## Dependencies

- **SwipeCardsKit** (SPM) — https://github.com/tobi404/SwipeCardsKit — Tinder-style swipeable card stack
  - Fallback if issues: CardStackView — https://github.com/dadalar/SwiftUI-CardStackView
- **Google Sign-In for iOS** (SPM) — Google OAuth with Gmail scopes
- No other third-party dependencies. Use Foundation/SwiftUI for everything else.

## Auth

- Google Sign-In SDK handles the OAuth flow
- Request scopes: gmail.readonly, gmail.modify, gmail.settings.basic, contacts.readonly
- Store OAuth tokens in Keychain via KeychainHelper
- Token refresh handled by Google Sign-In SDK
- On token expiry, prompt re-authentication

## Conventions

- @Observable for all view models (not ObservableObject)
- @MainActor on all view models
- async/await for all async work — no Combine, no DispatchQueue
- No force unwrapping anywhere
- No UIKit except UIImpactFeedbackGenerator for haptics
- SF Symbols for all icons: envelope, shield.slash, checkmark.circle, arrow.uturn.backward, party.popper
- Respect Dynamic Type — no hardcoded font sizes, use .title, .headline, .body, .caption
- Dark mode is default but respect system appearance setting

## Craft & Animation Requirements

These are binding constraints — the iOS Expert MUST implement all of them:

### Card Physics
- Use spring-based animation for card movement (.spring(response: 0.4, dampingFraction: 0.7))
- Cards rotate during drag: rotation angle = drag offset.x / 20, capped at ±15°
- Throw velocity determines dismiss vs snap-back: threshold at 500 pts/sec
- Cards behind the top card peek with progressive scale (0.95, 0.9) and offset

### Color Bleed
- As the card is dragged, apply a gradient overlay that scales with drag distance
- Swipe right: mint→cyan gradient on right edge, opacity = min(abs(offset.x) / 150, 0.6)
- Swipe left: coral→orange gradient on left edge, same opacity formula
- Swipe down: indigo→blue gradient on bottom edge, opacity = min(abs(offset.y) / 150, 0.6)

### Stamp Overlay
- When drag crosses the threshold (150pt), fade in a tilted text stamp on the card
- "BLOCKED" in coral-orange, rotated -15°, font .largeTitle bold
- "KEPT" in mint-green, rotated 15°
- "UNSUBSCRIBED" in indigo-blue, rotated 0°, with "Can't be undone" subtitle below
- Opacity animates from 0 to 1 as threshold is crossed

### Haptics
- UIImpactFeedbackGenerator(.light) when crossing swipe threshold
- UIImpactFeedbackGenerator(.medium) when card is dismissed
- UINotificationFeedbackGenerator(.success) on unsubscribe

### Completion Celebration
- When deck empties: "Inbox Cleaned!" text with .spring animation
- Stats counters animate from 0 to final value over 1.2 seconds
- Use a simple confetti-like particle effect (custom SwiftUI view with randomized falling shapes)

### Loading States
- Scanning screen: animated envelope icon (SF Symbol with .symbolEffect(.pulse))
- Live counter ticking up as emails are analyzed
- Skeleton card shapes building behind the counter

### Toast Notifications
- Slide in from top, auto-dismiss after 3 seconds
- Stack vertically if multiple in-flight
- Include "Undo" button that triggers the undo flow

## Data Privacy

- No email content is stored on disk. Email data is fetched from Gmail API, displayed, and discarded after the swipe decision.
- Only sender addresses and decisions are persisted locally.
- OAuth tokens are stored in Keychain — never in UserDefaults or plain files.

## Testing

- XCTest for unit tests
- Test view models with mock services injected via protocol
- Test SuspicionScorer with known fixture data
- Test DecisionStore persistence (UserDefaults or file-based)
```

- [ ] **Step 2: Commit**

```bash
cd ~/workspace/swipeclean
git add platforms/ios/AGENTS.md
git commit -m "Add iOS platform configuration with craft requirements"
```

---

### Task 4: Write Android AGENTS.md

**Files:**
- Create: `platforms/android/AGENTS.md`

- [ ] **Step 1: Write the Android platform configuration**

Write `~/workspace/swipeclean/platforms/android/AGENTS.md`:

```markdown
# Android: AGENTS.md

## Platform

**Minimum SDK:** 26 (Android 8.0)
**Target SDK:** 35
**Kotlin version:** 2.x+
**UI framework:** Jetpack Compose with Material 3
**Architecture:** MVVM with StateFlow, Hilt for DI

## Project Structure

platforms/android/app/src/main/java/com/swipeclean/app/
├── SwipeCleanApp.kt                    # Application class, Hilt entry point
├── MainActivity.kt
├── navigation/
│   └── SwipeCleanNavGraph.kt
├── features/
│   ├── welcome/
│   │   └── WelcomeScreen.kt
│   ├── auth/
│   │   ├── AuthViewModel.kt
│   │   └── AuthScreen.kt
│   ├── scanning/
│   │   ├── ScanningViewModel.kt
│   │   └── ScanningScreen.kt
│   ├── swipedeck/
│   │   ├── SwipeDeckViewModel.kt
│   │   ├── SwipeDeckScreen.kt
│   │   ├── EmailCardComposable.kt
│   │   └── StampOverlay.kt
│   └── stats/
│       ├── StatsViewModel.kt
│       └── StatsScreen.kt
├── services/
│   ├── GmailService.kt                 # Interface + real implementation
│   ├── MockGmailService.kt             # Mock for fan-out phase
│   ├── ContactsService.kt              # People API for contacts check
│   ├── UnsubscribeService.kt           # List-Unsubscribe handler
│   └── SuspicionScorer.kt              # Email scoring logic
├── models/
│   ├── EmailSender.kt
│   ├── EmailCard.kt
│   ├── SwipeDecision.kt
│   └── ScanSession.kt
├── storage/
│   ├── DecisionStore.kt                # DataStore for sender decisions
│   └── SessionHistoryStore.kt
└── utilities/
    ├── HapticManager.kt
    └── EncryptedPrefsHelper.kt

## Dependencies

- **LazyCardStack** — https://github.com/Hukumister/LazyCardStack — Tinder-style card stack for Compose
  - Fallback if issues: compose-tinder-card — https://github.com/alexstyl/compose-tinder-card
- **Google Identity Services** — Credential Manager API for Google Sign-In
- **Gmail API Client** — com.google.apis:google-api-services-gmail
- **Hilt** — dependency injection
- **Jetpack DataStore** — for persisted decisions and session history
- **EncryptedSharedPreferences** — for OAuth token storage
- No other third-party dependencies.

## Auth

- Google Identity Services (Credential Manager) handles the OAuth flow
- Request scopes: gmail.readonly, gmail.modify, gmail.settings.basic, contacts.readonly
- Store OAuth tokens in EncryptedSharedPreferences
- Token refresh handled by Google Identity Services
- On token expiry, prompt re-authentication

## Conventions

- Jetpack Compose for all UI — no XML layouts
- StateFlow for all view model state
- Coroutines for all async work
- Hilt for dependency injection — interfaces bound to implementations in modules
- Material 3 Dynamic Color — use MaterialTheme.colorScheme everywhere
- Material Icons for all icons
- Edge-to-edge display: use WindowInsets padding
- Predictive back gesture compatible: use Compose navigation's built-in support
- Follow Material You theming conventions

## Craft & Animation Requirements

These are binding constraints — the Android Expert MUST implement all of them:

### Card Physics
- Use Compose Animatable with spring spec for card movement (Spring(dampingRatio = 0.7f, stiffness = 400f))
- Cards rotate during drag: rotation = offsetX / 20f, capped at ±15°
- Throw velocity determines dismiss vs snap-back: threshold at 500 dp/sec
- Cards behind top card peek with progressive scale (0.95f, 0.9f) and offset

### Color Bleed
- As the card is dragged, apply a gradient overlay brush that scales with drag distance
- Swipe right: mint→cyan on right edge, alpha = min(abs(offsetX) / 150f, 0.6f)
- Swipe left: coral→orange on left edge, same alpha formula
- Swipe down: indigo→blue on bottom edge, alpha = min(abs(offsetY) / 150f, 0.6f)

### Stamp Overlay
- When drag crosses threshold (150dp), fade in tilted text stamp on card
- "BLOCKED" in coral-orange, rotated -15°, MaterialTheme.typography.displaySmall bold
- "KEPT" in mint-green, rotated 15°
- "UNSUBSCRIBED" in indigo-blue, rotated 0°, with "Can't be undone" subtitle
- Alpha animates from 0 to 1 as threshold is crossed

### Haptics
- HapticFeedbackType.LongPress equivalent (performHapticFeedback) when crossing threshold
- VibrationEffect.createOneShot(50, VibrationEffect.DEFAULT_AMPLITUDE) on dismiss
- VibrationEffect.createWaveform for success on unsubscribe

### Completion Celebration
- When deck empties: "Inbox Cleaned!" with spring animation
- Stats counters animate from 0 to final value using animateIntAsState over 1.2 seconds
- Simple confetti effect: custom Canvas composable with randomized falling shapes

### Loading States
- Scanning screen: animated envelope icon (use Compose animation on an icon)
- Live counter ticking up with animateIntAsState
- Skeleton card shapes building behind counter (shimmer composable)

### Toast Notifications
- Snackbar from top of screen (custom positioned), auto-dismiss after 3 seconds
- Stack vertically if multiple in-flight
- Include "Undo" action that triggers the undo flow

## Data Privacy

- No email content is stored on disk. Email data is fetched from Gmail API, displayed, and discarded after the swipe decision.
- Only sender addresses and decisions are persisted locally.
- OAuth tokens are stored in EncryptedSharedPreferences — never in plain SharedPreferences or files.

## Testing

- JUnit 5 for unit tests
- Test view models with mock services injected via Hilt test modules
- Test SuspicionScorer with known fixture data
- Test DecisionStore persistence
- Compose UI tests with ComposeTestRule for swipe gesture verification
```

- [ ] **Step 2: Commit**

```bash
cd ~/workspace/swipeclean
git add platforms/android/AGENTS.md
git commit -m "Add Android platform configuration with craft requirements"
```

---

### Task 5: Handle the No-Backend Situation

SwipeClean has no backend server — Gmail API is called directly from mobile clients. The nl-native `/fan-out` command expects `platforms/backend/AGENTS.md` and launches a Backend Expert agent. We need to handle this gracefully.

**Files:**
- Create: `platforms/backend/AGENTS.md`

- [ ] **Step 1: Create a backend AGENTS.md that signals "no backend"**

Write `~/workspace/swipeclean/platforms/backend/AGENTS.md`:

```markdown
# Backend: AGENTS.md

## Service

**Primary service:** None — no backend server for this project.

## Architecture

SwipeClean accesses the Gmail API and Google People API directly from the mobile clients via OAuth. There is no backend server, no database, no serverless functions.

All data is stored on-device:
- Sender decisions (kept/blocked/unsubscribed) — persisted locally
- OAuth tokens — stored in platform-secure storage (Keychain / EncryptedSharedPreferences)
- Session history — stored locally

## Backend Expert Instructions

**Skip implementation for this feature.** There are no endpoints to implement, no database to set up, no server code to write.

When `/fan-out` runs:
1. Write a minimal implementation spec acknowledging no backend work is needed
2. Write a task list with a single completed task: "No backend — Gmail API accessed directly from clients"
3. Mark all tasks complete immediately

The API contracts in the spec describe the Gmail REST API (an external Google service), not endpoints we build. The iOS and Android experts handle Gmail API calls directly using the Google client libraries.
```

- [ ] **Step 2: Commit**

```bash
cd ~/workspace/swipeclean
mkdir -p platforms/backend
git add platforms/backend/AGENTS.md
git commit -m "Add backend AGENTS.md — no backend, direct Gmail API access"
```

---

### Task 6: Run /propose swipeclean

Open Claude Code in `~/workspace/swipeclean` and run the nl-native proposal workflow.

- [ ] **Step 1: Run /propose**

```
/propose swipeclean
```

When the Spec Analyst asks you to describe the feature, point it to the design spec:

"Read the design spec at `docs/superpowers/specs/2026-05-05-swipeclean-design.md`. It contains the complete feature description, swipe actions, card design, feed logic, Gmail API scopes, screens, undo behavior, craft requirements, and platform-native polish details. Use this as the source for the proposal."

- [ ] **Step 2: Review generated artifacts**

The `/propose` workflow will produce these artifacts in `specs/changes/swipeclean/`:
- `proposal.md` — feature summary
- `specs/core/features/swipeclean.md` — EARS requirements
- `specs/core/api-contracts/swipeclean.md` — Gmail API contract (documenting the external API we consume, not build)
- `specs/core/data-models/swipeclean.md` — local data models (EmailSender, SwipeDecision, ScanSession)
- `specs/core/interactions/swipeclean.md` — full interaction spec with all states, transitions, gestures
- `constraints/ios.md` and `constraints/android.md`
- `ux-reconciliation.md`
- `gate-review.md`

- [ ] **Step 3: Review and approve the gate**

Review each artifact. Pay special attention to:
- The interaction spec has all 5 screens with all states defined
- The EARS requirements capture every swipe action, undo behavior, and feed logic rule
- The craft requirements from the design spec made it into the interaction spec
- Platform constraints are reasonable

When satisfied, approve the gate. The Architect will say: "Gate approved. Run `/fan-out` to begin implementation."

---

### Task 7: Run /fan-out

- [ ] **Step 1: Run /fan-out**

```
/fan-out
```

This launches three agents in parallel:
1. **iOS Expert** — reads `platforms/ios/AGENTS.md`, writes implementation spec + task list, then builds the SwiftUI app with SwipeCardsKit
2. **Android Expert** — reads `platforms/android/AGENTS.md`, writes implementation spec + task list, then builds the Compose app with LazyCardStack
3. **Backend Expert** — reads the no-backend AGENTS.md, writes a minimal spec, marks complete immediately

The iOS and Android experts will build against mock Gmail services during this phase. This is expected — the mock→real swap happens later.

- [ ] **Step 2: Monitor progress**

Use `/status` to check progress during fan-out. Watch for:
- Both platforms writing their implementation specs first (before coding)
- Task list checkpoints being committed
- Any constraint issues surfaced during implementation

- [ ] **Step 3: Steer if needed**

If anything looks off during implementation, use `/steer` with specific feedback:

```
/steer the card animation feels too stiff, loosen the spring damping
/steer the scanning screen needs more visual interest
```

---

### Task 8: Wire Mock Gmail Services to Real Implementation

After fan-out completes, both platforms have working apps with mock data. Now wire up the real Gmail API.

- [ ] **Step 1: Verify fan-out completion**

Run `/status` and confirm all platform tasks are checked off.

- [ ] **Step 2: Replace mock services**

Since there's no backend server, `/connect` won't fully apply. Instead, manually guide each platform expert to:

1. Replace `MockGmailService` with the real `GmailService` implementation that calls the Gmail REST API
2. Replace `MockContactsService` with real People API calls
3. Wire the real Google Sign-In flow (using the OAuth client IDs from Task 2)
4. Test with a real Gmail account

Use `/steer` to direct this:

```
/steer replace the mock Gmail service with the real Gmail REST API implementation using the Google client library. Use the OAuth tokens from Google Sign-In to authenticate API calls.
```

---

### Task 9: Preview, Verify, Archive

- [ ] **Step 1: Preview on simulators**

```
/preview
```

Walk through all 5 screens on both iOS Simulator and Android Emulator. Verify:
- Welcome screen appears on first launch
- Google Sign-In flow works
- Scanning animation plays with counter
- Swipe deck shows cards with all content (sender, subject, preview, count, badge)
- Swipe right/left/down all work with correct color bleed, stamps, haptics
- Undo animates the card back
- Stats screen shows correct counts with celebration animation
- Progress bar updates correctly

- [ ] **Step 2: Verify spec compliance**

```
/verify
```

Phase A: per-platform compliance check
Phase B: cross-platform coherence check

Fix any BLOCKERs surfaced by the QA Verifier.

- [ ] **Step 3: Archive**

```
/archive
```

Merges specs into baseline, extracts patterns, reviews steer log for permanent rules.

---

### Task 10: Test with Real Gmail Account

- [ ] **Step 1: Build and install on a device or simulator**

Build both apps and install. Sign in with a real Gmail account (one of the test users from the Google Cloud OAuth consent screen).

- [ ] **Step 2: Verify end-to-end flow**

1. Sign in → OAuth consent screen shows correct scopes
2. Scanning fetches real emails and groups by sender
3. Suspicious senders appear first (newsletters, promotions, unknown senders)
4. Swipe left on a sender → verify a Gmail filter is created (check Gmail settings)
5. Swipe down on a sender with List-Unsubscribe → verify the unsubscribe POST is sent
6. Swipe right → verify sender is recorded locally and excluded from next scan
7. Undo a block → verify the Gmail filter is removed
8. Complete the deck → verify stats are accurate
9. "Scan Again" → verify new senders appear (excluding already-decided ones)

- [ ] **Step 3: Fix any issues found**

Use `/steer` for spec-level issues or direct code fixes for implementation bugs.
