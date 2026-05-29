# Plan 3 — Base-Generation Probe Findings (2026-05-28)

Before building the verify-loop orchestrator, we ran a cheap base-generation probe to answer the gating question: **does naturally-generated code have defects the held-out oracle catches?** (If not, the loop has nothing to measure.) Platform: iOS view-model logic (where defects are likeliest). Scorer: `eval/runner/score_correctness.py` (method-level, 9 oracle tests).

## Pre-registration (written before running)
- Generations cluster at 1.0 ⇒ **no headroom for that generator** → "feature too easy for this generator," NOT "loop doesn't work."
- Spread below 1.0 ⇒ headroom exists → build the loop.

## Results

**Strong model (inherited / Opus), K=5:** `1.0, 1.0, 1.0, 1.0, 1.0` — **no headroom.** Opus one-shots the iOS view-model logic every time (pagination boundary, search/filter reset, load-more no-op, auth-gating all correct). All 5 also independently flagged the same (harmless) spec ambiguity: search vs. tag mutual-exclusivity — which no oracle test exercises.

**Haiku model (weaker generator), K=5:** `0.0, 0.0, 1.0, 1.0, 0.0` — **headroom exists** (mean 0.4, clear spread).
- haiku_1, haiku_2: `built=false` — implementation compile errors (e.g. `error` declared immutable; assigning `String` to an `Error`-typed field).
- haiku_5: `built=false` — "tests failed to compile against submission" (non-conformant public interface — renamed/missing symbol).
- haiku_3, haiku_4: `1.0` — correct.

## Interpretation
- **Gate: GREEN — build the loop, with haiku as the generation model.** (Reported as a deliberate finding, not a silent switch: Opus is too strong for this feature to show loop value, so generation drops to haiku to create a realistic defect rate while QA + fix stay strong.)
- **Nuance:** the headroom is entirely **compile/conformance failures** (`built=false`/0), not compile-but-logic-wrong (e.g. 6/9). So the verify loop will be measured on *rescuing non-compiling / non-conformant generations*, not on fixing subtle logic bugs. Both are legitimate value, but the experiment measures the former. The QA-verify step must therefore actually compile the submission (the held-out oracle's `built=false` is driven by `swift build` / test-compile failure) to detect these — which is fair (the real harness's verify can compile).
- **Methodology preserved:** when the loop is built, instrument each round with BOTH the QA-found-count and the oracle score, so a null can be attributed correctly (no headroom / QA blind / fix ineffective). The unbounded "ceiling" = all QA-detectable defects resolved, which may sit below true correctness if QA can't see a defect.

## Next step
Build the minimal verify-loop experiment: haiku generates → QA-verify (compiles + checks spec) → route findings to a strong fix agent → re-verify → ≤2 rounds; score baseline (gen as-is) vs treatment (≤2 rounds) vs ceiling (unbounded) with the held-out oracle. Then decide L3 promotion on the measured delta.

Probe generations live under `eval/runs/probe/ios/` (gitignored — experiment output).
