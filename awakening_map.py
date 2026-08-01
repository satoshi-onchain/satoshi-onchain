#!/usr/bin/env python3
"""awakening_map.py — join Query E's spent_map.csv to the Patoshi labels.

INPUT (from BigQuery Query E, exported here): spent_map.csv with columns
  coinbase_height, coinbase_txid, spending_txid, spending_height, spending_time
Reads patoshi_confirmed.csv for the labels; emits the ~1,145 Patoshi awakenings:
which spending tx moved which Patoshi coinbase, and when. No interpretation.

  python awakening_map.py        # -> patoshi_awakenings.csv + summary
"""
import csv, sys
from datetime import datetime, timezone

def main():
    try:
        rows = list(csv.DictReader(open("spent_map.csv", newline="")))
    except FileNotFoundError:
        sys.exit("spent_map.csv not found — run BigQuery Query E and export it here first.")
    pat = {int(r["height"]): float(r["phi"]) for r in csv.DictReader(open("patoshi_confirmed.csv", newline=""))
           if r["patoshi_confirmed"] == "1"}
    out = []
    for r in rows:
        h = int(r["coinbase_height"])
        if h in pat:
            out.append(r)
    out.sort(key=lambda r: int(r["coinbase_height"]))

    with open("patoshi_awakenings.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys()); w.writeheader(); w.writerows(out)

    print(f"Patoshi coinbases with a spend (awakenings): {len(out):,}")
    if out:
        def when(r):
            t = r.get("spending_time")
            return datetime.fromtimestamp(int(t), timezone.utc).date().isoformat() if t else "?"
        print("  earliest 8 (coinbase_height -> spending_height @ date):")
        for r in out[:8]:
            print(f"    blk {r['coinbase_height']:>6} -> spent in blk {r['spending_height']:>7}  @ {when(r)}"
                  f"  by {r['spending_txid'][:16]}…")
        yrs = {}
        for r in out:
            t = r.get("spending_time")
            if t: yrs[datetime.fromtimestamp(int(t), timezone.utc).year] = yrs.get(datetime.fromtimestamp(int(t), timezone.utc).year, 0) + 1
        print("  spends by year:", dict(sorted(yrs.items())))
    print("  wrote patoshi_awakenings.csv  (feed the coinbase_height column to judge.py to re-label)")

if __name__ == "__main__":
    main()
