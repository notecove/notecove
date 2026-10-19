<p align="center">
  <img src="assets/og-image.png" alt="NoteCove — Your workspace. Your AI's too." width="640"/>
</p>

# NoteCove Skills for Claude Code

[NoteCove](https://notecove.io) is a local-first notes and tasks app for Mac. Your notes, folders, and projects are all readable and writable by the `notecove` CLI — making it a natural home for AI-assisted workflows.

This repo contains Claude Code skills that integrate directly with your NoteCove instance.

**Before starting:** You'll need to install the CLI and authenticating the CLI with your NoteCove profile. See the Initializing Access of the [CLI Documentation](https://notecove.io/docs/features/cli/) or watch the [video](https://www.youtube.com/watch?v=BimxhrMzk9U) that walks you through it.

---

## Skills

### `/daily` — Daily briefing

Starts your day by compiling a fresh daily note in NoteCove: pulls outstanding todos from recent notes, reads active tasks from your projects, checks your calendar and the weather, scans open PRs, and writes a prioritized action list with a short coaching brief.

Based on an idea and initial implementation by [Ville Hellman](https://github.com/efexen).

**Install:** run `/daily-installation` once to configure the skill for your NoteCove folders and projects.

---

### `/feature-nc` — Feature implementation workflow

A structured, multi-phase workflow for implementing features against a NoteCove codebase. Guides Claude through analysis, planning, critique, and implementation — tracking everything as Notecove notes and tasks.

The framework and philosophy behind it are described in these posts (written before the NoteCove variant existed, but the ideas carry over directly):
- [The feature command](https://drew.thecsillags.com/posts/2026-01-29-feature-command/)
- [Further narrowing](https://drew.thecsillags.com/posts/2026-02-27-further-narrowing/)

**Watch it in action:**

[![feature-nc demo](https://img.youtube.com/vi/SAmejhaNZxk/maxresdefault.jpg)](https://www.youtube.com/watch?v=SAmejhaNZxk)

**Install:** run `/feature-nc-installation` once to configure the skill for your NoteCove projects.

---

### `/wt-manager` — Worktree manager

Runs as its own Claude Code agent alongside a fleet of other agents working in sibling git worktrees. Watches each worktree's state and open PRs, and turns everything that needs a human — a question, a plan to approve, a PR to review, a production deploy to run — into a ticket in a dedicated NoteCove project ("TM," for "To Me"), instead of interrupting you directly. Also dispatches queued tickets into whichever worktree frees up next.

Ships with background scripts (`wt-manager-scripts/`) for watching TM for your replies, scanning PR reviews, and keeping a "ready to merge" note current.

**Install:** run `/wt-manager-installation` once to bootstrap the TM project and its states/types, and configure the skill for your NoteCove instance.

---

## Installation

1. Clone this repo somewhere on your machine:
   ```bash
   git clone https://github.com/notecove/notecove.git evoceton
   cd evoceton
   ```

2. Open the repo in Claude Code:
   ```bash
   claude .
   ```

3. Run the installation skill for each skill you want to use:
   - `/daily-installation` — sets up the daily skill
   - `/feature-nc-installation` — sets up the feature workflow skill
   - `/wt-manager-installation` — sets up the worktree manager skill

The installation skills will discover or create the required NoteCove folders and projects, and patch the skill files with the correct IDs for your instance.

> **Prerequisites:** The `notecove` CLI must be installed and connected to your NoteCove instance. The CLI is bundled with [NoteCove for Mac](https://notecove.io).
