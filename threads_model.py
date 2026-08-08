#!/usr/bin/env python3
"""threads_model.py — BOUND the Patoshi miner's parallel thread/core count.

The winning-nonce distribution does NOT pin the thread count (see threads.py / EXCAVATION.md §10):
the high bits are ~uniform (one low-end excess, not K discrete steps) and the low-byte bands are used
evenly. So the winning nonces give no clean K-way partition. We bound the count the only defensible
way — from the reconstructed HASHRATE (chain-derived, solid) divided by a plausible per-core
double-SHA-256 rate (a 2009 hardware/software fact, OFF-chain — this is the error bar).

  Chain-derived (solid):
    expected hashes per block at difficulty 1 = 2^32 (exact for the whole Patoshi-dominant era:
      every block < 32256 has difficulty 1.0; the first retarget was block 32256, ~30 Dec 2009,
      by which point Patoshi's share was already ~0 — see deepdig.py / EXCAVATION.md §7).
    Patoshi hashrate = 2^32 / (active mean inter-Patoshi-block gap in seconds).

  Off-chain assumption (THE error bar):
    per-core rate of Satoshi's unoptimized CryptoPP CPU miner (v0.1 used the non-SSE ScanHash path;
    the 4-way SSE2 speedup came later, ~mid-2010) on a 2009 desktop CPU. Plausibly 0.5-2.0 MH/s/core.

Result: the hashrate is pinned to a few MH/s; the core count is a RANGE that depends entirely on the
per-core assumption. We report the range and refuse to invent a single integer.

Grade: [forensic] for the hashrate; [modeled / bounded] for the core count. No key, no signature.
Run: python threads_model.py
"""
import csv
import statistics as st
from datetime import datetime, timezone
from math import log

EXP_HASHES = (1 << 256) // ((0xFFFF << 208) + 1)  # exact expected hashes/block at difficulty 1 =
#   2^256/(target+1) = 4,295,032,833 = 2^32 * 65536/65535 (the pdiff-vs-bdiff gap); the round 2^32
#   under-states the true hashrate by ~0.0015%.
LN2 = log(2)
D1_ERA_END = 32256            # first difficulty retarget; every block below this is difficulty 1.0
OUTAGE_CUTOFF_S = 7200        # gaps > 2 h are treated as idle/outage, not "actively mining"
PER_CORE_MHS = [0.5, 0.75, 1.0, 1.5, 2.0]   # plausible 2009 unoptimized double-SHA-256 per core


def load():
    ts = {int(r["height"]): int(r["timestamp"])
          for r in csv.DictReader(open("early_blocks_merged.csv", newline=""))}
    phi = {int(r["height"]): float(r["phi"])
           for r in csv.DictReader(open("patoshi_confirmed.csv", newline=""))}
    return ts, phi


def mhs(gap_s):
    return EXP_HASHES / gap_s / 1e6


def hashrate_block(gaps, label):
    """Return (median, mean_active, mean_all) gaps + the three hashrate estimates."""
    median_gap = st.median(gaps)
    mean_all = st.mean(gaps)                                    # includes idle -> lower bound
    active = [g for g in gaps if g <= OUTAGE_CUTOFF_S]
    mean_active = st.mean(active)                               # active-period average
    # Poisson: for exponential inter-arrivals, mean = median / ln2 -> corrected active rate
    hr_median = EXP_HASHES * LN2 / median_gap / 1e6
    hr_active = mhs(mean_active)
    hr_all = mhs(mean_all)
    return dict(label=label, n=len(gaps), median_gap=median_gap, mean_active=mean_active,
                mean_all=mean_all, hr_median=hr_median, hr_active=hr_active, hr_all=hr_all,
                n_active=len(active))


