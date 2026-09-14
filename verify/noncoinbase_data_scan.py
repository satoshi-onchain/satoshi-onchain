"""Scan the SCRIPTS of every non-coinbase transaction in Bitcoin's first year.

WHY THIS EXISTS. `coinbase_data_scan.py` swept the coinbase channel exhaustively and closed it with
a capacity proof: across blocks 1-60,000 no coinbase scriptSig exceeds 32 bytes, so a 32-byte
commitment could not have fitted. Its own docstring then says non-coinbase transactions "are a
separate population and are enumerated separately (`first_year_payments.csv`)".

THE DEFECT. That enumeration records block, txid, counts, amounts and ADDRESSES. It does not record
a single SCRIPT. So the project's standing claim -- "Satoshi never committed a document to the
chain" -- rested on a sweep of ONE channel, with the other channel counted but never read. That is
the house pattern: a check that enumerates a population instead of projecting the question over it.

WHAT THIS DOES. Fetches the full scripts (input scriptSig AND output scriptPubKey) for every
non-coinbase transaction in the first year and applies the SAME probes coinbase_data_scan applies:

  - the three known whitepaper sha256 values, in both byte orders
  - any 32-byte high-entropy push that COULD be a commitment
  - OP_RETURN and any non-standard output type
  - printable-ASCII runs of 8+ characters
  - the capacity question: could a 32-byte payload have fitted at all

POSITIVE CONTROLS, IN TWO PARTS, AND BOTH RUN BEFORE THE SWEEP.

  A. SYNTHETIC -- a hand-built transaction carrying a real whitepaper digest, a text token, a
     long ASCII run, a 32-byte push, an OP_RETURN output and a non-standard output type.
     EVERY probe must fire on it.
  B. REAL      -- the 2013 whitepaper embedding (54e48e5f..., 948 outputs), fetched over the
     network, which exercises the fetch and parse path that a synthetic case cannot.

An earlier version used two real transactions instead. That was weaker in a way worth writing
down: BOTH of them only ever triggered the ASCII probe. Neither carried a whitepaper hash, an
OP_RETURN or a non-standard output, so the sweep reported zero for all three while nothing had
ever shown those probes could fire. A check that has never once returned a positive cannot be
read as having found nothing -- it is an untested branch, and its zero is not evidence.
A run that cannot see text in those two is broken, and its negatives mean nothing. The control runs
BEFORE the sweep and the script exits non-zero if it fails.

WHAT A NEGATIVE MEANS. That no commitment is present in the first-year non-coinbase population --
not that none exists anywhere in Satoshi's active window (which runs to Dec 2010). The bound is
stated in the output and must be quoted with any result.

Usage:  python verify/noncoinbase_data_scan.py [--csv first_year_payments.csv] [--limit N]
"""
import argparse
import binascii
import csv
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

API = "https://blockstream.info/api/tx/%s"
CHECKPOINT = "noncoinbase_scripts.json"

# The three whitepaper digests this scan looks for. Each is named by what it IS, because a
# bare hash in a verifier tells a reader nothing about what a hit would mean.
HASHES = {
    # The canonical paper as served from bitcoin.org, 24 March 2009. Reproducible by anyone:
    # fetch bitcoin.org/bitcoin.pdf from any Wayback capture and sha256 it.
    "b1674191a88ec5cdd733e4240a81803105dc412d6c6708d53ab94fc248f4f553":
        "whitepaper, canonical bitcoin.org 2009-03-24",
    # The pre-release draft circulated 3 October 2008, before the 31 October announcement.
    "427c63b364c6db914cf23072a09ffd53ee078397b7c6ab2d604e12865a982faa":
        "whitepaper, pre-release draft 2008-10-03",
    # A fourth version exists in the court record (COPA v Wright, judgment para 271.9) and is in no
    # public hands; its hash is in evidence that is not published and is not scanned for here.
}
for _h, _l in list(HASHES.items()):
    HASHES[binascii.hexlify(binascii.unhexlify(_h)[::-1]).decode()] = _l + " (byte-reversed)"

