#!/usr/bin/env python3
"""spent_patoshi.py — the ~1,145 Patoshi coinbases that were ever spent.

From patoshi_confirmed.csv, enumerate every high-confidence Patoshi coinbase with coinbase_spent==1,
characterize them, and write their heights to spent_patoshi_heights.txt (feed to judge.py). These are
the Patoshi coins that MOVED — the rest of the ~1.1M sits dormant.

The map "which spending tx (awakening) spent which coinbase" needs the spending-txid join
(acquire.sql Query C, or an outspends fetch per coinbase). The worked example is block 9 → the
block-9 spend chain (`spend_chain.py`). Grade: [forensic]. Run: python spent_patoshi.py
"""
import csv
from collections import Counter

def main():
    spent = []
    for r in csv.DictReader(open("patoshi_confirmed.csv", newline="")):
        if r["patoshi_confirmed"] == "1" and r["coinbase_spent"] == "1":
            spent.append(int(r["height"]))
    spent.sort()
    n = len(spent)
    print(f"spent high-confidence Patoshi coinbases: {n:,}  ({n*50:,} BTC moved)\n")

    # distribution by 5k band
    band = Counter(h//5000*5000 for h in spent)
    print("  by height band:")
    for b in sorted(band):
        print(f"    {b:>6}-{b+4999:<6}: {band[b]:4d}")
    print(f"\n  earliest 12 spent: {spent[:12]}")
    print(f"  latest 12 spent  : {spent[-12:]}")

    with open("spent_patoshi_heights.txt", "w") as f:
        f.write("\n".join(map(str, spent)) + "\n")
    print(f"\n  wrote spent_patoshi_heights.txt ({n:,} heights)")
    print(f"  feed to the verdict tool, e.g.:  python judge.py $(head -20 spent_patoshi_heights.txt)")
    print(f"  (each will rule PATOSHI + spent; block 9 is the worked spend chain in spend_chain.py)")

    print("\n  awakening -> coinbase map (which tx spent each): fetch-gated.")
    print("  run acquire.sql Query C (spending txid -> originating coinbase height) to resolve all;")
    print("  block 9 is done (spend_chain.py). The unspent complement (~1.1M BTC) is the dormant hoard.")

if __name__ == "__main__":
    main()
