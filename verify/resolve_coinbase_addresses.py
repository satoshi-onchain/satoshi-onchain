"""Resolve an early Bitcoin address to the block whose coinbase created it -- offline.

WHY THIS EXISTS. Bitcoin's first year paid almost every coinbase to a BARE PUBLIC KEY
(`41 <65-byte pubkey> ac`), not to an address. Block explorers display a P2PKH address for those
outputs as a convenience, but the address is never written on the chain -- it is DERIVED from the
key. So "which block minted the coins now sitting at address X" is a question you can answer from a
dump of coinbase scripts alone, with no node, no API and no network. This does that.

WHAT IT LETS US DO. When a correspondence names a payment -- an amount, a minute -- the chain gives
us the sending address but not who mined it. Resolving that address back to a block height puts it
next to the Patoshi labels, and the labels are an INDEPENDENT line of evidence: they come from the
nonce and ExtraNonce fields, which have nothing to do with keys or addresses. Agreement between a
letter and a nonce pattern is worth far more than either alone.

WHAT IT DOES NOT DO. It attributes nothing to a person. A height is not a name. `patoshi_confirmed`
is a statistical cluster label from Lerner's method, not a signature -- see the warnings in
`patoshi.py`. A hit here means "this address was minted by a block carrying the cluster's
fingerprint", never "Satoshi owned this".

RIPEMD-160 is implemented here in pure Python on purpose: OpenSSL 3 drops it from `hashlib` on many
builds, and this script must not need a C library to check a historical claim.

Usage:  python resolve_coinbase_addresses.py ADDR [ADDR ...]
        python resolve_coinbase_addresses.py --file addrs.txt
"""
import argparse
import csv
import hashlib
import os
import struct
import sys

sys.stdout.reconfigure(encoding="utf-8")

# --- RIPEMD-160, pure Python -------------------------------------------------------------------
_R = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15,
      7, 4, 13, 1, 10, 6, 15, 3, 12, 0, 9, 5, 2, 14, 11, 8,
      3, 10, 14, 4, 9, 15, 8, 1, 2, 7, 0, 6, 13, 11, 5, 12,
      1, 9, 11, 10, 0, 8, 12, 4, 13, 3, 7, 15, 14, 5, 6, 2,
      4, 0, 5, 9, 7, 12, 2, 10, 14, 1, 3, 8, 11, 6, 15, 13]
_RP = [5, 14, 7, 0, 9, 2, 11, 4, 13, 6, 15, 8, 1, 10, 3, 12,
       6, 11, 3, 7, 0, 13, 5, 10, 14, 15, 8, 12, 4, 9, 1, 2,
       15, 5, 1, 3, 7, 14, 6, 9, 11, 8, 12, 2, 10, 0, 4, 13,
       8, 6, 4, 1, 3, 11, 15, 0, 5, 12, 2, 13, 9, 7, 10, 14,
       12, 15, 10, 4, 1, 5, 8, 7, 6, 2, 13, 14, 0, 3, 9, 11]
_S = [11, 14, 15, 12, 5, 8, 7, 9, 11, 13, 14, 15, 6, 7, 9, 8,
      7, 6, 8, 13, 11, 9, 7, 15, 7, 12, 15, 9, 11, 7, 13, 12,
      11, 13, 6, 7, 14, 9, 13, 15, 14, 8, 13, 6, 5, 12, 7, 5,
      11, 12, 14, 15, 14, 15, 9, 8, 9, 14, 5, 6, 8, 6, 5, 12,
      9, 15, 5, 11, 6, 8, 13, 12, 5, 12, 13, 14, 11, 8, 5, 6]
