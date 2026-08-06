-- ============================================================================
-- Every payment made in Bitcoin's first year: 219 transactions.
--
-- WHAT THIS ESTABLISHES
--   For roughly its first year the chain is a near-unbroken run of coinbase-only blocks,
--   so every actual PAYMENT in that period can be listed EXHAUSTIVELY. There are 219.
--   That turns claims about early transfers into checkable ones: when an account says
--   "N coins moved on date D", you do not need to trust it, or trust us -- you look at
--   the handful of transactions that existed in that window and see whether one fits.
--   Monthly counts: 32 37 21 17 18 8 5 6 11 13 15 36.
--
-- READ THIS BEFORE USING THE ADDRESS COLUMNS -- ordering is NOT guaranteed
--   `outputs_btc` is ordered (ORDER BY o.index). `out_addresses` and `in_addresses` are
--   STRING_AGG WITHOUT an ORDER BY, so THEIR ORDER MAY NOT MATCH THE AMOUNTS. Do not pair
--   them positionally. Identify by ELIMINATION instead: an address appearing on the inputs
--   is receiving change, so the other output is the payment. We left the query as it was
--   actually run rather than silently fixing it, because the CSV in circulation came from
--   this exact text.
--
-- WHAT IT DOES NOT ESTABLISH
--   Nothing about WHO. Addresses are not names. Nothing here binds a person to a payment;
--   that always requires an outside document, and then it is testimony, not cryptography.
--
-- WHY BIGQUERY
--   Sweeping the first year through public explorer APIs gets rate-limited into failure --
--   our own early_tx_survey.py died mid-sweep twice. This answers in seconds. Free sandbox
--   tier is enough; no credentials of ours are involved.
--
-- NOTE: `hash` is RESERVED in BigQuery Standard SQL and must be backticked. Writing t.hash
-- fails with: Syntax error: Expected end of input but got keyword HASH.
-- ============================================================================

SELECT
  t.block_number,
  t.block_timestamp,
  t.`hash`                                        AS txid,
  t.input_count,
  t.output_count,
  t.input_value  / 1e8                            AS in_btc,
  t.output_value / 1e8                            AS out_btc,
  t.fee          / 1e8                            AS fee_btc,
  (SELECT STRING_AGG(FORMAT('%.8f', o.value / 1e8), ' | ' ORDER BY o.index)
     FROM UNNEST(t.outputs) AS o)                 AS outputs_btc,
  (SELECT STRING_AGG(a, ' | ')
     FROM UNNEST(t.outputs) AS o, UNNEST(o.addresses) AS a)  AS out_addresses,
  (SELECT STRING_AGG(a, ' | ')
     FROM UNNEST(t.inputs)  AS i, UNNEST(i.addresses) AS a)  AS in_addresses
FROM `bigquery-public-data.crypto_bitcoin.transactions` AS t
WHERE t.is_coinbase = FALSE
  AND t.block_timestamp < TIMESTAMP('2010-01-01')
ORDER BY t.block_number, t.`hash`
