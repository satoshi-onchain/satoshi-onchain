# Release signing — a checklist for reproducible, GPG-signed releases

**For the maintainer.** Signed releases let anyone verify **who** published a snapshot and that it
**wasn't tampered with**. They do **not** — and cannot — prove any on-chain claim; the tracker's findings
stand on their own reproducibility. This is authenticity, not authority. **Not money, not financial advice.**

> This uses **your** GPG key — the same one used for the Original Bitcoin Laboratory releases. The public
> key is committed at [`parthod0x-signing-key.asc`](parthod0x-signing-key.asc); fingerprint
> `B128 526A F85A E4A8 F22B  949F B014 5F74 B78C F1DA` (key id `B0145F74B78CF1DA`). Safeguarding the private
> key is yours; only the public key is published.

## 1. Verify before you sign

A signature over broken results just authenticates broken results. From a clean checkout:

```bash
python anchors.py           # genesis + block-170 anchors re-derive from their own source bytes
python nonce_safety.py      # section 14 — Satoshi's block-9 key signed 5x with distinct nonces
python authorship_test.py   # section 15 — the machine-verifiable key-control standard
python spend_chain.py       # section 9  — the block-9 spend chain, from raw tx bytes
# the full excavation (sections 1-13) regenerates from public chain data — see README "Reproduce"
# + acquire.sql (BigQuery) / acquire_rpc.py (node); the derived CSVs are gitignored, not shipped.
```

Confirm the tree is clean (`git status`), the author is correct (`parthod0x`), and there are **no**
secrets, keys, or generated CSVs staged (`git ls-files | grep -Ei 'key|secret|\.env|early_blocks|spent_'`
returns nothing).

## 2. Tag, signed

```bash
git tag -s vX.Y.Z -m "satoshi-onchain vX.Y.Z — <one-line summary>"
git push origin vX.Y.Z
git verify-tag vX.Y.Z        # sanity check the signature
```

(`v1.0.0` was a lightweight, **unsigned** tag; `v1.1.0` onward are **annotated and GPG-signed** — check any
of them with `git verify-tag vX.Y.Z`.)

## 3. A reproducible source archive + detached signature

Ship the **source** (Python, no opaque binaries; the derived CSVs are regenerated, not shipped):

```bash
git archive --format=tar.gz --prefix=satoshi-onchain-X.Y.Z/ \
    -o satoshi-onchain-X.Y.Z.tar.gz vX.Y.Z
gpg --armor --detach-sign satoshi-onchain-X.Y.Z.tar.gz     # -> satoshi-onchain-X.Y.Z.tar.gz.asc
sha256sum satoshi-onchain-X.Y.Z.tar.gz > SHA256SUMS
gpg --armor --detach-sign SHA256SUMS                       # sign the checksum file too
```

`git archive` from a tag is deterministic, so anyone can regenerate the archive and check the hash.

## 4. Publish

- Attach `satoshi-onchain-X.Y.Z.tar.gz`, its `.asc`, and the signed `SHA256SUMS` to the GitHub release.
- Publish your **public key** + fingerprint out of band (release notes + a keyserver); the key is committed
  at [`parthod0x-signing-key.asc`](parthod0x-signing-key.asc).
- These are **full** releases (mark the newest `--latest`), unlike OBL's experimental pre-releases.
- If the site (`docs/index.html`) carries a version/footer, bump it to the new tag so the published page
  stays in sync with the newest release.
- Repeat the **NOT money / not financial advice** framing.

## 5. What anyone runs to verify

Put this in the release notes:

```bash
gpg --import parthod0x-signing-key.asc       # or: gpg --recv-keys B0145F74B78CF1DA
gpg --fingerprint B0145F74B78CF1DA           # must match B128 526A F85A E4A8 F22B  949F B014 5F74 B78C F1DA
git verify-tag vX.Y.Z
gpg --verify satoshi-onchain-X.Y.Z.tar.gz.asc satoshi-onchain-X.Y.Z.tar.gz
gpg --verify SHA256SUMS.asc SHA256SUMS && sha256sum -c SHA256SUMS
# then the content itself — the part that matters:
python anchors.py            # re-derive the genesis anchor from source
python nonce_safety.py ; python authorship_test.py ; python spend_chain.py
```

## The trust model, stated plainly

- A valid signature proves the snapshot came from **you** and is **unmodified**. That's all.
- The **durable** guarantee isn't the signature — it's the **reproducible method**: anyone can re-derive
  the anchors and regenerate the excavation from the public chain, with no key and no service to trust.
- Nothing here — not a signature, not a tag — makes any claim about who Satoshi is. **Not money.**
