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
| **Content-addressed pinning (IPFS)** | the signed release bundle + `SHA256SUMS`, addressable by content hash rather than by host | **live** — `IPFS_TOKEN` is set; the `ipfs` job pins each release's signed assets. v1.1.0: `satoshi-onchain-1.1.0.tar.gz` → `QmVC79JpvswSS7in7Wde6vpt2zkXgfDoAcDAfdQWsE2W4R`, `satoshi-onchain-1.1.0.tar.gz.asc` → `QmUwAhpz9qdw9K1mUPqpKBFDp5tAZktXvbrXqwRtzL9Eon`, `SHA256SUMS` → `QmPmPmQ6MwUFtqNhZWFW4gvqWNXy3ugkA7wmqJyLojBKM6`, `SHA256SUMS.asc` → `QmPPWc4ZqGHMzMj6fm2dFKyNVs4a31xHkaiBpnXtXhytDC`, `satoshi-onchain-1.1.0.tar.gz.ots` → `QmdoCnMg71fRw42Yz4cKyQ8qYtiFMNWiruxmjLRgkciQy1`, `satoshi-onchain-1.1.0.tar.gz.asc.ots` → `QmTdESfiSt85nhUxybXEH2QvPTWjmQ7ximmFd1B5MF1zgU`, `SHA256SUMS.ots` → `QmdMUdg5jPCb53oPwNK9YG89pL9WT7k6DRypCC2DECFgQR`, `SHA256SUMS.asc.ots` → `QmeT8ErzZntPQbYcXDpxqHbKJjAqb1pvmpqwf9PButS2aN`, `SHA256SUMS.slhdsa` → `QmfDunRhGMjiLXQ771nRqBLM7E5oHCai2F1D73nQNkBviZ`, `SHA256SUMS.slhdsa.ots` → `Qmbncc4ZSZBKXcv1xvbDoqC47YKWu57MMwM3Pg2pcfBTmZ` (the timestamp and post-quantum files pinned 12 Sep 2026); v1.1.1: `satoshi-onchain-1.1.1.tar.gz` → `QmeipWrkm62ptVBWV3B8ZWyGAKmcV6DS9twtZ9c4zkCswC`, `satoshi-onchain-1.1.1.tar.gz.asc` → `QmcpXAaixGgN1DGkhMVaCumpYrWhjyFXRdWARHBnt8wwSC`, `SHA256SUMS` → `QmUGXmUv1SD5G9MWMiHL9kGJceSotn82HCZhFc3EqvtyhA`, `SHA256SUMS.asc` → `Qmbi9Ub3ormcX8GhfADNKh2fHPjsm25cfSNNPjAQycUFkA`, `satoshi-onchain-1.1.1.tar.gz.ots` → `QmaYtnkJscx2WvSuCuegv35e1wywcRxcESMWinjW2gLBsu`, `satoshi-onchain-1.1.1.tar.gz.asc.ots` → `QmUvv4BiRKRkwSmcqwqgJCAKtj1bZmaUCABP3eNLApBTLu`, `SHA256SUMS.ots` → `QmbKEsQknKZLqR8XqnaM9ZEuhDXJKwAWu5oJSYQGM7cLPm`, `SHA256SUMS.asc.ots` → `QmXEE4tEvTGVC1bGFAdcEnkxkkfvybBs3oYq6YD8tKKwTd`, `SHA256SUMS.slhdsa` → `QmZj4vnwApL1Hegy2ji7XaL7zufxovNKdr4EQ49vb8qSiq`, `SHA256SUMS.slhdsa.ots` → `QmR1Vd7VhPuEKDiL4rd9aaMRp2nn1NJmA1ZUjaTVNai4tz` (pinned 12 Sep 2026); v1.2.0: `satoshi-onchain-1.2.0.tar.gz` → `QmVPbQw5HuJeRhuM61DrgoWttBbjijwEsEBTtZh7vAXNfp`, `satoshi-onchain-1.2.0.tar.gz.asc` → `QmNzVSZaswuvPeu6JC7rEU1ds8SuTnnVsvgwHhb7wyB1Ds`, `SHA256SUMS` → `QmWXhPWbgULBJJSTvpUss2vg17wyKBmWLNydsdciCGZYWW`, `SHA256SUMS.asc` → `QmTVxxSicWV45WabhB1jqGBu333tdGuUCXRvX73ZwDYiZm`, `satoshi-onchain-1.2.0.tar.gz.ots` → `QmcjZHRu7fHz6dHgQGmrFTHi1rfbkaC8dtiTQuBsi73VNf`, `satoshi-onchain-1.2.0.tar.gz.asc.ots` → `QmewcXtTBiieoKPDKehnGhQiAyJ8ddA19x5KThfNUQHCqm` (every CID in this cell re-derived from the release bytes on 12 Sep 2026 with a standard-library CIDv0 calculator validated against four independently recorded pins); **v1.3.0**: `satoshi-onchain-1.3.0.tar.gz` → `Qmeh6TQPcqPCtm7GcCQsoTqpa74H8uG4tguCJWBkGmVJ4K`, `SHA256SUMS` → `QmVm9ZxGpsor2st3xXwuyb5WpYhqtMseAKbAwyuzc773h7`, `SHA256SUMS.asc` → `QmdohKx5fRvWhcQLwza3GGjoBnfaC9YbLbvRZRwMWbsih2`, `satoshi-onchain-1.3.0.tar.gz.asc` → `QmbCoUKz1WiujbuQhcbgwWbbnDFaNVZLURnv6UeuK67A77`, `satoshi-onchain-1.3.0.tar.gz.ots` → `QmVtdBNhu8Zatj4xqNG2trNxa8LU1kNpa9DcZYKG6KuF5B`, `satoshi-onchain-1.3.0.tar.gz.asc.ots` → `QmSu2QnnVk7Hee2ZndmfgT1kht9eiR2C9e2eGArML2HJUs`, `SHA256SUMS.ots` → `QmbJswFriNDVvw2ismzr4NFzivyQ8eeJsvokR5t2j1J81k`, `SHA256SUMS.asc.ots` → `QmY3aJHHShvUdpzNV6RZvy97PVke3EcXdvx6LsQ98ujxsw` (the four `.ots` pinned 12 Sep 2026) (all three large-enough assets re-fetched from a gateway and byte-compared to the local copies, not merely listed) (retrievable by CID from any gateway, cross-checkable against `SHA256SUMS`) |
| **Radicle** | a peer-to-peer git mirror, so the repository has no single hosting dependency | **live and in sync** — `rad:z4AkHVo5aTCwsbJFR8Q1AsJqszsjL` (owned by `parthod0x`). Synced 12 September 2026; `seed.radicle.garden` and `ash.radicle.garden` served the current head when checked. The node runs on the operator's machine and is started for each sync; the section below records an earlier period when the public copy was stale, kept as history. |

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
IDENTITY-MANIFEST.txt          12,930 B   sha256 4825c4c0984209bf64c478d011a1933dd28d186ad1659101aa4098f77deb72b7
IDENTITY-MANIFEST.txt.asc         273 B   OpenPGP, B128526AF85AE4A8F22B949FB0145F74B78CF1DA
IDENTITY-MANIFEST.txt.slhdsa    7,856 B   SLH-DSA-SHA2-128s, verified against the published pk
  + a .ots proof over each of the three
