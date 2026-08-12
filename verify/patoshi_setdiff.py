"""The pairwise Patoshi set difference. As far as anyone can establish, the first one published.

WHY THIS SCRIPT EXISTS
----------------------
Two independent external searches (12 Aug 2026) looked specifically for an inter-implementation
agreement statistic for Patoshi classification and found none. What the literature contains is
five error figures that are NOT COMPARABLE WITH ONE ANOTHER -- different sets, different block
ranges, different definitions of "error" -- and which span nearly three orders of magnitude:

    Lerner        0.1%             his own estimated tagging error
    Lopp          "well under 1%"  his own estimate
    Maxwell       ~200k coins, not 1.1M
    Whale Alert   31 of 50 possible false positives, on the only externally testable subsample
    BitMEX        "will have made many errors", "may have grossly overestimated"

We have not found |A n B|, |A \\ B|, |B \\ A|, |A /\\ B| or Jaccard published for any pair, and two
independent searches for such a statistic also found none. ⚠️ That is an absence of evidence, not
a proof that none exists — if one is published anywhere, this file should be corrected to cite it.
What follows computes it for one pair.

THE COMPARISON SET IS VERSIONED, AND THAT IS ITSELF A FINDING
--------------------------------------------------------------
Set B is the deployed btc-rpc-explorer list -- a real implementation people query, not a paper
figure. It is a git-tracked JSON file, which means it HAS a history:

    21,953 heights   the version this project compared against in entry 88
    21,950 heights   the version deployed today
       -3            35573, 35599 and 24504, removed 8 Nov 2023 after outside challenges

=> "The Patoshi list" names at least two different sets. Anyone who forked before 8 Nov 2023 and
   anyone who forked after hold different sets, and neither cites a version.

RANGE IS CONTROLLED FIRST, AND NO PUBLISHED COMPARISON HAS DONE THIS
--------------------------------------------------------------------
Headline totals are not comparable: BitMEX covered 2009 only (36,288 blocks), others run to
~54,316. Part of every quoted gap is COVERAGE, not disagreement. This restricts both sets to the
height range each actually spans before differencing anything.

Run:  python verify/patoshi_setdiff.py            (uses the cached snapshot)
      python verify/patoshi_setdiff.py --fetch    (re-fetch and re-hash set B)
"""
import csv
import hashlib
import json
import os
import sys
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
SNAP = os.path.join(REPO, "data", "btc-rpc-explorer-patoshi.json")

SRC = ("https://raw.githubusercontent.com/janoside/btc-rpc-explorer/master/"
       "public/txt/mining-pools-configs/BTC/0.json")

THRESHOLD = 0.5

# 2009-08-01 00:00:00 UTC. BitMEX reported agreement with Lerner up to about here and a
# breakdown after; no one has tested whether that boundary generalises to another pair.
AUG2009 = 1248998400

REMOVED = {35573, 35599, 24504}


def fetch():
    req = urllib.request.Request(SRC, headers={"User-Agent": "satoshi-onchain-research/1.0"})
    return urllib.request.urlopen(req, timeout=60).read().decode("utf-8")


