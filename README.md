# Satoshi on-chain: a reproducible verifier + Patoshi classifier

> **Scope.** Experimental laboratory research, in progress and expected to change. It reports what
> published, re-runnable methods find in public material — statistical and machine-verifiable
> findings, graded by their evidence — and draws no conclusion beyond them. Not money, not advice,
> no warranty. Details in [RIGHTS.md](RIGHTS.md).

**Goal.** Reconstruct *the verifiable on-chain footprint of the original Satoshi on the
original Bitcoin chain* — nothing that rests on off-chain claims or the word "Satoshi"
in someone's mouth. Every figure here is meant to be re-derivable from the chain itself
(a synced Bitcoin Core node, or the public `bigquery-public-data.crypto_bitcoin`
dataset), in a reproducible-measurement style — every figure re-derivable from public data.

The honest epistemics up front — three tiers, and we do not blur them:

| Tier | What | Certainty |
|---|---|---|
| **A. Definitional** | The genesis block (height 0) — hardcoded in the consensus rules; its coinbase message, key, and unspendable 50 BTC. | **Certain.** It *is* the chain's first constant. |
| **B. Statistical** | The **Patoshi** blocks — one dominant early miner fingerprinted by block-header structure (Lerner 2013). ~22.5k of the first ~54k blocks, ≈1.13M BTC attributed (Lerner 2013: ~22k, ~1.1M), of which about 94% has not been spent. Widely attributed to Satoshi. | **Statistical, not cryptographic.** A fingerprint, not a signature. |
| **C. Attested spend** | Block 170 — first payment, 10 BTC to `04ae1a62…` (Hal Finney), spending block 9's Patoshi coinbase; block 9's 50 BTC was then spent down through block 183 (`spend_chain.py`, `EXCAVATION.md` §9). | **On-chain certain**: block 9's coinbase was spent across 5 payments to 5 distinct new keys, reusing the block-9 key as change, leaving 18 BTC unspent to date. "It was Satoshi" rests on tier B. |

**The line we do not cross.** No genesis-era or Patoshi key has produced a
verifying signature. Only that would upgrade Tier B from *attributable* to *proven*.
Every public "I am Satoshi" claim (including the one rejected in *COPA v Wright* [2024] EWHC
1198 (Ch)) fails exactly this test. The ≈1.13M BTC staying largely silent since 2009 is itself the
strongest ongoing statement: the keys have not spoken, and no one else can make them speak.

---

## What's in here

| File | Role |
|---|---|
| `TIEBREAKER-CONSEQUENCES.md` | Three consequences of Lerner's disclosed unspent-coinbase tiebreaker that we have not found stated elsewhere (time-unstable membership; circularity of dormancy-keyed freeze policies; spent-subsample error rates as a structural worst case). The search is recorded in the file; pointers to prior statements are welcome. |
| `anchors.py` | The Tier-A/C verified anchors (genesis, block 9→170) as checkable claims + a `verify()` that confirms them against real block/tx data you supply. |
| `acquire.sql` | BigQuery: pull `height, timestamp, nonce, coinbase_script_hex, coinbase_value, coinbase_spent` for blocks 0–60,000. |
| `acquire_rpc.py` | The authoritative alternative: build the same CSV from a synced Bitcoin Core node via `getblock` RPC (node-derived, [C-chain]-grade). |
| `patoshi.py` | Parse the ExtraNonce from each coinbase, apply Lerner's LSB criterion, tally the attributed coins, and check dormancy. Emits `patoshi_labeled.csv` + a summary. |
| `merge_spent.py` | Fold the optional dormancy result (Query B) into the classification CSV by height. |
| `slots.py` | **Refine the LSB upper bound into a Patoshi *estimate*** via local excess-over-chance, and **validate it against dormancy** (a signal the LSB test does not see). Emits `patoshi_confirmed.csv` + `patoshi_intensity.png`. |
| `judge.py` | **The verdict tool.** For any block height, is the coin Satoshi's? GENESIS / PATOSHI / AMBIGUOUS / NOT-PATOSHI, with dormancy. Turns every "old wallet moved" headline into a checkable answer. |
| `plots.py` | Reproduce the "fingerprint": ExtraNonce-vs-height scatter (the Patoshi tracks) and the rolling nonce-LSB pass-rate (the era curve). |

Stdlib only, except `plots.py` (matplotlib). Nothing here needs network access at
run time once you have the block CSV.

---

## The method (faithful to Lerner 2013)

Sergio Demian Lerner's "Patoshi pattern" separates one early miner from the rest using
structure the miner's software inadvertently leaked into every block header:

1. **ExtraNonce slope (primary).** The coinbase scriptSig carries an ExtraNonce the
   miner increments. Plotted against block height, Patoshi's values fall on a set of
   tightly-correlated, near-linear tracks distinct from the rest of the network — the
   signature of a single, coordinated machine. `plots.py` reproduces this; the tracks
   are visible by eye.
