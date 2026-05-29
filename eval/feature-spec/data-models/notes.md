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
