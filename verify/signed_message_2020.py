"""The message signed with 145 early coinbase keys and published on 25 May 2020: every signature checked.

WHAT THIS CHECKS
----------------
On 25 May 2020 a text was published together with 145 lines of the form "<address> <signature>"
(paste.debian.net/plain/1148565). The archived copy used here is the Wayback Machine's capture of
that page at 2020-05-25 11:34:41 UTC, fetched as raw bytes and pinned by sha256 below.

For every line this script:
  1. runs the two structural checks of verify_signed_message.py (header byte, r on the curve);
  2. recovers the public key from the signature and the message, and compares its address with
     the address on the line;
  3. looks the address up among the coinbase outputs of blocks 0-60,000 (cb_outputs.csv), to find
     the block whose coinbase paid it;
  4. labels that block under two Patoshi classifications:
       A  this project's patoshi_confirmed.csv (nonce-LSB necessary, phi >= 0.5 sufficient);
       B  the deployed btc-rpc-explorer list (data/btc-rpc-explorer-patoshi.json, the snapshot
          patoshi_setdiff.py compares against).

The message text itself is not printed; its length and sha256 are, so a reader can confirm the
same bytes. Anyone can read it at the archived URL.

WHAT IT ESTABLISHES
-------------------
  - whether each signature verifies for its address over the published text;
  - which coinbase each signing key was first paid by, and when that block was mined;
  - how the two Patoshi classifications label those blocks.

WHAT IT DOES NOT ESTABLISH
--------------------------
  - who signed. A verifying signature shows that its maker held the key when signing, nothing
    about identity (see verify_signed_message.py);
  - that the keys are still held, or by whom;
  - anything about the statements in the text, which this project does not assess.

Run:  python verify/signed_message_2020.py [cache-dir]        (needs cb_outputs.csv, see README)
"""
import csv
import hashlib
import json
import os
import re
import sys
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import verify_signed_message as vsm  # noqa: E402
import resolve_coinbase_addresses as rca  # noqa: E402

SRC = "https://web.archive.org/web/20200525113441id_/https://paste.debian.net/plain/1148565"
SRC_SHA256 = "0bcad43befa311eec9c78eb946e622efcfbe987ba495f955cec81b43a8b92a7d"
UA = {"User-Agent": "satoshi-onchain-research/1.0"}


def fetch(cache_dir):
    os.makedirs(cache_dir, exist_ok=True)
    path = os.path.join(cache_dir, "paste-1148565.raw")
    if not os.path.exists(path):
        body = None
        for attempt in range(4):
            try:
                body = urllib.request.urlopen(urllib.request.Request(SRC, headers=UA), timeout=90).read()
                break
            except Exception:
                time.sleep(15 * (attempt + 1))
        if body is None:
            sys.exit("could not fetch the archived copy")
        with open(path, "wb") as fh:
            fh.write(body)
    raw = open(path, "rb").read()
    got = hashlib.sha256(raw).hexdigest()
    if got != SRC_SHA256:
        sys.exit("archived copy sha256 %s does not match the pinned %s" % (got, SRC_SHA256))
    return raw.decode("utf-8")


def parse(text):
    q1 = text.index('"')
    q2 = text.index('"', q1 + 1)
    message = text[q1 + 1:q2]
    pairs = []
    for ln in text[q2 + 1:].splitlines():
        parts = ln.split()
        if len(parts) == 2 and parts[0][0] in "1" and vsm.address_ok(parts[0])[0]:
            pairs.append((parts[0], parts[1]))
    return message, pairs


def main():
    cache = sys.argv[1] if len(sys.argv) > 1 else os.path.join(REPO, "signed-2020")
    text = fetch(cache)
    message, pairs = parse(text)
    m = message.encode("utf-8")
    print("archived copy: sha256 %s (matches the pinned value)" % SRC_SHA256)
    print("message: %d bytes, %d lines, sha256 %s (text not printed; read it at the archived URL)"
          % (len(m), message.count("\n") + 1, hashlib.sha256(m).hexdigest()))
    print("address/signature lines: %d" % len(pairs))

    ok = 0
    for addr, sig in pairs:
        if not all(passed for _, passed, _ in vsm.structural(sig)):
            print("  structural FAIL %s" % addr)
            continue
        _, recovered, err = vsm.recover(message, sig)
        if recovered == addr:
            ok += 1
        else:
            print("  does not verify for %s under this text (%s)" % (addr, err or recovered))
    print("signatures that verify for their address: %d of %d" % (ok, len(pairs)))

    cb = os.path.join(REPO, "cb_outputs.csv")
    if not os.path.exists(cb):
        print("\ncb_outputs.csv not present: block lookup skipped (see README, Query C)")
        return 0 if ok == len(pairs) else 1
    index = rca.build_address_index(cb)
    if index.get("1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa") != 0:
        sys.exit("control failed: block 0 does not map to the genesis address")
    ts = {}
    for r in csv.DictReader(open(os.path.join(REPO, "early_blocks_merged.csv"), encoding="utf-8")):
        if r["height"].isdigit():
            ts[int(r["height"])] = int(r["timestamp"])
    a_rows = rca.load_patoshi(os.path.join(REPO, "patoshi_confirmed.csv"))
    b_set = set(int(h) for h in json.load(open(os.path.join(REPO, "data", "btc-rpc-explorer-patoshi.json"),
                                                encoding="utf-8"))["block_heights"]["Patoshi"]["heights"])

    heights = []
    for addr, _ in pairs:
        h = index.get(addr)
        if h is None:
            print("  %s is not a coinbase output of blocks 0-60,000" % addr)
        else:
            heights.append(h)
    day = lambda h: time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime(ts[h])) if h in ts else "?"
    print("\nsigning addresses that are coinbase outputs: %d of %d" % (len(heights), len(pairs)))
    if heights:
        print("  lowest block %d (%s); highest block %d (%s)" % (min(heights), day(min(heights)),
                                                               max(heights), day(max(heights))))
    in_a = sorted(h for h in heights if rca.is_patoshi(a_rows.get(h)))
    in_b = sorted(h for h in heights if h in b_set)
    print("\nPatoshi labels of those blocks:")
    print("  A  this project (patoshi_confirmed.csv): %d  %s" % (len(in_a), in_a))
    print("  B  btc-rpc-explorer snapshot:            %d  %s" % (len(in_b), in_b))
    print("  labelled by both:                        %d  %s" % (len(set(in_a) & set(in_b)), sorted(set(in_a) & set(in_b))))
    print("\nA verifying signature shows its maker held the key when signing. It says nothing about who.")
    return 0 if ok == len(pairs) else 1


if __name__ == "__main__":
    sys.exit(main())
