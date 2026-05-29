# NL Native Eval — Plan 1b: Android Held-Out Oracle + Correctness Scorer

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Mirror Plan 1 on Android — a discriminating JUnit oracle for the same Notes feature, running on the **JVM via Gradle with no emulator**, proven to pass on a correct Kotlin reference and fail on a deliberately-broken one — plus an Android correctness scorer (`gradle test` → method-level pass rate) reusing the shared Plan 2 packager/aggregator.

**Architecture:** A Gradle Kotlin-JVM project whose `src/main/kotlin/notes/` is an empty *slot* the implementation-under-test drops into; JUnit 5 oracle tests in `src/test/kotlin/notes/` bind only to the public interface pinned in the spec. Logic-layer only (no Android framework imports), so it runs as plain JVM unit tests. Two validation fixtures (correct, broken) prove discrimination. A Python scorer parses Gradle's JUnit XML for method-level counts.

**Tech Stack:** Kotlin (JVM) via the Kotlin Gradle plugin (compiler pulled by Gradle — no standalone `kotlinc` needed), Gradle 9.4.x, JDK 17, JUnit 5 (Jupiter), `kotlinx-coroutines-test` (`runTest`). Python 3 stdlib for the scorer. Reuses `eval/runner/blind_package.py` + `aggregate_scores.py` + `quality_rubric.json` from Plan 2 (platform-agnostic).

---

## Background (read before starting)

Implements the Android slice of §4.1 of `docs/superpowers/specs/2026-05-28-nl-native-eval-design.md` and Plan 1b of the roadmap. Invariants (identical philosophy to Plan 1):

- **Grader-only + mechanically out of reach.** Oracle + fixtures live under `eval/oracle/android` and `eval/oracle-reference/android`, never under a workdir.
- **Binds to the spec-pinned public interface** (Kotlin package `notes`, exact type/function names). Non-conforming code fails to compile → correctness 0 (legitimate). No reflection hacks; the test imports the public API directly.
- **Method-level correctness.** Parse Gradle's JUnit XML (`build/test-results/test/*.xml`) for `testcase`/`failure` counts — never a summary line. Compile failure → 0; **a build that compiles but runs zero tests → non-gradeable 0** (same `built=false` semantics the iOS scorer settled).
- **Headroom.** Same defect-prone logic as iOS (pagination boundary, search-resets-page, filter-resets-page, load-more no-op).
- **Mirror, don't reinvent.** The interface, fixture data, and the 9 test behaviours match Plan 1's iOS oracle exactly so the two platforms measure the same thing.

## File Structure

```
eval/
  feature-spec/
    testable-interface-android.md          # pins the Kotlin public surface
  oracle/
    android/
      settings.gradle.kts
      build.gradle.kts
      gradle.properties
      src/main/kotlin/notes/.gitkeep        # SLOT: implementation-under-test drops here
      src/test/kotlin/notes/
        StubNotesApi.kt
        NotesViewModelOracleTest.kt
  oracle-reference/
    android/
      correct/notes/   Models.kt  NotesApi.kt  NotesViewModel.kt
      broken/notes/    Models.kt  NotesApi.kt  NotesViewModel.kt
  scripts/
    validate-android-oracle.sh
  runner/
    score_correctness_android.py
    tests/test_score_correctness_android.py
```

---

## Task 1: Stand up a working Gradle Kotlin-JVM + JUnit5 build (resolve versions empirically)

**This task's deliverable is a green `gradle test` with one trivial test — NOT oracle code.** Gradle 9.4 is new; the Kotlin-plugin / coroutines / JUnit versions must be mutually compatible. Resolve them here so everything after rides on a known-good build.

**Files:**
- Create: `eval/oracle/android/settings.gradle.kts`, `build.gradle.kts`, `gradle.properties`
- Create: `eval/oracle/android/src/main/kotlin/notes/.gitkeep`
- Create (temporary): a trivial test to prove the toolchain runs
- Modify: `eval/.gitignore`

- [ ] **Step 1: Create dirs**

```bash
mkdir -p eval/oracle/android/src/main/kotlin/notes \
         eval/oracle/android/src/test/kotlin/notes \
         eval/oracle-reference/android/correct/notes \
         eval/oracle-reference/android/broken/notes
touch eval/oracle/android/src/main/kotlin/notes/.gitkeep
```

