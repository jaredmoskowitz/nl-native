# eval/runner — scoring + judge-support tooling

Deterministic Python (stdlib-only) tools that turn generated code into the eval's two numbers. The nondeterministic LLM judgment is added by the Plan 3 orchestrator, which calls the judge over the blind bundle and feeds its reads to the aggregator here.

## Tools
- `score_correctness.py <code-dir>` — drops the code into the iOS oracle slot, runs `swift build`/`swift test`, prints `{built, passed, total, score}` (method-level pass rate; build failure → 0).
- `blind_package.py --out BUNDLE --key KEY.json --seed N label=dir ...` — copies each submission's `*.swift` into anonymized `submission_<i>/` dirs in randomized (seeded) order; writes the private `submission_<i> -> label` key separately. The judge receives only BUNDLE.
- `aggregate_scores.py --key KEY.json --rubric quality_rubric.json read1.json ...` — medians the judge reads per criterion/composite and de-anonymizes via the key.
- `quality_rubric.json` — the fixed rubric (criteria, 1–5 scale, mean composite), shared with the Plan 3 judge prompt.

## Run the tests
```bash
python3 -m unittest discover -s eval/runner/tests -p "test_*.py"```
The correctness tests are integration tests that invoke `swift` against the Plan 1 reference fixtures (correct → 1.0, broken → 6/9, empty → 0.0).
```
