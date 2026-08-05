# verify/ — reproduce the off-chain record yourself

Six scripts. Between them they rebuild every off-chain claim this project makes about Satoshi's
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
loop never terminates; and post bodies must be extracted with balanced `<div>` nesting, because
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

The Satoshi ↔ Martti Malmi correspondence, 2009–2011 — released by Malmi in February 2024 as a
witness in COPA v Wright. 260 messages, 144 of them Satoshi's. Saves the source HTML alongside the
parse so the parse can be audited against the bytes.

**This corpus contains its own control**, which is why it is worth more than a one-sided archive.
The obvious objection to any `Date` header is whether the timezone belongs to the sender or to their
mail provider. Here both sides are present:

```
satoshi   satoshin@gmx.com    +0000 x98    +0100 x46
sirius    mmalmi@cc.hut.fi    +0200 x74    +0300 x42
```

Malmi wrote from Helsinki University of Technology; Finland is EET/EEST — **+0200 winter, +0300
summer** — which is exactly what his headers say. So the offset is the **sender's machine**. And
checking every message against the EU daylight-saving boundary:

```
satoshi   n=144   consistent with EU DST: 144   inconsistent: 0
sirius    n=116   consistent with EU DST: 116   inconsistent: 0
```

Perfect on both sides across 22 months. Satoshi's `+0000/+0100` is **GMT/BST**, and notably *not*
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

## What none of this establishes

**No identity.** Every anchored fact above is about an artifact or an account. Read the anchor column
alone and the record runs 28 months without identifying a person. That is not a gap in the work — it
is the state of the record, and it is why this project treats identity as unresolved and artifacts as
the thing worth checking.

**No 2008 cryptographic timestamp** exists for any of it. The strongest classes available are
proof-of-work (the chain), live server database fields, and position in third-party archives — in
that order. They are not interchangeable and this project does not present them as though they were.
