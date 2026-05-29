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
