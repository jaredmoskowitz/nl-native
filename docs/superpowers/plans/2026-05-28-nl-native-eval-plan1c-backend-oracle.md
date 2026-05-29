# NL Native Eval — Plan 1c: Backend Held-Out Oracle + Correctness Scorer

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A discriminating **black-box HTTP** oracle for the Notes backend — boot a submitted server, hit its endpoints, assert contract compliance — proven to pass on a correct Python-stdlib reference server and fail on a deliberately-broken one. Plus a backend correctness scorer that boots a code dir's server and runs the oracle.

**Architecture:** Black-box: the oracle is implementation-agnostic — it only speaks HTTP to a running server at `NOTES_BASE_URL`. The eval's chosen stack is **Python 3 standard library** (`http.server`), so reference fixtures and submissions are a single runnable `server.py` with zero installs. The scorer boots `python3 <dir>/server.py <port>`, waits for readiness, runs the oracle suite against it, parses method-level pass counts, and reports `{built, passed, total, score}`. Boot/crash failure → `built=false`/0 (parity with iOS/Android non-gradeable semantics). Reuses the shared Plan 2 packager/aggregator/rubric for quality.

**Tech Stack:** Python 3 standard library only — `http.server`, `json`, `urllib`, `subprocess`, `socket`, `unittest`. No third-party packages, no Node, no DB.

---

## Background

Implements the Backend slice of §4.1 of the eval design spec and Plan 1c of the roadmap. Invariants:
- **Grader-only + out of reach:** oracle + fixtures under `eval/oracle/backend` / `eval/oracle-reference/backend`, never a workdir.
- **Black-box:** the oracle asserts only on HTTP responses against the contract (`eval/feature-spec/api-contracts/notes.md`). It does not read server source — so it scores any conformant implementation. A server that won't boot → `built=false`/0.
- **Method-level scoring:** count oracle test methods passed/failed via `unittest` result objects (not a printed summary).
- **Headroom + parity:** same Notes dataset as iOS/Android; 3 seeded backend defects (search ignored, auth not enforced, tag ignored) each break exactly one oracle test.

## File Structure

```
eval/
  feature-spec/testable-interface-backend.md      # the runnable-server contract
  oracle/backend/
    tests/test_notes_api.py                        # black-box HTTP oracle (hits NOTES_BASE_URL)
    slot/.gitkeep                                  # submission server.py drops here
  oracle-reference/backend/
    correct/server.py                              # correct → oracle passes 8/8
    broken/server.py                               # 3 defects → oracle fails exactly 3
  scripts/validate-backend-oracle.sh
  runner/
    score_correctness_backend.py
    tests/test_score_correctness_backend.py
```

---

## Task 1: Scaffold + pin the server contract

**Files:** `eval/oracle/backend/slot/.gitkeep`, `eval/feature-spec/testable-interface-backend.md`, `.gitignore` edit

- [ ] **Step 1: Create dirs**
```bash
mkdir -p eval/oracle/backend/tests eval/oracle/backend/slot \
         eval/oracle-reference/backend/correct eval/oracle-reference/backend/broken
touch eval/oracle/backend/slot/.gitkeep
```

- [ ] **Step 2: Write `eval/feature-spec/testable-interface-backend.md`**
```markdown
# Backend Testable Interface (binding contract for the oracle)

The backend MUST be a single runnable `server.py` (Python 3 standard library only) started as
`python3 server.py <port>`, serving on `127.0.0.1:<port>`, seeded with the fixed Notes dataset
below. The oracle is black-box (HTTP only).

## Dataset (fixed)
id=1 "Groceries" [home]; id=2 "Gym plan" [health]; id=3 "Grocery list 2" [home];
id=4 "Work tasks" [work]; id=5 "Reading" [home]. Valid credentials: a@b.com / pw → token "tok".

## Endpoints
- `POST /auth/login` body `{email, password}` → 200 `{"token": "tok"}` for valid creds; else 401 `{"message": "Invalid credentials"}`.
- `GET /notes?search=&tag=&page=&pageSize=` — requires header `Authorization: Bearer tok`; missing/invalid → 401 `{"message": "unauthenticated"}`.
  - `search`: case-insensitive substring on title. `tag`: exact match in tags.
  - `page` 1-based (default 1); `pageSize` default 20.
  - 200 response: `{"notes": [{"id","title","tags"}], "page": int, "totalPages": int, "totalCount": int}`
  - `totalPages = max(1, ceil(totalCount / pageSize))`.
```