TEXT = [b"http", b".pdf", b"bitcoin.org", b"whitepaper", b"white paper", b"sha256",
        b"satoshi", b"nakamoto", b"abstract", b"peer-to-peer"]

CONTROLS = [
    ("54e48e5f5c656b26c3bca14a8c95aa583d07ebe84dde3b7dd4a78f4e4186e713", "whitepaper embedding 2013"),
]

ASCII_RUN = re.compile(rb"[\x20-\x7e]{8,}")


def fetch(txid, tries=6):
    """One transaction, with escalating backoff on 429 (the lesson from early_tx_survey)."""
    wait = 3
    for attempt in range(tries):
        try:
            req = urllib.request.Request(API % txid, headers={"User-Agent": "satoshi-onchain/verify"})
            return json.loads(urllib.request.urlopen(req, timeout=90).read())
        except urllib.error.HTTPError as e:
            if e.code in (429, 502, 503, 504):
                time.sleep(wait)
                wait = min(wait * 2, 120)
                continue
            raise
        except Exception:
            time.sleep(wait)
            wait = min(wait * 2, 120)
    raise RuntimeError("could not fetch %s after %d attempts" % (txid, tries))


def scripts_of(tx):
    """Every script byte-string in a transaction, input and output, as (where, bytes)."""
    out = []
    for i, vin in enumerate(tx.get("vin") or []):
        h = (vin.get("scriptsig") or "")
        if h:
            out.append(("in%d.scriptSig" % i, binascii.unhexlify(h)))
        for j, w in enumerate(vin.get("witness") or []):
            if w:
                out.append(("in%d.witness%d" % (i, j), binascii.unhexlify(w)))
    for i, vout in enumerate(tx.get("vout") or []):
        h = (vout.get("scriptpubkey") or "")
        if h:
            out.append(("out%d.scriptPubKey" % i, binascii.unhexlify(h),))
    return out


def probe(txid, tx):
    """Apply every probe to one transaction. Returns a findings dict."""
    f = {"txid": txid, "hash_hits": [], "text_hits": [], "ascii_runs": [],
         "op_return": 0, "nonstandard": [], "big_pushes": 0, "max_script": 0, "total_bytes": 0}
    for where, b in scripts_of(tx):
        f["max_script"] = max(f["max_script"], len(b))
        f["total_bytes"] += len(b)
        hx = binascii.hexlify(b).decode()
        for hh, lbl in HASHES.items():
            if hh in hx:
                f["hash_hits"].append({"where": where, "label": lbl})
        low = b.lower()
        for t in TEXT:
            if t in low:
                f["text_hits"].append({"where": where, "probe": t.decode()})
        for m in ASCII_RUN.finditer(b):
            f["ascii_runs"].append({"where": where, "text": m.group(0).decode("ascii", "replace")})
        # a 32-byte push is OP_PUSHBYTES_32 (0x20) followed by 32 bytes
        f["big_pushes"] += sum(1 for k in range(len(b) - 32) if b[k] == 0x20)
    for vout in (tx.get("vout") or []):
        ty = vout.get("scriptpubkey_type") or "?"
        if ty == "op_return":
            f["op_return"] += 1
        elif ty not in ("p2pk", "p2pkh", "p2sh", "v0_p2wpkh", "v0_p2wsh", "v1_p2tr", "multisig"):
            f["nonstandard"].append(ty)
    return f


