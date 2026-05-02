Archive the active change after successful verification. This merges the delta specs into the stable baseline and closes the change.

Only run this after `/verify` has passed with no BLOCKER findings.

---

## Pre-flight

1. Confirm `$CHANGE/verification-report.md` exists and shows PASS status for Phase A and Phase B
2. If verification has not passed, tell the user to run `/verify` first

---

## Step 1 — Merge core specs into stable baseline

For each file in `$CHANGE/specs/core/`:

**New files** (no corresponding file in `specs/core/`):
- Copy directly to `specs/core/<path>`

**Modified files** (file exists in both `$CHANGE/specs/core/` and `specs/core/`):
- Merge changes using the following rules:
  - ADDED sections: append to the stable file
  - MODIFIED sections: replace the old section with the updated version
  - REMOVED sections: delete from the stable file
  - Version number: update to the version in the change file
  - Status: set to `archived`
  - Add to changelog: `| <new-version> | [brief description of change] | <today's date> |`

After merging, the stable `specs/core/` directory is the new baseline for all future features.

---

## Step 2 — Update UX standards

Read `agents/ux-designer.md`. Review the interaction specs from this change.

Identify any patterns that:
- Were novel in this change (not previously in UX standards)
- Proved successful (no major UX findings in verification)
- Would be reusable in future features

For each such pattern, append to `specs/core/ux-standards.md`:

```markdown
## [Pattern name]
*Added in: <change-name>*

[Description of the pattern — what it is and when to use it]

**States:** [relevant states]
**Transitions:** [transition rules]
**Feedback:** [haptic/visual feedback conventions]
```

If no new patterns emerged, note "No new patterns added from <change-name>."

---

## Step 2b — Harness evolution (learn from steers)

If `$CHANGE/steer-log.md` exists, review all steering entries. Look for patterns that should become permanent rules:

**Recurring corrections** — the same kind of steer applied more than once across this or prior changes (e.g., "list rows are always too dense", "always defaults to full-screen modals when sheets would be better"):
- Distill into a concrete rule
- Add to the relevant `platforms/<platform>/AGENTS.md` file

**Diverge selections that reveal taste** — user consistently picks the same style of alternative (e.g., minimal over dense, native over custom):
- Add as a design preference to `platforms/ios/AGENTS.md` or `platforms/android/AGENTS.md`

**Structural steers that indicate spec gaps** — if the Architect's contracts needed mid-flight changes, the gate review process may need tightening:
- Note in the archive summary, not as a rule

Format for AGENTS.md additions:

```markdown
## [Rule name]
*Learned from: <change-name>*

[The rule — specific enough to follow, not so specific it only applies to one feature]
```

Present proposed AGENTS.md additions to the user for approval before writing them. These compound over time — each one makes future features more aligned with the user's preferences without needing steers.

If no actionable patterns emerged from the steer log, note "No harness updates from <change-name> steers."

---

## Step 3 — Close the change

Move the change directory to the archive:

```
specs/changes/<name>/ → specs/changes/archive/<name>/
```

Add an `ARCHIVED.md` file to the archived directory:

```markdown
# Change: <name>
Archived: <date>
Status: Complete

## Summary
[One paragraph: what was built and verified]

## Contracts introduced or modified
| Contract | Version |
|---|---|

## Platforms
- iOS: [brief description of what was implemented]
- Android: [brief description of what was implemented]
- Backend: [brief description of what was implemented]

## Steers applied
[Number of steers, or "None"]

## Harness rules added
[List any rules added to AGENTS.md files, or "None"]
```

---

## Step 4 — Git commit

Stage and commit all changes:

```
git add specs/
git commit -m "feat: archive <change-name>

- Merged feature spec, API contracts, data models, interactions into baseline
- Updated UX standards with [N] new patterns
- Archived change directory"
```

---

## Completion

Tell the user:
- The change has been archived
- What was merged into the stable baseline
- The new spec baseline version (based on the highest contract version bumped)
- "Run `/propose <next-feature>` to start your next feature"
