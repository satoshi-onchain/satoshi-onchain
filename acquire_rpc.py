#!/usr/bin/env python3
"""Build the early-block CSV from a synced Bitcoin Core node (authoritative, [C-chain]).

Emits, for heights 0..MAX, the fields the classifier and anchor-verifier need:
    height,timestamp,nonce,coinbase_script_hex,coinbase_value,coinbase_output_script_hex,coinbase_spent

`coinbase_script_hex` is the coinbase scriptSig (contains the ExtraNonce Lerner parses).
`coinbase_spent` is chainstate-derived: gettxout()==null means the output is spent.
(Genesis is special: its coinbase is never in the UTXO set, so it reads "spent" -> we
force it to a sentinel; it is unspendable, not spent.)

    python acquire_rpc.py --rpc http://user:pass@127.0.0.1:8332 --max-height 60000 > early_blocks.csv
"""
import argparse, csv, json, sys, urllib.request

SAT = 100_000_000
_ID = 0


def rpc(url, method, *params):
    global _ID
    _ID += 1
    body = json.dumps({"jsonrpc": "1.0", "id": _ID, "method": method,
                       "params": list(params)}).encode()
    req = urllib.request.Request(url, data=body, headers={"content-type": "text/plain"})
    with urllib.request.urlopen(req, timeout=120) as r:
        out = json.load(r)
    if out.get("error"):
        raise RuntimeError(f"{method}{params}: {out['error']}")
    return out["result"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rpc", required=True, help="http://user:pass@host:8332")
    ap.add_argument("--max-height", type=int, default=60000)
    ap.add_argument("--progress-every", type=int, default=1000)
    a = ap.parse_args()

    w = csv.writer(sys.stdout)
    w.writerow(["height", "timestamp", "nonce", "coinbase_script_hex",
                "coinbase_value", "coinbase_output_script_hex", "coinbase_spent"])

    for h in range(a.max_height + 1):
        bh = rpc(a.rpc, "getblockhash", h)
        blk = rpc(a.rpc, "getblock", bh, 2)          # verbosity 2 -> decoded coinbase
        cb = blk["tx"][0]
        cb_script = cb["vin"][0].get("coinbase", "")  # scriptSig hex (ExtraNonce lives here)
        vout0 = cb["vout"][0]
        cb_value = round(vout0["value"] * SAT)
        cb_out_spk = vout0["scriptPubKey"].get("hex", "")
        if h == 0:
            spent = "unspendable"                      # genesis coinbase never enters UTXO set
        else:
            spent = "1" if rpc(a.rpc, "gettxout", cb["txid"], 0) is None else "0"
        w.writerow([h, blk["time"], blk["nonce"], cb_script,
                    cb_value, cb_out_spk, spent])
        if a.progress_every and h % a.progress_every == 0:
            print(f"...height {h}", file=sys.stderr)


if __name__ == "__main__":
    main()