- [ ] **Step 2: Write the Gradle files**

`eval/oracle/android/settings.gradle.kts`:
```kotlin
rootProject.name = "notes-oracle-android"
```

`eval/oracle/android/gradle.properties`:
```properties
org.gradle.jvmargs=-Xmx2g
kotlin.code.style=official
```

`eval/oracle/android/build.gradle.kts` (starting versions — **adjust in Step 3 if Gradle rejects them**):
```kotlin
plugins {
    kotlin("jvm") version "2.1.0"
}

repositories { mavenCentral() }

dependencies {
    testImplementation(platform("org.junit:junit-bom:5.11.3"))
    testImplementation("org.junit.jupiter:junit-jupiter")
    testImplementation("org.jetbrains.kotlinx:kotlinx-coroutines-test:1.9.0")
}

kotlin { jvmToolchain(17) }

tasks.test { useJUnitPlatform() }
```

- [ ] **Step 3: Prove the toolchain runs (resolve versions if needed)**

Write a throwaway test `eval/oracle/android/src/test/kotlin/notes/SmokeTest.kt`:
```kotlin
package notes

import kotlinx.coroutines.test.runTest
import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Test

class SmokeTest {
    @Test fun arithmetic_runs_on_jvm() = runTest { assertEquals(2, 1 + 1) }
}
```

Run:
```bash
cd /Users/jaredmoskowitz/workspace/nl-native/eval/oracle/android && gradle test
```
Expected: `BUILD SUCCESSFUL`, 1 test passed.

**If the build fails on plugin/version incompatibility** (e.g. "this version of the Kotlin Gradle plugin does not support Gradle 9.4"): per the project rules, after two failed attempts WebSearch for the Kotlin Gradle plugin version compatible with Gradle 9.4.x + JDK 17 (and the matching `kotlinx-coroutines-test` version), update `build.gradle.kts`, and retry. Record the working versions in a comment at the top of `build.gradle.kts`.

- [ ] **Step 4: Remove the smoke test and add `.gitignore` entries**

```bash
rm eval/oracle/android/src/test/kotlin/notes/SmokeTest.kt
```
Append to `eval/.gitignore`:
```gitignore
oracle/android/.gradle/
oracle/android/build/
oracle/android/src/main/kotlin/notes/*.kt
```

- [ ] **Step 5: Commit**

```bash
git add eval/oracle/android/settings.gradle.kts eval/oracle/android/build.gradle.kts \
        eval/oracle/android/gradle.properties \
        eval/oracle/android/src/main/kotlin/notes/.gitkeep eval/.gitignore
git commit -m "eval: scaffold Android Gradle Kotlin-JVM + JUnit5 build (versions resolved)"
```

---

## Task 2: Pin the Android testable interface

**Files:**
- Create: `eval/feature-spec/testable-interface-android.md`

- [ ] **Step 1: Write `eval/feature-spec/testable-interface-android.md`**

```markdown
# Android Testable Interface (binding contract for the oracle)

The Android logic layer MUST be a pure-Kotlin package `notes` with NO Android framework
imports (no `android.*`, no `androidx.*`), so it builds and tests via `gradle test` on the
JVM with no emulator. It MUST expose exactly:

## Value types (package `notes`)
- `data class Note(val id: String, val title: String, val tags: List<String>)`
- `data class Session(val token: String)`
- `data class NotesQuery(val search: String? = null, val tag: String? = null, val page: Int = 1, val pageSize: Int = 20)`
- `data class NotesPage(val notes: List<Note>, val page: Int, val totalPages: Int, val totalCount: Int)`
- `sealed class NotesError : Exception()` with `object Unauthenticated : NotesError()` and `data class Server(val msg: String) : NotesError()`

## Interface
```kotlin
interface NotesApi {
    suspend fun login(email: String, password: String): Session
    suspend fun listNotes(query: NotesQuery): NotesPage
}
```

## View model (`class NotesViewModel`)
- constructor `(api: NotesApi, pageSize: Int = 20)`
- read-only state (public getter, private setter): `notes: List<Note>`, `isLoading: Boolean`,
  `error: String?`, `page: Int`, `totalPages: Int`, `session: Session?`
- `val canLoadMore: Boolean` (== `page < totalPages`)
- `suspend` functions: `login(email, password)`, `search(text: String)`, `filterByTag(tag: String?)`,
  `refresh()`, `loadNextPage()`
- error messages: `Unauthenticated` → "Not signed in."; `Server(m)` → m; else → "Something went wrong."

Behaviour mirrors the iOS interface exactly (search & filter reset to page 1; loadNextPage is a
no-op when `canLoadMore` is false; failed first page leaves the list empty).
```

