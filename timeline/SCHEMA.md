# The timeline — what goes in, and what a row means

Three views over one source of truth (`events.json`): **Satoshi**, **Bitcoin**, and **combined**.
The generator (`build.py`) renders them; nothing is written by hand into the HTML.

## The rule that makes this worth building

**Every row carries an evidence grade and a way to check it. A row with no source does not exist.**

And the harder half: **absence is rendered too.** An event we know occurred but cannot verify gets a
row marked `gap`. A timeline showing only what was found looks complete when it is not — the exact
failure that produced three separate bugs in this project on one day (`coinbase_value` being an
assumed constant, `patoshi_confirmed` being a truncated subset, and a survey printing "sweep
complete" over four multi-thousand-block holes). All three looked finished. **A timeline is the same
kind of artifact, and gets the same discipline.**

## Grades, strongest first

| grade | means | can it be faked? |
|---|---|---|
| `CHAIN` | written into the Bitcoin blockchain; reproducible from any full node or public mirror | no — would require redoing the proof-of-work |
| `SERVER-DB` | a timestamp written by a third-party server's own database (SourceForge account rows, SVN commit times, forum registration) | not by the subject; only by the operator |
| `ADJUDICATED` | tested in court — sworn evidence, expert report, or judicial finding | contested and survived |
| `PARTY-RELEASED` | published by a named counterparty from their own records | depends on that party |
| `ARCHIVE-POS` | position in an archive with independent bracketing (e.g. arrival order among other senders) | hard, but the archive operator could |
| `CAPTURE` | a third-party crawl with its own timestamp (Wayback and similar) | hard |
| `SELF` | Satoshi's own unsigned assertion — a `Date:` header, a profile field | trivially |
| `NONE` | asserted, no independent support | — |

**No grade above `ADJUDICATED` implies identity.** Nothing here is `[cryptographic]`, because **no
genesis-era or Patoshi key has ever produced a verifying signature.** That ceiling is a property of
the world, not of our research, and the timeline must not blur it.

## Fields

```jsonc
{
  "id":        "2009-01-03-genesis",       // stable, kebab-case, referenced by other rows
  "when":      "2009-01-03T18:15:05Z",     // ISO 8601; UTC where known
  "precision": "second",                   // second | minute | hour | day | month | range
  "until":     null,                       // set only when precision == "range"
  "axis":      "both",                     // satoshi | bitcoin | both
  "grade":     "CHAIN",
  "title":     "The genesis block",
  "claim":     "One sentence, factual, no adjectives that are not load-bearing.",
  "evidence":  [ {"what": "...", "where": "url or archives/ path", "hash": "sha256 or null"} ],
  "reproduce": "the exact command or query that regenerates this, or null",
  "gap":       false,                      // true = known to have happened, NOT verifiable by us
  "notes":     "caveats, competing readings, what this does NOT establish"
}
```

### `gap: true` rows

Used for events that demonstrably occurred but whose artifact we do not hold. They render
distinctly and are counted separately. Examples: the 11 November 2008 whitepaper (dated to the
second, three exhibit references, **no bytes**); the `bc014`/`bc015`/`bc015a` builds (URLs in
disclosed correspondence, payloads not located).

**A gap is not a guess.** It requires the same evidence that the event happened; only the artifact is
missing. Speculation does not get a row in any form.

## What is deliberately excluded

- Anything resting on "widely believed", forum consensus, or a chain of inference with no artifact
- Identity attributions of any kind
- Anything whose only support is a mail `Date:` header **presented as location** — those are `SELF`
  and appear as claims about a header, never about a person's whereabouts
