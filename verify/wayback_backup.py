"""Preservation copies of Satoshi-era pages held only by the Internet Archive.

Same reasoning as the metzdowd backup: several anchors in this lab currently depend on one archive
staying online and one URL continuing to resolve. This pulls the ORIGINAL bytes (the `if_` suffix,
which omits the Archive's toolbar wrapper) for every capture of a target, hashes them, and writes a
manifest.

Targets are pages that carry server-recorded facts we cite:
  - sourceforge.net/users/{nakamoto2,s_nakamoto}   Joined dates + sequential user IDs
  - sourceforge.net/projects/bitcoin/              the activity feed naming who did what
  - showfiles.php?group_id=244765                  the "Research Paper" -> bitcoin.pdf release row
  - bitcoin.sourceforge.net/*                      the project's own site
  - p2pfoundation.ning.com/profile/SatoshiNakamoto the profile

Polite: identified UA, sequential, delay between fetches, skips what it already has.
"""
import urllib.request, urllib.parse, json, os, sys, time, hashlib, re

sys.stdout.reconfigure(encoding="utf-8")
UA = {"User-Agent": "obl-archive/1.0 (preservation copy; github.com/original-bitcoin-laboratory)"}
OUT = sys.argv[1] if len(sys.argv) > 1 else "wayback-satoshi-pages"
TARGETS = sys.argv[2:] or [
    "sourceforge.net/users/nakamoto2",
    "sourceforge.net/users/s_nakamoto",
    "sourceforge.net/projects/bitcoin/",
    "sourceforge.net/project/showfiles.php?group_id=244765",
    "bitcoin.sourceforge.net",
    "bitcoin.sourceforge.net/*",
    "p2pfoundation.ning.com/profile/SatoshiNakamoto",
]
CDX = ("http://web.archive.org/cdx/search/cdx?url={}&output=json"
       "&from=2008&to=2012&collapse=digest&filter=statuscode:200&limit=400")


def get(u, t=120):
    return urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=t).read()


os.makedirs(os.path.join(OUT, "pages"), exist_ok=True)
manifest, ok, skip, fail = [], 0, 0, 0
for tgt in TARGETS:
    try:
        rows = json.loads(get(CDX.format(urllib.parse.quote(tgt, safe=""))))
    except Exception as e:
        print(f"  {tgt}: CDX {e}"); continue
    if len(rows) < 2:
        print(f"  {tgt}: no captures"); continue
    print(f"  {tgt}: {len(rows)-1} captures")
    for ts, orig, mime, code, digest, length in ((r[1], r[2], r[3], r[4], r[5], r[6]) for r in rows[1:]):
        name = re.sub(r"[^A-Za-z0-9._-]", "_", f"{ts}_{orig}")[:150]
        dest = os.path.join(OUT, "pages", name)
        if os.path.exists(dest) and os.path.getsize(dest) > 0:
            skip += 1; raw = open(dest, "rb").read()
        else:
            try:
                raw = get(f"https://web.archive.org/web/{ts}if_/{orig}")
                open(dest, "wb").write(raw); ok += 1; time.sleep(0.5)
            except Exception as e:
                print(f"     FAIL {ts} {orig[:60]}: {e}"); fail += 1; continue
        manifest.append({"file": name, "target": tgt, "timestamp": ts, "url": orig,
                         "mimetype": mime, "bytes": len(raw),
                         "sha256": hashlib.sha256(raw).hexdigest()})

print(f"\n  fetched {ok}, already present {skip}, failed {fail}")

# MERGE with any existing manifest. Running this with a subset of targets (e.g. to retry one that
# failed) must not silently drop every other target's entries from the manifest and SHA256SUMS.
mpath = os.path.join(OUT, "MANIFEST.json")
if os.path.exists(mpath):
    prior = {m["file"]: m for m in json.load(open(mpath, encoding="utf-8"))}
    prior.update({m["file"]: m for m in manifest})
    # drop entries whose file no longer exists on disk
    manifest = [m for m in prior.values() if os.path.exists(os.path.join(OUT, "pages", m["file"]))]
    manifest.sort(key=lambda x: x["file"])
print(f"  {len(manifest)} pages, {sum(m['bytes'] for m in manifest):,} bytes")
json.dump(manifest, open(os.path.join(OUT, "MANIFEST.json"), "w", encoding="utf-8"), indent=1)
with open(os.path.join(OUT, "SHA256SUMS"), "w", encoding="utf-8", newline="\n") as f:
    for m in sorted(manifest, key=lambda x: x["file"]):
        f.write(f"{m['sha256']}  pages/{m['file']}\n")
print(f"  MANIFEST.json + SHA256SUMS written to {OUT}/")
