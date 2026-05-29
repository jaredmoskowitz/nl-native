# NL Native Eval — Plan 2: Scoring + Judge-Support Harness (iOS)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deterministic, fully-testable Python (stdlib-only) tooling that, given a directory of generated iOS code, produces a **correctness** number (by running the Plan 1 held-out oracle) and the **judge-support** artifacts for quality scoring — a blind/randomized code bundle plus a median aggregator. The actual LLM judgment is deferred to Plan 3.

**Architecture:** Three small CLIs under `eval/runner/`. `score_correctness.py` drops a code dir into the oracle slot, runs `swift build`/`swift test`, and parses method-level pass rate. `blind_package.py` anonymizes + randomizes submissions into a judge-ready bundle and writes a private key. `aggregate_scores.py` medians multiple judge reads and de-anonymizes via the key. All deterministic; the nondeterministic LLM call is Plan 3's job (it calls the judge as a Workflow `agent()` over the blind bundle, then feeds reads to the aggregator).

**Tech Stack:** Python 3 standard library only (`argparse`, `json`, `re`, `subprocess`, `shutil`, `random`, `statistics`, `unittest`). No third-party packages. Reuses the Plan 1 Swift oracle at `eval/oracle/ios`.

---

## Background (read before starting)

This implements the iOS slice of §4 of `docs/superpowers/specs/2026-05-28-nl-native-eval-design.md` and Plan 2 of the roadmap (`docs/superpowers/plans/2026-05-28-nl-native-improvements-ROADMAP.md`). Invariants:

- **Two separate numbers.** Correctness = held-out test pass rate; quality = blind judge. Never blend them.
- **Correctness is method-level.** XCTest's `Executed N tests, with M failures` summary counts *assertion* failures, not methods — so we parse per-`Test Case` result lines instead and count passed/failed **methods**. Build/compile failure → correctness = 0.
- **Blind grading is mandatory.** The judge sees bare `.swift` source under anonymized `submission_<i>` directories in randomized order — no condition labels, no git, no logs. The label↔id key is written to a *separate* file the judge never receives.
- **Determinism.** Every tool here is deterministic (the packager takes a `--seed`). The only nondeterministic component — the LLM judge — is added in Plan 3.
- **Reuse, don't duplicate.** The scorer drives the existing `eval/oracle/ios` package and restores its slot to `.gitkeep` afterward, exactly like `validate-ios-oracle.sh`.

## File Structure

```
eval/runner/
  score_correctness.py     # code dir -> {built, passed, total, score} via the iOS oracle
  blind_package.py         # label=dir... -> anonymized randomized bundle + private key
  aggregate_scores.py      # N judge-read JSONs + key -> per-condition median scores
  quality_rubric.json      # fixed rubric (criteria, scale, composite rule)
  tests/
    test_score_correctness.py   # integration: correct=1.0, broken=6/9, empty=0.0
    test_blind_package.py       # anonymization, determinism, key correctness
    test_aggregate_scores.py    # median + de-anonymization
    test_pipeline_smoke.py      # package -> stub judge -> aggregate (no LLM)
```

**Responsibilities:** each CLI is one stage; the rubric is shared config; tests are stdlib `unittest`, runnable with `python3 -m unittest discover -s eval/runner/tests -t .` from the repo root.

---

## Task 1: Scaffold the runner directory and rubric

**Files:**
- Create: `eval/runner/quality_rubric.json`
- Create: `eval/runner/tests/.gitkeep`

- [ ] **Step 1: Create directories**

Run:
```bash
mkdir -p eval/runner/tests
touch eval/runner/tests/.gitkeep
```

- [ ] **Step 2: Write `eval/runner/quality_rubric.json`**

```json
{
  "criteria": ["idiomatic", "error_handling", "structure", "clarity"],
  "scale": { "min": 1, "max": 5 },
  "composite": "mean",
  "notes": "Each criterion is scored 1-5 by an independent blind judge that sees only bare source code (no condition labels, git history, or loop logs). Composite is the mean of the four criteria. This rubric is shared by the aggregator (Plan 2) and the judge prompt (Plan 3)."
}
```

- [ ] **Step 3: Commit**

```bash
git add eval/runner/quality_rubric.json eval/runner/tests/.gitkeep
git commit -m "eval: scaffold runner dir + fixed quality rubric"
```

---

## Task 2: Correctness scorer (TDD)

