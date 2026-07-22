#!/usr/bin/env python3
"""Reproduce the Patoshi 'fingerprint' from patoshi_labeled.csv.

  python plots.py patoshi_labeled.csv        # -> extranonce_fingerprint.png, nonce_lsb_rate.png

Panel A  ExtraNonce vs block height: Patoshi's coordinated machine leaves near-linear
         tracks distinct from the rest of the network. This visual separation is Lerner's
         authoritative signal; the nonce-LSB filter (below) is corroborating.
Panel B  Rolling nonce-LSB pass-rate: elevated through the Patoshi era, collapsing to the
         ~19.5% chance baseline near block ~54,000 (late 2010) as Satoshi exits.
"""
import csv, sys

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
except ImportError:
    sys.exit("needs matplotlib:  pip install matplotlib")

LSB_CHANCE = 50 / 256
INK = "#1a1a1a"; MUTE = "#c9ced6"; ACCENT = "#2f6df6"   # legible, colorblind-safe pair


def load(path):
    rows = list(csv.DictReader(open(path, newline="")))
    for r in rows:
        r["height"] = int(r["height"])
        r["nonce_lsb_ok"] = r["nonce_lsb_ok"] == "1"
        r["extranonce"] = int(r["extranonce"]) if r["extranonce"] not in ("", "None") else None
    return rows


def fingerprint(rows):
    fig, ax = plt.subplots(figsize=(11, 5.2))
    other = [(r["height"], r["extranonce"]) for r in rows if r["extranonce"] is not None and not r["nonce_lsb_ok"]]
    pato = [(r["height"], r["extranonce"]) for r in rows if r["extranonce"] is not None and r["nonce_lsb_ok"]]
    if other:
        ax.scatter(*zip(*other), s=3, c=MUTE, linewidths=0, label="other miners")
    if pato:
        ax.scatter(*zip(*pato), s=3, c=ACCENT, linewidths=0, label="Patoshi candidate (nonce-LSB)")
    ax.set_title("ExtraNonce fingerprint — the Patoshi tracks", color=INK, fontsize=13, weight="bold")
    ax.set_xlabel("block height"); ax.set_ylabel("ExtraNonce")
    ax.legend(loc="upper left", frameon=False, markerscale=3)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    fig.tight_layout(); fig.savefig("extranonce_fingerprint.png", dpi=150)
    print("wrote extranonce_fingerprint.png")


def lsb_rate(rows, win=500):
    xs, ys, buf = [], [], []
    for r in rows:
        buf.append(1 if r["nonce_lsb_ok"] else 0)
        if len(buf) > win:
            buf.pop(0)
        xs.append(r["height"]); ys.append(sum(buf) / len(buf))
    fig, ax = plt.subplots(figsize=(11, 4.2))
    ax.plot(xs, ys, color=ACCENT, lw=1.6, label=f"nonce-LSB pass-rate ({win}-block roll)")
    ax.axhline(LSB_CHANCE, color=INK, ls="--", lw=1, label=f"chance baseline ({LSB_CHANCE:.1%})")
    ax.set_title("Patoshi era: nonce-LSB rate elevated, then collapsing ~block 54,000",
                 color=INK, fontsize=13, weight="bold")
    ax.set_xlabel("block height"); ax.set_ylabel("pass-rate"); ax.set_ylim(0, 1)
    ax.legend(loc="upper right", frameon=False)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    fig.tight_layout(); fig.savefig("nonce_lsb_rate.png", dpi=150)
    print("wrote nonce_lsb_rate.png")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("usage: python plots.py patoshi_labeled.csv")
    data = load(sys.argv[1])
    fingerprint(data)
    lsb_rate(data)
