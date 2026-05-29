# NL Native Eval — Design Spec

**Date:** 2026-05-28
**Status:** Approved (brainstorming) — pending implementation plan
**Topic:** A measurement harness ("the ruler") that tells us whether changes to the NL Native harness improve generated **code quality and correctness**, starting with the verify→fix→re-verify loop.

---

## 1. Context & motivation

We are improving the NL Native harness using Anthropic's "Building Effective AI Agents" workflow patterns. Three lessons were identified (see `docs/workflows-explained.html`):

- **L1** — `/fan-out`'s parallelism is asserted, not enforced (one context role-plays all platforms → cross-platform isolation is structurally violated).
- **L2** — naive real-parallelism breaks contract-version monitoring → redesign to **barrier-synced milestones**.
- **L3** — `/verify` is an evaluator but not an evaluator-*optimizer* → close the loop: verify → route finding to owning platform expert → fix → re-verify → until clean.

**Locked decisions** (see memory `project_nl_native_workflow_improvements`): enforce isolation; build order = L3 verify-loop first, then barrier fan-out; git **Option B** (worktree per platform); six design defaults including `≤2` fix rounds and re-verify-only-failed-finding-then-full-sweep.

**This spec defines the eval, not the loop.** Without an independent ruler we cannot tell whether the L3 loop (or any later change) actually improves anything. The verify-loop prototype is simply the **first change pushed through this eval**.

---

## 2. What the eval answers (dependent variables & hypotheses)

Two metrics, kept separate so neither masks the other:

- **Correctness** — held-out test pass rate.
- **Quality** — independent judge score.

**Hypotheses, written down to prevent misreading results:**

- The verify loop fixes spec-compliance BLOCKERs → **it should move correctness up**. This is its primary DV.
- The verify loop does **not** refactor for elegance → **quality is expected to stay roughly flat**. A flat quality number is a *pass*, not a failure.
- **Quality** is the primary DV for the *later* barrier-fan-out change (L1+L2), where real isolation should improve cross-platform coherence. Two numbers serve two experiments.

---

## 3. Experimental design

### 3.1 Paired structure (validity prerequisite)

If each condition independently re-ran `/fan-out`, most score variance would be *fan-out* noise rather than *loop* effect, and N=5 would drown the signal. Therefore:

```
per repeat r in 1..N:
  run /fan-out ONCE  →  snapshot post-fan-out state (git checkpoint = branch point)
       ├── fork worktree A → apply BASELINE  → score
       ├── fork worktree B → apply TREATMENT → score
       └── fork worktree C → apply CEILING   → score
```

All three conditions start from the **same** post-fan-out code; the **only** difference is the verify step. The score delta is therefore attributable to the loop. This is a **paired (within-sample) comparison**, which is what makes N=5 viable. It composes with git Option B: the fan-out checkpoint is the branch point; the three conditions run in forked worktrees.

### 3.2 Conditions