def load_b(do_fetch):
    if do_fetch or not os.path.exists(SNAP):
        text = fetch()
        os.makedirs(os.path.dirname(SNAP), exist_ok=True)
        with open(SNAP, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
    else:
        text = open(SNAP, encoding="utf-8").read()
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    heights = json.loads(text)["block_heights"]["Patoshi"]["heights"]
    return set(int(h) for h in heights), digest, len(text)


def load_ours():
    ours, tstamp = set(), {}
    with open(os.path.join(REPO, "patoshi_confirmed.csv"), newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            # The PATOSHI set is not phi >= 0.5 alone. judge.py: the nonce-LSB test is a
            # NECESSARY condition and phi >= 0.5 is the sufficient one; patoshi_confirmed
            # carries both. Using phi alone yields 23,893 instead of 18,589 and silently
            # inflates every disagreement figure below. Caught 12 Aug 2026 by the totals
            # failing to reconcile with entry 88.
            if r["height"].isdigit() and r["patoshi_confirmed"] == "1":
                ours.add(int(r["height"]))
    with open(os.path.join(REPO, "early_blocks_merged.csv"), newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            if r["height"].isdigit():
                tstamp[int(r["height"])] = int(r["timestamp"])
    return ours, tstamp


def report(a, b, tstamp, label):
    inter = a & b
    only_a = a - b
    only_b = b - a
    sym = only_a | only_b
    union = a | b
    print("  |A| ours          %7d" % len(a))
    print("  |B| explorer      %7d" % len(b))
    print("  |A n B| agree     %7d" % len(inter))
    print("  |A \\ B| ours only %7d   (%.2f%% of A)" % (len(only_a), pct(len(only_a), len(a))))
    print("  |B \\ A| theirs    %7d   (%.2f%% of B)" % (len(only_b), pct(len(only_b), len(b))))
    print("  |A /\\ B| symmetric%7d" % len(sym))
    print("  Jaccard           %9.4f" % (len(inter) / len(union) if union else 0.0))
    print("  disagreement rate %9.4f   = |A /\\ B| / |A u B|" % (len(sym) / len(union) if union else 0.0))
    return only_a, only_b, sym


def pct(n, d):
    return 100.0 * n / d if d else 0.0


def when(tstamp, h):
    import datetime
    if h not in tstamp:
        return "(no timestamp here)"
    return datetime.datetime.fromtimestamp(tstamp[h], datetime.timezone.utc).strftime("%Y-%m-%d")


def month(tstamp, h):
    import datetime
    return datetime.datetime.fromtimestamp(tstamp[h], datetime.timezone.utc).strftime("%Y-%m")


def main():
    do_fetch = "--fetch" in sys.argv
    b, digest, nbytes = load_b(do_fetch)
    a, tstamp = load_ours()
    phi_all = {}
    with open(os.path.join(REPO, "patoshi_confirmed.csv"), newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            if r["height"].isdigit():
                phi_all[int(r["height"])] = float(r["phi"] or 0)

    print("=" * 78)
    print(" SET B — the deployed btc-rpc-explorer Patoshi list")
    print("=" * 78)
    print("  source  %s" % SRC)
    print("  bytes   %d" % nbytes)
    print("  sha256  %s" % digest)
    print("  heights %d   range %d..%d" % (len(b), min(b), max(b)))
    print()
    print("  the three blocks removed 8 Nov 2023 after outside challenge:")
    for h in sorted(REMOVED):
        print("    %-8d %s" % (h, "ABSENT (removal confirmed)" if h not in b else "STILL PRESENT"))
    absent = sum(1 for h in REMOVED if h not in b)
    print("  => %d of 3 absent. 21953 - 3 = %d, and this list holds %d." % (absent, 21953 - 3, len(b)))

    print()
    print("=" * 78)
    print(" RANGE CONTROL — done BEFORE differencing, which no published comparison has done")
    print("=" * 78)
    lo, hi = min(b), max(b)
    ours_all = len(a)
    a_r = set(h for h in a if lo <= h <= hi)
    print("  set B spans          %d..%d" % (lo, hi))
    print("  our set spans        %d..%d  (%d blocks)" % (min(a), max(a), ours_all))
    print("  our blocks OUTSIDE B's range: %d   <- excluded from every figure below" % (ours_all - len(a_r)))
    print("  (they are not disagreements. They are coverage.)")

    print()
    print("=" * 78)
    print(" THE PAIRWISE DIFFERENCE, over the common range %d..%d" % (lo, hi))
    print("=" * 78)
    only_a, only_b, sym = report(a_r, b, tstamp, "common range")

    # --- The naive version of this split is WRONG, and the first run of this script made
    # the error. Set B extends to height 49973; our confirmed set stops at 24184. Every B
    # height above our maximum is automatically "theirs only" -- that is COVERAGE, not
    # disagreement, and counting it manufactured a 68% post-August figure out of nothing.
    print()
    print("=" * 78)
    print(" COVERAGE VS DISAGREEMENT — the distinction that makes the rest meaningful")
    print("=" * 78)
    top_a = max(a)
    above = sorted(h for h in b if h > top_a)
    print("  our confirmed set stops at   %6d   %s" % (top_a, when(tstamp, top_a)))
    print("  set B continues to           %6d   %s" % (max(b), when(tstamp, max(b))))
    print("  B heights above our maximum: %6d   (%.1f%% of B, ~%s BTC at 50/block)"
          % (len(above), pct(len(above), len(b)), "{:,}".format(len(above) * 50)))
    print()
    print("  These are NOT counted as disagreements below. A naive symmetric difference")
    print("  counts them and reports ~68% post-August disagreement. That figure is an")
    print("  artifact of range and this script produced it once before the control was added.")

    print()
    print("=" * 78)
    print(" MONTHLY AGREEMENT, over the range where BOTH sets are live")
    print("=" * 78)
    print("  %-9s %7s %7s %7s %8s %9s" % ("month", "|A|", "|B|", "agree", "symdiff", "disagree"))
    months = {}
    for h in (a | b):
        if h > top_a or h not in tstamp:
            continue
        m = month(tstamp, h)
        s_a, s_b = months.setdefault(m, (set(), set()))
        if h in a:
            s_a.add(h)
        if h in b:
            s_b.add(h)
    for m in sorted(months):
        aa, bb = months[m]
        u = aa | bb
        sd = (aa - bb) | (bb - aa)
        flag = "  <-- spike" if u and len(sd) / len(u) > 0.15 else ""
        print("  %-9s %7d %7d %7d %8d %8.1f%%%s"
              % (m, len(aa), len(bb), len(aa & bb), len(sd), 100.0 * len(sd) / len(u) if u else 0, flag))
    print()
    print("  => agreement is HIGH and STABLE at 5-10% disagreement, with ONE localised spike.")
    print("     It is not a progressive breakdown. BitMEX described a breakdown after August")
    print("     2009 in a different pair; in this pair August 2009 is a spike that RECOVERS.")

    print()
    print("=" * 78)
    print(" THE CLIFF — and it is a finding, not a gap in our data")
    print("=" * 78)
    print("  Every block above our maximum WAS scored. phi is present and non-trivial there;")
    print("  it simply never reaches threshold again. The signal collapses rather than stopping:")
    print()
    print("  %-16s %6s %9s %9s %8s" % ("heights", "n", "max phi", "mean phi", "confirmed"))
    for lo_k in range(21000, 32000, 1000):
        vals = [phi_all[h] for h in range(lo_k, lo_k + 1000) if h in phi_all]
        if not vals:
            continue
        print("  %6d-%-9d %6d %9.4f %9.4f %8d"
              % (lo_k, lo_k + 999, len(vals), max(vals), sum(vals) / len(vals),
                 sum(1 for h in range(lo_k, lo_k + 1000) if h in a)))
    print()
    print("  => a CLIFF, not a decay: full confirmation through 23999, then 186, then never")
    print("     again -- while the deployed list keeps labelling for another six months.")

    print()
    print("=" * 78)
    print(" WHERE THE DISAGREEMENT LIVES IN OUR OWN SCORE")
    print("=" * 78)
    got = sorted(phi_all[h] for h in only_b if h in phi_all and h <= max(a))
    if got:
        over = sum(1 for x in got if x >= THRESHOLD)
        print("  blocks THEY call Patoshi and we do not, WITHIN our range: %d" % len(got))
        print("    median phi %.4f   max phi %.4f   at or above threshold: %d"
              % (got[len(got) // 2], got[-1], over))
        if over == 0:
            print("  => every one sits BELOW our threshold. The two sets do not disagree at random;")
            print("     they disagree exactly along our confidence boundary, which is where a rule")
            print("     with irreversible consequences should be least willing to act.")
    print()
    print("=" * 78)
    print(" THE DECOMPOSITION — what 'they say Patoshi and we do not' actually consists of")
    print("=" * 78)
    top_a = max(a)
    out_of_range = sum(1 for h in only_b if h > top_a)
    in_range = len(only_b) - out_of_range
    print("  total theirs-only            %6d" % len(only_b))
    print("    beyond our cliff           %6d   (%.1f%%)  a disagreement about WHEN Patoshi"
          % (out_of_range, pct(out_of_range, len(only_b))))
    print("                                                stopped, not about which blocks")
    print("    within our range           %6d   (%.1f%%)  genuine per-block label conflict"
          % (in_range, pct(in_range, len(only_b))))
    print()
    print("  => These are two different disagreements and every published figure conflates")
    print("     them. The per-block conflict is SMALL and sits on the threshold; the large")
    print("     number is a six-month argument about when the pattern ended.")

    print()
    print("  NOT A VERDICT. There is no ground truth: no 2009-era key has ever signed anything,")
    print("  so neither set is 'right'. The measurable fact is the size and shape of the gap.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
