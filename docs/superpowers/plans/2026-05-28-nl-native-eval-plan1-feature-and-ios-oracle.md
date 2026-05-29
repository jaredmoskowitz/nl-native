# NL Native Eval — Plan 1: Toy Feature + iOS Held-Out Oracle

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Author the toy feature's NL Native specs and a discriminating iOS held-out test oracle (logic layer, runs via `swift test` with no simulator), proven to pass on a correct reference implementation and fail on a deliberately-broken one.

**Architecture:** A Swift Package whose `Sources/NotesFeature/` is an empty *slot* the implementation-under-test drops into; the oracle tests live in the package's `Tests/` and bind only to the public interface pinned in the feature spec. Two validation fixtures (correct, broken) prove the oracle discriminates. The oracle and fixtures live in `eval/oracle*` — grader-only, never copied into the harness workdir.

**Tech Stack:** Swift 5.9 SwiftPM package, XCTest, `async/await`, `@MainActor`. No SwiftUI/UIKit imports (keeps it `swift test`-runnable on macOS).

---

## Background (read before starting)

This plan implements §5 and the iOS portion of §4.1 of `docs/superpowers/specs/2026-05-28-nl-native-eval-design.md`. Key invariants from the spec:

- **The oracle must be mechanically unreachable by platform agents.** It lives under `eval/oracle/` and `eval/oracle-reference/`, never under `eval/workdir/`.
- **The oracle binds to a spec-pinned public interface** (module `NotesFeature`, exact type/method names). If a future generated implementation doesn't conform, it fails to compile → correctness = 0 for that cell (legitimate signal). The oracle therefore uses `import NotesFeature`, never `@testable import`.
- **Headroom:** the feature logic (pagination boundary, search-resets-page, load-more no-op past last page) is deliberately defect-prone so a sloppy implementation scores below ceiling.

## File Structure

```
eval/
  feature-spec/                         # NL Native input specs (markdown) — harness reads these later
    features/notes.md
    data-models/notes.md
    api-contracts/notes.md
    interactions/notes.md
    testable-interface-ios.md           # pins the Swift public surface the oracle binds to
  oracle/
    ios/
      Package.swift
      Sources/NotesFeature/.gitkeep     # SLOT: implementation-under-test drops here (empty in repo)
      Tests/NotesFeatureOracleTests/
        StubNotesAPI.swift              # in-memory fake conforming to NotesAPI
        NotesViewModelOracleTests.swift # the held-out tests
  oracle-reference/
    ios/
      correct/NotesFeature/             # correct impl → oracle must PASS
        Models.swift
        NotesAPI.swift
        NotesViewModel.swift
      broken/NotesFeature/              # defective impl → oracle must FAIL
        Models.swift
        NotesAPI.swift
        NotesViewModel.swift
  scripts/
    validate-ios-oracle.sh             # copies a variant into the slot, runs swift test, asserts pass/fail
```

**Responsibilities:** `feature-spec/` is harness input (the contract). `oracle/ios/Tests/` is the measurement. `oracle-reference/` are validation fixtures only. `scripts/validate-ios-oracle.sh` proves the oracle discriminates.

---

## Task 1: Scaffold the eval directories and Swift package

**Files:**
- Create: `eval/oracle/ios/Package.swift`
- Create: `eval/oracle/ios/Sources/NotesFeature/.gitkeep`
- Create: `eval/.gitignore`

- [ ] **Step 1: Create the directory tree**

Run:
```bash
mkdir -p eval/feature-spec/{features,data-models,api-contracts,interactions} \
         eval/oracle/ios/Sources/NotesFeature \
         eval/oracle/ios/Tests/NotesFeatureOracleTests \
         eval/oracle-reference/ios/correct/NotesFeature \
         eval/oracle-reference/ios/broken/NotesFeature \
         eval/scripts
touch eval/oracle/ios/Sources/NotesFeature/.gitkeep
```

- [ ] **Step 2: Write `eval/oracle/ios/Package.swift`**

```swift
// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "NotesFeature",
    platforms: [.macOS(.v13)],
    products: [
        .library(name: "NotesFeature", targets: ["NotesFeature"]),
    ],
    targets: [
        .target(name: "NotesFeature"),
        .testTarget(
            name: "NotesFeatureOracleTests",
            dependencies: ["NotesFeature"]
        ),
    ]
)
```

