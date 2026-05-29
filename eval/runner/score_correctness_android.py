#!/usr/bin/env python3
"""Score Android correctness: run the Plan 1b held-out oracle against a directory of
generated `notes` Kotlin sources and report the method-level pass rate.

Build/compile failure => built=false, score 0.0. A build that runs zero test cases
(tests failed to compile against the submission) is also non-gradeable (built=false).
The oracle slot is always restored to only .gitkeep.
"""
import argparse
import glob
import json
import os
import shutil
import subprocess
import xml.etree.ElementTree as ET

PKG = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "oracle", "android"))
SLOT = os.path.join(PKG, "src", "main", "kotlin", "notes")
RESULTS = os.path.join(PKG, "build", "test-results", "test")


def restore_slot():
    os.makedirs(SLOT, exist_ok=True)
    for name in os.listdir(SLOT):
        if name.endswith(".kt"):
            os.remove(os.path.join(SLOT, name))
    open(os.path.join(SLOT, ".gitkeep"), "a").close()


def load_slot(src_dir):
    os.makedirs(SLOT, exist_ok=True)
    gitkeep = os.path.join(SLOT, ".gitkeep")
    if os.path.exists(gitkeep):
        os.remove(gitkeep)
    for name in os.listdir(src_dir):
        if name.endswith(".kt"):
            shutil.copy(os.path.join(src_dir, name), os.path.join(SLOT, name))


def count_results():
    passed = failed = 0
    for path in glob.glob(os.path.join(RESULTS, "*.xml")):
        for tc in ET.parse(path).getroot().iter("testcase"):
            kinds = [child.tag for child in tc]
            if any(k in ("failure", "error") for k in kinds):
                failed += 1
            elif "skipped" in kinds:
                continue  # skipped tests count as neither passed nor failed
            else:
                passed += 1
    return passed, failed


def score(src_dir):
    load_slot(src_dir)
    if os.path.isdir(RESULTS):
        shutil.rmtree(RESULTS)  # avoid stale results from a prior run
    try:
        result = subprocess.run(["gradle", "test", "--rerun-tasks"], cwd=PKG,
                                capture_output=True, text=True)
        passed, failed = count_results()
        total = passed + failed
        if total == 0:
            # Either the library failed to compile, or the tests failed to compile
            # against this submission. Non-gradeable.
            return {"platform": "android", "built": False, "passed": 0, "total": 0,
                    "score": 0.0, "summary": "no test cases ran (compile failure)"}
        value = passed / total
        return {"platform": "android", "built": True, "passed": passed, "total": total,
                "score": value, "summary": f"{passed}/{total} methods passed"}
    finally:
        restore_slot()


def main():
    parser = argparse.ArgumentParser(description="Score Android correctness via the held-out oracle.")
    parser.add_argument("src_dir", help="directory of generated `notes` *.kt files")
    args = parser.parse_args()
    print(json.dumps(score(args.src_dir), indent=2))


if __name__ == "__main__":
    main()