def main():
    ts, phi = load()
    heights = sorted(h for h, p in phi.items() if p >= 0.5 and h < D1_ERA_END and h in ts)
    series = [ts[h] for h in heights]
    gaps = [series[i] - series[i - 1] for i in range(1, len(series)) if series[i] - series[i - 1] > 0]

    print("=" * 78)
    print("PATOSHI THREAD/CORE COUNT — a bounded inference, not an integer")
    print("=" * 78)
    print(f"Confirmed Patoshi blocks in the difficulty-1 era (phi>=0.5, height<{D1_ERA_END}): "
          f"{len(heights):,}")
    print(f"Span: block {heights[0]} .. {heights[-1]}  "
          f"({datetime.fromtimestamp(series[0], timezone.utc).date()} .. "
          f"{datetime.fromtimestamp(series[-1], timezone.utc).date()})")
    print(f"Difficulty = 1.0 exact over this whole range -> expected hashes/block = 2^256/(target+1) "
          f"= {EXP_HASHES:,} (= 2^32 * 65536/65535, the exact pdiff-vs-bdiff value, not the round 2^32).\n")

    # ---- overall hashrate --------------------------------------------------
    o = hashrate_block(gaps, "overall")
    print("1) HASHRATE (chain-derived, solid)")
    print(f"   inter-block gaps: n={o['n']:,}  median={o['median_gap']/60:.1f} min  "
          f"mean(active<=2h, n={o['n_active']:,})={o['mean_active']/60:.1f} min  "
          f"mean(all incl. outages)={o['mean_all']/60:.1f} min")
    print(f"   hashrate estimators:")
    print(f"     from active mean gap        : {o['hr_active']:.2f} MH/s   (best 'while running')")
    print(f"     from median gap (Poisson)   : {o['hr_median']:.2f} MH/s")
    print(f"     from all-gaps mean          : {o['hr_all']:.2f} MH/s   (lower bound, counts idle)")
    lo, hi = min(o['hr_all'], o['hr_median']), max(o['hr_active'], o['hr_median'])
    print(f"   => Patoshi hashrate ~ {lo:.1f}-{hi:.1f} MH/s (active).\n")

    # ---- per-month trend ---------------------------------------------------
    print("2) MONTHLY hashrate (median-gap, Poisson-corrected) — shows a flat, un-ramped rate")
    bymonth = {}
    for i in range(1, len(series)):
        g = series[i] - series[i - 1]
        if g <= 0:
            continue
        m = datetime.fromtimestamp(series[i], timezone.utc).strftime("%Y-%m")
        bymonth.setdefault(m, []).append(g)
    print("   month     blocks  median-gap  hashrate")
    for m in sorted(bymonth):
        gs = bymonth[m]
        if len(gs) < 5:
            continue
        med = st.median(gs)
        print(f"   {m}   {len(gs):>6}   {med/60:>6.1f} min   {EXP_HASHES*LN2/med/1e6:>5.2f} MH/s")
    print("   NOTE: the later-2009 apparent decline is AMBIGUOUS — at constant difficulty (=1) a")
    print("   constant-hashrate miner would find a constant #blocks/month, so the drop is EITHER a")
    print("   real throttle-down OR the phi>=0.5 set undercounting Patoshi in the diluted zone")
    print("   (more interleaved non-Patoshi blocks -> lower local LSB rate -> phi falls). Cannot be")
    print("   cleanly separated; the clean machine-capability estimate is the early-2009 PEAK.\n")

    # ---- implied core count ------------------------------------------------
    hr = o['hr_active']  # use the active estimate as the central hashrate
    print(f"3) IMPLIED CORE/THREAD COUNT = hashrate / per-core-rate   (hashrate = {hr:.2f} MH/s)")
    print("   per-core (MH/s)   implied cores")
    for pc in PER_CORE_MHS:
        print(f"      {pc:>4.2f}            {hr/pc:>4.1f}")
    lo_cores = hr / max(PER_CORE_MHS)
    hi_cores = hr / min(PER_CORE_MHS)
    print(f"   => cores in ~[{lo_cores:.0f}, {hi_cores:.0f}] depending ENTIRELY on the per-core "
          f"assumption.\n")

    # ---- nonce-structure cross-check (why the winning nonces don't pin it) --
    # BigQuery stores the header nonce as an (unpadded) hex string -> ALWAYS parse base 16.
    nz = {int(r["height"]): int(r["nonce"], 16)
          for r in csv.DictReader(open("early_blocks_merged.csv", newline=""))
          if r.get("nonce")}
    top = [0] * 16
    seen = 0
    for h in heights:
        if h in nz:
            top[(nz[h] >> 28) & 0xF] += 1
            seen += 1
    print("4) NONCE STRUCTURE cross-check (why winning nonces cannot pin K)")
    print(f"   top-nibble of winning nonce over {seen:,} Patoshi blocks (uniform would be 6.25% each):")
    print(f"     0x0={100*top[0]/seen:.1f}%  0x1={100*top[1]/seen:.1f}%  "
          f"0x2..0xf avg={100*sum(top[2:])/(14*seen):.1f}%")
    print("   -> one low-end excess (incremental search restarting low), NOT K discrete steps.")
    print("   The winning-nonce distribution is therefore silent on the thread count.\n")

    # ---- low-byte band: a residue partition (thread map), or a contiguous counter? ----
    low = [nz[h] & 0xFF for h in heights if h in nz]
    A, B = set(range(0, 10)), set(range(19, 59))       # the Patoshi bands
    inband = A | B
    n_in = sum(1 for x in low if x in inband)
    # if the winning low-byte encoded a thread id (thread = nonce mod K), the in-band set would be an
    # exact union of residue classes mod K. Test every K: does membership match a mod-K residue set?
    fit_K = None
    for K in range(2, 33):
        classes = {x % K for x in inband}
        if all((x % K in classes) == (x in inband) for x in range(256)):
            fit_K = K; break
    print("5) LOW-BYTE BAND — thread partition, or a counter artifact?")
    print(f"   the Patoshi band is {{0-9}} U {{19-58}} (50 of 256 low-byte values); the per-block")
    print(f"   LSB-confirmed set is 100% in-band by construction (this looser phi>=0.5 set: "
          f"{100*n_in/len(low):.1f}%, the rest are diluted-zone blocks).")
    print(f"   is the band a union of residue classes mod K (i.e. thread-id = nonce mod K)? "
          f"{'yes, K='+str(fit_K) if fit_K else 'NO for any K in 2..32'}")
    print("   -> the bands are CONTIGUOUS RANGES, not residue classes: a loop/counter artifact, not a")
    print("      thread-id partition. So the thread count cannot be read from the nonce pattern.\n")

    # ---- verdict -----------------------------------------------------------
    print("=" * 78)
    print("VERDICT (honest, bounded):")
    print(f"  * The chain PINS the hashrate: ~{lo:.0f}-{hi:.0f} MH/s while actively mining (early-2009")
    print("    peak, when classification is clean); it never RAMPED (cf. §7). The later apparent")
    print("    decline is real-throttle-or-classification-dilution and cannot be cleanly separated.")
    print("  * The chain does NOT pin the thread/core count: it equals hashrate / per-core-rate,")
    print("    and the per-core rate of the 2009 unoptimized miner is an OFF-chain unknown.")
    print(f"  * Under plausible per-core rates (0.5-2.0 MH/s) the count is ~{lo_cores:.0f}-"
          f"{hi_cores:.0f} cores;")
    print("    at the likely ~1-2 MH/s/core it is a SINGLE ordinary multi-core desktop (~2-4 cores).")
    print("  * The low-byte fingerprint is a CONTIGUOUS-RANGE counter artifact, not a mod-K residue")
    print("    (thread-id) partition (§5) — so the nonces carry no thread-count signal either.")
    print("  * A single integer cannot be claimed from on-chain data alone. Reported as a range.")
    print("=" * 78)


if __name__ == "__main__":
    main()
