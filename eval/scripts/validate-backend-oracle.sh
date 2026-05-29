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
