Reverse-engineer NL Native specs from an existing codebase. Point this at a Swift, Kotlin, or backend project and it extracts feature specs, API contracts, data models, and interaction specs in the NL Native format — so you can bring an existing app into the harness without starting from scratch.

**Usage:** `/adopt <path-to-existing-code>` or `/adopt` (uses current working directory)

---

## Pre-flight

1. Determine the target path (argument or cwd)
2. Detect what's there:
   - Swift/SwiftUI files → iOS platform
   - Kotlin/Compose files → Android platform
   - Backend code (TypeScript, Python, Go, etc.) → Backend platform
   - Multiple → process each
3. Confirm with user: "I found [iOS/Android/Backend] code at [path]. I'll extract specs from it. Proceed?"

---

## Step 1 — Inventory the codebase

### For iOS (Swift/SwiftUI)
Scan for:
- **Views** (`*View.swift`, `*Screen.swift`) → these become interaction spec states
- **ViewModels** (`*ViewModel.swift`, `@Observable` classes) → these reveal state machines and data flows
- **Models** (`*Model.swift`, structs conforming to `Codable`) → these become data model entities
- **Network/API clients** (URLSession calls, endpoint definitions) → these become API contracts
- **Navigation** (NavigationStack, TabView, sheet/fullScreenCover) → this becomes the interaction spec transitions

### For Android (Kotlin/Compose)
Scan for:
- **Composables** (`*Screen.kt`, `*Composable.kt`) → interaction spec states
- **ViewModels** (classes extending `ViewModel`, `StateFlow` usage) → state machines
- **Data classes** (especially with `@Serializable` or Room `@Entity`) → data model entities
- **API interfaces** (Ktor/Retrofit definitions) → API contracts
- **Navigation** (NavHost, NavGraph) → interaction spec transitions

### For Backend
Scan for:
- **Route handlers / endpoints** → API contracts
- **Database schemas / migrations** → data models
- **Auth middleware** → auth contract
- **Validation logic** → request constraints

---

## Step 2 — Extract API contracts

For each endpoint found:

```markdown
# API Contract: [Name]
Version: 1.0.0
Status: adopted

## Endpoints

### [METHOD] [PATH]

**Auth:** [Required | None]

**Request**
| Field | Type | Required | Description |
|---|---|---|---|
[extracted from request body types]

**Response 200**
| Field | Type | Description |
|---|---|---|
[extracted from response types]

**Errors**
| Status | Code | Description |
|---|---|---|
[extracted from error handling code]
```

Write to `specs/core/api-contracts/<name>.md`.

**Ambiguity handling:** If the code handles an error but doesn't have a named error code, generate one from the error message pattern (e.g., `INVALID_INPUT`, `NOT_FOUND`). Mark these as `[inferred]` in the description.

---

## Step 3 — Extract data models

For each entity/model:

```markdown
# Data Model: [Name]
Version: 1.0.0
Status: adopted

## Entities

### [EntityName]

| Field | Type | Nullable | Constraints | Description |
|---|---|---|---|---|
[extracted from struct/class/table definition]
```

Write to `specs/core/data-models/<name>.md`.

**Cross-reference:** If a field in the data model doesn't appear in any API contract response, note it as `[local-only]` — it may be a client-side computed property or a field that's stored but not exposed via API.

---

## Step 4 — Extract interaction specs

For each screen/view:

```markdown
# Interaction: [Screen Name]
Version: 1.0.0
Status: adopted

## States
[Extracted from ViewModel state enum / sealed class / @Observable properties]

## Transitions
[Extracted from navigation code, button actions, gesture handlers]

## Gestures
[Extracted from onTapGesture, swipeActions, longPressGesture, etc.]

## Error Cases
[Extracted from error handling in ViewModel / composable]
```

Write to `specs/core/interactions/<name>.md`.

---

## Step 5 — Extract feature specs

Group the API contracts, data models, and interactions into logical features. For each:

```markdown
# Feature: [Name]
Version: 1.0.0
Status: adopted

## Overview
[Inferred from the grouped screens, endpoints, and data models]

## Requirements
[Reverse-engineered from the code — what the code actually does, stated as EARS requirements]

## Scenarios
[Key flows expressed as Given/When/Then, derived from the interaction spec transitions]
```

Write to `specs/core/features/<name>.md`.

---

## Step 6 — Generate platform AGENTS.md (if missing)

If `platforms/<platform>/AGENTS.md` doesn't exist, generate one from what you observed in the codebase:
- Language version
- Framework and library choices
- Architecture patterns (MVVM, MVI, etc.)
- Testing framework
- Naming conventions
- Build tool / commands

---

## Step 7 — Report

Present a summary:

```
Adoption complete: [path]
════════════════════════════════════

EXTRACTED
  Features:         [N] → specs/core/features/
  API contracts:    [N] → specs/core/api-contracts/
  Data models:      [N] → specs/core/data-models/
  Interactions:     [N] → specs/core/interactions/

PLATFORMS DETECTED
  iOS:      [✓ Swift 6 / SwiftUI / MVVM]
  Android:  [✓ Kotlin / Compose / MVVM]
  Backend:  [✓ TypeScript / Supabase]

GENERATED
  platforms/ios/AGENTS.md       [created | already existed]
  platforms/android/AGENTS.md   [created | already existed]
  platforms/backend/AGENTS.md   [created | already existed]

WARNINGS
  - [N] endpoints have inferred error codes — review manually
  - [N] fields marked [local-only] — not exposed via API
  - [N] interaction states inferred from ViewModel — verify against actual UI

NEXT STEPS
  1. Review extracted specs for accuracy
  2. Run `/propose <next-feature>` to build on this baseline
  3. Or run `/verify` to check existing code against extracted specs
════════════════════════════════════
```

---

## Rules

- Never modify the existing codebase — adoption is read-only
- Mark all extracted specs with `Status: adopted` so they're distinguishable from harness-generated specs
- When in doubt about a field type or constraint, use the most permissive interpretation and add a `[verify]` note
- If the codebase has tests, cross-reference them with the extracted scenarios — tests are the most reliable source of intended behavior
- If the codebase has no tests, note this prominently — the extracted specs are best-effort
- Adoption produces a baseline. The user should review it before treating it as the source of truth.
