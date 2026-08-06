-- ============================================================================
-- Every fee-paying block in Bitcoin's first year.
--
-- WHAT THIS ESTABLISHES
--   Exactly eight blocks in the whole of 2009 collected a transaction fee.
--   Total fees paid across the year: 2.87 BTC. Every other block paid exactly 50.00.
--   The earliest is block 2817 (3 Feb 2009), whose 2.01 BTC fee is larger than the
--   other seven combined.
--
-- WHAT IT DOES NOT ESTABLISH
--   Nothing about WHO mined any of these blocks, or why any fee was set. A coinbase
--   value is not an identity. Do not read this table as attributing anything to anyone.
--
-- HOW TO RUN IT WITHOUT AN ACCOUNT OF OURS
--   console.cloud.google.com/bigquery -> paste -> Run. The dataset is Google's public
--   mirror of the chain; the free sandbox tier is enough. We supply no credentials and
--   you do not need ours.
--
-- HOW TO CHECK IT WITHOUT BIGQUERY AT ALL
--   There are only eight rows. Look each height up in any block explorer and read the
--   coinbase output. Eight manual lookups settles it. That is the point of publishing a
--   result small enough to check by hand.
--
-- WHY BIGQUERY RATHER THAN AN EXPLORER API
--   Sweeping 32,000 blocks through the public explorer APIs gets rate-limited into
--   failure -- our own first attempt (early_tx_survey.py) died mid-sweep for exactly
--   this reason. This answers in seconds.
--
-- A DATA-QUALITY WARNING, INCLUDING ABOUT OUR OWN EARLIER FILE
--   Several early-chain datasets in circulation -- including this repo's own
--   early_blocks.csv -- carry a `coinbase_value` column in which EVERY row holds the
--   identical 5000000000. It was assumed at acquisition, never read from the chain.
--   Searching such a file for fee-bearing blocks returns ZERO, and the conclusion that
--   invites -- "no early block ever collected a fee" -- is FALSE, as this query shows.
--   In that file the heights and timestamps are sound; `coinbase_value` is inert and
--   must not be used.
-- ============================================================================

SELECT
  block_number,
  block_timestamp,
  output_value / 1e8                     AS coinbase_btc,
  (output_value - 5000000000) / 1e8      AS fee_btc
FROM `bigquery-public-data.crypto_bitcoin.transactions`
WHERE is_coinbase = TRUE
  AND block_timestamp >= TIMESTAMP('2009-01-01')
  AND block_timestamp <  TIMESTAMP('2010-01-01')
  AND output_value <> 5000000000
ORDER BY block_number

-- Expected result, 6 Aug 2026 (the subsidy was 50 BTC throughout 2009, so fee = coinbase - 50):
--
--    2817   2009-02-03 05:16:42 UTC   52.01   2.01
--   12983   2009-05-02 05:02:21 UTC   50.03   0.03
--   14047   2009-05-11 14:58:31 UTC   50.10   0.10
--   19863   2009-07-20 22:54:07 UTC   50.14   0.14
--   20770   2009-08-07 22:27:45 UTC   50.13   0.13
--   23079   2009-09-17 16:10:30 UTC   50.12   0.12
--   25468   2009-10-20 22:30:46 UTC   50.12   0.12
--   28507   2009-12-01 21:45:59 UTC   50.22   0.22
--
-- These are settled blocks from 2009. If your run disagrees, the discrepancy is in the
-- tooling, not the chain -- and we would want to hear about it.
