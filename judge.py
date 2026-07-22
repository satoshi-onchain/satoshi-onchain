#!/usr/bin/env python3
"""judge.py -- is this coin Satoshi's? Verdict for any early block against the validated set.

Whenever a "Satoshi-era wallet just moved N BTC" headline appears, the honest question is:
was the coin's *coinbase block* Patoshi (Satoshi-attributed) or an ordinary early miner? This
reads slots.py's per-block output (patoshi_confirmed.csv) and answers for any height.

  python judge.py 9 170 2811                 # judge specific block heights
  python judge.py --file heights.csv         # heights in the first column
  python judge.py --demo                      # auto-pick one example of each verdict

Resolving a real awakening to heights: a Patoshi coin is a coinbase P2PK output, so a spend
consumes a coinbase directly -- the spending tx's input outpoint IS an early coinbase. Use
Query C in acquire.sql to turn a spending txid (or a funding address) into originating
coinbase height(s), then feed those heights here.

Verdicts (never over-claimed):
  GENESIS      height 0        -- Satoshi's by construction (Tier A, definitional).
  PATOSHI      confirmed set   -- Satoshi-attributed (Tier B, forensic; phi >= 0.5).
  AMBIGUOUS    LSB-pass, low phi -- passes the *necessary* condition but sits in the diluted
                                  zone; genuinely ~50/50 Patoshi vs ordinary miner.
  NOT PATOSHI  LSB-fail        -- fails the necessary nonce-LSB condition; an ordinary miner.
Attribution is [forensic], never [cryptographic]: no key here has ever signed.
"""
import csv, sys

SAT = 100_000_000


def load(path="patoshi_confirmed.csv"):
    try:
        rows = list(csv.DictReader(open(path, newline="")))
    except FileNotFoundError:
        sys.exit(f"missing {path} -- run:  python slots.py patoshi_labeled.csv")
    by_h = {}
    for r in rows:
        by_h[int(r["height"])] = {
            "height": int(r["height"]),
            "phi": float(r.get("phi", 0) or 0),
            "confirmed": r.get("patoshi_confirmed") == "1",
            "lsb": r.get("nonce_lsb_ok") == "1",
            "value": int(r.get("coinbase_value") or 5_000_000_000),
            "spent": r.get("coinbase_spent", "?"),
        }
    return by_h


def verdict(rec):
    h = rec["height"]
    if h == 0:
        return "GENESIS", "Satoshi's by construction (Tier A). 50 BTC, permanently unspendable."
    if rec["confirmed"]:
        return "PATOSHI", f"Satoshi-attributed (Tier B, forensic; phi={rec['phi']:.2f})."
    if rec["lsb"]:
        return "AMBIGUOUS", (f"passes the necessary nonce-LSB test but phi={rec['phi']:.2f} "
                             f"(diluted zone) -- ~50/50 Patoshi vs ordinary miner; not attributable.")
    return "NOT PATOSHI", "fails the necessary nonce-LSB condition -- an ordinary early miner, not Satoshi."


def dormancy(rec):
    return {"0": "UNSPENT (still dormant)", "1": "SPENT",
            "unspendable": "UNSPENDABLE (genesis)"}.get(rec["spent"], "unknown")


def judge_heights(by_h, heights):
    maxh = max(by_h)
    for h in heights:
        print("-" * 72)
        if h not in by_h:
            print(f"block {h:<8}  OUTSIDE acquired range (0..{maxh:,}). Extend the pull to judge it.")
            continue
        rec = by_h[h]
        v, why = verdict(rec)
        print(f"block {h:<8}  {v}")
        print(f"  {why}")
        print(f"  coinbase: {rec['value']/SAT:.0f} BTC   status: {dormancy(rec)}")
        if v == "PATOSHI" and rec["spent"] == "1":
            print(f"  NOTE: a *confirmed-Patoshi* coinbase that WAS spent -- rare and historic "
                  f"(e.g. block 9 -> Hal Finney, block 170). Genuine Satoshi movement.")
        if v == "PATOSHI" and rec["spent"] == "0":
            print(f"  If this ever moves, it would be the first Satoshi-cluster spend in 15+ years.")
        if v == "NOT PATOSHI":
            print(f"  A headline calling this 'Satoshi' is wrong: the fingerprint says ordinary miner.")
    print("-" * 72)


def demo(by_h):
    era = [r for r in by_h.values() if 1 <= r["height"] <= 54458]
    pick = {
        "genesis": 0,
        "Patoshi, spent (the famous one)": min((r["height"] for r in era if r["confirmed"] and r["spent"] == "1"), default=None),
        "Patoshi, still dormant": min((r["height"] for r in era if r["confirmed"] and r["spent"] == "0"), default=None),
        "ambiguous (LSB-pass, low phi)": next((r["height"] for r in sorted(era, key=lambda x: -x["height"]) if r["lsb"] and not r["confirmed"]), None),
        "not Patoshi (LSB-fail, early)": min((r["height"] for r in era if not r["lsb"]), default=None),
    }
    print("DEMO -- one real block of each verdict (auto-selected from the data):\n")
    for label, h in pick.items():
        if h is None:
            continue
        print(f"[{label}]")
        judge_heights(by_h, [h])
        print()


def main():
    args = sys.argv[1:]
    by_h = load()
    if not args or "--demo" in args:
        demo(by_h)
        if not args:
            print("Tip: python judge.py <height> [<height> ...]   or   --file heights.csv")
        return
    if args[0] == "--file":
        heights = [int(row[0]) for row in csv.reader(open(args[1])) if row and row[0].strip().lstrip("-").isdigit()]
    else:
        heights = [int(a) for a in args if a.lstrip("-").isdigit()]
    judge_heights(by_h, heights)


if __name__ == "__main__":
    main()