- [ ] **Step 3: Append to `eval/.gitignore`**
```gitignore
oracle/backend/slot/*.py
```

- [ ] **Step 4: Commit**
```bash
git add eval/oracle/backend/slot/.gitkeep eval/feature-spec/testable-interface-backend.md eval/.gitignore
git commit -m "eval: scaffold backend oracle + pin server contract"
```

---

## Task 2: Correct reference server

**Files:** `eval/oracle-reference/backend/correct/server.py`

- [ ] **Step 1: Write `correct/server.py`**
```python
#!/usr/bin/env python3
"""Reference Notes backend — Python stdlib only. Run: python3 server.py <port>"""
import json
import math
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs

NOTES = [
    {"id": "1", "title": "Groceries", "tags": ["home"]},
    {"id": "2", "title": "Gym plan", "tags": ["health"]},
    {"id": "3", "title": "Grocery list 2", "tags": ["home"]},
    {"id": "4", "title": "Work tasks", "tags": ["work"]},
    {"id": "5", "title": "Reading", "tags": ["home"]},
]
VALID_EMAIL, VALID_PASSWORD, TOKEN = "a@b.com", "pw", "tok"


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass  # keep the oracle output quiet

    def _send(self, code, obj):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _authed(self):
        return self.headers.get("Authorization") == f"Bearer {TOKEN}"

    def do_POST(self):
        if urlparse(self.path).path != "/auth/login":
            return self._send(404, {"message": "not found"})
        length = int(self.headers.get("Content-Length", 0))
        data = json.loads(self.rfile.read(length) or b"{}")
        if data.get("email") == VALID_EMAIL and data.get("password") == VALID_PASSWORD:
            return self._send(200, {"token": TOKEN})
        return self._send(401, {"message": "Invalid credentials"})

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path != "/notes":
            return self._send(404, {"message": "not found"})
        if not self._authed():
            return self._send(401, {"message": "unauthenticated"})
        q = parse_qs(parsed.query)
        search = q.get("search", [None])[0]
        tag = q.get("tag", [None])[0]
        page = int(q.get("page", ["1"])[0])
        page_size = int(q.get("pageSize", ["20"])[0])

        items = NOTES
        if search:
            items = [n for n in items if search.lower() in n["title"].lower()]
        if tag:
            items = [n for n in items if tag in n["tags"]]

        total = len(items)
        total_pages = max(1, math.ceil(total / page_size))
        start = (page - 1) * page_size
        page_items = items[start:start + page_size]
        self._send(200, {"notes": page_items, "page": page,
                         "totalPages": total_pages, "totalCount": total})


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    HTTPServer(("127.0.0.1", port), Handler).serve_forever()


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Smoke-check it boots** (manual sanity, not committed)
```bash
python3 eval/oracle-reference/backend/correct/server.py 8137 &
sleep 1
curl -s -X POST localhost:8137/auth/login -d '{"email":"a@b.com","password":"pw"}'
echo
curl -s localhost:8137/notes?page=1\&pageSize=2 -H "Authorization: Bearer tok"
echo
kill %1
```
Expected: `{"token": "tok"}` then a page with notes 1 and 2, `totalPages` 3, `totalCount` 5.

- [ ] **Step 3: Commit**
```bash
git add eval/oracle-reference/backend/correct/server.py
git commit -m "eval: add correct backend reference server"
```

---

## Task 3: Black-box HTTP oracle

**Files:** `eval/oracle/backend/tests/test_notes_api.py`

- [ ] **Step 1: Write `test_notes_api.py`**
```python
"""Black-box HTTP oracle for the Notes backend. Hits the server at NOTES_BASE_URL
(set by the scorer / validate script after booting a submission). Asserts only on
HTTP responses — implementation-agnostic."""
import json
import os
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen

BASE = os.environ.get("NOTES_BASE_URL", "http://127.0.0.1:8000")


def _call(method, path, body=None, token=None):
    data = json.dumps(body).encode() if body is not None else None
    req = Request(BASE + path, data=data, method=method)
    if body is not None:
        req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urlopen(req, timeout=5) as resp:
            return resp.status, json.loads(resp.read() or b"{}")
    except HTTPError as e:
        return e.code, json.loads(e.read() or b"{}")


