"""Preservation copy of the Satoshi <-> Martti Malmi ("Sirius") correspondence, 2009-2011.

Released by Malmi in February 2024 as evidence in COPA v Wright, where he was a witness. This is the
largest body of Satoshi's private correspondence in public, and unlike the mailing-list archive it
comes from the named counterparty rather than from a pseudonym.

Evidential class: released by an identified party and entered in court proceedings. That is stronger
than an anonymous claim and weaker than a server-recorded timestamp -- the dates are as Malmi's mail
client recorded them, not as an independent server stamped them. Treat accordingly.

Saves the source HTML alongside the parse so the parse can be audited against the bytes.
"""
import urllib.request, re, sys, os, json, html, hashlib

sys.stdout.reconfigure(encoding="utf-8")
UA = {"User-Agent": "obl-archive/1.0 (preservation copy; github.com/original-bitcoin-laboratory)"}
SRC = "https://mmalmi.github.io/satoshi/"
OUT = sys.argv[1] if len(sys.argv) > 1 else "malmi-satoshi"
os.makedirs(OUT, exist_ok=True)


def strip(h):
    h = re.sub(r"<br\s*/?>", "\n", h, flags=re.I)
    h = re.sub(r"<[^>]+>", "", h)
    return re.sub(r"\n{3,}", "\n\n", html.unescape(h)).replace("\xa0", " ").strip()


raw = urllib.request.urlopen(urllib.request.Request(SRC, headers=UA), timeout=180).read()
open(os.path.join(OUT, "source.html"), "wb").write(raw)
t = raw.decode("utf-8", "replace")
print(f"  fetched {len(raw):,} bytes")

# each message: <div class="message satoshi|sirius" id="email-N"> header divs + <pre> body
blocks = re.findall(r'<div class="message ([a-z]+)"[^>]*id="(email-\d+)"[^>]*>(.*?)</div>\s*(?=<div class="message|</body|$)',
                    t, re.S)
if not blocks:
    blocks = [(m.group(1), m.group(2), m.group(3)) for m in
              re.finditer(r'<div class="message ([a-z]+)"[^>]*id="(email-\d+)"[^>]*>(.*?)(?=<div class="message|</body)', t, re.S)]

msgs = []
for who, mid, body in blocks:
    hdr = {}
    # markup is: <div><strong>Date</strong>: Sat, 02 May 2009 18:06:58 +0100</div>
    for k in ("From", "To", "Date", "Subject"):
        m = re.search(r"<strong>" + k + r"</strong>\s*:\s*([^<]{0,300})", body)
        if m:
            hdr[k] = html.unescape(m.group(1)).strip()
    pre = re.search(r"<pre[^>]*>(.*?)</pre>", body, re.S)
    msgs.append({"id": mid, "who": who, **hdr, "body": strip(pre.group(1)) if pre else ""})

print(f"  parsed {len(msgs)} messages")
by = {}
for m in msgs:
    by[m["who"]] = by.get(m["who"], 0) + 1
print(f"  by sender class: {by}")
dated = [m for m in msgs if m.get("Date")]
if dated:
    print(f"  first: {dated[0].get('Date')}  {dated[0].get('Subject','')[:50]}")
    print(f"  last : {dated[-1].get('Date')}  {dated[-1].get('Subject','')[:50]}")
print(f"  bodies non-empty: {sum(1 for m in msgs if m['body'])}/{len(msgs)}")

json.dump(msgs, open(os.path.join(OUT, "emails.json"), "w", encoding="utf-8"), indent=1)
with open(os.path.join(OUT, "SHA256SUMS"), "w", encoding="utf-8", newline="\n") as f:
    for fn in sorted(os.listdir(OUT)):
        if fn == "SHA256SUMS":
            continue
        d = open(os.path.join(OUT, fn), "rb").read()
        f.write(f"{hashlib.sha256(d).hexdigest()}  {fn}\n")
print(f"  written: {OUT}/emails.json + source.html + SHA256SUMS")
