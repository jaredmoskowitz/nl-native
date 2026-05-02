# Schema: API Contract

Copy this template to `specs/changes/<change-name>/specs/core/api-contracts/<name>.md`.

Only the Architect writes or modifies API contracts. Only the Architect may increment the version number.

---

```markdown
# API Contract: [Name]
Version: 1.0.0
Status: draft

## Overview

[One paragraph describing what this contract covers — which domain, which resource, which set of operations.]

## Authentication

[Describe the auth scheme used across all endpoints in this contract, e.g.:]
- Bearer token in Authorization header
- Token obtained from [auth endpoint or SDK]
- Token expires after [duration]; refresh via [mechanism]

## Base URL

`/api/v1/[resource]`

---

## Endpoints

### [VERB] /[path]

[One sentence: what does this endpoint do?]

**Auth required:** Yes | No | Optional

**Request**

| Field | Type | Required | Constraints | Description |
|---|---|---|---|---|
| field_name | string | yes | max 255 chars | [description] |
| other_field | integer | no | min 0 | [description] |

*If the request is empty (GET with no body), write: "No request body."*

**Response — 200 OK**

| Field | Type | Nullable | Description |
|---|---|---|---|
| id | string (uuid) | no | [description] |
| created_at | string (ISO 8601) | no | [description] |
| field_name | string | no | [description] |

**Response — Streaming (if applicable)**

[Describe SSE or WebSocket response format if this endpoint streams:]

```
event: [event-type]
data: {"field": "value"}
```

**Errors**

| Status | Code | When |
|---|---|---|
| 400 | INVALID_INPUT | [specific condition, e.g. "required field missing"] |
| 401 | UNAUTHORIZED | [specific condition, e.g. "token expired or missing"] |
| 403 | FORBIDDEN | [specific condition, e.g. "user does not own this resource"] |
| 404 | NOT_FOUND | [specific condition] |
| 409 | CONFLICT | [specific condition, e.g. "duplicate entry"] |
| 422 | VALIDATION_ERROR | [specific condition] |
| 500 | INTERNAL_ERROR | Unexpected server error |

**Error response shape:**
```json
{
  "error": {
    "code": "INVALID_INPUT",
    "message": "Human-readable description",
    "details": {}
  }
}
```

---

### [VERB] /[path]

[Repeat for each endpoint in this contract]

---

## Pagination (if applicable)

[Describe the pagination scheme if any list endpoints use it:]

**Request parameters:**
- `cursor`: string — opaque cursor from previous response
- `limit`: integer — max items per page, default 20, max 100

**Response envelope:**
```json
{
  "items": [...],
  "next_cursor": "opaque-string-or-null",
  "has_more": true
}
```

## Rate limiting (if applicable)

[Describe any rate limits, e.g. "100 requests per minute per user. Exceeded requests receive 429 with Retry-After header."]

## Changelog

| Version | Change | Date |
|---|---|---|
| 1.0.0 | Initial contract | [date] |
```

---

## Versioning rules

| Change Type | Version Bump | Example |
|---|---|---|
| Clarification only, no behavioral change | Patch (1.0.0 → 1.0.1) | Rewording a field description |
| New optional field in response | Minor (1.0.0 → 1.1.0) | Adding `subtitle` to an existing response |
| New endpoint added | Minor (1.0.0 → 1.1.0) | New GET /items/search endpoint |
| Field renamed | Major (1.0.0 → 2.0.0) | `user_name` → `username` |
| Field removed | Major (1.0.0 → 2.0.0) | Removing `legacy_id` field |
| Required field added to request | Major (1.0.0 → 2.0.0) | Existing callers would break |
| Status code or error code changed | Major (1.0.0 → 2.0.0) | 404 → 403 for auth-required resources |

**Only the Architect increments contract versions.**

When a version is incremented during active implementation:
1. The Architect updates the contract file and changelog
2. All platform task lists that declare this contract as a dependency are notified
3. Dependent agents halt, re-read the updated contract, regenerate their task lists, and resume
