import json
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
RUNNER = os.path.join(HERE, "..", "score_correctness_backend.py")
REF = os.path.join(HERE, "..", "..", "oracle-reference", "backend")
CORRECT = os.path.join(REF, "correct")
BROKEN = os.path.join(REF, "broken")


def run(src_dir):
    proc = subprocess.run([sys.executable, RUNNER, src_dir], capture_output=True, text=True)
    assert proc.returncode == 0, f"scorer crashed: {proc.stderr}"
    return json.loads(proc.stdout)


class TestScoreCorrectnessBackend(unittest.TestCase):
    def test_correct_scores_full(self):
        r = run(CORRECT)
        self.assertTrue(r["built"])
        self.assertEqual(r["passed"], 8)
        self.assertEqual(r["total"], 8)
        self.assertEqual(r["score"], 1.0)

    def test_broken_scores_partial(self):
        r = run(BROKEN)
        self.assertTrue(r["built"])
        self.assertEqual(r["total"], 8)
        self.assertEqual(r["passed"], 5)
        self.assertEqual(
            r["failures"],
            ["test_notes_requires_auth", "test_notes_search", "test_notes_tag"],
        )

    def test_empty_dir_is_not_gradeable(self):
        with tempfile.TemporaryDirectory() as d:
            r = run(d)
            self.assertFalse(r["built"])
            self.assertEqual(r["score"], 0.0)


if __name__ == "__main__":
    unittest.main()
