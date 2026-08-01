#!/usr/bin/env python3
"""coinbase_keys.py — distinct coinbase pubkeys (fresh-key-per-coinbase).

Full run: reads coinbase_output_script_hex from early_blocks_merged.csv (populate it via
acquire_rpc.py / acquire.sql — it is EMPTY in the committed CSV), extracts each block's P2PK
coinbase pubkey, and counts distinct keys + flags any reuse over the whole Patoshi era.

Until that column is acquired, this confirms the pattern on a SMALL real sample fetched from the
chain (blocks 0,1,2,3,9). Every early coinbase is bare P2PK: `41 <65-byte pubkey> ac`.

Grade: [forensic]. Run: python coinbase_keys.py
"""
import csv

# fetched from the chain (blockchain.info / known genesis+block-9), verbatim P2PK output pubkeys:
SAMPLE = {
 0: "04678afdb0fe5548271967f1a67130b7105cd6a828e03909a67962e0ea1f61deb649f6bc3f4cef38c4f35504e51ec112de5c384df7ba0b8d578a4c702b6bf11d5f",
 1: "0496b538e853519c726a2c91e61ec11600ae1390813a627c66fb8be7947be63c52da7589379515d4e0a604f8141781e62294721166bf621e73a82cbf2342c858ee",
 2: "047211a824f55b505228e4c3d5194c1fcfaa15a456abdf37f9b9d97a4040afc073dee6c89064984f03385237d92167c13e236446b417ab79a0fcae412ae3316b77",
 3: "0494b9d3e76c5b1629ecf97fff95d7a4bbdac87cc26099ada28066c6ff1eb9191223cd897194a08d0c2726c5747f1db49e8cf90e75dc3e3550ae9b30086f3cd5aa",
 9: "0411db93e1dcdb8a016b49840f8c53bc1eb68a382e97b1482ecad7b148a6909a5cb2e0eaddfb84ccf9744464f82e160bfa9b8b64f9d4c03f999b8643f656b412a3",
}

def p2pk_pubkey(spk_hex):
    """Extract the pubkey from a bare-P2PK coinbase output: 0x41 <65> 0xac."""
    if not spk_hex:
        return None
    b = bytes.fromhex(spk_hex)
    if len(b) >= 67 and b[0] == 0x41 and b[-1] == 0xAC:
        return b[1:66].hex()
    return None

def full_run():
    keys, dupes, n = {}, [], 0
    for r in csv.DictReader(open("early_blocks_merged.csv", newline="")):
        pk = p2pk_pubkey(r.get("coinbase_output_script_hex", ""))
        if pk is None:
            continue
        n += 1
        if pk in keys:
            dupes.append((keys[pk], int(r["height"])))
        else:
            keys[pk] = int(r["height"])
    return n, len(keys), dupes

def main():
    n, distinct, dupes = full_run()
    if n:
        print("FULL RUN (coinbase_output_script_hex present):")
        print(f"  coinbase P2PK outputs read : {n:,}")
        print(f"  DISTINCT pubkeys           : {distinct:,}")
        print(f"  reused keys (height pairs) : {len(dupes)}  {dupes[:5] if dupes else '(none — fresh key per block)'}")
        return
    print("coinbase_output_script_hex is EMPTY in the CSV — showing the fetched real sample.\n")
    print("sample coinbase pubkeys (from the chain):")
    for h, pk in SAMPLE.items():
        print(f"  block {h:>2}: {pk[:24]}…")
    distinct_sample = len(set(SAMPLE.values()))
    print(f"\n  sample size {len(SAMPLE)}, distinct pubkeys {distinct_sample}  "
          f"-> {'ALL DISTINCT (fresh key per coinbase)' if distinct_sample==len(SAMPLE) else 'REUSE FOUND'}")
    print("\nFor the full ~22,540-block count: populate coinbase_output_script_hex via")
    print("  python acquire_rpc.py  (node)   or   acquire.sql Query A  (BigQuery)")
    print("then re-run this script — it will print DISTINCT pubkeys and any reuse over the whole era.")
    assert distinct_sample == len(SAMPLE)

if __name__ == "__main__":
    main()
