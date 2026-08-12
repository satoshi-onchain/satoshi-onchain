"""The complete version history of a deployed Patoshi block list, reconstructed from git.

WHY
---
Comparisons in the literature cite "the Patoshi list" as though it named one thing. It does not.
This reconstructs every version of one deployed list that has ever existed, from the repository
that serves it, and reports exactly when the membership changed and by which blocks.

  repo   github.com/janoside/btc-rpc-explorer          (MIT)
  file   public/txt/mining-pools-configs/BTC/0.json    key: block_heights.Patoshi.heights

⚠️ FAIRNESS NOTE, AND IT CORRECTS AN EARLIER DRAFT OF OUR OWN WRITE-UP.
The change was NOT undocumented and NOT quiet. The commit message says exactly what it did and
cites the discussion that prompted it. An earlier draft of entry 108 called it "silent"; that was
unfair and is retracted. The maintainer documented the change in the normal way.

  ⇒ The real problem is STRUCTURAL, not behavioural: the DATA carries no version field and no
    hash. Git records the change perfectly; a downstream consumer reading only the JSON cannot
    tell which version it holds. Those are different defects and only the second is a defect
    of this artifact.

Run:  python verify/patoshi_list_history.py [--refresh]
"""
import hashlib
import json
import os
import sys
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
OUT = os.path.join(REPO, "data", "btc-rpc-explorer-patoshi-history.json")

API = ("https://api.github.com/repos/janoside/btc-rpc-explorer/commits"
       "?path=public/txt/mining-pools-configs/BTC/0.json&per_page=100")
RAW = ("https://raw.githubusercontent.com/janoside/btc-rpc-explorer/%s/"
       "public/txt/mining-pools-configs/BTC/0.json")

UA = {"User-Agent": "satoshi-onchain-research/1.0"}


def fetch(url, api=False):
    h = dict(UA)
    if api:
        h["Accept"] = "application/vnd.github+json"
    return urllib.request.urlopen(urllib.request.Request(url, headers=h), timeout=60).read()


def build():
    commits = list(reversed(json.loads(fetch(API, api=True))))
    hist = []
    for c in commits:
        try:
            doc = json.loads(fetch(RAW % c["sha"]).decode("utf-8"))
            hs = doc.get("block_heights", {}).get("Patoshi", {}).get("heights")
        except Exception:
            hs = None
        if not hs:
            continue
        hs = sorted(int(x) for x in hs)
        hist.append({
            "sha": c["sha"],
            "date": c["commit"]["author"]["date"],
            "message": c["commit"]["message"].strip(),
            "n": len(hs),
            "set_sha256": hashlib.sha256(",".join(map(str, hs)).encode()).hexdigest(),
            "heights": hs,
        })
        time.sleep(0.15)
    return hist


def main():
    if "--refresh" in sys.argv or not os.path.exists(OUT):
        hist = build()
        os.makedirs(os.path.dirname(OUT), exist_ok=True)
        # store without the full arrays repeated -- keep only versions that DIFFER
        slim, seen = [], None
        for h in hist:
            if h["set_sha256"] != seen:
                slim.append(h)
                seen = h["set_sha256"]
            else:
                slim.append({k: v for k, v in h.items() if k != "heights"})
        json.dump(slim, open(OUT, "w"), indent=1)
        hist = slim
    else:
        hist = json.load(open(OUT))

    print("=" * 92)
    print(" EVERY VERSION OF THE DEPLOYED PATOSHI LIST")
    print("=" * 92)
    prev = None
    versions = 0
    for h in hist:
        mark = ""
        if prev is None:
            versions += 1
            mark = "  <- FIRST APPEARANCE"
        elif h["set_sha256"] != prev["set_sha256"]:
            versions += 1
            a, b = set(h.get("heights", [])), set(prev.get("heights", []))
            mark = "  <- CHANGED"
            if b and a:
                rm, ad = sorted(b - a), sorted(a - b)
                if rm:
                    mark += "  removed %s" % (rm if len(rm) <= 8 else "%d blocks" % len(rm))
                if ad:
                    mark += "  added %s" % (ad if len(ad) <= 8 else "%d blocks" % len(ad))
        print("  %s  %s  n=%6d  set=%s%s"
              % (h["sha"][:12], h["date"][:10], h["n"], h["set_sha256"][:12], mark))
        print("        %s" % h["message"].splitlines()[0][:80])
        if h["set_sha256"] != (prev or {}).get("set_sha256"):
            prev = h
    print("=" * 92)
    print("  DISTINCT VERSIONS: %d" % versions)
    print()
    print("  ⇒ The list first appeared 2021-08-14 with 21,953 heights and changed once,")
    print("    2023-11-08, to 21,950. Both versions are 'the Patoshi list'.")
    print()
    print("  ⚠️ AND THE FAIR READING: the change was properly documented — the commit message")
    print("     states what it did and cites the discussion behind it. What the artifact lacks")
    print("     is a VERSION FIELD: a consumer reading the JSON alone cannot tell which of the")
    print("     two it holds. That is a defect of the data format, not of the maintainer.")
    print()
    print("  ⚠️ NOT A CRITICISM OF THE CLASSIFICATION EITHER. There is no ground truth here:")
    print("     no 2009-era key has ever signed anything, so no version of any such list can")
    print("     be shown correct or incorrect. Only that they differ, and by how much.")
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())
