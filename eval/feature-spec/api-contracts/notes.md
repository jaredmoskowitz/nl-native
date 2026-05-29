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
