# API Contract: Notes
Version: 1.0.0
Status: approved

## Overview

CRUD operations for user notes. All endpoints require authentication. Users can only access their own notes — server enforces ownership via row-level security.

## Authentication

Bearer token in `Authorization` header. Token obtained from the app's auth system. All requests without a valid token receive 401.

## Base URL

`/api/v1/notes`

---

## Endpoints

### GET /api/v1/notes

Fetch all notes for the authenticated user, ordered by creation time descending.

**Auth required:** Yes

**Request:** No request body. No query parameters in v1.0.0.

**Response — 200 OK**

```json
{
  "notes": [
    {
      "id": "uuid",
      "title": "string",
      "body": "string",
      "created_at": "ISO 8601 string",
      "updated_at": "ISO 8601 string"
    }
  ]
}
```

| Field | Type | Nullable | Description |
|---|---|---|---|
| notes | array | no | Ordered newest first. Empty array if user has no notes. |
| notes[].id | string (uuid) | no | Stable identifier |
| notes[].title | string | no | Note title, max 255 chars |
| notes[].body | string | no | Note body. Empty string if no body was provided. |
| notes[].created_at | string (ISO 8601) | no | UTC timestamp |
| notes[].updated_at | string (ISO 8601) | no | UTC timestamp |

**Errors**

| Status | Code | When |
|---|---|---|
| 401 | UNAUTHORIZED | Missing or expired token |
| 500 | INTERNAL_ERROR | Unexpected server error |

---

### POST /api/v1/notes

Create a new note.

**Auth required:** Yes

**Request**

| Field | Type | Required | Constraints | Description |
|---|---|---|---|---|
| title | string | yes | 1–255 chars | Note title |
| body | string | no | max 50,000 chars | Note body. Omitting is equivalent to empty string. |

**Response — 201 Created**

```json
{
  "note": {
    "id": "uuid",
    "title": "string",
    "body": "string",
    "created_at": "ISO 8601 string",
    "updated_at": "ISO 8601 string"
  }
}
```

Same field definitions as GET response item.

**Errors**

| Status | Code | When |
|---|---|---|
| 400 | INVALID_INPUT | title is missing or empty |
| 400 | INVALID_INPUT | title exceeds 255 characters |
| 400 | INVALID_INPUT | body exceeds 50,000 characters |
| 401 | UNAUTHORIZED | Missing or expired token |
| 500 | INTERNAL_ERROR | Unexpected server error |

**Error response shape:**
```json
{
  "error": {
    "code": "INVALID_INPUT",
    "message": "title is required",
    "field": "title"
  }
}
```

The optional `field` key indicates which request field caused a validation error.

---

### DELETE /api/v1/notes/:id

Delete a note by ID.

**Auth required:** Yes

**Request:** No request body.

**Response — 204 No Content**

Empty body.

**Errors**

| Status | Code | When |
|---|---|---|
| 401 | UNAUTHORIZED | Missing or expired token |
| 403 | FORBIDDEN | Note exists but belongs to a different user |
| 404 | NOT_FOUND | No note with this ID exists |
| 500 | INTERNAL_ERROR | Unexpected server error |

---

## Changelog

| Version | Change | Date |
|---|---|---|
| 1.0.0 | Initial contract — list, create, delete | 2026-04-26 |
