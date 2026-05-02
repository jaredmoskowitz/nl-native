Launch parallel native implementation for the active approved change. This command starts the iOS, Android, and Backend implementation agents simultaneously, each working from the gate-approved specs. iOS and Android agents use mock data layers so they don't block on the backend being ready.

---

## Pre-flight checks

1. Find the active change: look for a directory in `specs/changes/` that has a `gate-review.md` but no `archive/` marker
2. Verify `gate-review.md` exists and contains human approval (look for "approved" confirmation)
3. If no approved change exists, tell the user to run `/propose <feature-name>` first
4. Check that platform AGENTS.md files exist:
   - `platforms/ios/AGENTS.md`
   - `platforms/android/AGENTS.md`
   - `platforms/backend/AGENTS.md`

**If `platforms/backend/AGENTS.md` does not exist:** This is the first feature that needs a backend. Before proceeding, ask the user to configure their backend stack. Walk them through the key decisions:

1. **What backend service?** (Supabase, Firebase, Cloudflare Workers, custom server, etc.)
2. **What language/runtime?** (TypeScript/Deno, TypeScript/Node, Python, Go, etc.)
3. **What database?** (Postgres, Firestore, DynamoDB, SQLite/Turso, etc.)
4. **What auth provider?** (Supabase Auth, Firebase Auth, Clerk, custom JWT, etc.)
5. **Any file storage needs?** (R2, S3, Supabase Storage, etc.)

Use their answers to generate `platforms/backend/AGENTS.md` from the template in `schemas/backend-agents.md`. Then proceed with fan-out.

The same check applies to `platforms/ios/AGENTS.md` and `platforms/android/AGENTS.md` — if missing, ask the user to confirm or customize the defaults from the agent profile before proceeding.

Set `CHANGE=specs/changes/<active-change-name>`.

---

## Read the approved specs

Load the following files into context before spawning any agent:
- `$CHANGE/specs/core/features/*.md` — feature requirements
- `$CHANGE/specs/core/api-contracts/*.md` — API contracts (note versions)
- `$CHANGE/specs/core/data-models/*.md` — data models (note versions)
- `$CHANGE/specs/core/interactions/*.md` — interaction specs
- `$CHANGE/ux-reconciliation.md` — platform-specific behavioral rulings
- `$CHANGE/constraints/ios.md` — iOS constraints (already reconciled)
- `$CHANGE/constraints/android.md` — Android constraints (already reconciled)
- `$CHANGE/constraints/backend.md` — backend constraints (already reconciled, if filed)

---

## Launch iOS Expert

Read `agents/ios-expert.md` and `platforms/ios/AGENTS.md`.

**Step 1 — Write the iOS implementation spec**

Before writing any code, produce `$CHANGE/specs/ios/implementation.md`:
- Map each feature requirement to a specific view, view model, or service
- Define the view hierarchy and navigation flow
- Define data fetching strategy (how API responses map to local models)
- Define the mock API client protocols and fixture data (derived from API contract response shapes)
- Note any platform-specific behaviors from the constraint reconciliation

**Step 2 — Write the iOS task list**

Produce `$CHANGE/tasks/ios-tasks.md` with contract dependencies in frontmatter:

```markdown
---
contract-dependencies:
  api-contracts/<name>: <version>
  data-models/<name>: <version>
---

## Tasks
- [ ] [Task description]
- [ ] [Task description]
```

Tasks must be granular enough to be completed and checked off individually. Each task should take no more than a few hours.

**Step 2b — Define checkpoints**

Group tasks into 2-4 milestones (natural boundaries like "data layer", "primary screen", "secondary screens", "polish"). Mark each milestone in the task list with a checkpoint label:

```markdown
## Tasks
- [ ] Create data models and API client protocol
- [ ] Implement mock API client with fixture data
<!-- checkpoint: ios-data-layer -->
- [ ] Build NoteListView with ViewModel
- [ ] Build NoteDetailView
<!-- checkpoint: ios-primary-screens -->
- [ ] Add pull-to-refresh and loading states
- [ ] Implement swipe-to-delete
- [ ] Write XCTest cases
<!-- checkpoint: ios-complete -->
```

**Step 3 — Implement**

Work through the task list top to bottom. After completing each task, mark it `[x]`.

**When you reach a checkpoint:** Commit all work with a message like `checkpoint: ios-data-layer`. Append an entry to `$CHANGE/checkpoints.md`:

```markdown
## [checkpoint-label]
Platform: iOS
Date: [date]
Tasks completed: [list]
Summary: [1-2 sentences of what was built]
Git ref: [commit hash]
```

Checkpoints enable `/steer` to revert to a known-good state if the user wants to change direction.

Follow `platforms/ios/AGENTS.md` conventions strictly. If you encounter a situation not covered by the spec, note it as an implementation decision in the task comment — do not contact other agents.

**Mock data layer:** Implement all API client protocols with mock conformances using fixture data from the API contract. Views and view models must depend on the protocol, never the concrete implementation. The real backend binding is deferred until backend tasks complete and integration verification runs.