- [ ] **Step 2: Commit**

```bash
git add eval/feature-spec/testable-interface-android.md
git commit -m "eval: pin Android (Kotlin) testable interface"
```

---

## Task 3: Write the Android oracle (tests first — must fail to compile against the empty slot)

**Files:**
- Create: `eval/oracle/android/src/test/kotlin/notes/StubNotesApi.kt`
- Create: `eval/oracle/android/src/test/kotlin/notes/NotesViewModelOracleTest.kt`

- [ ] **Step 1: Write `StubNotesApi.kt`**

```kotlin
package notes

import kotlin.math.ceil

/** In-memory NotesApi for the oracle: deterministic search/tag/pagination so the
 *  view-model behaviour is the only thing under test. */
class StubNotesApi(
    private val all: List<Note>,
    private val validCredentials: Pair<String, String>? = "a@b.com" to "pw",
    private val failListWith: NotesError? = null,
) : NotesApi {
    var listCallCount = 0
        private set

    override suspend fun login(email: String, password: String): Session {
        val creds = validCredentials
        if (creds != null && creds.first == email && creds.second == password) {
            return Session("tok")
        }
        throw NotesError.Server("Invalid credentials")
    }

    override suspend fun listNotes(query: NotesQuery): NotesPage {
        listCallCount++
        failListWith?.let { throw it }

        var filtered = all
        query.search?.takeIf { it.isNotEmpty() }?.let { s ->
            filtered = filtered.filter { it.title.contains(s, ignoreCase = true) }
        }
        query.tag?.let { t -> filtered = filtered.filter { it.tags.contains(t) } }

        val total = filtered.size
        val size = maxOf(1, query.pageSize)
        val totalPages = maxOf(1, ceil(total.toDouble() / size).toInt())
        val start = (query.page - 1) * size
        val slice = filtered.drop(maxOf(0, start)).take(size)
        return NotesPage(slice, query.page, totalPages, total)
    }
}
```

- [ ] **Step 2: Write `NotesViewModelOracleTest.kt`** (9 tests, mirroring the iOS oracle)