| Condition | Verify behavior | Measures |
|---|---|---|
| **Baseline** | `/verify` once, then stop (today's behavior — QA reports, no auto-fix) | code as fan-out + one verify leaves it |
| **Treatment** | the `≤2`-round auto-fix loop (default d) | the proposed L3 change |
| **Ceiling** | **unbounded** auto-fix loop (same QA-driven loop, no round cap) | "all **QA-detectable** defects resolved" |

**Ceiling is the unbounded loop, NOT an oracle fixer.** The unbounded loop validates whether 2 rounds is enough (it shares QA's detection limits, so treatment-vs-ceiling isolates *round count* as the variable). An oracle-fixer ceiling answers a different question — "is QA's *detection* good enough?" — and is deferred to a separate later probe (§8). The two must not be conflated.

### 3.3 Repeats

- **N = 5 repeats per condition** for the first cut.
- Report **distributions**, not single numbers.
- Explicit caveat: **N=5 detects only large effects.** A null result means "no large effect detected," not "no effect."

---

## 4. Metrics

### 4.1 Correctness — held-out tests (all three platforms)

- **iOS** — XCTest on the logic layer. Preferred: pure-Swift SPM module run via `swift test` on macOS (no simulator). Fallback: `xcodebuild test` against a simulator destination if logic/UI are entangled.
- **Android** — JUnit on the JVM (no emulator). Fast.
- **Backend** — headless test runner.
- Score = fraction of held-out tests passing.
- **Compile/build failure → correctness = 0 for that cell.** This is legitimate signal (baseline left it broken; treatment may repair it), but must be defined so runs don't error out and lose data points — especially iOS, where `xcodebuild` hard-fails.

### 4.2 Quality — independent judge (all three platforms, static read)

- A grader agent, **independent of the QA Verifier prompt and rubric** (no shared text), static-reads the generated code and scores quality on a fixed rubric.
- **Blind grading is a hard requirement.** Artifacts handed to the judge are stripped to **bare source code** — no condition labels, no git history, no loop logs — and presented in **randomized order**. Otherwise the judge infers "this one looks more worked-on" and inflates treatment.
- Judge runs at **low temperature, 3× per artifact; take the median** (judge noise stacks on generation noise).

---

## 5. Toy feature & oracle provenance

- **Purpose-built mobile feature**, rich enough to induce natural defects: *notes with tags + search + pagination + auth*. Surface area: several endpoints, ≥2 error codes, an auth rule, a pagination edge case — lots of view-model/repository logic where compliance defects live.
- **Held-out tests are authored first, from the spec, by us** (not generated by the harness) and live in a **grader-only location the platform agents never read** (`eval/oracle/{ios,android,backend}/`), separate from the worked project (`eval/workdir/`). Out-of-reach must be **mechanized**, not merely intended.
- The feature must have demonstrated **headroom**: a dry run should confirm the baseline leaves real, test-detectable gaps. If baseline already scores ~ceiling, the feature is too easy and must be made harder before trusting any delta.

---

## 6. Architecture & orchestration

- The eval is itself a **Workflow-tool script** — fan-out once → fork three worktrees → run conditions in parallel → judge. (It is an orchestrator-workers + parallelization workflow.)
- **Directory layout (proposed):**
  ```
  eval/
    workdir/            # the worked project the harness operates in (specs + platform AGENTS.md + generated code)
    oracle/             # grader-only — NEVER copied into workdir
      ios/  android/  backend/   # held-out tests
    feature-spec/       # the purpose-built feature's NL Native specs (input)
    runner/             # the Workflow-tool eval script + scoring/judge harness
    results/            # per-run distributions, per-round trajectories, reports
  ```
- **iOS cost relief:** encode "logic lives in a pure-Swift, UI-free testable module" in iOS `AGENTS.md` so XCTest runs via `swift test` without a simulator. Good architecture regardless.

---

## 7. Reporting & interpretation

Per condition, per platform:
- The **distribution** of both scores across N=5 repeats.
- The **per-round score trajectory inside treatment** (round 0 = post-fan-out, round 1, round 2) — the cleanest read on whether round 2 earns its cost.
- Correctness vs quality reported as **two separate numbers**.
- Interpretation notes baked into the report: expected correctness↑ / quality≈flat for the verify loop; N=5 large-effects-only caveat.

---

## 8. Out of scope / future probes

- **Oracle-fixer ceiling** — a separate experiment answering "is QA detection good enough?" (a fixer that can see the held-out tests / true defects). Deferred.
- **Multi-feature suite** and **larger N** for smaller-effect detection.
- **Multi-platform correctness for the barrier-fan-out change** — quality-of-coherence metrics specific to L1+L2.

---

## 9. Success criteria for the eval itself

The eval is "good enough to trust" when:
1. The paired structure is in place (one fan-out, three forked conditions).
2. The toy feature demonstrably has headroom (baseline < ceiling on a dry run).
3. Held-out tests are mechanically unreachable by platform agents.
4. The judge is independent + blind + median-of-3.
5. A full run produces the distribution + per-round trajectory report described in §7.

Only then do we read the verify-loop result as signal.
