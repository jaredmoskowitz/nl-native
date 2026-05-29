Run the NL Native verification workflow for the active change. Verification runs in two phases: per-platform spec compliance, then cross-platform coherence.

---

## Pre-flight

Find the active change directory: `specs/changes/<name>/` with completed task lists.

Load into context:
- `$CHANGE/specs/core/features/*.md`
- `$CHANGE/specs/core/api-contracts/*.md`
- `$CHANGE/specs/core/data-models/*.md`
- `$CHANGE/specs/core/interactions/*.md`
- `$CHANGE/tasks/ios-tasks.md`
- `$CHANGE/tasks/android-tasks.md`
- `$CHANGE/tasks/backend-tasks.md`

---

## Phase A — Per-platform verification (run all in parallel)

Read `agents/qa-verifier.md` and act as the QA Verifier for each platform.

### For each platform (iOS, Android, and Backend):

**1. Task completion check**
- Are all tasks in the task list marked `[x]`?
- If not, list which tasks are incomplete. This is a BLOCKER.

**2. Requirement coverage**
For every requirement (REQ-XXX) in the feature spec:
- Find the corresponding implementation in `platforms/<platform>/`
- Confirm the implementation exists and matches the requirement
- Confirm a test exists that covers this requirement

**3. Scenario coverage**
For every Given/When/Then scenario in the feature spec:
- Find the corresponding test
- Confirm it exercises the full scenario (Given state set up, When action triggered, Then assertion made)

**4. Interaction spec compliance**
For every state defined in the interaction spec:
- Confirm the state is represented in the implementation
- Confirm state transitions are correct
- Confirm error presentations match the spec

**5. Contract compliance**
- Confirm the implementation uses the contract version declared in the task list frontmatter
- Confirm all request fields are sent, all response fields are parsed
- Confirm all specified error codes are handled

Produce: `$CHANGE/verification-report.md` — Phase A section

```markdown
## Phase A: Per-Platform

### iOS
Status: PASS | FAIL | PARTIAL

#### Requirement Coverage
| Requirement | Implementation | Test | Result |
|---|---|---|---|

#### Scenario Coverage
| Scenario | Test | Result |
|---|---|---|

#### Mock Data Layer
| API Client Protocol | Mock Conformance | Real Conformance Ready | Result |
|---|---|---|---|

#### Findings
- FINDING-XXX [BLOCKER|WARNING|INFO] → [routing]: [description]

### Android
[Same structure as iOS, with Interface instead of Protocol]

### Backend
Status: PASS | FAIL | PARTIAL

#### Endpoint Coverage
| Contract Endpoint | Implementation | Test | Result |
|---|---|---|---|

#### Data Model Coverage
| Entity | Table/Collection Created | Schema Matches Spec | Result |
|---|---|---|---|

#### Error Code Coverage
| Endpoint | Error Code | Implemented | Result |
|---|---|---|---|

#### Access Control
| Policy (from data model) | Implementation | Result |
|---|---|---|

#### Findings
- FINDING-XXX [BLOCKER|WARNING|INFO] → [routing]: [description]
```

---

## Phase A.5 — Auto-resolution loop

If Phase A produced BLOCKER findings, do NOT just stop and wait. Close the loop: the QA Verifier still only *reports* (it never edits code — see `agents/qa-verifier.md`), but the orchestration layer routes each finding to the agent that owns the code, that agent fixes it, and QA re-verifies. This was validated empirically (see `docs/superpowers/specs/2026-05-28-plan3-probe-findings.md`: it raised correctness from 0.40 to 1.00 on weak-model output).

**Step 1 — Partition the BLOCKERs by their routing** (the finding already names its route):

- **Implementation-class** → owning platform/Backend expert (the finding routes to "iOS Expert", "Android Expert", "Backend Expert", or an integration finding). These have a concrete fix → they enter the loop.
- **Decision-class** → Architect (contract), Spec Analyst (spec ambiguity), or UX Designer (behavioral). These need a *decision*, not a fix — auto-looping would invent intent. **Escalate these to the human immediately** and do not loop on them.

**Step 2 — Bounded fix loop (≤ 2 rounds):**

```
remaining = implementation-class BLOCKERs
round = 0
while remaining and round < 2:
    round += 1
    for each finding: the owning platform expert fixes it (in its own worktree)
    QA re-verifies ONLY the findings in `remaining`
    remaining = findings still failing
```

- Each round, the owning agent makes the minimal fix the finding calls for. QA re-checks just those findings (not the whole suite) to keep rounds cheap.
- If `remaining` is empty before round 2, exit early.

