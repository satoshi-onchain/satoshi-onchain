# Excavation — empirical facts about the Patoshi/Satoshi miner

Machine-derived facts from the labeled early-block data (`patoshi_confirmed.csv` +
`early_blocks_merged.csv`, blocks 0–60,000). Every number is a count or arithmetic over public block
data. **No interpretation, no narrative.** Reproduce: `python excavate.py`.

Grade: **[forensic]**, never [cryptographic] — nothing here involves a key or a signature. The one
key/signature anchor tying this footprint to "Satoshi" lives outside this file (block 9 → block 170
Finney transaction; see the `bitcoin-origin-claims` verification of that signature).

## 1. Spend / dormant ledger (high-confidence Patoshi set, phi ≥ 0.5)

| Quantity | Value |
|---|--:|
| high-confidence Patoshi blocks | 18,589 |
| total coinbase | 929,450 BTC |
| **unspent (dormant)** | **872,200 BTC** (17,444 blocks, **93.8%**) |
| ever spent | 57,250 BTC (1,145 blocks, 6.2%) |
| era-wide estimate (excess-over-chance) | **~22,540 blocks ≈ 1,127,001 BTC** |

The high-confidence set is a lower bound (counts only where Patoshi dominates); the excess-over-chance
estimate (~22,540 / ~1.13M) is the rigorous count and matches Lerner (~22,000 / ~1.1M).

## 2. Diurnal (hour-of-day) activity — NO sleep cycle

UTC hour-of-day block-production histogram is **statistically flat**:

| Window | n | min/hr | max/hr | χ² (23 dof) | verdict |
|---|--:|--:|--:|--:|---|
| full era (~1.5 y) | 18,589 | 727 | 817 | **10.0** | uniform |
| early (blocks 1–15,000) | 12,041 | 475 | 536 | **9.3** | uniform |
| restarts (ExtraNonce step-downs) | 1,445 | 48 | 78 | — | ~flat |

χ² ≈ 10 against a 23-dof threshold of 35.2 (p=0.05): the hour-of-day distribution is **indistinguishable
from uniform**. **Empirically, the mining machine ran ~24/7 with no diurnal ("sleep") gap.** This
*confirms* the Patoshi fingerprint (§4) while finding **no** support in block production for the popular
daily-sleep-schedule claim. (Boundary: this tests the *diurnal* cycle only; day-level or longer on/off
patterns are not tested here.)

## 3. ExtraNonce structure (single-miner tracks)

- ExtraNonce range **1 … 9,688**; consecutive deltas are small positives (mode +1, then +2, +3, …).
- **1,445 step-downs** ("resets") over 18,589 blocks — the ExtraNonce climbs within a session, then
  restarts. Interpreted as an artifact only: a single incrementing counter restarted ~1,445 times.
- First run (heights:ExtraNonce): `1:4 2:11 3:14 … 14:62` then restart `15:10 16:11 …` — the sawtooth.

## 4. Nonce low-byte bands — the fingerprint (non-circular, over ALL era blocks)

Per-value average count of each low-byte value across blocks 1–54,458:

| low-byte set | # values | avg count / value | vs baseline |
|---|--:|--:|--:|
| band {0–9} | 10 | 672.3 | ×5.4 |
| band {19–58} | 40 | 551.3 | ×4.4 |
| **in-band (both)** | 50 | 575.5 | **×4.62** |
| gap {10–18} | 9 | 122.1 | ×0.98 (baseline) |
| gap {59–255} | 197 | 124.8 | ×1.00 (baseline) |

The gaps sit exactly at the non-Patoshi baseline (~124.7/value): **Patoshi's winning nonce low-byte was
never in {10–18} or {59–255}.** Excess per in-band value × 50 = **~22,540 blocks** (independent
cross-check of §1). The full nonce is only mildly low-biased (53.7% < 2³¹ vs 50% uniform) — the sharp
signal is the low-byte bands, not the magnitude.

## 5. Track reconstruction (mining sessions between restarts)

- **1,446 tracks** (runs between ExtraNonce restarts).
- Track length: mean **12.9 blocks**, median 8, max 178.
- ExtraNonce slope within a track: median **~46 / block** (mean skewed by outliers).
- Consistent with a single machine: ExtraNonce climbs ~linearly within a session, then restarts.

## 6. Which Patoshi coins moved (the 6.2% ever spent)

- 1,145 spent Patoshi coinbases (57,250 BTC).
- **Spend rate rises with height** — the *earliest* coins are the *most* dormant:

  | height band | spent / total | rate |
  |---|--:|--:|
  | 0–4,999 | 189 / 4,018 | 4.7% |
  | 5,000–9,999 | 205 / 4,078 | 5.0% |
  | 10,000–14,999 | 219 / 3,944 | 5.6% |
  | 15,000–19,999 | 272 / 3,808 | 7.1% |
  | 20,000–24,999 | 260 / 2,741 | 9.5% |