**Contract version monitoring:** At the start of each task, check whether any contract in your `contract-dependencies` has been incremented since you last read it. If so:
1. Stop current task
2. Re-read the updated contract
3. Assess impact on remaining tasks
4. Update `ios-tasks.md` accordingly
5. Resume

---

## Launch Android Expert

Read `agents/android-expert.md` and `platforms/android/AGENTS.md`.

**Step 1 — Write the Android implementation spec**

Before writing any code, produce `$CHANGE/specs/android/implementation.md`:
- Map each feature requirement to a specific composable, view model, repository, or use case
- Define the composable hierarchy and navigation graph
- Define data fetching strategy (how API responses map to local models and Room entities)
- Define the mock API client interfaces and fixture data (derived from API contract response shapes)
- Note any platform-specific behaviors from the constraint reconciliation

**Step 2 — Write the Android task list**

Produce `$CHANGE/tasks/android-tasks.md` with contract dependencies in frontmatter:

```markdown
---
contract-dependencies:
  api-contracts/<name>: <version>
  data-models/<name>: <version>
---

## Tasks
- [ ] [Task description]
- [ ] [Task description]
```

**Step 2b — Define checkpoints**

Same as iOS — group tasks into 2-4 milestones and mark with `<!-- checkpoint: android-[milestone] -->` comments.

**Step 3 — Implement**

Work through the task list top to bottom. After completing each task, mark it `[x]`.

**When you reach a checkpoint:** Commit all work with a message like `checkpoint: android-data-layer`. Append an entry to `$CHANGE/checkpoints.md` (same format as iOS).

Follow `platforms/android/AGENTS.md` conventions strictly. If you encounter a situation not covered by the spec, note it as an implementation decision in the task comment — do not contact other agents.

**Mock data layer:** Implement all API client interfaces with fake implementations using fixture data from the API contract. Views and view models must depend on the interface, never the concrete implementation. The real backend binding is deferred until backend tasks complete and integration verification runs.

**Contract version monitoring:** Same as iOS — halt on contract version change, reassess, resume.

---

## Launch Backend Expert

Read `agents/backend-expert.md` and `platforms/backend/AGENTS.md`.

**Step 1 — Write the backend implementation spec**

Before writing any code, produce `$CHANGE/specs/backend/implementation.md`:
- Map each API contract endpoint to a specific function, route handler, or edge function
- Translate the abstract data model to your service's concrete schema (tables, collections, types)
- Define the authentication and authorization strategy using your service's primitives
- Map each error code in the contract to a detection condition and response
- Note any service-specific behaviors from the constraint reconciliation

**Step 2 — Write the backend task list**

Produce `$CHANGE/tasks/backend-tasks.md` with contract dependencies in frontmatter:

```markdown
---
contract-dependencies:
  api-contracts/<name>: <version>
  data-models/<name>: <version>
---

## Tasks
- [ ] Create database migration for [entity] table
- [ ] Implement [endpoint] function
- [ ] Add access control / RLS policies
- [ ] Write integration tests for [endpoint]
```

Tasks should follow this order: schema first, then endpoints, then auth/access control, then tests.

**Step 2b — Define checkpoints**

Same as iOS and Android — group tasks into 2-4 milestones and mark with `<!-- checkpoint: backend-[milestone] -->` comments. Natural backend milestones: `schema`, `endpoints`, `auth`, `complete`.

**Step 3 — Implement**

Work through the task list top to bottom. After completing each task, mark it `[x]`.

**When you reach a checkpoint:** Commit all work with a message like `checkpoint: backend-schema`. Append an entry to `$CHANGE/checkpoints.md` (same format as iOS and Android).

Follow `platforms/backend/AGENTS.md` conventions strictly. If you encounter a situation not covered by the spec, note it as an implementation decision in the task comment — do not contact other agents.

**Contract version monitoring:** Same as iOS and Android — halt on contract version change, reassess, resume.

---

## If the Architect changes a contract mid-implementation

When a contract version is incremented during fan-out:

1. Identify which platform task lists declare that contract as a dependency
2. Notify those agents to halt their current task
3. Each affected agent re-reads the updated contract, updates their task list, and resumes
4. Log the version change and affected tasks in `$CHANGE/gate-review.md` under a "Mid-flight contract changes" section

---

## Completion

When all three task lists (iOS, Android, Backend) are fully checked off:

1. Summarize what was built on each platform (files created/modified)
2. Note any implementation decisions made autonomously (outside the spec)
3. Note which platform agents are still using mock data layers (if backend completed after platforms, note that mocks can now be swapped for real implementations)
4. Tell the user: "Implementation complete. Run `/verify` to validate."

**Partial completion:** If iOS and Android finish before Backend, those platforms are functional with mock data. Report progress and continue — platform agents do not need to wait for Backend to complete their task lists. The mock→real swap happens during verification.
