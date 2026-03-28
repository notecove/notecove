---
allowed-tools:
  - Read(///tmp/**)
  - Read(///private/tmp/**)
  - Write(///tmp/**)
  - Write(///private/tmp/**)
  - Bash(nc_canary=1 notecove folder *)
  - Bash(nc_canary=1 notecove note *)
  - Bash(nc_canary=1 notecove task *)
  - Bash(nc_canary=1 notecove open *)
  - Bash(nc_canary=1 mktemp *)
  - Bash(nc_canary=1 rm /tmp/nc-*)
  - Bash(nc_canary=1 rm /private/tmp/nc-*)
  - Bash(nc_canary=1 git checkout -b *)
  - Bash(nc_canary=1 git branch *)
---

# Feature Implementation Workflow

**Task:** $ARGUMENTS

---

## Setup

0. **Check if argument is a Notecove task reference:**
   - If `$ARGUMENTS` matches the pattern `NOTE-{something}` (or contains a reference like "see NOTE-{something}"), treat it as a Notecove task ID
   - Read the task: `notecove task show $ARGUMENTS --project NOTE --json` — use the full argument as-is (e.g., `NOTE-rrd`), do NOT strip the prefix or extract just the short part
   - The task body is your actual feature description — use it as the basis for deriving the slug and all subsequent steps
   - Always read both `title` and the body content (from `contentJson.content` or the plain-text `contentText`) since the title alone may not contain everything you need
   - **Read the task type** from the `typeName` field in the JSON and use it as a lens for the whole session. Examples:
     - `cli` — scope is `packages/cli`; don't plan desktop or iOS work unless the body explicitly calls for it
     - `desktop` — scope is `packages/desktop`; same constraint
     - `ios` — scope is `packages/ios`; same constraint
     - `crdt` — the ticket is about sync/data correctness; read the relevant storage ADRs before planning, and weight testing strategies toward crdt-inspection and multi-instance scenarios
     - `performance` — the ticket is about speed or efficiency; establish a baseline measurement before touching code, and validate against it
     - `null` / no type — no constraint; use judgment from the task body
       The type won't always map cleanly to a rule — use it as a signal to understand _what kind of work this is_ and plan accordingly.
   - **Mark as Doing immediately:** if the task state is not already `Doing`, run `notecove task change $ARGUMENTS --state "Doing" --project NOTE` — this prevents `/feature-next` from offering the same ticket to another worker
   - **Tag with worktree:** detect the current worktree name by running `git worktree list` and matching against `pwd`. Use the directory basename as the identifier (e.g. `notecove-3-wt2` → `wt2`, or just the full basename if short). Append `#wt-{name}` to the task description via `notecove task change $ARGUMENTS --content "$(existing content) #wt-{name}" --project NOTE`. This makes the active worktree visible when viewing the task on phone or kanban. Remove the tag when the session completes (Phase 4 done).
1. Derive a kebab-case slug from the task description (e.g., "rename an SD" → `rename-sd`)
2. Create and checkout git branch: `{slug}`. If `$ARGUMENTS` was a `NOTE-*` reference, `begin-change` will have pre-created a placeholder branch named after the ticket (e.g. `NOTE-hkz6`) to mark the worktree as in-use. After `git checkout -b {slug}` succeeds, delete the placeholder: `git branch -d {ticket-name}` (e.g. `git branch -d NOTE-hkz6`).
3. **Create Notecove folder structure:**
   - Run `notecove folder list --json` and parse the output to find a folder named `Claude`
   - If `Claude` folder does not exist, create it: `notecove folder create Claude --json` — parse the JSON output to get the folder ID
   - Create the feature subfolder: `notecove folder create "{slug}" --parent {claudeFolderId} --json` — save the returned folder ID as `{slugFolderId}` for all subsequent note creation
4. **Save the original prompt** as a note:
   - Run `mktemp /tmp/nc-prompt-XXXXXX` via Bash and capture the **returned path from stdout** — this is `{tempFile}`. Do NOT use the literal pattern `/tmp/nc-prompt-XXXXXX` as the file path.
   - Use the Write tool to write the prompt content to `{tempFile}`, starting with `# Prompt`:
     - If the prompt came from a Notecove task (step 0): include a task link on the next line — `Source task: [[T:{taskId}|{taskTitle}]]` — where `{taskId}` is the raw `id` field from the task JSON, then the resolved task body below
     - If the prompt was plain text: write the $ARGUMENTS text directly
   - Run `notecove note create --folder {slugFolderId} --content-file {tempFile} --format markdown --json`
   - The note title will be derived from the first line of content, so start the content with `# Prompt`
   - Run `notecove open {noteId}` to open the note for the user
   - Clean up the temp file after the note is created
5. **Create the top-level feature task:**
   - Run `notecove task create "{Short feature description}" --folder {slugFolderId} --json --project CLAU`
   - Parse the JSON output to get `id` (the internal task ID) and `slug.full` (e.g., `CLAU-42`)
   - Save both the task ID and slug — this is the **parent task** for all plan steps

**Temp file handling:**

- Always use `mktemp /tmp/nc-{purpose}-XXXXXX` (via Bash) to generate a unique temp file path (multiple /feature-nc sessions may run concurrently). The **returned path from stdout** is the actual file path — do NOT use the literal pattern string as a file path.
- **Use the Write tool** to write content to the temp file — do NOT use heredocs, `cat <<EOF`, or `echo` redirection via Bash
- **Use the Read tool** to read temp files when needed — do NOT use `cat` via Bash
- `/tmp` and `/private/tmp` are both pre-authorized for Read and Write (no user prompt needed)
- Clean up temp files after use (via Bash `rm`)

**Important state to track throughout the workflow:**

- `{slugFolderId}` — Notecove folder ID for creating notes
- `{topLevelTaskId}` — internal ID of the top-level feature task
- `{topLevelTaskSlug}` — slug of the top-level feature task (e.g., `CLAU-42`)
- Note IDs — save the ID returned by each `note create` so notes can be edited and re-read later
- Task IDs and slugs — save these for each created task for linking and state updates

**Critical principle — always re-read before acting:**

- The user may edit notes directly in Notecove (inline text edits or comments on selected text)
- Before acting on ANY note you created earlier, **always re-read it first**:
  - `notecove note show {noteId} --format markdown-with-comments` — returns markdown content AND comment threads in a single call (inline edits + comments with line numbers, author, and replies)
- Treat both inline edits and comments as user feedback that must be addressed
- **Responding to comments**: When you find comments on a note or task, respond as a reply to that comment thread:
  - For note comments: `notecove note comments reply {noteId} {threadId} "your response"`
  - For task comments: `notecove task comments reply {slug} {threadId} "your response" --project {project}`
  - The `threadId` is found in the `--json` output under each comment thread's `id` field

**Persisting Explore subagent results:**

Whenever you launch an Explore subagent (in ANY phase — analysis, planning, implementation, etc.), save its results as a Notecove note immediately after it returns:

1. Create a temp file: `mktemp /tmp/nc-explore-XXXXXX`
2. Use the Write tool to write the content to the temp file, starting with `# Explore: {brief description of what was explored}`, followed by a blank line, then the **full verbatim output** from the subagent (do not summarize or filter)
3. Create the note: `notecove note create --folder {slugFolderId} --content-file {tempFile} --format markdown --json`
4. Save the returned note ID — you may need to re-read this research later
5. Clean up the temp file

This produces one note per Explore invocation. The notes serve as a persistent research trail that the user can review, correct, or reference later.

**Reading tasks:**

- When referencing any Notecove task, always read the **full task** (title + body + comments) — the title alone often doesn't contain everything you need
- Use `notecove task show {slug} --json --project {project}` to get everything in one call: title is in `title`, body is in `contentText` (plain text) or `contentJson.content` (XML), and comments are in `comments`

---

## Phase 1: Analysis & Questions

Your task is NOT to implement yet, but to fully understand and prepare.

**Responsibilities:**

- Analyze and understand the existing codebase thoroughly
- Determine exactly how this feature integrates, including dependencies, structure, edge cases (within reason), and constraints
- Clearly identify anything unclear or ambiguous in the description or current implementation
- Write all questions or ambiguities as a Notecove note (do NOT repeat questions in the chat — only put them in the note):
  - Create the note via heredoc stdin, starting with `# Questions 1: {topic}`:
    ```bash
    notecove note create --folder {slugFolderId} --content-file - --format markdown --json << 'EOF'
    # Questions 1: {topic}
    ...
    EOF
    ```
  - Save the note ID in case the note needs to be edited later
  - Run `notecove open {noteId}` to open the note for the user

**Design Document Identification:**

Identify which design documents are relevant to this feature. Check:

- `ADR/` directory - Architecture Decision Records and implementation tenets
- `website/technical_documents/` - Technical specifications
- Other design docs mentioned in CLAUDE.md or the codebase

List relevant documents in the Questions note under a "Relevant Design Documents" section. These will be audited against in Phase 3.

**Website Documentation Check:**

Before planning, check if this feature adds/removes/changes anything in the website's feature documentation (`website/features/`). If so:

- Make "Update website documentation" an explicit item in the plan
- If this is a **new feature**, ask the user: "Should this be added to the feature list on the website? It might not warrant inclusion."
- Remember that feature lists are **per-platform** (desktop, iOS, Android) - features don't automatically apply to all platforms

**ADR Context Check:**

Before planning, check if this feature relates to documented architecture:

- **Storage/CRDT/Sync work**: Read `ADR/storage/` for context on storage format, sync architecture
- **Cross-SD operations**: Read `ADR/architecture/cross-sd-move-state-machine.md`
- **IPC changes**: Read `ADR/integration/ipc-protocol.md`
- **If unsure**: Use Explore subagent to determine which ADRs are relevant (results will be persisted automatically — see "Persisting Explore subagent results" above)
- Note any architectural constraints or patterns that must be followed

**Verification Plan:**

Propose a verification strategy in the Questions note for the user to review and approve before planning begins. Consult `ADR/testing/README.md` for the full catalog of testing strategies.

Based on your analysis of the feature, answer the following questions and include your answers in the Questions note under a "Verification Strategy" section — the user will review and correct your proposal:

1. **Does this feature involve sync/CRDT operations?**
   - Yes → Suggest: multi-instance testing, sloppy-sync, crdt-inspection
   - No → Continue

2. **Does this feature involve cross-machine scenarios?**
   - Yes → Suggest: sloppy-sync (FileSyncSimulator), multi-instance testing
   - No → Continue

3. **Does this feature change storage format or CRDT structure?**
   - Yes → Suggest: crdt-inspection, unit tests for format compliance
   - No → Continue

4. **Is this primarily a UI feature?**
   - Yes → Suggest: e2e-playwright, consider visual regression testing
   - No → Continue

5. **Does this feature affect iOS?**
   - Yes → Suggest: ios-testing (XCTest)
   - No → Continue

Document your proposed strategies in the Questions note under a "Verification Strategy" section. The goal is to **maximize automation** and **minimize manual user verification**. The user must review and approve this strategy before planning begins.

For each suggested strategy, reference the relevant doc in `ADR/testing/` for implementation patterns.

**Important:**

- Do NOT assume any requirements or scope beyond explicitly described details
- Do NOT implement anything yet - just explore, plan, and ask questions
- This phase is iterative: when the user says they've answered, re-read the Questions note:
  - `notecove note show {questionsNoteId} --format markdown-with-comments` — returns content AND comment threads in one call; process both inline edits and comments as answers
- You may create additional "Questions {N}: {topic}" notes for follow-up questions
- Continue until all ambiguities are resolved

**Checkpoint behavior:**

- **Always create the Questions note** — this step is NEVER skipped. Even if the feature description is perfectly clear and you have zero ambiguities, you MUST still create the note with at minimum the Verification Strategy section. If you have no questions, state that explicitly and explain why in the note.
- **Questions and verification strategy go in the note only** — do NOT repeat them in chat. Tell the user the Questions note is ready and wait for their response.
- **MUST wait for user response** — do NOT proceed to Phase 2 until the user has explicitly responded (inline edits, comments, or a chat message). Auto-proceeding without user input is not allowed, even if all questions seem answerable from context.
- **After reading answers**: If all questions are resolved, proceed to Phase 2 automatically. Only pause if questions remain unanswered.

---

## Phase 2: Plan Creation

Based on the full exchange, produce a plan as Notecove tasks and a Plan note.

**Task Creation Workflow:**

Create tasks in the CLAU project that mirror the plan structure. The hierarchy is:

```
Top-level feature task (already created in Setup)
├── Phase task (if phases exist)
│   ├── Main step task
│   │   ├── Sub-step task
│   │   └── Sub-step task
│   └── Main step task
│       └── Sub-step task
└── Main step task (if no phases, directly under top-level)
    ├── Sub-step task
    └── Sub-step task
```

For each task:

1. Create it with `notecove task create "{title}" --folder {slugFolderId} --parent {parentSlug} --json --project CLAU --content "{detailed description}" --content-format markdown`
   - Always include a `--content` body with enough detail for someone to understand the task without reading the title alone
2. Parse the JSON output to extract `id` and `slug.full`
3. Save these for use in the Plan note

**Plan Note:**

After creating all tasks, compose the Plan note content:

- Start with `# Plan: {feature description}`
- For each task, include a task link using the format `[[T:taskId|Step title]]` — this renders as a clickable chip in Notecove that shows the task's current state color (grey for Todo, green for Done)
  - To get `taskId`: use the `id` field directly from JSON output (e.g., `7td85ffaxwcs6naswax37va3g1`) — it is already the raw 26-char ID, no processing needed. Do NOT use `slug.full` (which has a project prefix and colon).
- Create the note via heredoc stdin:
  ```bash
  notecove note create --folder {slugFolderId} --content-file - --format markdown --json << 'EOF'
  # Plan: {feature description}
  ...
  EOF
  ```
- Save the Plan note ID for later editing
- Run `notecove open {planNoteId}` to open the plan note for the user

**Plan Note Template Example:**

```markdown
# Plan: Add authentication module

## Tasks

### Step 1: Setup authentication module

[[T:abc123def456|Setup authentication module]]

- [[T:ghi789jkl012|Create authentication service class]]
- [[T:mno345pqr678|Implement JWT token handling]]
- [[T:stu901vwx234|Update plan]]

### Step 2: Develop frontend login UI

[[T:yza567bcd890|Develop frontend login UI]]

- [[T:efg123hij456|Design login page component]]
- [[T:klm789nop012|Integrate component with endpoints]]
- [[T:qrs345tuv678|Update plan]]

## Verification Strategy

| Strategy   | Tests                                        | Status |
| ---------- | -------------------------------------------- | ------ |
| Unit Tests | `describe('MyFeature', ...)` in `__tests__/` | Todo   |
| E2E Tests  | `my-feature.spec.ts`                         | Todo   |

## Deferred Items

(Items moved here only with user approval)

- None
```

**Verification Strategy (included in the Plan note, not a separate note):**

Include a `## Verification Strategy` section in the Plan note (see template above). This should list:

- Automated testing strategies (unit tests, e2e tests, etc.) with status
- Manual verification items only if they CANNOT be automated — explain why for each
- The goal is to **maximize automation** and **minimize manual user verification**

**Phase Notes (if feature is complex enough):**

For complex features with multiple phases, create a "Plan Phase {N}: {phase name}" note for each phase in the `Claude/{slug}` folder.

**Requirements for the plan:**

- Include clear, minimal, concise steps
- Do NOT add extra scope or unnecessary complexity beyond explicitly clarified details
- Steps should be modular, elegant, minimal, and integrate seamlessly within the existing codebase
- Use TDD: tests are part of the plan and written before the thing they test
- For EVERY step that changes an interface, service, or component props, add an explicit sub-step: 'Grep for and update all test mocks and fixtures for [changed module]'. List mock update tasks explicitly, don't bundle them into 'fix tests'.

**Priority and Deferral Rules:**

- **You do NOT get to choose** the priority or optionality of items in the plan
- **If you think something should be deferred**, ask the user first:
  - "I'm considering deferring X because Y. Is that acceptable?"
  - If they agree, change the task state to "Deferred": `notecove task change {slug} --state Deferred --project CLAU`
  - Update the Plan note to move the item to the "Deferred Items" section
  - If they disagree, keep it in place at full priority

**Plan Maintenance:**

- **Every step** must end with a sub-step to update the Plan note and task states
- Update the Plan note via heredoc stdin:
  ```bash
  notecove note edit {planNoteId} --content-file - --format markdown << 'EOF'
  # Plan: {feature description}
  ...updated content...
  EOF
  ```
- Update task states via `notecove task change {slug} --state {state} --project CLAU`
- Available states: `Todo`, `Doing`, `Done`, `Deferred`

**⏸ CHECKPOINT**: When the Plan note and all tasks are created, say "Plan created. Say 'continue' for Phase 3"

---

## Phase 3: Plan Critique

Before critiquing, re-read the Plan note to pick up any user feedback:

- `notecove note show {planNoteId} --format markdown-with-comments` — returns markdown content AND comment threads in one call; check for both inline edits and comments

Address any user feedback found before proceeding with your own critique.

Review the plan as a staff engineer. Evaluate:

- **Ordering**: Do earlier steps inadvertently rely on later things?
- **Feedback loop**: Which ordering gets us to something we can interactively test sooner?
- **Debug tools**: Do we have debug tools ready when we'll want them if something's not working?
- **Missing items**: Is there something missing that should be asked about?
- **Risk assessment**: Have risks been properly assessed? Should we consider additional tests?
- **TDD compliance**: Are tests written BEFORE implementation in every phase?
  - Each phase should follow RED-GREEN-REFACTOR cycle:
    - RED: Write tests first, verify they FAIL (no implementation yet)
    - GREEN: Implement to make tests PASS
    - REFACTOR: Clean up if needed
  - Implementation steps must NOT appear before test steps
  - Tests must NOT be deferred to end of phase or marked as "write tests after implementation"
  - If tests appear out of order, restructure the phase to follow proper TDD workflow
  - This is MANDATORY - test-after-implementation violates TDD principles

**Design Document Compliance Audit:**

For each design document identified in Phase 1, verify the plan complies:

1. **Re-read the design document(s)** - Don't rely on memory; read them fresh
2. **Check each plan item** - Does it align with the tenets/specifications?
3. **Look for violations** - File naming conventions, directory structures, ID formats, protocols, etc.
4. **Document findings** - Edit the Plan note to add a "Design Compliance" section listing:
   - Which documents were checked
   - Any violations found (and how they're addressed in the plan)
   - Confirmation that the plan aligns with each relevant tenet

If violations are found that aren't addressed by the plan, add tasks to fix them or ask the user if they should be deferred.

**Additional requirements:**

- If this phase generates questions, create a "Plan Questions {N}: {topic}" note in the `Claude/{slug}` folder
- If plan changes are needed, update the Plan note via heredoc stdin: `notecove note edit {planNoteId} --content-file - --format markdown << 'EOF' ... EOF`
- If tasks need to be added, removed, or reordered, update them via `notecove task create` / `notecove task change` / `notecove task delete`

**⏸ CHECKPOINT**: When plan is finalized, say "Plan finalized. Say 'continue' for Phase 4"

---

## Phase 4: Implementation

Now implement precisely as planned, in full.

**Implementation Requirements:**

- Write elegant, minimal, modular code
- Adhere strictly to existing code patterns, conventions, and best practices
- Include clear comments/documentation within the code where needed
- As you complete each step:
  - Update the task state: `notecove task change {slug} --state Doing --project CLAU` when starting a step
  - Update the task state: `notecove task change {slug} --state Done --project CLAU` when completing a step
  - Note any deviations from the original plan in the Plan note (update via heredoc stdin: `notecove note edit {planNoteId} --content-file - --format markdown << 'EOF' ... EOF`)
- Follow TDD: write failing tests first, then implement to make them pass
- Run ci-runner before any commits

**⏸ CHECKPOINT**: Pause before commits for user approval

---

## Appendix: Platform Feature Tracking

When updating website documentation, remember that features are **platform-specific**:

| Platform | Status      | Feature List Location                            |
| -------- | ----------- | ------------------------------------------------ |
| Desktop  | Active      | `website/features/` (current)                    |
| iOS      | Coming Soon | `website/features/ios/` (create when needed)     |
| Android  | Planned     | `website/features/android/` (create when needed) |

**Important:** When documenting a feature:

- Clearly indicate which platform(s) it applies to
- Don't assume a desktop feature will be available on mobile (or vice versa)
- Update the appropriate platform-specific feature list(s)

## Appendix: Notecove CLI Quick Reference

**Folder operations:**

- `notecove folder list --json` — list all folders (find by name)
- `notecove folder create "{name}" --parent {parentId} --json` — create subfolder

**Note operations:**

- `notecove note create --folder {folderId} --content-file {path} --format markdown --json` — create note (title from first `#` heading)
- `notecove note edit {noteId} --content-file {path} --format markdown` — replace note content
- `notecove note edit {noteId} --append-file {path} --format markdown` — append to note
- `notecove note show {noteId} --format markdown-with-comments` — read note content AND comment threads in one call (preferred for re-reading notes with potential user feedback)
- `notecove note show {noteId} --format markdown` — read note content as markdown only (no comments)
- `notecove note show {noteId} --json` — read note as JSON (includes comments and content as XML; use only when you need the raw ProseMirror structure)

**Open operations:**

- `notecove open {noteId}` — open a note in the desktop app (use after creating or editing notes)

**Note comment operations:**

- `notecove note comments list {noteId}` — list comment threads on a note
- `notecove note comments add {noteId} "content"` — add a comment to a note
- `notecove note comments reply {noteId} {threadId} "content"` — reply to a comment thread

**Task operations:**

- `notecove task create "{title}" --folder {slugFolderId} --parent {parentSlug} --json --project CLAU --content "{description}" --content-format markdown` — create task with body
- `notecove task change {slug} --state {Todo|Doing|Done|Deferred} --project CLAU` — update state
- `notecove task change {slug} --state {state} --json --project CLAU` — update state with JSON output
- `notecove task show {slug} --project CLAU` — view task details
- `notecove task tree {slug} --project CLAU` — view task hierarchy
- `notecove task comments list {slug} --project CLAU` — list comments on a task
- `notecove task comments add {slug} "content" --project CLAU` — add a comment to a task
- `notecove task comments reply {slug} {threadId} "content" --project CLAU` — reply to a comment thread

**Task link syntax** (for use in note content):

- `[[T:taskId|Display Title]]` — renders as a clickable chip showing the task's state color
- The `taskId` is the `id` field from JSON output — use it directly, no processing needed
  - JSON returns `"id": "7td85ffaxwcs6naswax37va3g1"` (raw 26-char ID)
  - Final link: `[[T:7td85ffaxwcs6naswax37va3g1|Display Title]]`
  - **Do NOT** use `slug.full` (e.g., `CLAU-7td:85ffaxwcs6naswax37va3g1`) — stripping the prefix and colon can produce incorrect IDs
