---
allowed-tools:
  - Edit
  - Read
  - Bash(nc_canary=1 notecove folder *)
  - Bash(nc_canary=1 notecove project *)
---

# Feature-NC Skill Installation

Configures the `feature-nc.md` skill for this Notecove instance by verifying or creating the required projects and patching `feature-nc.md` with the correct slug prefixes.

Run this once before first use, or again to reconfigure for a different project setup.

---

## Steps

### 1. Check CLI

```bash
notecove agent-instructions
```

Confirm the CLI is reachable before proceeding.

### 2. List projects

```bash
notecove project list --json
```

The skill uses two projects:

| Role | Default `slugPrefix` | Description |
|------|---------------------|-------------|
| **Ticket source** | `NOTE` | Where feature tickets live (read-only; you show tasks from here) |
| **Implementation tasks** | `CLAU` | Where the skill creates plan tasks during a session |

### 3. Resolve ticket-source project

Find the project that contains feature/engineering tickets. If `NOTE` exists, use it. If not:
- List the available projects and ask the user: "Which project contains the feature tickets the skill should read? (default: NOTE)"
- Record the confirmed slug prefix as `{ticketProject}`.

### 4. Resolve implementation-task project

Find or create the project where the skill will create plan tasks.

- If `CLAU` exists, use it.
- If not, ask the user: "Should I create a new project for implementation tasks, or use an existing one? (I'll create 'Claude' with slug CLAU by default.)"
  - If creating: `notecove project create "Claude" --json` — record the returned `slugPrefix` as `{claudeProject}`.
  - If using an existing one: record the user-provided `slugPrefix` as `{claudeProject}`.

### 5. Check Claude parent folder

```bash
notecove folder list --json
```

Look for a folder named `Claude` at the root level. This is where the skill creates per-feature subfolders. If it doesn't exist, note that it will be created automatically on first `/feature-nc` run (the skill handles this itself — no action needed here).

### 6. Patch feature-nc.md

Read `feature-nc.md` (same directory as this file).

If `{ticketProject}` differs from `NOTE` or `{claudeProject}` differs from `CLAU`, use the Edit tool to replace all occurrences throughout the file:
- `--project NOTE` → `--project {ticketProject}`
- `--project CLAU` → `--project {claudeProject}`

Do not change any other content.

If both match the defaults, no edit is needed — report that the file is already configured correctly.

### 7. Report

Tell the user:
- Ticket-source project: slug prefix + name
- Implementation-task project: slug prefix + name (note if created)
- Claude parent folder: exists or will be auto-created on first run
- Whether `feature-nc.md` was patched or was already correct