```

> **Revision 2, 12 August 2026** — adds the agent's post-quantum successor key and its succession
> certificate. **Revision 1 (`11b3f7db…`, 11,394 B) is anchored in Bitcoin block 962049 and that
> anchor stands**; it proves revision 1 existed before that block and is not withdrawn.
**Proof of domain control.** Each of the three domains answers a TXT query at its apex with the same
record — only the domain's controller can set it:

```
$ dig +short TXT satoshioncha.in
parthod0x-pgp=B128526AF85AE4A8F22B949FB0145F74B78CF1DA; manifest=https://bitcoin-lab.org/IDENTITY-MANIFEST.txt https://satoshioncha.in/IDENTITY-MANIFEST.txt
```

> ★ **It pins the KEY FINGERPRINT, not a manifest hash.** The first version pinned
> `parthod0x-manifest=<sha256>` and went stale within a day when the manifest was revised. **A
> binding that breaks whenever the thing it binds is improved is the wrong binding.** The record
> proves domain control and publishes only a fingerprint, which is already public — never a key.
>
> ⚠️ **Check it against the authoritative nameservers, not a public resolver — a cached answer is not
> the zone.** One domain's change read as "not applied" on both `1.1.1.1` and `8.8.8.8` while
> `dns1`/`dns2.registrar-servers.com` already served it, with 1,755 s of TTL still to run.

**Revision 1 anchored 11 August 2026 in Bitcoin block 962049** — its three proofs upgraded from
pending to complete, each carrying `BitcoinBlockHeaderAttestation(962049)`:

```
block hash     00000000000000000000b1914635ada20cd0992856ebba4ba21b5ea4815eda1b
merkle root    cf62d5d80f9e0a2fecdba1c129eff6fb42ce259572649c163e42e8641ea90864
block time     2026-08-11 20:03:25 UTC
```

**Revision 2 (`4825c4c0…`, 12,930 B) anchored 12 August 2026 in Bitcoin block 962081** — the three
proofs published beside it each carry `BitcoinBlockHeaderAttestation(962081)`:

```
block hash     000000000000000000000d3c4cb24b2fd84a2f65eb39c14f5708285820e9e0a1
merkle root    cbf9d141073c02fc3d955dfa6c8e7e758b5ec7388eb529eb9c4f7ee86d8d9b48
block time     2026-08-12 03:29:39 UTC
```

**The merkle root was read off the chain and compared, not taken from the `ots` output** — which is
the point of an anchor: checkable against Bitcoin by anyone, trusting neither the calendars nor us.

**This copy is byte-identical to the one on `bitcoin-lab.org`** — same sha256, same signatures, same
anchored proofs — so either host serves a copy that verifies, and neither is load-bearing. That is
the whole point of publishing it twice.


## The post-quantum designations — one for each identity that publishes

Two keys can outlive a break of elliptic-curve signatures, and each is now designated **in writing,
in advance, with its limits stated**:

```
PQ-SUCCESSION-CERTIFICATE.txt      the 2026 agent's successor       10 Aug 2026
                                   signed by the chain key AND the successor AND (12 Aug) the
                                   OpenPGP key -- three signatures, two identities, one document
