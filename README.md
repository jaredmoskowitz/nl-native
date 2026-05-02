<p align="center">
  <img src="logo.svg" width="200" alt="NL Native logo" />
</p>

<h1 align="center">NL Native</h1>

<p align="center"><strong>Specify once. Build natively — Swift for iOS, Kotlin for Android, any backend.</strong></p>

Flutter and React Native let you write code once and deploy to both platforms. The tradeoff: you're writing to a lowest common denominator. UI feels slightly off. Platform conventions get papered over. Performance ceilings appear. You end up fighting the framework to do things the platform does for free.

NL Native takes a different approach. You write your app in plain English. AI agents implement it natively on each platform — real SwiftUI on iOS, real Jetpack Compose on Android, your choice of backend service. No shared code. No cross-platform runtime. No compromises.

---

## How it works

NL Native is a **development harness**, not a framework. You don't import it. You adopt it. It's a set of conventions, spec templates, agent role definitions, and Claude Code slash commands that coordinate AI agents to build native apps from natural language specifications.

```
You write specs in plain English
        ↓
Spec Analyst structures them (EARS notation, Given/When/Then)
        ↓
Architect defines API contracts + data models (versioned)
        ↓
UX Designer defines interactions + behavioral rules
        ↓
iOS Expert implements in Swift/SwiftUI ──┐
                                          │
Android Expert implements in Kotlin/Compose ──├── in parallel, no shared code
                                          │
Backend Expert implements endpoints + schema ──┘
        ↓                                     ↑
        │                            /steer (redirect if needed)
        ↓
QA Verifier checks spec compliance per-platform, then cross-platform coherence
        ↓
Archive: merge delta specs into baseline, learn from steers, ready for next feature
```

The **spec is the product**. Code is output. When requirements change, you update the spec — agents update the code.

---

## Why native beats cross-platform

| | React Native / Flutter | NL Native |
|---|---|---|
| Code | Written once, shared | Never written by you — generated natively |
| iOS UI | Bridge to native / Skia renderer | Real SwiftUI |
| Android UI | Bridge to native / Skia renderer | Real Jetpack Compose |
| Backend | You build it | Generated from the same spec |
| Platform conventions | Approximated | Native by default |
| Performance | Near-native | Native |
| Platform APIs | Via wrappers | Direct |
| Maintenance | One codebase, cross-platform bugs | Three codebases, spec-verified coherence |
| AI generation quality | Model must reason about cross-platform | Model reasons in native idioms |

The last point matters more than it seems. LLMs are better at generating idiomatic Swift than at generating React Native that correctly handles iOS vs. Android deltas. Native is actually the easier target for AI code generation.

---

## What's in this repo

```
nl-native/
├── agents/              # Agent role definitions — read before acting in any role
│   ├── spec-analyst.md
│   ├── architect.md
│   ├── ux-designer.md
│   ├── ios-expert.md
│   ├── android-expert.md
│   ├── backend-expert.md
│   └── qa-verifier.md
├── schemas/             # Spec templates — fill these in for each feature
│   ├── feature-spec.md
│   ├── api-contract.md
│   ├── data-model.md
│   ├── interaction-spec.md
│   ├── platform-constraint.md
│   └── backend-agents.md
├── .claude/
│   └── commands/        # Slash commands for Claude Code
│       ├── propose.md   # Gate sequence: spec → architecture → UX → approval
│       ├── fan-out.md   # Launch parallel iOS + Android + Backend implementation
│       ├── steer.md     # Mid-flight course correction (amend or diverge)
│       ├── verify.md    # Per-platform + cross-platform coherence checks
│       ├── archive.md   # Merge delta specs into baseline, learn from steers
│       └── status.md    # Current change status dashboard
├── docs/                # Research and design docs
└── example/             # Worked example: a Notes app
    └── specs/
```

---

## Quick start

### 1. Copy this repo into your project

