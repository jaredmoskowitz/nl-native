Redirect implementation mid-flight when the approach, UI, or behavior isn't right. This command works during or after `/fan-out` — it's how you course-correct without restarting the full `/propose` cycle.

`/steer` auto-detects which mode to use based on your feedback. You don't need to think about it.

**Usage:** `/steer <your feedback>`

Examples:
- `/steer use a bottom sheet instead of a full-screen modal for note creation`
- `/steer the note list feels wrong`
- `/steer both platforms should use tab navigation, not a hamburger menu`
- `/steer the backend should batch the notification calls instead of firing them individually`

---

## Pre-flight

1. Find the active change: `specs/changes/<name>/` with task lists present
2. Load into context:
   - `$CHANGE/specs/core/features/*.md`
   - `$CHANGE/specs/core/api-contracts/*.md`
   - `$CHANGE/specs/core/data-models/*.md`
   - `$CHANGE/specs/core/interactions/*.md`
   - `$CHANGE/tasks/ios-tasks.md`
   - `$CHANGE/tasks/android-tasks.md`
   - `$CHANGE/tasks/backend-tasks.md`
   - `$CHANGE/steer-log.md` (if exists — prior steering decisions)
3. Read the checkpoint history: `$CHANGE/checkpoints.md` (if exists)

---

## Detect mode

Analyze the user's feedback to determine the appropriate mode. **Do not ask the user which mode to use** — decide based on the input.

### → Amend mode

Use when the feedback is **specific and actionable** — the user can describe what they want changed.

Signals:
- Names a concrete component, pattern, or behavior ("use a bottom sheet", "switch to tab navigation")
- References a specific screen or flow ("the creation flow should...")
- Describes a technical change ("batch the API calls", "use pagination instead of infinite scroll")
- Gives a before/after ("instead of X, do Y")

### → Diverge mode

Use when the feedback is **vague or aesthetic** — the user knows something is wrong but can't specify the fix.

Signals:
- Emotional or subjective language ("feels wrong", "doesn't look right", "too cluttered", "not what I had in mind")
- No concrete alternative proposed
- References overall feel rather than specific components ("the whole list experience", "the flow")
- Asks a question rather than making a statement ("is there a better way to do this?")

### → Clarify (rare)

If genuinely ambiguous — the feedback could be either specific or vague depending on interpretation — ask **one** question:

"I can make a specific change to the spec, or I can show you a few alternative approaches to pick from. Which would be more helpful here?"

---

## Amend mode

### Step 1 — Scope the change

Determine what kind of change this is:

| Change type | Routes through | Affects |
|---|---|---|
| Behavioral (UI flow, states, transitions, gestures) | UX Designer | Interaction spec → platform tasks |
| Structural (endpoints, data shapes, auth) | Architect | API contract or data model → all platform tasks |
| Implementation (approach, pattern, library choice) | Direct to platform expert(s) | Platform tasks only — no spec change |

### Step 2 — Produce the spec delta

**For behavioral changes:** Act as the UX Designer. Read the current interaction spec. Produce a targeted amendment — not a full rewrite, just the diff:

```markdown
## Steer Amendment: [short description]
Date: [date]
Type: behavioral
Triggered by: [user's feedback, quoted]

### Changes to interaction spec

**[interactions/<name>.md]**
- Section: [States | Transitions | Gestures | Error Cases]
- Was: [current spec text]
- Now: [amended spec text]
- Rationale: [why this change addresses the feedback]
```

Apply the amendment to the interaction spec file.

**For structural changes:** Act as the Architect. Evaluate whether this requires a contract version bump. Produce:

```markdown
## Steer Amendment: [short description]
Date: [date]
Type: structural
Triggered by: [user's feedback, quoted]

### Contract changes

**[api-contracts/<name>.md or data-models/<name>.md]**
- Change: [description]
- Version: [old] → [new]
- Severity: [patch | minor | major]
```

Apply the change and bump the version.

**For implementation changes:** No spec amendment needed. Produce a directive that goes directly to the affected platform agent(s):

```markdown
## Steer Directive: [short description]
Date: [date]
Type: implementation
Triggered by: [user's feedback, quoted]
Platforms: [ios | android | backend | all]

### Directive
[What the platform agent should change in their approach]
```

### Step 3 — Calculate blast radius

For each platform (iOS, Android, Backend), check the task list:
- Which tasks are **completed** and affected by this change? → Mark as `[~]` (invalidated, needs re-execution)
- Which tasks are **pending** and affected? → Update description to reflect the amendment
- Which tasks are **unaffected**? → Leave as-is

Report the blast radius to the user:

