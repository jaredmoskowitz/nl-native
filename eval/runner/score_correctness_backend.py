#!/usr/bin/env python3
"""Score backend correctness: boot a submitted server.py, run the Plan 1c black-box
oracle against it, and report the method-level pass rate.

Boot/crash failure (no server.py, import error, never binds) => built=false, score 0.0.
"""
import argparse
import contextlib
import json
import os
import socket
import subprocess
import time
import unittest
from urllib.error import URLError
from urllib.request import urlopen

HERE = os.path.dirname(os.path.abspath(__file__))
ORACLE_TESTS = os.path.normpath(os.path.join(HERE, "..", "oracle", "backend", "tests"))


def _free_port():
    with contextlib.closing(socket.socket()) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _wait_ready(port, proc, timeout=8.0):
    deadline = time.time() + timeout
    url = f"http://127.0.0.1:{port}/notes"
    while time.time() < deadline:
        if proc.poll() is not None:
            return False  # server process exited (crash / import error)
        try:
            urlopen(url, timeout=1)
            return True  # 2xx (unlikely without auth) still means it's up
        except URLError as e:
            # An HTTP error (e.g. 401) means the server is up and responding.
            if hasattr(e, "code"):
                return True
            time.sleep(0.15)  # connection refused — not ready yet
        except Exception:
            time.sleep(0.15)
    return False


def _run_oracle(base_url):
    prev = os.environ.get("NOTES_BASE_URL")
    os.environ["NOTES_BASE_URL"] = base_url
    try:
        suite = unittest.TestLoader().discover(ORACLE_TESTS, pattern="test_notes_api.py")
        with open(os.devnull, "w") as devnull:
            result = unittest.TextTestRunner(stream=devnull, verbosity=0).run(suite)
        failed_names = sorted(
            tc._testMethodName for tc, _ in (result.failures + result.errors)
        )
        passed = result.testsRun - len(result.failures) - len(result.errors)
        return passed, result.testsRun, failed_names
    finally:
        if prev is None:
            os.environ.pop("NOTES_BASE_URL", None)
        else:
            os.environ["NOTES_BASE_URL"] = prev


def score(src_dir):
    server = os.path.join(src_dir, "server.py")
    if not os.path.isfile(server):
        return {"platform": "backend", "built": False, "passed": 0, "total": 0,
                "score": 0.0, "failures": [], "summary": "no server.py"}
    for _attempt in range(3):
        port = _free_port()
        proc = subprocess.Popen(["python3", server, str(port)],
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try:
            if _wait_ready(port, proc):
                passed, total, failures = _run_oracle(f"http://127.0.0.1:{port}")
                value = (passed / total) if total else 0.0
                return {"platform": "backend", "built": True, "passed": passed,
                        "total": total, "score": value, "failures": failures,
                        "summary": f"{passed}/{total} oracle tests passed"}
        finally:
            proc.terminate()
            with contextlib.suppress(Exception):
                proc.wait(timeout=5)
        # boot did not become ready (genuine crash, or a transient port race) — retry
    return {"platform": "backend", "built": False, "passed": 0, "total": 0,
            "score": 0.0, "failures": [], "summary": "server failed to boot"}


def main():
    parser = argparse.ArgumentParser(description="Score backend correctness via the black-box oracle.")
    parser.add_argument("src_dir", help="directory containing server.py")
    args = parser.parse_args()
    print(json.dumps(score(args.src_dir), indent=2))


if __name__ == "__main__":
    main()
