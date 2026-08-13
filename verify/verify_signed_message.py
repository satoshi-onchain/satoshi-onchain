"""Verify a Bitcoin signed message from first principles, with no dependencies.

WHY THIS EXISTS
---------------
Claims that someone controls an early Bitcoin key appear regularly, and they are almost always
presented as a SCREENSHOT of a verifier website showing a green tick.

  ⇒ A SCREENSHOT OF A VERIFIER IS NOT A VERIFICATION. It is a picture.

A real signed message is two short strings of TEXT — an address and a signature — and anyone can
check them in seconds, on their own machine, with no website and nobody's permission. This file is
that check, written out so the mathematics is visible rather than delegated.

THE POINT MOST OFTEN MISSED
-----------------------------
    The question is NEVER "does this signature recover to a public key".
    The question is ALWAYS "does it recover to *THE* address".

ECDSA public-key recovery almost always succeeds. Feed it a well-formed signature and an arbitrary
message and it will hand you *some* address, every time. **That is why a green tick, on its own,
carries no information: the hard part is not recovery, it is recovering to the address you were
asked about.**

TWO THINGS THIS FILE CHECKS BEFORE THE MESSAGE IS EVEN CONSIDERED
------------------------------------------------------------------
Both are properties of the signature bytes alone, so no transcription of the message can change
them, and either one failing means the string is not a signature at all:

    1. the header byte must be 27..34   — it encodes the recovery id and the compression flag
    2. `r` must be a point on secp256k1 — in a real signature r IS the x-coordinate of R = kG,
                                          so it is on the curve BY CONSTRUCTION

⚠️ AND A NOTE ON WHY A FAILURE IS NOT ALWAYS A FORGERY. A signed message commits to the EXACT BYTES
   of its text. A changed quote mark, an accent, a trailing newline — any of these produces a
   verification failure on a perfectly genuine signature. **Report a failure as "does not verify
   under the transcriptions tried", never as "forged"** — unless it fails one of the two structural
   checks above, which the message cannot affect.

  ★ A PASS, by contrast, needs no such hedging. That asymmetry is why the test is worth running.

WHAT VERIFICATION CAN AND CANNOT SHOW
---------------------------------------
  ✅ that whoever produced the signature held the private key at some point
  ⛔ NOT who that person is. Authorship and identity are not cryptographic properties.
  ⛔ NOT that they hold it now — a signature can be made once and shown forever.

Run:  python verify/verify_signed_message.py                       # self-test only
      python verify/verify_signed_message.py <address> <sig> <message-file>
"""
import base64
import hashlib
import sys

# secp256k1
P = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
GX = 0x79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798
GY = 0x483ADA7726A3C4655DA4FBFC0E1108A8FD17B448A68554199C47D08FFB10D4B8

# The genesis block's coinbase output is P2PK: the public key is written into block 0 in
# plaintext and has been readable by anyone since 3 January 2009. It is used here purely as a
# SELF-TEST — a known key/address pair to prove the arithmetic in this file is correct.
GENESIS_PUBKEY = ("04678afdb0fe5548271967f1a67130b7105cd6a828e03909a67962e0ea1f61deb6"
                  "49f6bc3f4cef38c4f35504e51ec112de5c384df7ba0b8d578a4c702b6bf11d5f")
GENESIS_ADDR = "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"

B58 = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"


def inv(a, m):
    return pow(a, m - 2, m)


def add(p, q):
    if p is None:
        return q
    if q is None:
        return p
    if p[0] == q[0] and (p[1] + q[1]) % P == 0:
        return None
    if p == q:
        lam = 3 * p[0] * p[0] % P * inv(2 * p[1] % P, P) % P
    else:
        lam = (q[1] - p[1]) % P * inv((q[0] - p[0]) % P, P) % P
    x = (lam * lam - p[0] - q[0]) % P
    return (x, (lam * (p[0] - x) - p[1]) % P)


def mul(k, p):
    r = None
    while k:
        if k & 1:
            r = add(r, p)
        p = add(p, p)
        k >>= 1
    return r


def sha256(b):
    return hashlib.sha256(b).digest()


def hash160(b):
    return hashlib.new("ripemd160", sha256(b)).digest()


def b58check_encode(payload):
    b = payload + sha256(sha256(payload))[:4]
    n = int.from_bytes(b, "big")
    s = ""
    while n:
        n, r = divmod(n, 58)
        s = B58[r] + s
    return "1" * (len(b) - len(b.lstrip(b"\x00"))) + s


