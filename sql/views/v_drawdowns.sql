-- Running drawdown: distance from the running all-time high per symbol.
CREATE OR REPLACE VIEW v_drawdowns AS
SELECT
    symbol,
    trade_date,
    close,
    MAX(close) OVER (
        PARTITION BY symbol ORDER BY trade_date
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS running_max,
    (close - MAX(close) OVER (
        PARTITION BY symbol ORDER BY trade_date
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    )) / MAX(close) OVER (
        PARTITION BY symbol ORDER BY trade_date
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS drawdown_pct
FROM prices;
