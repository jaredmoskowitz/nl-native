# Platform Constraint Report: Android
Change: note-creation
Date: 2026-04-26
Author: Android Expert

## Summary

The feature maps well to Android idioms. The one notable difference is the delete gesture — Android does not have a native swipe-to-reveal pattern equivalent to iOS. The interaction spec already anticipated this with the "Long press (Android)" alternative. No blockers. Complexity: Low.

## Constraints

### Delete gesture — no swipe-to-reveal equivalent

**Requirement:** Interaction spec — delete gesture
**Severity:** Minor

**Issue:** iOS uses swipe-left to reveal a Delete action. Android does not have an equivalent native gesture in Jetpack Compose. Swipe-to-dismiss exists (SwipeToDismissBox) but removes the item immediately — it doesn't reveal an action button.

**Proposed alternative:** Long-press on a note item enters a contextual action mode, showing a Delete option in a contextual action bar or as a floating action. This is the Android-native pattern for destructive list actions.

**Impact:** The delete gesture differs between platforms (swipe on iOS, long-press on Android). The outcome is identical: a confirmation dialog appears before deletion. Experiential equivalence is maintained; gesture parity is not — which is correct per the UX designer's note in the interaction spec.

**Decision needed from:** None — the interaction spec already anticipates this with "(iOS) / Long press (Android)".

---

## Implementation notes

- `BottomSheetScaffold` or a `ModalBottomSheet` is the natural Android equivalent for the note editor sheet.
- Pull-to-refresh uses Compose's `PullToRefreshBox` (available in Compose BOM 2024+).
- Relative timestamps will use `DateUtils.getRelativeTimeSpanString()` — no library needed.
- The Note Editor's discard confirmation will use a Material 3 `AlertDialog`.

## Estimated task breakdown

| Task | Effort |
|---|---|
| NotesViewModel (fetch, delete, create with StateFlow) | M |
| NotesScreen composable (list, states, gestures) | M |
| NoteEditorBottomSheet composable + ViewModel | M |
| Ktor client integration (3 endpoints) | S |
| JUnit 5 + MockK tests | M |
| **Total** | **M** |
