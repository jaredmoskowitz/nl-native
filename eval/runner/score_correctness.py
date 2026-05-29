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
        if total == 0:
            # The library compiled (swift build passed) but zero test cases ran, which
            # means the held-out test target failed to compile against this submission
            # (e.g. a renamed or missing public symbol the oracle references). The oracle
            # could not measure it, so report it as non-gradeable (built=False, score 0) —
            # NOT an ambiguous clean "0 of 0". 'built' thus means "the oracle ran".
            return {"platform": "ios", "built": False, "passed": 0, "total": 0,
                    "score": 0.0, "summary": "tests failed to compile against submission"}
        value = passed / total
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