**Step 3 — Escalate survivors.** Any implementation BLOCKER still failing after 2 rounds is escalated to the human (alongside any decision-class findings from Step 1). Do not silently loop further.

**Step 4 — Regression sweep.** Once the loop clears (or only WARNINGs/INFO remain), run **one full Phase A pass** to catch regressions introduced by the fixes. Only then proceed to Phase B.

The human gate stays at `/propose`; this loop runs autonomously and surfaces to the human only on surviving blockers. Round count and the per-round findings are logged for the steer/harness-evolution review.

---

## Phase B — Cross-platform coherence

Only run Phase B after both platforms have no BLOCKER findings in Phase A (i.e. the Phase A.5 loop cleared them or they were escalated and resolved).

**1. Contract version alignment**

| Contract | iOS version | Android version | Backend version | Match? |
|---|---|---|---|---|

If versions don't match across any platform: FINDING [BLOCKER] → Architect

**2. Request/response consistency**

For each endpoint in the API contract:
- Compare how iOS sends the request vs. how Android sends the request
- Compare how iOS parses the response vs. how Android parses the response
- Confirm the backend accepts the request shape both platforms send
- Confirm the backend returns the response shape both platforms expect to parse
- Flag any field that one platform sends/parses and the other does not, or that the backend omits/adds

**3. Auth flow consistency**

- Confirm all three platforms (iOS, Android, Backend) agree on the auth flow
- Confirm both mobile platforms obtain tokens the same way
- Confirm the backend validates tokens the way both mobile platforms send them
- Confirm token refresh and expiry handling is consistent across all three

**4. Data model compatibility**

- Confirm both mobile platforms deserialize the same fields from each API response
- Confirm the backend serializes all fields that mobile platforms expect
- Confirm field types are compatible across all three (e.g., all treat `id` as a string, `created_at` as ISO 8601)

**5. Integration verification (mock → real)**

For each API client protocol/interface on the mobile platforms:
- Confirm a real implementation exists (not just the mock)
- If the real implementation connects to the backend, verify it produces the same results as the mock for the fixture data scenarios
- If the real implementation is not yet wired up, flag as WARNING (not BLOCKER) — the mock layer is functional

**6. Visual consistency (design system compliance)**

For each token in the design system spec (`specs/core/design-system/*.md`):
- Compare the iOS implementation's value against the spec
- Compare the Android implementation's value against the spec
- Confirm both platforms use the same hex colors for action palettes
- Confirm spacing, corner radii, and typography scale match
- Confirm animation parameters (spring damping, durations, thresholds) match
- Flag any platform that deviates without a filed and reconciled constraint

| Token | Spec Value | iOS Value | Android Value | Match? |
|---|---|---|---|---|
| [token-name] | [spec value] | [iOS value] | [Android value] | ✓ or FINDING |

Visual mismatches without a filed constraint are BLOCKER findings routed to the relevant platform expert.

**6. Experiential equivalence**

For each user-facing scenario in the feature spec:
- Can the same outcome be achieved on both platforms?
- Does the same user action produce the same result on both platforms?
- Are error messages equivalent (not identical — equivalent)?

Append to verification report:

```markdown
## Phase B: Cross-Platform Coherence

Status: PASS | FAIL | PARTIAL

### Contract Version Alignment
[table — iOS, Android, Backend versions for each contract]

### Request/Response Consistency
[findings or "All endpoints consistent across iOS, Android, and Backend"]

### Auth Flow Consistency
[findings or "Consistent across all three platforms"]

### Data Model Compatibility
[findings or "Compatible across all three platforms"]

### Integration Verification (Mock → Real)
| Platform | API Client | Mock Status | Real Status | Result |
|---|---|---|---|---|
[For each platform's API client protocol/interface]

### Experiential Equivalence
[findings or "Equivalent"]

### Findings
- FINDING-XXX [BLOCKER|WARNING|INFO] → [routing]: [description]
```

---

## Outcome

**All PASS, no BLOCKERs:**
Tell the user: "Verification passed. Run `/archive` to close this change."

**BLOCKERs present:**
- Implementation-class BLOCKERs are auto-resolved by the Phase A.5 loop (route → fix → re-verify, ≤ 2 rounds). Report which findings the loop fixed and in how many rounds.
- Decision-class BLOCKERs (contract / spec-ambiguity / behavioral) and any implementation BLOCKER that survives 2 rounds are escalated to the human, each with its routing and what it needs.
- The human acts only on the escalated set; there is no manual re-run for the auto-resolved ones.

**WARNINGs only:**
Present warnings to the user for acknowledgment. They do not block archiving but should be addressed in a follow-up change.
