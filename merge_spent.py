#!/usr/bin/env python3
"""Merge the optional dormancy result (Query B) into the classification CSV (Query A).

  python merge_spent.py early_blocks.csv spent_status.csv   # -> early_blocks_merged.csv

spent_status.csv must have columns: height, coinbase_spent  ('0' unspent | '1' spent |
'unspendable'). Rows without a match keep '?'. Feed early_blocks_merged.csv to patoshi.py
to get the unspent/spent split.
"""
import csv, sys

if len(sys.argv) != 3:
    sys.exit("usage: python merge_spent.py early_blocks.csv spent_status.csv")

spent = {int(r["height"]): r["coinbase_spent"]
         for r in csv.DictReader(open(sys.argv[2], newline=""))}

rows = list(csv.DictReader(open(sys.argv[1], newline="")))
fields = rows[0].keys()
if "coinbase_spent" not in fields:
    fields = list(fields) + ["coinbase_spent"]
for r in rows:
    r["coinbase_spent"] = spent.get(int(r["height"]), r.get("coinbase_spent", "?"))

with open("early_blocks_merged.csv", "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(fields))
    w.writeheader(); w.writerows(rows)
print(f"merged {sum(1 for r in rows if r['coinbase_spent'] in ('0','1','unspendable'))}"
      f"/{len(rows)} spent-flags -> early_blocks_merged.csv")