_SP = [8, 9, 9, 11, 13, 15, 15, 5, 7, 7, 8, 11, 14, 14, 12, 6,
       9, 13, 15, 7, 12, 8, 9, 11, 7, 7, 12, 7, 6, 15, 13, 11,
       9, 7, 15, 11, 8, 6, 6, 14, 12, 13, 5, 14, 13, 13, 7, 5,
       15, 5, 8, 11, 14, 14, 6, 14, 6, 9, 12, 9, 12, 5, 15, 8,
       8, 5, 12, 9, 12, 5, 14, 6, 8, 13, 6, 5, 15, 13, 11, 11]
_K = [0x00000000, 0x5A827999, 0x6ED9EBA1, 0x8F1BBCDC, 0xA953FD4E]
_KP = [0x50A28BE6, 0x5C4DD124, 0x6D703EF3, 0x7A6D76E9, 0x00000000]


def _rol(x, n):
    return ((x << n) | (x >> (32 - n))) & 0xFFFFFFFF


def _f(j, x, y, z):
    if j < 16:
        return x ^ y ^ z
    if j < 32:
        return (x & y) | (~x & z)
    if j < 48:
        return (x | ~y) ^ z
    if j < 64:
        return (x & z) | (y & ~z)
    return x ^ (y | ~z)


