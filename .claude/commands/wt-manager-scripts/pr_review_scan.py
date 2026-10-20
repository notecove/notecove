"""Scan open worktree PRs for human reviews and merge readiness; report changes.

Config: set GH_REPO (owner/name) as an environment variable, or pass it as
the first arg, if `gh` can't infer the repo from the current directory.
Set BASE_BRANCH if your default branch isn't `main`.
"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.realpath(__file__))
STATE = os.path.join(HERE, 'pr_review_state.json')
BOTS = {'github-actions', 'copilot-pull-request-reviewer', 'claude'}
REPO = sys.argv[1] if len(sys.argv) > 1 else os.environ.get('GH_REPO')
BASE_BRANCH = os.environ.get('BASE_BRANCH', 'main')


def sh(*a):
    return subprocess.run(a, capture_output=True, text=True, check=True).stdout


status_args = ['python3', os.path.join(HERE, 'wt_status.py'), '--base-branch', BASE_BRANCH]
if REPO:
    status_args += ['--repo', REPO]
ws = json.loads(sh(*status_args))

prs = {}
for t in ws['worktrees']:
    for p in t.get('prs', []):
        prs[p['number']] = (t['branch'], p)

gh_view_args = ['gh', 'pr', 'view', '{n}', '--json',
                 'title,url,reviewDecision,latestReviews,mergeable,mergeStateStatus']
if REPO:
    gh_view_args += ['--repo', REPO]

out = {}
for n, (tree, p) in sorted(prs.items()):
    args = [a.format(n=n) if a == '{n}' else a for a in gh_view_args]
    d = json.loads(sh(*args))
    human = sorted({f"{r['author']['login']}:{r['state']}" for r in d['latestReviews']
                    if r['author']['login'] not in BOTS and not r['author']['login'].endswith('[bot]')})
    ready = d.get('reviewDecision') == 'APPROVED' and d.get('mergeable') == 'MERGEABLE'
    blockers = []
    if d.get('mergeable') == 'CONFLICTING':
        blockers.append('merge conflicts, needs a rebase')
    if d.get('reviewDecision') not in ('APPROVED', None, ''):
        blockers.append(f"review: {d.get('reviewDecision')}")
    elif not human:
        blockers.append('no human review yet')
    out[str(n)] = {'tree': tree, 'title': d['title'][:80], 'url': d['url'], 'human': human,
                   'ready': ready, 'mergeable': d['mergeable'], 'blockers': blockers}

prev = json.load(open(STATE)) if os.path.exists(STATE) else {}
new_review, new_ready, still_ready = [], [], []
for n, v in out.items():
    pv = prev.get(n, {})
    added = sorted(set(v['human']) - set(pv.get('human', [])))
    if added:
        new_review.append((n, v, added))
    if v['ready'] and not pv.get('ready'):
        new_ready.append((n, v))
    elif v['ready']:
        still_ready.append((n, v))
merged_or_closed = sorted(set(prev) - set(out))
json.dump(out, open(STATE, 'w'), indent=1)

print('FIRST_RUN' if not prev else 'DELTA')
for n, v, added in new_review:
    print(f"REVIEW #{n} ({v['tree']}) {', '.join(added)} | {v['title']} | {v['url']}")
for n, v in new_ready:
    print(f"READY #{n} ({v['tree']}) | {v['title']} | {v['url']}")
for n, v in still_ready:
    print(f"STILL_READY #{n} ({v['tree']}) | {v['title']}")
for n in merged_or_closed:
    print(f"GONE #{n} ({prev[n]['tree']}) | {prev[n]['title']}")
reviewed = [(n, v) for n, v in out.items() if v['human']]
print(f"SUMMARY open={len(out)} with_human_review={len(reviewed)} ready={sum(v['ready'] for v in out.values())}")
for n, v in reviewed:
    print(f"  HUMAN #{n} ({v['tree']}) {', '.join(v['human'])} ready={v['ready']} | {v['title']}")
