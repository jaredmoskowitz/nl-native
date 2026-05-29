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

    def test_library_compiles_but_tests_dont_is_zero(self):
        # A submission that compiles as a library but renames a public symbol the
        # held-out tests reference: `swift build` passes, `swift test` fails to compile,
        # so zero test cases run. Must be reported non-gradeable (built=False, score 0).
        import shutil
        with tempfile.TemporaryDirectory() as d:
            for name in os.listdir(CORRECT):
                if name.endswith(".swift"):
                    shutil.copy(os.path.join(CORRECT, name), os.path.join(d, name))
            vm = os.path.join(d, "NotesViewModel.swift")
            with open(vm) as fh:
                src = fh.read()
            with open(vm, "w") as fh:
                fh.write(src.replace("canLoadMore", "canLoadMoreX"))
            r = run(d)
            self.assertEqual(r["score"], 0.0)
            self.assertFalse(r["built"])
            self.assertEqual(r["total"], 0)


if __name__ == "__main__":
    unittest.main()
