#!/usr/bin/env bash
# Proves the iOS oracle discriminates: passes on the correct impl, fails on the broken one.
set -euo pipefail

EVAL_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PKG="$EVAL_ROOT/oracle/ios"
SLOT="$PKG/Sources/NotesFeature"

run_variant() {
  local variant="$1" expect="$2"
  rm -rf "$SLOT"; mkdir -p "$SLOT"
  cp "$EVAL_ROOT/oracle-reference/ios/$variant/NotesFeature/"*.swift "$SLOT/"
  echo "== swift test against '$variant' (expect: $expect) =="
  if ( cd "$PKG" && swift test ); then result="pass"; else result="fail"; fi
  echo ">> '$variant' => $result"
  if [ "$result" != "$expect" ]; then
    echo "VALIDATION FAILED: '$variant' expected '$expect' but got '$result'"
    exit 1
  fi
}

run_variant correct pass
run_variant broken  fail

# Restore the empty slot.
rm -rf "$SLOT"; mkdir -p "$SLOT"; touch "$SLOT/.gitkeep"
echo "ORACLE VALIDATION OK: passes on correct, fails on broken."