**Files:**
- Test: `eval/runner/tests/test_score_correctness.py`
- Create: `eval/runner/score_correctness.py`

- [ ] **Step 1: Write the failing test**

`eval/runner/tests/test_score_correctness.py`:

```python
import json
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
RUNNER = os.path.join(HERE, "..", "score_correctness.py")
REF = os.path.join(HERE, "..", "..", "oracle-reference", "ios")
CORRECT = os.path.join(REF, "correct", "NotesFeature")
BROKEN = os.path.join(REF, "broken", "NotesFeature")


def run(src_dir):
    proc = subprocess.run(
        [sys.executable, RUNNER, src_dir],
        capture_output=True, text=True,
    )
    assert proc.returncode == 0, f"scorer crashed: {proc.stderr}"
    return json.loads(proc.stdout)


class TestScoreCorrectness(unittest.TestCase):
    def test_correct_scores_full(self):
        r = run(CORRECT)
        self.assertTrue(r["built"])
        self.assertEqual(r["passed"], 9)
        self.assertEqual(r["total"], 9)
        self.assertEqual(r["score"], 1.0)

    def test_broken_scores_partial(self):
        r = run(BROKEN)
        self.assertTrue(r["built"])
        self.assertEqual(r["total"], 9)
        self.assertEqual(r["passed"], 6)  # 3 seeded defects fail 3 methods
        self.assertAlmostEqual(r["score"], 6 / 9)

    def test_empty_dir_is_build_failure_zero(self):
        with tempfile.TemporaryDirectory() as d:
            r = run(d)
            self.assertFalse(r["built"])
            self.assertEqual(r["score"], 0.0)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the test to verify it fails**

Run:
```bash
cd /Users/jaredmoskowitz/workspace/nl-native
python3 -m unittest discover -s eval/runner/tests -p "test_score_correctness.py" 2>&1 | tail -5
```
Expected: FAIL — `score_correctness.py` does not exist yet (the subprocess call fails / assertion error).

- [ ] **Step 3: Write `eval/runner/score_correctness.py`**

```python
#!/usr/bin/env python3
"""Score iOS correctness: run the Plan 1 held-out oracle against a directory of
generated NotesFeature sources and report the method-level pass rate.

Usage: score_correctness.py <dir-of-NotesFeature-swift-files>
Prints a JSON object: {platform, built, passed, total, score, summary}.
Build/compile failure => built=false, score=0.0. The oracle slot is always
restored to contain only .gitkeep afterward.
"""
import argparse
import json
import os
import re
import shutil
import subprocess

PKG = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "oracle", "ios"))
SLOT = os.path.join(PKG, "Sources", "NotesFeature")

# Matches per-test-case result lines, e.g.:
#   Test Case '-[NotesFeatureOracleTests.NotesViewModelOracleTests test_x]' passed (0.001 seconds)
RESULT_RE = re.compile(r"Test Case '.*?' (passed|failed)")


def restore_slot():
    os.makedirs(SLOT, exist_ok=True)
    for name in os.listdir(SLOT):
        if name.endswith(".swift"):
            os.remove(os.path.join(SLOT, name))
    open(os.path.join(SLOT, ".gitkeep"), "a").close()


def load_slot(src_dir):
    os.makedirs(SLOT, exist_ok=True)
    gitkeep = os.path.join(SLOT, ".gitkeep")
    if os.path.exists(gitkeep):
        os.remove(gitkeep)
    for name in os.listdir(src_dir):
        if name.endswith(".swift"):
            shutil.copy(os.path.join(src_dir, name), os.path.join(SLOT, name))


def score(src_dir):
    load_slot(src_dir)
    try:
        build = subprocess.run(["swift", "build"], cwd=PKG, capture_output=True, text=True)
        if build.returncode != 0:
            return {"platform": "ios", "built": False, "passed": 0,
                    "total": 0, "score": 0.0, "summary": "build failed"}
        test = subprocess.run(["swift", "test"], cwd=PKG, capture_output=True, text=True)
        out = test.stdout + test.stderr
        results = RESULT_RE.findall(out)
        passed = results.count("passed")
        failed = results.count("failed")
        total = passed + failed
        value = (passed / total) if total else 0.0
        return {"platform": "ios", "built": True, "passed": passed,
                "total": total, "score": value, "summary": f"{passed}/{total} methods passed"}
    finally:
        restore_slot()


