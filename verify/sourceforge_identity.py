"""SourceForge account anchors for nakamoto2 / s_nakamoto.

Two server-set facts per account that have to agree with each other:
  Joined date  -- not user-editable
  User ID      -- assigned sequentially at account creation

A backdated Joined field would need an out-of-sequence ID, so checking IDs across accounts of the
era is an independent test of the dates. Layout note: pages captured before ~mid-2009 label the
field "Site Member Since"; later ones say "Joined".
"""
import urllib.request, json, re, sys, html, time

sys.stdout.reconfigure(encoding="utf-8")
UA = {"User-Agent": "obl-archive/1.0 (provenance check; github.com/original-bitcoin-laboratory)"}
CDX = "http://web.archive.org/cdx/search/cdx?url=sourceforge.net/users/{}&output=json&limit=1&from=2008&to=2013"
WB = "https://web.archive.org/web/{}if_/http://sourceforge.net:80/users/{}"


def get(u, t=90, tries=4):
    """The Wayback Machine returns transient 5xx under load; a single attempt is not reliable."""
    for n in range(tries):
        try:
            return urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=t).read()
        except Exception:
            if n == tries - 1:
                raise
            time.sleep(3 * (n + 1))


rows = []
for u in sys.argv[1:] or ["nakamoto2", "s_nakamoto", "nanotube", "dooglus"]:
    try:
        d = json.loads(get(CDX.format(u)))
        if len(d) < 2:
            print(f"  {u:14s} no capture in range"); continue
        t = re.sub(r"<script.*?</script>", "", get(WB.format(d[1][1], u)).decode("utf-8", "replace"),
                   flags=re.S | re.I)
        txt = re.sub(r"\|{2,}", "|", re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "|", t))))
        uid = (re.search(r"User ?ID:?\s*\|+\s*(\d+)", txt) or [None, None])[1]
        jd = (re.search(r"(?:Site Member Since|Joined):?\s*\|+\s*(\d{4}-\d{2}-\d{2})", txt) or [None, None])[1]
        if not (uid and jd):
            print(f"  {u:14s} fields not present in that capture ({d[1][1]}) -- layout predates them")
        else:
            print(f"  {u:14s} joined={jd}  id={uid}   (capture {d[1][1]})")
        if uid and jd:
            rows.append((int(uid), jd, u))
    except Exception as e:
        print(f"  {u:14s} {e}")

rows.sort()
mono = all(rows[i][1] <= rows[i + 1][1] for i in range(len(rows) - 1))
print(f"\n  IDs ascending -> join dates ascending: {mono}  (n={len(rows)})")
for i, d, u in rows:
    print(f"    {i:>9}  {d}  {u}")
sys.exit(0 if mono else 1)
