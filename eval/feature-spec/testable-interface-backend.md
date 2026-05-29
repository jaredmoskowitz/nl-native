# Backend Testable Interface (binding contract for the oracle)

The backend MUST be a single runnable `server.py` (Python 3 standard library only) started as
`python3 server.py <port>`, serving on `127.0.0.1:<port>`, seeded with the fixed Notes dataset
below. The oracle is black-box (HTTP only).

## Dataset (fixed)
id=1 "Groceries" [home]; id=2 "Gym plan" [health]; id=3 "Grocery list 2" [home];
id=4 "Work tasks" [work]; id=5 "Reading" [home]. Valid credentials: a@b.com / pw → token "tok".

## Endpoints
- `POST /auth/login` body `{email, password}` → 200 `{"token": "tok"}` for valid creds; else 401 `{"message": "Invalid credentials"}`.
- `GET /notes?search=&tag=&page=&pageSize=` — requires header `Authorization: Bearer tok`; missing/invalid → 401 `{"message": "unauthenticated"}`.
  - `search`: case-insensitive substring on title. `tag`: exact match in tags.
  - `page` 1-based (default 1); `pageSize` default 20.
  - 200 response: `{"notes": [{"id","title","tags"}], "page": int, "totalPages": int, "totalCount": int}`
  - `totalPages = max(1, ceil(totalCount / pageSize))`.