def main():
    parser = argparse.ArgumentParser(description="Score iOS correctness via the held-out oracle.")
    parser.add_argument("src_dir", help="directory of generated NotesFeature *.swift files")
    args = parser.parse_args()
    print(json.dumps(score(args.src_dir), indent=2))


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run the test to verify it passes**

Run:
```bash
cd /Users/jaredmoskowitz/workspace/nl-native
python3 -m unittest discover -s eval/runner/tests -p "test_score_correctness.py" 2>&1 | tail -8
git status --short eval/oracle/ios/Sources/NotesFeature
```
Expected: `Ran 3 tests ... OK`. The slot status shows no tracked change (only `.gitkeep`, restored by the scorer).

- [ ] **Step 5: Commit**

```bash
git add eval/runner/score_correctness.py eval/runner/tests/test_score_correctness.py
git commit -m "eval: add iOS correctness scorer (method-level oracle pass rate)"
```

---

## Task 3: Blind packager (TDD)

**Files:**
- Test: `eval/runner/tests/test_blind_package.py`
- Create: `eval/runner/blind_package.py`

- [ ] **Step 1: Write the failing test**

`eval/runner/tests/test_blind_package.py`:

```python
import json
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
RUNNER = os.path.join(HERE, "..", "blind_package.py")


def make_src(root, name, body):
    d = os.path.join(root, name)
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "Impl.swift"), "w") as fh:
        fh.write(body)
    return d


class TestBlindPackage(unittest.TestCase):
    def _package(self, work, seed):
        a = make_src(work, "a", "// baseline code")
        b = make_src(work, "b", "// treatment code")
        c = make_src(work, "c", "// ceiling code")
        out = os.path.join(work, "bundle")
        key = os.path.join(work, "key.json")
        proc = subprocess.run(
            [sys.executable, RUNNER, "--out", out, "--key", key, "--seed", str(seed),
             "baseline=" + a, "treatment=" + b, "ceiling=" + c],
            capture_output=True, text=True,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        return out, json.load(open(key))

    def test_anonymized_dirs_and_no_label_leak(self):
        with tempfile.TemporaryDirectory() as work:
            out, key = self._package(work, seed=1)
            subs = sorted(os.listdir(out))
            self.assertEqual(subs, ["submission_0", "submission_1", "submission_2"])
            # The judge-facing bundle must not contain any condition label.
            for sub in subs:
                files = os.listdir(os.path.join(out, sub))
                self.assertEqual(files, ["Impl.swift"])
            blob = "".join(
                open(os.path.join(out, s, "Impl.swift")).read() for s in subs
            )
            # code bodies carry the labels in this fixture; that's fine — what must NOT
            # leak is the *directory naming*. Assert names are purely positional:
            self.assertTrue(all(s.startswith("submission_") for s in subs))

    def test_key_is_a_valid_permutation(self):
        with tempfile.TemporaryDirectory() as work:
            _, key = self._package(work, seed=1)
            self.assertEqual(sorted(key.keys()), ["submission_0", "submission_1", "submission_2"])
            self.assertEqual(sorted(key.values()), ["baseline", "ceiling", "treatment"])

    def test_deterministic_for_same_seed(self):
        with tempfile.TemporaryDirectory() as w1, tempfile.TemporaryDirectory() as w2:
            _, k1 = self._package(w1, seed=42)
            _, k2 = self._package(w2, seed=42)
            self.assertEqual(k1, k2)

    def test_seed_changes_order(self):
        # There exists at least one seed pair producing different mappings.
        with tempfile.TemporaryDirectory() as w:
            mappings = set()
            for s in range(10):
                out = os.path.join(w, f"bundle{s}")
                key = os.path.join(w, f"key{s}.json")
                a = make_src(w, f"a{s}", "x"); b = make_src(w, f"b{s}", "y"); c = make_src(w, f"c{s}", "z")
                subprocess.run(
                    [sys.executable, RUNNER, "--out", out, "--key", key, "--seed", str(s),
                     "baseline=" + a, "treatment=" + b, "ceiling=" + c],
                    capture_output=True, text=True, check=True,
                )
                mappings.add(tuple(sorted(json.load(open(key)).items())))
            self.assertGreater(len(mappings), 1)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the test to verify it fails**

Run:
```bash
cd /Users/jaredmoskowitz/workspace/nl-native
python3 -m unittest discover -s eval/runner/tests -p "test_blind_package.py" 2>&1 | tail -5
```
Expected: FAIL — `blind_package.py` does not exist.

- [ ] **Step 3: Write `eval/runner/blind_package.py`**

```python
#!/usr/bin/env python3
"""Produce a blind, randomized bundle of code submissions for the quality judge,
plus a private key mapping anonymized ids back to condition labels.

Usage:
  blind_package.py --out BUNDLE --key KEY.json --seed N label=dir [label=dir ...]

The BUNDLE contains submission_0/, submission_1/, ... each holding only the
*.swift files of one submission, with NO label in the directory name. The KEY
(written separately, never inside BUNDLE) maps submission_<i> -> label.
Deterministic given --seed.
"""
import argparse
import json
import os
import random
import shutil


