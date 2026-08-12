"""Two Patoshi classifiers disagree almost entirely along ONE axis: whether the coinbase was spent.

WHERE THIS CAME FROM
--------------------
Not from us. The method's own author states the rule, in public, in his own words
(github.com/janoside/btc-rpc-explorer discussions/465, SergioDemianLerner, 29 Aug 2022):

    "The Patoshi pattern finding algorithm attributes blocks with different probabilities.
     Some blocks are unequivocally Patoshi's, some are really hard to tell. IN CASE OF DOUBT,
     THE ALGORITHM CHECKS IF THE COINBASE IS UNSPENT, AND IN THAT CASE IT CONSIDERS THE BLOCK
     PART OF PATOSHI. I don't think a block explorer should attribute blocks to Patoshi without
     a warning that there are false positives and false negatives."

That sentence turns a vague "the sets differ" into a testable question about HOW they differ.
OUR SIDE'S INDEPENDENCE FROM SPEND DATA -- CHECKED IN THE CODE, NOT ASSUMED.
An earlier draft of this file asserted "our classifier uses no spend information whatever". That
needed verifying, because this repo's own README says slots.py "validates against dormancy". It
does -- but as a REPORTED DIAGNOSTIC, not as an input. The label is:

    patoshi_confirmed = nonce_lsb_ok AND phi >= 0.5 AND 1 <= height <= era_end

  nonce_lsb_ok  patoshi.py, the LSB criterion            no spend data
  phi           local rolling LSB pass rate               no spend data
  era_end       slots.py era_end(), thresholded on that   no spend data
                same LSB rate
  coinbase_spent  read ONLY by spend_rate(), which prints a PASS/CHECK line

=> The label is a function of nonce-LSB structure alone, so spend structure in the gap cannot
   originate in our labelling rule.

⚠️ ONE HONEST QUALIFICATION. This repo's stated validation EXPECTS the confirmed set to be
   ~0% spent. Spend data therefore informed confidence in the method even though it never
   enters a label -- a weaker dependence than an input, and not zero. Recorded so nobody has
   to discover it later.

⚠️ THE OBVIOUS TEST IS A TRAP, AND THE FIRST DRAFT OF THIS SCRIPT FELL INTO IT.
"Blocks only THEY accept should be unspent" sounds like a prediction. It is not a test: the
blocks BOTH classifiers accept are already 99.9% unspent, because Patoshi's coins famously never
moved. Confirming 100% against a 99.9% base rate confirms nothing.

  => The informative direction is the OPPOSITE one: blocks only WE accept are 85% SPENT,
     against an agreed-set rate of 0.1%. THAT is the separation, and it is ~864x.

WHAT THE SEPARATION WOULD MEAN, IF READING (a) BELOW IS THE RIGHT ONE
----------------------------------------------------------------------
A classifier that consults spend history is not a function of block structure alone. It is a
function of THE CHAIN'S FUTURE: a doubt-case block counted as Patoshi today should, by the stated
rule, stop counting the moment its coinbase moves.

  => Such a set cannot be a fixed consensus predicate. A rule of the form
     "freeze Satoshi's coins if they have not moved" keyed on a set that ALREADY USED
     "has not moved" as a criterion is not measuring two things. It is measuring one twice.

  => And it reframes the LARGEST published error figure. Whale Alert's authors flag 31 of 50 as
     possible false positives -- but those 50 are the SPENT coinbases, i.e. exactly the
     population the tiebreaker discriminates against. That is a structural worst case, not a
     representative rate, and nobody appears to have said so.

FAIRNESS, IN BOTH DIRECTIONS
----------------------------
  * The tiebreaker is a REASONABLE heuristic for a historical study. It is disclosed, and the
    author volunteered it unprompted. He also said explorers should not tag without a warning.
  * He makes a counterpoint this script does not refute: "even if you subtract all disputed
    blocks from the grand total, it doesn't change much the amount of bitcoins mined by Patoshi."
    ON THE AGGREGATE HE IS RIGHT -- the disputed blocks are a small fraction of the total.
    The objection here is not to the aggregate. It is to per-block use in a rule.
  * TWO READINGS FIT THE DATA and this measurement cannot separate them: their tiebreaker
    excluding spent doubt-cases, or OUR classifier having false positives concentrated among
    spent coinbases (early non-Patoshi miners being exactly who spent theirs). We do not claim
    to know which. Everything above is conditional on that being unresolved.
  * NOTHING here shows either set is wrong. No 2009-era key has ever signed anything, so no
    ground truth exists and none can. Only the SHAPE of the difference is measurable.

Run:  python verify/patoshi_spend_axis.py
"""
import csv
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)

BASELINE = 45.6   # unspent rate across all scored blocks, printed below and recomputed