- Earliest spent Patoshi coinbases (heights): `9, 286, 357, 394, 413, 624, 651, 658, 688, 702, 720, 730`.
  **Block 9 is the first** — the coinbase spent in block 170 to Hal Finney (the signature of that spend
  is verified in `bitcoin-origin-claims`; it is the one hard key-anchor for the whole footprint).

## 7. Hashrate / throttle (difficulty from coinbase nBits × timestamps) — `deepdig.py`

- **Difficulty stayed exactly 1.00 through all of 2009**, then rose only in 2010 (1.27 Jan → 2.27 Feb
  → 4.36 Mar → 8.10 Apr → 12.55 May → 16.62 Jun).
- **Confirmed-Patoshi monthly share:** 85% (2009-01) → 78–82% (spring) → 71% (Jul) → 58% (Aug) → 73%
  (Sep) → **3% (Oct) → 0% (Nov 2009)**. Patoshi *dominance* is a 2009 phenomenon; the weaker LSB tail
  persists to block ~54,458 (late 2010) but the high-confidence set is essentially the first ~10 months.
- Network hashrate was **~5–12 MH/s** in 2009 (diff·2³²/interval).
- **The restraint is visible:** difficulty never left 1.00 while Patoshi produced 58–85% of blocks — the
  miner held a roughly constant, modest rate and **did not ramp**; difficulty rose only in 2010, *after*
  Patoshi's share had collapsed and others arrived.

## 8. Dark-period gaps (finer than hour-of-day) — `deepdig.py`

- 18,588 consecutive high-confidence Patoshi intervals: **median 16.4 min, mean 20.6 min.**
- Near-continuous, **but not unbroken**: 149 gaps >1 h, 79 >3 h, **45 >6 h**, 17 >12 h, **max 126 h
  (~5.3 days).**
- Combined with §2 (χ²=10, no diurnal cycle): the machine mined **near-continuously with no daily
  rhythm**, punctuated by **sporadic multi-hour/multi-day outages** that are *not* on a daily schedule.
  (More complete than either "24/7" or "slept nightly".)

## 9. What Satoshi did with block 9 — the first spent coinbase (Tier C) — `spend_chain.py`

Block 9's 50-BTC coinbase (P2PK to key `0411db93…`) is the **first Patoshi coinbase ever spent.** Its
full spend path, parsed from the raw transactions (chain-linked, self-verifying):

| block | tx | payment (new key) | change (block-9 key) |
|--:|---|--:|--:|
| 170 | `f4184fc5…` | 10 BTC → `04ae1a62…` (first-ever payment, recipient Hal Finney) | 40 BTC |
| 181 | `a16f3ce4…` | 10 BTC → `04b5abd4…` | 30 BTC |
| 182 | `591e91f8…` | 1 BTC → `0401518f…` | 29 BTC |
| 182 | `12b5633b…` | 1 BTC → `04baa9d3…` | 28 BTC |
| 183 | `828ef3b0…` | 10 BTC → `04bed827…` | **18 BTC (UNSPENT to date)** |

- **32 BTC** paid out to **5 distinct new keys**; the **block-9 key was reused as change** at every hop.
- The final **18 BTC change (block 183, 12 Jan 2009) has never moved** (blockstream: `828ef3b0` vout1
  unspent; vout0 spent at block 496).
- Key-reuse fact: the block-9 key signed 5 times here (nonces all distinct — verified separately). No
  other Satoshi coinbase key appears in these spends — **fresh recipient key per payment.**

## Next excavations (fetch-gated — not in the current CSV)

- **Distinct coinbase pubkeys per block** (P2PK output scripts) — to count distinct Satoshi keys over
  the full ~22,540 blocks and confirm fresh-key-per-coinbase. The spend chain (§9) already shows
  fresh recipient keys per payment; the full coinbase-key set needs the coinbase `scriptPubKey`
  (empty in the current CSV — acquire via the RPC/BigQuery path in `acquire_rpc.py`/`acquire.sql`).
- **Per-thread nonce partition** — the multi-thread reconstruction from the band densities (§4/C):
  the 50 in-band values are used ~uniformly (density ratio {0..9}:{19..58} ≈ 0.91), consistent with
  even coverage of a restricted range; the exact thread count is not yet pinned.
- **Full spend-graph of every spent Patoshi coinbase** (1,145 of them) — extend `spend_chain.py`'s
  method chain-wide to map which awakenings trace to which coinbase (feed `judge.py`).

*(Done since the first draft: §7 hashrate/throttle, §8 dark-period gaps, §9 the block-9 spend chain.)*