class NotesApiOracle(unittest.TestCase):
    def _token(self):
        _, body = _call("POST", "/auth/login", {"email": "a@b.com", "password": "pw"})
        return body["token"]

    def test_login_success(self):
        status, body = _call("POST", "/auth/login", {"email": "a@b.com", "password": "pw"})
        self.assertEqual(status, 200)
        self.assertIn("token", body)

    def test_login_failure(self):
        status, body = _call("POST", "/auth/login", {"email": "a@b.com", "password": "nope"})
        self.assertEqual(status, 401)
        self.assertEqual(body.get("message"), "Invalid credentials")

    def test_notes_requires_auth(self):
        status, _ = _call("GET", "/notes?page=1&pageSize=2")
        self.assertEqual(status, 401)

    def test_notes_first_page(self):
        token = self._token()
        status, body = _call("GET", "/notes?page=1&pageSize=2", token=token)
        self.assertEqual(status, 200)
        self.assertEqual([n["id"] for n in body["notes"]], ["1", "2"])
        self.assertEqual(body["page"], 1)
        self.assertEqual(body["totalPages"], 3)
        self.assertEqual(body["totalCount"], 5)

    def test_notes_second_page(self):
        token = self._token()
        _, body = _call("GET", "/notes?page=2&pageSize=2", token=token)
        self.assertEqual([n["id"] for n in body["notes"]], ["3", "4"])

    def test_notes_last_page(self):
        token = self._token()
        _, body = _call("GET", "/notes?page=3&pageSize=2", token=token)
        self.assertEqual([n["id"] for n in body["notes"]], ["5"])

    def test_notes_search(self):
        token = self._token()
        _, body = _call("GET", "/notes?search=Groc&page=1&pageSize=20", token=token)
        self.assertEqual([n["id"] for n in body["notes"]], ["1", "3"])
        self.assertEqual(body["totalCount"], 2)

    def test_notes_tag(self):
        token = self._token()
        _, body = _call("GET", "/notes?tag=home&page=1&pageSize=2", token=token)
        self.assertEqual([n["id"] for n in body["notes"]], ["1", "3"])
        self.assertEqual(body["totalCount"], 3)
        self.assertEqual(body["totalPages"], 2)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Commit**
```bash
git add eval/oracle/backend/tests/test_notes_api.py
git commit -m "eval: add black-box HTTP oracle for the Notes backend"
```

---

## Task 4: Backend correctness scorer → green on the correct server

**Files:** `eval/runner/score_correctness_backend.py`

- [ ] **Step 1: Write `score_correctness_backend.py`**
```python
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
```

- [ ] **Step 2: Run the scorer against the correct reference**
```bash
cd /Users/jaredmoskowitz/workspace/nl-native
python3 eval/runner/score_correctness_backend.py eval/oracle-reference/backend/correct
```
Expected JSON: `built: true`, `passed: 8`, `total: 8`, `score: 1.0`, `failures: []`.

- [ ] **Step 3: Commit**
```bash
git add eval/runner/score_correctness_backend.py
git commit -m "eval: add backend correctness scorer (boots server, runs black-box oracle)"
```

---

## Task 5: Broken server → oracle catches exactly 3 defects

Three defects, each breaking exactly one oracle test: (1) `search` ignored, (2) auth not enforced on `/notes`, (3) `tag` ignored.

**Files:** `eval/oracle-reference/backend/broken/server.py`

- [ ] **Step 1: Write `broken/server.py`** (identical to correct EXCEPT `do_GET`)

Copy `correct/server.py` verbatim, then replace its `do_GET` method with:
```python
    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path != "/notes":
            return self._send(404, {"message": "not found"})
        # DEFECT 2: auth not enforced — missing the _authed() check.
        q = parse_qs(parsed.query)
        page = int(q.get("page", ["1"])[0])
        page_size = int(q.get("pageSize", ["20"])[0])

        items = NOTES
        # DEFECT 1: `search` query parameter ignored (no title filtering).
        # DEFECT 3: `tag` query parameter ignored (no tag filtering).

        total = len(items)
        total_pages = max(1, math.ceil(total / page_size))
        start = (page - 1) * page_size
        page_items = items[start:start + page_size]
        self._send(200, {"notes": page_items, "page": page,
                         "totalPages": total_pages, "totalCount": total})
```
Everything else (imports, NOTES, `_send`, `_authed`, `do_POST`, `main`) is identical to correct.

