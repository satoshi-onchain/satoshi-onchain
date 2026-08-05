"""Full preservation copy of the cryptography@metzdowd.com pipermail archive.

Why: every anchored date this lab cites for Satoshi's 18 messages rests on this one server. It is a
single point of failure for the most important evidence in the corpus. The gzipped monthly mboxes
carry FULL headers -- Message-ID, sender Date with timezone, the mbox From_ line written by the list
server -- which the rendered HTML strips.

Polite: identified User-Agent, sequential, delay between requests, skips anything already fetched.
"""
import urllib.request, re, sys, os, time, gzip, hashlib, json

sys.stdout.reconfigure(encoding="utf-8")

BASE = "https://www.metzdowd.com/pipermail/cryptography"
OUT = sys.argv[1] if len(sys.argv) > 1 else "metzdowd-cryptography"
UA = "obl-archive/1.0 (preservation copy; contact via github.com/original-bitcoin-laboratory)"

os.makedirs(os.path.join(OUT, "mbox"), exist_ok=True)
os.makedirs(os.path.join(OUT, "index"), exist_ok=True)


def get(url, timeout=120):
    return urllib.request.urlopen(
        urllib.request.Request(url, headers={"User-Agent": UA}), timeout=timeout
    ).read()


# ---- index -------------------------------------------------------------------------------
idx = get(f"{BASE}/").decode("utf-8", "replace")
open(os.path.join(OUT, "index", "archive-index.html"), "w", encoding="utf-8").write(idx)
gzs = sorted(set(re.findall(r'href="([^"]*\.txt\.gz)"', idx)))
print(f"  archive index saved; {len(gzs)} monthly mboxes listed")

manifest = []
ok = skip = fail = 0
for i, name in enumerate(gzs, 1):
    name = name.split("/")[-1]
    dest = os.path.join(OUT, "mbox", name)
    if os.path.exists(dest) and os.path.getsize(dest) > 0:
        skip += 1
        raw = open(dest, "rb").read()
    else:
        try:
            raw = get(f"{BASE}/{name}")
            open(dest, "wb").write(raw)
            ok += 1
            time.sleep(0.4)
        except Exception as e:
            print(f"    FAIL {name}: {e}")
            fail += 1
            continue
    try:
        text = gzip.decompress(raw).decode("utf-8", "replace")
        # pipermail OBFUSCATES the address: "From satoshi at vistomail.com  Fri Oct 31 ...".
        # Requiring "@" here counts zero. Requiring only "^From " over-counts by 67 -- body lines
        # that begin with "From " and were never escaped. Match the full From_ shape.
        msgs = len(re.findall(r"^From \S+ (?:at|@) \S+  \w{3} \w{3}", text, re.M))
    except Exception:
        text, msgs = "", -1
    manifest.append({
        "file": name,
        "bytes": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "messages": msgs,
    })
    if i % 40 == 0:
        print(f"    {i}/{len(gzs)} …")

print(f"\n  fetched {ok}, already present {skip}, failed {fail}")
total = sum(m["bytes"] for m in manifest)
msgs = sum(m["messages"] for m in manifest if m["messages"] > 0)
print(f"  {len(manifest)} mboxes, {total:,} bytes, ~{msgs:,} messages")

json.dump(manifest, open(os.path.join(OUT, "MANIFEST.json"), "w", encoding="utf-8"), indent=1)
with open(os.path.join(OUT, "SHA256SUMS"), "w", encoding="utf-8", newline="\n") as f:
    for m in sorted(manifest, key=lambda x: x["file"]):
        f.write(f"{m['sha256']}  mbox/{m['file']}\n")
print(f"  MANIFEST.json + SHA256SUMS written to {OUT}/")
