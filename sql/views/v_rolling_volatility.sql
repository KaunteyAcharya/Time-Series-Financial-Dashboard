-- 20-day rolling volatility of log returns, annualized (sqrt(252)).
-- Uses a CTE to compute log returns first, then STDDEV over 20-row window.
CREATE OR REPLACE VIEW v_rolling_volatility AS
WITH daily AS (
    SELECT
        symbol,
        trade_date,
        close,
        LN(close / LAG(close) OVER (
            PARTITION BY symbol ORDER BY trade_date
        )) AS log_return
    FROM prices
)
SELECT
    symbol,
    trade_date,
    close,
    log_return,
    STDDEV(log_return) OVER (
        PARTITION BY symbol ORDER BY trade_date
        ROWS BETWEEN 19 PRECEDING AND CURRENT ROW
    ) AS vol_20d,
    STDDEV(log_return) OVER (
        PARTITION BY symbol ORDER BY trade_date
        ROWS BETWEEN 19 PRECEDING AND CURRENT ROW
    ) * SQRT(252) AS vol_20d_annualized
FROM daily;
