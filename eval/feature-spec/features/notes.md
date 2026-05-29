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
