"""Wait on the Notecove event stream for TM ticket changes made by someone
other than the manager itself.

On any task event for the TM project, diff the TM snapshot against tm_state.json
(state, comment count, modified time). Comment-only changes whose newest
comments are all by the manager are absorbed silently. Anything else is printed
and the script exits, so the caller wakes up, acts, and re-arms.

Config: set TM_PROJECT_ID (required) and MANAGER_NAME (your agent identity,
as it appears as a comment author — required to avoid reacting to your own
comments) as environment variables, or pass them as the first two args.
"""

import json
import os
import re
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.realpath(__file__))
STATE = os.path.join(HERE, "tm_state.json")
TM_PROJECT_ID = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("TM_PROJECT_ID")
MANAGER = sys.argv[2] if len(sys.argv) > 2 else os.environ.get("MANAGER_NAME")
HEADER = re.compile(r"^\[(\d+)\]\s+(\S+)\s+\S+\s+(\S+)")

if not TM_PROJECT_ID or not MANAGER:
    sys.exit("Usage: tm_events.py <TM_PROJECT_ID> <MANAGER_NAME> (or set TM_PROJECT_ID / MANAGER_NAME env vars)")


def run_json(args):
    out = subprocess.run(["notecove", *args, "--json"], capture_output=True, text=True,
                         timeout=60, check=True).stdout
    return json.loads(out)


def snapshot():
    snap = {}
    for t in run_json(["task", "list", "--project", "TM", "--limit", "500"]):
        slug = t["slug"]["short"] if isinstance(t["slug"], dict) else t["slug"]
        snap[slug] = {"id": t["id"], "title": t["title"], "state": t.get("stateName"),
                      "comments": t.get("commentCount", 0), "modified": t.get("modified")}
    return snap


def newest_comment_authors(slug, count):
    threads = run_json(["task", "comments", "list", slug, "--project", "TM"])
    items = []
    for th in threads:
        for c in [th, *th.get("replies", [])]:
            items.append((c.get("created") or c.get("createdAt") or 0,
                          c.get("authorName") or c.get("author") or c.get("user") or ""))
    items.sort()
    return {str(a) for _, a in items[-count:]} if count > 0 else set()


def diff(old, new):
    changes = []
    for slug, t in new.items():
        o = old.get(slug)
        if o is None:
            changes.append((slug, f"NEW {slug} [{t['state']}] {t['title']}", False))
            continue
        parts = []
        if t["state"] != o["state"]:
            parts.append(f"state {o['state']} -> {t['state']}")
        added = t["comments"] - o["comments"]
        only_comments = not parts
        if added:
            parts.append(f"comments {o['comments']} -> {t['comments']}")
        if not parts and t["modified"] != o["modified"]:
            parts.append("edited")
            only_comments = False
        if parts:
            mine = only_comments and added > 0 and newest_comment_authors(slug, added) <= {MANAGER}
            changes.append((slug, f"CHANGED {slug} ({', '.join(parts)}) {t['title']}", mine))
    for slug in old:
        if slug not in new:
            changes.append((slug, f"GONE {slug} {old[slug]['title']}", False))
    return changes


def main():
    old = json.load(open(STATE)) if os.path.exists(STATE) else snapshot()
    json.dump(old, open(STATE, "w"), indent=1)
    tm_ids = {t["id"] for t in old.values()}
    proc = subprocess.Popen(["notecove", "events", "--types", "task.*,comment.*"], stdout=subprocess.PIPE,
                            stderr=subprocess.DEVNULL, text=True)
    pending = False
    for line in proc.stdout:
        m = HEADER.match(line)
        if m:
            etype, entity = m.group(2), m.group(3)
            pending = (etype.startswith("task") or etype.startswith("comment")) and entity.startswith("task/") and entity.split("/")[-1] in tm_ids
            continue
        if not pending and TM_PROJECT_ID not in line:
            continue
        pending = False
        time.sleep(2)
        new = snapshot()
        tm_ids = {t["id"] for t in new.values()}
        changes = diff(old, new)
        json.dump(new, open(STATE, "w"), indent=1)
        old = new
        real = [c for _, c, mine in changes if not mine]
        if real:
            print("\n".join(real))
            proc.terminate()
            return


if __name__ == "__main__":
    main()
