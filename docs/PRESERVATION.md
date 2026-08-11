# Preservation — keeping the tracker retrievable, from more than one root

The durable artifact of this project is not a service; it is the **reproducible method** — the classifier,
the source-anchored axes, and the checks that let anyone re-derive the Satoshi/Patoshi on-chain footprint
from public block data without trusting us (`anchors.py` re-derives the genesis block from its own bytes;
`EXCAVATION.md` regenerates every figure from the public chain). A method is only as durable as its
availability, so preservation is part of the mission: keep the source of truth **retrievable,
content-addressed, and self-verifying**, so it survives a dead link, a lost account, or a host that
disappears. **Not money, not financial advice.**

Three independent roots, mirroring the [Original Bitcoin Laboratory](https://github.com/original-bitcoin-laboratory)'s
preservation, so no single one is load-bearing:

| Layer | What it preserves | Status |
|---|---|---|
| **Software Heritage** | full history of both satoshi-onchain repositories (`satoshi-onchain`, `.github`), in the universal source-code archive | **live** — [`.github/workflows/preserve.yml`](../.github/workflows/preserve.yml) requests archival daily and on every release, no credentials required |
| **Content-addressed pinning (IPFS)** | the signed release bundle + `SHA256SUMS`, addressable by content hash rather than by host | **live** — `IPFS_TOKEN` is set; the `ipfs` job pins each release's signed assets. v1.1.0: `satoshi-onchain-1.1.0.tar.gz` → `QmVC79JpvswSS7in7Wde6vpt2zkXgfDoAcDAfdQWsE2W4R`; v1.1.1: `satoshi-onchain-1.1.1.tar.gz` → `QmeipWrkm62ptVBWV3B8ZWyGAKmcV6DS9twtZ9c4zkCswC`; v1.2.0: `satoshi-onchain-1.2.0.tar.gz` → `QmVPbQw5HuJeRhuM61DrgoWttBbjijwEsEBTtZh7vAXNfp` (with `SHA256SUMS` → `QmWXhPWbgULBJJSTvpUss2vg17wyKBmWLNydsdciCGZYWW` and the two `.asc` detached signatures also pinned) (retrievable by CID from any gateway, cross-checkable against `SHA256SUMS`) |
| **Radicle** | a peer-to-peer git mirror, so the repository has no single hosting dependency | **live** — published as `rad:z4AkHVo5aTCwsbJFR8Q1AsJqszsjL` (owned by `parthod0x`, `did:key:z6MkqZAx…`); mirror head matches GitHub `main` |

Everything preserved is **hash-anchored**: the genesis re-derivation, the released source tarball, and the
evidence CSVs all carry digests a copy either matches or does not — so redundancy multiplies availability
without multiplying trust.

## The identity manifest — one signed answer for the whole periphery

Preservation spreads the work across hosts nobody here controls, which raises a question the mirrors
themselves cannot answer: **who says this Radicle repository, this organisation, this domain is
ours?** Until 12 August 2026 the answer was prose in this file — worth nothing to a reader with a
reason to doubt it.

[`IDENTITY-MANIFEST.txt`](IDENTITY-MANIFEST.txt) replaces that prose with one signature. It is
**GPG-signed, SLH-DSA counter-signed, and Bitcoin-anchored**, and it covers this project as well as
the Laboratory: the OpenPGP key, the post-quantum counter-signing key, the GitHub account and both
organisations, the three sites, and the Radicle identity including this repository's
`rad:z4AkHVo5aTCwsbJFR8Q1AsJqszsjL`.

```
IDENTITY-MANIFEST.txt          11,394 B   sha256 11b3f7db9497374d99e58873fc4d0c46740a292587c5cbc5cc9473d130816f94
IDENTITY-MANIFEST.txt.asc         273 B   OpenPGP, B128526AF85AE4A8F22B949FB0145F74B78CF1DA
IDENTITY-MANIFEST.txt.slhdsa    7,856 B   SLH-DSA-SHA2-128s, verified against the published pk
  + a .ots proof over each of the three
```

**This copy is byte-identical to the one on `bitcoin-lab.org`** — same sha256, same signatures — so
either host serves a copy that verifies, and neither is load-bearing. That is the whole point of
publishing it twice.

## Why this is faithful to what the tracker is

This adds nothing to the *classification* and attaches no value to anything — it only makes the existing,
already-verifiable method harder to lose and easier to reach. It extends the project's own standard (source
preserved as primary evidence; results independently regenerable from the public chain) from "published on
one host" to "retrievable from several independent, content-addressed archives." Still **not money**: no
token, no sale by us — a forensic instrument to which this project assigns no value, preserved.
*(What a third party might do is not ours to bind; the commitment is about our own conduct.)*

## Enabling the two scaffolded layers

### IPFS (content-addressed pinning) — automated once a token is set
1. Create an account at a pinning service and generate an **API JWT** (e.g. Pinata → *API Keys* → *New Key*
   with `pinFileToIPFS` permission → copy the JWT).
2. In the `satoshi-onchain` repo: **Settings → Secrets and variables → Actions → New repository secret**,
   name it `IPFS_TOKEN`, paste the JWT.

On the next published release the `ipfs` job downloads the signed `*.tar.gz`, `SHA256SUMS`, and `*.asc`,
pins each to IPFS, and logs the CIDs — retrievable from any gateway and cross-checkable against `SHA256SUMS`.

### Radicle (peer-to-peer git mirror) — a one-time local publish, then keep in sync
1. Install: `curl -sSfL https://radicle.xyz/install | sh` (adds `rad` under `~/.radicle/bin`).
2. Use the existing identity (`rad auth` with the `parthod0x` key) or create one; keys live in
   `~/.radicle/keys/`.
3. In a clone of this repo: `rad init --public --name satoshi-onchain` — publishes the repository to
   Radicle and prints its **Repository ID** (`rad:z…`). Start the node if prompted: `rad node start`.
4. Keep it in sync: after each GitHub push, run `git push rad` (the `rad` remote is added by `rad init`),
   or `rad sync --announce`.

**Published.** The satoshi-onchain repository is on Radicle as **`rad:z4AkHVo5aTCwsbJFR8Q1AsJqszsjL`**,
owned by the `parthod0x` identity (`did:key:z6MkqZAx6fnZ3iosXhTk7K3GzyzcNC2pxy5peUAuvYL45kUA`, the same
identity as the [genesis](https://github.com/original-bitcoin-laboratory/genesis) repo). Fetch the
decentralized mirror with:

```
rad clone rad:z4AkHVo5aTCwsbJFR8Q1AsJqszsjL
```

The mirror's `main` head tracks GitHub `main`; durable public availability depends on a seed replicating
the repository, so keep a node online or arrange a seed to hold the RID.

*(Optional CI:* add the exported key as `RAD_KEYPAIR` (and passphrase as `RAD_PASSPHRASE`) to let the
`radicle` job attempt an automated sync — but the local `git push rad` above is the reliable path.)*

Until the secrets/identity are set, the scaffolded jobs log "skipped — not configured"; Software Heritage
archival runs regardless.

**NOT money.**
