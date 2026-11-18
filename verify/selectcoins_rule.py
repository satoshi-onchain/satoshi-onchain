"""Coin selection in three early client source trees, when one wallet transaction matches exactly.

WHAT IT CHECKS. The function `SelectCoins` in `main.cpp` decides which wallet transactions a
payment spends. This script fetches `main.cpp`, `main.h`, `db.cpp`, `serialize.h` and `uint256.h`
of three early source trees from Software Heritage by content hash, verifies each file's git blob
hash locally, and checks, in each tree:

  1. `serialize.h` declares the VERSION the tree is labelled with (101, 103, 105);
  2. the wallet's key is the transaction ID: `mapWallet` is a `map<uint256, CWalletTx>`;
     `AddToWallet` inserts under `wtxIn.GetHash()`; the wallet file stores each transaction under
     `GetHash()` (`WriteTx`); and `LoadWallet` (`db.cpp`) puts each stored transaction into
     `mapWallet` under its stored key;
  3. ordering: `operator<(uint256, uint256)` compares as `base_uint`, whose `operator<` compares its
     `unsigned int` words (32-bit on x86) from `pn[WIDTH-1]` down to `pn[0]`; `GetHex()` prints the
     bytes of `pn` from last to first;
  4. `SelectCoins` walks `mapWallet` from begin() to end(); it skips a wallet transaction that is
     not final, is marked spent, or has a credit to the wallet of zero or less; and it returns at
     once the first one whose credit equals the requested amount;
  5. the requested amount is payment plus fee: `CreateTransaction` runs `nValue += nFee` and then
     `SelectCoins(nValue, ...)`, which is the only call in `main.cpp` (`main.h` does not declare it);
  6. coinbase maturity: `CWalletTx` derives from `CMerkleTx` and defines no `GetCredit` of its own;
     `CMerkleTx::GetCredit` returns 0 for a coinbase while `GetBlocksToMaturity() > 0`;
     `GetBlocksToMaturity` is `max(0, (COINBASE_MATURITY+20) - GetDepthInMainChain())`;
     `COINBASE_MATURITY` is 100; and depth is `best height - block height + 1`. So a coinbase has
     zero credit until its depth is 120, its own block counting as 1;
  7. `SelectCoins` is identical, character for character (line endings normalised), in all three
     trees, and its text matches a pinned sha256. Because the whole text is pinned, a reader can see
     every input the function reads; any added condition would change the hash.

WHAT FOLLOWS FROM THE CODE. Call a wallet transaction eligible when it is final, not marked spent,
and has a credit to the wallet greater than zero. When the requested amount (payment plus fee)
equals the credit of one or more eligible wallet transactions, `SelectCoins` returns the one that
comes first in ascending `uint256` order of its transaction ID. Among eligible wallet transactions
that choice depends only on credit and transaction ID. On a little-endian CPU (x86 is one) that
order is ascending order of the transaction ID as printed. This covers the exact-match branch
only. When no credit equals the amount, other branches of the same function apply (the smallest
larger credit, or a randomised subset sum) and are not described here.

THE THREE TREES, labelled by the VERSION their serialize.h declares.
  101  files inside the archive distributed as bitcoin-0.1.0.rar (2,132,686 bytes, sha256 8b17eb9a...)
  103  files inside the archive distributed as bitcoin-0.1.3.rar (2,127,418 bytes, sha256 3d73b1a8...)
  105  revision 1 of the SourceForge SVN repository (2009-08-30), whose tree is fetched by
       verify/sourceforge_svn_files.py
  This script checks the files' blob hashes, not the archives.

ESTABLISHES: what these three source trees do when one eligible wallet transaction's credit equals
the requested amount, and that `SelectCoins` is the same in all three.
DOES NOT ESTABLISH: which software built any particular transaction. A transaction on the chain does
not record the program that built it, and a wallet can be modified.

Usage:  python verify/selectcoins_rule.py [cache-dir]
        Fifteen files, twelve distinct blobs (uint256.h is shared by all three trees, main.h by
        101 and 103); stdlib only.
Exit 0 when every check passes, 1 otherwise.
"""
import hashlib, os, re, sys, time, urllib.error, urllib.request

sys.stdout.reconfigure(encoding="utf-8")
UA = {"User-Agent": "satoshi-onchain/verify"}
SWH = "https://archive.softwareheritage.org/api/1"
CACHE = sys.argv[1] if len(sys.argv) > 1 else "selectcoins-src"
os.makedirs(CACHE, exist_ok=True)

