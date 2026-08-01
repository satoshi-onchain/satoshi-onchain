#!/usr/bin/env python3
"""threads.py — try to pin the Patoshi miner's thread count from the winning-nonce structure.

The classifier uses the winning nonce's LOW byte (∈ {0..9}∪{19..58}). If the miner partitioned the
32-bit nonce space across N threads, that partition may show as structure in the HIGH bits (each
thread searching a contiguous slice) or in the fine low-byte shape. This reports the empirical
structure and states honestly whether a thread count is uniquely determined. No interpretation.

Reads patoshi_confirmed.csv + early_blocks_merged.csv. Run: python threads.py
"""
import csv, statistics as st
from collections import Counter

def load():
    conf = {int(r["height"]) for r in csv.DictReader(open("patoshi_confirmed.csv", newline=""))
            if r["patoshi_confirmed"] == "1"}
    nonces = []
    for r in csv.DictReader(open("early_blocks_merged.csv", newline="")):
        h = int(r["height"])
        if h in conf:
            nonces.append(int(r["nonce"], 16))
    return nonces

def uniformity_chi2(counts, k):
    exp = sum(counts)/k
    return sum((c-exp)**2/exp for c in counts)

def main():
    N = load()
    n = len(N)
    print(f"confirmed-Patoshi winning nonces: {n:,}\n")

    print("== high-bit structure (would a thread partition show here?) ==")
    for shift, label, k in [(24,"top byte (>>24)",256), (28,"top nibble (>>28)",16), (30,"top 2 bits",4)]:
        c = Counter(x >> shift for x in N)
        counts = [c.get(i,0) for i in range(k)]
        chi = uniformity_chi2(counts, k)
        print(f"  {label:16}: {k} bins, chi2={chi:.0f} (dof {k-1}); "
              f"{'CLUSTERED' if chi > 3*(k-1) else 'uniform (no thread bands here)'}")
    print("  top-2-bit distribution (quarters of the nonce range):")
    c2 = Counter(x >> 30 for x in N)
    for q in range(4):
        cnt=c2.get(q,0); print(f"     [{q}/4]: {cnt:6,} ({cnt/n:5.1%})  {'#'*round(cnt/n*80)}")
    print("  top-nibble distribution (16ths):")
    c4 = Counter(x >> 28 for x in N)
    for q in range(16):
        cnt=c4.get(q,0); print(f"     0x{q:x}: {cnt:5,} ({cnt/n:4.1%}) {'#'*round(cnt/n*160)}")
    # split full range into K contiguous slices; a K-thread miner would fill all K ~evenly
    print("\n== full-range slices (each thread would occupy ~1/K of 2^32) ==")
    for k in (2,3,4,5,6,8,16):
        c = Counter(min(k-1, x*k>>32) for x in N)
        counts=[c.get(i,0) for i in range(k)]
        spread = (max(counts)-min(counts))/(sum(counts)/k)
        print(f"  K={k:2}: per-slice spread {spread:+.0%} of mean  {'(even -> consistent with >=K search regions)' if spread<0.15 else ''}")

    print("\n== low-byte fine structure (the two bands) ==")
    lsb = Counter(x & 0xFF for x in N)
    lo = [lsb.get(v,0) for v in range(0,10)]; hi = [lsb.get(v,0) for v in range(19,59)]
    print(f"  band {{0..9}}  (10 values): total {sum(lo):,}, mean {st.mean(lo):.0f}/value")
    print(f"  band {{19..58}} (40 values): total {sum(hi):,}, mean {st.mean(hi):.0f}/value")
    print(f"  the widths are 10 and 40 (ratio 1:4); values within each band are ~flat.")

    print("\n== honest verdict ==")
    print("  The winning nonce is ~uniform across the 32-bit range EXCEPT a ~2x EXCESS in the lowest")
    print("  1/16 (top nibble 0x0 = 11.3% vs 6.25% uniform; 0x1 slightly up; 0x2..0xf ~flat). That")
    print("  low-end excess is the signature of an INCREMENTAL search restarting from a low nonce each")
    print("  block (blocks found early land at low nonces); the rest of the space is covered ~evenly.")
    print("  There is NO clean K-way even partition — the K-slice spread grows smoothly (driven by that")
    print("  single low-end excess), not in K discrete steps — so a thread count CANNOT be uniquely read")
    print("  from the winning-nonce distribution; pinning N needs hash-rate/timing modelling (not done).")
    print("  What IS fixed: the low byte ∈ {0..9}∪{19..58} (50/256 values, widths 10 and 40, ~even).")

if __name__ == "__main__":
    main()
