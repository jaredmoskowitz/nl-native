Wire mobile platform mock data layers to the real backend. This command generates the real API client implementations, runs them against the live backend, and reports any mismatches vs. the mock fixture data.

**This command is triggered automatically** when backend tasks complete during `/fan-out` and at least one mobile platform has also completed its tasks. It can also be run manually: `/connect`

---

## Pre-flight

1. Find the active change: `specs/changes/<name>/`
2. Verify backend tasks are complete: `$CHANGE/tasks/backend-tasks.md` — all tasks `[x]`
3. Verify at least one mobile platform has tasks complete
4. Load:
   - `$CHANGE/specs/core/api-contracts/*.md` — the contract both sides should agree on
   - `$CHANGE/specs/core/data-models/*.md` — the data shapes
   - Platform implementation specs: `$CHANGE/specs/ios/implementation.md`, `$CHANGE/specs/android/implementation.md`
   - `platforms/backend/AGENTS.md` — backend service details (base URL, auth method)

---

## Step 1 — Verify backend is reachable

Determine the backend base URL from `platforms/backend/AGENTS.md` (local dev URL or deployed URL).

```bash
# Health check — try to hit the base URL
curl -s -o /dev/null -w "%{http_code}" <BASE_URL>/health
# Or just check if the service responds
curl -s -o /dev/null -w "%{http_code}" <BASE_URL>
```

If the backend is not reachable:
- Check if local dev needs to be started (e.g., `supabase start`, `wrangler dev`)
- Report instructions to the user and stop

---

## Step 2 — Contract smoke test

For each endpoint in the API contract, make a real request and verify the response shape matches:

```bash
# For each endpoint:
# 1. Authenticate (if required)
# 2. Send a request with valid test data
# 3. Verify response status code
# 4. Verify response body has all fields specified in the contract
# 5. Verify field types match
```

Report results:

```
Contract smoke test
  POST /api/v1/notes     → 201 ✓  Response shape matches contract ✓
  GET  /api/v1/notes      → 200 ✓  Response shape matches contract ✓
  DELETE /api/v1/notes/:id → 204 ✓  No body expected ✓
```

For each error case in the contract, try to trigger it:

```
Error case coverage
  POST /api/v1/notes (no title)     → 400 INVALID_INPUT ✓
  POST /api/v1/notes (no auth)      → 401 UNAUTHORIZED ✓
  DELETE /api/v1/notes/nonexistent  → 404 NOT_FOUND ✓
```

---

## Step 3 — Generate real API client implementations

### For iOS

Read the mock protocol conformances from the iOS codebase. For each protocol:

1. Create a real implementation that hits the actual backend
2. Use URLSession (or whatever the iOS AGENTS.md specifies)
3. Map the API contract request/response shapes to the protocol's types
4. Handle all error codes from the contract

```swift
// Example: generated real implementation
struct RealNotesAPIClient: NotesAPIClient {
    let baseURL: URL
    let authToken: String

    func listNotes() async throws -> [Note] {
        var request = URLRequest(url: baseURL.appendingPathComponent("api/v1/notes"))
        request.setValue("Bearer \(authToken)", forHTTPHeaderField: "Authorization")
        let (data, response) = try await URLSession.shared.data(for: request)
        guard let httpResponse = response as? HTTPURLResponse,
              httpResponse.statusCode == 200 else {
            throw APIError.requestFailed
        }
        return try JSONDecoder().decode([Note].self, from: data)
    }
    // ... other methods
}
```

Place in the same directory as the mock, following iOS AGENTS.md conventions.

### For Android

Same pattern — create real implementations of the API client interfaces:

```kotlin
// Example: generated real implementation
class RealNotesApiClient(
    private val baseUrl: String,
    private val httpClient: HttpClient
) : NotesApiClient {
    override suspend fun listNotes(): List<Note> {
        return httpClient.get("$baseUrl/api/v1/notes").body()
    }
    // ... other methods
}
```

Update the Hilt module to bind the real implementation.

---

## Step 4 — Integration verification

Run the app (or tests) with the real API client and verify:

1. **Fixture data comparison:** Do the real API responses have the same shape as the mock fixture data?
2. **Round-trip test:** Create → Read → Delete cycle works end-to-end
3. **Auth flow:** Token acquisition and refresh work with the real backend
4. **Error handling:** Real error responses are parsed correctly by the mobile clients

Report any mismatches:

```
Integration verification
════════════════════════════════════

iOS
  NotesAPIClient.listNotes()    → ✓ Response matches mock shape
  NotesAPIClient.createNote()   → ✓ Created note returned with ID
  NotesAPIClient.deleteNote()   → ✓ 204 handled correctly
  Auth token refresh            → ✓ Works with real backend

Android
  NotesApiClient.listNotes()    → ✓ Response matches mock shape
  NotesApiClient.createNote()   → ✗ MISMATCH: backend returns `createdAt` but mock used `created_at`
  NotesApiClient.deleteNote()   → ✓ Handled correctly

MISMATCHES FOUND: 1
  Android createNote: field name mismatch (createdAt vs created_at)
  → Fix in: Android API client deserialization OR backend response serialization
  → Contract says: created_at (snake_case) — backend is wrong

════════════════════════════════════
```

---

## Step 5 — Update task lists

After successful connection:

1. Mark mock→real swap as complete in each platform's task list
2. Update `$CHANGE/checkpoints.md` with a `connected` checkpoint
3. Update mock data status (visible in `/status`)

---

## Auto-trigger from `/fan-out`

When running inside `/fan-out`, this command is triggered automatically when:

1. All backend tasks are marked `[x]` in `$CHANGE/tasks/backend-tasks.md`
2. At least one mobile platform has all tasks marked `[x]`

The fan-out orchestrator should check after each backend task completion whether all backend tasks are now done. If so, and a mobile platform is also done, run `/connect`.

If a mobile platform finishes after `/connect` has already run for the other platform, run `/connect` again for the newly completed platform only.

---

## Rules

- Never skip the contract smoke test — always verify the backend implements the contract before wiring mobile clients
- If the backend is unreachable, do not generate real client implementations — they'll be wrong
- Clean up test data created during the smoke test (DELETE anything you POSTed)
- If a mismatch is found, identify which side is wrong by checking the API contract — the contract is the source of truth
- Real client implementations must pass all the same tests that the mock implementations pass
- This command modifies code (generates real implementations) — it's not read-only like `/preview`
