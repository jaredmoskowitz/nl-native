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
| **Plan 2 — scoring + judge-support harness (iOS)** | ✅ **built, validated, merged to main** |
| Plan 1b — Android oracle + correctness scorer | ⬜ next |
| Plan 1c — Backend oracle + correctness scorer | ⬜ |
| Plan 3 — eval orchestrator (verify loop prototyped here) | ⬜ after 1b/1c |
| Plan 3 — base-generation probe + verify-loop calibration | ✅ done — loop raises correctness 0.40→1.00 (haiku gen); L3 gate GREEN |
| **L3 promotion into `verify.md`** | ✅ **grafted (bounded auto-fix loop in Phase A.5)** |
| L1+L2 — barrier-synced fan-out | ⬜ remaining — the last roadmap item (own spec+plan+build) |

---

## Track A — Build the eval ruler

- [x] **Plan 1 — Toy feature + iOS oracle.** Notes+tags+search+pagination+auth NL Native specs; iOS logic-layer XCTest oracle (`swift test`, no simulator); correct + broken fixtures; `validate-ios-oracle.sh` proving it passes on correct / fails on exactly the seeded defects. *(Done.)*
- [x] **Plan 2 — Scoring + judge-support harness (iOS).** `eval/runner/` Python stdlib tooling: iOS correctness scorer (method-level oracle pass rate; lib-compiles-but-tests-don't → non-gradeable 0), blind packager, median aggregator, fixed rubric. The shared packager/aggregator/rubric serve all platforms; the LLM judge call is deferred to Plan 3. *(Done, merged to main.)*
- [ ] **Plan 1b — Android oracle + correctness scorer.** Mirror Plan 1: JUnit on the JVM via Gradle (no emulator), targeting the pinned interface ported to Kotlin; correct + broken fixtures + `validate-android-oracle.sh`. Plus an Android correctness scorer (`gradle test` parse) reusing the shared packager/aggregator.
- [ ] **Plan 1c — Backend oracle + correctness scorer.** Black-box HTTP tests against the running server (implementation-agnostic). Pick a concrete backend stack for the eval. Correct + broken fixtures + `validate-backend-oracle.sh` + a backend correctness scorer.
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

## Recommended sequence — all oracles first, then one comprehensive run

Decided May 28: the expensive, slow, nondeterministic part is the **Plan 3 live run** (fan-out + verify-loop + judge). Oracle-building is cheap, deterministic, and needed regardless — so build all three oracles first and do the costly Plan 3 run **once across all platforms**, rather than running iOS now and re-running later.

1. **Plan 1b (Android)** — oracle + correctness scorer (JUnit/JVM via Gradle, no emulator). ← next
2. **Plan 1c (Backend)** — oracle + correctness scorer (black-box HTTP).
3. **Plan 3 (all-platform)** — orchestrator. **First step is a cheap N=1 calibration dry-run** to validate the pipeline *and* confirm generation headroom (code good enough to compile, flawed enough to fix) before the full N=5 run. De-risking kept, "big run done once" honored.
4. **Decision gate:** does treatment beat baseline? Is 2 rounds enough (treatment vs ceiling)?
5. **L3 promotion** into `verify.md` (if it won).
6. **L1+L2** barrier-synced fan-out, measured on the all-platform ruler.

*Why not thin-iOS-slice-first:* it reaches a first number faster but forces re-running the expensive Plan 3 orchestration again for Android/Backend later. The calibration dry-run in step 3 recovers the de-risking without that duplication.

## Decision gates

- **After Plan 3's first run:** treatment vs baseline (does the loop raise correctness?) and treatment vs ceiling (is the ≤2-round cap leaving gains on the table?). Outcome decides L3 promotion and the final round cap.
- **Reading the numbers:** for L3, expect correctness↑ and quality≈flat (flat quality is a pass). Quality is the *primary* signal for L1+L2.
- **N=5 caveat:** detects only large effects; a null means "no large effect," not "no effect."

## Pointers

- Eval design spec: `docs/superpowers/specs/2026-05-28-nl-native-eval-design.md`
- Plan 1 (done): `docs/superpowers/plans/2026-05-28-nl-native-eval-plan1-feature-and-ios-oracle.md`
- Explainer: `docs/workflows-explained.html`
- Eval usage: `eval/README.md`
