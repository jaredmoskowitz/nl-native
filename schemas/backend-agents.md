# Schema: Backend AGENTS.md

Copy this template to `platforms/backend/AGENTS.md` and fill it in when configuring your project's backend. The Backend Expert reads this file before every implementation.

This file is created once per project — typically during your first `/fan-out` — and updated as your backend stack evolves.

---

```markdown
# Backend: AGENTS.md

## Service

**Primary service:** [Supabase | Firebase | Cloudflare Workers | AWS Lambda | Custom server | etc.]
**Language/runtime:** [TypeScript/Deno | TypeScript/Node | Python | Go | Rust | etc.]

## Architecture

**Database:** [Supabase Postgres | Firestore | PlanetScale | DynamoDB | SQLite/Turso | etc.]
**Auth provider:** [Supabase Auth | Firebase Auth | Clerk | Auth0 | Custom JWT | etc.]
**File storage:** [Supabase Storage | Cloudflare R2 | S3 | Firebase Storage | etc.]
**Serverless functions:** [Supabase Edge Functions | Cloudflare Workers | Vercel Functions | Firebase Cloud Functions | etc.]
**Additional services:** [List any external APIs, queues, search engines, etc.]

## Project Structure

[Describe the directory layout for backend code. Example:]

platforms/backend/
├── supabase/
│   ├── functions/          # Edge functions (one directory per function)
│   ├── migrations/         # Timestamped SQL migrations
│   └── config.toml         # Supabase project config
├── packages/
│   ├── api/                # Shared typed API client (if applicable)
│   ├── types/              # Auto-generated and hand-written types
│   └── validators/         # Shared Zod schemas (if applicable)
└── ...

## Conventions

[Project-specific rules. Examples:]

- All database queries go through the typed API package — never query the database directly from app code
- Use parameterized queries exclusively — no string interpolation in SQL
- Edge functions use Deno; all other server code uses Node
- Run `pnpm db:types` after every migration to regenerate types
- Naming: snake_case for database columns, camelCase for API responses
- Migrations are timestamped: `YYYYMMDDHHMMSS_description.sql`
- Soft deletes (deleted_at timestamp) — never hard-delete user data
- All secrets in environment variables, never committed

## Auth Strategy

[How auth works end-to-end. Example:]

- Supabase Auth handles sign-up/sign-in (email + Apple OAuth)
- JWT in Authorization header for all authenticated requests
- Row-Level Security policies enforce data ownership: `auth.uid() = user_id`
- Refresh tokens handled by Supabase client SDK

## Testing

[How backend code is tested. Example:]

- Integration tests run against a local Supabase instance (`supabase start`)
- Each edge function has a test file in `functions/<name>/test.ts`
- Migrations are tested by running `supabase db reset` + seed data
- CI runs `supabase db push --dry-run` to validate migrations

## Local Development

[Commands to run the backend locally. Example:]

supabase start                  # Start local Supabase (Postgres, Auth, Storage)
supabase functions serve        # Serve edge functions locally
pnpm db:types                   # Regenerate types from schema
pnpm db:migrate                 # Apply pending migrations
supabase db reset               # Reset local DB + reseed

## Deployment

[How the backend is deployed. Example:]

- Supabase CLI pushes migrations: `supabase db push`
- Edge functions deployed via: `supabase functions deploy <name>`
- Environment variables set in Supabase dashboard
- No manual deployments — CI/CD handles it via GitHub Actions
```