TREES = {
    101: {"main.cpp": "2ba261da8b038c7840acd104fdd1013972413837",
          "main.h": "0567fca5a00114d0948553f3962428d7a9bbce4a",
          "serialize.h": "31d09c06a56741f24f01926540aa8604eba411d3",
          "uint256.h": "9a0c77049774f5d9de7ce339e6ff21846265e866",
          "db.cpp": "4e181448992ffd72c0ab3592957e1afc836fb7a2"},
    103: {"main.cpp": "eaa9ab7da9210a01b71b78db6870be6add4f6e80",
          "main.h": "0567fca5a00114d0948553f3962428d7a9bbce4a",
          "serialize.h": "7f61c391504293accab789fd5c111032542f8ef9",
          "uint256.h": "9a0c77049774f5d9de7ce339e6ff21846265e866",
          "db.cpp": "db2ce285fa86be9dcf846f1fdfd3a701ece8b027"},
    105: {"main.cpp": "97000db3810f3a2834fc58558ef8c78a9a8e03af",
          "main.h": "3432b316e7f878035fa69da1903517adaabae9e5",
          "serialize.h": "b7ab86d22ab1f5639a4861c7e75e1bdda30545a5",
          "uint256.h": "9a0c77049774f5d9de7ce339e6ff21846265e866",
          "db.cpp": "f38f3ffad83a1d02dba6ec5cdcac4aec83a99a25"},
}

# sha256 of the SelectCoins function text (line endings normalised). Pinning the whole text is what
# lets the page say what the function does NOT read: any added filter changes this hash.
SELECTCOINS_SHA256 = "50a2d40807045fa67e916c7a47c8f5adba50f8320cdfe8be8d45f69adf679c64"


def git_blob_sha1(data):
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()


def fetch(sha):
    dest = os.path.join(CACHE, sha)
    if os.path.exists(dest):
        data = open(dest, "rb").read()
    else:
        for attempt in range(6):
            try:
                req = urllib.request.Request(f"{SWH}/content/sha1_git:{sha}/raw/", headers=UA)
                data = urllib.request.urlopen(req, timeout=120).read()
                break
            except urllib.error.HTTPError as e:
                if attempt == 5:
                    raise
                time.sleep(min(600, 60 * (attempt + 1)) if e.code == 429 else 5 * (attempt + 1))
            except Exception:
                if attempt == 5:
                    raise
                time.sleep(5 * (attempt + 1))
        time.sleep(1.0)
    if git_blob_sha1(data) != sha:
        raise SystemExit(f"FAIL  {sha}: content does not hash to its git blob id")
    if not os.path.exists(dest):
        open(dest, "wb").write(data)
    return data.decode("latin-1").replace("\r\n", "\n")


def function(src, signature):
    i = src.find(signature)
    if i < 0:
        return None
    depth = 0
    for k in range(src.find("{", i), len(src)):
        if src[k] == "{":
            depth += 1
        elif src[k] == "}":
            depth -= 1
            if depth == 0:
                return src[i:k + 1]
    return None


ok = True
def check(cond, label):
    global ok
    print(("  ok    " if cond else "  FAIL  ") + label)
    ok = ok and bool(cond)


