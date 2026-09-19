# verify/ — reproduce the off-chain record yourself

Scripts and queries, each stating what it establishes and what it does not. Between them they rebuild every off-chain claim this project makes about Satoshi's
footprint, from public sources, with no API key, no login, and no trust in us.

Python 3.9+, standard library only. Each is polite: identified User-Agent, sequential requests,
delays between them, and it skips anything already fetched.

```bash
python verify/sourceforge_identity.py                    # account dates + sequential user IDs
python verify/sourceforge_svn_log.py     svn-log.json    # 252 server-timestamped commits
python verify/sourceforge_svn_files.py   ./svn-archive   # the file bodies for each revision
python verify/bitcointalk_satoshi.py     ./bitcointalk   # 539 posts + raw HTML
python verify/metzdowd_backup.py         ./metzdowd      # 274 mboxes, full headers
python verify/wayback_backup.py          ./wayback-pages # original bytes of the cited captures
python verify/github_history_census.py   --out census.json   # bitcoin/bitcoin 2009-2010: 385 commits, 122 carried twice
```

---

## What each one establishes

### `sourceforge_identity.py`

Fetches the archived SourceForge user pages for `nakamoto2` and `s_nakamoto` and reads two fields
that have to agree with each other:

```
  1173666   2004-12-07   nanotube
  1546005   2006-06-26   dooglus
  2238460   2008-10-05   nakamoto2      <- registered the Bitcoin project
  2321442   2008-12-10   s_nakamoto
```

`Joined` is server-set and not user-editable; user IDs are assigned **sequentially at account
creation**. A backdated join date would therefore need an out-of-sequence ID. The script checks
monotonicity and exits non-zero if it fails.

**Establishes:** the account that registered the Bitcoin project on SourceForge was created
**5 October 2008** — 26 days before the whitepaper was announced.
**Does not establish:** who created it.

*Note the page layout changed: captures before ~mid-2009 label the field "Site Member Since", later
ones say "Joined". The script handles both.*

### `github_history_census.py`

Counts the `bitcoin/bitcoin` commits from its first commit (30 Aug 2009) to the end of 2010 from
GitHub's public API, four unauthenticated calls, and measures the SVN conversion's doubling: pairs of
one `git-svn-id` copy and one copy without, their date offsets, and the author strings on each copy.
`--stats` (needs `GITHUB_TOKEN`) compares each pair's additions, deletions and file list.

```
385 commits · 42 merges · 341 non-merge · 202 with git-svn-id
122 pairs: non-trailer copy 0.00 d (median) to 8.09 d (max) later, not earlier in any pair
112 of 120 compared pairs identical · 8 differ by a few lines · 8 commits with the literal author "--author=Satoshi Nakamoto"
```

**Establishes:** that the canonical repository is two records of one history for this period, and
that a date read from the non-trailer copy can be up to eight days late. **Does not establish:** how
the second lineage arose, or anything about identity (author fields are self-asserted). The
SourceForge SVN log (`sourceforge_svn_log.py`) is the server-timestamped record; this census is about
the GitHub copy that most people read instead.

### `sourceforge_svn_log.py`

Pulls the complete revision log of `svn.code.sf.net/p/bitcoin/code` from Software Heritage, which
holds a full crawl. SourceForge itself no longer serves this history.

```
252 revisions, 2009-08-30 .. 2011-09-13
  s_nakamoto     164   2009-10-21T01:08:05Z .. 2010-12-15T22:43:51Z
  gavinandresen   66
  sirius-m        21   "First commit"
  laszloh          1
```

SVN commit timestamps are written by the server at commit time.

**Establishes:** 164 server-recorded timestamps of Satoshi's working activity — the densest such
record outside the block chain — and that the **last one is 2010-12-15 22:43:51Z**, two days after
the final bitcointalk activity.
**Does not establish:** anything about who was at the keyboard, or where. The script prints the
hour-of-day distribution because it is data; drawing a timezone from it is an inference the data does
not carry.

### `sourceforge_svn_files.py`

Walks each revision's tree and fetches the file bodies (content-addressed, so shared blobs are
fetched once). Gives the full 2009–2011 source history that SourceForge no longer serves.
Requires `svn-log.json` from the previous script.

For a complete copy in one request, ask Software Heritage's vault to cook the whole history instead:

```bash
curl -X POST https://archive.softwareheritage.org/api/1/vault/git-bare/swh:1:rev:5c085256f7dbfe999afbf10808828f0df9f877f1/
# poll the same URL until "status":"done", then GET .../raw/
```

Use the vault for the full history; use the walk above when you only want specific revisions.

### `bitcointalk_satoshi.py`

Collects every publicly listed post by user 3, saving the raw HTML alongside the parse so the parse
can be audited against the bytes.

