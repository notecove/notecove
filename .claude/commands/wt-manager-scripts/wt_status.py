"""Snapshot every git worktree of the current repo: branch, dirty state,
ahead/behind the base branch, open PRs, and a vacancy guess.

Replaces a private `wt-status` binary with something anyone can run. Session
liveness (which worktree has a live Claude Code agent attached) is NOT here —
that comes from the ListAgents tool inside the skill itself, since a shell
script has no way to see other agent sessions.

Usage:
    python3 wt_status.py [--base-branch main] [--repo owner/name]

Output: a JSON object `{"worktrees": [...]}` on stdout. Each entry:
    path, branch, dirty (bool), ahead, behind, prs (list), vacant (bool)
"""
import argparse
import json
import subprocess


def sh(*args, cwd=None):
    return subprocess.run(args, cwd=cwd, capture_output=True, text=True, check=True).stdout


def list_worktrees():
    out = sh('git', 'worktree', 'list', '--porcelain')
    trees, cur = [], {}
    for line in out.splitlines():
        if not line:
            if cur:
                trees.append(cur)
            cur = {}
            continue
        if line.startswith('worktree '):
            cur['path'] = line.split(' ', 1)[1]
        elif line.startswith('branch '):
            cur['branch'] = line.split(' ', 1)[1].removeprefix('refs/heads/')
        elif line == 'detached':
            cur['branch'] = None
    if cur:
        trees.append(cur)
    return trees


def git_info(path, base_branch):
    dirty = bool(sh('git', '-C', path, 'status', '--porcelain').strip())
    try:
        counts = sh('git', '-C', path, 'rev-list', '--left-right', '--count',
                    f'origin/{base_branch}...HEAD').split()
        behind, ahead = int(counts[0]), int(counts[1])
    except subprocess.CalledProcessError:
        behind, ahead = None, None
    return dirty, ahead, behind


def prs_for_branch(branch, repo=None):
    if not branch:
        return []
    args = ['gh', 'pr', 'list', '--head', branch, '--json',
            'number,title,url,isDraft,reviewDecision,mergeable,statusCheckRollup']
    if repo:
        args += ['--repo', repo]
    try:
        return json.loads(sh(*args))
    except subprocess.CalledProcessError:
        return []


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--base-branch', default='main')
    ap.add_argument('--repo', default=None)
    args = ap.parse_args()

    out = []
    for t in list_worktrees():
        path, branch = t.get('path'), t.get('branch')
        if branch in (None, args.base_branch):
            continue  # skip the main checkout / detached heads
        dirty, ahead, behind = git_info(path, args.base_branch)
        prs = prs_for_branch(branch, args.repo)
        out.append({
            'path': path,
            'branch': branch,
            'dirty': dirty,
            'ahead': ahead,
            'behind': behind,
            'prs': prs,
            'vacant': not dirty and not prs,
        })
    print(json.dumps({'worktrees': out}, indent=1))


if __name__ == '__main__':
    main()
