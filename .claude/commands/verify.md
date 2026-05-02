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

**If any BLOCKER findings exist in Phase A, stop here.** Route findings to the appropriate agent and wait for fixes before proceeding to Phase B.

---

## Phase B — Cross-platform coherence

Only run Phase B after both platforms have no BLOCKER findings in Phase A.

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
- List each BLOCKER finding with its routing
- Tell the user which agent needs to address each finding
- After fixes, the user should re-run `/verify`

**WARNINGs only:**
Present warnings to the user for acknowledgment. They do not block archiving but should be addressed in a follow-up change.