- [ ] **Step 3: Write `eval/.gitignore`** (keep build artifacts out of the repo)

```gitignore
.build/
*.xcodeproj
DerivedData/
oracle/ios/Sources/NotesFeature/*.swift
workdir/
```

Note: the last line ignores any implementation dropped into the slot — only `.gitkeep` is tracked, so the slot stays empty in git.

- [ ] **Step 4: Commit**

```bash
git add eval/oracle/ios/Package.swift eval/oracle/ios/Sources/NotesFeature/.gitkeep eval/.gitignore
git commit -m "eval: scaffold directories and iOS oracle Swift package"
```

---

## Task 2: Write the NL Native feature specs (harness input)

These are the contract the oracle pins to and the harness will later consume. Markdown, no code to test — verify by review.

**Files:**
- Create: `eval/feature-spec/features/notes.md`
- Create: `eval/feature-spec/data-models/notes.md`
- Create: `eval/feature-spec/api-contracts/notes.md`
- Create: `eval/feature-spec/interactions/notes.md`
- Create: `eval/feature-spec/testable-interface-ios.md`

- [ ] **Step 1: Write `features/notes.md`** (EARS requirements + Given/When/Then)

```markdown
# Feature: Notes (list, search, tag-filter, paginate) with Auth

## Requirements (EARS)
- REQ-001: When the user submits valid credentials, the system shall establish a session.
- REQ-002: If the user submits invalid credentials, the system shall report an error and establish no session.
- REQ-003: While no session exists, if the user requests notes, the system shall report an unauthenticated error and load no notes.
- REQ-004: When the user opens the list with a session, the system shall load the first page of notes (page size 20).
- REQ-005: When the user requests the next page, the system shall append the next page and advance the current page.
- REQ-006: While the current page is the last page, if the user requests the next page, the system shall make no further request.
- REQ-007: When the user searches, the system shall reset to the first page and replace the list with matches.
- REQ-008: When the user filters by tag, the system shall reset to the first page and replace the list with matches.
- REQ-009: If a list request fails, the system shall report the error and stop loading without altering the existing list on a failed first page (list remains empty if none loaded).

## Scenarios (Given/When/Then)
- Happy login: Given valid credentials, When login, Then a session exists and no error.
- Bad login: Given invalid credentials, When login, Then error set and no session.
- Guarded load: Given no session, When refresh, Then unauthenticated error and empty list.
- First page: Given a session and 5 notes (page size 2), When refresh, Then notes = first 2 and canLoadMore is true.
- Next page: Given first page loaded, When loadNextPage, Then notes = first 4 and page = 2.
- Last page: Given all pages loaded, When loadNextPage again, Then no API call and list unchanged.
- Search resets: Given page 2 loaded, When search matches 2 notes, Then page = 1 and list = the 2 matches.
- Tag filter: Given a session, When filterByTag("home"), Then page = 1 and list = first page of home-tagged notes.
- List error: Given the list call will fail, When refresh, Then error is the server message and isLoading is false.
```

- [ ] **Step 2: Write `data-models/notes.md`**

```markdown
# Data Models (v1.0.0)

## Note
- id: string (stable identifier)
- title: string
- tags: array<string>

## Session
- token: string

## NotesPage
- notes: array<Note>
- page: int (1-based)
- totalPages: int (>= 1)
- totalCount: int (>= 0)
```

- [ ] **Step 3: Write `api-contracts/notes.md`**

```markdown
# API Contract: notes (v1.0.0)

## POST /auth/login
Request: { email: string, password: string }
Response 200: { token: string }
Errors: 401 invalid_credentials → message "Invalid credentials"

## GET /notes
Query: search?: string, tag?: string, page: int=1, pageSize: int=20
Response 200: NotesPage
Errors: 401 unauthenticated; 500 server { message: string }
Semantics:
- search: case-insensitive substring match on title.
- tag: exact match against a note's tags.
- pagination: 1-based; totalPages = ceil(totalCount / pageSize), minimum 1.
```

- [ ] **Step 4: Write `interactions/notes.md`**