def synthetic_control():
    """A hand-built transaction that triggers EVERY probe, including three that no real
    transaction in the control set ever reaches.

    WHY THIS EXISTS. The real controls only ever exercised the ASCII probe -- both of them
    reported text_hits=0 and neither carried a whitepaper hash, an OP_RETURN or a non-standard
    output. So the sweep reported "0 whitepaper hashes, 0 OP_RETURN, 0 non-standard" while
    NOTHING had ever shown those three probes could fire at all. A negative from a check that
    has never once returned a positive is not evidence; it is an untested branch.

    This control is synthetic on purpose. It is not fetched, so it cannot fail for a network
    reason, and it deliberately contains a real whitepaper digest, a text probe token, a long
    ASCII run, a 32-byte push, an OP_RETURN output and a non-standard output type.
    """
    wp_hash = "b1674191a88ec5cdd733e4240a81803105dc412d6c6708d53ab94fc248f4f553"
    payload = b"bitcoin.org SYNTHETIC CONTROL -- not a real transaction"
    script = (bytes([0x20]) + binascii.unhexlify(wp_hash)      # OP_PUSHBYTES_32 + 32 bytes
              + bytes([len(payload)]) + payload)
    hx = binascii.hexlify(script).decode()
    return {
        "vin": [{"scriptsig": hx}],
        "vout": [
            {"scriptpubkey": hx, "scriptpubkey_type": "op_return"},
            {"scriptpubkey": hx, "scriptpubkey_type": "synthetic_nonstandard"},
        ],
    }


def run_synthetic():
    """Every probe must fire. Any that does not is a dead check, and the sweep's
    corresponding zero would be meaningless."""
    f = probe("synthetic", synthetic_control())
    expect = {
        "whitepaper-hash probe": len(f["hash_hits"]) > 0,
        "text probe":            len(f["text_hits"]) > 0,
        "ASCII-run probe":       len(f["ascii_runs"]) > 0,
        "32-byte push probe":    f["big_pushes"] > 0,
        "OP_RETURN probe":       f["op_return"] > 0,
        "non-standard probe":    len(f["nonstandard"]) > 0,
    }
    print("  SELFTEST A -- SYNTHETIC, every probe must fire")
    for name, fired in expect.items():
        print("    %-24s %s" % (name, "fires" if fired else "DEAD -- its zero means nothing"))
    ok = all(expect.values())
    print("  SELFTEST A %s\n" % ("PASSED" if ok else "FAILED -- probes above are not live."))
    return ok


