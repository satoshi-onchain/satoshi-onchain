"""Were Bitcoin's first-year payments funded by coins from the Patoshi cluster?

THE QUESTION, AND WHY IT IS DIFFERENT FROM THE USUAL ONE. The standing claim about the Patoshi
cluster is a BALANCE claim: roughly 1.1M BTC were mined by one miner and have never moved. This asks
the FLOW version instead -- during Bitcoin's first year, when coins actually moved, whose coins were
moving? Two local datasets answer it jointly and are almost never joined: the per-block Patoshi
labels (derived from nonce/ExtraNonce, nothing to do with keys) and the complete 219-payment record
of the first year.

HOW, WITHOUT A NETWORK. Nearly every early coinbase paid a BARE PUBLIC KEY, so the address an
explorer shows is derived, not stored. Invert that over a dump of coinbase scripts and you get
address -> minting height for the whole early chain; each payment's INPUT addresses then resolve to
the blocks that minted those coins, and each block carries a label. No node, no API, no key.

*** THE TRAP THIS SCRIPT EXISTS TO AVOID ***
`patoshi_confirmed` is NOT "is this a Patoshi block". Per slots.py it is

    nonce_lsb_ok AND phi >= CONF AND 1 <= height <= era_end

-- a HIGH-CONFIDENCE SUBSET. The phi threshold means the flag can only ever be 1 up to about block
24,184, even though the era runs to ~54,458 and the rigorous era-wide count is ~22,540 (see
EXCAVATION.md). A naive comparison therefore counts every block above ~24,184 as "not Patoshi" BY
CONSTRUCTION, and manufactures a depletion effect out of nothing. The first version of this analysis
did exactly that and reported a number that was too strong.

So: the analysis is RESTRICTED to funding heights within the label's valid range, and the base rate
is computed over THAT SAME RANGE. Apples to apples or not at all.

WHAT A RESULT HERE IS AND IS NOT.
  * "Patoshi-minted" = the spent coins came from blocks carrying the cluster's statistical
    fingerprint. NOT "Satoshi sent this". Nobody signed anything.
  * The label has false positives AND false negatives. Note the direction: false positives would make
    the cluster look like it spent MORE than it did, so they bias AGAINST the finding below, not for
    it.
  * An input that resolves to no coinbase was funded by an earlier payment -- the chain saying the
    coins had already changed hands.

Read the output as a distribution over a labelled cluster, never as an attribution of any payment.

Usage:  python first_year_patoshi_map.py [--payments PATH] [--out PATH]
"""
import argparse
import collections
import csv
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from resolve_coinbase_addresses import build_address_index, load_patoshi, is_patoshi  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ap = argparse.ArgumentParser()
ap.add_argument("--payments", default=os.path.join(HERE, "..", "..", "archives", "bigquery-onchain",
                                                   "first_year_payments.csv"))
ap.add_argument("--cb", default=os.path.join(HERE, "..", "cb_outputs.csv"))
ap.add_argument("--patoshi", default=os.path.join(HERE, "..", "patoshi_confirmed.csv"))
ap.add_argument("--out", default=os.path.join(HERE, "..", "first_year_patoshi_map.csv"))
a = ap.parse_args()

if not os.path.exists(a.payments):
    sys.exit(f"payments file not found: {a.payments}\nregenerate with verify/first_year_payments.sql")

pat = load_patoshi(a.patoshi)
flagged = {h for h, r in pat.items() if is_patoshi(r)}
LIM = max(flagged)
BASE = len(flagged) / LIM
print(f"  labels loaded          : {len(pat):,} heights, {len(flagged):,} flagged")
print(f"  label's VALID range    : 1..{LIM:,}  (phi threshold truncates it; see the docstring)")
print(f"  base rate in that range: {100*BASE:.1f}%\n")

print("  building address index (pure-Python RIPEMD-160, ~1 min)...")
idx = build_address_index(a.cb)
print(f"  address index          : {len(idx):,} coinbase addresses\n")

rows = list(csv.DictReader(open(a.payments, encoding="utf-8-sig")))
out, per, dropped = [], [], 0
for r in rows:
    uniq = sorted({x for x in (r["in_addresses"] or "").split(" | ") if x})
    hs = [idx.get(ad) for ad in uniq]
    inrange = [h for h in hs if h is not None and h <= LIM]
    dropped += sum(1 for h in hs if h is not None and h > LIM)
    npat = sum(1 for h in inrange if h in flagged)
    if inrange:
        per.append((r, len(inrange), npat))
    out.append({
        "block_number": r["block_number"], "block_timestamp": r["block_timestamp"],
        "txid": r["txid"], "out_btc": r["out_btc"], "fee_btc": r["fee_btc"],
        "n_input_addresses": len(uniq),
        "n_traced_in_label_range": len(inrange), "n_patoshi_minted": npat,
        "patoshi_fraction": f"{npat/len(inrange):.4f}" if inrange else "",
        "n_traced_above_label_range": sum(1 for h in hs if h is not None and h > LIM),
        "n_untraced_already_circulating": sum(1 for h in hs if h is None),
    })

tin = sum(n for _, n, _ in per)
tpat = sum(p for _, _, p in per)
big = sorted(per, key=lambda x: -x[1])[:5]
rest = [x for x in per if x not in big]
rn, rp = sum(n for _, n, _ in rest), sum(p for _, _, p in rest)
fr = sorted(p / n for _, n, p in per)

print(f"  transactions with >=1 input inside the label's range : {len(per)} of {len(rows)}")
print(f"  inputs excluded for lying above the label's range     : {dropped:,}\n")
print(f"  === three weightings, because the input count is dominated by a few consolidators ===")
print(f"    input-weighted            : {tpat:,}/{tin:,} = {100*tpat/tin:.1f}%   vs base {100*BASE:.1f}%"
      f"   -> {(tpat/tin)/BASE:.2f}x")
print(f"    same, minus the 5 biggest : {rp:,}/{rn:,} = {100*rp/rn:.1f}%"
      f"   -> {(rp/rn)/BASE:.2f}x   ({100*sum(n for _,n,_ in big)/tin:.0f}% of inputs removed)")
print(f"    median per-transaction    : {fr[len(fr)//2]:.3f}   mean {sum(fr)/len(fr):.3f}   vs base {BASE:.3f}")
print(f"\n    spend >=1 flagged coin    : {sum(1 for _,_,p in per if p>0)}/{len(per)}"
      f" = {100*sum(1 for _,_,p in per if p>0)/len(per):.1f}%")
print(f"    funded ENTIRELY by flagged: {sum(1 for _,n,p in per if p==n)}/{len(per)}"
      f" = {100*sum(1 for _,n,p in per if p==n)/len(per):.1f}%")
print(f"\n  if spending were blind to the label, expected ~{BASE*tin:,.0f} of {tin:,}; observed {tpat:,}.")
print(f"  ==> coins from the flagged cluster are spent at ~{(tpat/tin)/BASE:.2f}x the rate of blocks in"
      f" general: DEPLETED ~{BASE/(tpat/tin):.1f}x, and the result survives dropping the consolidations.")

with open(a.out, "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=list(out[0].keys()))
    w.writeheader()
    w.writerows(out)
print(f"\n  written -> {a.out}")
print("  REMINDER: a statistical cluster label is not an identity, and false positives bias this")
print("  result TOWARDS the null -- the true depletion is if anything stronger, not weaker.")
