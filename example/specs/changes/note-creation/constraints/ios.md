# Platform Constraint Report: iOS
Change: note-creation
Date: 2026-04-26
Author: iOS Expert

## Summary

The note-creation feature is straightforward to implement on iOS. SwiftUI's sheet presentation handles the editor naturally. Swipe-to-delete is a native list gesture. No App Store restrictions apply. Complexity: Low.

## Constraints

### Swipe-to-delete gesture

**Requirement:** Interaction spec — delete gesture
**Severity:** Minor

**Issue:** The interaction spec specifies "Swipe left" to reveal delete on iOS. This is correct for iOS — `.swipeActions` in SwiftUI List provides exactly this. No constraint. Noting for transparency.

**Proposed alternative:** N/A — proceeding with swipe-to-reveal as specified.

**Impact:** None.

**Decision needed from:** None — no action required.

---

## Implementation notes

- The Note Editor will be presented as a `.sheet` on iOS, which supports the "swipe down to dismiss" gesture specified in the interaction spec. The `interactiveDismissDisabled` modifier will be set based on whether the editor is in the `Editing` state, ensuring the discard confirmation fires correctly.
- Pull-to-refresh is native in SwiftUI List via `.refreshable`.
- Relative timestamps will use `RelativeDateTimeFormatter` — no library needed.

## Estimated task breakdown

| Task | Effort |
|---|---|
| NotesViewModel (fetch, delete, create) | M |
| NotesView (list, states, gestures) | M |
| NoteEditorView + NoteEditorViewModel | M |
| APIClient integration (3 endpoints) | S |
| XCTest cases | M |
| **Total** | **M** |