```kotlin
package notes

import kotlinx.coroutines.test.runTest
import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Assertions.assertFalse
import org.junit.jupiter.api.Assertions.assertNotNull
import org.junit.jupiter.api.Assertions.assertNull
import org.junit.jupiter.api.Assertions.assertTrue
import org.junit.jupiter.api.Test

class NotesViewModelOracleTest {

    private fun fixture() = listOf(
        Note("1", "Groceries", listOf("home")),
        Note("2", "Gym plan", listOf("health")),
        Note("3", "Grocery list 2", listOf("home")),
        Note("4", "Work tasks", listOf("work")),
        Note("5", "Reading", listOf("home")),
    )

    private fun vm(api: StubNotesApi) = NotesViewModel(api, pageSize = 2)

    private suspend fun signedIn(api: StubNotesApi): NotesViewModel {
        val v = vm(api)
        v.login("a@b.com", "pw")
        return v
    }

    @Test fun login_success_setsSession() = runTest {
        val v = vm(StubNotesApi(fixture()))
        v.login("a@b.com", "pw")
        assertNotNull(v.session)
        assertNull(v.error)
        assertFalse(v.isLoading)
    }

    @Test fun login_failure_setsErrorNoSession() = runTest {
        val v = vm(StubNotesApi(fixture()))
        v.login("a@b.com", "wrong")
        assertNull(v.session)
        assertNotNull(v.error)
    }

    @Test fun loadBeforeLogin_setsErrorAndEmptyList() = runTest {
        val v = vm(StubNotesApi(fixture()))
        v.refresh()
        assertNotNull(v.error)
        assertTrue(v.notes.isEmpty())
        assertFalse(v.isLoading)
    }

    @Test fun refresh_loadsFirstPage() = runTest {
        val v = signedIn(StubNotesApi(fixture()))
        v.refresh()
        assertEquals(listOf("1", "2"), v.notes.map { it.id })
        assertEquals(1, v.page)
        assertTrue(v.canLoadMore)
    }

    @Test fun loadNextPage_appendsAndAdvances() = runTest {
        val v = signedIn(StubNotesApi(fixture()))
        v.refresh()
        v.loadNextPage()
        assertEquals(listOf("1", "2", "3", "4"), v.notes.map { it.id })
        assertEquals(2, v.page)
    }

    @Test fun loadNextPage_stopsAtLastPage() = runTest {
        val api = StubNotesApi(fixture())
        val v = signedIn(api)
        v.refresh()
        v.loadNextPage()
        v.loadNextPage()
        assertEquals(5, v.notes.size)
        assertFalse(v.canLoadMore)
        val callsBefore = api.listCallCount
        v.loadNextPage()
        assertEquals(callsBefore, api.listCallCount, "loadNextPage past the last page must not call the API")
        assertEquals(5, v.notes.size)
    }

    @Test fun search_resetsToFirstPage() = runTest {
        val v = signedIn(StubNotesApi(fixture()))
        v.refresh()
        v.loadNextPage()
        v.search("Groc")
        assertEquals(1, v.page)
        assertEquals(listOf("1", "3"), v.notes.map { it.id })
        assertFalse(v.canLoadMore)
    }

    @Test fun filterByTag_resetsAndFilters() = runTest {
        val v = signedIn(StubNotesApi(fixture()))
        v.refresh()
        v.loadNextPage()
        v.filterByTag("home")
        assertEquals(1, v.page)
        assertEquals(listOf("1", "3"), v.notes.map { it.id })
        assertTrue(v.canLoadMore)
    }

    @Test fun listError_setsErrorAndClearsLoading() = runTest {
        val api = StubNotesApi(fixture(), failListWith = NotesError.Server("boom"))
        val v = signedIn(api)
        v.refresh()
        assertEquals("boom", v.error)
        assertFalse(v.isLoading)
        assertTrue(v.notes.isEmpty())
    }
}
```

- [ ] **Step 3: Run to confirm it fails to build (empty slot)**

```bash
cd /Users/jaredmoskowitz/workspace/nl-native/eval/oracle/android && gradle test 2>&1 | tail -15
```
Expected: BUILD FAILED — unresolved references (`NotesViewModel`, `Note`, `NotesApi`, …) because the slot is empty. Correct by design.

- [ ] **Step 4: Commit**

```bash
git add eval/oracle/android/src/test
git commit -m "eval: add Android held-out oracle (StubNotesApi + NotesViewModel tests)"
```

---

## Task 4: Correct reference implementation → oracle green

**Files:**
- Create: `eval/oracle-reference/android/correct/notes/Models.kt`, `NotesApi.kt`, `NotesViewModel.kt`

- [ ] **Step 1: Write `correct/notes/Models.kt`**

```kotlin
package notes

data class Note(val id: String, val title: String, val tags: List<String>)

data class Session(val token: String)

data class NotesQuery(
    val search: String? = null,
    val tag: String? = null,
    val page: Int = 1,
    val pageSize: Int = 20,
)

data class NotesPage(
    val notes: List<Note>,
    val page: Int,
    val totalPages: Int,
    val totalCount: Int,
)

sealed class NotesError : Exception() {
    object Unauthenticated : NotesError()
    data class Server(val msg: String) : NotesError()
}
```

- [ ] **Step 2: Write `correct/notes/NotesApi.kt`**

```kotlin
package notes

interface NotesApi {
    suspend fun login(email: String, password: String): Session
    suspend fun listNotes(query: NotesQuery): NotesPage
}
```

- [ ] **Step 3: Write `correct/notes/NotesViewModel.kt`**

