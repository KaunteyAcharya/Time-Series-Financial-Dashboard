-- SMA-20, SMA-50, SMA-200 using ROWS BETWEEN (not RANGE) so the frame
-- counts exact rows regardless of date gaps (weekends, holidays).
CREATE OR REPLACE VIEW v_moving_averages AS
SELECT
    symbol,
    trade_date,
    close,
    AVG(close) OVER (
        PARTITION BY symbol ORDER BY trade_date
        ROWS BETWEEN 19 PRECEDING AND CURRENT ROW
    ) AS sma_20,
    AVG(close) OVER (
        PARTITION BY symbol ORDER BY trade_date
        ROWS BETWEEN 49 PRECEDING AND CURRENT ROW
    ) AS sma_50,
    AVG(close) OVER (
        PARTITION BY symbol ORDER BY trade_date
        ROWS BETWEEN 199 PRECEDING AND CURRENT ROW
    ) AS sma_200,
    CASE
        WHEN AVG(close) OVER (
            PARTITION BY symbol ORDER BY trade_date
            ROWS BETWEEN 49 PRECEDING AND CURRENT ROW
        ) > AVG(close) OVER (
            PARTITION BY symbol ORDER BY trade_date
            ROWS BETWEEN 199 PRECEDING AND CURRENT ROW
        ) THEN 'golden_cross'
        ELSE 'death_cross'
    END AS ma_signal
FROM prices;
