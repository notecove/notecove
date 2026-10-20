"""Bootstrap the 'To Me' (TM) project, its states/types/board columns, and the
wt-manager skill's three notes (Worktrees, State, How-to). Idempotent: safe to
re-run, picks up whatever already exists instead of duplicating it.

Usage: python3 setup_tm_project.py

Prints a JSON object with the ids the wt-manager-installation skill needs to
patch into wt-manager.md:
    {"tm_project_id", "folder_id", "worktrees_note_id", "state_note_id", "howto_note_id"}
"""
import json
import subprocess
import sys

STATES = [
    ('waiting', 'Waiting for response', '#F59E0B'),
    ('onhold', 'On Hold', '#8B5CF6'),
    ('blocked', 'Blocked', '#EF4444'),
    ('wontdo', "Won't Do", '#6B7280'),
]
TYPES = [
    ('apply', 'Apply', '🚀'),
    ('merge', 'Merge', '🔀'),
    ('decide', 'Decide', '🤔'),
    ('message', 'Message', '💬'),
    ('review', 'Review', '👀'),
]
DEFAULT_TYPES_TO_DROP = {'feature', 'bug', 'chore'}

FOLDER_NAME = 'Worktree Manager'
NOTES = {
    'worktrees_note_id': ('Worktrees', (
        "# Worktrees\n\nOne `## <worktree>` section per active agent, each with a "
        "table of its open PRs. The manager keeps this current; add a row here "
        "when you dispatch a new worktree.\n\n## example-worktree\n\n"
        "| PR | Status |\n| --- | --- |\n| _(none yet)_ | |\n"
    )),
    'state_note_id': ('Worktree Manager State', (
        "# Worktree Manager State\n\n## Queue\n\n_(tickets waiting for a vacant "
        "worktree go here, oldest first)_\n\n## Overlaps\n\n_(worktrees touching "
        "the same files or stacked PRs)_\n\n### Ready to merge\n\n_(rewritten by "
        "ready_section.py)_\n\n### Waiting on you\n\n_(left blank; the manager "
        "reads TM directly for this)_\n\n## Worktree notes\n\n_(standing "
        "per-worktree instructions)_\n"
    )),
    'howto_note_id': ('Worktree Manager How-To', (
        "# Worktree Manager How-To\n\nStanding instructions for the manager "
        "agent, read at the start of every session. Edit this note directly; "
        "the manager re-reads it each time it starts.\n\n- Add house rules here "
        "as you discover you need them.\n"
    )),
}


def run(args, check=True):
    return subprocess.run(['notecove', *args], capture_output=True, text=True, timeout=60, check=check)


def run_json(args):
    return json.loads(run(args + ['--json']).stdout)


def find_or_create_project():
    for p in run_json(['project', 'list']):
        if p['slugPrefix'] == 'TM':
            return p['id'], False
    out = run(['project', 'create', 'To Me', '--slug', 'TM']).stdout
    for line in out.splitlines():
        if line.strip().startswith('ID:'):
            return line.split('ID:', 1)[1].strip(), True
    sys.exit(f"Could not parse project id from:\n{out}")


def configure_states_and_types(project):
    existing_states = {s['name'] for s in project['states']}
    for state_id, name, color in STATES:
        if name not in existing_states:
            run(['project', 'change', 'TM', '--add-state', '--state-id', state_id,
                 '--state-name', name, '--state-color', color])

    existing_type_names = {t['name'] for t in project['types']}
    for t in project['types']:
        if t['id'] in DEFAULT_TYPES_TO_DROP:
            run(['project', 'change', 'TM', '--remove-type', t['id']])
    for type_id, name, icon in TYPES:
        if name not in existing_type_names:
            run(['project', 'change', 'TM', '--add-type', '--type-id', type_id,
                 '--type-name', name, '--icon', icon])


def add_board_columns(project):
    boards = run_json(['project', 'board', 'list', 'TM'])
    if not boards:
        return
    board = boards[0]
    existing_state_ids = {c.get('stateId') for c in board.get('columns', [])}
    for state_id, name, color in STATES:
        if state_id not in existing_state_ids:
            run(['project', 'board', 'change', 'TM', board['id'],
                 '--add-column', name, '--state-id', state_id, '--color', color])


def find_or_create_folder(sd_id):
    for f in run_json(['folder', 'list']):
        if f['name'] == FOLDER_NAME and not f.get('parentId'):
            return f['id']
    out = run_json(['folder', 'create', FOLDER_NAME, '--sd', sd_id])
    return out['id']


def find_or_create_notes(folder_id):
    existing = {n['title']: n['id'] for n in run_json(['note', 'list', '--folder', folder_id, '--limit', '200'])}
    ids = {}
    for key, (title, content) in NOTES.items():
        if title in existing:
            ids[key] = existing[title]
            continue
        proc = subprocess.run(['notecove', 'note', 'create', '--folder', folder_id,
                               '--content-file', '-', '--format', 'markdown', '--json'],
                              input=content, capture_output=True, text=True, timeout=60, check=True)
        ids[key] = json.loads(proc.stdout)['id']
    return ids


def main():
    tm_id, created = find_or_create_project()
    project = run_json(['project', 'show', 'TM'])
    configure_states_and_types(project)
    project = run_json(['project', 'show', 'TM'])  # re-read after changes
    add_board_columns(project)

    folder_id = find_or_create_folder(project['sdId'])
    note_ids = find_or_create_notes(folder_id)

    result = {'tm_project_id': tm_id, 'folder_id': folder_id, **note_ids}
    print(json.dumps(result, indent=1))
    print(f"\nTM project {'created' if created else 'already existed'}.", file=sys.stderr)


if __name__ == '__main__':
    main()
