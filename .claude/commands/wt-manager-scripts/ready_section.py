"""Rewrite the manager's state note's '### Ready to merge' section from
pr_review_state.json.

Config: set STATE_NOTE_ID (the Notecove note to rewrite) as an environment
variable, or pass it as the first arg. The note must already contain a
'### Ready to merge' section and a following section to anchor the rewrite
to (see END_MARKER below) — the installation script sets this up.
"""
import json
import os
import subprocess
import sys
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.realpath(__file__))
NOTE = sys.argv[1] if len(sys.argv) > 1 else os.environ.get('STATE_NOTE_ID')
END_MARKER = os.environ.get('READY_SECTION_END_MARKER', '### Waiting on you')

if not NOTE:
    sys.exit("Usage: ready_section.py <STATE_NOTE_ID> (or set STATE_NOTE_ID env var)")

state = json.load(open(os.path.join(HERE, 'pr_review_state.json')))
when = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')

ready = [(n, v) for n, v in sorted(state.items()) if v['ready']]
reviewed = [(n, v) for n, v in sorted(state.items()) if v['human'] and not v['ready']]
lines = ['### Ready to merge', '', f"Updated by the manager's PR scan ({when}). Approved, CI green and mergeable:", '']
lines += [f"- [#{n}]({v['url']}) ({v['tree']}) {v['title']}" for n, v in ready] or ['- Nothing right now.']
lines += ['', '**Human-reviewed but not yet mergeable:**', '']
lines += [f"- [#{n}]({v['url']}) ({v['tree']}) {', '.join(v['human'])}; blocked by: " + '; '.join(v['blockers']) for n, v in reviewed] or ['- None.']
section = '\n'.join(lines) + '\n\n'

raw = subprocess.run(['timeout', '30', 'notecove', 'note', 'show', NOTE, '--format', 'markdown'], capture_output=True, text=True, check=True).stdout
body = raw.split('Content:\n', 1)[1]
i = body.index('### Ready to merge')
j = body.index(END_MARKER, i)
new = body[:i] + section + body[j:]
if new != body:
    path = os.path.join(HERE, 'ready_note.md')
    open(path, 'w').write(new)
    subprocess.run(['timeout', '60', 'notecove', 'note', 'edit', NOTE, '--content-file', path], check=True, capture_output=True)
    check = subprocess.run(['timeout', '30', 'notecove', 'note', 'show', NOTE, '--format', 'markdown'], capture_output=True, text=True).stdout
    print('updated' if f'({when})' in check else 'WRITE NOT VERIFIED')
else:
    print('unchanged')
