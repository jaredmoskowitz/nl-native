#!/usr/bin/env bash
# Proves the iOS oracle discriminates: passes on the correct impl, and on the broken
# impl fails EXACTLY the seeded-defect tests. Distinguishes "caught the defect" from
# "did not compile" by building first.
set -euo pipefail

EVAL_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PKG="$EVAL_ROOT/oracle/ios"
SLOT="$PKG/Sources/NotesFeature"

# Always restore the empty slot, even on failure.
trap 'rm -rf "$SLOT"; mkdir -p "$SLOT"; touch "$SLOT/.gitkeep"' EXIT

load_variant() {
  local variant="$1"
  rm -rf "$SLOT"; mkdir -p "$SLOT"
  cp "$EVAL_ROOT/oracle-reference/ios/$variant/NotesFeature/"*.swift "$SLOT/"
}

echo "== correct: expect build OK + all tests pass =="
load_variant correct
( cd "$PKG" && swift build ) || { echo "VALIDATION FAILED: correct did not build"; exit 1; }
( cd "$PKG" && swift test )  || { echo "VALIDATION FAILED: correct did not pass all tests"; exit 1; }
echo ">> correct => pass"

echo "== broken: expect build OK + exactly the seeded defects caught =="
load_variant broken
( cd "$PKG" && swift build ) || { echo "VALIDATION FAILED: broken did not build (cannot distinguish defect from compile error)"; exit 1; }
output="$( cd "$PKG" && swift test 2>&1 || true )"

expected_failures=(
  "test_search_resetsToFirstPage"
  "test_loadNextPage_stopsAtLastPage"
  "test_filterByTag_resetsAndFilters"
)
failed_lines="$( echo "$output" | grep -E "Test Case .* failed" || true )"
for t in "${expected_failures[@]}"; do
  echo "$failed_lines" | grep -q "$t" || {
    echo "VALIDATION FAILED: expected broken to fail '$t' but it did not"
    echo "$output"
    exit 1
  }
done

fail_count="$( echo "$failed_lines" | grep -c . || true )"
if [ "$fail_count" -ne "${#expected_failures[@]}" ]; then
  echo "VALIDATION FAILED: expected ${#expected_failures[@]} failing test cases, got $fail_count"
  echo "$output"
  exit 1
fi
echo ">> broken => fail (caught exactly: ${expected_failures[*]})"

echo "ORACLE VALIDATION OK: passes on correct, fails on exactly the seeded defects."