```markdown
# Interaction Spec

## States
- signedOut: no session; any list action yields an unauthenticated error.
- loading: a request is in flight; isLoading is true.
- loaded: notes present; canLoadMore = (page < totalPages).
- error: a user-visible message is set; isLoading is false.

## Transitions
- search and tag-filter always reset to page 1 before loading.
- loadNextPage is a no-op when canLoadMore is false (no request issued).
- a failed first-page load leaves the list empty and sets error.
```

- [ ] **Step 5: Write `testable-interface-ios.md`** (pins the public Swift surface the oracle binds to)

```markdown
# iOS Testable Interface (binding contract for the oracle)

The iOS logic layer MUST be a pure-Swift module named `NotesFeature` with NO SwiftUI/UIKit
imports, so it builds and tests via `swift test` on macOS. It MUST expose exactly:

## Value types (public, Equatable, Sendable)
- `Note` — init(id: String, title: String, tags: [String]); public lets id, title, tags.
- `Session` — init(token: String); public let token.
- `NotesQuery` — init(search: String? = nil, tag: String? = nil, page: Int = 1, pageSize: Int = 20); public vars.
- `NotesPage` — init(notes: [Note], page: Int, totalPages: Int, totalCount: Int); public lets.
- `NotesError: Error, Equatable` — cases `.unauthenticated`, `.server(String)`.

## Protocol (public)
```swift
public protocol NotesAPI: Sendable {
    func login(email: String, password: String) async throws -> Session
    func listNotes(_ query: NotesQuery) async throws -> NotesPage
}
```

## View model (public, @MainActor, final class `NotesViewModel`)
- init(api: NotesAPI, pageSize: Int = 20)
- read-only published-style state: `notes: [Note]`, `isLoading: Bool`, `error: String?`,
  `page: Int`, `totalPages: Int`, `session: Session?`
- computed `canLoadMore: Bool` (== page < totalPages)
- async methods: `login(email:password:)`, `search(_:)`, `filterByTag(_:)`, `refresh()`, `loadNextPage()`
- error messages: `.unauthenticated` → "Not signed in."; `.server(m)` → m; unknown → "Something went wrong."
```

- [ ] **Step 6: Commit**

```bash
git add eval/feature-spec
git commit -m "eval: add Notes toy-feature NL Native specs + iOS testable interface"
```

---

## Task 3: Write the iOS oracle (tests first — they must fail to compile against the empty slot)

**Files:**
- Create: `eval/oracle/ios/Tests/NotesFeatureOracleTests/StubNotesAPI.swift`
- Create: `eval/oracle/ios/Tests/NotesFeatureOracleTests/NotesViewModelOracleTests.swift`

- [ ] **Step 1: Write `StubNotesAPI.swift`** (in-memory fake conforming to the public `NotesAPI`)

```swift
import Foundation
import NotesFeature

/// In-memory NotesAPI used by the oracle. Applies search, tag, and pagination
/// deterministically so view-model behaviour is the only thing under test.
final class StubNotesAPI: NotesAPI, @unchecked Sendable {
    let all: [Note]
    let validCredentials: (email: String, password: String)?
    let failListWith: NotesError?
    private(set) var listCallCount = 0

    init(all: [Note],
         validCredentials: (email: String, password: String)? = ("a@b.com", "pw"),
         failListWith: NotesError? = nil) {
        self.all = all
        self.validCredentials = validCredentials
        self.failListWith = failListWith
    }

    func login(email: String, password: String) async throws -> Session {
        if let c = validCredentials, c.email == email, c.password == password {
            return Session(token: "tok")
        }
        throw NotesError.server("Invalid credentials")
    }

    func listNotes(_ query: NotesQuery) async throws -> NotesPage {
        listCallCount += 1
        if let failure = failListWith { throw failure }

        var filtered = all
        if let s = query.search, !s.isEmpty {
            filtered = filtered.filter { $0.title.range(of: s, options: .caseInsensitive) != nil }
        }
        if let t = query.tag {
            filtered = filtered.filter { $0.tags.contains(t) }
        }

        let total = filtered.count
        let size = max(1, query.pageSize)
        let totalPages = max(1, Int(ceil(Double(total) / Double(size))))
        let start = (query.page - 1) * size
        let slice = Array(filtered.dropFirst(max(0, start)).prefix(size))
        return NotesPage(notes: slice, page: query.page, totalPages: totalPages, totalCount: total)
    }
}
```