```bash
git clone https://github.com/yourusername/nl-native.git
cd my-app
cp -r ../nl-native/.claude .
cp -r ../nl-native/agents .
cp -r ../nl-native/schemas .
```

### 2. Set up your platform directories

```
my-app/
├── platforms/
│   ├── ios/        # Xcode project
│   ├── android/    # Android Studio project
│   └── backend/    # Backend service (configured on first /fan-out)
├── specs/
│   ├── core/       # Stable, archived specs (source of truth)
│   └── changes/    # Active feature work
├── agents/         # From this repo
└── .claude/        # From this repo
```

### 3. Customize the agent profiles

Edit `agents/ios-expert.md` and `agents/android-expert.md` to match your stack — min SDK versions, specific libraries, architecture patterns.

The backend agent profile is configured automatically on your first `/fan-out` — it asks you which backend service, database, and auth provider you want to use, then generates `platforms/backend/AGENTS.md`.

### 4. Propose your first feature

Open Claude Code in your project directory and run:

```
/propose user-authentication
```

This runs the full gate sequence: natural language → structured spec → architecture → UX → platform constraints → your approval before any code is written.

### 5. Fan out to native implementations

After approval:

```
/fan-out
```

Launches parallel subagents — iOS, Android, and Backend — each implementing the approved spec in native code. iOS and Android use mock data layers so they don't block on the backend.

### 6. Steer if needed

During or after implementation, if something isn't right:

```
/steer use tab navigation instead of a hamburger menu
```

Specific feedback triggers **amend mode** — surgical spec change, blast radius calculation, re-execute only affected tasks.

```
/steer the settings screen feels wrong
```

Vague feedback triggers **diverge mode** — generates 3 alternatives, you pick one, selection becomes a binding constraint.

### 7. Verify

```
/verify
```

Phase A: Each platform checks that all spec requirements are implemented and tested.
Phase B: Cross-platform coherence — same API contract, same auth flow, same data shapes, equivalent user experiences, integration verification (mock → real backend swap).

### 8. Archive

```
/archive
```

Merges the delta specs into your stable baseline. Scans the steer log for recurring patterns and proposes permanent rules for your AGENTS.md files. Next feature builds on the new foundation.

---

## Core concepts

### Specs, not code, are the source of truth

When you need to change behavior, you change the spec. Agents update the code. This inverts the usual relationship — instead of documentation that trails implementation, you have specifications that lead it.

### EARS notation

Requirements use EARS (Easy Approach to Requirements Syntax):

- `When [trigger], the system shall [behavior]`
- `While [state], the system shall [behavior]`
- `If [condition], then the system shall [behavior]`
- `The system shall [behavior]` (ubiquitous)

This makes requirements testable. Every requirement becomes a test scenario.

### Versioned API contracts

API contracts carry semantic versions. The Architect is the only agent who bumps versions. Platform agents declare which contract versions they depend on — if a contract changes mid-implementation, dependent agents halt and retask against the new version before continuing.

### Hub-and-spoke communication

Platform agents (iOS, Android, Backend) never communicate with each other directly. All cross-cutting decisions go through the Architect. This prevents coherence drift — the common failure mode in parallel development where platforms silently diverge.

### Mock data layers

During `/fan-out`, iOS and Android agents implement their API client as a protocol/interface with a mock conformance using fixture data from the API contract. This means mobile platforms can build, test, and demo the full UI without waiting for the backend. When the backend is ready, swapping mock for real requires zero changes to views or view models.

### Mid-flight steering

`/steer` lets you redirect implementation without restarting `/propose`. Two modes, auto-detected:

- **Amend** — you know what you want changed. Produces a spec delta, calculates blast radius, surgically re-executes affected tasks.
- **Diverge** — you know something's wrong but can't articulate it. Generates alternatives, you pick, selection becomes a constraint.

Checkpoints (committed at milestones during fan-out) let you revert to a clean state before applying a steer.

