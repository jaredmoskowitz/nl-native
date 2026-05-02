# Schema: Feature Spec

Copy this template to `specs/changes/<change-name>/specs/core/features/<feature-name>.md`.

Fill in every section. Delete placeholder text. Do not leave TODOs.

---

```markdown
# Feature: [Feature Name]
Version: 1.0.0
Status: draft

## Summary

[One paragraph. What does this feature do? Who uses it? What problem does it solve?
Be specific. "Users can create notes" is better than "note management functionality."]

## Scope

**In scope:**
- [Specific behavior or capability included in this feature]
- [Another capability]

**Out of scope:**
- [Explicitly excluded behavior — prevents scope creep during implementation]
- [Another exclusion]

**Open questions:**
- [Questions that must be answered before this spec is finalized]
- [Delete this section if there are none]

## Requirements

### [Section — group related requirements, e.g. "Creation", "Editing", "Deletion"]

- REQ-001: [EARS requirement — e.g. "When the user taps Create, the system shall display a new note editor"]
- REQ-002: [EARS requirement]
- REQ-003: [EARS requirement]

### [Next Section]

- REQ-004: [EARS requirement]
- REQ-005: [EARS requirement]

## Scenarios

### [Scenario name — describe the situation, e.g. "User creates a note successfully"]

**Given** [initial state or precondition]
**When** [user action or system event]
**Then** [expected outcome]
**And** [additional expected outcome, if needed]

### [Scenario name — error case]

**Given** [initial state]
**When** [action that causes an error]
**Then** [how the error is presented]
**And** [what recovery options are available]

### [Scenario name — edge case]

**Given** [edge condition, e.g. "the user has no items", "the device is offline"]
**When** [action]
**Then** [expected behavior]
```

---

## EARS reference

| Pattern | Template | Example |
|---|---|---|
| Ubiquitous | `The system shall [behavior]` | `The system shall persist notes across app restarts` |
| Event-driven | `When [trigger], the system shall [behavior]` | `When the user taps Save, the system shall store the note` |
| State-driven | `While [state], the system shall [behavior]` | `While offline, the system shall queue changes locally` |
| Conditional | `If [condition], then the system shall [behavior]` | `If the note is empty, then the system shall discard it without prompting` |
| Optional | `Where [feature], the system shall [behavior]` | `Where biometric auth is enabled, the system shall require it before displaying notes` |

## Writing good requirements

**Testable:** A QA agent must be able to write a pass/fail test for every requirement. If you can't imagine the test, rewrite the requirement.

**Atomic:** One behavior per requirement. "The system shall save the note and show a confirmation" is two requirements.

**Implementation-free:** Don't mention buttons, components, or code. "The system shall allow the user to dismiss the editor" — not "there shall be an X button in the top-right corner."

**Unambiguous:** "The system shall respond quickly" is bad. "When the user taps Save, the system shall store the note and return to the list within 300ms" is good.

## Scenario coverage checklist

Every feature spec must include scenarios for:
- [ ] Happy path (the intended flow, working correctly)
- [ ] Empty/zero state (user has no data yet)
- [ ] Error state (network failure, server error, validation failure)
- [ ] Edge cases specific to the feature (long content, many items, concurrent actions)
- [ ] Permission/auth-required cases (if applicable)
```
