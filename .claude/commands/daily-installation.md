---
allowed-tools:
  - Edit
  - Read
  - Bash(nc_canary=1 notecove folder *)
  - Bash(nc_canary=1 notecove project *)
  - Bash(nc_canary=1 notecove note list *)
  - Bash(ls ~/daily/backup-notecove.sh)
---

# Daily Skill Installation

Configures the `daily.md` skill for this Notecove instance by discovering or creating the required folders, verifying required projects exist, and patching `daily.md` with the correct IDs.

Run this once before first use, or again any time you need to reconfigure.

---

## Steps

### 1. Check CLI

```bash
notecove agent-instructions
```

Confirm the CLI is reachable before proceeding.

### 2. Discover folders

```bash
notecove folder list --json
```

Look for folders with these exact names (case-sensitive). Record each `id`:

| Folder | Expected name |
|--------|---------------|
| Daily  | `Daily` |
| Inbox  | `Inbox` |
| Claude memory | `Claude memory` |

### 3. Create missing folders

For any folder not found, create it at the root level and record the returned `id`:

```bash
notecove folder create "Daily" --json
notecove folder create "Inbox" --json
notecove folder create "Claude memory" --json
```

### 4. Verify projects

```bash
notecove project list --json
```

Confirm these projects exist by `slugPrefix`. Projects cannot be created via CLI — if any are missing, tell the user and stop.

| Project | `slugPrefix` | Purpose |
|---------|-------------|---------|
| Regular TODO | `TODO` | Day-to-day personal tasks |
| Pre-release Notecove | `NOTE` | Notecove product work |
| Notecove Backlog | `NB` | Notecove backlog |
| Claude | `CLAU` | Claude-related tasks |
| Marketing/content | `NM` | NM tasks |

### 5. Check backup script

```bash
ls ~/daily/backup-notecove.sh
```

If missing: warn "⚠️  ~/daily/backup-notecove.sh not found — Step 1 of the daily skill will fail. Create or symlink it before running /daily."

### 6. Patch daily.md

Read the `daily.md` skill file (same directory as this file). Update the Folder IDs table with the IDs discovered or created above. Use the Edit tool to replace each ID cell precisely — do not rewrite surrounding content.

### 7. Report

Tell the user:
- Which folders were found vs created (with IDs)
- Which projects were found vs missing
- Whether the backup script exists
- Confirmation that `daily.md` has been patched (or that no changes were needed because IDs already matched)