### Harness evolution

At `/archive` time, the steer log is reviewed for recurring corrections. Patterns get distilled into permanent rules in your AGENTS.md files — so the harness learns your preferences over time. Each feature makes the next one more aligned with your taste.

### Two-phase verification

**Phase A — Per-platform:** Does the implementation match the spec? Are all requirements covered? Do tests exist for each scenario? Does the backend implement all endpoints?

**Phase B — Cross-platform coherence:** Do all three platforms use the same API contract version? Do they serialize the same fields? Is the auth flow equivalent? Does the same user action produce the same outcome? Are mobile platforms connected to the real backend (or still on mocks)?

---

## Agent topology

```
                    ┌──────────────┐
                    │ Spec Analyst │  (translates intent → structured spec)
                    └──────┬───────┘
                           │
              ┌────────────┴─────────────┐
              │                          │
       ┌──────┴──────┐          ┌────────┴───────┐
       │  Architect  │◄────────►│  UX Designer   │
       │ (API, data) │          │  (interactions) │
       └──────┬──────┘          └────────────────┘
              │
    ┌─────────┼─────────┐
    │         │         │
┌───┴───┐  ┌──┴────┐  ┌─┴──────┐
│  iOS  │  │Android│  │Backend │  ← no lateral communication
│ Expert│  │ Expert│  │ Expert │    (mock data decouples mobile from backend)
└───┬───┘  └──┬────┘  └─┬──────┘
    └─────────┼──────────┘
              │
       ┌──────┴──────┐
       │ QA Verifier │  (reports only, never fixes)
       └─────────────┘
```

---

## The development lifecycle

```
/propose  →  /fan-out  →  /steer (as needed)  →  /verify  →  /archive
                ↑               ↓                              ↓
                └── checkpoint revert               harness learns
                    (if needed)                     from steers
```

---

## FAQ

**Do I need a backend agent?**
The Backend Expert is included by default but the harness works without it. If your app is frontend-only or you want to set up the backend manually, you can skip it. The first time `/fan-out` runs, it asks you to configure your backend stack.

**What backend services are supported?**
The spec layer is service-agnostic. At the spec level, you define abstract types, endpoints, and access patterns. The Backend Expert translates these to your chosen service — Supabase, Firebase, Cloudflare Workers, a custom server, or anything else. You configure the service in `platforms/backend/AGENTS.md`.

**What LLM / agent tool does this require?**
The slash commands are written for Claude Code. The agent profiles and spec format work with any LLM. If you're using Cursor, Windsurf, or another tool, the workflow translates directly — just adapt the command invocation.

**What about React Native?**
You can add an `rn-expert.md` agent profile if you want an additional target. The harness is platform-count-agnostic. Some teams use this with iOS + Android + web (Next.js) simultaneously.

**How is this different from just prompting Claude to write an app?**
One-shot prompting produces code with no spec, no versioning, no verification, and no baseline to build the next feature on. NL Native produces a spec system that accumulates knowledge — each archived feature makes the next one faster and more coherent. The harness also learns your preferences over time through `/steer` and harness evolution.

**What if I don't like what the agents build?**
Run `/steer` with your feedback. If you can describe what you want changed, it amends the spec surgically. If you just know something's off, it shows you alternatives to pick from. Checkpoints let you revert to a clean state if needed.

**Is the code AI-generated forever?**
The code is native Swift, Kotlin, and your backend language. Engineers can read, modify, and own it like any other codebase. The harness accelerates initial implementation — it doesn't prevent human involvement.

---

## Contributing

This repo is the harness itself. PRs welcome for:
- Additional agent profiles (web, backend variants)
- Platform-specific AGENTS.md templates (different iOS/Android/backend stack preferences)
- Improved schema templates
- Worked examples
- Translations of the workflow to other agent tools (Cursor, Windsurf, etc.)
