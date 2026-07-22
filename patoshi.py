#!/usr/bin/env python3
"""Patoshi classifier (faithful to Lerner 2013), operating on the early-block CSV.

It extracts, per block:
  - the ExtraNonce from the coinbase scriptSig (2009 Satoshi-client format: the coinbase
    is `push(nBits) push(nExtraNonce)`, so ExtraNonce is the 2nd data push);
  - `nonce_lsb_ok`: whether the header nonce's low byte is in 0-9 or 19-58 (Lerner's
    threading restriction). This is a *necessary condition* Patoshi blocks satisfy, not
    a sufficient one: by chance ~50/256 = 19.5% of non-Patoshi blocks also pass, so the
    definitive per-block separation is the ExtraNonce-track clustering that plots.py
    renders. We therefore report the LSB filter as a bound and point to the tracks.

  python patoshi.py early_blocks.csv        # -> patoshi_labeled.csv + summary to stdout

Tolerant CSV: accepts a minimal export (height/number, timestamp, nonce,
coinbase_script_hex OR coinbase_param). coinbase_value defaults to 50 BTC (correct for
blocks 0..~209,999); coinbase_spent defaults to '?' (dormancy not computed until you
run the spent anti-join and merge it in).

Grade: [forensic], never [cryptographic]. No key here has ever signed anything.
"""
import csv, sys
from collections import deque

SAT = 100_000_000
LSB_CHANCE = 50 / 256           # baseline pass-rate for the nonce-LSB filter (~0.195)
SUBSIDY_0 = 50 * SAT            # coinbase reward for blocks 0..209,999


def col(r, *names, default=None):
    for n in names:
        if n in r and r[n] not in (None, ""):
            return r[n]
    return default


def to_int(x):
    try:
        return int(x)
    except (ValueError, TypeError):
        return int(float(x))


def data_pushes(script: bytes):
    out, i, n = [], 0, len(script)
    while i < n:
        op = script[i]; i += 1
        if 1 <= op <= 0x4b:
            out.append(script[i:i + op]); i += op
        elif op == 0x4c and i < n:
            l = script[i]; i += 1; out.append(script[i:i + l]); i += l
        elif op == 0x4d and i + 1 < n:
            l = int.from_bytes(script[i:i + 2], "little"); i += 2; out.append(script[i:i + l]); i += l
        elif op == 0x4e and i + 3 < n:
            l = int.from_bytes(script[i:i + 4], "little"); i += 4; out.append(script[i:i + l]); i += l
        # else: a non-push opcode (single byte, already consumed) -> ignore
    return out


def script_int(b: bytes) -> int:
    if not b:
        return 0
    v = 0
    for i, byte in enumerate(b):
        v |= byte << (8 * i)
    if b[-1] & 0x80:                       # sign bit in the last byte
        v &= ~(0x80 << (8 * (len(b) - 1)))
        return -v
    return v


def extranonce(coinbase_script_hex: str):
    pushes = data_pushes(bytes.fromhex(coinbase_script_hex)) if coinbase_script_hex else []
    return script_int(pushes[1]) if len(pushes) >= 2 else None   # 2nd push (pre-BIP34)


def nonce_lsb_ok(nonce_int: int) -> bool:
    lsb = nonce_int & 0xFF
    return 0 <= lsb <= 9 or 19 <= lsb <= 58


def detect_nonce_hex(rows):
    """BigQuery `crypto_bitcoin` stores the header nonce as an 8-char HEX string
    (e.g. '709e3e28'); the node-RPC path exports it as a decimal integer. If any
    value carries a hex letter a-f, the whole column is hex (certain over thousands
    of early blocks). Ambiguous all-digit columns default to decimal (the RPC path)."""
    for r in rows:
        if any(c in "abcdefABCDEF" for c in str(col(r, "nonce") or "")):
            return True
    return False


def parse_nonce(raw, is_hex: bool) -> int:
    s = str(raw).strip()
    if s.lower().startswith("0x"):
        return int(s, 16)
    return int(s, 16) if is_hex else to_int(s)


def main():
    if len(sys.argv) != 2:
        sys.exit("usage: python patoshi.py early_blocks.csv")
    rows = list(csv.DictReader(open(sys.argv[1], newline="")))
    nonce_hex = detect_nonce_hex(rows)

    labeled = []
    for r in rows:
        h = to_int(col(r, "height", "number"))
        nonce = parse_nonce(col(r, "nonce"), nonce_hex)
        en = extranonce(col(r, "coinbase_script_hex", "coinbase_param", default=""))
        ok = nonce_lsb_ok(nonce) and h != 0      # genesis is hand-crafted, exclude
        labeled.append({"height": h, "extranonce": en, "nonce_lsb_ok": int(ok),
                        "coinbase_value": to_int(col(r, "coinbase_value", default=SUBSIDY_0)),
                        "coinbase_spent": col(r, "coinbase_spent", default="?")})

    labeled.sort(key=lambda x: x["height"])

    # Era end = the LAST height whose trailing 500-block LSB rate is still clearly above
    # chance. Using "last above" (not "first below") ignores momentary mid-era dips, so it
    # tracks the real collapse (~54,000, late 2010) rather than a transient.
    roll, era_end = deque(maxlen=500), None
    for x in labeled:
        roll.append(x["nonce_lsb_ok"])
        if x["height"] > 1000 and len(roll) == roll.maxlen and sum(roll) / len(roll) > LSB_CHANCE + 0.08:
            era_end = x["height"]
    with open("patoshi_labeled.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(labeled[0].keys()))
        w.writeheader(); w.writerows(labeled)

    # --- summary ---
    scanned = len(labeled)
    flt = [x for x in labeled if x["nonce_lsb_ok"]]
    btc = sum(x["coinbase_value"] for x in flt) / SAT
    have_spent = any(x["coinbase_spent"] in ("0", "1") for x in labeled)
    print(f"nonce column read as           : {'HEX (BigQuery)' if nonce_hex else 'DECIMAL (RPC)'}")
    print(f"blocks scanned                 : {scanned}  (0..{labeled[-1]['height']})")
    print(f"nonce-LSB filter passes        : {len(flt)}  ({len(flt)/scanned:.1%};  chance baseline {LSB_CHANCE:.1%})")
    print(f"  -> the excess over baseline is the Patoshi signal; the ExtraNonce tracks")
    print(f"     (plots.py) separate true Patoshi blocks from chance passers.")
    print(f"Patoshi-era end (LSB rate -> baseline): ~block {era_end}   [Lerner: ~54,000, late 2010]")
    print(f"coins under the LSB filter     : {btc:,.0f} BTC   (UPPER bound; includes chance passers)")
    if have_spent:
        unspent = sum(x["coinbase_value"] for x in flt if x["coinbase_spent"] == "0") / SAT
        print(f"  of which unspent             : {unspent:,.0f} BTC")
        print(f"  of which ever spent          : {btc - unspent:,.0f} BTC")
    else:
        print(f"  dormancy                     : NOT COMPUTED  (run the spent anti-join, then")
        print(f"                                 merge coinbase_spent by height and re-run)")
    print(f"Lerner clustered reference     : ~22,000 blocks, ~1,100,000 BTC, essentially all unspent")
    print(f"wrote patoshi_labeled.csv  ->  feed to plots.py for the ExtraNonce fingerprint")
    print("\nGrade: [forensic], not [cryptographic]. Attribution to Satoshi rests on the")
    print("fingerprint + the block-170/Finney anchor, never on a signature.")


if __name__ == "__main__":
    main()
