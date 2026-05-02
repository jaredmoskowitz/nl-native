# Interaction: Notes
Version: 1.0.0
Status: approved

## Overview

The notes experience consists of two surfaces: the Notes List (the primary screen) and the Note Editor (presented when creating a note). The interaction spec covers all states, transitions, and gestures for both surfaces.

---

## Notes List

### States

**Loading**
Entry trigger: Screen first opens, or user triggers a manual refresh.
What the user sees: The content area is replaced with a loading indicator. Navigation controls remain visible. No interaction with the list is possible.
Timeout: If loading exceeds 15 seconds with no response, transition to Error state.

**Empty**
Entry trigger: Fetch completes and returns zero notes.
What the user sees: A centered message ("No notes yet") and a single primary action ("Create your first note"). No list is shown.
Action available: Tapping the primary action opens the Note Editor.

**Populated**
Entry trigger: Fetch completes and returns one or more notes.
What the user sees: A scrollable list of note items, each showing: title (full), body preview (up to 2 lines, truncated with ellipsis), and relative timestamp. Items are ordered newest first.
Interactions: See Gestures section.

**Error**
Entry trigger: Fetch fails (network error, server error, timeout).
What the user sees: An error message ("Couldn't load notes") and a Retry button. The list content area is replaced — no partial list is shown.
Recovery: Tapping Retry returns to Loading state.

**Refreshing**
Entry trigger: User initiates a pull-to-refresh while in Populated state.
What the user sees: The list remains visible. A platform-native refresh indicator appears at the top.
On success: Transition to Populated with updated data.
On failure: Transition back to Populated with existing data, show a non-blocking error banner.

### State transitions

| From | Event | To | Notes |
|---|---|---|---|
| — | Screen opens | Loading | Always |
| Loading | Fetch succeeds, notes > 0 | Populated | |
| Loading | Fetch succeeds, notes = 0 | Empty | |
| Loading | Fetch fails or timeout | Error | |
| Populated | Pull gesture | Refreshing | |
| Refreshing | Fetch succeeds | Populated | Replace data |
| Refreshing | Fetch fails | Populated | Keep existing data, show error banner |
| Error | Tap Retry | Loading | |
| Any | Note created successfully | Populated | New note prepended to list |
| Any | Note deleted successfully | Populated (or Empty if last note) | |

### Gestures

| Gesture | Target | Effect | Feedback |
|---|---|---|---|
| Pull down | List | Enter Refreshing state | Platform-native refresh control |
| Tap | "Create" button / FAB | Open Note Editor | System haptic: light |
| Swipe left (iOS) / Long press (Android) | Note item | Reveal delete action | None |
| Tap Delete | Revealed action | Show deletion confirmation | System haptic: medium on confirmation |
| Tap item | Note item | No action in v1.0.0 (no detail view) | None |

*Note: Delete gesture is platform-native. iOS uses swipe-to-reveal. Android uses a long-press context action or contextual action bar. Both must result in a confirmation before deletion — the exact gesture is the platform expert's choice.*

---

## Note Editor

### States

**Empty**
Entry trigger: Editor opens.
What the user sees: Title field (focused, keyboard shown), body field below. A Save/Done action in the navigation. A dismiss/cancel action.
Keyboard: Title field receives focus immediately on open.

**Editing**
Entry trigger: User types in either field.
What the user sees: Same as Empty, with content in the fields. Save action is enabled only when title is non-empty.

**Saving**
Entry trigger: User taps Save with a valid title.
What the user sees: Save action is replaced with a loading indicator. Both fields become non-interactive.
Duration: Until server responds.
Timeout: If saving exceeds 15 seconds, transition to Save Error state.

**Save Error**
Entry trigger: Save request fails.
What the user sees: An inline error message ("Couldn't save. Try again.") with a Retry button. Fields are re-enabled with original content intact. No content is lost.

**Discard Confirmation**
Entry trigger: User attempts to dismiss the editor while Editing (content present).
What the user sees: A confirmation prompt ("Discard this note?") with two options: Discard (destructive) and Keep Editing.

### State transitions

| From | Event | To | Notes |
|---|---|---|---|
| — | User initiates creation | Empty | |
| Empty | User types | Editing | |
| Editing | User clears all content | Empty | |
| Editing | Tap Save (title non-empty) | Saving | |
| Empty | Tap Dismiss | [Editor closes] | No confirmation needed |
| Editing | Tap Dismiss | Discard Confirmation | |
| Discard Confirmation | Tap Discard | [Editor closes] | Draft is lost |
| Discard Confirmation | Tap Keep Editing | Editing | Resume editing |
| Saving | Save succeeds | [Editor closes] | Note added to list |
| Saving | Save fails | Save Error | |
| Save Error | Tap Retry | Saving | |

### Gestures and interactions

| Gesture | Target | Effect | Feedback |
|---|---|---|---|
| Tap | Title field | Focus title, show keyboard | None |
| Tap | Body field | Focus body, show keyboard | None |
| Tap | Save / Done | Begin save (if title non-empty) | System haptic: light on success |
| Tap | Dismiss / Cancel | Dismiss or confirm discard | None |
| Swipe down (iOS sheet) | Editor | Same as Dismiss | |

---

## Error presentation

| Error | Presentation | Position | Dismissible | Recovery |
|---|---|---|---|---|
| List fetch failure | Full-screen error state | Replaces list | No | Retry button |
| Refresh failure | Non-blocking banner | Top of list | Auto (5s) | None |
| Save failure | Inline in editor | Above keyboard | Yes (on retry) | Retry button |
| Delete failure | Non-blocking banner | Top of list | Auto (5s) | None |

---

## Edge cases

**Very long title:** Title field accepts up to 255 characters. Beyond that, input is blocked (no error — just stops accepting characters). In the list, titles longer than one line are truncated with ellipsis.

**Very long body:** Body field accepts up to 50,000 characters. In the list, body preview is always truncated at 2 lines regardless of length.

**Rapid tapping Save:** Save action becomes non-interactive the moment saving begins. Double-tap cannot create duplicate notes.

**Deletion of last note:** After deleting the last note, the list transitions to the Empty state.

**Network lost mid-save:** Treated as a Save failure. Editor remains open, content preserved, Retry available.