```kotlin
package notes

class NotesViewModel(
    private val api: NotesApi,
    private val pageSize: Int = 20,
) {
    var notes: List<Note> = emptyList()
        private set
    var isLoading: Boolean = false
        private set
    var error: String? = null
        private set
    var page: Int = 1
        private set
    var totalPages: Int = 1
        private set
    var session: Session? = null
        private set

    private var searchText: String? = null
    private var tagFilter: String? = null

    val canLoadMore: Boolean get() = page < totalPages

    suspend fun login(email: String, password: String) {
        isLoading = true
        error = null
        try {
            session = api.login(email, password)
        } catch (e: Throwable) {
            session = null
            error = message(e)
        } finally {
            isLoading = false
        }
    }

    suspend fun search(text: String) {
        searchText = text.ifEmpty { null }
        loadFirstPage()
    }

    suspend fun filterByTag(tag: String?) {
        tagFilter = tag
        loadFirstPage()
    }

    suspend fun refresh() {
        loadFirstPage()
    }

    suspend fun loadNextPage() {
        if (!canLoadMore) return
        load(page + 1, append = true)
    }

    private suspend fun loadFirstPage() {
        load(1, append = false)
    }

    private suspend fun load(targetPage: Int, append: Boolean) {
        if (session == null) {
            error = message(NotesError.Unauthenticated)
            return
        }
        isLoading = true
        error = null
        try {
            val result = api.listNotes(NotesQuery(searchText, tagFilter, targetPage, pageSize))
            page = result.page
            totalPages = result.totalPages
            notes = if (append) notes + result.notes else result.notes
        } catch (e: Throwable) {
            error = message(e)
        } finally {
            isLoading = false
        }
    }

    private fun message(e: Throwable): String = when (e) {
        is NotesError.Unauthenticated -> "Not signed in."
        is NotesError.Server -> e.msg
        else -> "Something went wrong."
    }
}
```

- [ ] **Step 4: Run the oracle against the correct implementation**

```bash
cd /Users/jaredmoskowitz/workspace/nl-native/eval/oracle/android
rm -f src/main/kotlin/notes/.gitkeep
cp ../../../oracle-reference/android/correct/notes/*.kt src/main/kotlin/notes/
gradle test 2>&1 | tail -6
```
Expected: `BUILD SUCCESSFUL`, 9 tests, 0 failures.

- [ ] **Step 5: Clean the slot and commit the reference**

```bash
cd /Users/jaredmoskowitz/workspace/nl-native/eval/oracle/android
rm -f src/main/kotlin/notes/*.kt
touch src/main/kotlin/notes/.gitkeep
cd /Users/jaredmoskowitz/workspace/nl-native
git add eval/oracle-reference/android/correct
git commit -m "eval: add correct Android reference impl (oracle passes)"
```

---

## Task 5: Broken implementation → oracle catches exactly 3 defects

Same three seeded defects as the iOS broken fixture: `search` and `filterByTag` do not reset to page 1, and `loadNextPage` has no `canLoadMore` guard. Must fail exactly `search_resetsToFirstPage`, `filterByTag_resetsAndFilters`, `loadNextPage_stopsAtLastPage`; the other 6 pass.

**Files:**
- Create: `eval/oracle-reference/android/broken/notes/Models.kt` (identical to correct)
- Create: `eval/oracle-reference/android/broken/notes/NotesApi.kt` (identical to correct)
- Create: `eval/oracle-reference/android/broken/notes/NotesViewModel.kt` (defective)

- [ ] **Step 1: Copy the unchanged files**

```bash
cp eval/oracle-reference/android/correct/notes/Models.kt  eval/oracle-reference/android/broken/notes/Models.kt
cp eval/oracle-reference/android/correct/notes/NotesApi.kt eval/oracle-reference/android/broken/notes/NotesApi.kt
```

- [ ] **Step 2: Write the defective `broken/notes/NotesViewModel.kt`**

Identical to the correct version EXCEPT the three marked functions:

