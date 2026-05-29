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
