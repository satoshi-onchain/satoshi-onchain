#!/usr/bin/env python3
"""authorship_test.py — what would machine-verifiably prove control of a Satoshi key? (Tier C)

The only machine-checkable proof that someone controls a Satoshi key is a signature over a FRESH
challenge (chosen after the fact, so it cannot be lifted from public data) under a known-Satoshi
public key -- or, equivalently, moving a known-Satoshi coin. This script shows, using ONLY public
on-chain data and NO private key, why re-presenting an existing signature is not that proof:

  1. Satoshi's block-9 key produced public signatures in 2009 (spend_chain.py, section 9). ANYONE can
     re-verify one against the key -> "Verified OK" -- holding no private key. So a passing
     verification of an already-public signature demonstrates control of NO key.
  2. That same signature FAILS against a fresh challenge chosen now. A real proof would sign THIS.
  3. The ~1.1M-BTC dormant coinbases (section 1) never signed at all -> there is not even a public
     signature to re-present; only a fresh signature or a coin move could speak for them.

On the machine standard, the control predicate
    ECDSA_verify(known_satoshi_pubkey, H(fresh_challenge), sig) == True   (challenge chosen after the fact)
or a spend of a known-Satoshi coin has never returned True on-chain. This is neutral cryptographic
epistemics -- no person, no external source, only public bytes -- and it is the foundation the
three-tier model (README) rests on: identity is a key-control predicate, not a claim.

Grade: [definitional]/[forensic]. Run: python authorship_test.py
"""
import hashlib
from nonce_safety import verify, extract, FULL_K9        # secp256k1 verify + sig/digest extractor
from spend_chain import CHAIN                            # the public block-9-chain txs (single source)

def dsha(b): return hashlib.sha256(hashlib.sha256(b).digest()).digest()

def main():
    pub = (int(FULL_K9[2:66], 16), int(FULL_K9[66:130], 16))
    name, height, raw = CHAIN[0]                          # a real public 2009 signature (block 170)
    r, s, z = extract(raw)

    print("What would machine-verifiably prove control of a Satoshi key?")
    print("(only public data below; this script holds NO private key)\n")

    print(f"  [1] a PUBLIC 2009 signature by block-9 key 0411db93 (blk {height}, tx {name}):")
    print(f"      verify(satoshi_pubkey, its own 2009 digest, sig) = {verify(pub, z, r, s)}   <- 'Verified OK'")
    print("      Anyone can produce this line from public bytes -> it shows control of NO key.\n")

    fresh = b"I control a Satoshi key. <fresh challenge chosen after the fact>"
    z_fresh = int.from_bytes(dsha(fresh), "big")
    print("  [2] the SAME signature against a FRESH challenge (what a real proof must sign):")
    print(f"      verify(satoshi_pubkey, H(fresh_challenge), sig) = {verify(pub, z_fresh, r, s)}   <- fails")
    print(f"      fresh challenge: {fresh.decode()!r}\n")

    print("  [3] the ~1.1M-BTC dormant Patoshi coinbases (section 1) NEVER signed -> there is not even")
    print("      a public signature to re-present; only a fresh signature or a coin move speaks for them.\n")

    print("STANDARD: the control predicate")
    print("    ECDSA_verify(known_satoshi_pubkey, H(fresh_challenge), sig) == True   (challenge fixed after the fact)")
    print("  -- or a spend of a known-Satoshi coin -- has never returned True on-chain. A signature binds")
    print("  to exactly one digest, so re-presenting a public one proves nothing; only signing a fresh")
    print("  challenge (or moving a coin) needs the private key. [neutral cryptographic epistemics]")

    assert verify(pub, z, r, s) and not verify(pub, z_fresh, r, s)
    print("\nALL CHECKS PASSED")

if __name__ == "__main__":
    main()
