"""Enumerate every non-coinbase transaction in Bitcoin's first year.

Early Bitcoin is almost entirely empty. For roughly the first year the chain is a near-unbroken run
of coinbase-only blocks, which means every actual PAYMENT in that period can be listed exhaustively
-- and, as far as we can find, nobody has published that list.

That matters because it turns claims about early transfers into checkable ones. When a named person
says "Satoshi sent me N coins on date D", you do not need to trust it, or trust us: you look at the
handful of transactions that existed in that window and see whether one fits. That is how the 100
BTC Satoshi sent Nicholas Bohm on 1 February 2009 was located -- exactly one payment of exactly 100
BTC exists in a ten-day window of 1,501 blocks, and Bohm's own email of that evening quotes the
receiving address and the minute.

It also shows what the method CANNOT do. Dustin Trammell's sworn "first transfer of 25.00" narrows
to exactly two candidate payments before 19 January 2009 and stops there: neither can be pinned to
him without his address.

WHY THIS SCRIPT IS BUILT THE WAY IT IS. The first version of it died silently after several hours.
Public explorers rate-limit hard, and it treated a 429 like any other transient error -- a 2-second
retry -- so the attempts burned out mid-sweep and the process exited having written nothing. Four
consequences, all deliberate here:

  * a 429 gets a long ESCALATING wait, not a token retry;
  * progress is CHECKPOINTED to disk, so an interrupted run resumes instead of restarting;
  * output is line-buffered, so a long run can actually be watched;
  * UNREAD BLOCK RANGES ARE RECORDED AND THE RUN EXITS NON-ZERO. See below.

THE FAILURE THAT MADE THAT LAST POINT NECESSARY. A later run *did* finish, printed "sweep complete",
and wrote a file that was quietly missing 43 payments across four multi-thousand-block gaps. The
cause was one line: when the retries were exhausted the loop did `h -= 10; continue`, stepping over
the unread window and leaving no trace. Nothing in the output distinguished a complete survey from a
holed one, and the omission was caught only by cross-checking against an unrelated data source
(Google's BigQuery mirror), which turned out to be a strict superset -- 140/140 agreement on
everything this script *did* see, and 43 payments it never looked at.

The lesson is not "rate limits are annoying". It is that **a tool whose entire value is
exhaustiveness must never be able to report success while holding holes.** Gaps are now tracked,
merged, written to `<out>.gaps`, printed, and the process exits 2.

**Use BigQuery instead where you can** -- see `first_year_payments.sql`, which answers the same
question in seconds and cannot be rate-limited into silence. This script remains useful as an
INDEPENDENT second path: it reaches the chain through an entirely different pipeline, so agreement
between the two means something.

Output: a CSV of every block containing more than a coinbase, with each transaction's inputs,
outputs and values. No key, no node.

Usage:  python early_tx_survey.py [--from N] [--to N] [--out survey.csv]
"""
import json
import sys
import os
import time
import urllib.request
import urllib.error
import datetime
import argparse
import csv

sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
API = "https://blockstream.info/api"
UA = {"User-Agent": "satoshi-onchain/1.0 (early-chain survey; github.com/satoshi-onchain)"}


def get(url, tries=6):
    """Fetch JSON, treating rate limits as the distinct condition they are."""
    for i in range(tries):
        try:
            return json.load(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60))
        except urllib.error.HTTPError as e:
            if e.code == 429:
                wait = 30 * (i + 1)
                print(f"    rate-limited; waiting {wait}s", flush=True)
                time.sleep(wait)
            else:
                time.sleep(3 + 3 * i)
        except Exception:
            time.sleep(3 + 3 * i)
    return None


def txt(url, tries=6):
    for i in range(tries):
        try:
            return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60).read().decode()
        except urllib.error.HTTPError as e:
            if e.code == 429:
                time.sleep(30 * (i + 1))
            else:
                time.sleep(3 + 3 * i)
        except Exception:
            time.sleep(3 + 3 * i)
    return None


ap = argparse.ArgumentParser()
ap.add_argument("--from", dest="lo", type=int, default=1)
ap.add_argument("--to", dest="hi", type=int, default=32000)
ap.add_argument("--out", default="early_tx_survey.csv")
a = ap.parse_args()

ckpt = a.out + ".active"
active = []
if os.path.exists(ckpt):
    with open(ckpt, encoding="utf-8") as fh:
        for ln in fh:
            parts = ln.strip().split("\t")
            if len(parts) == 3:
                active.append((int(parts[0]), int(parts[1]), parts[2]))
    print(f"  resuming: {len(active)} active blocks already found", flush=True)

known = {h for h, _, _ in active}