def package(entries, out_dir, key_file, seed):
    order = list(range(len(entries)))
    random.Random(seed).shuffle(order)
    os.makedirs(out_dir, exist_ok=True)
    key = {}
    for sub_index, orig_index in enumerate(order):
        label, src = entries[orig_index]
        sub_name = "submission_%d" % sub_index
        dst = os.path.join(out_dir, sub_name)
        os.makedirs(dst, exist_ok=True)
        for name in sorted(os.listdir(src)):
            if name.endswith(".swift"):
                shutil.copy(os.path.join(src, name), os.path.join(dst, name))
        key[sub_name] = label
    with open(key_file, "w") as fh:
        json.dump(key, fh, indent=2, sort_keys=True)
    return key


def parse_entry(value):
    label, sep, path = value.partition("=")
    if not sep or not label or not path:
        raise argparse.ArgumentTypeError("expected label=dir, got %r" % value)
    return (label, path)


def main():
    parser = argparse.ArgumentParser(description="Blind-package submissions for the judge.")
    parser.add_argument("--out", required=True, help="output bundle directory")
    parser.add_argument("--key", required=True, help="path to write the private id->label key")
    parser.add_argument("--seed", type=int, required=True, help="deterministic shuffle seed")
    parser.add_argument("entries", nargs="+", type=parse_entry, help="label=dir pairs")
    args = parser.parse_args()
    package(args.entries, args.out, args.key, args.seed)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run the test to verify it passes**

Run:
```bash
cd /Users/jaredmoskowitz/workspace/nl-native
python3 -m unittest discover -s eval/runner/tests -p "test_blind_package.py" 2>&1 | tail -6
```
Expected: `Ran 4 tests ... OK`.

- [ ] **Step 5: Commit**

```bash
git add eval/runner/blind_package.py eval/runner/tests/test_blind_package.py
git commit -m "eval: add blind packager (anonymize + randomize submissions for judge)"
```

---

## Task 4: Median aggregator (TDD)

**Files:**
- Test: `eval/runner/tests/test_aggregate_scores.py`
- Create: `eval/runner/aggregate_scores.py`

- [ ] **Step 1: Write the failing test**

`eval/runner/tests/test_aggregate_scores.py`:

```python
import json
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
RUNNER = os.path.join(HERE, "..", "aggregate_scores.py")
RUBRIC = os.path.join(HERE, "..", "quality_rubric.json")


def write_json(path, obj):
    with open(path, "w") as fh:
        json.dump(obj, fh)
    return path


class TestAggregateScores(unittest.TestCase):
    def test_medians_and_deanonymizes(self):
        with tempfile.TemporaryDirectory() as work:
            key = write_json(os.path.join(work, "key.json"),
                             {"submission_0": "treatment", "submission_1": "baseline"})
            # three judge reads; composite for submission_0 = [3,5,4] -> median 4
            r1 = write_json(os.path.join(work, "r1.json"), {
                "submission_0": {"idiomatic": 3, "error_handling": 3, "structure": 3, "clarity": 3, "composite": 3},
                "submission_1": {"idiomatic": 2, "error_handling": 2, "structure": 2, "clarity": 2, "composite": 2},
            })
            r2 = write_json(os.path.join(work, "r2.json"), {
                "submission_0": {"idiomatic": 5, "error_handling": 5, "structure": 5, "clarity": 5, "composite": 5},
                "submission_1": {"idiomatic": 2, "error_handling": 2, "structure": 2, "clarity": 2, "composite": 2},
            })
            r3 = write_json(os.path.join(work, "r3.json"), {
                "submission_0": {"idiomatic": 4, "error_handling": 4, "structure": 4, "clarity": 4, "composite": 4},
                "submission_1": {"idiomatic": 1, "error_handling": 1, "structure": 1, "clarity": 1, "composite": 1},
            })
            proc = subprocess.run(
                [sys.executable, RUNNER, "--key", key, "--rubric", RUBRIC, r1, r2, r3],
                capture_output=True, text=True,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            out = json.loads(proc.stdout)
            self.assertEqual(out["treatment"]["composite"], 4)   # median of 3,5,4
            self.assertEqual(out["baseline"]["composite"], 2)    # median of 2,2,1
            self.assertEqual(out["treatment"]["idiomatic"], 4)
            self.assertIn("clarity", out["baseline"])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the test to verify it fails**

Run:
```bash
cd /Users/jaredmoskowitz/workspace/nl-native
python3 -m unittest discover -s eval/runner/tests -p "test_aggregate_scores.py" 2>&1 | tail -5
```
Expected: FAIL — `aggregate_scores.py` does not exist.

- [ ] **Step 3: Write `eval/runner/aggregate_scores.py`**

```python
#!/usr/bin/env python3
"""Median-aggregate multiple blind judge reads and de-anonymize via the key.

Usage:
  aggregate_scores.py --key KEY.json --rubric RUBRIC.json read1.json [read2.json ...]

Each read JSON maps submission_<i> -> {criterion: score, ..., "composite": score}.
Output (stdout) maps the de-anonymized condition label -> median scores per
criterion and composite, across all reads.
"""
import argparse
import json
import statistics


def aggregate(reads, key, criteria):
    fields = list(criteria) + ["composite"]
    result = {}
    for sub_id, label in key.items():
        per_field = {}
        for field in fields:
            values = [r[sub_id][field] for r in reads if sub_id in r and field in r[sub_id]]
            per_field[field] = statistics.median(values) if values else None
        result[label] = per_field
    return result