```
Blast radius:
  iOS:     2 tasks invalidated (tasks 3, 5), 1 task updated (task 7)
  Android: 2 tasks invalidated (tasks 3, 5), 1 task updated (task 7)
  Backend: 0 tasks affected
```

### Step 4 — Ask for confirmation

Present the amendment and blast radius. Ask: "Apply this change and resume implementation?"

If yes:
1. Apply spec changes
2. If contract version was bumped, trigger the contract monitoring flow (affected agents halt, re-read, resume)
3. Log the steer in `$CHANGE/steer-log.md`
4. Resume implementation — affected agents re-execute invalidated tasks

If no: discard the amendment, ask for refined feedback.

---

## Diverge mode

### Step 1 — Identify the area of concern

Parse the user's feedback to determine:
- **What area?** Which screen, flow, component, or interaction is the concern about?
- **Which platforms?** Does this affect iOS, Android, Backend, or all? (UI concerns typically affect iOS + Android; architectural concerns may affect all three)

Tell the user what you identified: "I'll generate alternatives for [area] on [platforms]."

### Step 2 — Generate alternatives

For each affected platform, generate **3 alternatives** for the area of concern. Each alternative must include:

1. **Name** — a short label (e.g., "Compact cards", "Grouped list", "Grid layout")
2. **Description** — 2-3 sentences explaining the approach and why it might work
3. **Key difference** — what makes this meaningfully different from the others
4. **Trade-off** — what you gain and what you give up

If possible, show code snippets or describe the visual outcome concretely enough that the user can picture it.

Present alternatives clearly:

```
Area: Note list on iOS

Option A — Compact cards
  Each note is a card with title, first line preview, and date.
  Swipe-left for delete. Tap to open.
  + Dense, scannable. Good for users with many notes.
  - Less visual hierarchy. Harder to distinguish notes at a glance.

Option B — Grouped by date
  Notes grouped under date headers (Today, Yesterday, This Week, Older).
  Each note shows title + full first paragraph preview.
  + Natural chronological scanning. Feels organized.
  - Takes more vertical space. Users with few notes see lots of whitespace.

Option C — Minimal list
  Title-only rows with subtle timestamp right-aligned.
  Tap to open, long-press for actions. No swipe gestures.
  + Clean, fast, focused. Feels premium.
  - Less information density. Requires tap to see content.
```

### Step 3 — User selects

Ask: "Which approach do you prefer? You can also combine elements (e.g., 'A with the grouping from B')."

### Step 4 — Record the selection

Once the user picks, convert their selection into a **binding constraint** in the interaction spec:

```markdown
## Steer Selection: [short description]
Date: [date]
Type: diverge-and-select
Area: [what was the concern]
Selected: [option name]
Rejected: [other option names]

### Constraint added to interaction spec
[The specific behavioral rule derived from the selection]

### Rationale
[Why the user chose this — quote them if they gave a reason]
```

Apply the constraint to the interaction spec. Then follow the amend mode blast radius flow (Steps 3-4) to invalidate and re-execute affected tasks.

---

## Checkpoint revert (optional, either mode)

If the change is large enough that patching feels wrong, offer to revert to a checkpoint:

"This affects [N] completed tasks across [platforms]. Would you rather revert to checkpoint [name] and rebuild from there with the updated spec? Or apply the change surgically and re-run only the affected tasks?"

If the user chooses revert:
1. Reset platform code to the checkpoint's git state
2. Apply the spec amendment
3. Mark all tasks after the checkpoint as `[ ]` (pending)
4. Resume implementation from the checkpoint

---

## Steer log

Every steer (amend or diverge) is logged in `$CHANGE/steer-log.md`:

```markdown
# Steer Log

## [Date] — [Short description]
**Mode:** amend | diverge
**Type:** behavioral | structural | implementation
**Feedback:** "[user's original words]"
**Change:** [what was changed in the spec]
**Blast radius:** [summary]
**Platforms affected:** [list]
```

This log serves two purposes:
1. Audit trail — see how the feature evolved during implementation
2. Harness evolution signal — if you see recurring patterns in steers, consider adding rules to your platform AGENTS.md files to prevent the issue in future features

---

## Rules

- Never skip the blast radius calculation — even small changes can cascade
- Never modify specs without showing the user what will change and getting confirmation
- The steer log is append-only — never edit previous entries
- If a steer would invalidate more than 70% of completed tasks, recommend reverting to a checkpoint instead
- Diverge mode alternatives must be meaningfully different — not three variations of the same idea
- Implementation directives (no spec change) do not require contract version bumps
- If the same area has been steered more than twice, flag this to the user — the spec may need a deeper rethink via `/propose`
