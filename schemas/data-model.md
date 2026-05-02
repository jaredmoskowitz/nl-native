# Schema: Data Model

Copy this template to `specs/changes/<change-name>/specs/core/data-models/<name>.md`.

Only the Architect writes or modifies data models. Only the Architect may increment the version number.

---

```markdown
# Data Model: [Name]
Version: 1.0.0
Status: draft

## Overview

[One paragraph describing what entities this model covers and how they relate to the system's domain.]

---

## Entities

### [EntityName]

[One sentence: what does this entity represent?]

| Field | Type | Nullable | Default | Constraints | Description |
|---|---|---|---|---|---|
| id | uuid | no | gen_random_uuid() | primary key | |
| created_at | timestamptz | no | now() | | |
| updated_at | timestamptz | no | now() | | updated by trigger |
| user_id | uuid | no | | FK → users.id | owner |
| [field] | [type] | [yes/no] | [value or —] | [constraints] | [description] |

**Indexes:**
| Index | Fields | Type | Purpose |
|---|---|---|---|
| [entity]_user_id_idx | user_id | btree | Lookup by owner |
| [entity]_created_at_idx | created_at | btree | Time-ordered queries |

**Row-Level Security:**
| Policy | Operation | Rule |
|---|---|---|
| Users own their [entities] | SELECT, INSERT, UPDATE, DELETE | `user_id = auth.uid()` |

---

### [AnotherEntity]

[Repeat for each entity]

---

## Relationships

```
[EntityA] ──────── [EntityB]
   1                  many

[EntityB] ──────── [EntityC]
  many               many (via [junction table])
```

[Describe each relationship in prose: "Each [EntityA] belongs to one [EntityB]. Each [EntityB] may have many [EntityA]s. When a [EntityB] is deleted, its [EntityA]s are cascade-deleted."]

---

## Enumerations

### [EnumName]

| Value | Description |
|---|---|
| VALUE_ONE | [when this value is used] |
| VALUE_TWO | [when this value is used] |

---

## Migration notes

[Describe any migration considerations for this version:]
- New tables require a migration
- Column additions to existing tables must be nullable or have a default
- Column renames require a two-phase migration (add new → backfill → drop old)
- Document any data that needs to be seeded

---

## Serialization

[If any field requires special serialization for API transport, document it here:]
- `created_at` is serialized as ISO 8601 string in API responses
- `metadata` is a JSONB column, serialized as a JSON object (never null, default `{}`)

## Changelog

| Version | Change | Date |
|---|---|---|
| 1.0.0 | Initial model | [date] |
```

---

## Type reference

The data model uses abstract types at the spec level. The Backend Expert translates these to concrete service-specific types in the backend implementation spec.

| Spec Type | API Type | iOS Type | Android Type | PostgreSQL | Firestore | DynamoDB |
|---|---|---|---|---|---|---|
| uuid | string | UUID | String | uuid | string | S |
| text | string | String | String | text | string | S |
| varchar(n) | string | String | String | varchar(n) | string | S |
| integer | integer | Int | Int | integer | number | N |
| bigint | integer | Int64 | Long | bigint | number | N |
| boolean | boolean | Bool | Boolean | boolean | boolean | BOOL |
| timestamp | string (ISO 8601) | Date | Instant | timestamptz | Timestamp | S (ISO 8601) |
| json | object | [Codable struct] | [Serializable data class] | jsonb | map | M |
| uuid[] | string[] | [UUID] | List\<String\> | uuid[] | array | L |

**Service agnosticism:** The spec-level data model (written by the Architect) uses the Spec Type column. RLS policies and indexes in the spec describe the *access pattern and intent*, not the implementation mechanism. The Backend Expert translates these to concrete service primitives (Postgres RLS, Firestore Security Rules, DynamoDB IAM policies, middleware guards, etc.) in their implementation spec.

## Versioning rules

Same as API contracts — only the Architect increments versions, following semver semantics:

| Change | Version Bump |
|---|---|
| New nullable column | Minor |
| New non-nullable column with default | Minor |
| New table | Minor |
| Column renamed | Major |
| Column removed | Major |
| Type changed | Major |
| Non-nullable column without default | Major |