def load():
    conf = os.path.join(REPO, "patoshi_confirmed.csv")
    ours, spent, phi = set(), {}, {}
    with open(conf, newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            if not r["height"].isdigit():
                continue
            h = int(r["height"])
            spent[h] = r["coinbase_spent"] == "1"
            phi[h] = float(r["phi"] or 0)
            if r["patoshi_confirmed"] == "1":
                ours.add(h)
    snap = os.path.join(REPO, "data", "btc-rpc-explorer-patoshi.json")
    theirs = set(int(h) for h in json.load(open(snap, encoding="utf-8"))
                 ["block_heights"]["Patoshi"]["heights"])
    return ours, theirs, spent, phi


def unspent_pct(S, spent):
    S = [h for h in S if h in spent]
    if not S:
        return 0.0, 0
    return 100.0 * sum(1 for h in S if not spent[h]) / len(S), len(S)


def main():
    ours, theirs, spent, phi = load()
    top = max(ours)
    # ⚠️ Same range control as patoshi_setdiff.py, and for the same reason: compare only
    # where BOTH sets are live. Using only an upper bound here (and not theirs' lower bound
    # of 3) produced 1,327 where the set-diff produced 1,325 -- a two-block discrepancy
    # between two of our own scripts, which is exactly how a corpus starts drifting.
    lo = min(theirs)
    ours_r = {h for h in ours if lo <= h <= top}
    both = ours_r & theirs
    only_ours = ours_r - theirs
    only_theirs = {h for h in theirs if h <= top} - ours_r

    print("=" * 84)
    print(" THE SPEND AXIS — measured, after the other author told us where to look")
    print("=" * 84)
    print("  Comparison restricted to heights %d..%d, where both classifiers are live." % (lo, top))
    print()
    print("  %-26s %8s %12s" % ("population", "n", "UNSPENT"))
    print("  " + "-" * 50)
    base, nbase = unspent_pct(set(spent), spent)
    rows = [("all scored blocks (baseline)", set(spent)),
            ("agreed Patoshi by both", both),
            ("OURS only", only_ours),
            ("THEIRS only", only_theirs)]
    vals = {}
    for name, S in rows:
        p, n = unspent_pct(S, spent)
        vals[name] = p
        print("  %-26s %8d %11.1f%%" % (name, n, p))

    print()
    print("=" * 84)
    print(" THE PREDICTION, AND WHAT ACTUALLY HAPPENED")
    print("=" * 84)
    t, o = vals["THEIRS only"], vals["OURS only"]
    agreed = vals["agreed Patoshi by both"]
    print("  predicted: THEIRS-only should skew UNSPENT (his tiebreaker admits unspent doubt-cases)")
    print("  observed : THEIRS-only %.1f%% unspent" % t)
    print()
    print("  ⚠️ AND ON ITS OWN THAT IS NEARLY MEANINGLESS, which the first draft of this script")
    print("     missed. The blocks BOTH classifiers accept are already %.1f%% unspent — Patoshi's" % agreed)
    print("     coins famously never moved. 100.0%% against a %.1f%% base rate is +%.1f points." % (agreed, t - agreed))
    print("     A prediction that a set is unspent, in a population that is already all unspent,")
    print("     is not a test. Reporting it as a confirmation would have been a real error.")
    print()
    print("  ★ THE LOAD-BEARING OBSERVATION IS THE OTHER SIDE, and it is not subtle:")
    print()
    print("       blocks BOTH accept        %5.1f%% spent" % (100 - agreed))
    print("       blocks only WE accept     %5.1f%% spent      <-- %.0fx enrichment"
          % (100 - o, (100 - o) / max(0.001, 100 - agreed)))
    print()
    print("  (our label = nonce_lsb_ok AND phi>=0.5 AND height<=era_end; all three derive from")
    print("   nonce LSBs. coinbase_spent is read only to PRINT a validation line. Verified in")
    print("   slots.py, not assumed -- see this file's header for the one qualification.)")
    print()
    print("  ⇒ The %d blocks our classifier accepts and theirs rejects are OVERWHELMINGLY" % len(only_ours))
    print("    SPENT, against an agreed-set rate near zero. The disagreement is concentrated")
    print("    almost entirely on spent coinbases.")
    print()
    print("  ⚠️ TWO READINGS FIT THIS, AND THIS MEASUREMENT CANNOT SEPARATE THEM:")
    print("      (a) their tiebreaker EXCLUDES spent doubt-cases — which is what its author")
    print("          says the algorithm does, so this is his design showing through; or")
    print("      (b) OUR classifier has false positives, concentrated among spent coinbases")
    print("          because early non-Patoshi miners are exactly who spent theirs.")
    print()
    print("    ★ What can be said either way: our classifier consults NO spend data, so the")
    print("      85% figure cannot originate in our design. It is a property of the gap.")
    print("      Which side owns it is undetermined, and we do not claim to know.")

    print()
    print("=" * 84)
    print(" WHY IT MATTERS FOR ANY RULE THAT KEYS ON THE SET")
    print("=" * 84)
    print("  ⚠️ EVERYTHING IN THIS SECTION IS CONDITIONAL ON READING (a) ABOVE. If reading")
    print("     (b) is correct, none of it follows and the separation is our own false")
    print("     positives. It is stated as an implication, never as a conclusion.")
    print()
    print("  A classifier that consults spend history is a function of the chain's FUTURE.")
    print("  By the stated rule, a doubt-case block counted as Patoshi today stops qualifying")
    print("  the moment its coinbase moves.")
    print()
    print("  ⇒ 'freeze the coins that have not moved', keyed on a set built partly from")
    print("    'has not moved', measures one property twice and calls it corroboration.")
    print()
    print("  ⇒ It also reframes the largest published number: Whale Alert flag 31 of 50 possible")
    print("    false positives, but those 50 are SPENT coinbases — precisely the population")
    print("    this tiebreaker discriminates against. A structural worst case, not a rate.")
    print()
    print("  ⚠️ NOT A CRITICISM OF THE HEURISTIC. It is disclosed, it was volunteered, and for")
    print("     a historical study it is reasonable. Its author also said explorers should not")
    print("     tag blocks without a false-positive warning, and that subtracting the disputed")
    print("     blocks barely moves the AGGREGATE — which is true, and not in dispute here.")
    print()
    print("  ⚠️ AND NO GROUND TRUTH EXISTS. No 2009-era key has ever signed anything. Neither")
    print("     set can be shown right or wrong. Only the shape of the difference is measurable.")
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())