def main():
    parser = argparse.ArgumentParser(description="Median-aggregate + de-anonymize judge reads.")
    parser.add_argument("--key", required=True, help="submission_<i> -> label key JSON")
    parser.add_argument("--rubric", required=True, help="quality rubric JSON (for criteria)")
    parser.add_argument("reads", nargs="+", help="judge read JSON files")
    args = parser.parse_args()

    with open(args.key) as fh:
        key = json.load(fh)
    with open(args.rubric) as fh:
        rubric = json.load(fh)
    reads = []
    for path in args.reads:
        with open(path) as fh:
            reads.append(json.load(fh))

    print(json.dumps(aggregate(reads, key, rubric["criteria"]), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run the test to verify it passes**

Run:
```bash
cd /Users/jaredmoskowitz/workspace/nl-native
python3 -m unittest discover -s eval/runner/tests -p "test_aggregate_scores.py" 2>&1 | tail -6
```
Expected: `Ran 1 test ... OK`.

- [ ] **Step 5: Commit**

```bash
git add eval/runner/aggregate_scores.py eval/runner/tests/test_aggregate_scores.py
git commit -m "eval: add median aggregator (de-anonymize blind judge reads)"
```

---

## Task 5: End-to-end pipeline smoke test (package -> stub judge -> aggregate)

Proves the deterministic quality pipeline wires together without any LLM: a **stub judge** reads the anonymized bundle (it only sees `submission_<i>` dirs, never the key) and emits scores; the aggregator de-anonymizes them.

**Files:**
- Test: `eval/runner/tests/test_pipeline_smoke.py`

- [ ] **Step 1: Write the smoke test**

`eval/runner/tests/test_pipeline_smoke.py`:

```python
import json
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
PACKAGER = os.path.join(HERE, "..", "blind_package.py")
AGGREGATOR = os.path.join(HERE, "..", "aggregate_scores.py")
RUBRIC = os.path.join(HERE, "..", "quality_rubric.json")
REF = os.path.join(HERE, "..", "..", "oracle-reference", "ios")
CORRECT = os.path.join(REF, "correct", "NotesFeature")
BROKEN = os.path.join(REF, "broken", "NotesFeature")


def stub_judge(bundle_dir):
    """Stand-in for Plan 3's LLM judge. Sees ONLY the anonymized bundle (no key).
    Scores each submission by a trivial deterministic proxy: lines of code (longer
    NotesViewModel == 'more complete'). Returns the read dict the aggregator expects."""
    read = {}
    for sub in sorted(os.listdir(bundle_dir)):
        loc = 0
        sub_path = os.path.join(bundle_dir, sub)
        for name in os.listdir(sub_path):
            if name.endswith(".swift"):
                with open(os.path.join(sub_path, name)) as fh:
                    loc += sum(1 for _ in fh)
        score = 5 if loc > 250 else 3   # arbitrary deterministic proxy
        read[sub] = {"idiomatic": score, "error_handling": score,
                     "structure": score, "clarity": score, "composite": score}
    return read


class TestPipelineSmoke(unittest.TestCase):
    def test_package_judge_aggregate(self):
        with tempfile.TemporaryDirectory() as work:
            bundle = os.path.join(work, "bundle")
            key = os.path.join(work, "key.json")
            subprocess.run(
                [sys.executable, PACKAGER, "--out", bundle, "--key", key, "--seed", "3",
                 "correct=" + CORRECT, "broken=" + BROKEN],
                capture_output=True, text=True, check=True,
            )
            # three stub-judge reads (deterministic here, would be 3 LLM reads in Plan 3)
            read_paths = []
            for i in range(3):
                p = os.path.join(work, f"read{i}.json")
                with open(p, "w") as fh:
                    json.dump(stub_judge(bundle), fh)
                read_paths.append(p)

            proc = subprocess.run(
                [sys.executable, AGGREGATOR, "--key", key, "--rubric", RUBRIC] + read_paths,
                capture_output=True, text=True,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            out = json.loads(proc.stdout)
            # de-anonymized labels present
            self.assertEqual(sorted(out.keys()), ["broken", "correct"])
            for label in ("broken", "correct"):
                self.assertIn("composite", out[label])
                self.assertIn("clarity", out[label])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the full runner suite**

Run:
```bash
cd /Users/jaredmoskowitz/workspace/nl-native
python3 -m unittest discover -s eval/runner/tests -p "test_*.py" 2>&1 | tail -8
```
Expected: all tests pass — `Ran 9 tests ... OK` (3 correctness + 4 packager + 1 aggregator + 1 smoke).

- [ ] **Step 3: Commit**

```bash
git add eval/runner/tests/test_pipeline_smoke.py
git commit -m "eval: add deterministic quality-pipeline smoke (package -> stub judge -> aggregate)"
```

---

## Task 6: Document the runner and update eval status

**Files:**
- Create: `eval/runner/README.md`
- Modify: `eval/README.md` (Status table row for "Scoring + blind judge harness")

- [ ] **Step 1: Write `eval/runner/README.md`**

```markdown
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

- [ ] **Step 2: Update the Status table in `eval/README.md`**

Change the row:
```markdown
| Scoring + blind judge harness | ⬜ planned |
```
to:
```markdown
| Scoring + judge-support harness (iOS) | ✅ deterministic tooling built; LLM judge call lands in Plan 3 |
```

- [ ] **Step 3: Commit**

```bash
git add eval/runner/README.md eval/README.md
git commit -m "eval: document runner tooling + update status"
```

---

## Done criteria

- [ ] `python3 -m unittest discover -s eval/runner/tests -p "test_*.py" -t .` is green (9 tests).
- [ ] `score_correctness.py` returns 1.0 for the correct reference, 6/9 for the broken fixture, 0.0 for a non-building dir, and restores the oracle slot to only `.gitkeep`.
- [ ] `blind_package.py` produces label-free `submission_<i>` dirs + a separate key, deterministic per seed.
- [ ] `aggregate_scores.py` medians reads and de-anonymizes via the key.
- [ ] The pipeline smoke proves package → (stub) judge → aggregate end-to-end with no LLM.
- [ ] `eval/runner/README.md` written; `eval/README.md` status updated.
- [ ] All committed on branch `nl-native-eval-plans`.

## Follow-on (Plan 3)

The orchestrator runs `/fan-out` once, forks baseline/treatment/ceiling worktrees, then per condition: calls `score_correctness.py` for correctness, and for quality runs `blind_package.py` → judges each `submission_<i>` 3× via Workflow `agent()` (structured scores against `quality_rubric.json`) → `aggregate_scores.py`. N=5 repeats; reports distributions + per-round trajectory.
```
