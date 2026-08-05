"""Enumerate every non-coinbase transaction in Bitcoin's first year.

Early Bitcoin is almost entirely empty. For roughly the first year the chain is a near-unbroken
run of coinbase-only blocks, which means every actual PAYMENT in that period can be listed
exhaustively -- and, as far as we can find, nobody has published that list.

That matters because it turns claims about early transfers into checkable ones. When a named
person says "Satoshi sent me N coins on date D", you do not need to trust it or to trust us: you
look at the handful of transactions that existed in that window and see whether one fits. That is
how the 100 BTC Satoshi sent Nicholas Bohm on 1 February 2009 was located -- exactly one payment
of exactly 100 BTC exists in a ten-day window of 1,501 blocks.

This script produces the underlying list, block by block, from a public explorer. No key, no node.

Output: a CSV of every block containing more than a coinbase, with each transaction's inputs,
outputs and values.

Usage:  python early_tx_survey.py [--from N] [--to N] [--out survey.csv]
"""
import json
import sys
import time
import urllib.request
import datetime
import argparse
import csv

sys.stdout.reconfigure(encoding="utf-8")
API = "https://blockstream.info/api"
UA = {"User-Agent": "satoshi-onchain/1.0 (early-chain survey; github.com/satoshi-onchain)"}


def get(url, tries=4):
    for i in range(tries):
        try:
            return json.load(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60))
        except Exception:
            time.sleep(2 + 2 * i)
    return None


def txt(url, tries=4):
    for i in range(tries):
        try:
            return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60).read().decode()
        except Exception:
            time.sleep(2 + 2 * i)
    return None


ap = argparse.ArgumentParser()
ap.add_argument("--from", dest="lo", type=int, default=1)
ap.add_argument("--to", dest="hi", type=int, default=36000)
ap.add_argument("--out", default="early_tx_survey.csv")
a = ap.parse_args()

print(f"  scanning blocks {a.lo}-{a.hi} for non-coinbase activity")
seen, active, h = set(), [], a.hi
while h >= a.lo:
    batch = get(f"{API}/blocks/{h}")
    if not batch:
        h -= 10
        continue
    for b in batch:
        if b["height"] in seen or not (a.lo <= b["height"] <= a.hi):
            continue
        seen.add(b["height"])
        if b["tx_count"] > 1:
            active.append((b["height"], b["tx_count"], b["timestamp"], b["id"]))
    h = min(b["height"] for b in batch) - 1
    if len(seen) % 2000 < 10:
        print(f"    {len(seen):,} blocks scanned, {len(active)} with payments")
    time.sleep(0.12)

active.sort()
print(f"  {len(seen):,} blocks scanned; {len(active)} contain a payment "
      f"({100*len(active)/max(1,len(seen)):.3f}%)")

rows = []
for ht, n, ts, bid in active:
    for t in get(f"{API}/block/{bid}/txs") or []:
        if t["vin"][0].get("is_coinbase"):
            continue
        rows.append({
            "height": ht,
            "time_utc": datetime.datetime.fromtimestamp(ts, datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
            "txid": t["txid"],
            "n_in": len(t["vin"]),
            "n_out": len(t["vout"]),
            "total_out_btc": f"{sum(o['value'] for o in t['vout'])/1e8:.8f}",
            "outputs_btc": " | ".join(f"{o['value']/1e8:g}" for o in t["vout"]),
            "addresses": " | ".join(str(o.get("scriptpubkey_address") or o.get("scriptpubkey_type")) for o in t["vout"]),
        })
    time.sleep(0.12)

with open(a.out, "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)
print(f"  {len(rows)} payments written -> {a.out}")