def address_ok(a):
    """base58check.

    ⚠️ base58 deliberately omits 0, O, I and l so that lookalike characters CANNOT be confused.
       That design is what makes a one-character substitution detectable by arithmetic rather than
       by eyesight — always check an address before checking a signature against it.
    """
    n = 0
    for c in a:
        if c not in B58:
            return False, "character %r is not in the base58 alphabet" % c
        n = n * 58 + B58.index(c)
    b = n.to_bytes((n.bit_length() + 7) // 8, "big")
    b = b"\x00" * (len(a) - len(a.lstrip("1"))) + b
    if len(b) != 25:
        return False, "decodes to %d bytes, not 25" % len(b)
    if sha256(sha256(b[:-4]))[:4] != b[-4:]:
        return False, "CHECKSUM FAILS — this is not a Bitcoin address"
    return True, "valid"


def varint(n):
    if n < 0xFD:
        return bytes([n])
    if n <= 0xFFFF:
        return b"\xfd" + n.to_bytes(2, "little")
    return b"\xfe" + n.to_bytes(4, "little")


def msg_hash(message):
    """The Bitcoin signed-message digest.

    The magic prefix is what stops a signature made here from being replayed as a TRANSACTION
    signature — the two commit to different byte strings.
    """
    m = message.encode("utf-8")
    return sha256(sha256(b"\x18Bitcoin Signed Message:\n" + varint(len(m)) + m))


def structural(sig_b64):
    """Everything decidable from the signature bytes ALONE — no message involved."""
    out = []
    try:
        raw = base64.b64decode(sig_b64)
    except Exception as e:
        return [("base64 decodes", False, type(e).__name__)]
    out.append(("signature is 65 bytes", len(raw) == 65, "%d bytes" % len(raw)))
    if len(raw) != 65:
        return out
    hdr = raw[0]
    out.append(("header byte in 27..34", 27 <= hdr <= 34,
                "header = %d%s" % (hdr, "" if 27 <= hdr <= 34 else "  <- not a signed-message header")))
    r = int.from_bytes(raw[1:33], "big")
    on = []
    for recid in range(4):
        x = r + (N if recid >= 2 else 0)
        if x >= P:
            continue
        y2 = (pow(x, 3, P) + 7) % P
        if pow(pow(y2, (P + 1) // 4, P), 2, P) == y2:
            on.append(recid)
    out.append(("r is on the curve", bool(on),
                "recovery ids %s" % on if on else
                "NONE — r cannot be (kG).x, so this is not an ECDSA signature over anything"))
    return out


def recover(message, sig_b64):
    """Recover the address a signature commits to. Returns (pubkey_hex, address, error)."""
    raw = base64.b64decode(sig_b64)
    if len(raw) != 65:
        return None, None, "signature is %d bytes, not 65" % len(raw)
    header = raw[0]
    if not 27 <= header <= 34:
        return None, None, "header byte %d out of range 27..34" % header
    recid = (header - 27) & 3
    compressed = (header - 27) >= 4
    r = int.from_bytes(raw[1:33], "big")
    s = int.from_bytes(raw[33:65], "big")
    if not (1 <= r < N and 1 <= s < N):
        return None, None, "r or s out of range"

    e = int.from_bytes(msg_hash(message), "big")
    x = r + (N if recid >= 2 else 0)
    if x >= P:
        return None, None, "x out of field"
    y2 = (pow(x, 3, P) + 7) % P
    y = pow(y2, (P + 1) // 4, P)
    if pow(y, 2, P) != y2:
        return None, None, "no square root — r is not an x-coordinate on the curve"
    if (y & 1) != (recid & 1):
        y = P - y

    rinv = inv(r, N)
    Q = mul(rinv, add(mul(s, (x, y)), mul(N - (e % N), (GX, GY))))
    if Q is None:
        return None, None, "recovered point at infinity"
    if compressed:
        pub = bytes([2 + (Q[1] & 1)]) + Q[0].to_bytes(32, "big")
    else:
        pub = b"\x04" + Q[0].to_bytes(32, "big") + Q[1].to_bytes(32, "big")
    return pub.hex(), b58check_encode(b"\x00" + hash160(pub)), None


def selftest():
    print("=" * 84)
    print(" SELF-TEST — is the arithmetic in this file correct?")
    print("=" * 84)
    a = b58check_encode(b"\x00" + hash160(bytes.fromhex(GENESIS_PUBKEY)))
    ok = a == GENESIS_ADDR
    print("  the genesis block's published public key hashes to")
    print("     %s" % a)
    print("  expected")
    print("     %s" % GENESIS_ADDR)
    print("  ⇒ %s" % ("PASS — the address arithmetic is correct" if ok else "FAIL — do not use this file"))
    v, why = address_ok(GENESIS_ADDR)
    print("  base58check on that address: %s (%s)" % (v, why))
    return ok


def main(argv):
    if len(argv) < 4:
        selftest()
        print("""
  USAGE
      python verify/verify_signed_message.py <address> <signature-base64> <message-file>

  The message MUST come from a file, byte for byte. A signature commits to exact bytes, and
  retyping a message through a shell will change them.

  HOW TO READ THE RESULT
      structural checks fail  -> the string is not a signature; the message is irrelevant
      recovers to the address -> whoever made it held that private key. Nothing about WHO.
      recovers elsewhere      -> does not verify FOR THIS ADDRESS under the message given
""")
        return 0

    addr, sig = argv[1], argv[2]
    message = open(argv[3], "r", encoding="utf-8").read()

    print("=" * 84)
    print(" STRUCTURAL — decidable from the signature alone, before any message")
    print("=" * 84)
    ok_struct = True
    for name, ok, note in structural(sig):
        print("  %-26s %-4s %s" % (name, "OK" if ok else "FAIL", note))
        ok_struct = ok_struct and ok
    v, why = address_ok(addr)
    print("  %-26s %-4s %s" % ("address parses", "OK" if v else "FAIL", why))

    print()
    print("=" * 84)
    print(" RECOVERY")
    print("=" * 84)
    pub, got, err = recover(message, sig)
    if err:
        print("  could not recover: %s" % err)
        print("""
  ⇒ Because this failed a STRUCTURAL check, the message text is irrelevant to the outcome.""")
        return 1
    print("  message length   %d bytes" % len(message.encode("utf-8")))
    print("  recovers to      %s" % got)
    print("  expected         %s" % addr)
    print("  public key       %s…" % pub[:32])
    print()
    if got == addr:
        print("  ✅ VERIFIED. Whoever produced this signature held the private key for that address.")
        print("     ⚠️ It says nothing about WHO they are, and nothing about whether they hold it now.")
        return 0
    print("""  ⛔ DOES NOT VERIFY FOR THIS ADDRESS.

  ⚠️ Not necessarily a forgery. A signed message commits to EXACT BYTES — a changed quote mark,
     accent or trailing newline breaks a genuine signature. Check the message file first.""")
    return 1


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main(sys.argv))
