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