```
539 unique posts, msg 28 .. 29479
first  2009-11-22 18:04:28  "Welcome to the new Bitcoin forum!"
last   2010-12-12 18:22:33  "Added some DoS limits, removed safe mode (0.3.19)"
```

**The profile counter says 575; the public list enumerates 539.** The script reports that gap rather
than hiding it. The 36 difference is real and reproducible — pagination genuinely ends at
`start=520` — and posts can be counted while not being listed (deleted, moved, or in a board guests
cannot read).

*Two parsing traps it handles: SMF re-serves the last page for any `start` beyond the end, so a naive
loop does not terminate; and post bodies must be extracted with balanced `<div>` nesting, because
quote blocks live inside the post div and a non-greedy match truncates such posts to the word
"Quote".*

### `metzdowd_backup.py`

Full preservation copy of the `cryptography@metzdowd.com` pipermail archive — 274 monthly mboxes,
39,742 messages. The gzipped mboxes carry headers the rendered HTML strips: `Message-ID`, the
sender's `Date` with timezone, and the `From_` line.

**Establishes:** an offline copy of the archive that carries Satoshi's 18 messages, so no claim about
them depends on one server staying online.
**Read this before drawing conclusions from the timestamps:** pipermail writes its `From_` line from
the message's own `Date` header. Across all 345 messages in the Oct 2008 – Jan 2009 window the delay
between the two is *exactly zero for every sender*, which is only possible if one is derived from the
other. **The archive is not a timestamping service.** What it records independently is arrival
**order** — the file is not date-sorted, and message numbers are assigned as messages are processed —
so each message sits in a bracket of independently-dated messages from other people.

*pipermail obfuscates addresses as `user at host`. A `From_` regex requiring `@` matches nothing.*

### `malmi_satoshi_emails.py`

The Satoshi ↔ Martti Malmi correspondence, 2009–2011 — self-published by Malmi in February 2024 at
<https://mmalmi.github.io/satoshi/>. 260 messages, 144 of them Satoshi's. Saves the source HTML alongside the
parse so the parse can be audited against the bytes.

**This corpus contains its own control**, which is why it is worth more than a one-sided archive.
The obvious objection to any `Date` header is whether the timezone belongs to the sender or to their
mail provider. Here both sides are present:

```
satoshi   satoshin@gmx.com    +0000 x98    +0100 x46
sirius    mmalmi@… (redacted)    +0200 x74    +0300 x42
```

Malmi's own messages place him in Finland, which is EET/EEST — **+0200 winter, +0300
summer** — which is exactly what his headers say. So the offset is the **sender's machine**. And
checking every message against the EU daylight-saving boundary:

```
satoshi   n=144   consistent with EU DST: 144   inconsistent: 0
sirius    n=116   consistent with EU DST: 116   inconsistent: 0
```

Perfect on both sides across 22 months. Satoshi's `+0000/+0100` follows the **UTC/UTC+1 summer-time pattern** (a machine setting, not a location), and notably *not*
GMX's German `+0100/+0200`.

