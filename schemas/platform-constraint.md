# Schema: Platform Constraint Report

Copy this template to `specs/changes/<change-name>/constraints/<platform>.md`
where `<platform>` is `ios`, `android`, or `backend`.

Platform experts write constraint reports during the propose gate — after reviewing specs but before any code is written. A constraint report surfaces implementation problems early, so they can be resolved in the spec before fan-out begins.

---

```markdown
# Platform Constraint Report: [iOS | Android | Backend]
Change: [change-name]
Date: [date]
Author: [iOS Expert | Android Expert | Backend Expert]

## Summary

[One paragraph: overall assessment of the feature from this platform's perspective. 
Is it straightforward? Are there significant constraints? Estimate implementation complexity: Low / Medium / High.]

---

## Constraints

### [Constraint short name]

**Requirement:** REQ-XXX (or "API Contract: [name]", or "Interaction: [name]")
**Severity:** Blocker | Significant | Minor

**Issue:**
[Describe exactly why this requirement cannot be implemented as specified on this platform.
Be precise. "iOS doesn't support background location without a justification string and explicit user permission" is good.
"This might be tricky on iOS" is not.]

**Proposed alternative:**
[What would you do instead? Be specific.
"Request 'When In Use' location permission at the time the feature is first used, with a pre-permission rationale screen. 
Store the last known location locally and use it when permission is unavailable."]

**Impact on user experience:**
[How does this differ from the spec? Is the user experience equivalent, degraded, or just different?
"The user sees a permission dialog before the feature activates. Otherwise identical to spec."]

**Decision needed from:**
[ ] Architect — contract change needed
[ ] UX Designer — interaction spec update needed
[ ] Human — judgment call required
[x] None — proposing this as accepted alternative

---

### [Another constraint]

[Repeat for each constraint]

---

## Implementation notes

[Optional section. Flag anything the Architect or UX Designer should know before finalizing specs, 
that isn't a hard constraint but might affect design decisions:]

- [e.g.] The SSE streaming endpoint is fine, but iOS SSEParser will need a 30-second keepalive ping to prevent connection drops on cellular. Recommend adding this to the API contract.
- [e.g.] Android's SpeechRecognizer requires RECORD_AUDIO permission. This is not in the current permission spec. Add to the features/auth spec.

---

## Estimated task breakdown

[Optional but encouraged — helps the Architect understand implementation scope:]

| Task | Estimated effort |
|---|---|
| [Core feature implementation] | [S / M / L] |
| [Auth/permission handling] | [S / M / L] |
| [Error handling] | [S / M / L] |
| [Tests] | [S / M / L] |
| **Total** | **[S / M / L]** |

S = hours, M = 1-2 days, L = 3+ days
```

---

## Severity guide

**Blocker** — The requirement as written cannot be implemented on this platform at all, or would violate platform policies (App Store / Play Store rules). Must be resolved before fan-out.

**Significant** — The requirement can be implemented but requires a meaningful deviation from the spec that changes the user experience. Must be acknowledged and approved before fan-out.

**Minor** — Small implementation detail that differs from spec defaults. Platform expert can handle it autonomously without spec update, but is flagging it for transparency.

## When to file a constraint

File a constraint when:
- A platform API is unavailable or requires a permission not mentioned in the spec
- An interaction is physically impossible on the platform (e.g., no equivalent gesture)
- App Store or Play Store guidelines prohibit or restrict the specified behavior
- A contract field type cannot be represented in the platform's type system without conversion
- The estimated implementation effort is significantly higher than expected (flag as an implementation note)

Do not file a constraint for:
- Library or framework choices — those are your decision
- Implementation details — those are your domain
- Things you'd do differently — constraints are blockers, not preferences
