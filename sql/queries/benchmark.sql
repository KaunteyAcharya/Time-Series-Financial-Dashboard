-- ============================================================
-- BENCHMARK: Compare regular view vs materialized view latency
-- Run with \timing on in psql
-- ============================================================

\timing on

-- 1. Warm-up: query the regular volatility view
SELECT symbol, trade_date, vol_20d_annualized
FROM v_rolling_volatility
WHERE symbol = 'AAPL'
ORDER BY trade_date DESC
LIMIT 100;

-- 2. Create materialized view for expensive rolling calcs
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_rolling_volatility AS
SELECT * FROM v_rolling_volatility
WITH DATA;

CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_vol_symbol_date
    ON mv_rolling_volatility (symbol, trade_date);

-- 3. Query the materialized view
SELECT symbol, trade_date, vol_20d_annualized
FROM mv_rolling_volatility
WHERE symbol = 'AAPL'
ORDER BY trade_date DESC
LIMIT 100;

-- 4. Materialized moving averages
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_moving_averages AS
SELECT * FROM v_moving_averages
WITH DATA;

CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_ma_symbol_date
    ON mv_moving_averages (symbol, trade_date);

-- 5. Materialized Bollinger bands
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_bollinger_bands AS
SELECT * FROM v_bollinger_bands
WITH DATA;

CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_bb_symbol_date
    ON mv_bollinger_bands (symbol, trade_date);

-- 6. EXPLAIN ANALYZE on key queries
EXPLAIN ANALYZE
SELECT * FROM v_rolling_volatility
WHERE symbol = 'AAPL' AND trade_date >= CURRENT_DATE - INTERVAL '1 year';

EXPLAIN ANALYZE
SELECT * FROM mv_rolling_volatility
WHERE symbol = 'AAPL' AND trade_date >= CURRENT_DATE - INTERVAL '1 year';

\timing off
