#!/usr/bin/env python3
"""spend_chain.py — Tier C: what Satoshi did with the first-spent coinbase (block 9).

Block 9's 50-BTC coinbase (P2PK to key 0411db93…) is the FIRST Patoshi coinbase ever spent. This
traces its full spend path from the raw transaction bytes (verbatim from the chain). Every output is
a value + a P2PK pubkey; the ONLY reused key is the block-9 key itself, kept as change at each hop.

Empirical facts only — no interpretation, no third parties beyond the on-chain recipient keys.
Grade: [forensic]. The block-9 key never signed anything except these spends (all on-chain).
Run: python spend_chain.py
"""

import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")  # render the '→' output on Windows cp1252 consoles too

CB9_TXID   = "0437cd7f8525ceed2324359c2d0ba26006d92d856a9c20fa0241106ee5a597c9"  # block 9 coinbase
SATOSHI_K9 = "0411db93e1dcdb8a016b49840f8c53bc1eb68a382e97b1482ecad7b148a6909a5cb2"  # its pubkey (prefix)

# Raw transactions of the chain (blockstream.info /tx/<id>/hex), in order:
CHAIN = [
 ("f4184fc5…9e16", 170, "0100000001c997a5e56e104102fa209c6a852dd90660a20b2d9c352423edce25857fcd370400"
  "0000004847304402204e45e16932b8af514961a1d3a1a25fdf3f4f7732e9d624c6c61548ab5fb8cd410220181522ec8eca07"
  "de4860a4acdd12909d831cc56cbbac4622082221a8768d1d0901ffffffff0200ca9a3b00000000434104ae1a62fe09c5f51b"
  "13905f07f06b99a2f7159b2225f374cd378d71302fa28414e7aab37397f554a7df5f142c21c1b7303b8a0626f1baded5c72a7"
  "04f7e6cd84cac00286bee0000000043410411db93e1dcdb8a016b49840f8c53bc1eb68a382e97b1482ecad7b148a6909a5cb2"
  "e0eaddfb84ccf9744464f82e160bfa9b8b64f9d4c03f999b8643f656b412a3ac00000000"),
 ("a16f3ce4…14be", 181, "0100000001169e1e83e930853391bc6f35f605c6754cfead57cf8387639d3b4096c54f18f4010000"
  "0048473044022027542a94d6646c51240f23a76d33088d3dd8815b25e9ea18cac67d1171a3212e02203baf203c6e7b80ebd3e5"
  "88628466ea28be572fe1aaa3f30947da4763dd3b3d2b01ffffffff0200ca9a3b00000000434104b5abd412d4341b45056d3e37"
  "6cd446eca43fa871b51961330deebd84423e740daa520690e1d9e074654c59ff87b408db903649623e86f1ca5412786f61ade2"
  "bfac005ed0b20000000043410411db93e1dcdb8a016b49840f8c53bc1eb68a382e97b1482ecad7b148a6909a5cb2e0eaddfb84"
  "ccf9744464f82e160bfa9b8b64f9d4c03f999b8643f656b412a3ac00000000"),
 ("591e91f8…8073", 182, "0100000001be141eb442fbc446218b708f40caeb7507affe8acff58ed992eb5ddde43c6fa10100000"
  "04847304402201f27e51caeb9a0988a1e50799ff0af94a3902403c3ad4068b063e7b4d1b0a76702206713f69bd344058b0dee5"
  "5a9798759092d0916dbbc3e592fee43060005ddc17401ffffffff0200e1f5050000000043410401518fa1d1e1e3e162852d68d"
  "9be1c0abad5e3d6297ec95f1f91b909dc1afe616d6876f92918451ca387c4387609ae1a895007096195a824baf9c38ea98c09c"
  "3ac007ddaac0000000043410411db93e1dcdb8a016b49840f8c53bc1eb68a382e97b1482ecad7b148a6909a5cb2e0eaddfb84c"
  "cf9744464f82e160bfa9b8b64f9d4c03f999b8643f656b412a3ac00000000"),
 ("12b5633b…91ba", 182, "010000000173805864da01f15093f7837607ab8be7c3705e29a9d4a12c9116d709f8911e59010000"
  "0049483045022052ffc1929a2d8bd365c6a2a4e3421711b4b1e1b8781698ca9075807b4227abcb0221009984107ddb9e381378"
  "2b095d0d84361ed4c76e5edaf6561d252ae162c2341cfb01ffffffff0200e1f50500000000434104baa9d36653155627c740b3"
  "409a734d4eaf5dcca9fb4f736622ee18efcf0aec2b758b2ec40db18fbae708f691edb2d4a2a3775eb413d16e2e3c0f8d4c69119"
  "fd1ac009ce4a60000000043410411db93e1dcdb8a016b49840f8c53bc1eb68a382e97b1482ecad7b148a6909a5cb2e0eaddfb84"
  "ccf9744464f82e160bfa9b8b64f9d4c03f999b8643f656b412a3ac00000000"),
 ("828ef3b0…09fe", 183, "0100000001ba91c1d5e55a9e2fab4e41f55b862a73b24719aad13a527d169c1fad3b63b512010000"
  "0049483045022100c12a7d54972f26d14cb311339b5122f8c187417dde1e8efb6841f55c34220ae0022066632c5cd4161efa3a"
  "2837764eee9eb84975dd54c2de2865e9752585c53e7cce01ffffffff0200ca9a3b00000000434104bed827d37474beffb37efe"
  "533701ac1f7c600957a4487be8b371346f016826ee6f57ba30d88a472a0e4ecd2f07599a795f1f01de78d791b382e65ee1c58b"
  "4508ac00d2496b0000000043410411db93e1dcdb8a016b49840f8c53bc1eb68a382e97b1482ecad7b148a6909a5cb2e0eaddfb"
  "84ccf9744464f82e160bfa9b8b64f9d4c03f999b8643f656b412a3ac00000000"),
]
# blockstream confirms 828ef3b0 vout1 (the last change) is UNSPENT to date (vout0 spent at block 496):
TERMINUS_CHANGE_UNSPENT = True