```kotlin
package notes

class NotesViewModel(
    private val api: NotesApi,
    private val pageSize: Int = 20,
) {
    var notes: List<Note> = emptyList()
        private set
    var isLoading: Boolean = false
        private set
    var error: String? = null
        private set
    var page: Int = 1
        private set
    var totalPages: Int = 1
        private set
    var session: Session? = null
        private set

    private var searchText: String? = null
    private var tagFilter: String? = null

    val canLoadMore: Boolean get() = page < totalPages

    suspend fun login(email: String, password: String) {
        isLoading = true
        error = null
        try {
            session = api.login(email, password)
        } catch (e: Throwable) {
            session = null
            error = message(e)
        } finally {
            isLoading = false
        }
    }

    // DEFECT 1: does not reset to page 1 — reloads the current page.
    suspend fun search(text: String) {
        searchText = text.ifEmpty { null }
        load(page, append = false)
    }

    // DEFECT 3: does not reset to page 1 — reloads the current page.
    suspend fun filterByTag(tag: String?) {
        tagFilter = tag
        load(page, append = false)
    }

    suspend fun refresh() {
        load(1, append = false)
    }

    // DEFECT 2: no canLoadMore guard — always requests the next page.
    suspend fun loadNextPage() {
        load(page + 1, append = true)
    }

    private suspend fun load(targetPage: Int, append: Boolean) {
        if (session == null) {
            error = message(NotesError.Unauthenticated)
            return
        }
        isLoading = true
        error = null
        try {
            val result = api.listNotes(NotesQuery(searchText, tagFilter, targetPage, pageSize))
            page = result.page
            totalPages = result.totalPages
            notes = if (append) notes + result.notes else result.notes
        } catch (e: Throwable) {
            error = message(e)
        } finally {
            isLoading = false
        }
    }

    private fun message(e: Throwable): String = when (e) {
        is NotesError.Unauthenticated -> "Not signed in."
        is NotesError.Server -> e.msg
        else -> "Something went wrong."
    }
}
```

- [ ] **Step 3: Run the oracle against the broken implementation**

```bash
cd /Users/jaredmoskowitz/workspace/nl-native/eval/oracle/android
rm -f src/main/kotlin/notes/.gitkeep src/main/kotlin/notes/*.kt
cp ../../../oracle-reference/android/broken/notes/*.kt src/main/kotlin/notes/
gradle test 2>&1 | tail -20 || true
```
Expected: BUILD FAILED (test failures), with exactly these failing: `search_resetsToFirstPage`, `filterByTag_resetsAndFilters`, `loadNextPage_stopsAtLastPage`. The other 6 pass. (Inspect `build/test-results/test/*.xml` if needed to confirm the exact set.)

- [ ] **Step 4: Clean the slot and commit the broken fixture**

```bash
cd /Users/jaredmoskowitz/workspace/nl-native/eval/oracle/android
rm -f src/main/kotlin/notes/*.kt
touch src/main/kotlin/notes/.gitkeep
cd /Users/jaredmoskowitz/workspace/nl-native
git add eval/oracle-reference/android/broken
git commit -m "eval: add broken Android fixture (oracle catches 3 defects)"
```

---

## Task 6: Automate Android oracle validation

**Files:**
- Create: `eval/scripts/validate-android-oracle.sh`

- [ ] **Step 1: Write `validate-android-oracle.sh`**

```bash
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
```

- [ ] **Step 2: Make executable and run**

```bash
chmod +x eval/scripts/validate-android-oracle.sh
eval/scripts/validate-android-oracle.sh
```
Expected final line: `ANDROID ORACLE VALIDATION OK: passes on correct, fails on exactly the seeded defects.`

- [ ] **Step 3: Commit**

```bash
git add eval/scripts/validate-android-oracle.sh
git commit -m "eval: add Android oracle validation script"
```

---

## Task 7: Android correctness scorer (TDD)

**Files:**
- Test: `eval/runner/tests/test_score_correctness_android.py`
- Create: `eval/runner/score_correctness_android.py`

- [ ] **Step 1: Write the failing test**

