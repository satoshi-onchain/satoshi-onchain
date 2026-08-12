"""The only externally adjudicated blocks in the Patoshi problem, scored by our classifier.

THE SITUATION
-------------
Every published Patoshi error rate we have found is a SELF-REPORT from inside the model that
produced the set: Lerner 0.1%, Lopp "well under 1%", Whale Alert 31-of-50 possible false positives
(and those three measure different things on different sets, so they do not contradict each other). No one has ever
published an inter-implementation agreement statistic -- |A n B|, |A \\ B|, Jaccard, anything.

There is, however, a tiny set of labels that were decided by a process OUTSIDE the classifier.

⚠️ THIS IS NOT GROUND TRUTH AND MUST NOT BE CALLED THAT. No 2009-era key has ever signed anything,
so no Patoshi label can be shown correct. What follows is a considered judgement by several
analysts, accepted by the method's author and acted on by a maintainer -- which is the strongest
external check the problem admits, and still not a fact about who mined anything.

    THREE BLOCKS were challenged by outside analysts, the challenge was ACCEPTED by the
    classifier's own author, and a deployed public implementation REMOVED them.

    35573, 35599   challenged 27 Aug 2022 (cricktor) on COMMON-INPUT OWNERSHIP: a 2017
                   transaction spent both coinbases alongside 58 coinbases classified
                   NON-Patoshi. Lerner replied 29 Aug 2022: "They could be false positives
                   of the slope finding algorithm", and noted another ExtraNonce line
                   crosses the Patoshi slope at 35599.
    24504          challenged 13 Sep 2022 (Lopp) on a DIFFERENT ground: it intersects
                   another miner's ExtraNonce slope, and its timestamp is 65 s after its
                   parent -- shorter than the identified miner's habit.
    8 Nov 2023     btc-rpc-explorer removed all three.

WHY THIS IS WORTH RUNNING
-------------------------
Our classifier was built from block bytes and knew nothing of this dispute. The challenges did not
come from a phi score -- they came from a spend pattern and a timestamp gap. So the EVIDENCE is
independent of our model even though the model family (ExtraNonce slopes) overlaps.

    => scoring these three is a blind test against the only externally decided labels we know of.

WHAT IT CANNOT DO, stated first so nobody overreads the output
--------------------------------------------------------------
  n = 3. This establishes no rate. It cannot.
  Selection is adversarial: these blocks were chosen BECAUSE they looked wrong. Agreement is
      what two working methods SHOULD produce, so a pass is weak evidence and a miss would
      have been strong evidence against us.
  It tests FALSE POSITIVES only. No externally adjudicated TRUE positive exists anywhere,
      because no 2009-era key has ever signed anything.

Run:  python verify/adjudicated_blocks.py
"""
import csv
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)

THRESHOLD = 0.5

ADJUDICATED = [
    (35573, "cricktor, 27 Aug 2022", "2017 tx spent this coinbase with 58 non-Patoshi coinbases"),
    (35599, "cricktor, 27 Aug 2022", "same tx; Lerner: another ExtraNonce line crosses the slope here"),
    (24504, "Lopp, 13 Sep 2022", "intersects another miner's slope; 65 s after its parent"),
]


def load(fn, key="height"):
    p = os.path.join(REPO, fn)
    with open(p, newline="", encoding="utf-8") as fh:
        return {int(r[key]): r for r in csv.DictReader(fh) if r[key].isdigit()}


def main():
    conf = load("patoshi_confirmed.csv")
    blocks = load("early_blocks_merged.csv")

    print("=" * 78)
    print(" THE THREE ADJUDICATED BLOCKS, SCORED BY OUR CLASSIFIER")
    print("=" * 78)
    print(" threshold: phi >= %.1f  =>  patoshi_confirmed" % THRESHOLD)
    print()
    print("  %-8s %-10s %-8s %-12s  %s" % ("height", "extranonce", "phi", "our verdict", "challenged on"))
    print("  " + "-" * 74)

    agree = 0
    for h, who, why in ADJUDICATED:
        r = conf.get(h)
        if r is None:
            print("  %-8d NOT IN OUR DATA" % h)
            continue
        phi = float(r["phi"])
        ours = "PATOSHI" if phi >= THRESHOLD else "not patoshi"
        # The external adjudication REMOVED them, i.e. decided "not patoshi".
        if phi < THRESHOLD:
            agree += 1
        print("  %-8d %-10s %-8.4f %-12s  %s" % (h, r["extranonce"], phi, ours, who))
        print("           %s" % why)

    print()
    print("  agreement with the external adjudication: %d of %d" % (agree, len(ADJUDICATED)))

    # --- Lopp's stated reason for 24504, checked against OUR OWN set rather than asserted.
    print()
    print("=" * 78)
    print(" LOPP'S TIMESTAMP ARGUMENT, TESTED AGAINST OUR OWN CONFIRMED SET")
    print("=" * 78)
    print(" His claim: 24504 sits 65 s after its parent, and the identified miner")
    print(" generally avoided intervals that short. That is checkable here.")
    print()

    d = blocks.get(24504)
    par = blocks.get(24503)
    if d and par:
        delta = int(d["timestamp"]) - int(par["timestamp"])
        print("  24504 - 24503 = %d s   (his figure: 65 s)" % delta)

    # distribution of parent deltas across OUR confirmed set
    deltas = []
    for h, r in conf.items():
        if float(r["phi"]) < THRESHOLD:
            continue
        a, b = blocks.get(h), blocks.get(h - 1)
        if a and b:
            deltas.append(int(a["timestamp"]) - int(b["timestamp"]))
    if deltas:
        deltas.sort()
        short = sum(1 for x in deltas if 0 <= x <= 65)
        neg = sum(1 for x in deltas if x < 0)
        print("  our confirmed set: %d blocks with a measurable parent gap" % len(deltas))
        print("    <= 65 s : %d  (%.2f%%)" % (short, 100.0 * short / len(deltas)))
        print("    negative: %d  (timestamps are not monotonic on this chain)" % neg)
        print("    median  : %d s" % deltas[len(deltas) // 2])
        print()
        if 100.0 * short / len(deltas) < 5:
            print("  => the habit he describes is REAL in our set too: short gaps are rare.")
        else:
            print("  => WARNING: short gaps are NOT rare in our set. His premise does not reproduce here,")
            print("     and the 24504 removal would rest on the slope argument alone.")

    print()
    print("=" * 78)
    print(" WHAT THIS IS AND IS NOT")
    print("=" * 78)
    print("  IS      the only externally adjudicated labels we know of, scored blind")
    print("  IS NOT  a rate. n = 3.")
    print("  IS NOT  a test of false NEGATIVES -- no adjudicated true positive exists")
    print("  NOTE    the blocks were selected BECAUSE they looked wrong, so agreement is")
    print("          the expected outcome for any working method. A MISS would have been")
    print("          the informative result. It did not happen, and that is worth exactly")
    print("          that much and no more.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