- [ ] **Step 2: Write `NotesViewModelOracleTests.swift`** (the held-out tests)

```swift
import XCTest
import NotesFeature

@MainActor
final class NotesViewModelOracleTests: XCTestCase {

    private func fixtureNotes() -> [Note] {
        [
            Note(id: "1", title: "Groceries",      tags: ["home"]),
            Note(id: "2", title: "Gym plan",        tags: ["health"]),
            Note(id: "3", title: "Grocery list 2",  tags: ["home"]),
            Note(id: "4", title: "Work tasks",      tags: ["work"]),
            Note(id: "5", title: "Reading",         tags: ["home"]),
        ]
    }

    private func makeVM(_ api: StubNotesAPI) -> NotesViewModel {
        NotesViewModel(api: api, pageSize: 2)
    }

    private func signedIn(_ api: StubNotesAPI) async -> NotesViewModel {
        let vm = makeVM(api)
        await vm.login(email: "a@b.com", password: "pw")
        return vm
    }

    func test_login_success_setsSession() async {
        let vm = makeVM(StubNotesAPI(all: fixtureNotes()))
        await vm.login(email: "a@b.com", password: "pw")
        XCTAssertNotNil(vm.session)
        XCTAssertNil(vm.error)
        XCTAssertFalse(vm.isLoading)
    }

    func test_login_failure_setsErrorNoSession() async {
        let vm = makeVM(StubNotesAPI(all: fixtureNotes()))
        await vm.login(email: "a@b.com", password: "wrong")
        XCTAssertNil(vm.session)
        XCTAssertNotNil(vm.error)
    }

    func test_loadBeforeLogin_setsErrorAndEmptyList() async {
        let vm = makeVM(StubNotesAPI(all: fixtureNotes()))
        await vm.refresh()
        XCTAssertNotNil(vm.error)
        XCTAssertTrue(vm.notes.isEmpty)
        XCTAssertFalse(vm.isLoading)
    }

    func test_refresh_loadsFirstPage() async {
        let vm = await signedIn(StubNotesAPI(all: fixtureNotes()))
        await vm.refresh()
        XCTAssertEqual(vm.notes.map(\.id), ["1", "2"])
        XCTAssertEqual(vm.page, 1)
        XCTAssertTrue(vm.canLoadMore)
    }

    func test_loadNextPage_appendsAndAdvances() async {
        let vm = await signedIn(StubNotesAPI(all: fixtureNotes()))
        await vm.refresh()
        await vm.loadNextPage()
        XCTAssertEqual(vm.notes.map(\.id), ["1", "2", "3", "4"])
        XCTAssertEqual(vm.page, 2)
    }

    func test_loadNextPage_stopsAtLastPage() async {
        let api = StubNotesAPI(all: fixtureNotes())
        let vm = await signedIn(api)
        await vm.refresh()       // page 1
        await vm.loadNextPage()  // page 2
        await vm.loadNextPage()  // page 3 (last: 5 notes / 2 => 3 pages)
        XCTAssertEqual(vm.notes.count, 5)
        XCTAssertFalse(vm.canLoadMore)
        let callsBefore = api.listCallCount
        await vm.loadNextPage()  // must be a no-op
        XCTAssertEqual(api.listCallCount, callsBefore,
                       "loadNextPage past the last page must not call the API")
        XCTAssertEqual(vm.notes.count, 5)
    }

    func test_search_resetsToFirstPage() async {
        let vm = await signedIn(StubNotesAPI(all: fixtureNotes()))
        await vm.refresh()
        await vm.loadNextPage()       // now on page 2
        await vm.search("Groc")       // matches "Groceries" + "Grocery list 2"
        XCTAssertEqual(vm.page, 1)
        XCTAssertEqual(vm.notes.map(\.id), ["1", "3"])
        XCTAssertFalse(vm.canLoadMore)
    }

    func test_filterByTag_resetsAndFilters() async {
        let vm = await signedIn(StubNotesAPI(all: fixtureNotes()))
        await vm.refresh()       // page 1
        await vm.loadNextPage()  // advance to page 2 — makes the page-reset assertion load-bearing
        await vm.filterByTag("home")  // ids 1,3,5; page size 2 => page 1 = [1,3]
        XCTAssertEqual(vm.page, 1)
        XCTAssertEqual(vm.notes.map(\.id), ["1", "3"])
        XCTAssertTrue(vm.canLoadMore)
    }

    func test_listError_setsErrorAndClearsLoading() async {
        let api = StubNotesAPI(all: fixtureNotes(), failListWith: .server("boom"))
        let vm = await signedIn(api)
        await vm.refresh()
        XCTAssertEqual(vm.error, "boom")
        XCTAssertFalse(vm.isLoading)
        XCTAssertTrue(vm.notes.isEmpty)
    }
}
```

