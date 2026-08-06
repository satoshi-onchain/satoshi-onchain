"""Render events.json into three interactive timelines: Satoshi, Bitcoin, combined.

Nothing is hand-written into the output. The HTML is a function of events.json, so the timeline can
be regenerated, diffed, and checked -- and a claim can only appear on it by first existing as a row
with a grade and a source.

VALIDATION IS A HARD GATE. A malformed row aborts the build rather than rendering. That is
deliberate: the whole point of this artifact is that it can be trusted at a glance, and a timeline
that silently drops a bad row is worse than one that refuses to build. This project has already been
bitten three times by artifacts that looked complete and were not.

Usage:  python build.py [--events events.json] [--out timeline.html]
"""
import argparse
import collections
import datetime
import html
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

GRADES = ["CHAIN", "SERVER-DB", "ADJUDICATED", "PARTY-RELEASED", "ARCHIVE-POS", "CAPTURE", "SELF", "NONE"]
AXES = ["satoshi", "bitcoin", "both"]
PRECISIONS = ["second", "minute", "hour", "day", "month", "range"]
REQUIRED = ["id", "when", "precision", "axis", "grade", "title", "claim", "evidence", "gap"]

ap = argparse.ArgumentParser()
ap.add_argument("--events", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "events.json"))
ap.add_argument("--corpus", default=None,
                help="root holding bitcoin-origin-claims/ and archives/; omit to infer")
ap.add_argument("--out", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "timeline.html"))
a = ap.parse_args()

events = json.load(open(a.events, encoding="utf-8"))
print(f"  {len(events)} events loaded from {os.path.basename(a.events)}")

# ---- validation: hard gate -------------------------------------------------------------------
errs, seen = [], set()
for i, e in enumerate(events):
    tag = e.get("id") or f"index {i}"
    for f in REQUIRED:
        if f not in e:
            errs.append(f"{tag}: missing required field {f!r}")
    if e.get("id") in seen:
        errs.append(f"{tag}: duplicate id")
    seen.add(e.get("id"))
    if e.get("grade") not in GRADES:
        errs.append(f"{tag}: grade {e.get('grade')!r} not one of {GRADES}")
    if e.get("axis") not in AXES:
        errs.append(f"{tag}: axis {e.get('axis')!r} not one of {AXES}")
    if e.get("precision") not in PRECISIONS:
        errs.append(f"{tag}: precision {e.get('precision')!r} not one of {PRECISIONS}")
    if not re.match(r"^\d{4}(-\d{2}(-\d{2}(T\d{2}:\d{2}:\d{2}Z)?)?)?$", str(e.get("when", ""))):
        errs.append(f"{tag}: 'when' {e.get('when')!r} is not ISO 8601")
    if e.get("precision") == "range" and not e.get("until"):
        errs.append(f"{tag}: precision 'range' requires 'until'")
    ev = e.get("evidence")
    if not isinstance(ev, list) or not ev:
        errs.append(f"{tag}: evidence must be a non-empty list -- a row with no source does not exist")
    else:
        for j, x in enumerate(ev):
            if not x.get("what") or not x.get("where"):
                errs.append(f"{tag}: evidence[{j}] needs both 'what' and 'where'")
if errs:
    print(f"\n  *** {len(errs)} VALIDATION ERROR(S) -- NOT BUILDING ***")
    for x in errs:
        print(f"      {x}")
    sys.exit(2)
print("  validation passed")

events.sort(key=lambda e: (str(e["when"]), e["id"]))
gaps = sum(1 for e in events if e["gap"])
by_grade = collections.Counter(e["grade"] for e in events)
by_axis = collections.Counter(e["axis"] for e in events)
print(f"  {len(events)-gaps} verified, {gaps} gap rows")
print(f"  grades: {dict(by_grade)}")
print(f"  axes:   {dict(by_axis)}")


def fmt(e):
    w = str(e["when"])
    if e["precision"] == "range":
        return f"{w} &rarr; {e.get('until')}"
    if e["precision"] in ("second", "minute", "hour"):
        return w.replace("T", " ").replace("Z", " UTC")
    return w


def esc(s):
    return html.escape(str(s), quote=True) if s is not None else ""


rows = []
for e in events:
    evid = "".join(
        f'<li><b>{esc(x["what"])}</b><br><span class="w">{esc(x["where"])}</span>'
        + (f'<br><code class="h">{esc(x["hash"])}</code>' if x.get("hash") else "")
        + "</li>"
        for x in e["evidence"])
    rep = (f'<div class="rep"><span class="lbl">reproduce</span><code>{esc(e["reproduce"])}</code></div>'
           if e.get("reproduce") else
           '<div class="rep none"><span class="lbl">reproduce</span><i>no mechanical reproduction — this row rests on a document</i></div>')
    notes = f'<div class="notes"><span class="lbl">caveats</span>{esc(e["notes"])}</div>' if e.get("notes") else ""
    rows.append(f'''<article class="ev{' gap' if e['gap'] else ''}" data-axis="{e['axis']}" data-grade="{e['grade']}" data-gap="{str(e['gap']).lower()}" id="{esc(e['id'])}">
  <header>
    <time>{fmt(e)}</time>
    <span class="g g-{e['grade']}">{e['grade']}</span>
    {'<span class="gapflag">NOT HELD</span>' if e['gap'] else ''}
    <h3>{esc(e['title'])}</h3>
  </header>
  <p class="claim">{esc(e['claim'])}</p>
  <details><summary>evidence &amp; reproduction</summary>
    <ul class="evid">{evid}</ul>{rep}{notes}
  </details>
</article>''')

