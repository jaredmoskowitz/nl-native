# Example: Notes App

This example walks through the NL Native workflow for a simple Notes app — creating and listing notes. It shows what each artifact looks like at each step of the `/propose` gate.

## The plain English prompt

> "I want users to be able to create notes with a title and body, see a list of their notes, and delete notes they no longer need."

That's it. That's the input. Everything below is what the propose gate produces from it.

## What gets generated

```
example/specs/changes/note-creation/
├── specs/core/
│   ├── features/notes.md          ← Spec Analyst output
│   ├── api-contracts/notes.md     ← Architect output
│   └── interactions/notes.md      ← UX Designer output
├── constraints/
│   ├── ios.md                     ← iOS Expert constraint report
│   ├── android.md                 ← Android Expert constraint report
│   └── backend.md                 ← Backend Expert constraint report
├── proposal.md                    ← Spec Analyst output
└── gate-review.md                 ← Architect gate review (approved)
```

## Workflow trace

1. Human types: `/propose note-creation`
2. Claude (as Spec Analyst) asks: "Describe the feature." Human gives the prompt above.
3. Spec Analyst writes `proposal.md` and `features/notes.md`
4. Human approves the feature spec
5. Architect writes `api-contracts/notes.md` (in parallel with step 6)
6. UX Designer writes `interactions/notes.md` (in parallel with step 5)
7. iOS Expert reads all specs, writes `constraints/ios.md`
8. Android Expert reads all specs, writes `constraints/android.md`
9. Backend Expert reads all specs, writes `constraints/backend.md`
10. UX Designer writes `ux-reconciliation.md` (in this example: no conflicts)
11. Architect writes `gate-review.md`
12. Human approves → runs `/fan-out`

## What happens after approval

After `/fan-out`:
- **iOS Expert** builds mock API client (protocol + fixture data), then SwiftUI views and view models
- **Android Expert** builds mock API client (interface + fake implementation), then Compose screens
- **Backend Expert** creates database migration, implements endpoints, adds access control
- All three work in parallel with no lateral communication
- iOS and Android use mock data so they don't block on the backend

During implementation, if the user doesn't like the direction:
- `/steer use a card layout instead of plain list rows` → amend mode (specific change)
- `/steer the note list feels cluttered` → diverge mode (shows 3 alternatives to pick from)

After `/verify` and `/archive`:
- Steer log is reviewed for recurring patterns → rules added to AGENTS.md (harness evolution)
