#!/usr/bin/env bash
# Proves the Android oracle discriminates: passes on the correct impl, and on the
# broken impl fails exactly the seeded-defect tests. Builds first to distinguish
# "caught the defect" from "did not compile".
set -euo pipefail

EVAL_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PKG="$EVAL_ROOT/oracle/android"
SLOT="$PKG/src/main/kotlin/notes"

trap 'rm -rf "$SLOT"; mkdir -p "$SLOT"; touch "$SLOT/.gitkeep"' EXIT

load_variant() {
  local variant="$1"
  rm -rf "$SLOT"; mkdir -p "$SLOT"
  cp "$EVAL_ROOT/oracle-reference/android/$variant/notes/"*.kt "$SLOT/"
}

echo "== correct: expect all tests pass =="
load_variant correct
( cd "$PKG" && gradle test --rerun-tasks ) || { echo "VALIDATION FAILED: correct did not pass"; exit 1; }
echo ">> correct => pass"

echo "== broken: expect exactly the seeded defects caught =="
load_variant broken
( cd "$PKG" && gradle test --rerun-tasks ) && { echo "VALIDATION FAILED: broken unexpectedly passed"; exit 1; }

expected=(
  "search_resetsToFirstPage"
  "filterByTag_resetsAndFilters"
  "loadNextPage_stopsAtLastPage"
)
xml_dir="$PKG/build/test-results/test"
# Collect failing testcase names from the JUnit XML.
failures="$(python3 - "$xml_dir" <<'PY'
import glob, os, sys, xml.etree.ElementTree as ET
names = []
for f in glob.glob(os.path.join(sys.argv[1], "*.xml")):
    for tc in ET.parse(f).getroot().iter("testcase"):
        if any(c.tag in ("failure", "error") for c in tc):
            names.append(tc.get("name"))
print("\n".join(sorted(set(names))))
PY
)"
for t in "${expected[@]}"; do
  echo "$failures" | grep -q "$t" || { echo "VALIDATION FAILED: expected broken to fail '$t'"; echo "$failures"; exit 1; }
done
count="$(echo "$failures" | grep -c . || true)"
[ "$count" -eq "${#expected[@]}" ] || { echo "VALIDATION FAILED: expected ${#expected[@]} failing tests, got $count: $failures"; exit 1; }
echo ">> broken => fail (caught exactly: ${expected[*]})"

echo "ANDROID ORACLE VALIDATION OK: passes on correct, fails on exactly the seeded defects."
