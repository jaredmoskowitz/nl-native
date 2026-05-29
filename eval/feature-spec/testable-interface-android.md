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