bodies = {}
for version, files in TREES.items():
    print(f"\nVERSION {version}")
    src = {name: fetch(sha) for name, sha in files.items()}
    for name, sha in files.items():
        print(f"  {name:12} sha1_git {sha}  (blob hash verified)")
    m, h = src["main.cpp"], src["main.h"]
    check(re.search(r"VERSION\s*=\s*%d\s*;" % version, src["serialize.h"]), f"serialize.h declares VERSION = {version}")
    check("\nmap<uint256, CWalletTx> mapWallet;" in m, "mapWallet is declared map<uint256, CWalletTx>")
    check("uint256 hash = wtxIn.GetHash();" in m and "mapWallet.insert(make_pair(hash, wtxIn))" in m,
          "wallet transactions are inserted under their GetHash() (transaction ID)")
    lt = function(src["uint256.h"], "friend inline bool operator<(const base_uint& a, const base_uint& b)")
    check(lt and "for (int i = base_uint::WIDTH-1; i >= 0; i--)" in lt, "uint256 operator< compares pn[WIDTH-1] down to pn[0]")
    gh = function(src["uint256.h"], "std::string GetHex() const")
    check(gh and "((unsigned char*)pn)[sizeof(pn) - i - 1]" in gh, "GetHex() prints the bytes of pn from last to first")
    sc = function(m, "bool SelectCoins(int64 nTargetValue, set<CWalletTx*>& setCoinsRet)")
    check(sc is not None, "SelectCoins found")
    if sc:
        check("for (map<uint256, CWalletTx>::iterator it = mapWallet.begin(); it != mapWallet.end(); ++it)" in sc,
              "SelectCoins walks mapWallet from begin() to end()")
        check("if (!pcoin->IsFinal() || pcoin->fSpent)" in sc, "skips wallet transactions that are not final or are marked spent")
        check(re.search(r"int64 n = pcoin->GetCredit\(\);\s*if \(n <= 0\)\s*continue;", sc), "skips wallet transactions with credit <= 0")
        check(re.search(r"else if \(n == nTargetValue\)\s*\{\s*setCoinsRet\.insert\(pcoin\);\s*return true;", sc),
              "returns at once the first one whose credit equals the target")
        bodies[version] = sc
    wtx = function(h, "class CWalletTx : public CMerkleTx")
    check(wtx is not None and "GetCredit(" not in wtx, "CWalletTx derives from CMerkleTx and defines no GetCredit of its own")
    mtx = function(h, "class CMerkleTx : public CTransaction")
    gc = mtx and re.search(r"int64 GetCredit\(\) const\s*\{\s*// Must wait until coinbase is safely deep enough in the chain before valuing it\s*"
                           r"if \(IsCoinBase\(\) && GetBlocksToMaturity\(\) > 0\)\s*return 0;", mtx)
    check(gc, "CMerkleTx::GetCredit returns 0 for a coinbase while GetBlocksToMaturity() > 0")
    check("return max(0, (COINBASE_MATURITY+20) - GetDepthInMainChain());" in m, "GetBlocksToMaturity = max(0, (COINBASE_MATURITY+20) - depth)")
    check(re.search(r"static const int COINBASE_MATURITY = 100;", h), "COINBASE_MATURITY = 100")
    dep = function(m, "int CMerkleTx::GetDepthInMainChain() const")
    check(dep and re.search(r"return pindexBest->nHeight - pindex->nHeight \+ 1;\s*\}$", dep),
          "depth = best height - block height + 1 (a transaction's own block counts as 1)")
    ct = function(m, "bool CreateTransaction(")
    check(ct and re.search(r"nValue \+= nFee;\s*// Choose coins to use\s*set<CWalletTx\*> setCoins;\s*"
                           r"if \(!SelectCoins\(nValue, setCoins\)\)", ct),
          "CreateTransaction adds the fee to the payment, then calls SelectCoins with the sum")
    calls = re.findall(r"(?<![\w\"])SelectCoins\(", m)
    check(len(calls) == 2 and "SelectCoins" not in h,
          "main.cpp has one definition and one call of SelectCoins; main.h does not declare it")
    check("return CWalletDB().WriteTx(GetHash(), *this);" in h, "the wallet file stores each transaction under GetHash()")
    check(re.search(r"ssKey >> hash;\s*CWalletTx& wtx = mapWallet\[hash\];", src["db.cpp"]),
          "LoadWallet puts each stored transaction into mapWallet under its stored key")
    check(re.search(r"inline bool operator<\(const uint256& a, const uint256& b\)\s*\{ return \(base_uint256\)a <  \(base_uint256\)b; \}",
                    src["uint256.h"]), "operator<(uint256, uint256) compares as base_uint")

print()
versions = sorted(bodies)
same = len(versions) == len(TREES) and all(bodies[v] == bodies[versions[0]] for v in versions)
check(same, "SelectCoins is identical in VERSION " + ", ".join(map(str, versions)))
if same:
    digest = hashlib.sha256(bodies[versions[0]].encode('latin-1')).hexdigest()
    check(digest == SELECTCOINS_SHA256, f"SelectCoins text matches the pinned sha256 {SELECTCOINS_SHA256[:16]}...")
    print(f"        ({bodies[versions[0]].count(chr(10)) + 1} lines)")
print("\nWhen an eligible wallet transaction's credit equals the requested amount, the one first in\n"
      "ascending uint256 order of its transaction ID is selected."
      if ok else "\nOne or more checks failed; no rule is stated.")
sys.exit(0 if ok else 1)