- [ ] **Step 2: Run the scorer against the broken server**
```bash
cd /Users/jaredmoskowitz/workspace/nl-native
python3 eval/runner/score_correctness_backend.py eval/oracle-reference/backend/broken
```
Expected JSON: `built: true`, `total: 8`, `passed: 5`, `score: 0.625`, and `failures` exactly `["test_notes_requires_auth", "test_notes_search", "test_notes_tag"]` (sorted). If a different set fails, do NOT adjust the oracle — diagnose the defect/transcription and report.

- [ ] **Step 3: Commit**
```bash
git add eval/oracle-reference/backend/broken/server.py
git commit -m "eval: add broken backend server (oracle catches 3 defects)"
```

---

## Task 6: Validation script

**Files:** `eval/scripts/validate-backend-oracle.sh`

- [ ] **Step 1: Write `validate-backend-oracle.sh`**
```bash
#!/usr/bin/env bash
# Proves the backend oracle discriminates: the correct server scores 1.0, and the
# broken server fails EXACTLY the three seeded-defect tests.
set -euo pipefail

EVAL_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SCORER="$EVAL_ROOT/runner/score_correctness_backend.py"

correct="$(python3 "$SCORER" "$EVAL_ROOT/oracle-reference/backend/correct")"
echo "$correct"
echo "$correct" | python3 -c "import json,sys; r=json.load(sys.stdin); assert r['built'] and r['score']==1.0, 'correct must score 1.0'; print('>> correct => pass')"

broken="$(python3 "$SCORER" "$EVAL_ROOT/oracle-reference/backend/broken")"
echo "$broken"
echo "$broken" | python3 -c "
import json, sys
r = json.load(sys.stdin)
expected = ['test_notes_requires_auth', 'test_notes_search', 'test_notes_tag']
assert r['built'], 'broken should still boot'
assert r['failures'] == expected, f'expected {expected}, got {r[\"failures\"]}'
print('>> broken => fail (caught exactly: ' + ' '.join(expected) + ')')
"
echo "BACKEND ORACLE VALIDATION OK: passes on correct, fails on exactly the seeded defects."
```

- [ ] **Step 2: Make executable and run**
```bash
chmod +x eval/scripts/validate-backend-oracle.sh
eval/scripts/validate-backend-oracle.sh
```
Expected final line: `BACKEND ORACLE VALIDATION OK: passes on correct, fails on exactly the seeded defects.`

- [ ] **Step 3: Commit**
```bash
git add eval/scripts/validate-backend-oracle.sh
git commit -m "eval: add backend oracle validation script"
```

---

## Task 7: Scorer TDD test + docs

**Files:** `eval/runner/tests/test_score_correctness_backend.py`, `eval/README.md`, `eval/runner/README.md`

- [ ] **Step 1: Write the scorer test**
```python
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
```

- [ ] **Step 2: Run it**
```bash
cd /Users/jaredmoskowitz/workspace/nl-native
python3 -m unittest discover -s eval/runner/tests -p "test_score_correctness_backend.py" 2>&1 | tail -6
```
Expected: `Ran 3 tests ... OK`.

- [ ] **Step 3: Update `eval/README.md` status row** for the backend oracle to:
```markdown
| Backend oracle (black-box HTTP) + scorer | ✅ built & validated |
```

- [ ] **Step 4: Add to `eval/runner/README.md` Tools list:**
```markdown
- `score_correctness_backend.py <code-dir>` — boots `<code-dir>/server.py`, runs the black-box HTTP oracle, reports method-level pass rate (boot/crash → `built=false`/0).
```

- [ ] **Step 5: Commit**
```bash
git add eval/runner/tests/test_score_correctness_backend.py eval/README.md eval/runner/README.md
git commit -m "eval: add backend scorer test + docs/status"
```

---

## Done criteria

- [ ] `eval/scripts/validate-backend-oracle.sh` ends with `BACKEND ORACLE VALIDATION OK`.
- [ ] `python3 -m unittest discover -s eval/runner/tests -p "test_score_correctness_backend.py"` green (correct → 1.0, broken → 5/8 failing exactly the 3, empty → built=false/0).
- [ ] Oracle is black-box (no server source reads); reuses shared packager/aggregator for quality.
- [ ] All committed on branch `nl-native-backend-oracle`.

## Follow-on

All three oracles + scorers now exist. **Plan 3** — all-platform orchestrator: calibration N=1 dry-run → full N=5, prototyping + measuring the verify loop.
