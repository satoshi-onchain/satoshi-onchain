# `btc-rpc-explorer-patoshi.json` — where this came from and why a copy is kept

## What it is

A verbatim snapshot of the mining-pool configuration file used by **btc-rpc-explorer**, a widely
deployed open-source Bitcoin block explorer. Its `block_heights.Patoshi.heights` array is the
Patoshi block list that explorer actually serves.

```
source   https://raw.githubusercontent.com/janoside/btc-rpc-explorer/master/
         public/txt/mining-pools-configs/BTC/0.json
fetched  12 August 2026
bytes    158,525
sha256   d5749c02cea4662ec96e6bd0478531a0f005714d9d6ca7415c2885eccce3711f
heights  21,950   range 3 .. 49,973
upstream MIT licensed. Copyright remains with its authors; this is an unmodified copy.
in-file  the list's own `ref` field cites
         github.com/jlopp/bitcoin-utils/blob/master/findPatoshiBlockTimestampDeltas.php
```

## ★ Why a snapshot exists at all, rather than fetching at run time

**Because the upstream list is not versioned, and it has already changed.**

```
21,953 heights   the version this project compared against on 11 Aug 2026
21,950 heights   the version deployed today
    -3           blocks 35573, 35599 and 24504, removed 8 Nov 2023 after outside challenge
```

**A comparison against "the Patoshi list" is meaningless without saying which one.** Upstream
carries no version number, no hash and no changelog entry a consumer can pin to, so **this file
supplies the pin**: the sha256 above is what every figure in the analysis was computed against.

> ⚠️ **If you re-fetch and the hash differs, the list has changed again.** That is not an error —
> it is the finding. Record the new hash, re-run, and report both.

## Reproducing

```
python verify/patoshi_setdiff.py            # uses this snapshot
python verify/patoshi_setdiff.py --fetch    # re-fetch upstream, re-hash, overwrite
python verify/adjudicated_blocks.py         # score the three retracted blocks
```

## What this file is NOT

**It is not evidence that any of these blocks were mined by Satoshi Nakamoto.** No 2009-era key has
ever signed anything, so every Patoshi set — theirs and ours alike — is a claim about extranonce
and nonce patterns, never about a person. **The analysis measures the gap between two such claims.
It does not adjudicate them.**
