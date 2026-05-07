# AGENTS.md

Guidance for AI coding agents (Codex, Cursor, Claude Code, etc.) working in this repo.

> If you're using Claude Code, also read [CLAUDE.md](CLAUDE.md) — it has the same content with Claude-specific framing.

## What this is

NL Native is a **development harness** — not a framework, library, or app. It defines:

- Seven agent role definitions ([agents/](agents/))
- Spec templates ([schemas/](schemas/))
- Slash commands and verification skills ([.claude/](.claude/))
- A worked example ([example/](example/))

There is no runtime. No Swift, no Kotlin, no backend code lives at the top level of this repo. Apps that adopt NL Native add `platforms/ios/`, `platforms/android/`, `platforms/backend/` directories alongside the harness.

**Specs are the source of truth. Code is output.** When requirements change, update the spec — the platform agents update the code.

## Hard constraints

- **No application code in this repo.** Don't add Swift sources, Kotlin sources, server code, build files (`Package.swift`, `build.gradle`, etc.), or platform tooling. Those belong in projects that adopt the harness.
- **Strict agent ownership.** Every agent file in [agents/](agents/) has an "Owns" and "Key Rule" section. Don't blur those boundaries.
- **No lateral platform communication.** The iOS, Android, and Backend experts NEVER call each other or reference each other's outputs directly. All cross-cutting decisions route through the Architect. This is the single most important property of the harness — preserve it.
- **Only the Architect bumps contract versions.** API contracts and data models in `schemas/` use semver. The Architect is the only role that may bump them. Patch = cosmetic, Minor = additive, Major = breaking.
- **The QA Verifier reports, never fixes.** It writes findings into a verification report. It does not touch implementation files.
- **EARS notation is mandatory** for all requirements. Use `When [trigger], the system shall [behavior]` / `While [state]...` / `If [condition]...` / `The system shall...`.

## Agent topology

```
         Spec Analyst
              │
      ┌───────┴────────┐
      │                │
  Architect ◄────► UX Designer
      │
  ┌───┼───┐
  │   │   │
 iOS  Android Backend     ← no lateral communication
  │   │   │
  └───┼───┘
      │
  QA Verifier
```

| Agent | File | Owns | Key rule |
|---|---|---|---|
| Spec Analyst | [agents/spec-analyst.md](agents/spec-analyst.md) | Proposals, feature specs | Never writes code or makes tech choices |
| Architect | [agents/architect.md](agents/architect.md) | API contracts, data models, gate reviews | Only role that bumps contract versions |
| UX Designer | [agents/ux-designer.md](agents/ux-designer.md) | Interaction specs | Defines behavior, not visuals |
| Visual Designer | [agents/visual-designer.md](agents/visual-designer.md) | Visual identity, design system | Visuals, not behavior |
| iOS Expert | [agents/ios-expert.md](agents/ios-expert.md) | Swift/SwiftUI code, iOS impl spec | No contact with other platform agents |
| Android Expert | [agents/android-expert.md](agents/android-expert.md) | Kotlin/Compose code, Android impl spec | No contact with other platform agents |
| Backend Expert | [agents/backend-expert.md](agents/backend-expert.md) | Endpoints, schema, auth | Service-agnostic at spec level |
| QA Verifier | [agents/qa-verifier.md](agents/qa-verifier.md) | Verification reports | Reports findings, never fixes them |

## Workflow (slash commands)

Defined in [.claude/commands/](.claude/commands/). The lifecycle is strict and ordered:

1. `/propose <feature-name>` — plain English → EARS spec → API contracts → data models → interaction spec → gate review → human approval. **No code is written until the human approves.**
2. `/fan-out` — parallel iOS, Android, Backend implementation. Each platform writes an impl spec, task list with contract dependencies, then implements. iOS and Android use mock data layers so they don't block on the backend. Auto-triggers `/connect` when backend completes.
3. `/steer <feedback>` — mid-flight course correction. Specific feedback → spec delta + surgical re-execution. Vague feedback → generate alternatives, user picks.
4. `/preview` — build, boot simulator/emulator, walk interaction spec states, capture screenshots.
5. `/connect` — wire mock data layers to the real backend. Smoke-test endpoints, generate real clients, verify mock→real swap.
6. `/verify` — Phase A: per-platform spec compliance. Phase B (only if Phase A passes): cross-platform coherence + integration.
7. `/archive` — merge delta specs into baseline, learn from steers, propose permanent AGENTS.md rules.
8. `/adopt <path>` — reverse-engineer specs from an existing codebase.
9. `/status` — dashboard.

## Spec templates

All in [schemas/](schemas/):

- [feature-spec.md](schemas/feature-spec.md) — EARS requirements + Given/When/Then scenarios
- [api-contract.md](schemas/api-contract.md) — versioned endpoints with full error enumerations
- [data-model.md](schemas/data-model.md) — versioned entities with types, constraints, relationships
- [interaction-spec.md](schemas/interaction-spec.md) — states, transitions, gestures, error presentation (behavioral, not visual)
- [design-system.md](schemas/design-system.md) — visual tokens and component specs
- [platform-constraint.md](schemas/platform-constraint.md) — blocker/issue reports from platform experts
- [backend-agents.md](schemas/backend-agents.md) — backend service configuration template

## When you change something here

- Edit an agent profile? Update [README.md](README.md) if you changed the agent's role summary, and update [CLAUDE.md](CLAUDE.md) if you changed key rules.
- Add a slash command? Add it to the table in [README.md](README.md) and the workflow list in [CLAUDE.md](CLAUDE.md).
- Add a schema? Add it to the schemas table in this file, [README.md](README.md), and [CLAUDE.md](CLAUDE.md).
- Touch the agent topology? You're probably wrong — confirm with the user first. If you're not, update the diagram in this file, [CLAUDE.md](CLAUDE.md), and [README.md](README.md) consistently.

## Contributing surface

PRs welcome for: new agent profiles (e.g. web-expert, rn-expert), AGENTS.md templates for additional backend services, schema improvements, worked examples, and ports of slash commands to other agent tools.
