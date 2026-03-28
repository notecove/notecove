---
created: 1773597036641
folder: /Inbox
modified: 1773597754515
pinned: false
---
# Drew's Daily Skill

Starts the day by creating a new notecove note with a date heading and compiling a fresh todo list from recent notes, as well as the Regular TODO board.

# Notecove CLI Reference

All note/task access goes through the `notecove` CLI. Key commands:

**List notes in a folder:**
```bash
notecove note list --folder <folder-id> --json
```

**Read a note's content:**
```bash
notecove note show <note-id> --format markdown
```

**Create a new note:**
```bash
notecove note create --folder <folder-id> --content "..." --format markdown --json
```

**Append to an existing note:**
```bash
notecove note edit <note-id> --append "..." --format markdown
```

**Replace a note's content:**
```bash
notecove note edit <note-id> --content "..." --format markdown
```

**List tasks from a project:**
```bash
notecove task list --project <slug-prefix> --json
# e.g. --project TODO, --project NOTE
```

**Filter tasks by state:**
```bash
notecove task list --project TODO --state "In Progress" --json
```

**Show task details (including ID for linking):**
```bash
notecove task show <slug> --json
# .id and .title fields give you what you need for a task link
```

## Notecove Link Syntax

Always use these forms — never plain slug text or `N:` prefix for notes:

- **Tasks:** `[[T:<long-id>|display title]]` — long-id from `notecove task show <slug> --json` → `.id`
- **Notes:** `[[<note-id>|display title]]` — just the bare note ID, no prefix

## Folder IDs

| Folder | ID |
|--------|----|
| Inbox  | `joauGHXCRlCWl90yEucQ7g` |
| Daily  | `xnmkbpc836kv322v3h5gtwznk7` |
| Claude memory | `ppaaekyxd7a293wgep4w09v56m` |

## Projects

| Project | Slug prefix | Purpose |
|---------|-------------|---------|
| Regular TODO | `TODO` | Day-to-day personal tasks |
| Pre-release Notecove | `NOTE` | Notecove product work |
| Notecove Backlog | `NB` | Notecove backlog |
| Claude | `CLAU` | Claude-related tasks |

# Note Location

Daily notes live in the **Daily** folder (`xnmkbpc836kv322v3h5gtwznk7`). One note per day, titled with the full date, e.g. `Sunday 15th March 2026`.

# Steps

## 1. Back up the SD

```bash
bash ~/daily/backup-notecove.sh
```

If it exits non-zero, note it in the Daily Brief ("⚠️ SD backup failed") but don't block the rest of the daily on it.

## 2. Find or create today's note

Check whether a note for today already exists in the Daily folder:

```bash
notecove note list --folder xnmkbpc836kv322v3h5gtwznk7 --json | jq '[.[] | {id, title, modified}]'
```

- If a note titled with today's date exists, use it (note the ID).
- If not, create a new one — the content will be written in step 9.

## 3. Read Claude memory notes

List and read all notes in the Claude memory folder (`ppaaekyxd7a293wgep4w09v56m`):

```bash
notecove note list --folder ppaaekyxd7a293wgep4w09v56m --json
```

Read each note's content. These notes contain observations about Drew's patterns, tendencies, and context that aren't derivable from tasks or recent daily notes — things like energy patterns, what kinds of tasks tend to get stuck, what framing works, what doesn't. Use them to inform:
- The tone and emphasis of the Daily Brief
- Which items to surface in the top-3
- How to frame first steps (e.g. if a pattern says "big tasks don't happen, small ones do")
- The coaching **Note:** section

These notes are yours to maintain. At the end of each daily run (step 11), update or create notes here based on what you observed while building today's brief. Good candidates: patterns in what's been stuck, observations about energy or mood across recent days, meta-observations about what's working or not in the daily format itself.

## 4. Read recent entries

List notes in the Daily folder sorted by modified date, then read the 2-3 most recent ones:

```bash
notecove note show <note-id> --format markdown
```