- [ ] **Step 3: Run the oracle against the empty slot to confirm it fails to build**

Run:
```bash
cd eval/oracle/ios && swift test
```
Expected: BUILD FAILURE — `cannot find 'NotesViewModel' in scope` (and `Note`, `Session`, etc.). This is correct: with no implementation in the slot, the oracle cannot compile. (An empty slot = correctness 0, by design.)

- [ ] **Step 4: Commit**

```bash
git add eval/oracle/ios/Tests
git commit -m "eval: add iOS held-out oracle (StubNotesAPI + NotesViewModel tests)"
```

---

## Task 4: Write the correct reference implementation; oracle must go green

**Files:**
- Create: `eval/oracle-reference/ios/correct/NotesFeature/Models.swift`
- Create: `eval/oracle-reference/ios/correct/NotesFeature/NotesAPI.swift`
- Create: `eval/oracle-reference/ios/correct/NotesFeature/NotesViewModel.swift`

- [ ] **Step 1: Write `correct/NotesFeature/Models.swift`**

```swift
import Foundation

public struct Note: Equatable, Sendable {
    public let id: String
    public let title: String
    public let tags: [String]
    public init(id: String, title: String, tags: [String]) {
        self.id = id
        self.title = title
        self.tags = tags
    }
}

public struct Session: Equatable, Sendable {
    public let token: String
    public init(token: String) { self.token = token }
}

public struct NotesQuery: Equatable, Sendable {
    public var search: String?
    public var tag: String?
    public var page: Int
    public var pageSize: Int
    public init(search: String? = nil, tag: String? = nil, page: Int = 1, pageSize: Int = 20) {
        self.search = search
        self.tag = tag
        self.page = page
        self.pageSize = pageSize
    }
}

public struct NotesPage: Equatable, Sendable {
    public let notes: [Note]
    public let page: Int
    public let totalPages: Int
    public let totalCount: Int
    public init(notes: [Note], page: Int, totalPages: Int, totalCount: Int) {
        self.notes = notes
        self.page = page
        self.totalPages = totalPages
        self.totalCount = totalCount
    }
}

public enum NotesError: Error, Equatable, Sendable {
    case unauthenticated
    case server(String)
}
```

- [ ] **Step 2: Write `correct/NotesFeature/NotesAPI.swift`**

```swift
public protocol NotesAPI: Sendable {
    func login(email: String, password: String) async throws -> Session
    func listNotes(_ query: NotesQuery) async throws -> NotesPage
}
```

- [ ] **Step 3: Write `correct/NotesFeature/NotesViewModel.swift`**