2. **Nonce LSB restriction (corroborating).** For Patoshi blocks the low byte of the
   header nonce is confined to `0–9` or `19–58` — an artifact of how the miner split the
   nonce space across its parallel search slots. `patoshi.py` applies this as an automatic
   first-pass label (`nonce & 0xFF ∈ [0,9] ∪ [19,58]`).
3. **The result.** ~22,000 of the first ~50,000 blocks; ≈1.1M BTC; the signature
   **vanishes near block ~54,000 (late 2010)**, coinciding with Satoshi's exit.

**Honesty about the classifier.** The nonce-LSB filter is a clean automatic heuristic,
but the *authoritative* attribution is Lerner's ExtraNonce-track clustering, which is a
statistical/visual separation this repo helps you *see* (via `plots.py`) rather than
fully automate. Blocks near the ~54,000 boundary carry attribution uncertainty. Treat
`patoshi.py`'s labels as a faithful reproduction of the *approach*, cross-check against
the plotted tracks, and remember: this is **[statistical], not [cryptographic]** — every
claim is graded with an explicit evidence-tier discipline (definitional / statistical / attested).

---

## Reproduce

```bash
# 1. Acquire the early-block CSV (pick one path)
#    a) node-derived (authoritative):
python acquire_rpc.py --rpc http://user:pass@127.0.0.1:8332 --max-height 60000 > early_blocks.csv
#    b) or BigQuery: run acquire.sql, export the result to early_blocks.csv

# 2. Verify the Tier-A / Tier-C anchors against the same data
python anchors.py --blocks early_blocks.csv --rpc http://user:pass@127.0.0.1:8332

# 3. Classify Patoshi blocks, tally the coins, check dormancy
python patoshi.py early_blocks.csv          # -> patoshi_labeled.csv + summary

# 4. See the fingerprint
python plots.py patoshi_labeled.csv          # -> extranonce_fingerprint.png, nonce_lsb_rate.png
```

Expected order-of-magnitude from step 3: ~22k Patoshi blocks, ≈1.05–1.1M BTC, of which
about 6% (1,145 coinbases, 57,250 BTC) has been spent; the rest is unspent. (Non-Patoshi early
miners *have* moved coins — e.g. the “Satoshi-era wallet” movements reported in 2025–26 — and the
classifier is exactly what lets you show those fall outside the Patoshi set.)

---

## Reproduced results (run 2026-07-22, `bigquery-public-data.crypto_bitcoin`, blocks 0–60,000)

