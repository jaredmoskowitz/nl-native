import json
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
RUNNER = os.path.join(HERE, "..", "score_correctness_android.py")
REF = os.path.join(HERE, "..", "..", "oracle-reference", "android")
CORRECT = os.path.join(REF, "correct", "notes")
BROKEN = os.path.join(REF, "broken", "notes")


def run(src_dir):
    proc = subprocess.run([sys.executable, RUNNER, src_dir], capture_output=True, text=True)
    assert proc.returncode == 0, f"scorer crashed: {proc.stderr}"
    return json.loads(proc.stdout)


class TestScoreCorrectnessAndroid(unittest.TestCase):
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
        self.assertEqual(r["passed"], 6)
        self.assertAlmostEqual(r["score"], 6 / 9)

    def test_empty_dir_is_build_failure_zero(self):
        with tempfile.TemporaryDirectory() as d:
            r = run(d)
            self.assertFalse(r["built"])
            self.assertEqual(r["score"], 0.0)

    def test_library_compiles_but_tests_dont_is_zero(self):
        # A submission that renames a public symbol the held-out tests reference: it
        # compiles in isolation, but `gradle test` fails to compile the test target
        # against it -> zero test cases -> non-gradeable (built=False, score 0).
        import shutil
        with tempfile.TemporaryDirectory() as d:
            for name in os.listdir(CORRECT):
                if name.endswith(".kt"):
                    shutil.copy(os.path.join(CORRECT, name), os.path.join(d, name))
            vm = os.path.join(d, "NotesViewModel.kt")
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
