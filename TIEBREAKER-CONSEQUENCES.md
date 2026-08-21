# The unspent-coinbase tiebreaker, and three consequences nobody had drawn

*First published in this repository, 21 August 2026. A prior-art search on that date — academic
papers, Bitslog, Lopp's tools and blog, Whale Alert, Elementus, the Gudmundsson thesis, GitHub
code and discussions, X — found sources that note classifier uncertainty in general, and none
that identify the spend-history dependency below or its consequences. We therefore state them
here as original analysis, citing only the disclosed design they follow from.*

---

## The disclosed design

On 29 August 2022, in GitHub discussion `janoside/btc-rpc-explorer#465`, Sergio Demian Lerner
described his Patoshi classifier:

> "The Patoshi pattern finding algorithm attributes blocks with different probabilities. Some
> blocks are unequivocally Patoshi's, some are really hard to tell. **In case of doubt, the
> algorithm checks if the coinbase is unspent, and in that case it considers the block part of
> Patoshi.**"

For a historical study this is a reasonable heuristic, and it was disclosed voluntarily. Nothing
below is a criticism of the choice. What follows are its logical consequences, which do not
appear to have been published by anyone.

## Consequence 1 — membership is partly a function of spend history, so the set is not stable in time

A doubt-case block is *in* the Patoshi set **because its coinbase has not moved**. If that
coinbase ever moves, the same algorithm run again assigns the block differently: the set's
membership depends on an input that changes over time. "The Patoshi set" is therefore not a fixed
historical attribution but a time-indexed one — *the set as of the spend state at evaluation
time* — and any consumer that hard-codes a block list (every public consumer we found does) has
frozen one evaluation of a moving function.

## Consequence 2 — a dormancy-keyed freeze policy on this set is circular

Proposals of the form *"freeze the dormant coins attributed to Satoshi"*, keyed on such a set,
use dormancy twice: once as an **input** to the attribution (the tiebreaker) and once as the
**trigger** of the policy. For every doubt-case block the reasoning is: *it is attributed because
it is dormant; it is frozen because it is attributed*. The policy manufactures part of its own
target class. Any such proposal must either restrict itself to the unequivocal subset (where the
tiebreaker never fired) or accept that its scope is partly self-referential.

## Consequence 3 — error rates measured on the spent subsample are a structural worst case

Published spot-checks of the classifier measure error on **spent** blocks (e.g. the ~31-of-50
figure circulated from the Whale Alert analysis), because a spend can expose evidence that
contradicts the attribution. But the tiebreaker *discriminates against spent coinbases by
construction*: a doubt-case block only entered the set while unspent. The spent subsample is
therefore enriched for exactly the borderline attributions most likely to be wrong — the
population least favoured by the tiebreaker. An error rate measured there is a **structural upper
bound**, not a representative rate; quoting it as representative overstates the classifier's
error, and quoting the dormant set's stability as accuracy understates the doubt cases inside it.

## What this changes here, and what it does not

This repository's evidence-tier discipline already labels the Patoshi set **[forensic], never
[cryptographic]**. These three consequences sharpen that label: the set is not merely statistical
rather than proven, its *membership rule itself is time-dependent* for the doubt cases. Nothing
in this repository keys any claim on dormancy, and the tier table in `README.md` is unaffected.

## A live instance, added the same day

Hours after this document was first published, a review of primary sources for the LayerTwo Labs
"eCash" (ECX) hard fork — `ecash-com/fast-facts` and Paul Sztorc's own posts — showed the exact
structure Consequences 1 and 2 describe, deployed: *"220 whitelisted 'repurpose' transactions
reassign Satoshi-era (Patoshi) coins without signatures"* (`setRepurposeTx`, `src/repo_txns.h`),
with the subset selected, in Sztorc's words, because *"having never availed the opportunity to
sell any portion of them … makes it nearly certain they were abandoned."*

That is dormancy used as an input to the attribution and as the justification of the
reassignment (Consequence 2), executed through a hard-coded transaction list that freezes one
evaluation of a time-dependent membership function (Consequence 1). We quote the project's own
materials and characterise nothing beyond what the structure entails; whether the policy is wise
is not this document's question. What it demonstrates is that these consequences are not
hypothetical: reassignment policies keyed on dormancy over Patoshi-derived sets exist in shipping
code, and their soundness turns on exactly the properties analysed above.

---

Anyone citing these consequences should cite Lerner's 2022 disclosure for the design and this
document for the consequences — that is the entire public chain as of the search date above.
