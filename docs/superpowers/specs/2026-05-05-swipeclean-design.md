# SwipeClean — Design Spec

A cross-platform native app that lets users clean their Gmail inbox by swiping through emails from suspicious/unknown senders. Swipe right to keep, swipe left to block, swipe down to unsubscribe.

## Architecture

**Approach:** Fully independent native apps — pure SwiftUI on iOS, pure Kotlin/Jetpack Compose on Android. No shared code. nl-native specs keep them in sync.

**No backend.** Both apps talk directly to the Gmail API via OAuth from the device. Email filtering and suspicion scoring happen on-device.

### Tech Stack

| Platform | Language | UI Framework | Swiping Library | Auth |
|----------|----------|-------------|-----------------|------|
| iOS | Swift 6.0+, iOS 17.0+ | SwiftUI | [SwipeCardsKit](https://github.com/tobi404/SwipeCardsKit) | Google Sign-In SDK |
| Android | Kotlin 2.x+ | Jetpack Compose | [LazyCardStack](https://github.com/Hukumister/LazyCardStack) | Google Identity Services |

**Alternatives considered:**
- SwiftUI: [CardStackView](https://github.com/dadalar/SwiftUI-CardStackView) — similar API, also viable
- Compose: [compose-tinder-card](https://github.com/alexstyl/compose-tinder-card) — Modifier-based approach, lighter weight

## Swipe Actions

| Direction | Action | Gmail API Call | Reversible |
|-----------|--------|---------------|------------|
| Right | Keep — sender is fine | None (local record only) | Yes |
| Left | Block sender | Create filter: skip inbox + trash | Yes (remove filter) |
| Down | Unsubscribe + block | HTTP POST to List-Unsubscribe URL, then create block filter | Partially (block reversible, unsubscribe is not) |

Swipe down is only available when the email has a `List-Unsubscribe` header with a `mailto:` or HTTP POST option per RFC 8058.

## Email Card Design

Each card in the swipe deck represents one sender. The card displays the most recent email from that sender.

### Card Contents

- **Sender avatar** — first letter of sender name, colored with a deterministic gradient based on email address
- **Sender name** — bold, prominent
- **Sender email address** — muted, below the name
- **Subject line** — of the most recent email
- **Body preview** — first ~150 characters of the email body
- **Email count** — "23 emails from this sender"
- **Engagement indicator** — "never replied" if user has never sent to this address
- **Unsubscribe badge** — blue badge with "Unsubscribe ↓" when List-Unsubscribe is available
- **Swipe hints** — subtle directional labels at bottom of card: "← Block", "↓ Unsubscribe", "Keep →"

## Feed Logic — Suspicion Scoring

The app fetches email metadata from Gmail, groups by sender, and scores each sender to build the swipe deck. Higher scores appear first.

### Scoring Signals

| Signal | Weight | Reasoning |
|--------|--------|-----------|
| Never replied to sender | High | One-way senders are likely newsletters/spam |
| High email volume from sender | High | Frequent automated senders |
| Has List-Unsubscribe header | Medium | Mailing lists, not personal email |
| Gmail "Promotions" category | Medium | Gmail already classifies it as promotional |
| Sender not in contacts | Low | Unknown but could be legitimate |
| Email never opened | Low | User doesn't engage with these |

### Feed Rules

- Emails are grouped by sender
- One card per sender (the most recent email)
- Scored by suspicion signals, highest first
- Senders already decided on (kept or blocked in a previous session) are excluded
- Only emails from the inbox are considered (not sent, drafts, trash)

## Gmail API Scopes

| Scope | Purpose |
|-------|---------|
| `gmail.readonly` | Read emails, headers, metadata |
| `gmail.modify` | Create filters, block senders |
| `gmail.settings.basic` | Manage filters for blocking |
| `contacts.readonly` (People API) | Check if sender is in user's contacts |

## Screens & User Flow

### Screen 1: Welcome

- Shown only on first launch
- App logo and tagline
- Brief explanation: "Swipe away spam and unwanted emails"
- Single "Get Started" CTA

### Screen 2: Google Sign-In

- Standard Google OAuth consent flow
- Requests all four scopes
- Error state if user denies scopes — explains why each is needed
- Token stored securely: Keychain on iOS, EncryptedSharedPreferences on Android

### Screen 3: Loading / Scanning

- Animated envelope icon being sorted (not a generic spinner)
- Live counter ticking up: "Scanning... 247 emails analyzed"
- Groups by sender, computes suspicion scores
- Builds the swipe deck from highest to lowest score
- Skeleton card stack building behind the counter as a preview

### Screen 4: Swipe Deck (Core Screen)

- Card stack with top card fully visible, next 2-3 cards peeking behind
- Swipe right (keep), left (block), down (unsubscribe when available)
- Color tint bleeds into card edges on drag: green right, red left, blue down
- Stamp overlay ("BLOCKED" / "KEPT" / "UNSUBSCRIBED") fades in past the swipe threshold
- Swipe-down stamp includes a warning line: "Can't be undone" beneath "UNSUBSCRIBED"
- Progress bar at top: "12 of 45 senders reviewed"
- Undo button below the card stack (single level)
- Toast notification after each Gmail API action: "Blocked sender@spam.com" with undo link
- Empty state when deck is done → transitions to Stats screen

### Screen 5: Stats / Summary

- Session summary: blocked count, kept count, unsubscribed count
- Total emails affected: "Cleaned up 156 emails from 12 blocked senders"
- Confetti burst animation on arrival, stats counters animate up
- "Scan Again" button to re-fetch and find new senders
- "Done" button to close
- History of past sessions accessible from here

## Undo Behavior

- Single-level undo (last action only)
- **Block undo:** removes the Gmail filter, card animates back onto the stack
- **Keep undo:** removes local record, card animates back
- **Unsubscribe undo:** cannot undo the HTTP unsubscribe request, but can remove the block filter. User is warned that unsubscribe cannot be reversed before the card is dismissed.
- Undo animation: card flies back from off-screen with deceleration curve, stack shuffles to make room

## Craft & Interaction Design

### Visual Identity

- **Theme:** Rich dark mode — deep backgrounds (#0f0f1a), elevated card surfaces (#1e1e2e), not flat black
- **Accent gradients:**
  - Keep/positive: mint → cyan
  - Block/danger: coral → orange
  - Unsubscribe/info: indigo → blue
- **Typography:** SF Pro Display on iOS, Inter (or system default) on Android. Clear hierarchy — sender name bold, email muted, subject medium weight, body preview at lower opacity.
- **Follows system appearance** — dark mode by default, respects light mode if set

### Micro-Interactions

- **Card physics:** Spring-based animation with velocity tracking. Cards rotate ±15° max as dragged. Throw velocity determines dismiss vs. snap-back.
- **Color bleed:** Gradient tint bleeds into card edges during drag. Opacity scales with drag distance. Gives instant directional feedback.
- **Haptics:**
  - Light impact when crossing the swipe threshold
  - Medium impact on card dismiss
  - Success notification haptic on unsubscribe
- **Stamp overlay:** "BLOCKED" or "KEPT" text stamp fades in on the card past the swipe threshold — tilted, bold, colored. Confirms intent before release.
- **Undo animation:** Card flies back from off-screen with deceleration. Stack shuffles to make room. Feels like rewinding time.
- **Completion celebration:** Confetti burst + "Inbox Cleaned!" with stats counters animating up when deck is empty.

### Loading & Empty States

- **Scanning:** Animated envelope sorting narrative with live counter. Skeleton card stack building. Not a spinner.
- **All clean:** Peaceful illustration + "Your inbox looks clean!" with sparkle animation. Secondary action: "Scan with lower threshold."
- **Network error:** Friendly illustration, not a red alert. "Couldn't reach Gmail." Retry button. Preserves session progress.
- **Action feedback:** Subtle toast after each Gmail API action. Stacks if multiple in-flight. Auto-dismisses after 3 seconds. Includes undo link.

### Platform-Native Polish

**iOS:**
- UIImpactFeedbackGenerator for all haptics
- SF Symbols for all icons (envelope, shield.slash, checkmark.circle)
- Native SwiftUI spring animations (.spring())
- Keychain for OAuth token storage
- Respects Dynamic Type for accessibility
- Swipe gesture integrates with iOS back-swipe without conflict

**Android:**
- Material 3 Dynamic Color (accent from wallpaper)
- Material Icons for all icons
- Compose spring animations (Animatable)
- EncryptedSharedPreferences for token storage
- Predictive back gesture compatible
- Edge-to-edge display with proper window insets
- Material You theming conventions

## Data Storage

All local, on-device:

- **Decided senders:** list of sender addresses with their decision (kept/blocked/unsubscribed) and timestamp. Persisted so they're excluded from future scans.
- **OAuth tokens:** Keychain (iOS) / EncryptedSharedPreferences (Android)
- **Session history:** past scan results (counts, dates) for the Stats screen
- **No email content is stored.** Email data is fetched from Gmail API, displayed, and discarded after the swipe decision.

## Out of Scope for v1

- Multiple Gmail account support
- Scheduled/automatic scanning
- Whitelist management (editing past keep/block decisions)
- Email content search or filtering within the app
- Light mode custom theme (follows system only)
- Backend or cloud sync
- Batch operations (select multiple and block)
