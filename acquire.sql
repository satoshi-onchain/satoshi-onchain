-- Early-block fields for the Patoshi classifier.
-- Dataset: bigquery-public-data.crypto_bitcoin  (Google BigQuery public data)
-- Two tiers. Run QUERY A first (cheap, seconds). QUERY B is the optional dormancy
-- enrichment (a full-history anti-join, larger scan). The node-RPC path
-- (acquire_rpc.py) is the authoritative alternative and needs no schema assumptions.
--
-- patoshi.py reads by HEADER NAME (not column order) and tolerates a minimal export,
-- so Query A alone drives the classifier + fingerprint. Column aliases below already
-- match what the script looks for.

-- ============================================================================
-- QUERY 0 — schema sanity check (run once; ~0 bytes). Confirms coinbase_param + nonce.
-- ============================================================================
-- SELECT number, timestamp, nonce, coinbase_param
-- FROM `bigquery-public-data.crypto_bitcoin.blocks`
-- WHERE number = 170;

-- ============================================================================
-- QUERY A — classification data, from `blocks` only (cheap: the blocks table is small).
-- Produces the Patoshi set + ExtraNonce fingerprint. coinbase_param is the coinbase
-- scriptSig hex (ExtraNonce lives here). Value is a literal 50 BTC — exact for every
-- block 0..209,999 — so no transactions-table scan is needed. Spent = '?' (unknown yet).
-- Export the result to early_blocks.csv.
-- ============================================================================
SELECT
  number                     AS height,
  UNIX_SECONDS(timestamp)    AS timestamp,
  nonce                      AS nonce,                 -- integer nonce
  coinbase_param             AS coinbase_script_hex,   -- coinbase scriptSig hex
  5000000000                 AS coinbase_value,        -- 50 BTC, exact for this range
  ''                         AS coinbase_output_script_hex,
  '?'                        AS coinbase_spent         -- fill via Query B (optional)
FROM `bigquery-public-data.crypto_bitcoin.blocks`
WHERE number <= 60000
ORDER BY height;

-- ============================================================================
-- QUERY B — dormancy (optional). For each early coinbase, was its output ever spent?
-- The `spent` CTE scans every input in history, so this is the expensive one; it is
-- a standard full-history anti-join. Export to spent_status.csv, then merge
-- coinbase_spent back into early_blocks.csv by height (see merge_spent.py) and re-run
-- patoshi.py to get the unspent/spent split.
-- ============================================================================
-- WITH early_cb AS (
--   SELECT `hash` AS txid, block_number AS height
--   FROM `bigquery-public-data.crypto_bitcoin.transactions`
--   WHERE is_coinbase = TRUE AND block_number <= 60000
-- ),
-- spent AS (
--   SELECT DISTINCT i.spent_transaction_hash AS txid
--   FROM `bigquery-public-data.crypto_bitcoin.transactions`, UNNEST(inputs) AS i
--   WHERE i.spent_transaction_hash IS NOT NULL
-- )
-- SELECT
--   e.height,
--   IF(e.height = 0, 'unspendable',
--      IF(e.txid IN (SELECT txid FROM spent), '1', '0')) AS coinbase_spent
-- FROM early_cb e
-- ORDER BY height;

-- ============================================================================
-- QUERY C — resolve a real "old wallet just moved" event to originating coinbase HEIGHTS,
-- so judge.py can rule it Patoshi-or-not. A Patoshi coin is a coinbase P2PK output, so a
-- spend consumes a coinbase directly: the spending tx's input outpoint IS the coinbase.
--   * Path 1: you have the SPENDING txid  -> set @spend_txid.
--   * Path 2: you have a FUNDING address  -> set @addr; finds coinbases that paid it.
-- Export the `height` column and feed it to:  python judge.py --file <that.csv>
-- ============================================================================
-- Path 1 — spending txid -> the coinbase heights it consumed:
-- SELECT DISTINCT cb.block_number AS height
-- FROM `bigquery-public-data.crypto_bitcoin.transactions` s, UNNEST(s.inputs) i
-- JOIN `bigquery-public-data.crypto_bitcoin.transactions` cb
--   ON cb.`hash` = i.spent_transaction_hash AND cb.is_coinbase
-- WHERE s.`hash` = '<PASTE_SPENDING_TXID>'
-- ORDER BY height;
--
-- Path 2 — a funding address -> the coinbase blocks that paid it:
-- SELECT DISTINCT block_number AS height
-- FROM `bigquery-public-data.crypto_bitcoin.transactions`, UNNEST(outputs) o
-- WHERE is_coinbase AND '<PASTE_ADDRESS>' IN UNNEST(o.addresses)
-- ORDER BY height;

-- ============================================================================
-- QUERY D — COINBASE OUTPUT KEYS (fresh-key-per-coinbase). Cheap: transactions table,
-- coinbase rows only. Two forms.
--   D1 (instant answer): distinct coinbase output scripts over the Patoshi era.
--   D2 (export): per-block coinbase output script hex -> merge into early_blocks_merged.csv's
--       coinbase_output_script_hex column (by height), then run coinbase_keys.py for the
--       Patoshi-subset distinct count.
-- ============================================================================
-- D1 — instant:
-- SELECT COUNT(*) AS coinbase_outputs,
--        COUNT(DISTINCT o.script_hex) AS distinct_output_scripts,
--        COUNTIF(o.type = 'pubkey')   AS p2pk_outputs
-- FROM `bigquery-public-data.crypto_bitcoin.transactions` t, UNNEST(t.outputs) o
-- WHERE t.is_coinbase AND t.block_number BETWEEN 1 AND 54458 AND o.index = 0;
--   -> if distinct_output_scripts == coinbase_outputs, every coinbase used a fresh key.
--
-- D2 — export (header: height,coinbase_output_script_hex):
-- SELECT t.block_number AS height, o.script_hex AS coinbase_output_script_hex
-- FROM `bigquery-public-data.crypto_bitcoin.transactions` t, UNNEST(t.outputs) o
-- WHERE t.is_coinbase AND t.block_number <= 60000 AND o.index = 0
-- ORDER BY height;

-- ============================================================================
-- QUERY E — AWAKENING -> COINBASE MAP for all spent early coinbases. EXPENSIVE (full-history
-- input scan, like Query B): finds the spending tx of every early coinbase. Export to
-- spent_map.csv, then locally join to patoshi_confirmed.csv to get the ~1,145 Patoshi map.
-- ============================================================================
-- SELECT cb.block_number AS coinbase_height,
--        cb.`hash`       AS coinbase_txid,
--        s.`hash`        AS spending_txid,
--        s.block_number  AS spending_height,
--        UNIX_SECONDS(s.block_timestamp) AS spending_time
-- FROM `bigquery-public-data.crypto_bitcoin.transactions` cb
-- JOIN `bigquery-public-data.crypto_bitcoin.transactions` s, UNNEST(s.inputs) i
--   ON i.spent_transaction_hash = cb.`hash`
-- WHERE cb.is_coinbase AND cb.block_number <= 54458
-- ORDER BY coinbase_height;