`eval/runner/tests/test_score_correctness_android.py`:
```python
import json
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
RUNNER = os.path.join(HERE, "..", "score_correctness_android.py")
REF = os.path.join(HERE, "..", "..", "oracle-reference", "android")
CORRECT = os.path.join(REF, "correct", "notes")
BROKEN = os.path.join(REF, "broken", "notes")


def run(src_dir):
    proc = subprocess.run([sys.executable, RUNNER, src_dir], capture_output=True, text=True)
    assert proc.returncode == 0, f"scorer crashed: {proc.stderr}"
    return json.loads(proc.stdout)


class TestScoreCorrectnessAndroid(unittest.TestCase):
    def test_correct_scores_full(self):
        r = run(CORRECT)
        self.assertTrue(r["built"])
        self.assertEqual(r["passed"], 9)
        self.assertEqual(r["total"], 9)
        self.assertEqual(r["score"], 1.0)

    def test_broken_scores_partial(self):
        r = run(BROKEN)
        self.assertTrue(r["built"])
        self.assertEqual(r["total"], 9)
        self.assertEqual(r["passed"], 6)
        self.assertAlmostEqual(r["score"], 6 / 9)

    def test_empty_dir_is_build_failure_zero(self):
        with tempfile.TemporaryDirectory() as d:
            r = run(d)
            self.assertFalse(r["built"])
            self.assertEqual(r["score"], 0.0)

    def test_library_compiles_but_tests_dont_is_zero(self):
        # A submission that renames a public symbol the held-out tests reference: it
        # compiles in isolation, but `gradle test` fails to compile the test target
        # against it -> zero test cases -> non-gradeable (built=False, score 0).
        import shutil
        with tempfile.TemporaryDirectory() as d:
            for name in os.listdir(CORRECT):
                if name.endswith(".kt"):
                    shutil.copy(os.path.join(CORRECT, name), os.path.join(d, name))
            vm = os.path.join(d, "NotesViewModel.kt")
            with open(vm) as fh:
                src = fh.read()
            with open(vm, "w") as fh:
                fh.write(src.replace("canLoadMore", "canLoadMoreX"))
            r = run(d)
            self.assertEqual(r["score"], 0.0)
            self.assertFalse(r["built"])
            self.assertEqual(r["total"], 0)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run to verify it fails**

```bash
cd /Users/jaredmoskowitz/workspace/nl-native
python3 -m unittest discover -s eval/runner/tests -p "test_score_correctness_android.py" 2>&1 | tail -5
```
Expected: FAIL — `score_correctness_android.py` does not exist.

- [ ] **Step 3: Write `eval/runner/score_correctness_android.py`**

```python
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
```

- [ ] **Step 4: Run to verify it passes**

```bash
cd /Users/jaredmoskowitz/workspace/nl-native
python3 -m unittest discover -s eval/runner/tests -p "test_score_correctness_android.py" 2>&1 | tail -8
git status --short eval/oracle/android/src/main/kotlin/notes
```
Expected: `Ran 4 tests ... OK` (gradle runs make this slow, ~30–60s). Slot shows no tracked change.

- [ ] **Step 5: Commit**

```bash
git add eval/runner/score_correctness_android.py eval/runner/tests/test_score_correctness_android.py
git commit -m "eval: add Android correctness scorer (gradle JUnit XML pass rate)"
```

---

## Task 8: Document + update status

**Files:**
- Modify: `eval/README.md` (Status table)
- Modify: `eval/runner/README.md` (add the Android scorer)

- [ ] **Step 1: Update `eval/README.md` Status table**

Change the row `| Android oracle (JUnit / JVM) | ⬜ planned |` to:
```markdown
| Android oracle (JUnit/JVM) + scorer | ✅ built & validated |
```

- [ ] **Step 2: Add a line to `eval/runner/README.md`** under the Tools list:

```markdown
- `score_correctness_android.py <code-dir>` — drops Kotlin `notes` sources into the Android oracle slot, runs `gradle test`, parses the JUnit XML for method-level pass rate (same `built=false` non-gradeable semantics as the iOS scorer).
```

- [ ] **Step 3: Commit**

```bash
git add eval/README.md eval/runner/README.md
git commit -m "eval: document Android oracle + scorer; update status"
```

---

## Done criteria

- [ ] `eval/scripts/validate-android-oracle.sh` ends with `ANDROID ORACLE VALIDATION OK`.
- [ ] `python3 -m unittest discover -s eval/runner/tests -p "test_score_correctness_android.py"` is green (correct → 1.0, broken → 6/9, empty → 0.0, renamed-symbol → non-gradeable 0).
- [ ] Oracle binds only to the public `notes` interface; slot restored to only `.gitkeep`.
- [ ] Working Gradle/Kotlin/JUnit versions recorded in `build.gradle.kts`.
- [ ] All committed on branch `nl-native-android-oracle`.

## Follow-on

- **Plan 1c** — Backend oracle + scorer (black-box HTTP; pick a concrete stack).
- **Plan 3** — all-platform orchestrator (calibration N=1 dry-run → full N=5).
