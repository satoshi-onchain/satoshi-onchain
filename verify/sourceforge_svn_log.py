"""The complete SourceForge SVN history of the Bitcoin project, via Software Heritage.

Why this matters: SVN commit timestamps are set by the SERVER at commit time, on infrastructure
Satoshi did not run. They are the same evidential class as the SourceForge join date -- and there
are 164 of them under s_nakamoto. This is the densest machine-verifiable record of Satoshi's
working activity that exists outside the block chain.

SourceForge itself no longer serves the repo history; Software Heritage holds a full crawl.
Origin: https://svn.code.sf.net/p/bitcoin/code
"""
import urllib.request, json, sys, re, os, hashlib

sys.stdout.reconfigure(encoding="utf-8")
UA = {"User-Agent": "obl-archive/1.0 (preservation copy; github.com/original-bitcoin-laboratory)"}
SWH = "https://archive.softwareheritage.org/api/1"
HEAD = "5c085256f7dbfe999afbf10808828f0df9f877f1"
OUT = sys.argv[1] if len(sys.argv) > 1 else "svn-log.json"


def g(u, t=120):
    return urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=t)


url, allr = f"{SWH}/revision/{HEAD}/log/?limit=1000", []
while True:
    r = g(url)
    allr += json.loads(r.read())
    m = re.search(r'<([^>]+)>;\s*rel="next"', r.headers.get("Link", "") or "")
    if not m:
        break
    url = m.group(1)

rows = []
for r in allr:
    msg = (r.get("message") or "").strip().splitlines()
    rows.append({
        "rev": r["id"],
        "date": r["date"],
        "author": (r.get("author") or {}).get("name", "?"),
        "committer_date": r.get("committer_date"),
        "message": msg[0][:200] if msg else "",
    })
rows.sort(key=lambda x: x["date"])

print(f"  {len(rows)} revisions   {rows[0]['date'][:10]} .. {rows[-1]['date'][:10]}")
by = {}
for x in rows:
    by.setdefault(x["author"], []).append(x)
print("\n  committer            n     first                last")
print("  " + "-" * 68)
for a, v in sorted(by.items(), key=lambda x: -len(x[1])):
    print(f"  {a:18s} {len(v):4d}   {v[0]['date'][:19]}  {v[-1]['date'][:19]}")

s = by.get("s_nakamoto", [])
if s:
    print(f"\n  === s_nakamoto: {len(s)} commits ===")
    print(f"  first : {s[0]['date'][:19]}  {s[0]['message'][:56]}")
    print(f"  last  : {s[-1]['date'][:19]}  {s[-1]['message'][:56]}")
    tz = {}
    for x in s:
        t = x["date"][-6:]
        tz[t] = tz.get(t, 0) + 1
    print(f"  declared offsets: {tz}")

json.dump(rows, open(OUT, "w", encoding="utf-8"), indent=1)
print(f"\n  written: {OUT}  sha256={hashlib.sha256(open(OUT,'rb').read()).hexdigest()[:16]}…")