# Measure the corpus this timeline is drawn from, so the page can state its own incompleteness
# with a real number rather than a vague hedge.
#
# IF THE CORPUS IS NOT REACHABLE, SAY SO -- DO NOT PRINT ZERO. An unmeasured count rendered as "0"
# is indistinguishable from a measured zero, and that is precisely the failure this project keeps
# hitting (a column of assumed constants; a truncated label; a survey reporting success over holes).
# This exact bug shipped once: built from inside the published repo, the corpus path did not resolve
# and the live page asserted "0 distinct dated events" as though it had counted them.
import glob
_root = a.corpus or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_entries = glob.glob(os.path.join(_root, "bitcoin-origin-claims", "*.md"))
_archives = [d for d in glob.glob(os.path.join(_root, "archives", "*"))
             if os.path.isdir(d) and os.path.exists(os.path.join(d, "SHA256SUMS"))]
CORPUS_MEASURED = bool(_entries)
if CORPUS_MEASURED:
    _dates = set()
    for _f in _entries:
        _dates |= set(re.findall(r"(?:200[7-9]|201[0-9])-\d{2}-\d{2}",
                                 open(_f, encoding="utf-8", errors="replace").read()))
    CORPUS_LINE = (f"The research corpus behind it contains <b>{len(_dates)}</b> distinct dated events "
                   f"across {len(_entries)} written entries and {len(_archives)} sealed archives, and "
                   f"migration into this file is deliberate rather than bulk — each row has to acquire a "
                   f"grade, a source and a reproduction path before it can appear. That corpus is a local "
                   f"research archive and is not itself published, so this number is stated, not linkable.")
    print(f"  corpus behind it: {len(_dates)} dated events, {len(_entries)} entries, {len(_archives)} sealed archives")
else:
    CORPUS_LINE = ("The research corpus behind it is not part of this repository, so its size is not "
                   "stated here rather than guessed at.")
    print("  NOTE: corpus not reachable from this path -- the page will say so instead of printing zero")

built = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
doc = f'''<title>Satoshi &amp; Bitcoin — a verifiable timeline</title>
<style>
:root{{--bg:#fff;--fg:#111;--mut:#666;--line:#e3e3e3;--card:#fafafa;--gap:#fff8e1;--gapline:#e0b400}}
@media(prefers-color-scheme:dark){{:root{{--bg:#0f1115;--fg:#e8e8ea;--mut:#9aa0aa;--line:#262a33;--card:#161922;--gap:#241f10;--gapline:#7a5c00}}}}
:root[data-theme=dark]{{--bg:#0f1115;--fg:#e8e8ea;--mut:#9aa0aa;--line:#262a33;--card:#161922;--gap:#241f10;--gapline:#7a5c00}}
:root[data-theme=light]{{--bg:#fff;--fg:#111;--mut:#666;--line:#e3e3e3;--card:#fafafa;--gap:#fff8e1;--gapline:#e0b400}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--bg);color:var(--fg);font:15px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}}
.wrap{{max-width:900px;margin:0 auto;padding:28px 18px 80px}}
h1{{font-size:24px;margin:0 0 6px}}
.sub{{color:var(--mut);margin:0 0 22px}}
.bar{{position:sticky;top:0;background:var(--bg);border-bottom:1px solid var(--line);padding:12px 0;margin-bottom:18px;z-index:5}}
.bar button{{font:inherit;font-size:13px;padding:5px 12px;margin-right:6px;border:1px solid var(--line);background:var(--card);color:var(--fg);border-radius:999px;cursor:pointer}}
.bar button[aria-pressed=true]{{background:var(--fg);color:var(--bg);border-color:var(--fg)}}
.bar .grp{{margin-top:8px}}
.bar label{{font-size:13px;color:var(--mut);margin-right:10px}}
.ev{{border:1px solid var(--line);background:var(--card);border-radius:10px;padding:14px 16px;margin:0 0 12px}}
.ev.gap{{background:var(--gap);border-color:var(--gapline)}}
.ev header{{display:flex;flex-wrap:wrap;gap:8px;align-items:center}}
.ev time{{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:12.5px;color:var(--mut)}}
.ev h3{{font-size:16px;margin:4px 0 0;flex-basis:100%}}
.g{{font-size:10.5px;letter-spacing:.06em;padding:2px 7px;border-radius:4px;border:1px solid var(--line);color:var(--mut)}}
.g-CHAIN{{background:#0a7f3f;color:#fff;border-color:#0a7f3f}}
.g-SERVER-DB{{background:#1256a0;color:#fff;border-color:#1256a0}}
.g-ADJUDICATED{{background:#5a3fa0;color:#fff;border-color:#5a3fa0}}
.g-PARTY-RELEASED,.g-ARCHIVE-POS,.g-CAPTURE{{background:transparent}}
.g-SELF,.g-NONE{{background:#8a1f1f;color:#fff;border-color:#8a1f1f}}
.gapflag{{font-size:10.5px;letter-spacing:.06em;padding:2px 7px;border-radius:4px;background:var(--gapline);color:#000}}
.claim{{margin:8px 0 6px}}
details summary{{cursor:pointer;color:var(--mut);font-size:13px}}
.evid{{margin:10px 0;padding-left:18px}}
.evid li{{margin-bottom:8px;font-size:13.5px}}
.w{{color:var(--mut);font-size:12.5px;word-break:break-all}}
code{{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:12px;word-break:break-all}}
.h{{color:var(--mut)}}
.rep,.notes{{margin-top:8px;font-size:13px}}
.rep.none i{{color:var(--mut)}}
.lbl{{display:inline-block;min-width:82px;color:var(--mut);font-size:11px;letter-spacing:.06em;text-transform:uppercase}}
.count{{color:var(--mut);font-size:13px;margin:6px 0 16px}}
.legend{{border:1px solid var(--line);border-radius:10px;padding:12px 16px;margin:22px 0;font-size:13.5px;color:var(--mut)}}
</style>
<div class="wrap">
<h1>Satoshi &amp; Bitcoin — a verifiable timeline</h1>
<p class="sub">Every row carries an evidence grade and, where one exists, a command that regenerates
it. Rows we <b>cannot</b> verify are shown too, marked <b>NOT HELD</b> — because a timeline showing
only what was found looks complete when it is not.</p>

<div class="incomplete"><b>This timeline is incomplete, and says so on purpose.</b>
It currently holds <b>{len(events)}</b> events. {CORPUS_LINE}
<b>Absence of a row here is not evidence that nothing happened on that date.</b>
Applying the same standard to ourselves that we apply to everyone else.</div>

<div class="bar">
  <div>
    <button data-view="both" aria-pressed="true">Combined</button>
    <button data-view="satoshi" aria-pressed="false">Satoshi</button>
    <button data-view="bitcoin" aria-pressed="false">Bitcoin</button>
  </div>
  <div class="grp">
    <label><input type="checkbox" id="gapsOnly"> gaps only</label>
    <label><input type="checkbox" id="chainOnly"> chain-grade only</label>
  </div>
</div>
<p class="count" id="count"></p>

{"".join(rows)}

<div class="legend">
<b>Grades, strongest first.</b>
<b>CHAIN</b> — written into the blockchain; forging it would mean redoing the proof-of-work.
<b>SERVER-DB</b> — a timestamp written by a third party's database, not by the subject.
<b>ADJUDICATED</b> — tested in court.
<b>PARTY-RELEASED</b> — published by a named counterparty from their own records.
<b>ARCHIVE-POS</b> — position in an archive, independently bracketed.
<b>CAPTURE</b> — a third-party crawl with its own clock.
<b>SELF</b> — Satoshi's own unsigned assertion; trivially fakeable.
<br><br><b>Nothing here is cryptographic.</b> No genesis-era or Patoshi key has ever produced a
verifying signature, so no row on this timeline identifies a person. That is a fact about the world,
not a gap in the research — and only a signature would change it.
<br><br>Generated {built} from <code>events.json</code>. The page is a function of that file.
</div>
</div>
<script>
var view="both", gapsOnly=false, chainOnly=false;
function apply(){{
  var n=0, all=document.querySelectorAll(".ev");
  all.forEach(function(el){{
    var ax=el.dataset.axis, ok=(view==="both")||(ax===view)||(ax==="both");
    if(gapsOnly && el.dataset.gap!=="true") ok=false;
    if(chainOnly && el.dataset.grade!=="CHAIN") ok=false;
    el.style.display=ok?"":"none"; if(ok)n++;
  }});
  var g=0; all.forEach(function(el){{if(el.style.display!=="none"&&el.dataset.gap==="true")g++;}});
  document.getElementById("count").textContent=n+" events shown — "+(n-g)+" verified, "+g+" not held";
}}
document.querySelectorAll(".bar button").forEach(function(b){{
  b.onclick=function(){{
    view=b.dataset.view;
    document.querySelectorAll(".bar button").forEach(function(x){{x.setAttribute("aria-pressed",String(x===b));}});
    apply();
  }};
}});
document.getElementById("gapsOnly").onchange=function(e){{gapsOnly=e.target.checked;apply();}};
document.getElementById("chainOnly").onchange=function(e){{chainOnly=e.target.checked;apply();}};
apply();
</script>
'''
open(a.out, "w", encoding="utf-8").write(doc)
print(f"  written -> {a.out}  ({len(doc):,} bytes)")
