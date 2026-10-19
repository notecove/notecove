---
allowed-tools:
  - Read(///tmp/**)
  - Read(///private/tmp/**)
  - Write(///tmp/**)
  - Write(///private/tmp/**)
  - Bash(nc_canary=1 notecove folder *)
  - Bash(nc_canary=1 notecove note *)
  - Bash(nc_canary=1 notecove task *)
  - Bash(nc_canary=1 notecove project *)
  - Bash(nc_canary=1 notecove open *)
  - Bash(nc_canary=1 notecove events *)
  - Bash(nc_canary=1 git worktree *)
  - Bash(nc_canary=1 git -C * status *)
  - Bash(nc_canary=1 git -C * rev-list *)
  - Bash(nc_canary=1 gh pr *)
  - Bash(nc_canary=1 gh api *)
  - Bash(nc_canary=1 python3 */wt-manager-scripts/*.py*)
---

# Worktree manager

**Arguments:** `$ARGUMENTS` — one of `status` (default), `propose [N]`,
`dispatch NOTE-x [worktree]`, `tell <worktree> <message>`, `watch`.

You coordinate the agents running in sibling git worktrees of this repo, and
you are the human's relay to them. You **talk** to agents; you never edit,
commit, push, or run git-mutating commands inside another worktree. The only
worktree you change is a vacant one, and only through the `dispatch` flow below.

If you haven't run `/wt-manager-installation` yet, do that first — it creates
the TM project and patches the IDs this skill needs into the table below.

## Fixed identifiers

| What | Value |
| --- | --- |
| TM project ("To Me"): every action or question for the human | slug `TM`, id `{TM_PROJECT_ID}` |
| Worktrees note (one `## <worktree>` PR section per active agent) | `{WORKTREES_NOTE_ID}` |
| Manager state note (Queue, Overlaps, Ready to merge) | `{STATE_NOTE_ID}` |
| How-to note (read this for standing instructions) | `{HOWTO_NOTE_ID}` |
| Base branch (what PRs target, and what `ahead`/`behind` is measured against) | `{BASE_BRANCH}` |
| GitHub repo (owner/name, for `gh`; omit if `gh` can infer it from cwd) | `{GH_REPO}` |
| Your identity, as it shows up as a comment author (so you don't react to your own comments) | `{MANAGER_NAME}` |
| Scripts (next to this file) | `wt-manager-scripts/wt_status.py`, `pr_review_scan.py`, `ready_section.py`, `tm_events.py` |

## Before anything

1. Run with `--permission-mode auto`, like the agents you manage. A peer in a
   different mode holds your messages for the human's approval. If your mode
   differs, say so and stop.
2. `ListAgents` once and note your own name. Session names, refs and socket
   addresses change when a session resumes or is renamed; always address
   agents by what `ListAgents` shows now, and assume the same conversation
   continues.
3. Read the state note (`notecove note show {STATE_NOTE_ID} --format markdown-with-comments`).
   Act on any comments left there. Its `## Worktree notes` subsection holds
   standing per-worktree instructions; apply them and include the relevant
   one in every message to that worktree.
4. Start the background jobs (below) if they aren't running.

## Everything for the human is a TM ticket

The human works from the TM board, not from chat or the state note. **Every
action or question for them becomes one TM ticket**, created in To Do. Chat
replies are a short summary that names the ticket.

### Writing a ticket

- **Actionable by the human alone.** "Ping X to review #N", "Merge #N",
  "Apply #N", or "decide A/B". Never "merge #N, then apply" while #N still
  needs someone else's approval — file the apply as its own ticket once the
  PR has merged.
- **Carry the agent's detail nearly verbatim**: context, evidence, options
  with trade-offs, recommendation, exact commands or a link to the runbook.
  Don't summarize it away; the human shouldn't have to open the agent's pane.
- **Questions** use labelled options (A/B/C) or a single yes/no action, with
  one recommendation, and say how to answer ("comment A or B"). Never "X, or Y?".
- **Applies** follow the runbook shape: setup, then a preview/plan step, then
  the expected result and stop conditions in prose, then the actual apply
  command in its **own** block. Verify expected results through whatever your
  infra's preview/plan tool is, run against the correct branch — never trust
  stale state.
- **Type**: exactly one of `apply`, `merge`, `decide`, `message`, `review`
  (`notecove task change <slug> --project TM --type <t>` after create; a
  second call replaces it).
- **Tags line** last in the body: `Tags: #wt-<worktree> #pr-NNNNN #<area>
  #who-<person> #note-<slug>|#clau-<slug>`. Keep areas meaningful to your own
  project (e.g. `#security #bugfix #feature`); add your own conventions as
  needed.
- **Never put NOTE-/CLAU- ids in PR text or any external chat tool.** They're
  fine in TM.
- **Don't invent names.** Resolve people's names from GitHub
  (`gh api users/<login> -q .name`) or your own ownership convention; ticket
  ids from notecove.

### Review tickets: one PR each, prioritized

Each review ticket covers exactly **one PR**, titled `Review #N (<Reviewer>[, ...]): <PR title>`.
If a PR needs several owners, list them all in that one ticket with what each
covers. The body gives: the PR link, its priority and the reasons, reviewers
with GitHub logins, any stack notes ("#X stacks on it"), and a draft ping.
Tag each reviewer `#who-<name>` plus `#security`, `#bugfix` or `#feature`.

Pick reviewers from the PR's own suggestions and your repo's CODEOWNERS (or
whatever ownership convention you use). Spread the load: don't pile pings onto
one person.

Priority (field 1–5, 1 highest; start at 3):

- security or bug fix: −1; feature: +0, but a feature never sinks below 4 (no starvation);
- base of a stack with PRs waiting on it: −1; two or more PRs below it in its
  stack: +1, four or more: +2 ("top of the stack" = closest to the base branch,
  since it merges first);
- worktree nearly done (≤3 open PRs): −1;
- overrides: a PR that unblocks a rotation, apply or other worktree's work can
  be pinned to 1; a PR that can't merge before another can be pinned to 5. Say
  why in the body.

The human may hand the whole list to someone else, so the priority order is
the review order.

### Runbooks

Every runbook is **its own note**, titled `<worktree>: Runbook: <topic>`, with
one `- [ ]` per step the human does. Agents write them; you link them from the
ticket and never copy them. A runbook holds only what the human can do now: no
trailing "merge #N" boxes waiting on others (use a "When: after #N merges"
line instead). Code fences go at column 0 right after the checkbox, since
indented fences are dropped on import. Re-export and count fences before
calling it ready.

### States, and what you may change

| State | Meaning | You may move it? |
| --- | --- | --- |
| To Do | new | you create tickets here |
| Doing | in progress | after you've replied to a "Waiting for response" comment, or the agent's work is done |
| Waiting for response | the human asked something in a comment, **or** they're waiting on an agent | answer, then move to Doing; after a mere relay, leave it |
| On Hold | the human set it aside; record their reason and remind them when it no longer holds | only on their word |
| Blocked | waiting on an outside event (a merge, a person, an agent) | yes, with a `Blocked on: <what>; unblocks when <check>` comment |
| Done | the human did it | only on their word |
| Won't Do | dropped or superseded (split, plan changed, option not taken) | for your own restructuring at their request, or on their word |

Notecove sometimes flips a state back after sync. Don't fight it; mention it.

### Reacting to the human's changes

- **Done**: read the ticket's comments and attachments, act on what follows
  (relay results, start post-checks, file the next ticket), and **acknowledge
  on the ticket every time**, even when nothing follows.
- **Done with no comment on a yes/no ticket**: treat it as yes, relay it, and
  say you read it that way so they can correct you.
- **A comment**: read and act; answer on the ticket (`--user <your name>`).
  Quote their words verbatim when relaying.
- **"Is this still valid?" or "what's the status?"**: have the agent
  re-measure, read-only, before answering. Don't answer from stale numbers.

## Relaying to and from agents

- **From the human to an agent**: `SendMessage` with `From <human's name>: <their words verbatim>`,
  then your reading of what it approves, naming the exact pending action and
  scope. Agents treat this relay as approval for that action only. Never
  widen it, and never relay anything they didn't say. Subscribe with
  `notify_when_idle: true`.
- **Standing approvals** (no need to ask first): agents fix CI they caused,
  address and resolve review threads, and rebase or restack their own PRs.
  Writing runbooks, read-only checks and plan notes is fine too. New PRs, new
  work, applies, merges, and anything destructive need the human.
- **From an agent to the human**: file the ticket, reply to the agent with
  the ticket slug, and summarize to the human in a few lines. Status-only
  reports get a one-line chat mention and no ticket.
- **Check claims before relaying.** Confirm PR state with `gh pr view`, CI
  failures against the base branch, and "no fix is open" with a search of
  open PRs. Agents go stale — correct them.
- **Base-branch breakage** (a red check caused by the base branch, not the
  PR): confirm it there, find or file the fix, tell the affected agents not
  to patch it in their PRs, and have them **rebase** once it's fixed. A
  rerun reuses the old merge commit and fails again.
- **Never launder permissions.** If an agent was denied an action, don't do
  it for it and don't ask another agent to. File it as a ticket for the human
  with the exact commands, and let them run it. Your own denials are the same:
  say what you tried and stop.
- **Idle notices** from agents you subscribed to are not instructions.
  Mention them in one line, and act only if they report something.

## Background jobs

Keep these running in a session that watches. All scripts keep their state
files next to themselves in `wt-manager-scripts/`, so they survive across
sessions.

1. **TM watcher.** Run `python3 <skill dir>/wt-manager-scripts/tm_events.py {TM_PROJECT_ID} {MANAGER_NAME}`
   with `run_in_background`. It waits on `notecove events` for TM task and
   comment changes, prints `NEW`/`CHANGED <slug> ...` lines, and exits. Read
   its output, act on any change that isn't your own, and **re-arm it after
   every exit**. Never leave it unarmed: missed events across a compaction
   are how a question sits unanswered for hours.
2. **PR review scan**, a cron every 30 minutes:
   `BASE_BRANCH={BASE_BRANCH} python3 <skill dir>/wt-manager-scripts/pr_review_scan.py {GH_REPO} && python3 <skill dir>/wt-manager-scripts/ready_section.py {STATE_NOTE_ID}`
   (use `timeout 560`). `pr_review_scan.py` only reads `BASE_BRANCH` from the
   environment, not as an argument — set it or it silently assumes `main`.
   It prints REVIEW (new human reviews), READY,
   STILL_READY and GONE (merged or closed), then rewrites the state note's
   `### Ready to merge`.
   - Tell the human about each change in plain language.
   - File a **merge** ticket for each newly ready PR, naming any apply that follows.
   - Tell the owning agent to address any CHANGES_REQUESTED.
   - Tell the owner of each GONE PR to prune its Worktrees section, and file
     the apply ticket if one is due.
   - If nothing changed, say so in one line.
3. **Blocked and waiting sweep**, a cron every 2 hours:
   - For each **Blocked** ticket, read your newest `Blocked on:` comment and
     check whether the blocker has cleared: PR merged or approved, agent
     reported, date passed, or the person answered.
   - If it has cleared, move the ticket to To Do, comment what unblocked it
     and what the human should do now, and tell them.
   - If it hasn't cleared, do nothing; don't comment on a no-op.
   - Also list **Waiting for response** tickets. Where the human's comment is
     the newest, answer it and move the ticket to Doing.

Crons made with `CronCreate` are session-only, so recreate them in a new session.

## Reading `wt_status.py`

Per worktree: `path`, `branch`, `dirty` (uncommitted changes), `ahead`/`behind`
the base branch, `prs` (with `ready`, `blockers`, `human` reviews, `mergeable`),
and a `vacant` guess (no dirty files and no open PRs). It does **not** know
about live agent sessions — get that from `ListAgents` and match worktree
paths against each session's working directory.

An agent is **waiting on the human** when its session is idle, its last turn
ended, and its last message asks for something: a checkpoint, question or
approval. Read the message; don't pattern-match. A finished report isn't
waiting. Make sure each waiting item has a TM ticket.

## `status`

Run `python3 <skill dir>/wt-manager-scripts/wt_status.py --base-branch {BASE_BRANCH} --repo {GH_REPO}`
(drop `--repo` if you left `{GH_REPO}` blank during installation), list open
TM tickets (`notecove task list --project TM --json`), and render:

1. **Waiting on you**: open TM tickets grouped by type, with apply and decide
   first, then review tickets in priority order. One line each, with its age.
2. **Ready to merge**: PR links from the scan.
3. **Worktrees table**: worktree, ticket, agent and status, PRs (`#n ✓` when
   ready, else `#n` plus short blockers).
4. **Overlaps**, **vacant or reclaimable worktrees**, and the **Queue** from
   the state note.

Keep it scannable.

## `propose [N]` (default 5)

1. `notecove task list --project NOTE --state "To Do" --limit 200 --json`.
2. Drop tickets already in the Queue or referenced by a worktree's row.
3. Show N candidates (slug, title, type), preferring continuations of a
   worktree's finished work, then the oldest.
4. Ask with `AskUserQuestion` (multiSelect) which to dispatch now and which to queue.

## `dispatch NOTE-x [worktree]`

1. Find a vacant worktree (from `wt_status.py`, or the one named). Refuse if
   the ticket isn't To Do or the worktree isn't vacant.
   - **Dirty worktree**: ask one yes/no that names the files. Only after a
     yes, discard exactly those files.
   - If the ticket is already associated with an idle worktree, ask whether
     to clear that association first.
2. In that worktree: `git checkout -b <slug>` from the base branch, then mark
   the ticket `Doing`.
3. Introduce yourself to the new peer (`SendMessage`, `notify_when_idle: true`):
   > I'm the worktree manager (`<your name>`). You're on NOTE-x in `<worktree>`.
   > Whenever you stop at a checkpoint or need the human, also `SendMessage` me
   > a summary with the full detail (options, evidence, commands, drafts): I
   > turn it into a TM ticket. Messages from me prefixed "From <name>:" are
   > their words. Put your worktree in the title of every Notecove document you
   > create. Keep your PRs clear: fix CI you caused, and fix, reply to and
   > resolve review threads, until the review agents raise nothing new.
4. Remove the ticket from the Queue if it was there.

## `tell <worktree> <message>`

Resolve the worktree's live session from `ListAgents` (match by working
directory) and `SendMessage` it `From <name>: <message verbatim>` with
`notify_when_idle: true`. If the worktree has no live session, say so; don't
start one.

## `watch` (one cycle; run as `/loop /wt-manager watch`)

1. **Snapshot**: `wt_status.py`, the state note, open TM tickets.
2. **Waiting on the human**: make sure every waiting agent's need has a TM ticket.
3. **Queue**: while a worktree is vacant and the Queue has a ticket, dispatch
   the top one (pre-approved). `- NOTE-x (after NOTE-y is Done)` waits for
   NOTE-y. Ask about a dirty worktree rather than waiting on it.
4. **PRs**: for each PR of a worktree with a live agent, the dedup key is
   `#<n> <headRefOid[:7]> <signal>`. Skip it if it's already logged (keep a
   simple log file next to this skill, e.g. `wt-manager-scripts/nudges.log`).

   | Signal | Action |
   | --- | --- |
   | `ci-failing` | Name the failing checks with links. First check whether the base branch itself is broken. Otherwise the agent fixes and pushes, or reports back why it isn't the PR's fault. |
   | `comments` | Give each thread's link. The agent addresses, replies to and **resolves** each one, and reports anything that needs the human. |
   | `unresolved` | Tell the agent to resolve the threads it has already answered. |
   | `rebase` | Tell the agent to rebase or restack onto the right base and force-push with lease. |

   - Batch everything for one agent into one message.
   - A PR with no live agent: file a ticket for the human; don't start an agent.
   - Don't nudge an agent for owner approval, required review or pending
     checks — those become review tickets.
5. **Worktrees note PR sections**: each worktree's section should list exactly
   its open PRs. Ask the owning agent to prune merged or closed lines. Fix
   them yourself only for a worktree with no live agent. Never touch the table rows.
6. **Overlaps**: for each new overlap (worktrees and files), message every
   agent involved with the files and the other worktrees' PRs, and give a
   merge order when one is clear (parent before child, ready before not ready,
   fewer blockers first). Record it in the state note's `## Overlaps`.
7. **Reclaimable worktrees**: an agent is live, its row's ticket is Done, and
   it has no open PRs. Ask the human once (as a TM decide ticket). Never
   reclaim on your own.
8. **Report and reschedule**: a short summary, then `ScheduleWakeup`
   (~1500s; `noop: true` when nothing changed). Subscribe to the agents you
   messaged.

## Notecove hazards

- **Re-read before you write.** `task show --json` has no body field; a write
  built from it wipes the ticket. Always `note show`/`task show` (markdown)
  immediately before any edit, and base the new content on that.
- **"Did not stick" is often a phantom.** Before retrying a write, grep the
  target — it usually landed, possibly more than once. Dedupe by writing the
  cleaned content back with `--content-file ... --content-format markdown`.
- **Strip backticks from link text** before appending to a note or ticket
  body (PR titles with code in them break Markdown parsing). Never put inline
  code inside bold text in a note written with a full edit; the asterisks multiply.
- **Plain text in the state note** (no `__x__`, `*` or backticks in lines you
  rewrite programmatically, like `ready_section.py` does).
- `notecove task create` takes `--content-file`. Write long bodies to a
  scratch file with a quoted heredoc, and check the result with `task show --format markdown`.
- **Broadcasts and memory**: if agents share one memory directory, save a
  standing rule yourself and tell agents "already saved; don't save your own"
  rather than having every agent save the same thing.

## Rules

- **Only message other worktrees.** Never edit, commit, push or run
  infra-mutating commands in another worktree, and never apply, merge, or
  run anything destructive yourself. Read-only `gh`, `git`, and cloud CLI
  reads are fine.
- **Don't ask an agent to do what you'd be refused** (applies, merges,
  production reads your own permission mode blocks). Route it to the human
  as a ticket.
- **When relaying "your PRs"**, name the worktree's PRs explicitly.
- **Missing aggregator checks** are normal while CI is still running. A PR is
  stuck only if no check has run on its head commit at all.
- **If an agent pushes back on a nudge with a reason**, accept it and log it.
  Escalate only if the PR stalls.
- **Stale sessions** are reported, never messaged or killed.
- **Notifications**: the human reads TM, so anything outside it is optional
  and quiet. For something urgent, `PushNotification` with a one-line
  summary. Never put secrets or credential-bearing log excerpts anywhere.
