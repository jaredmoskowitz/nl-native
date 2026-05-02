Show the current NL Native project status — active change, phase, task completion, checkpoints, steers, and any blockers.

---

## Detect project state

**No active change:**
If `specs/changes/` contains no directories (or only an `archive/` subdirectory), report:

```
NL Native — No active change

Run `/propose <feature-name>` to start a new feature.
```

---

**Active change found:**

Read all files in `specs/changes/<active-change-name>/` and report the following dashboard:

```
NL Native Status
════════════════════════════════════
Change:   <change-name>
Phase:    [Proposing | Approved — Awaiting fan-out | Implementing | Verifying | Ready to Archive]

SPECS
  Feature spec:       [✓ Complete | ✗ Missing | ~ Draft]
  API contracts:      [✓ v1.0.0 | ✗ Missing]
  Data models:        [✓ v1.0.0 | ✗ Missing]
  Interaction spec:   [✓ Complete | ✗ Missing | ~ Draft]

GATE
  Constraints filed:  iOS [✓ | ✗]   Android [✓ | ✗]   Backend [✓ | ✗ | — N/A]
  UX reconciliation:  [✓ Complete | ✗ Missing | ~ Pending]
  Gate review:        [✓ Approved | ~ Pending approval | ✗ Missing]

IMPLEMENTATION
  iOS tasks:      [X / Y complete]   [✓ All done | ~ In progress | ✗ Not started]
  Android tasks:  [X / Y complete]   [✓ All done | ~ In progress | ✗ Not started]
  Backend tasks:  [X / Y complete]   [✓ All done | ~ In progress | ✗ Not started | — No backend]

  Mock data status:
    iOS:      [Mock | Real | — N/A]
    Android:  [Mock | Real | — N/A]

  Contract dependencies:
    api-contracts/<name>:    iOS [v1.0.0] Android [v1.0.0] Backend [v1.0.0] [✓ Aligned | ✗ Mismatch]
    data-models/<name>:      iOS [v1.0.0] Android [v1.0.0] Backend [v1.0.0] [✓ Aligned | ✗ Mismatch]

CHECKPOINTS
  iOS:      [checkpoint-1 ✓, checkpoint-2 ✓, checkpoint-3 ~]
  Android:  [checkpoint-1 ✓, checkpoint-2 ~]
  Backend:  [checkpoint-1 ✓]
  (or "No checkpoints yet" if checkpoints.md doesn't exist)

STEERS
  Total steers: [N]
  Last steer:   [date] — [short description] ([amend | diverge])
  (or "No steers applied" if steer-log.md doesn't exist)

VERIFICATION
  Phase A — iOS:       [✓ Pass | ✗ Fail | ~ Not run]
  Phase A — Android:   [✓ Pass | ✗ Fail | ~ Not run]
  Phase A — Backend:   [✓ Pass | ✗ Fail | ~ Not run]
  Phase B — Coherence: [✓ Pass | ✗ Fail | ~ Not run | — Blocked by Phase A]
  Open blockers:       [N findings | None]

NEXT STEP
  [One sentence telling the user exactly what to do next]
════════════════════════════════════
```

## Logic for NEXT STEP

- Gate not approved → "Run `/propose` or await human approval of the gate review"
- Gate approved, implementation not started → "Run `/fan-out` to begin implementation"
- Implementation in progress → "Continue implementation on [platforms still in progress]"
- Implementation in progress, user may want to redirect → "Implementation in progress. Run `/steer <feedback>` to redirect if needed."
- Implementation complete, verification not run → "Run `/verify` to validate"
- Verification has blockers → "Fix [N] blocker findings before re-running `/verify`"
- Verification passed → "Run `/archive` to close this change"
- No active change → "Run `/propose <feature-name>` to start a new feature"

## Logic for Mock data status

- If platform task list exists but backend task list does not → "— N/A"
- If platform task list exists and backend tasks are not all complete → "Mock"
- If both platform and backend tasks are complete → check if real API client implementation exists → "Real" or "Mock"
