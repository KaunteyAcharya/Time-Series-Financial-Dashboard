-- ============================================================
-- SANITY CHECK 1: No duplicate (symbol, trade_date) rows
-- Expected: 0 rows
-- ============================================================
SELECT symbol, trade_date, COUNT(*) AS cnt
FROM prices
GROUP BY symbol, trade_date
HAVING COUNT(*) > 1;

-- ============================================================
-- SANITY CHECK 2: SMA-20 spot check
-- Compare the view's SMA-20 against a manual calculation for
-- AAPL on the most recent date. Both values should match.
-- ============================================================
WITH manual_sma AS (
    SELECT
        symbol,
        trade_date,
        close,
        AVG(close) OVER (
            ORDER BY trade_date
            ROWS BETWEEN 19 PRECEDING AND CURRENT ROW
        ) AS manual_sma_20
    FROM prices
    WHERE symbol = 'AAPL'
)
SELECT
    m.symbol,
    m.trade_date,
    m.close,
    m.manual_sma_20,
    v.sma_20 AS view_sma_20,
    ABS(m.manual_sma_20 - v.sma_20) AS diff
FROM manual_sma m
JOIN v_moving_averages v
    ON m.symbol = v.symbol AND m.trade_date = v.trade_date
ORDER BY m.trade_date DESC
LIMIT 10;

-- ============================================================
-- SANITY CHECK 3: Gap-filled series has zero NULL closes
-- Expected: 0 rows
-- ============================================================
SELECT symbol, cal_date
FROM v_calendar_gapfill
WHERE close_filled IS NULL;

-- ============================================================
-- SANITY CHECK 4: Data completeness per symbol
-- ============================================================
SELECT
    symbol,
    MIN(trade_date) AS first_date,
    MAX(trade_date) AS last_date,
    COUNT(*)        AS total_rows,
    MAX(trade_date) - MIN(trade_date) AS calendar_span_days
FROM prices
GROUP BY symbol
ORDER BY symbol;

-- ============================================================
-- SANITY CHECK 5: Drawdown should always be <= 0
-- Expected: 0 rows
-- ============================================================
SELECT symbol, trade_date, drawdown_pct
FROM v_drawdowns
WHERE drawdown_pct > 0.0001;

-- ============================================================
-- SANITY CHECK 6: Bollinger upper band >= lower band always
-- Expected: 0 rows
-- ============================================================
SELECT symbol, trade_date, upper_band, lower_band
FROM v_bollinger_bands
WHERE upper_band < lower_band;
