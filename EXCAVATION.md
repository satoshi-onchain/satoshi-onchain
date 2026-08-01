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

**Dormancy freshness (re-checked 1 Aug 2026):** a current full-history spend snapshot (BigQuery
`acquire.sql` Query B) vs the prior snapshot shows **0** Patoshi coinbases newly spent — the count
holds at exactly 1,145 spent / 17,444 unspent, and total early coinbases spent is unchanged at
32,647. The dormant hoard has not moved. (Re-run: export Query B → `spent_status.csv`, diff by
height; any unspent→spent flip in the Patoshi set is the tripwire → `judge.py`.)

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

## 10. Nonce structure & the thread question (`threads.py`)

Do the winning nonces reveal how many threads the miner ran? Over the confirmed set:
- **High bits are NOT a clean thread partition.** The nonce is ~uniform across the 32-bit range
  **except a ~2× excess in the lowest 1/16** (top nibble `0x0` = 11.3% vs 6.25% uniform; `0x1` slightly
  up; `0x2..0xf` ~flat). That low-end excess is the signature of an **incremental search restarting
  from a low nonce each block** (blocks found early land at low nonces).
- Splitting the range into K even slices, the per-slice spread grows *smoothly* with K (15% at K=2 →
  56% at K=8), driven by that single low-end excess — **not K discrete steps**. So a **thread count
  cannot be uniquely read from the winning-nonce distribution**; pinning N needs hash-rate/timing
  modelling (not done here). What *is* fixed: the low byte ∈ {0..9}∪{19..58} (50/256 values, widths
  10 and 40, used ~evenly). Reported as structure, not an inferred thread count.

## 11. Coinbase-key distinctness — fresh key per coinbase, WHOLE ERA (`coinbase_keys.py`)

Every early coinbase is bare P2PK (`41 <65-byte pubkey> ac`). Real sample (fetched):

| block | coinbase pubkey |
|--:|---|
| 0 | `04678afd…` |
| 1 | `0496b538…` |
| 2 | `047211a8…` |
| 3 | `0494b9d3…` |
| 9 | `0411db93…` |

**Whole-era count now confirmed (BigQuery `acquire.sql` Query D1, blocks 1–54,458):**

| metric | value |
|---|--:|
| coinbase outputs (index 0) | **54,458** |
| distinct output scripts | **54,458** |
| P2PK-type outputs | **54,458** |

All three are **equal**: every coinbase in blocks 1–54,458 is a **bare-P2PK output with a distinct
pubkey — zero key reuse across the entire early era.** Consistent with the v0.1 keypool. (Sample of
5 above → the same result at scale.)

**Pubkey-level cross-check (D2 exported, extracted locally by `coinbase_keys.py`):** the actual
65-byte P2PK pubkeys were pulled and de-duplicated, not just the script strings:

| set | coinbase P2PK outputs | distinct pubkeys | reused |
|---|--:|--:|--:|
| all early (blocks 0–54,458) | 54,459 | **54,459** | **0** |
| high-confidence Patoshi subset (φ≥0.5) | 18,589 | **18,589** | **0** |

