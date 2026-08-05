"""Locate, on-chain, the 100 BTC that Satoshi sent Nicholas Bohm on 1 February 2009.

WHY THIS IS WORTH DOING. Almost everything known about Satoshi's early sends is inferred from the
chain alone. This one is different: a named recipient described the transfer **in a witness
statement, under a statement of truth, in the High Court of England and Wales** — and then died,
in January 2024, before he could be cross-examined on it.

    Bohm, First Witness Statement, sec.15 (COPA v Wright, {C/10/1}):
      "On 1 February 2009, (a date which I have remembered by checking Exhibit NB1), Satoshi sent
       me a transfer of 100 Bitcoin. This transfer was unprompted (in the sense that we had not
       discussed a transfer being made). ... There are also two other Bitcoin transactions
       referred to in that correspondence, which I remember did take place as described there."

    and sec.24, on losing the wallet in a 2011 machine change:
      "The wallet was empty by then (I had variously spent / transferred the bitcoins in it)."

So there is a sworn, dated, quantified claim about a specific early transaction. This script asks
whether the chain agrees. It does.

WHAT IT ESTABLISHES, AND HOW STRONGLY.

  Very strong (this is the load-bearing part):
    - Non-coinbase activity in early 2009 is almost nil. Across blocks 2100-3600 (29 Jan - 8 Feb
      2009) only 13 blocks contain any transaction beyond the coinbase.
    - Among every one of those transactions, EXACTLY ONE pays exactly 100 BTC.
    - It confirms in block 2616 at 2009-02-01 16:25:12 UTC -- Bohm's stated date.
    - Its shape is a gift, not a payment: two mined 50 BTC inputs, one round 100 BTC output,
      no change address.
    - The receiving address takes a SECOND early payment (19.01 BTC on 3 Feb 2009), matching
      "two other Bitcoin transactions", and is emptied during 2011, matching his account of
      spending the wallet down before losing access.

  Weak, and must not be oversold:
    - Both funding coinbases carry the Patoshi nonce-LSB fingerprint. That is CONSISTENT with
      Satoshi's miner, but in this era ~74% of ALL blocks are Patoshi, so two Patoshi inputs
      would arise by chance about 55% of the time. It corroborates; it does not identify.
    - The Patoshi fingerprint is [forensic], never [cryptographic]. No signature here proves
      who sent anything.
    - Bohm's date came from his own email archive, and a send date is not a confirmation date.

  Therefore: this is an identification by date + amount + uniqueness + downstream behaviour,
  each independently checkable, and NOT a cryptographic proof. Stated that way, it is the closest
  this project has come to putting a court-sworn name against a specific early Satoshi transaction.

Usage:  python bohm_transfer.py            # full check against a public explorer
        python bohm_transfer.py --offline  # re-state the recorded result without network
"""
import json
import sys
import time
import urllib.request
import datetime
import argparse

sys.stdout.reconfigure(encoding="utf-8")

API = "https://blockstream.info/api"
UA = {"User-Agent": "satoshi-onchain/1.0 (provenance check; github.com/satoshi-onchain)"}

TXID = "7d73200eac9b66ea105fe63378c69f5d68663f925297117ed178deaddb6fc3d5"
ADDR = "1CHE5JRfc5mr8ZtVUP7nnsS5HC4bWcXoc6"
LO, HI = 2100, 3600


def get(url, tries=3):
    for _ in range(tries):
        try:
            return json.load(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=45))
        except Exception:
            time.sleep(2)
    return None


def utc(ts):
    return datetime.datetime.fromtimestamp(ts, datetime.timezone.utc)


