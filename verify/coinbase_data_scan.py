"""Scan every early coinbase -- scriptSig AND output script -- for a whitepaper commitment.

THE QUESTION. Did Satoshi ever commit a document to the chain? A signature over the whitepaper would
settle which file is the real one. Nothing in this project has ever found such an artifact, but the
claim "he never did" was resting on a partial sweep of scriptSigs fetched one block at a time from a
rate-limited API.

It does not need to. `early_blocks_merged.csv` already holds, locally, the coinbase scriptSig and the
coinbase output script for the whole Patoshi era. The sweep is a file scan, not a network job.

WHAT IS TESTED, in both fields:
  - the three known whitepaper sha256 values, in both byte orders
  - any 32-byte high-entropy push that COULD be a commitment to something
  - URL and text fragments
  - the capacity question: how many bytes were ever available to hold a 32-byte hash

WHAT A NEGATIVE MEANS. That no commitment is present in the coinbase channel across the scanned
range -- not that none exists anywhere. Non-coinbase transactions are a separate population and are
enumerated separately (`first_year_payments.csv`, 219 rows in the first year).

Usage:  python verify/coinbase_data_scan.py [--csv early_blocks_merged.csv]
"""
import argparse
import binascii
import collections
import csv
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

HASHES = {
    "b1674191a88ec5cdd733e4240a81803105dc412d6c6708d53ab94fc248f4f553": "canonical 24 Mar 2009",
    "427c63b364c6db914cf23072a09ffd53ee078397b7c6ab2d604e12865a982faa": "draft 3 Oct 2008",
    "e6cc7c952c688b234f9872c3e2f50060ae6556fd27925cba503c6460048e50a9": "11 Nov 2008 (not held)",
}
for _h, _l in list(HASHES.items()):
    HASHES[binascii.hexlify(binascii.unhexlify(_h)[::-1]).decode()] = _l + " (byte-reversed)"

TEXT = [b"http", b".pdf", b"bitcoin.org", b"whitepaper", b"white paper", b"sha256",
        b"nakamoto", b"upload.ae", b"ecash", b"electronic cash", b"paper"]

ap = argparse.ArgumentParser()
ap.add_argument("--csv", default="early_blocks_merged.csv")
a = ap.parse_args()

if not os.path.exists(a.csv):
    sys.exit(f"  !! {a.csv} not found -- run from the satoshi-onchain root")

sig_len = collections.Counter()
out_len = collections.Counter()
hash_hits, text_hits, big_pushes = [], [], []
first_over_32 = None
n = 0
control_ok = False

with open(a.csv, newline="", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        try:
            h = int(row["height"])
        except Exception:
            continue
        n += 1
        for field, counter in (("coinbase_script_hex", sig_len),
                               ("coinbase_output_script_hex", out_len)):
            hx = (row.get(field) or "").strip().lower()
            if not hx:
                continue
            try:
                raw = binascii.unhexlify(hx)
            except Exception:
                continue
            if field == "coinbase_script_hex":
                counter[len(raw)] += 1
                if h == 0 and b"The Times 03/Jan/2009" in raw:
                    control_ok = True
                if h != 0 and len(raw) > 32 and first_over_32 is None:
                    first_over_32 = (h, len(raw), raw)
            else:
                counter[len(raw)] += 1
            for hh, lbl in HASHES.items():
                if hh in hx:
                    hash_hits.append((h, field, lbl))
            low = raw.lower()
            for t in TEXT:
                if t in low:
                    text_hits.append((h, field, t.decode(), raw[:90]))
            # A 32-byte push, but ONLY where it can actually be one.
            #
            # The naive version of this -- regex for 0x20 followed by 32 bytes -- returned 6,505
            # "hits", every one of them a slice of a public key: a coinbase output script here is
            # 41 <65-byte pubkey> ac, and 0x20 occurs inside pubkeys by chance. A pattern match
            # inside a field whose structure you already know is not a finding.
            #
            # So: parse the script properly and only count a push that starts at offset 0 of a
            # scriptSig, or that follows a completed preceding push.
            if field == "coinbase_script_hex":
                i = 0
                while i < len(raw):
                    op = raw[i]
                    if op == 0x20 and i + 33 <= len(raw):
                        blob = raw[i + 1:i + 33]
                        if len(set(blob)) > 20:
                            big_pushes.append((h, field, blob.hex()))
                        i += 33
                    elif 1 <= op <= 75:
                        i += 1 + op
                    else:
                        i += 1

print(f"\n  scanned {n:,} blocks from {a.csv}")
print(f"  block-0 Times-headline control: {'OK' if control_ok else '*** FAILED ***'}")
if not control_ok:
    sys.exit("  aborting: the control failed, so a clean result would mean nothing")

print(f"\n  coinbase scriptSig length distribution:")
for ln, c in sorted(sig_len.items()):
    flag = "   <- could hold a 32-byte hash" if ln >= 32 else ""
    print(f"    {ln:5d} B : {c:6,d}{flag}")

print(f"\n  coinbase OUTPUT script length distribution:")
for ln, c in sorted(out_len.items())[:12]:
    print(f"    {ln:5d} B : {c:6,d}")

print(f"\n  ★ RESULTS")
print(f"    whitepaper-hash commitments found : {len(hash_hits)}")
for x in hash_hits:
    print(f"       block {x[0]}  {x[1]}  {x[2]}")
print(f"    text-probe hits                   : {len(text_hits)}")
for h_, fld, t, raw in text_hits[:10]:
    print(f"       block {h_}  {fld}  '{t}'  {raw!r}"[:150])
print(f"    32-byte high-entropy pushes       : {len(big_pushes)}")
for x in big_pushes[:10]:
    print(f"       block {x[0]}  {x[1]}  {x[2]}")

print(f"\n  ★ CAPACITY")
if first_over_32:
    h_, ln, raw = first_over_32
    print(f"    first scriptSig over 32 bytes (excluding block 0): height {h_:,} ({ln} B)")
    print(f"      {raw.decode('latin1', 'replace')!r}")
    print(f"    -> below height {h_:,}, a 32-byte commitment COULD NOT FIT.")
else:
    mx = max((ln for ln in sig_len if ln), default=0)
    print(f"    NO coinbase scriptSig in blocks 1-{n-1:,} exceeds 32 bytes.")
    print(f"    longest seen (incl. block 0): {mx} bytes")
    print(f"    -> across this entire range a 32-byte commitment COULD NOT HAVE BEEN THERE.")
    print(f"       Not 'not found' -- could not fit.")
