<p align="center"><strong>NL Native — Evaluation Harness</strong></p>

<p align="center"><em>A ruler for measuring whether changes to the harness improve generated code.</em></p>

---

## Why this exists

NL Native is being improved using agentic workflow patterns (an evaluator–optimizer verify loop, a barrier-synced fan-out). The open question for any such change is simple and unforgiving: **does it actually make the generated iOS / Android / Backend code better, or does it just feel better?**

This harness answers that with measurement, not vibes. It runs the harness on a fixed toy feature under different configurations and scores the output, so a change can be accepted or rejected on evidence.

## What it measures

Two numbers, kept separate so neither can mask the other:

- **Correctness** — held-out test pass rate. The tests are authored independently, live here under `oracle/` where the platform agents can never read them, and run against whatever the harness produces. iOS/Android exercise the logic layer (view models, repositories, mappers); Backend is black-box HTTP.
- **Quality** — an independent, blind judge (separate from the harness's own QA Verifier; median of three reads) scores the source statically across all three platforms.

## How it compares

A **paired** design: the harness runs `/fan-out` **once**, then the same post-fan-out code is forked into three conditions that differ *only* in the verify step:

| Condition | Verify behaviour |
|---|---|
| **Baseline** | `/verify` once, then stop (today's behaviour) |
| **Treatment** | the bounded verify→fix→re-verify loop (≤ 2 rounds) |
| **Ceiling** | the unbounded loop (all QA-detectable defects resolved) |

Because only the verify step varies, any score gap is attributable to the change, and a small number of repeats yields real signal.

## Layout

```
eval/
  feature-spec/        NL Native specs for the toy feature (harness input)
  oracle/              held-out tests — grader-only, never copied into a workdir
    ios/               Swift Package; Sources/NotesFeature is an empty "slot"
                       the implementation-under-test drops into
  oracle-reference/    validation fixtures: a correct impl and a broken one,
                       used to prove the oracle discriminates
  scripts/             validation / run scripts
```

## Run what exists today

The iOS oracle is built and self-checking. From the repo root:

```bash
./eval/scripts/validate-ios-oracle.sh
```

This drops the correct reference into the slot (expects all tests green), then the broken fixture (expects exactly the seeded defects to fail), and asserts the oracle discriminates. It should end with:

```
ORACLE VALIDATION OK: passes on correct, fails on exactly the seeded defects.
```

## Status

| Piece | State |
|---|---|
| iOS held-out oracle + toy feature spec | ✅ built & validated |
| Android oracle (JUnit/JVM) + scorer | ✅ built & validated |
| Backend oracle (black-box HTTP) | ⬜ planned |
| Scoring + judge-support harness (iOS) | ✅ deterministic tooling built; LLM judge call lands in Plan 3 |
| Eval orchestrator (fan-out → fork → score → report) | ⬜ planned |

The verify loop is prototyped *inside* the orchestrator as the treatment/ceiling strategy and only promoted into the real `/verify` if it wins here.

## Design docs

- Design spec: [`../docs/superpowers/specs/2026-05-28-nl-native-eval-design.md`](../docs/superpowers/specs/2026-05-28-nl-native-eval-design.md)
- Plan 1 (this milestone): [`../docs/superpowers/plans/2026-05-28-nl-native-eval-plan1-feature-and-ios-oracle.md`](../docs/superpowers/plans/2026-05-28-nl-native-eval-plan1-feature-and-ios-oracle.md)
