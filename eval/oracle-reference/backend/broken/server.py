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


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    HTTPServer(("127.0.0.1", port), Handler).serve_forever()


if __name__ == "__main__":
    main()
