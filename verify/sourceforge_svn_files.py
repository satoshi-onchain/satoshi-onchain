"""Full file bodies for every SourceForge SVN revision, from Software Heritage.

The log alone (verify/sourceforge_svn_log.py) gives 252 server-set timestamps. This adds what each
revision actually contained: for every revision, the trunk tree with each file's content hash, and
the blob bodies themselves (content-addressed, so shared blobs are fetched once).

Result: the complete 2009-2011 source history that SourceForge itself no longer serves.
"""
import urllib.request, json, sys, os, time, hashlib

sys.stdout.reconfigure(encoding="utf-8")
UA = {"User-Agent": "obl-archive/1.0 (preservation copy; github.com/original-bitcoin-laboratory)"}
SWH = "https://archive.softwareheritage.org/api/1"
OUT = sys.argv[1] if len(sys.argv) > 1 else "sourceforge-bitcoin-svn"
os.makedirs(os.path.join(OUT, "blobs"), exist_ok=True)


def g(u, t=120, raw=False):
    """Retries with backoff; 429 (rate limit) gets a long sleep rather than aborting the run."""
    for attempt in range(8):
        try:
            r = urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=t).read()
            return r if raw else json.loads(r)
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < 7:
                wait = min(900, 60 * (attempt + 1))
                time.sleep(wait)
                continue
            if attempt == 7:
                raise
            time.sleep(5 * (attempt + 1))
        except Exception:
            if attempt == 7:
                raise
            time.sleep(5 * (attempt + 1))


def entries(d):
    return d if isinstance(d, list) else d.get("content", [])


revs = json.load(open(os.path.join(OUT, "svn-log.json"), encoding="utf-8"))
trees, blobs, fetched, skipped = {}, {}, 0, 0
for n, r in enumerate(revs, 1):
    try:
        root = entries(g(f"{SWH}/revision/{r['rev']}/directory/"))
    except Exception as e:
        print(f"  rev {r['rev'][:10]}: {e}"); continue
    tr = [e for e in root if e.get("name") == "trunk" and e.get("type") == "dir"]
    if not tr:
        continue
    files = entries(g(f"{SWH}/directory/{tr[0]['target']}/"))
    listing = []
    for f in files:
        if f.get("type") != "file":
            continue
        sha = f.get("target")
        listing.append({"name": f["name"], "length": f.get("length"), "sha1_git": sha})
        blobs[sha] = f["name"]
    trees[r["rev"]] = {"date": r["date"], "author": r["author"],
                       "message": r["message"], "files": listing}
    if n % 25 == 0:
        print(f"    {n}/{len(revs)} revisions, {len(blobs)} distinct blobs so far")

print(f"\n  {len(trees)} revisions mapped, {len(blobs)} distinct file blobs")
for sha, name in blobs.items():
    dest = os.path.join(OUT, "blobs", sha)
    if os.path.exists(dest) and os.path.getsize(dest) > 0:
        skipped += 1; continue
    try:
        open(dest, "wb").write(g(f"{SWH}/content/sha1_git:{sha}/raw/", raw=True))
        fetched += 1
        if fetched % 50 == 0:
            print(f"    fetched {fetched}/{len(blobs)}")
        time.sleep(0.15)
    except Exception as e:
        print(f"    FAIL {sha[:12]} {name}: {e}")

json.dump(trees, open(os.path.join(OUT, "trees.json"), "w", encoding="utf-8"), indent=1)
with open(os.path.join(OUT, "SHA256SUMS"), "w", encoding="utf-8", newline="\n") as f:
    for fn in sorted(os.listdir(os.path.join(OUT, "blobs"))):
        d = open(os.path.join(OUT, "blobs", fn), "rb").read()
        f.write(f"{hashlib.sha256(d).hexdigest()}  blobs/{fn}\n")
tot = sum(os.path.getsize(os.path.join(OUT, "blobs", x)) for x in os.listdir(os.path.join(OUT, "blobs")))
print(f"\n  blobs: fetched {fetched}, already had {skipped}, {tot:,} bytes")
print(f"  written: {OUT}/trees.json + blobs/ + SHA256SUMS")