PQ-COUNTERSIGN-DESIGNATION.txt     parthod0x's counter-signing key   12 Aug 2026
                                   sha256 51c69df077f6150e04e97c9128dbe2919282879ceed107ebcfd464e8fa7c6246
                                   signed by the OpenPGP key AND by the designated key itself
```

**Both are OpenTimestamped, and that is the part that carries the weight.** A designation made
BEFORE a break proves it was made while the root key was still trustworthy; one made after is
indistinguishable from a forger's.

> ⚠️ **Each states what its key may NOT do, and those limits are part of the designation.** Neither
> proves the identity of any person, neither confers power over the chain, neither asserts any name
> or trade mark, and neither says anything about value.

## Why this is faithful to what the tracker is

This adds nothing to the *classification* and attaches no value to anything — it only makes the existing,
already-verifiable method harder to lose and easier to reach. It extends the project's own standard (source
preserved as primary evidence; results independently regenerable from the public chain) from "published on
one host" to "retrievable from several independent, content-addressed archives." Still **not money**: no
token, no sale by us — a measuring instrument to which this project assigns no value, preserved.
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

## ⚠️ Fixed at v1.3.0 — the post-quantum artifacts were not being pinned

Through v1.2.0 the `preserve` workflow downloaded `*.tar.gz`, `SHA256SUMS` and `*.asc`. It did
**not** download `*.slhdsa` or `*.ots`, so the **post-quantum counter-signature and its
OpenTimestamps proof had no content-addressed copy** — the two artifacts whose entire purpose is to
outlive a break of the Ed25519 key were the only release assets not preserved by content address.

The durable half was the half that was not being kept. Fixed in `preserve.yml` from v1.3.0; the
v1.3.0 `.slhdsa`/`.ots` will be pinned on the next run of the workflow and their CIDs recorded here.

## Radicle, measured rather than assumed — 22 August 2026 (historical; in sync since 12 September 2026)

Checked while cutting v1.3.0, and the row above overstates it. **The local Radicle store is
current; the seed network is not.**

```
local (you)         sigrefs ccbcb02   main e3cb690, tags through v1.3.0
17 known seeds      sigrefs 4371db8   5 days to 1 week old, EVERY ONE of them
push to rad         succeeded         "Synced with 0 seed(s)"
rad sync --announce failed            "All seeds timed out" -- twice, 180s, 12 peers connected
node                                  "not configured to listen for inbound connections"
```

★★ **Two traps worth writing down.**

**1. `rad sync` reports success while doing nothing.** Run before `git push rad`, it printed
*"Nothing to announce, already in sync with 17 seed(s)"* — while the mirror sat **nine commits
behind**. It announces what the node already has; it does not push the working repo. **`git push rad`
is the step that moves commits**, and a routine that says only "Radicle push" invites exactly this.
The same mirror was found behind once before (commit `730ef1f`).

**2. Announcing is not propagating.** A seed learns of an update by **fetching from you**, which
needs your node reachable. With no inbound listener the announcement goes out and no seed can act
on it — the mirror is real and local, and the network copy is a week stale.

⇒ **Stated honestly: Radicle is currently a local mirror with a stale public copy, not a live
redundant host.** Making it live needs the node reachable — inbound listening plus a forwarded port,
or a hosted seed that pulls. Until then, **treat GitHub + IPFS + Software Heritage as the real
redundancy** and do not lean on the "no single hosting dependency" claim.

## ⚠️ A pin that was listed but no longer retrievable — found and restored, 23 August 2026

The audit fetches every CID this file records instead of trusting the list. One did not come back:

```
satoshi-onchain-1.2.0.tar.gz   QmVPbQw5Hu…   HTTP 200, 1,152,699 B   fine
SHA256SUMS  (v1.2.0)           QmWXhPWbgU…   HTTP 404 from PINATA'S OWN GATEWAY
```

★ **The asymmetry is what made it a finding rather than a flaky gateway.** Two objects from the same
release, fetched the same way, one served and one 404 — and the 404 came from the gateway of the
service holding the pin, not from a public mirror under load. **A pin that is recorded is not a pin
that retrieves, and only fetching tells you which you have.**

Restored by dispatching `preserve.yml` against the v1.2.0 tag; it returned **the same CID this file
already recorded** (`QmWXhPWbgULBJJSTvpUss2vg17wyKBmWLNydsdciCGZYWW`), so the record was right and
only the object had gone. The retrieved bytes are identical to the offline copy of that manifest held in the project's cold
backup (path deliberately not named here — it is a secret store).

The same run pinned v1.2.0's post-quantum artifacts for the first time — they were never covered
before the workflow fix above:

```
SHA256SUMS.asc        QmTVxxSicWV45WabhB1jqGBu333tdGuUCXRvX73ZwDYiZm
SHA256SUMS.asc.ots    QmeUmkY5yFeo56Ge4tVJnXBDxiy9kDszKopFzbCL5EV3aK
SHA256SUMS.ots        QmVeG4HqtXBZKUsFcD2JNVMLShfwqys421zpyj923sWiGd
SHA256SUMS.slhdsa     QmYJhj9Kk2rGW2AKo8KgqaH5yhXRoFEmpJpZug3wjjsRUu
SHA256SUMS.slhdsa.ots QmWZMQrEqrRKBQMhT7wh8TFLPYMbeWuLbBP7sMBaBPKpYR
```

⇒ **Re-run the retrieval check periodically.** `python _audit_public.py ipfs` in the workspace
fetches every recorded CID; a listing that is not exercised will eventually be wrong without
anyone noticing.

## v1.3.0's timestamp is anchored — Bitcoin block 963620

Stamped 22 August 2026 and upgraded 23 August once a calendar folded it into a block:

```
SHA256SUMS.slhdsa.ots     600 B pending  ->  2,534 B, Bitcoin block 963620
```

The proof still carries pending markers for two of the three calendars it was submitted to. **That
is normal and is not a defect** — a proof branches per calendar, and one Bitcoin attestation is what
makes it verifiable. The release asset was replaced with the upgraded proof, so anyone downloading
now gets the anchored one rather than a promise, and the same bytes are in the cold backup.

**Post-quantum artifacts, pinned for v1.3.0 for the first time** (the workflow could not reach them
before the fix above):

```
SHA256SUMS.slhdsa      QmfXyGiJ2S8kQWd3fMpssQTFsjbNRBdvUimSr2PHh9MFfH
SHA256SUMS.slhdsa.ots  QmawXftYvbVbcpP4r3bjXAGLrJmGMw7RySfYxVa3ZGH3v4
```

⇒ **The counter-signature and its Bitcoin anchor are now content-addressed, signed and archived in
three independent places.** That is the state this file always claimed and, until today, did not
have.
