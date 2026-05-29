# NL Native Workflow Improvements — Master Roadmap

**Last updated:** 2026-05-28

## North star

Improve the NL Native harness with agentic workflow patterns, and prove each change improves the *generated code* with an independent eval ("the ruler"). **Build the ruler first, measure, and only promote changes that win.** No vibes.

The two harness improvements being pursued:
- **L3 — verify→fix→re-verify loop** (evaluator-optimizer): QA reports → orchestration routes the finding to the owning platform expert → fix in its worktree → re-verify → ≤2 rounds → escalate survivors. (Built order: first.)
- **L1+L2 — barrier-synced fan-out** (real parallelization): enforce platform isolation; the Architect reconciles + freezes contracts only at milestone barriers; worktree per platform. (Built order: second.)

Background/why: `docs/workflows-explained.html`. Locked decisions: enforce isolation; L3 before L1+L2; git Option B (worktree per platform); six design defaults. Eval rationale + full design: `docs/superpowers/specs/2026-05-28-nl-native-eval-design.md`.

---

## Status snapshot

| Item | State |
|---|---|
| Lessons + locked decisions + explainer page | ✅ done (on main) |
| Eval design spec | ✅ done (on main) |
| **Plan 1 — toy feature + iOS held-out oracle** | ✅ **built, validated, merged to main** |
| Plan 1b — Android oracle | ⬜ next |
| Plan 1c — Backend oracle | ⬜ |
| Plan 2 — scoring + blind judge harness | ⬜ |
| Plan 3 — eval orchestrator (verify loop prototyped here) | ⬜ |
| L3 promotion into `verify.md` | ⬜ gated on Plan 3 result |
| L1+L2 — barrier-synced fan-out | ⬜ after L3 |

---

## Track A — Build the eval ruler

- [x] **Plan 1 — Toy feature + iOS oracle.** Notes+tags+search+pagination+auth NL Native specs; iOS logic-layer XCTest oracle (`swift test`, no simulator); correct + broken fixtures; `validate-ios-oracle.sh` proving it passes on correct / fails on exactly the seeded defects. *(Done.)*
- [ ] **Plan 1b — Android oracle.** Mirror Plan 1: JUnit on the JVM (no emulator), targeting the same pinned interface ported to Kotlin. Deliver: Android oracle + correct/broken fixtures + `validate-android-oracle.sh`.
- [ ] **Plan 1c — Backend oracle.** Black-box HTTP tests against the running server (implementation-agnostic). Pick a concrete backend stack for the eval. Deliver: backend oracle + correct/broken fixtures + `validate-backend-oracle.sh`.
- [ ] **Plan 2 — Scoring + blind judge harness.** Input: a directory of generated code. Output two numbers per platform: **correctness** (run the held-out oracle → pass rate; compile/build failure → 0) and **quality** (blind, randomized-order, median-of-3 judge, independent of the QA Verifier prompt).
- [ ] **Plan 3 — Eval orchestrator.** The Workflow-tool runner: run `/fan-out` **once** → fork three worktrees → apply the three verify **strategies** (baseline / treatment ≤2-round loop / unbounded-loop ceiling) → score via Plan 2 → aggregate distributions + per-round trajectory + report. N=5 repeats, paired. **This is where the verify loop is first prototyped and measured.**

## Track B — Harness improvements (gated on the ruler)

- [ ] **L3 promotion.** If treatment beats baseline in Plan 3 (correctness↑), graft the verify→fix→re-verify loop into the real `/verify` (`verify.md`). Keep QA "reports only"; orchestration routes.
- [ ] **L1+L2 — barrier-synced fan-out.** Own spec + plan. Enforce isolation via real subagents in per-platform worktrees; Architect reconciles/freezes contracts at milestone barriers (replacing continuous contract monitoring). Measured mainly on the **quality/coherence** number, not correctness.

---

## Dependencies

```
Plan 1 ─┬─> Plan 1b ─┐
        ├─> Plan 1c ─┤
        └────────────┴─> Plan 2 ─> Plan 3 ─> L3 promotion
                                       │
L1+L2 (reuses the ruler) ──────────────┘ (can follow independently)
```
Plan 2 needs ≥1 oracle. Plan 3 needs Plan 2 + the oracle(s) it scores. L3 promotion needs a Plan 3 result.

## Recommended sequence — thin iOS slice first

Fastest path to a real, decision-grade number, and it leads with the priority platform (iOS):

1. **Plan 2 (iOS-only)** — scoring + judge wired to the existing iOS oracle.
2. **Plan 3 (iOS-only)** — orchestrator end-to-end on iOS → **first verify-loop measurement.**
3. **Decision gate:** does treatment beat baseline? Is 2 rounds enough (treatment vs ceiling)?
4. **Broaden:** Plan 1b (Android), Plan 1c (Backend), extend Plan 2/3 to all platforms.
5. **L3 promotion** into `verify.md` (if it won).
6. **L1+L2** barrier-synced fan-out, measured on the broadened ruler.

*Alternative — breadth-first:* build Plan 1b + 1c before Plan 2/3 if you want all-platform correctness from the very first measurement. Trade-off: slower to the first number.

## Decision gates

- **After Plan 3's first run:** treatment vs baseline (does the loop raise correctness?) and treatment vs ceiling (is the ≤2-round cap leaving gains on the table?). Outcome decides L3 promotion and the final round cap.
- **Reading the numbers:** for L3, expect correctness↑ and quality≈flat (flat quality is a pass). Quality is the *primary* signal for L1+L2.
- **N=5 caveat:** detects only large effects; a null means "no large effect," not "no effect."

## Pointers

- Eval design spec: `docs/superpowers/specs/2026-05-28-nl-native-eval-design.md`
- Plan 1 (done): `docs/superpowers/plans/2026-05-28-nl-native-eval-plan1-feature-and-ios-oracle.md`
- Explainer: `docs/workflows-explained.html`
- Eval usage: `eval/README.md`
