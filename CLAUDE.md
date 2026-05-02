# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

NL Native is a **development harness** — not a framework or library. It orchestrates AI agents to build native iOS (Swift/SwiftUI) and Android (Kotlin/Jetpack Compose) apps from natural language specifications. You don't import it; you adopt its conventions, spec templates, agent roles, and slash commands.

**Specs are the source of truth.** Code is output. When requirements change, update the spec — agents update the code.

## Slash Commands (Workflow)

The development lifecycle is a strict sequence:

1. `/propose <feature-name>` — 7-step gate sequence: plain English → EARS spec → API contracts + data models → interaction spec → platform constraints → UX reconciliation → gate review → human approval. **No code is written until the human approves.**
2. `/fan-out` — Launches parallel iOS, Android, and Backend implementation agents. Each writes an implementation spec, a task list with contract version dependencies and checkpoints, then implements task-by-task. iOS and Android use mock data layers during fan-out so they don't block on the backend. Auto-triggers `/connect` when backend completes.
3. `/steer <feedback>` — Mid-flight course correction. Auto-detects mode: **amend** (specific feedback → spec delta → blast radius → surgical re-execution) or **diverge** (vague dissatisfaction → generate alternatives → user picks → binding constraint). Can revert to checkpoints if needed.
4. `/preview` — Builds the app, boots the simulator/emulator, walks through interaction spec states, captures screenshots. See what was built before verifying. Pairs with `/steer`.
5. `/connect` — Wires mock data layers to the real backend. Smoke-tests all endpoints, generates real API client implementations, verifies the mock→real swap. **Auto-triggered** from `/fan-out` when backend completes; can also run manually.
6. `/verify` — Two-phase verification. Phase A: per-platform spec compliance (all three platforms in parallel). Phase B: cross-platform coherence + integration verification (only runs if Phase A passes with no BLOCKERs).
7. `/archive` — Merges delta specs into `specs/core/` baseline, extracts reusable UX patterns, learns from steers, moves change to `specs/changes/archive/`, commits.
8. `/adopt <path>` — Reverse-engineers NL Native specs from an existing codebase. Extracts feature specs, API contracts, data models, and interaction specs so you can bring an existing app into the harness.
9. `/status` — Dashboard showing active change phase, spec completion, task progress, checkpoints, steers, contract alignment, verification state, and next step.

## Agent Roles

Six agents with strict ownership boundaries. Read the agent file before acting in any role.

| Agent | File | Owns | Key Rule |
|---|---|---|---|
| Spec Analyst | `agents/spec-analyst.md` | Proposals, feature specs | Never writes code or makes tech choices |
| Architect | `agents/architect.md` | API contracts, data models, gate reviews | Only agent who bumps contract versions (semver) |
| UX Designer | `agents/ux-designer.md` | Interaction specs, UX reconciliation | Defines behavior, not visuals |
| iOS Expert | `agents/ios-expert.md` | All iOS code, iOS impl spec, iOS tasks | Also reads `platforms/ios/AGENTS.md`. Uses mock data layer during fan-out. |
| Android Expert | `agents/android-expert.md` | All Android code, Android impl spec, Android tasks | Also reads `platforms/android/AGENTS.md`. Uses mock data layer during fan-out. |
| Backend Expert | `agents/backend-expert.md` | All backend code, backend impl spec, backend tasks | Also reads `platforms/backend/AGENTS.md`. Service-agnostic at spec level. |
| QA Verifier | `agents/qa-verifier.md` | Verification reports | Reports findings only — never fixes anything |

**Hub-and-spoke topology:** Platform agents never communicate with each other. All cross-cutting decisions go through the Architect. This prevents coherence drift.

## Architecture: Change Directory

Each feature lives in `specs/changes/<feature-name>/` with this structure:

```
specs/changes/<feature-name>/
├── proposal.md
├── gate-review.md
├── ux-reconciliation.md
├── verification-report.md
├── specs/
│   ├── core/
│   │   ├── features/<name>.md
│   │   ├── api-contracts/<name>.md
│   │   ├── data-models/<name>.md
│   │   └── interactions/<name>.md
│   ├── ios/implementation.md
│   ├── android/implementation.md
│   └── backend/implementation.md
├── tasks/
│   ├── ios-tasks.md          # Declares contract-dependencies in frontmatter
│   ├── android-tasks.md
│   └── backend-tasks.md
└── constraints/
    ├── ios.md
    ├── android.md
    └── backend.md
```

Stable baseline lives in `specs/core/`. Archived changes live in `specs/changes/archive/`.

## Spec Templates

All in `schemas/`. Fill these when producing specs:

- `feature-spec.md` — EARS notation requirements + Given/When/Then scenarios
- `api-contract.md` — Versioned endpoints with full error enumerations
- `data-model.md` — Versioned entities with types, constraints, relationships
- `interaction-spec.md` — States, transitions, gestures, error presentation (behavioral, not visual)
- `platform-constraint.md` — Blocker/issue reports from platform experts

## Key Conventions

- **EARS notation** for all requirements: `When [trigger], the system shall [behavior]` / `While [state]...` / `If [condition]...` / `The system shall...`
- **Contract versioning:** Semver on all API contracts and data models. Patch = cosmetic, Minor = additive, Major = breaking. Only Architect bumps.
- **Contract version monitoring during fan-out:** Platform task lists declare contract dependencies. If a contract version changes mid-implementation, the dependent agent halts, re-reads, reassesses, and resumes.
- **Two-phase verification:** Phase A (per-platform compliance) must pass before Phase B (cross-platform coherence) runs. BLOCKERs halt progress; WARNINGs are acknowledged but don't block.

## Platform Defaults

**iOS** (override in `platforms/ios/AGENTS.md`):
- Swift 6.0+, iOS 17.0+, SwiftUI, MVVM with `@Observable`, async/await, XCTest
- No force unwrapping, no `DispatchQueue.main.async` (use `@MainActor`), no Combine

**Android** (override in `platforms/android/AGENTS.md`):
- Kotlin 2.x+, Jetpack Compose, MVVM with StateFlow, Coroutines, JUnit 5

**Backend** (override in `platforms/backend/AGENTS.md`):
- Service-agnostic at spec level. The `AGENTS.md` file specifies the concrete service (Supabase, Firebase, Cloudflare Workers, custom server, etc.), language, and conventions for the project.

## Example

`example/specs/changes/note-creation/` contains a complete worked example showing all artifacts from proposal through gate review for a Notes app feature.