Look for:
- Outstanding unchecked `- [ ]` todos — carry forward to today
- `- [-]` items (won't do) — **do not carry forward**; note any reason given below the item as context
- Linked notecove tasks — **verify the state of every task link found**; only carry forward tasks that are NOT in a terminal state (Done, Cancelled, Rejected, Won't Do, or similar). Do not surface completed tasks.
- Implicit action items: phrases like "need to", "should", "will", "follow up", "action item"
- Context from recent work relevant to today
- Any `## Health` observations — scan across recent days for patterns (energy, focus, mood, sleep, symptoms) and surface anything worth noting in today's Daily Brief

Also scan recent notes in the Inbox folder (`joauGHXCRlCWl90yEucQ7g`) for relevant context.

## 5. Read today's calendar events

Query the "Email Alerts" Apple Calendar for events happening today:

```bash
osascript <<'EOF'
tell application "Calendar"
  set theCalendar to calendar "Email Alerts"
  set startOfDay to current date
  set hours of startOfDay to 0
  set minutes of startOfDay to 0
  set seconds of startOfDay to 0
  set endOfDay to startOfDay + 86399
  set theEvents to (every event of theCalendar whose start date >= startOfDay and start date <= endOfDay)
  set output to {}
  repeat with e in theEvents
    set end of output to (summary of e) & "|" & ((start date of e) as string) & "|" & (description of e)
  end repeat
  return output
end tell
EOF
```

Include a `## Schedule` section in today's note listing each event with its time and description. If an event has a description referencing notecove tasks or notes, surface those links inline. If there are no events, omit the section entirely.

## 6. Check weather

Fetch today's forecast for Glen Cove, NY:

```bash
curl -s "wttr.in/Glen+Cove,NY?format=j1" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['weather'][0]['maxtempF'])"
```

If the forecasted high is **over 45°F**, include this as a standalone H1 in the note, placed right after the date heading and cruise countdown line:

```markdown
# You Should Walk During Lunch
```

If the high is 45°F or below, omit it entirely.

## 7. Check PR status

Run these `gh` commands to get current PR state:

```bash
# PRs needing your review
gh search prs --review-requested=@me --state=open --json number,title,repository,updatedAt,url

# Your open PRs
gh search prs --author=@me --state=open --json number,title,repository,updatedAt,url
```

If `gh` is unavailable or returns an error, skip this step and omit the `## PR Status` block from the output.

## 9. Read active tasks

Pull active tasks from the Regular TODO project and the NM (marketing/content) project:

```bash
notecove task list --project TODO --json
notecove task list --project NM --json
```

Note any tasks that are not in a terminal state (done/cancelled). These feed into the micro-action list in step 11.

**NM column ordering:** For NM tasks, kanban column order is determined by `listPosition` sorted descending (higher = top of column). When picking the 2–3 NM tasks to surface in the action list, take from the top of the `To Do` column — i.e. the NM To Do tasks with the highest `listPosition` values.

## 10. Generate the Daily Brief

Before writing the note, compose a short daily brief. This is a personal coaching note to help set the tone and priorities for the day.

**What to include:**

- **Focus** — Call out 1–2 things that matter most today. Don't just name them — identify the *first concrete step* and make the entry point obvious. Reference items from the micro-action list below.
- **Note:** — One short coaching observation based on recent patterns and the Claude memory notes. Look for: things that keep not happening (name the hidden first step), patterns in energy or mood, something going well worth naming, or a reframe if there's been friction. 2–4 sentences max.

## 11. Compile the action list

The goal is an ordered list of up to 10 things that could each be done in a single sitting (30–90 min). **Pick one and do it** — not a todo list to complete, a menu to choose from.

**Medical** is always its own mandatory section — include everything non-terminal regardless of count.

**For the remaining 10 items:**

- **Decompose big tasks.** Read the full task body (`notecove task show <slug> --format markdown`). If a task is clearly multiple things, don't list it — list its smallest atomic action instead. Add a note: `*(this task is actually 3 things — consider splitting)*` if it would help.
- **NM (marketing/content) tasks:** cap at 2–3 max, only the ones with a clear immediate action. Don't surface the whole backlog.
- **Order by:** urgency + staleness + how small/completable the action is. Smaller and more actionable ranks higher — the point is to pick something and do it, not to list everything important.
- **Only non-terminal tasks** — verify state with `notecove task show <slug> --format markdown | grep "^State:"` before including.

**Format each item as a numbered entry** so the "pick one" framing is explicit:

```
### Today's 10 — pick one

1. [[T:<id>|Short action description]]
   *First step: open X and do Y*

2. - [ ] Plain todo action
   *First step: ...*
```

**Task links vs plain todos:**
- Notecove task → bare task link `[[T:<task-id>|action description]]`, get `id` from `notecove task show <slug> --json`
- No task → plain checkbox `- [ ] action`

**Spacing:** blank line between items so trailing `>` blockquotes close properly.

**AI prompts:** add an indented prompt suggestion where Claude could help:
```
1. [[T:abc123|Draft release notes]]
   > Prompt: "Draft release notes for 0.3.9. Tone: concise, user-focused."
```

## 12. Write today's note

If the note was just created, write the full content. If it already existed and already has today's heading, skip (report what's there). Use this structure:

```markdown
# Sunday 15th March 2026

## Daily Brief

**Today's focus:**
- [Priority 1 — first concrete step: ...]
- [Priority 2 — first concrete step: ...]

**Note:**
[Coaching observation — pattern, nudge, or reframe. 2–4 sentences.]

---

## Schedule  *(omit if no events today)*

- **9:00 AM** — [event]

---

## PR Status  *(omit if none)*

**Needs your review:**
- [ ] Review [owner/repo#number](url): title _(N days ago)_

**Your open PRs:**
- [owner/repo#number](url): title _(N days ago)_

---

## Health

**Observations:**
-

---

### Medical

[[T:<id>|Task title]]
- [ ] Plain medical todo

---

### Today's 10 — pick one

1. [[T:<id>|Atomic action — what specifically to do]]
   *First step: ...*

2. - [ ] Plain action with no task
   *First step: ...*

3. [[T:<id>|Another action]]
   *(this task is actually 3 things — consider splitting)*

---

## Drew's Notes

**How are you feeling today?**

*(space for a personal check-in — energy, mood, anything on your mind)*

---
```

Notes on structure:
- `## Drew's Notes` goes **at the end** — it's a diary section
- `### Medical` always present, all active medical items, mandatory
- `### Today's 10 — pick one` — ordered by value + actionability, max 10 items, each atomic
- Big tasks decomposed to their smallest action; NM tasks capped at 2–3
- `## PR Status` omitted if no open PRs
- `## Schedule` omitted if no calendar events

To write the note:
- **New note:** use `--content-file` with the full markdown when creating
- **Existing empty note:** use `notecove note edit <id> --content-file <path> --format markdown`

After writing, pin today's note and unpin the previous day's note:

```bash
notecove note pin <today-note-id>
notecove note unpin <previous-note-id>
```

The previous note ID comes from the list fetched in step 2 — it's the most recently modified daily note that isn't today's. If today's note already existed (not newly created), still pin/unpin as above. Only unpin notes that are actually pinned (check the `pinned` field in the list output).

## 13. Update Claude memory notes

After writing today's note, update the Claude memory folder (`ppaaekyxd7a293wgep4w09v56m`) with anything you observed while building the brief. You don't need to do this exhaustively — just capture what felt notable or what you'd want to remember next time.

Good things to record or update:
- **Patterns in stuck tasks** — what keeps not getting done and why (e.g. "tasks without a named first step don't happen")
- **Energy / mood patterns** — what recent daily notes reveal about Drew's energy, rhythm, or motivation
- **What's working** — if a framing or format seemed right, note it so future runs can lean into it
- **Meta-observations** — anything about how Drew thinks, what tends to motivate or drain him, what kinds of prompts actually get used

Each topic should be its own note in the folder (e.g. "Patterns — stuck tasks", "Job search context", "Energy observations"). Create new notes for new topics; update existing notes rather than duplicating.

Write via heredoc stdin:
```bash
notecove note create --folder ppaaekyxd7a293wgep4w09v56m --content-file - --format markdown --json << 'EOF'
# [Topic]
...
EOF
```

Or update an existing note:
```bash
notecove note edit <id> --content-file - --format markdown << 'EOF'
# [Topic]
...updated content...
EOF
```

## 14. Report to the user

After writing the note, briefly tell the user:

- The note ID and how to open it (`notecove open <id>`)
- The 3 items selected and why
- Any memory notes created or updated

## Notes

- Keep the TODO list clean and actionable
- Don't duplicate items that already exist in the most recent entries
- If there's already a heading for today's date, don't create a duplicate — just report what TODOs exist
- The `↩` marker is reserved for the weekly review skill — don't use it here
- Date headings use the format `# Monday 2nd February 2026` — always use `#` heading level
