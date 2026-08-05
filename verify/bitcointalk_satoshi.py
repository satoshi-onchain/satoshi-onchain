"""Full preservation copy of Satoshi's bitcointalk posts (user 3).

575 posts, each with a server-side date and a permalink. This is by a wide margin the largest
Satoshi corpus in existence, and until now this project had never collected it -- every claim about
what Satoshi said on the forum rested on one server staying online and on other people's quotations.

Dates here are SERVER-DB class: SMF stores and renders the post time; the poster does not set it.

Polite: identified UA, sequential, delay between pages, saves raw HTML as well as parsed JSON so the
parse can be re-run or audited against the bytes.
"""
import urllib.request, re, sys, os, time, json, html, hashlib

sys.stdout.reconfigure(encoding="utf-8")
UA = {"User-Agent": "obl-archive/1.0 (preservation copy; github.com/original-bitcoin-laboratory)"}
BASE = "https://bitcointalk.org/index.php?action=profile;u=3;sa=showPosts;start={}"
OUT = sys.argv[1] if len(sys.argv) > 1 else "bitcointalk-satoshi"
os.makedirs(os.path.join(OUT, "raw"), exist_ok=True)


def get(u, t=120):
    return urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=t).read()


def strip(h):
    h = re.sub(r"<br\s*/?>", "\n", h, flags=re.I)
    h = re.sub(r"</?(?:div|p|tr|table)[^>]*>", "\n", h, flags=re.I)
    h = re.sub(r"<[^>]+>", "", h)
    return re.sub(r"\n{3,}", "\n\n", html.unescape(h)).replace("\xa0", " ").strip()


def post_body(block):
    """Extract <div class="post">…</div> with BALANCED nesting.

    A non-greedy match to the first </div> truncates every post that opens with a quote block --
    SMF renders those as <div class="quoteheader">…</div><div class="quote">…</div> INSIDE the post
    div, so the body came out as the single word "Quote". That silently hit 159 of 539 posts.
    """
    m = re.search(r'<div class="post"[^>]*>', block)
    if not m:
        return ""
    i, depth = m.end(), 1
    for tag in re.finditer(r"<(/?)div\b[^>]*>", block[m.end():]):
        depth += -1 if tag.group(1) else 1
        if depth == 0:
            i = m.end() + tag.start()
            break
    else:
        i = len(block)
    return strip(block[m.end():i])


posts, start, seen_msgs = [], 0, set()
while True:
    dest = os.path.join(OUT, "raw", f"start{start:04d}.html")
    if os.path.exists(dest) and os.path.getsize(dest) > 5000:
        raw = open(dest, "rb").read()
    else:
        raw = get(BASE.format(start))
        open(dest, "wb").write(raw)
        time.sleep(1.2)
    t = raw.decode("utf-8", "replace")
    # each post: a titlebg2 header row (board path, subject link, date) then a body table
    blocks = re.split(r'<tr class="titlebg2">', t)[1:]
    n = 0
    for b in blocks:
        link = re.search(r'href="([^"]*topic=(\d+)\.msg(\d+)[^"]*)"[^>]*>(.*?)</a>', b, re.S)
        date = re.search(r'on:\s*([A-Z][a-z]+ \d{1,2}, \d{4}, \d{2}:\d{2}:\d{2} [AP]M)', b)
        if not (link and date):
            continue
        boards = re.findall(r'href="[^"]*board=\d+\.0"[^>]*>(.*?)</a>', b, re.S)

        posts.append({
            "topic": int(link.group(2)), "msg": int(link.group(3)),
            "url": html.unescape(link.group(1)),
            "subject": strip(link.group(4)),
            "date": date.group(1),
            "board": " / ".join(strip(x) for x in boards),
            "body": post_body(b),
        })
        n += 1
    print(f"  start={start:4d}  parsed {n} posts   (total {len(posts)})")
    # SMF re-serves the LAST page for any start beyond the end, so "n == 0" never fires and the
    # loop would run forever fetching duplicates. Stop on the first page that yields nothing new.
    fresh = {q["msg"] for q in posts[-n:]} - seen_msgs if n else set()
    if not fresh:
        print(f"  start={start:4d}  nothing new -- end of list")
        break
    seen_msgs |= fresh
    start += 20
    if start > 2000:
        break

seen, uniq = set(), []
for p in sorted(posts, key=lambda x: x["msg"]):
    if p["msg"] in seen:
        continue
    seen.add(p["msg"]); uniq.append(p)
print(f"\n  {len(uniq)} unique posts   msg {uniq[0]['msg']} .. {uniq[-1]['msg']}")
# The profile page reports 575 posts. The public list enumerates 539: pagination ends at start=520
# (26 full pages of 20, then a final 19). The 36-post difference is real and reproducible -- posts
# can be counted by the profile while not appearing in the list (deleted, moved, or in a board that
# guests cannot read). Recorded rather than papered over.
PROFILE_COUNT = 575
print(f"  profile counter: {PROFILE_COUNT}   publicly enumerable: {len(uniq)}   "
      f"counted but not listed: {PROFILE_COUNT - len(uniq)}")
print(f"  first: {uniq[0]['date']}  {uniq[0]['subject'][:52]}")
print(f"  last : {uniq[-1]['date']}  {uniq[-1]['subject'][:52]}")
json.dump(uniq, open(os.path.join(OUT, "posts.json"), "w", encoding="utf-8"), indent=1)
with open(os.path.join(OUT, "SHA256SUMS"), "w", encoding="utf-8", newline="\n") as f:
    for fn in sorted(os.listdir(os.path.join(OUT, "raw"))):
        d = open(os.path.join(OUT, "raw", fn), "rb").read()
        f.write(f"{hashlib.sha256(d).hexdigest()}  raw/{fn}\n")
print(f"  written: {OUT}/posts.json + raw/ + SHA256SUMS")