def ripemd160(msg):
    h = [0x67452301, 0xEFCDAB89, 0x98BADCFE, 0x10325476, 0xC3D2E1F0]
    ln = len(msg)
    msg = msg + b"\x80"
    while len(msg) % 64 != 56:
        msg += b"\x00"
    msg += struct.pack("<Q", ln * 8)
    for off in range(0, len(msg), 64):
        X = struct.unpack("<16I", msg[off:off + 64])
        a, b, c, d, e = h
        ap, bp, cp, dp, ep = h
        for j in range(80):
            t = (_rol((a + _f(j, b, c, d) + X[_R[j]] + _K[j // 16]) & 0xFFFFFFFF, _S[j]) + e) & 0xFFFFFFFF
            a, e, d, c, b = e, d, _rol(c, 10), b, t
            t = (_rol((ap + _f(79 - j, bp, cp, dp) + X[_RP[j]] + _KP[j // 16]) & 0xFFFFFFFF, _SP[j]) + ep) & 0xFFFFFFFF
            ap, ep, dp, cp, bp = ep, dp, _rol(cp, 10), bp, t
        t = (h[1] + c + dp) & 0xFFFFFFFF
        h = [t, (h[2] + d + ep) & 0xFFFFFFFF, (h[3] + e + ap) & 0xFFFFFFFF,
             (h[4] + a + bp) & 0xFFFFFFFF, (h[0] + b + cp) & 0xFFFFFFFF]
    return b"".join(struct.pack("<I", x) for x in h)


# Self-test on the published RIPEMD-160 vectors. If this fails, every address below is wrong, so it
# is a hard abort rather than a warning.
assert ripemd160(b"").hex() == "9c1185a5c5e9fc54612808977ee8f548b2258d31"
assert ripemd160(b"abc").hex() == "8eb208f7e05d987a9b044a8e98c6b087f15a0bfc"
assert ripemd160(b"message digest").hex() == "5d0689ef49d2fae572b881b123a85ffa21595f36"

_B58 = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"


def b58check(payload):
    chk = hashlib.sha256(hashlib.sha256(payload).digest()).digest()[:4]
    n = int.from_bytes(payload + chk, "big")
    out = ""
    while n:
        n, r = divmod(n, 58)
        out = _B58[r] + out
    return "1" * (len(payload + chk) - len((payload + chk).lstrip(b"\x00"))) + out


def script_to_address(hex_script):
    """Bare-P2PK (41..ac) or P2PKH (76a914..88ac) -> base58 address. None if neither."""
    try:
        s = bytes.fromhex(hex_script.strip())
    except ValueError:
        return None
    if len(s) >= 67 and s[0] == 0x41 and s[-1] == 0xAC:          # bare pubkey
        h160 = ripemd160(hashlib.sha256(s[1:66]).digest())
    elif len(s) == 25 and s[:3] == b"\x76\xa9\x14" and s[-2:] == b"\x88\xac":  # P2PKH
        h160 = s[3:23]
    else:
        return None
    return b58check(b"\x00" + h160)


assert script_to_address(
    "410496b538e853519c726a2c91e61ec11600ae1390813a627c66fb8be7947be63c52da7589379515d4e0a604f8141781"
    "e62294721166bf621e73a82cbf2342c858eeac") == "12c6DSiU4Rq3P4ZxziKxzrL5LmMBrzjrJX", \
    "genesis coinbase must resolve to the known genesis address"

def build_address_index(cb_path, progress=None):
    """address -> minting height, for every coinbase in the dump. For use by other scripts here."""
    idx = {}
    for i, r in enumerate(csv.DictReader(open(cb_path, encoding="utf-8"))):
        ad = script_to_address(r["coinbase_output_script_hex"])
        if ad:
            idx[ad] = int(r["height"])
        if progress and i and i % 5000 == 0:
            progress(i)
    return idx


def load_patoshi(pat_path):
    """height -> label row. Empty dict if absent."""
    if not os.path.exists(pat_path):
        return {}
    return {int(r["height"]): r for r in csv.DictReader(open(pat_path, encoding="utf-8"))}


def is_patoshi(row):
    return bool(row) and str(row.get("patoshi_confirmed", "")).strip().lower() in ("1", "true")


def _cli():
    ap = argparse.ArgumentParser()
    ap.add_argument("addresses", nargs="*")
    ap.add_argument("--file")
    ap.add_argument("--cb", default=None, help="path to cb_outputs.csv")
    ap.add_argument("--patoshi", default=None, help="path to patoshi_confirmed.csv")
    a = ap.parse_args()

    want = list(a.addresses)
    if a.file:
        want += [l.strip() for l in open(a.file, encoding="utf-8") if l.strip() and not l.startswith("#")]
    if not want:
        sys.exit("give at least one address")

    here = os.path.dirname(os.path.abspath(__file__))
    cb_path = a.cb or os.path.join(here, "..", "cb_outputs.csv")
    pat_path = a.patoshi or os.path.join(here, "..", "patoshi_confirmed.csv")

    pat = {}
    if os.path.exists(pat_path):
        for r in csv.DictReader(open(pat_path, encoding="utf-8")):
            pat[int(r["height"])] = r
        print(f"  patoshi labels loaded: {len(pat):,} heights")
    else:
        print("  NOTE: patoshi_confirmed.csv absent -- heights will resolve but carry no cluster label")

    print(f"  scanning {os.path.basename(cb_path)} for {len(want)} address(es)\n")
    want_set = set(want)
    found = {}
    n = 0
    for r in csv.DictReader(open(cb_path, encoding="utf-8")):
        n += 1
        ad = script_to_address(r["coinbase_output_script_hex"])
        if ad in want_set:
            found[ad] = int(r["height"])
            if len(found) == len(want_set):
                break
    print(f"  {n:,} coinbase scripts read\n")

    for ad in want:
        h = found.get(ad)
        if h is None:
            print(f"  {ad}")
            print(f"      NOT a coinbase address in the scanned range -- it was funded by a PAYMENT,")
            print(f"      not by mining (or lies beyond the dump's last height).\n")
            continue
        p = pat.get(h)
        if p:
            flag = "PATOSHI-CONFIRMED" if p.get("patoshi_confirmed", "").strip().lower() in ("1", "true") else "not in the Patoshi cluster"
            print(f"  {ad}")
            print(f"      minted by block {h:,}   [{flag}]")
            print(f"      extranonce={p.get('extranonce')}  nonce_lsb_ok={p.get('nonce_lsb_ok')}  phi={p.get('phi')}\n")
        else:
            print(f"  {ad}\n      minted by block {h:,}   [no label for this height]\n")



if __name__ == "__main__":
    _cli()