```swift
import Foundation

@MainActor
public final class NotesViewModel {
    public private(set) var notes: [Note] = []
    public private(set) var isLoading = false
    public private(set) var error: String?
    public private(set) var page = 1
    public private(set) var totalPages = 1
    public private(set) var session: Session?

    private let api: NotesAPI
    private let pageSize: Int
    private var searchText: String?
    private var tagFilter: String?

    public init(api: NotesAPI, pageSize: Int = 20) {
        self.api = api
        self.pageSize = pageSize
    }

    public var canLoadMore: Bool { page < totalPages }

    public func login(email: String, password: String) async {
        isLoading = true
        error = nil
        defer { isLoading = false }
        do {
            session = try await api.login(email: email, password: password)
        } catch {
            session = nil
            self.error = Self.message(error)
        }
    }

    public func search(_ text: String) async {
        searchText = text.isEmpty ? nil : text
        await loadFirstPage()
    }

    public func filterByTag(_ tag: String?) async {
        tagFilter = tag
        await loadFirstPage()
    }

    public func refresh() async {
        await loadFirstPage()
    }

    public func loadNextPage() async {
        guard canLoadMore else { return }
        await load(targetPage: page + 1, append: true)
    }

    private func loadFirstPage() async {
        await load(targetPage: 1, append: false)
    }

    private func load(targetPage: Int, append: Bool) async {
        guard session != nil else {
            error = Self.message(NotesError.unauthenticated)
            return
        }
        isLoading = true
        error = nil
        defer { isLoading = false }
        do {
            let query = NotesQuery(search: searchText, tag: tagFilter, page: targetPage, pageSize: pageSize)
            let result = try await api.listNotes(query)
            page = result.page
            totalPages = result.totalPages
            if append {
                notes += result.notes
            } else {
                notes = result.notes
            }
        } catch {
            self.error = Self.message(error)
        }
    }

    private static func message(_ error: Error) -> String {
        if let e = error as? NotesError {
            switch e {
            case .unauthenticated: return "Not signed in."
            case .server(let m):   return m
            }
        }
        return "Something went wrong."
    }
}
```

- [ ] **Step 4: Run the oracle against the correct implementation**

Run:
```bash
cd eval/oracle/ios
rm -f Sources/NotesFeature/.gitkeep
cp ../../oracle-reference/ios/correct/NotesFeature/*.swift Sources/NotesFeature/
swift test
```
Expected: PASS — all 9 tests green.

- [ ] **Step 5: Clean the slot and commit the reference**

Run:
```bash
cd eval/oracle/ios
rm -f Sources/NotesFeature/*.swift
touch Sources/NotesFeature/.gitkeep
cd ../../..
git add eval/oracle-reference/ios/correct
git commit -m "eval: add correct iOS reference impl (oracle passes)"
```

---

## Task 5: Write the broken implementation; oracle must catch it

The broken variant copies the correct one but introduces three real defects: `search` does **not** reset to page 1, `loadNextPage` does **not** guard on `canLoadMore`, and `filterByTag` does **not** reset to page 1. These must fail `test_search_resetsToFirstPage`, `test_loadNextPage_stopsAtLastPage`, and `test_filterByTag_resetsAndFilters` respectively.

**Files:**
- Create: `eval/oracle-reference/ios/broken/NotesFeature/Models.swift` (identical to correct)
- Create: `eval/oracle-reference/ios/broken/NotesFeature/NotesAPI.swift` (identical to correct)
- Create: `eval/oracle-reference/ios/broken/NotesFeature/NotesViewModel.swift` (defective)

- [ ] **Step 1: Copy the unchanged files**

Run:
```bash
cp eval/oracle-reference/ios/correct/NotesFeature/Models.swift  eval/oracle-reference/ios/broken/NotesFeature/Models.swift
cp eval/oracle-reference/ios/correct/NotesFeature/NotesAPI.swift eval/oracle-reference/ios/broken/NotesFeature/NotesAPI.swift
```

- [ ] **Step 2: Write the defective `broken/NotesFeature/NotesViewModel.swift`**

Identical to the correct version EXCEPT the two marked methods:

```swift
import Foundation

@MainActor
public final class NotesViewModel {
    public private(set) var notes: [Note] = []
    public private(set) var isLoading = false
    public private(set) var error: String?
    public private(set) var page = 1
    public private(set) var totalPages = 1
    public private(set) var session: Session?

    private let api: NotesAPI
    private let pageSize: Int
    private var searchText: String?
    private var tagFilter: String?

    public init(api: NotesAPI, pageSize: Int = 20) {
        self.api = api
        self.pageSize = pageSize
    }

    public var canLoadMore: Bool { page < totalPages }

    public func login(email: String, password: String) async {
        isLoading = true
        error = nil
        defer { isLoading = false }
        do {
            session = try await api.login(email: email, password: password)
        } catch {
            session = nil
            self.error = Self.message(error)
        }
    }

    // DEFECT 1: does not reset to page 1 — reloads the current page.
    public func search(_ text: String) async {
        searchText = text.isEmpty ? nil : text
        await load(targetPage: page, append: false)
    }

    // DEFECT 3: does not reset to page 1 — reloads the current page.
    public func filterByTag(_ tag: String?) async {
        tagFilter = tag
        await load(targetPage: page, append: false)
    }

    public func refresh() async {
        await load(targetPage: 1, append: false)
    }

    // DEFECT 2: no canLoadMore guard — always requests the next page.
    public func loadNextPage() async {
        await load(targetPage: page + 1, append: true)
    }

    private func load(targetPage: Int, append: Bool) async {
        guard session != nil else {
            error = Self.message(NotesError.unauthenticated)
            return
        }
        isLoading = true
        error = nil
        defer { isLoading = false }
        do {
            let query = NotesQuery(search: searchText, tag: tagFilter, page: targetPage, pageSize: pageSize)
            let result = try await api.listNotes(query)
            page = result.page
            totalPages = result.totalPages
            if append {
                notes += result.notes
            } else {
                notes = result.notes
            }
        } catch {
            self.error = Self.message(error)
        }
    }

    private static func message(_ error: Error) -> String {
        if let e = error as? NotesError {
            switch e {
            case .unauthenticated: return "Not signed in."
            case .server(let m):   return m
            }
        }
        return "Something went wrong."
    }
}
```

- [ ] **Step 3: Run the oracle against the broken implementation**

Run:
```bash
cd eval/oracle/ios
rm -f Sources/NotesFeature/.gitkeep Sources/NotesFeature/*.swift
cp ../../oracle-reference/ios/broken/NotesFeature/*.swift Sources/NotesFeature/
swift test
```
Expected: FAILURE — exactly three methods fail (`test_search_resetsToFirstPage`, `test_loadNextPage_stopsAtLastPage`, `test_filterByTag_resetsAndFilters`); the other 6 pass. This proves the oracle discriminates correct from broken.

- [ ] **Step 4: Clean the slot and commit the broken fixture**

Run:
```bash
cd eval/oracle/ios
rm -f Sources/NotesFeature/*.swift
touch Sources/NotesFeature/.gitkeep
cd ../../..
git add eval/oracle-reference/ios/broken
git commit -m "eval: add broken iOS fixture (oracle catches 2 defects)"
```

---

## Task 6: Automate oracle validation

**Files:**
- Create: `eval/scripts/validate-ios-oracle.sh`

- [ ] **Step 1: Write `validate-ios-oracle.sh`**

```bash
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
```

- [ ] **Step 2: Make it executable and run it**

Run:
```bash
chmod +x eval/scripts/validate-ios-oracle.sh
eval/scripts/validate-ios-oracle.sh
```
Expected output ends with:
```
>> correct => pass
== broken: expect build OK + exactly the seeded defects caught ==
>> broken => fail (caught exactly: test_search_resetsToFirstPage test_loadNextPage_stopsAtLastPage test_filterByTag_resetsAndFilters)
ORACLE VALIDATION OK: passes on correct, fails on exactly the seeded defects.
```

- [ ] **Step 3: Commit**

```bash
git add eval/scripts/validate-ios-oracle.sh
git commit -m "eval: add iOS oracle validation script (discrimination check)"
```

---

## Done criteria (maps to spec §9)

- [ ] Feature specs written under `eval/feature-spec/` (harness input + pinned iOS interface).
- [ ] iOS oracle exists under `eval/oracle/ios/` and binds only to the public interface (no `@testable`).
- [ ] Oracle is mechanically out of reach: lives outside any future `eval/workdir/`; the slot is git-empty.
- [ ] `validate-ios-oracle.sh` proves the oracle passes on correct and fails on broken (headroom + discrimination).
- [ ] All work committed on branch `nl-native-workflow-improvements`.

## Follow-on plans (not in scope here)

- **Plan 1b:** Android held-out oracle (JUnit/JVM) mirroring this structure; reference + broken fixtures; `validate-android-oracle.sh`.
- **Plan 1c:** Backend held-out oracle as black-box HTTP tests against the running server (implementation-agnostic); reference + broken fixtures.
- **Plan 2:** Scoring + blind median-of-3 judge harness (consumes these oracles).
- **Plan 3:** Eval orchestrator (fan-out once → fork 3 worktrees → baseline/treatment/ceiling verify strategies → score → report).