**What that does not establish.** A timezone is a machine setting, and a setting is not a location.
Read it alongside the other time signals rather than instead of them — the PDF creation offsets and
the SVN commit-hour distribution point elsewhere, and this project publishes the disagreement rather
than resolving it. See [the off-chain record](https://satoshioncha.in/#offchain).

### `wayback_backup.py`

Pulls the **original bytes** (the `if_` suffix, which omits the Archive's toolbar wrapper) of every
capture of the pages this project cites, hashes them, and writes a manifest.

Run it with no arguments for the default target list, or pass targets explicitly. Passing a subset
merges into any existing manifest rather than replacing it.

---

### `fees_2009.sql`

**Not a script — a query**, because the public explorer APIs rate-limit a 32,000-block sweep into
failure (our own `early_tx_survey.py` died mid-sweep for exactly that reason). This runs against
Google's public mirror of the chain, `bigquery-public-data.crypto_bitcoin`, and answers in seconds.

**Establishes:** exactly **eight** blocks in the whole of 2009 collected a transaction fee; the total
paid across the year is **2.87 BTC**; every other block paid exactly 50.00. The earliest is **block
2817, 3 February 2009, fee 2.01 BTC** — larger than the other seven combined.

**Does not establish:** who mined any of them, or why any fee was set. A coinbase value is not an
identity.

**Check it without BigQuery:** there are only eight rows. Look each height up in any block explorer
and read the coinbase output. The result is deliberately small enough to verify by hand.

**Carries a warning about this repo's own data.** `early_blocks.csv` has a `coinbase_value` column in
which every one of its 60,001 rows holds the identical `5000000000` — assumed at acquisition, not
read from the chain. Searching it for fee-bearing blocks returns **zero**, and the conclusion that
invites is false. Heights and timestamps in that file are sound; **`coinbase_value` is inert and must
not be used.**

### `first_year_payments.sql`

**Establishes:** Bitcoin's entire first year contains **219 non-coinbase transactions** — every
payment anyone made, listable exhaustively. That is what makes early claims checkable: an account
saying *"N coins moved on date D"* can be held against the handful of transactions that existed that
week. Often none fits.

**Ordering caveat:** `outputs_btc` is index-ordered; `out_addresses`/`in_addresses` are **not**, so do
not pair them positionally — identify by elimination (an address on the inputs is taking change).
Published as-run rather than silently fixed, because the circulating CSV came from this exact text.

**Does not establish:** anything about *who*. Addresses are not names.

### `resolve_coinbase_addresses.py`

Bitcoin's first year paid almost every coinbase to a **bare public key**, not an address — explorers
*derive* the address for display; it is not written on the chain. This inverts that derivation
offline, so you can ask **"which block minted the coins now at address X"** with no node, no API and
no network, then place the answer next to the Patoshi labels.

**Why that pairing matters:** the Patoshi labels come from the **nonce and ExtraNonce** fields, which
have nothing to do with keys or addresses. When a document and a nonce pattern agree, that is two
independent lines; when they disagree, that is worth more than either alone. **We have used it for
both** — including one case where it declined to corroborate a tempting identification.

**Does not establish:** any person. A height is not a name, and `patoshi_confirmed` is a statistical
cluster label, not a signature.

RIPEMD-160 is implemented in pure Python because OpenSSL 3 drops it from `hashlib` on many builds,
and checking a historical claim should not require a C library. It **self-tests against the published
RIPEMD-160 vectors and against the genesis coinbase** on every run, and aborts if either fails.

### `first_year_patoshi_map.py`

Joins the two early-chain datasets that are rarely joined: the **per-block Patoshi labels**
(from nonce/ExtraNonce — nothing to do with keys) and the **complete 219-payment first-year record**.
The usual Patoshi claim is about *balances*; this measures the same thing as **flow**.

**Establishes:** coins from flagged blocks were spent at **0.26×** the rate the cluster mined them —
19.7% of spent coins against a 76.9% base rate, a **~3.9× depletion**. Blind spending would put ~1,367
of 1,779 spent coins in the flagged set; **351** are. Survives deleting the five largest consolidation
transactions (19.6%, unchanged), so it is not a few miners sweeping their own wallets.

**Read the docstring before trusting any number you compute from it.** `patoshi_confirmed` is **not**
"is this a Patoshi block" — it is a high-confidence subset whose `phi` threshold means it can only be
set up to about block **24,184**, though the era runs to ~54,458. Compare against the whole chain and
every later block is "not Patoshi" *by construction*. **Our first run made exactly that mistake and
reported a stronger result than the data supports.** The script now restricts to the label's valid
range and computes the base rate over that same range.

**Direction of remaining error:** false positives make the cluster look like it spent *more* than it
did, so they bias the result **towards** the null. The true depletion is if anything stronger.

**Does not establish:** any person. A cluster label is a statistical fingerprint, not a signature.

## Also in this directory

Each of these is self-describing at the top of the file; the one-line summaries are its own docstring.

| script | what it does |
|---|---|
| `adjudicated_blocks.py` | The only externally adjudicated blocks in the Patoshi problem, scored by our classifier. |
| `audit_published_hashes.py` | Stress test: every SHA-256 published in our documents, checked against the real artifact. |
| `coinbase_data_scan.py` | Scans every early coinbase — scriptSig and output script — for a whitepaper commitment. |
| `noncoinbase_data_scan.py` | Scans the scripts of every non-coinbase transaction in Bitcoin's first year for the same. |
| `patoshi_list_history.py` | The complete version history of a deployed Patoshi block list, reconstructed from git. |
| `patoshi_setdiff.py` | The pairwise Patoshi set difference between published classifiers. |
| `patoshi_spend_axis.py` | Two Patoshi classifiers disagree almost entirely along one axis: whether the coinbase was spent. |
| `sourceforge_download_stats.py` | SourceForge's own download statistics for the Bitcoin project, back to 2008. |
| `verify_signed_message.py` | Verifies a Bitcoin signed message from first principles, with no dependencies. |
| `wayback_orig_headers.py` | Recovers the original server's response headers from an Internet Archive capture. |

## What none of this establishes

**No identity.** Every anchored fact above is about an artifact or an account. Read the anchor column
alone and the record runs 28 months without identifying a person. That is not a gap in the work — it
is the state of the record, and it is why this project treats identity as unresolved and artifacts as
the thing worth checking.

**No 2008 cryptographic timestamp** exists for any of it. The strongest classes available are
proof-of-work (the chain), live server database fields, and position in third-party archives — in
that order. They are not interchangeable and this project does not present them as though they were.

---

*[statistical], not [cryptographic] — no verifying signature exists and none is claimed. Experimental research, in progress, no conclusions beyond the findings. Not money. Not financial advice. No warranty. [Rights, sourcing and corrections](../RIGHTS.md).*