import hashlib

def parse(raw):
    b = bytes.fromhex(raw); o = 5
    prev = b[o:o+32][::-1].hex(); o += 32 + 4
    o += 1 + b[o] + 4                                   # scriptSig + sequence
    nout = b[o]; o += 1
    outs = []
    for _ in range(nout):
        val = int.from_bytes(b[o:o+8], "little"); o += 8
        L = b[o]; o += 1; spk = b[o:o+L]; o += L
        pub = spk[1:1+65].hex() if spk and spk[0] == 0x41 else spk.hex()
        outs.append((val, pub))
    return prev, outs

def main():
    print("Tier C — the block-9 coinbase (50 BTC, Satoshi's key 0411db93), spend path:\n")
    prev_expected = CB9_TXID
    sent, recipients, change = 0, set(), 0
    for name, height, raw in CHAIN:
        prev, outs = parse(raw)
        assert prev == prev_expected, f"chain break at {name}"
        line = []
        for i,(v,pub) in enumerate(outs):
            if pub.startswith(SATOSHI_K9):
                line.append(f"{v/1e8:.0f} BTC change→block-9 key")
                change = v
            else:
                line.append(f"{v/1e8:.0f} BTC→{pub[:12]}…")
                sent += v; recipients.add(pub[:16])
        print(f"  blk{height:<4} {name}: " + " | ".join(line))
        # recompute this tx's own txid to chain the next assert
        prev_expected = hashlib.sha256(hashlib.sha256(bytes.fromhex(raw)).digest()).digest()[::-1].hex()

    print(f"\n  block 9 coinbase: 50 BTC")
    print(f"  spent out to {len(recipients)} distinct NEW keys: {sent/1e8:.0f} BTC")
    print(f"  residual change at the reused block-9 key: {change/1e8:.0f} BTC")
    print(f"  that {change/1e8:.0f}-BTC change output (block 183) is UNSPENT to date: {TERMINUS_CHANGE_UNSPENT}")
    print("\n  Empirical: Satoshi reused ONE key (block-9 coinbase) as change through 5 spends in Jan 2009,")
    print("  paid 5 distinct new keys, and left the final 18 BTC untouched. [forensic]")

if __name__ == "__main__":
    main()
