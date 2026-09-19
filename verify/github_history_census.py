#!/usr/bin/env python3
"""Census of the bitcoin/bitcoin git history, 30 Aug 2009 to 31 Dec 2010: how many commits, under which
author strings, and how many exist twice on parallel lineages converted from Subversion.

The canonical repository's early history was imported from SourceForge SVN and carries most commits
twice: one copy with a `git-svn-id` trailer (author `s_nakamoto`, the SVN account) and one without,
dated the same day or up to eight days later, some under the author string `Satoshi Nakamoto` and a
few under the literal string `--author=Satoshi Nakamoto`. A date read from the wrong copy is off by up
to eight days, and in eight pairs the two copies differ by a few lines. This script measures that from
GitHub's own commit records and writes one JSON summary. [statistical]

    python verify/github_history_census.py                     # four unauthenticated API calls
    python verify/github_history_census.py --out census.json
    python verify/github_history_census.py --stats             # also compares each pair's additions,
                                                               # deletions and file list: one call per
                                                               # commit, so it needs GITHUB_TOKEN

Standard library only. Without `--stats` it stays inside GitHub's unauthenticated rate limit. Method:
list every commit on the default-branch history in the window (paginated), exclude merge commits and
the root, group the rest by first message line, and count groups that pair a trailer copy with a
non-trailer copy. Counting by message is a proxy for "the same change"; `--stats` is what makes a
pairing a fact rather than a coincidence of wording.
"""
from __future__ import annotations

import argparse
import collections
import json
import os
import sys
import time
import urllib.request
from datetime import datetime, timezone

SINCE, UNTIL = "2009-08-30T00:00:00Z", "2011-01-01T00:00:00Z"
API = "https://api.github.com/repos/bitcoin/bitcoin/commits"
UA = "satoshi-onchain census (github.com/satoshi-onchain; polite, sequential)"


def get(url: str) -> object:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/vnd.github+json"})
    tok = os.environ.get("GITHUB_TOKEN")
    if tok:
        req.add_header("Authorization", f"Bearer {tok}")
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def commits() -> list[dict]:
    rows: list[dict] = []
    for page in range(1, 20):
        got = get(f"{API}?since={SINCE}&until={UNTIL}&per_page=100&page={page}")
        for c in got:
            msg = c["commit"]["message"]
            rows.append({"sha": c["sha"], "date": c["commit"]["author"]["date"], "name": c["commit"]["author"]["name"],
                         "email": c["commit"]["author"]["email"], "msg": msg.split("\n")[0], "parents": len(c["parents"]),
                         "svn": "git-svn-id" in msg})
        if len(got) < 100:
            break
        time.sleep(1)
    return rows


def stats(sha: str) -> tuple[int, int, str]:
    c = get(f"{API}/{sha}")
    time.sleep(0.5)
    return int(c["stats"]["additions"]), int(c["stats"]["deletions"]), ",".join(sorted(f["filename"] for f in c["files"]))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--out", default=None)
    ap.add_argument("--stats", action="store_true", help="compare each pair's change statistics (needs GITHUB_TOKEN)")
    a = ap.parse_args()
    rows = commits()
    names = collections.Counter(r["name"] for r in rows)
    trailer = sum(1 for r in rows if r["svn"])
    non_merge = [r for r in rows if r["parents"] == 1]
    by_msg: dict[str, list[dict]] = collections.defaultdict(list)
    for r in non_merge:
        by_msg[r["msg"]].append(r)
    pairs = [v for v in by_msg.values() if {x["svn"] for x in v} == {True, False}]
    gaps: list[float] = []
    copy_names: collections.Counter = collections.Counter()
    same = differ = failed = 0
    differing: list[dict] = []
    for v in pairs:
        svn = [x for x in v if x["svn"]][0]
        non = [x for x in v if not x["svn"]][0]
        d0 = datetime.fromisoformat(svn["date"].replace("Z", "+00:00"))
        d1 = datetime.fromisoformat(non["date"].replace("Z", "+00:00"))
        gaps.append(round((d1 - d0).total_seconds() / 86400, 2))
        for x in v:
            if not x["svn"]:
                copy_names[x["name"]] += 1
        if a.stats:
            try:
                s0, s1 = stats(svn["sha"]), stats(non["sha"])
            except Exception as e:  # noqa: BLE001 - a failed fetch is reported, not hidden
                failed += 1
                continue
            if s0 == s1:
                same += 1
            else:
                differ += 1
                differing.append({"trailer": svn["sha"][:9], "other": non["sha"][:9], "trailer_add_del": s0[:2], "other_add_del": s1[:2], "message": svn["msg"][:60]})
    gaps.sort()
    summary = {
        "window": [SINCE, UNTIL],
        "commits_on_default_branch_history": len(rows),
        "author_name_strings": dict(names),
        "with_git_svn_id_trailer": trailer,
        "merge_commits": sum(1 for r in rows if r["parents"] > 1),
        "non_merge_commits": len(non_merge),
        "duplicate_groups_trailer_plus_non_trailer": len(pairs),
        "non_trailer_copy_author_strings": dict(copy_names),
        "non_trailer_minus_trailer_days": {"min": gaps[0], "median": gaps[len(gaps) // 2], "p90": gaps[int(len(gaps) * 0.9)], "max": gaps[-1],
                                           "non_trailer_earlier": sum(1 for g in gaps if g < 0)} if gaps else None,
        "author_eq_literal_option_string": sorted((r["sha"][:9], r["date"][:10]) for r in rows if r["name"].startswith("--author=")),
        "pairs_compared": {"identical": same, "differ": differ, "not_compared": failed, "differing": differing} if a.stats else "not run (--stats)",
        "source": API + " (GitHub's own records, read on the run date; the history can be rewritten by its owners)",
        "run_date": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    text = json.dumps(summary, indent=2)
    print(text)
    if a.out:
        with open(a.out, "w", encoding="utf-8", newline="\n") as f:
            f.write(text + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
