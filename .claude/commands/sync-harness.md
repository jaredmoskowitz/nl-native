Sync nl-native harness changes from this project to the upstream repo. Use when any harness-related file is modified — agent profiles, schemas, pipeline skills, or CLAUDE.md command definitions.

**Trigger:** Any edit to files in `agents/`, `schemas/`, or `.claude/commands/` that defines pipeline behavior (not app-specific code). Also trigger when the user mentions "nl-native", "harness", or "pipeline" in the context of improvements.

The nl-native harness lives at `/Users/jaredmoskowitz/workspace/nl-native` and is the open-source upstream. This project (Sweep) is a downstream consumer that also drives harness development. Changes flow both ways, but harness improvements made here must be pushed upstream so other projects benefit.

---

## What belongs in nl-native (upstream)

- **Agent profiles** (`agents/*.md`) — spec-analyst, architect, ux-designer, visual-designer, ios-expert, android-expert, backend-expert, qa-verifier
- **Schema templates** (`schemas/*.md`) — feature-spec, api-contract, data-model, interaction-spec, design-system, platform-constraint, backend-agents
- **Pipeline skills** (`.claude/commands/*.md`) — propose, fan-out, verify, steer, connect, mirror, preview, adopt, archive, status
- **Harness README and documentation**

## What stays in Sweep only (downstream)

- **Platform code** (`platforms/`)
- **Specs for specific features** (`specs/changes/`)
- **Platform AGENTS.md files** (`platforms/ios/AGENTS.md`, `platforms/android/AGENTS.md`) — these are project-specific
- **App-specific CLAUDE.md content**
- **OAuth credentials, build configs, entitlements**

---

## Process

### Step 1 — Identify harness changes

Check which modified files are harness-related:

```bash
git diff --name-only HEAD~1 | grep -E '^(agents/|schemas/|\.claude/commands/)'
```

Or check the current working tree:

```bash
git diff --name-only | grep -E '^(agents/|schemas/|\.claude/commands/)'
```

### Step 2 — Diff against upstream

For each harness file that changed, compare with the nl-native version:

```bash
diff <file-in-sweep> /Users/jaredmoskowitz/workspace/nl-native/<same-path>
```

If the file doesn't exist upstream, it's a new addition. If it differs, check whether Sweep's version is newer (has improvements) or whether upstream has diverged independently.

### Step 3 — Copy and commit

Copy changed files to nl-native:

```bash
cp <file> /Users/jaredmoskowitz/workspace/nl-native/<same-path>
```

Commit with a clear message explaining what changed and why:

```bash
cd /Users/jaredmoskowitz/workspace/nl-native
git add <files>
git commit -m "<description of harness improvement>"
git push origin main
```

### Step 4 — Verify parity

After syncing, confirm both repos have the same harness files:

```bash
diff <(ls agents/) <(ls /Users/jaredmoskowitz/workspace/nl-native/agents/)
diff <(ls schemas/) <(ls /Users/jaredmoskowitz/workspace/nl-native/schemas/)
diff <(ls .claude/commands/) <(ls /Users/jaredmoskowitz/workspace/nl-native/.claude/commands/)
```

---

## When invoked proactively

When a harness file is modified in Sweep, output:

```
Harness sync: [file]
Change: [one-line description]
Action: SYNC to nl-native / SKIP (app-specific)
```

If SYNC, proceed with Steps 2-4. If multiple files changed, batch them into a single upstream commit.
