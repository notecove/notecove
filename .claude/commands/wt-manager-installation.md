---
allowed-tools:
  - Edit
  - Read
  - Bash(nc_canary=1 notecove *)
  - Bash(python3 */wt-manager-scripts/setup_tm_project.py)
  - Bash(cp * ~/.claude/commands/)
  - Bash(cp -r * ~/.claude/commands/)
---

# Worktree Manager Skill Installation

Configures the `wt-manager.md` skill for this Notecove instance: creates (or
finds) the TM project, its extra states/types/board columns, and the three
notes the skill reads and writes, then patches `wt-manager.md`'s identifier
table with the result. Also asks a few questions the bootstrap script can't
answer for you (base branch, GitHub repo, your agent identity).

Run this once before first use, or again any time you need to reconfigure —
it's idempotent and will not duplicate anything that already exists.

---

## Steps

### 1. Check CLI

```bash
notecove agent-instructions
```

Confirm the CLI is reachable before proceeding.

### 2. Run the bootstrap script

```bash
python3 wt-manager-scripts/setup_tm_project.py
```

(Run from the same directory as this file.) It creates the `TM` project if
missing, adds the `Waiting for response` / `On Hold` / `Blocked` / `Won't Do`
states and the `apply` / `merge` / `decide` / `message` / `review` types,
drops the default `Feature`/`Bug`/`Chore` types, adds matching board columns,
and creates (or finds) a `Worktree Manager` folder with three notes
(`Worktrees`, `Worktree Manager State`, `Worktree Manager How-To`).

Parse its JSON stdout for `tm_project_id`, `folder_id`, `worktrees_note_id`,
`state_note_id`, `howto_note_id`. If it exits non-zero, show the user the
error and stop — don't retry blindly.

### 3. Ask the three things the script can't infer

Use `AskUserQuestion` (or plain questions if that's unavailable):

- **Base branch** — what your PRs target (default: `main`).
- **GitHub repo** — `owner/name`, only if `gh pr list` can't infer it from
  this directory already (test with `gh repo view --json nameWithOwner` from
  the repo you'll be managing worktrees for; if that resolves, you can leave
  this blank and the scripts will rely on `gh`'s own inference).
- **Manager identity** — what name should appear as this agent's comment
  author on Notecove (so `tm_events.py` can tell its own comments apart from
  everyone else's). A short, stable string like `wt-manager` is fine.

### 4. Patch wt-manager.md

Read `wt-manager.md` (same directory as this file). Replace each placeholder
in its "Fixed identifiers" table with the Edit tool — do not rewrite anything
else:

| Placeholder | Replace with |
| --- | --- |
| `{TM_PROJECT_ID}` | `tm_project_id` from step 2 |
| `{WORKTREES_NOTE_ID}` | `worktrees_note_id` from step 2 |
| `{STATE_NOTE_ID}` | `state_note_id` from step 2 |
| `{HOWTO_NOTE_ID}` | `howto_note_id` from step 2 |
| `{BASE_BRANCH}` | the base branch from step 3 |
| `{GH_REPO}` | the GitHub repo from step 3, or delete the value and leave the cell blank if `gh` infers it on its own |
| `{MANAGER_NAME}` | the manager identity from step 3 |

The scripts in `wt-manager-scripts/` read these same values from environment
variables or CLI args, not from the skill file — if you'll run the background
jobs outside of a Claude Code session (e.g. a plain cron), export
`TM_PROJECT_ID`, `MANAGER_NAME`, `GH_REPO`, `BASE_BRANCH`, `STATE_NOTE_ID`
there too, matching what you just patched into `wt-manager.md`.

### 5. Offer to copy to ~/.claude/commands

Ask the user: "Copy `wt-manager.md`, `wt-manager-installation.md`, and the
`wt-manager-scripts/` directory to `~/.claude/commands/` so the skill is
available globally?"

If yes:
```bash
cp wt-manager.md wt-manager-installation.md ~/.claude/commands/
cp -r wt-manager-scripts ~/.claude/commands/
```
(Run from the same directory as this file.)

If no, skip.

### 6. Report

Tell the user:
- Whether the TM project was created or already existed, and its states/types
- The `Worktree Manager` folder and its three notes (created or found)
- The base branch, GitHub repo (or "inferred by `gh`"), and manager identity recorded
- Confirmation that `wt-manager.md` has been patched
- Whether the skill files were copied to `~/.claude/commands/`
- A reminder to start the background jobs (TM watcher, PR review scan, blocked/waiting sweep) described in `wt-manager.md`'s "Background jobs" section the first time `/wt-manager` runs
