#!/usr/bin/env python3
"""deepdig.py — deeper empirical excavations, from data already in the CSVs (no fetch).

  A. HASHRATE / THROTTLE   — implied hash-rate over time (difficulty from the coinbase nBits push
                             + timestamps), network vs Patoshi, to see the miner's restraint.
  B. DARK-PERIOD GAPS      — inter-Patoshi-block gaps at fine resolution: does the miner ever go
                             dark for hours? (finer test than the hour-of-day histogram).
  C. NONCE BAND DENSITIES  — the exact per-value shape of the {0-9}u{19-58} fingerprint.

Reads early_blocks_merged.csv (+ patoshi_confirmed.csv for the label). No interpretation.
Grade: [forensic]. Run: python deepdig.py
"""
import csv, statistics as st
from collections import Counter, defaultdict
from datetime import datetime, timezone

SAT = 100_000_000

def data_pushes(script):
    out, i, n = [], 0, len(script)
    while i < n:
        op = script[i]; i += 1
        if 1 <= op <= 0x4b:
            out.append(script[i:i+op]); i += op
        elif op == 0x4c and i < n:
            l = script[i]; i += 1; out.append(script[i:i+l]); i += l
        else:
            break
    return out

def nbits_of(hexs):
    p = data_pushes(bytes.fromhex(hexs)) if hexs else []
    return int.from_bytes(p[0], "little") if p else None

def difficulty(nbits):
    exp = nbits >> 24; mant = nbits & 0xFFFFFF
    target = mant << (8*(exp-3))
    target1 = 0xFFFF << (8*(0x1D-3))
    return target1/target if target else 0

def load():
    conf = {int(r["height"]): (r["patoshi_confirmed"]=="1")
            for r in csv.DictReader(open("patoshi_confirmed.csv", newline=""))}
    rows = {}
    for r in csv.DictReader(open("early_blocks_merged.csv", newline="")):
        h = int(r["height"])
        rows[h] = {"t": int(r["timestamp"]), "nonce": int(r["nonce"],16),
                   "nbits": nbits_of(r["coinbase_script_hex"]),
                   "spent": r["coinbase_spent"], "pat": conf.get(h, False)}
    return rows

def main():
    rows = load()
    pat = {h:r for h,r in rows.items() if r["pat"]}

    print("="*72)
    print("A. HASHRATE / THROTTLE  (difficulty from coinbase nBits x timestamps)")
    print("="*72)
    # bin by calendar month
    bymonth = defaultdict(list)
    for h,r in rows.items():
        if h==0 or r["nbits"] is None: continue
        ym = datetime.fromtimestamp(r["t"], timezone.utc).strftime("%Y-%m")
        bymonth[ym].append((h,r))
    print(f"  {'month':8} {'blocks':>7} {'pat%':>5} {'diff':>8} {'net GH/s':>9} {'Patoshi GH/s':>13}")
    for ym in sorted(bymonth):
        b = bymonth[ym]
        span = max(r["t"] for _,r in b) - min(r["t"] for _,r in b)
        if span <= 0: continue
        net_hashes = sum(difficulty(r["nbits"])*2**32 for _,r in b)
        pat_hashes = sum(difficulty(r["nbits"])*2**32 for _,r in b if r["pat"])
        npat = sum(1 for _,r in b if r["pat"])
        diff = st.mean(difficulty(r["nbits"]) for _,r in b)
        print(f"  {ym:8} {len(b):7d} {npat/len(b):5.0%} {diff:8.2f} "
              f"{net_hashes/span/1e9:9.2f} {pat_hashes/span/1e9:13.2f}")
    print("  (Patoshi GH/s is the implied rate needed for its share; watch whether it stays")
    print("   ~flat/declining while the network grows -> restraint, not a ramp.)")

    print("\n" + "="*72)
    print("B. DARK-PERIOD GAPS  (inter-Patoshi-block, finer than hour-of-day)")
    print("="*72)
    tp = sorted(r["t"] for r in pat.values())
    gaps = [b-a for a,b in zip(tp, tp[1:])]
    gaps_pos = [g for g in gaps if g>=0]
    print(f"  consecutive Patoshi blocks: {len(gaps):,}")
    print(f"  gap median {st.median(gaps_pos)/60:.1f} min, mean {st.mean(gaps_pos)/60:.1f} min, max {max(gaps_pos)/3600:.2f} h")
    for thr,lbl in [(3600,'>1h'),(3*3600,'>3h'),(6*3600,'>6h'),(12*3600,'>12h')]:
        c = sum(1 for g in gaps_pos if g>thr)
        print(f"    gaps {lbl:>4}: {c:5d}  ({c/len(gaps_pos):.2%} of intervals)")
    # per-calendar-day Patoshi block count: any dark days?
    byday = Counter(datetime.fromtimestamp(t, timezone.utc).strftime("%Y-%m-%d") for t in tp)
    days = list(byday.values())
    zero_days = 0  # days with a block but 0 patoshi are captured via the span below
    print(f"  active days (>=1 Patoshi block): {len(byday):,}; per-day median {int(st.median(days))}, min {min(days)}, max {max(days)}")
    print(f"  -> a long dark gap or many min-1 days would indicate on/off; short gaps = ~continuous.")

    print("\n" + "="*72)
    print("C. NONCE BAND DENSITIES  (per-value shape of the fingerprint, confirmed Patoshi)")
    print("="*72)
    lsb = Counter(r["nonce"] & 0xFF for r in pat.values())
    band_lo = [lsb.get(v,0) for v in range(0,10)]
    band_hi = [lsb.get(v,0) for v in range(19,59)]
    print(f"  band {{0..9}}  per-value: {band_lo}")
    print(f"  band {{19..58}} per-value min {min(band_hi)}, max {max(band_hi)}, mean {st.mean(band_hi):.0f}")
    print(f"  band {{0..9}} total {sum(band_lo):,} over 10 values (mean {st.mean(band_lo):.0f}/value)")
    print(f"  band {{19..58}} total {sum(band_hi):,} over 40 values (mean {st.mean(band_hi):.0f}/value)")
    # is the low band exactly 2x-ish the density? report the ratio (thread-structure hint, no over-claim)
    print(f"  density ratio {{0..9}} : {{19..58}} = {st.mean(band_lo)/st.mean(band_hi):.2f}")
    gaps_v = [v for v in range(256) if not (0<=v<=9 or 19<=v<=58)]
    print(f"  out-of-band values with ANY confirmed-Patoshi block: "
          f"{sum(1 for v in gaps_v if lsb.get(v,0)>0)} of {len(gaps_v)}  (expect 0 — the fingerprint is exact)")

if __name__ == "__main__":
    main()