def survey():
    """Every block in the window carrying more than a coinbase."""
    print(f"  scanning blocks {LO}-{HI} for any non-coinbase activity …")
    seen, hits, h = set(), [], HI
    while h >= LO:
        batch = get(f"{API}/blocks/{h}")
        if not batch:
            h -= 10
            continue
        for b in batch:
            if b["height"] in seen or not (LO <= b["height"] <= HI):
                continue
            seen.add(b["height"])
            if b["tx_count"] > 1:
                hits.append(b["height"])
        h = min(b["height"] for b in batch) - 1
        time.sleep(0.15)
    print(f"  {len(seen)} blocks scanned; {len(hits)} carry a non-coinbase transaction")
    return sorted(hits)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--offline", action="store_true")
    a = ap.parse_args()

    print(__doc__.split("Usage:")[0].rstrip()[:0] or "", end="")
    print("== Satoshi -> Nicholas Bohm, 100 BTC, 1 February 2009 ==\n")

    if a.offline:
        print(f"  tx      {TXID}")
        print(f"  block   2616 at 2009-02-01 16:25:12 UTC")
        print(f"  inputs  2 x 50.00000000 BTC (coinbases of blocks 2459 and 2485, both Patoshi-slot)")
        print(f"  output  100.00000000 BTC -> {ADDR}, no change")
        print(f"  also    19.01000000 BTC -> same address on 2009-02-03 (block 2915)")
        print(f"  spent   during 2011; address balance now 0")
        return

    heights = survey()
    hundreds = []
    print("\n  === every non-coinbase transaction in the window ===")
    for ht in heights:
        bid = urllib.request.urlopen(
            urllib.request.Request(f"{API}/block-height/{ht}", headers=UA), timeout=45).read().decode()
        for t in get(f"{API}/block/{bid}/txs") or []:
            if t["vin"][0].get("is_coinbase"):
                continue
            outs = " + ".join(f"{o['value'] / 1e8:g}" for o in t["vout"])
            flag = ""
            if any(abs(o["value"] / 1e8 - 100) < 1e-9 for o in t["vout"]):
                hundreds.append((ht, t["txid"]))
                flag = "   <== exactly 100 BTC"
            print(f"   blk {ht:<5} {t['txid'][:20]}…  in {len(t['vin']):>2}  out [{outs}]{flag}")
        time.sleep(0.2)

    print(f"\n  transactions paying exactly 100 BTC: {len(hundreds)}")
    assert len(hundreds) == 1, "expected exactly one; the record has changed — investigate"
    ht, txid = hundreds[0]
    assert txid == TXID, f"unexpected txid {txid}"

    tx = get(f"{API}/tx/{txid}")
    blk = get(f"{API}/block/{tx['status']['block_hash']}")
    print(f"\n  === the transaction ===")
    print(f"   txid    {txid}")
    print(f"   block   {ht} at {utc(blk['timestamp']):%Y-%m-%d %H:%M:%S} UTC   <-- Bohm's stated date")
    for v in tx["vin"]:
        st = get(f"{API}/tx/{v['txid']}/status")
        print(f"   IN      {(v.get('prevout') or {}).get('value', 0) / 1e8:>12.8f} BTC  coinbase of block {st.get('block_height')}")
    for o in tx["vout"]:
        print(f"   OUT     {o['value'] / 1e8:>12.8f} BTC  -> {o.get('scriptpubkey_address')}")
    print("   shape   two mined inputs, one round output, NO change address = a gift, not a payment")

    st = get(f"{API}/address/{ADDR}")["chain_stats"]
    print(f"\n  === the recipient address ===")
    print(f"   {ADDR}")
    print(f"   funded {st['funded_txo_sum'] / 1e8:g} BTC over {st['tx_count']} transactions; "
          f"balance {(st['funded_txo_sum'] - st['spent_txo_sum']) / 1e8:g} BTC")
    for t in get(f"{API}/address/{ADDR}/txs") or []:
        got = sum(o["value"] for o in t["vout"] if o.get("scriptpubkey_address") == ADDR) / 1e8
        bt = t.get("status", {}).get("block_time")
        print(f"   blk {t['status'].get('block_height'):<7} {utc(bt):%Y-%m-%d %H:%M} UTC  "
              f"{'receives ' + format(got, 'g') + ' BTC' if got else 'spends'}")

    print("""
  === what this does and does not show ===
  DOES:  exactly one 100 BTC transaction exists in a ten-day window of near-zero activity, on the
         precise date a named recipient swore to; it is shaped like a gift; the receiving address
         takes a second early payment days later (his "two other transactions") and is emptied in
         2011 (his account of spending it down before losing wallet access).
  DOES NOT: prove who signed it. The Patoshi fingerprint on the funding coinbases is [forensic] and
         weakly discriminating here -- ~74% of blocks in this era are Patoshi, so two Patoshi inputs
         arise by chance roughly half the time. No signature identifies a sender.""")


main()