So the **fresh-key-per-coinbase** fact holds at the key level, including the **18,589-block Patoshi
set — every Patoshi coinbase used a brand-new key, no reuse anywhere.** (54,459 vs D1's 54,458: D2
includes the genesis block 0 coinbase, which D1's `BETWEEN 1 AND 54458` excluded.)

## 12. The spent Patoshi coinbases fed to the verdict tool (`spent_patoshi.py`)

The **1,145** high-confidence Patoshi coinbases that were ever spent (57,250 BTC moved) — all fall in
**blocks 9–24,182** (the dominance window); earliest is **block 9** (→ `spend_chain.py`). Heights are
written to `spent_patoshi_heights.txt` (feed `judge.py`). The unspent complement (~1.1M BTC) is the
dormant hoard.

**The full awakening→coinbase map is now resolved** (`acquire.sql` Query E → `awakening_map.py`,
`patoshi_awakenings.csv`): all **1,145** spent Patoshi coinbases, each joined to the exact tx that
spent it and when. The count matches the independent enumeration above (cross-check). **When the
coins moved (by spend year):**

| year | Patoshi awakenings | | year | Patoshi awakenings |
|--:|--:|---|--:|--:|
| 2009 | 345 | | 2013 | 20 |
| 2010 | 285 | | 2014 | 2 |
| 2011 | **483** | | 2015 | 2 |
| 2012 | 6 | | 2020 | 1 |
| | | | 2024 | 1 |

- **97% of all Patoshi awakenings happened in 2009–2011** (1,113 / 1,145); after 2012 the set is
  essentially frozen — only **34** spends in 13 years, and just **two** since 2015 (one in 2020, one
  in 2024). The dormant hoard is not merely unspent — the *spending* of Patoshi coins effectively
  stopped after the early years.
- 2011 is the single biggest awakening year (483) — spends concentrate in the earliest era, then
  taper to near-zero, consistent with the height-banded spend-rate in §6.
- Earliest awakenings: `blk 9 → blk 170 @ 2009-01-12` (the Finney tx), `blk 286 → 524 @ 2009-01-15`,
  `blk 357 → 728 @ 2009-01-16`. Some early coinbases stayed dormant for years before moving
  (`blk 413 → blk 130673 @ 2011-06-14`).

## 13. Thread / core count — a bounded inference, not an integer (`threads_model.py`)

The winning-nonce distribution cannot pin the thread count (§10), so bound it from the **hashrate**
(chain-derived) ÷ a **per-core rate** (a 2009 hardware fact, off-chain — this is the error bar).

**Hashrate (chain-derived, solid).** Over the 23,893 confirmed Patoshi blocks of the difficulty-1 era
(all blocks < 32,256 have difficulty exactly 1.0 ⇒ expected hashes/block = 2³² = 4.295 × 10⁹; first
retarget was block 32,256, ~30 Dec 2009, by which point Patoshi's share was ~0):

| estimator (inter-Patoshi-block gap) | gap | hashrate |
|---|--:|--:|
| active mean (gaps ≤ 2 h) | 14.7 min | **4.88 MH/s** |
| median, Poisson-corrected (mean = median/ln2) | 12.8 min | 3.88 MH/s |
| all-gaps mean (counts idle → lower bound) | 16.8 min | 4.27 MH/s |

**⇒ Patoshi ran at ~3.9–4.9 MH/s while active** (early-2009 monthly peak ≈ 4.6 MH/s). Monthly rate:
4.6 (Jan) → 4.1–4.2 (Mar–May) → 2.7–2.8 (Aug–Oct). *The later decline is ambiguous:* at constant
difficulty a constant-hashrate miner finds a constant #blocks/month, so the drop is **either a real
throttle-down or the φ≥0.5 set undercounting Patoshi in the diluted zone** (more interleaved
non-Patoshi blocks → lower local LSB rate → φ falls below 0.5) — not cleanly separable. The clean
machine-capability number is the **early-2009 peak ≈ 4.5–4.9 MH/s**. It **never ramped** (cf. §7).

**Implied cores = hashrate ÷ per-core rate** (Satoshi's v0.1 miner used the *unoptimized* CryptoPP
path; the 4-way SSE2 speedup came later, ~mid-2010):

| per-core (MH/s) | 0.50 | 0.75 | 1.0 | 1.5 | 2.0 |
|---|--:|--:|--:|--:|--:|
| implied cores (@4.88 MH/s) | 9.8 | 6.5 | 4.9 | 3.3 | 2.4 |

**Verdict:** the chain pins the **hashrate** (~4–5 MH/s, un-ramped) but **not** the thread/core count,
which equals hashrate ÷ an off-chain per-core rate. Under plausible per-core rates the count is
**~2–10 cores**; at the likely ~1–2 MH/s/core it is a **single ordinary multi-core desktop (~2–5
cores).** No single integer is claimable from on-chain data alone — reported as a range. (Nonce
cross-check: winning-nonce top-nibble = 0 in **26.3%** of blocks vs 6.25% uniform — a single low-end
excess from frequent block rebuilds/ExtraNonce bumps, **not** K discrete thread bands; §10.)

**Band-structure cross-check (`threads_model.py` §5) — the fingerprint is a counter, not a thread map.**
If the low byte encoded a thread id (`thread = nonce mod K`), the Patoshi band {0–9}∪{19–58} would be an
exact **union of residue classes mod K**. It is not, for **any K in 2–32** — the bands are **contiguous
ranges**, a loop/counter artifact, not a residue partition (and within-band values are used ~uniformly,
§4). So the nonces carry **no thread-count signal**: the ~2–5-core figure rests on the hashrate bound
alone, and the exact count is genuinely un-pinnable from public data — a rigorous negative, not a gap.

**Two mining-mechanics refinements (`threads_model.py`).** (a) The hashrate now divides by the **exact**
difficulty-1 work `2²⁵⁶/(target+1) = 4,295,032,833` (`= 2³² · 65536/65535`, the pdiff-vs-bdiff value),
not the round `2³²` — a ~0.0015% correction that leaves the ~2–5-core conclusion intact but makes the
number exact. (b) The **ExtraNonce sawtooth (§3) is a mining necessity, not a stylistic choice**: at
difficulty 1 a full 32-bit nonce sweep finds a block only `1−1/e ≈ 63%` of the time, so `~37%` of sweeps
exhaust the nonce and must roll the coinbase ExtraNonce (→ new merkle root → fresh nonce space). The
fingerprint and the mining mechanics are the same fact from two sides. *(Both derived in the
`bitcoin-origin-claims` mining deep-dives; the neutral difficulty-1 exactness is also in OBL's
`retarget` module.)*

## 14. Nonce-safety of Satoshi's keys — the ECDSA-nonce audit (`nonce_safety.py`)

A reused or biased ECDSA nonce `k` recovers the private key from public signatures alone (reuse:
`k=(z₁−z₂)/(s₁−s₂)`, then `d=(s₁k−z₁)/r`). So "could a Satoshi key have leaked?" is a **checkable
predicate over public data** (`GROUP BY r`), never an assumption. The only place Satoshi keys ever
signed is the **block-9 coinbase key `0411db93`**, which signed the five spends of the block-9 change
chain (§9). Reconstructing each `SIGHASH_ALL` digest from the raw bytes and verifying:

| block | tx | verifies vs `0411db93` | nonce `r` |
|--:|---|:--:|---|
| 170 | `f4184fc5…` | ✓ | `4e45e169…` |
| 181 | `a16f3ce4…` | ✓ | `27542a94…` |
| 182 | `591e91f8…` | ✓ | `1f27e51c…` |
| 182 | `12b5633b…` | ✓ | `52ffc192…` |
| 183 | `828ef3b0…` | ✓ | `c12a7d54…` |

- **All 5 signatures verify; all 5 nonces are distinct (5/5 unique) → no reuse, no leak.** The RNG
  behaved. (Corroborating context: the real ECDSA-nonce key thefts — Android 2013, lattice sweeps
  2019 — all cluster post-2012; no Satoshi-era key appears in them.)
- **The ~1.1M-BTC unspent Patoshi coinbases (§1) are different keys that never signed at all** → no
  nonce exists to attack → **nonce-immune**. Their only exposure is quantum (the P2PK pubkey is
  on-chain, §11), not any classical nonce flaw.
- Boundary: "unspent ⇒ never-signed" is a **per-key empirical fact, not a theorem** — the block-9 key
  was itself reused as change — so it is *checked* here, per key, not assumed.

## 15. What would machine-verifiably prove control of a Satoshi key? (`authorship_test.py`)

The three-tier model rests on one predicate: **identity is key control, and key control is checkable.**
The only machine-verifiable proof that someone controls a Satoshi key is a signature over a **fresh
challenge** (fixed *after* the fact, so it can't be lifted from public data) under a known-Satoshi
public key — or, equivalently, **moving a known-Satoshi coin**. Using only public block-9 data and no
private key:

| step | check | result |
|---|---|:--:|
| [1] re-verify a **public** 2009 signature by `0411db93` against its own 2009 digest | `verify(pubkey, z₂₀₀₉, sig)` | **True** ("Verified OK") |
| [2] the **same** signature against a **fresh** challenge chosen now | `verify(pubkey, H(fresh), sig)` | **False** |

- **[1] is reproducible by anyone from public bytes**, holding no private key — so a passing
  verification of an *already-public* signature demonstrates control of **no** key. A signature binds
  to exactly one digest (the 2009 transaction's), and re-presenting it authenticates nothing new.
- **[2] is what a real proof requires** — signing a challenge chosen after the fact needs the private
  key. The control predicate
  `ECDSA_verify(known_satoshi_pubkey, H(fresh_challenge), sig) == True` (or a spend of a known-Satoshi
  coin) **has never returned True on-chain.**
- The **~1.1M-BTC dormant coinbases (§1) never signed at all** — there isn't even a public signature to
  re-present; only a fresh signature or a coin move could speak for them (§14: never-signed ⇒
  nonce-immune, quantum-only exposure).

Neutral cryptographic epistemics — no person, no external source, only public bytes. This is the
foundation under Tiers A/B/C: the tracker measures key-checkable facts and would flag instantly if any
known-Satoshi key ever signed a fresh message or moved a coin (`judge.py`).

## Next excavations (fetch-gated — not in the current CSV)

- ~~**Distinct coinbase pubkeys, full count**~~ — **DONE (§11):** BigQuery Query D1 confirms 54,458 /
  54,458 / 54,458 (outputs / distinct scripts / P2PK) over blocks 1–54,458 — fresh key per coinbase,
  whole era, zero reuse.
- ~~**Thread count**~~ — **DONE as a bounded inference (§13, `threads_model.py`):** the chain pins
  the hashrate (~4–5 MH/s, un-ramped) but not the core count (= hashrate ÷ off-chain per-core rate);
  bounded to ~2–10 cores, most plausibly a single multi-core desktop (~2–5). No integer claimable.
- ~~**Awakening→coinbase map for all 1,145 spent coinbases**~~ — **DONE (§12):** `acquire.sql`
  Query E → `awakening_map.py` → `patoshi_awakenings.csv`; all 1,145 mapped to spending tx + date,
  97% in 2009–2011, only 2 spends since 2015.

*(Done since the first draft: §7 hashrate/throttle, §8 dark-period gaps, §9 block-9 spend chain,
§10 nonce/thread structure, §11 coinbase-key distinctness (whole era, D1+D2), §12 spent-Patoshi
enumeration + full awakening map, §13 thread/core count bounded inference, §14 ECDSA-nonce safety
audit, §15 the machine-verifiable key-control standard.)*
