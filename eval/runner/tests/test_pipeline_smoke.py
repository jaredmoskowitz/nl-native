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
