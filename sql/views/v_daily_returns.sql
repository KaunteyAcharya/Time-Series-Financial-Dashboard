-- Log returns: ln(close_t / close_{t-1})
-- LAG() partitioned by symbol ensures no cross-symbol contamination.
CREATE OR REPLACE VIEW v_daily_returns AS
SELECT
    symbol,
    trade_date,
    close,
    LAG(close) OVER w                          AS prev_close,
    LN(close / LAG(close) OVER w)              AS log_return,
    (close - LAG(close) OVER w)
        / LAG(close) OVER w                    AS simple_return
FROM prices
WINDOW w AS (PARTITION BY symbol ORDER BY trade_date
             ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW);