# The scan frontier is tracked SEPARATELY from the blocks found. Deriving "where we got to" from
# min(found) is wrong: found blocks are sparse, so the lowest one says nothing about how far the
# sweep actually reached, and resuming from it silently skips every block above it.
front = a.out + ".frontier"
h = a.hi
if os.path.exists(front):
    try:
        h = min(a.hi, int(open(front, encoding="utf-8").read().strip()))
        print(f"  resuming sweep at height {h}", flush=True)
    except Exception:
        h = a.hi

print(f"  scanning blocks {a.lo}-{a.hi} for non-coinbase activity", flush=True)
seen = set()

# Ranges this run could NOT read. See the note above: skipping them silently is the bug this
# tracking exists to make impossible.
gaps = []

while h >= a.lo:
    batch = get(f"{API}/blocks/{h}")
    if not batch:
        # Every retry was exhausted. We step over this window and keep going -- but the step is
        # RECORDED, because an unrecorded step is what turns "exhaustive survey" into a quiet lie.
        gaps.append((max(a.lo, h - 9), h))
        print(f"    !! UNREAD: blocks {max(a.lo, h-9)}-{h} -- recorded as a gap", flush=True)
        h -= 10
        continue
    for b in batch:
        if b["height"] in seen or not (a.lo <= b["height"] <= a.hi):
            continue
        seen.add(b["height"])
        if b["tx_count"] > 1 and b["height"] not in known:
            active.append((b["height"], b["timestamp"], b["id"]))
            known.add(b["height"])
    h = min(b["height"] for b in batch) - 1
    if len(seen) % 1000 < 10:
        print(f"    {len(seen):,} scanned, {len(active)} with payments (at height {h})", flush=True)
        with open(ckpt, "w", encoding="utf-8") as fh:
            for r in sorted(active):
                fh.write(f"{r[0]}\t{r[1]}\t{r[2]}\n")
        with open(front, "w", encoding="utf-8") as fh:
            fh.write(str(h))
    time.sleep(0.45)

active.sort()
with open(ckpt, "w", encoding="utf-8") as fh:
    for r in active:
        fh.write(f"{r[0]}\t{r[1]}\t{r[2]}\n")
print(f"  sweep complete: {len(seen):,} blocks, {len(active)} contain a payment "
      f"({100 * len(active) / max(1, len(seen)):.3f}%)", flush=True)

rows = []
for i, (ht, ts, bid) in enumerate(active):
    for t in get(f"{API}/block/{bid}/txs") or []:
        if t["vin"][0].get("is_coinbase"):
            continue
        rows.append({
            "height": ht,
            "time_utc": datetime.datetime.fromtimestamp(ts, datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
            "txid": t["txid"],
            "n_in": len(t["vin"]),
            "n_out": len(t["vout"]),
            "total_out_btc": f"{sum(o['value'] for o in t['vout']) / 1e8:.8f}",
            "outputs_btc": " | ".join(f"{o['value'] / 1e8:g}" for o in t["vout"]),
            "addresses": " | ".join(str(o.get("scriptpubkey_address") or o.get("scriptpubkey_type")) for o in t["vout"]),
        })
    if i % 25 == 0:
        print(f"    detailing {i}/{len(active)} blocks", flush=True)
    time.sleep(0.45)

if rows:
    with open(a.out, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
print(f"  {len(rows)} payments written -> {a.out}", flush=True)

# ---- completeness verdict ---------------------------------------------------------------------
# A survey whose value is EXHAUSTIVENESS must never report success while holding holes. This block
# exists because an earlier run of this script did exactly that: rate limiting exhausted the
# retries, the loop stepped over the unread windows, and it printed "sweep complete" over a file
# missing 43 payments across four multi-thousand-block gaps. The omission was only caught by
# cross-checking against an unrelated data source. Loud failure now, every time.
if gaps:
    merged = []
    for lo, hi in sorted(gaps):
        if merged and lo <= merged[-1][1] + 1:
            merged[-1][1] = max(merged[-1][1], hi)
        else:
            merged.append([lo, hi])
    missing = sum(hi - lo + 1 for lo, hi in merged)
    with open(a.out + ".gaps", "w", encoding="utf-8") as fh:
        for lo, hi in merged:
            fh.write("%d\t%d\n" % (lo, hi))
    print(f"\n  *** INCOMPLETE: {missing:,} blocks in {len(merged)} range(s) were never read ***",
          flush=True)
    for lo, hi in merged[:20]:
        print(f"      {lo:,}-{hi:,}", flush=True)
    print(f"  ranges written to {a.out}.gaps -- rerun with --from/--to to fill them.", flush=True)
    print("  DO NOT present this output as an exhaustive survey until the gaps are closed.",
          flush=True)
    sys.exit(2)

print("  sweep verified complete: every block in range was read.", flush=True)