Actual output from the pipeline above on a full BigQuery pull (60,001 blocks; nonce read
as hex, the dataset's format):

| Quantity | Measured | Lerner reference | Reading |
|---|---:|---:|---|
| Nonce-LSB filter passes | **29,837** (49.7%) | — | Upper bound: true Patoshi + chance passers |
| Predicted if ~22k Patoshi + 19.5% chance on the rest | ~29,400 | — | **Measured 29,837 ≈ predicted** ✓ |
| Coins under the LSB filter | **1,491,850 BTC** | — | Upper bound (includes chance passers) |
| — of which **unspent** | **1,170,350 BTC** | ≈1.1M BTC | **Lands on Lerner** ✓ |
| — of which spent | 321,500 BTC | ~0 (true Patoshi) | Mostly chance-passers; block 9 → Finney is in here |
| Patoshi-era end (LSB rate → baseline) | **block 54,458** | ~54,000 (late 2010) | **Lands on Lerner** ✓ |
| Fingerprint | sawtooth ExtraNonce tracks, visible by eye | Lerner's tracks | See `extranonce_fingerprint.png` |

The nonce-LSB rate starts at ~97% (Satoshi mining nearly alone), holds ~80% to block
~16,000, then declines as other miners arrive and collapses to the 19.5% chance baseline
at ~54,000–55,000 — see `nonce_lsb_rate.png`. **Dormancy cross-check:** these dormant Patoshi coinbases are bare P2PK outputs, so their public keys
have been on the chain since 2009; they belong to the class most exposed to a break of elliptic-curve
signatures.

### Refined estimate — `slots.py` (excess-over-chance, dormancy-validated)

The LSB filter over-counts by the chance-passers. `slots.py` removes them two independent
ways, restricted to the Patoshi era (blocks 1–54,458):

| | Result | Lerner |
|---|---:|---:|
| **(1) Excess-over-chance count** — `N = N_era − n_fail/(1−p0)`, closed form | **22,540 blocks** | ~22,000 |
| **(2) Intensity-integrated** — `Σ φ(h)`, `φ = clip((ρ(h)−p0)/(1−p0),0,1)` | **22,539 blocks** | ~22,000 |
| Estimated Patoshi coins | **~1,126,974 BTC** | ~1,100,000 |
| (raw LSB upper bound, for contrast) | 28,774 blocks | — |

Two estimators built on different principles land within **one block** of each other and on
Lerner. `φ(h)` — the fraction of blocks near height `h` that are Patoshi — is the whole
story in one curve (`patoshi_intensity.png`): ~94% at the start, decaying to 0 exactly at
the era end. **The area under it is the count.**

**Dormancy validation (independent — the LSB test cannot see spends):**

| Population | Coinbase spend rate |
|---|---:|
| High-confidence Patoshi (`φ ≥ 0.5`) | **6.2%** |
| Discarded chance-passers (LSB-pass, low `φ`) | 42.5% |
| LSB-fail background (ordinary miners) | 86.7% |

The confirmed set is **14× more dormant than background** and **6.9× more than the discarded
chance-passers** — ordered exactly as the labels predict, corroborated by a signal the
classifier did not use. (The residual 6.2% is genuine early Satoshi test-spends — e.g. block
9 → Finney — plus some transition-zone contamination; it is not zero, and we don't pretend it
is.)

**Remaining honest bound:** the *count* (~22.5k) is rigorous; per-block *hard* labels are
confident only where Patoshi dominates. Near/after ~54k, individual LSB-passers are
genuinely 50/50 — that ambiguity is a fact about the chain, not a gap in the tool.

### Judge a real awakening — `judge.py`

When a "Satoshi-era wallet just moved N BTC" headline lands, resolve it to a verdict:

```bash
python judge.py --demo                 # one real block of each verdict, auto-selected
python judge.py 9 1 12                  # -> PATOSHI(spent, Finney) / PATOSHI(dormant) / NOT-PATOSHI
# resolve a real event to heights first (Query C in acquire.sql), then:
python judge.py --file heights.csv
```

A Patoshi coin is a coinbase P2PK output, so a spend consumes a coinbase directly — the
spending tx's input outpoint *is* an early coinbase. **Query C** turns a spending txid (or a
funding address) into originating coinbase height(s); `judge.py` rules each PATOSHI /
AMBIGUOUS / NOT-PATOSHI against the validated set. This is exactly what shows the “Satoshi-era wallet”
movements reported in 2025–26 fall outside the Patoshi set (verdict NOT-PATOSHI) — and, conversely, would flag it
instantly and unambiguously if the Patoshi cluster moved. Teaching case from the demo:
**block 12 is dormant but NOT Patoshi** (nonce LSB = 63, out of range) — dormancy alone is
not proof of Satoshi.

---

### Provenance — the exposed key is original, not incidental

The quantum-exposed coin class these Patoshi coinbases belong to is **not a later design
accident.** The earliest public Bitcoin source — the 15 Nov 2008 pre-release (archive
SHA256 `f0327ebbea17f7d6e14be5f5534c6ff16c7648f588cbb096fc8fdfcb7e071abf`, re-verified here
against the Satoshi Nakamoto Institute listing) — already locks every visible output as
**bare P2PK** (`<pubkey> OP_CHECKSIG`), with **no P2PKH pattern**
(`OP_DUP OP_HASH160 … OP_EQUALVERIFY OP_CHECKSIG`) anywhere in its payment paths. Coinbase,
change, and send outputs all expose the public key at rest. So the early Satoshi/Patoshi
coinbases tracked here carry public-key exposure from Bitcoin's *first* public source line,
not from a later convention — reinforcing why this dormant value is precisely the
quantum-relevant class. (Verified directly from the hash-anchored archive: the pre-release's
visible payment paths contain no `OP_DUP`/`OP_HASH160`/`OP_EQUALVERIFY`, only bare
`OP_CHECKSIG`.)

---

## Scope notes

- **"Original Bitcoin" is unambiguous here.** Every block studied predates any fork (mining and the
  block-170 payment, 2009–2010), so the same early history is read identically on every chain that
  inherits it; nothing here depends on which chain is consulted.
- **What we *cannot* get.** Satoshi's identity; cryptographic proof Patoshi = Satoshi. (Satoshi
  *did* spend on-chain in Jan 2009 — block 9's coinbase was spent down through block 183, and ~1,145
  of the ~22,540 Patoshi coinbases were later spent; see `EXCAVATION.md` §6/§9. But the **bulk — the
  ~1.1M-BTC Patoshi hoard — sits dormant**, and the dormancy *is* the data.)

## Sources
- S. D. Lerner, "The Well Deserved Fortune of Satoshi Nakamoto" (bitslog, 2013) and
  follow-up Patoshi analyses — the ExtraNonce/nonce methodology.
- Genesis + block-170/Hal-Finney facts: the chain itself (verify via `anchors.py`).
- Dormancy status (2026): public analytics dashboards (not re-derived here); the Patoshi
  cluster remains unmoved while non-Patoshi Satoshi-era coins have awakened.

---

**Rights, sourcing and corrections:** see [RIGHTS.md](RIGHTS.md) — what this project uses,
where it comes from, how named people are treated, and how to ask for a correction.
