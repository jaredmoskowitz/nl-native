Run the NL Native propose gate for a new feature. This is a multi-step process that produces a fully reviewed, human-approved spec before any code is written.

The argument $ARGUMENTS is the feature name (e.g. `user-authentication`, `note-creation`). If no argument is provided, ask the user what feature they want to propose.

---

## Step 1 — Create the change directory

Create the directory structure for this change:

```
specs/changes/<feature-name>/
├── specs/
│   └── core/
│       ├── features/
│       ├── api-contracts/
│       ├── data-models/
│       └── interactions/
├── constraints/
│   ├── ios.md
│   └── android.md
├── proposal.md
├── ux-reconciliation.md
└── gate-review.md
```

---

## Step 2 — Spec Analyst produces the proposal and feature spec

Read `agents/spec-analyst.md` and act as the Spec Analyst.

Ask the user to describe the feature in plain English. Take as much time as needed — ask clarifying questions until you have enough to write a complete spec.

Produce:
1. `specs/changes/<feature-name>/proposal.md` — using the proposal section of the Spec Analyst profile
2. `specs/changes/<feature-name>/specs/core/features/<feature-name>.md` — using the `schemas/feature-spec.md` template

Requirements must use EARS notation. Every requirement must have at least one scenario. Scenarios must cover happy path, empty state, error states, and edge cases.

Present the feature spec to the user and ask for feedback. Revise until the user is satisfied. Do not proceed until the user explicitly says "approved" or "looks good."

---

## Step 3 — Architect and UX Designer work in parallel

### Architect (read `agents/architect.md`)

Produce:
- `specs/changes/<feature-name>/specs/core/api-contracts/<feature-name>.md` — using `schemas/api-contract.md`
- `specs/changes/<feature-name>/specs/core/data-models/<feature-name>.md` — using `schemas/data-model.md`

All endpoints must be fully specified including all error responses. All data model fields must be typed and constrained. Assign version 1.0.0 to all new contracts.

### UX Designer (read `agents/ux-designer.md`)

Produce:
- `specs/changes/<feature-name>/specs/core/interactions/<feature-name>.md` — using `schemas/interaction-spec.md`

All states must be defined. All state transitions must be explicit. All error presentations must be specified.

---

## Step 4 — Platform experts review and file constraints

Read `agents/ios-expert.md` and `agents/android-expert.md`. For each platform:

1. Read the feature spec, API contract, data model, and interaction spec
2. Identify any constraints — requirements that cannot be implemented as specified on this platform
3. Produce the constraint report using `schemas/platform-constraint.md`:
   - `specs/changes/<feature-name>/constraints/ios.md`
   - `specs/changes/<feature-name>/constraints/android.md`

If there are no constraints, write "No constraints identified." in the file.

---

## Step 5 — UX reconciliation

Read `agents/ux-designer.md`. Review both constraint reports.

For each constraint that affects user experience:
- State your ruling: accept the platform alternative, require equivalent behavior via a different approach, or escalate to the human
- Update the interaction spec if needed

Produce: `specs/changes/<feature-name>/ux-reconciliation.md`

Format:
```markdown
# UX Reconciliation: <feature-name>

## [Constraint name]
**Platform:** iOS | Android
**Ruling:** [Accept alternative | Require equivalent | Escalate]
**Rationale:** [Why]
**Spec update:** [What changed in the interaction spec, or "None"]
```

---

## Step 6 — Gate review

Read `agents/architect.md`. Produce: `specs/changes/<feature-name>/gate-review.md`

The gate review must include:

1. **Contract change table** — every API contract and data model introduced or modified, with version, change description, and severity (cosmetic / additive / breaking)

2. **Unresolved conflicts** — any constraint that requires human judgment, listed with options and tradeoffs

3. **Implementation checklist** — confirm:
   - [ ] All requirements have at least one scenario
   - [ ] All endpoints have complete error specifications
   - [ ] All data model fields are typed and constrained
   - [ ] All interaction states are defined
   - [ ] All platform constraints are filed and reconciled (or escalated)
   - [ ] No open questions remain in the feature spec

4. **Approval request** — a plain English summary of what is being approved and what will be built

---

## Step 7 — Human approval

Present the gate review to the user. Summarize:
- What the feature does (one sentence)
- The contracts being introduced (names and versions)
- Any constraint rulings the user should be aware of
- Any items escalated for human judgment

**Do not proceed to fan-out until the user explicitly approves.** If the user requests changes, return to the appropriate step, make the changes, and re-present the gate review.

When approved, tell the user: "Gate approved. Run `/fan-out` to begin implementation."
