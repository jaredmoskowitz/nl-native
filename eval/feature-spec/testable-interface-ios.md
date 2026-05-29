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