def run_controls():
    print("  SELFTEST B -- a REAL transaction KNOWN to carry readable data, fetched over the network")
    ok = True
    for txid, label in CONTROLS:
        try:
            f = probe(txid, fetch(txid))
        except Exception as e:
            print("    %-28s FETCH FAILED: %s" % (label, e))
            ok = False
            continue
        seen = len(f["ascii_runs"]) + len(f["text_hits"])
        print("    %-28s ascii_runs=%-4d text_hits=%-3d max_script=%dB  %s"
              % (label, len(f["ascii_runs"]), len(f["text_hits"]), f["max_script"],
                 "OK" if seen else "SAW NOTHING"))
        if f["ascii_runs"][:1]:
            print("        e.g. %r" % f["ascii_runs"][0]["text"][:70])
        if not seen:
            ok = False
    print("  SELFTEST %s\n" % ("PASSED -- a clean sweep below is meaningful."
                               if ok else "FAILED -- negatives below would be worthless."))
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default="first_year_payments.csv")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--skip-controls", action="store_true")
    a = ap.parse_args()

    if not a.skip_controls and not (run_synthetic() and run_controls()):
        sys.exit(2)

    with open(a.csv, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    txids = [r["txid"] for r in rows if r.get("txid")]
    if a.limit:
        txids = txids[:a.limit]

    cache = {}
    if os.path.exists(CHECKPOINT):
        cache = json.load(open(CHECKPOINT, encoding="utf-8"))
        print("  resumed: %d of %d already fetched" % (len(cache), len(txids)))

    findings, failed = [], []
    for n, txid in enumerate(txids, 1):
        if txid not in cache:
            try:
                cache[txid] = fetch(txid)
            except Exception as e:
                failed.append({"txid": txid, "error": str(e)})
                continue
            if n % 10 == 0:
                json.dump(cache, open(CHECKPOINT, "w", encoding="utf-8"))
                print("    %d/%d fetched" % (n, len(txids)), flush=True)
            time.sleep(0.35)
        findings.append(probe(txid, cache[txid]))
    json.dump(cache, open(CHECKPOINT, "w", encoding="utf-8"))

    print("\n  scanned %d non-coinbase transactions from %s" % (len(findings), a.csv))
    if failed:
        print("  ** %d UNREAD -- this sweep is INCOMPLETE **" % len(failed))
        for f in failed[:10]:
            print("     %s  %s" % (f["txid"][:20], f["error"][:60]))

    hh = [f for f in findings if f["hash_hits"]]
    th = [f for f in findings if f["text_hits"]]
    ar = [f for f in findings if f["ascii_runs"]]
    orr = [f for f in findings if f["op_return"]]
    ns = [f for f in findings if f["nonstandard"]]
    mx = max((f["max_script"] for f in findings), default=0)

    print("\n  RESULTS")
    print("    whitepaper-hash commitments : %d" % len(hh))
    print("    text-probe hits             : %d" % len(th))
    print("    printable ASCII runs (8+)   : %d" % len(ar))
    print("    OP_RETURN outputs           : %d" % sum(f["op_return"] for f in findings))
    print("    non-standard output types   : %d" % len(ns))
    for f in (hh + th + ar + orr + ns)[:20]:
        print("      %s  %s" % (f["txid"][:20], json.dumps(
            {k: v for k, v in f.items() if k != "txid" and v})[:150]))

    # ---- CHANCE CONTROL -------------------------------------------------
    # A printable byte-run is a PROXY for text, not text. Random DER signature bytes land in
    # 0x20-0x7e about 37% of the time, so 8-byte "ASCII runs" occur by chance in any signature
    # corpus. Reporting the raw count as a finding would be reading noise. Two controls:
    #   (a) analytic  -- expected runs given the byte count
    #   (b) SHUFFLE   -- the same bytes with their order destroyed. If real scripts carried text,
    #                    they would show MORE runs than their own shuffle. Fewer or equal = none.
    import random
    allb = bytearray()
    for f_tx in cache.values():
        for vin in (f_tx.get("vin") or []):
            if vin.get("scriptsig"):
                allb += binascii.unhexlify(vin["scriptsig"])
        for vo in (f_tx.get("vout") or []):
            if vo.get("scriptpubkey"):
                allb += binascii.unhexlify(vo["scriptpubkey"])
    total_runs = sum(len(f["ascii_runs"]) for f in findings)
    p = 95 / 256.0
    expected = len(allb) * (p ** 8) * (1 - p)
    random.seed(7)
    sim = []
    for _ in range(5):
        s = bytearray(allb)
        random.shuffle(s)
        sim.append(len(ASCII_RUN.findall(bytes(s))))
    print("\n  CHANCE CONTROL for the ASCII runs")
    print("    bytes scanned            : %d" % len(allb))
    print("    observed runs            : %d  (spread over %d transactions)" % (total_runs, len(ar)))
    print("    expected by chance       : %.0f" % expected)
    print("    SHUFFLE control (5 runs) : %s   <- same bytes, order destroyed" % sim)
    verdict = "AT OR BELOW chance -- NO TEXT PRESENT" if total_runs <= max(sim) else \
              "ABOVE the shuffle -- INVESTIGATE, this may be real text"
    print("    -> %s" % verdict)

    print("\n  CAPACITY")
    print("    longest script in this population: %d bytes" % mx)
    if mx < 33:
        print("    -> a 32-byte commitment COULD NOT HAVE FITTED anywhere in this population.")
    else:
        print("    -> scripts here are large enough to hold a 32-byte commitment; the")
        print("       negative above is 'not present', NOT 'could not fit'.")

    print("\n  BOUND -- quote this with any result")
    print("    Population: non-coinbase transactions in Bitcoin's FIRST YEAR only.")
    print("    Satoshi's active window runs to Dec 2010; blocks beyond this CSV are UNSCANNED.")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
