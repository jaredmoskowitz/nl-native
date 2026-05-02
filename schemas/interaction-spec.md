# Schema: Interaction Spec

Copy this template to `specs/changes/<change-name>/specs/core/interactions/<name>.md`.

The UX Designer writes interaction specs. They define behavior, not visual design. Platform experts translate behavioral specs into native idioms — you do not specify which components, layouts, or colors to use.

---

```markdown
# Interaction: [Feature or Screen Name]
Version: 1.0.0
Status: draft

## Overview

[One paragraph describing what user-facing experience this spec covers. What can the user do here? What does the system show and respond with?]

---

## States

Every interactive surface has explicit states. Define all of them.

### Loading
**Entry trigger:** [What causes the screen/component to enter a loading state]
**What the user sees:** [Described behaviorally — "content area is replaced with a loading indicator" not "show a spinner"]
**Blocking?:** [Does loading block all interaction, or only part of the screen?]
**Timeout behavior:** [After how long does loading become an error state? What happens?]

### Empty
**Entry trigger:** [When does this state occur? First launch? No results? Filtered to zero?]
**What the user sees:** [Described behaviorally — "a message and a primary action to create the first item"]
**Action available:** [What can the user do from the empty state?]

### Populated
**Entry trigger:** [Data is available and loaded]
**What the user sees:** [Described behaviorally — "a list of items in reverse chronological order"]
**Interactions available:** [What the user can do — tap, swipe, scroll, etc.]

### Error
**Entry trigger:** [Network failure, server error, auth expiry, etc. — list each separately if behavior differs]
**What the user sees:** [How is the error presented — inline, banner, modal? Is it dismissible?]
**Recovery action:** [What can the user do — retry, go back, contact support?]

### [Additional states specific to this feature]
[Add states as needed — e.g. Editing, Confirming, Submitting, Success]

---

## State transitions

| From | Event | To | Notes |
|---|---|---|---|
| — | Screen opens | Loading | Always starts loading |
| Loading | Data arrives | Populated | |
| Loading | Data arrives (empty) | Empty | |
| Loading | Network error | Error | |
| Loading | Timeout (>10s) | Error | Show "taking too long" message |
| Populated | User taps Create | [Screen/modal opens] | |
| Error | User taps Retry | Loading | |

[Add or remove rows as needed. Every state should have at least one exit transition.]

---

## Gestures and interactions

| Gesture | Target | Effect | Feedback |
|---|---|---|---|
| Tap | List item | Open item detail | System haptic: light |
| Swipe left | List item | Reveal delete action | None |
| Tap Delete | Revealed action | Confirm deletion | System haptic: medium on confirm |
| Pull down | List | Trigger refresh | Refresh control animation |
| Long press | List item | Enter multi-select mode | System haptic: medium |

[List every interactive gesture. Be explicit about feedback — haptic type, sound, animation.]

---

## Feedback

### Haptics
[Describe haptic feedback patterns — use system haptic types (light, medium, heavy, success, warning, error) rather than custom patterns.]

### Animations
[Describe timing and character of transitions — "items fade in staggered at 50ms intervals" not "use a spring animation."]

### Confirmations
[Describe any explicit confirmation steps — "destructive actions require a confirmation with the item name displayed."]

---

## Error presentation

| Error type | Presentation | Dismissible? | Recovery |
|---|---|---|---|
| Network unavailable | Inline banner at top | No (auto-dismisses when connectivity returns) | None needed |
| Server error (500) | Inline banner with retry | Yes | Retry button |
| Validation failure | Inline below each field | Yes (on correction) | Correct and resubmit |
| Auth expired | Modal (blocks UI) | No | Re-authenticate |
| Not found | Replace content area | No | Go back |

---

## Edge cases

- **Very long content:** [How does the UI handle unusually long text, names, or lists?]
- **Offline creation:** [If the user creates something offline, what happens? Queue locally? Block?]
- **Concurrent modification:** [If two sessions modify the same item, what wins?]
- **Rapid actions:** [If the user taps repeatedly or very fast, what happens? Debounce? Disable?]
- **[Feature-specific edge case]:** [Describe and specify behavior]

---

## Platform notes

[Document any known platform differences that platform experts should be aware of:]
- On iOS, [behavior X] is implemented as [idiom]. On Android, the equivalent is [idiom]. Both must produce [outcome Y].
- [Any behaviors that must be identical across platforms]
- [Any behaviors where platform-native variation is acceptable]
```

---

## Behavioral writing guide

**Do:** describe what the user experiences
> "When the user taps the item, it expands to reveal its detail. The expansion animates at 250ms. Items above and below shift to accommodate the new height."

**Don't:** describe components or implementation
> ~~"Use an accordion component. Set animation duration to 250ms. Apply layout animation to the RecyclerView."~~

**Do:** specify the outcome of every error
> "If the request fails, a non-blocking banner appears at the top of the screen with the message 'Couldn't save. Try again.' and a Retry button. The banner dismisses automatically after 5 seconds or on tap."

**Don't:** leave errors implicit
> ~~"Handle errors appropriately."~~

**Do:** define empty states explicitly
> "When the user has no items, the list area is replaced with a centered illustration, the text 'No items yet', and a primary button labeled 'Create your first item'."

**Don't:** forget about the zero state
> ~~"Show a list of items."~~
