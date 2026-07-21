-- Bollinger Bands: SMA-20 +/- 2 standard deviations of close price.
CREATE OR REPLACE VIEW v_bollinger_bands AS
SELECT
    symbol,
    trade_date,
    close,
    AVG(close) OVER w                          AS sma_20,
    STDDEV(close) OVER w                       AS stddev_20,
    AVG(close) OVER w + 2 * STDDEV(close) OVER w AS upper_band,
    AVG(close) OVER w - 2 * STDDEV(close) OVER w AS lower_band,
    CASE
        WHEN close > AVG(close) OVER w + 2 * STDDEV(close) OVER w THEN 'overbought'
        WHEN close < AVG(close) OVER w - 2 * STDDEV(close) OVER w THEN 'oversold'
        ELSE 'neutral'
    END AS bb_signal,
    (close - (AVG(close) OVER w - 2 * STDDEV(close) OVER w))
        / NULLIF(
            (AVG(close) OVER w + 2 * STDDEV(close) OVER w)
            - (AVG(close) OVER w - 2 * STDDEV(close) OVER w),
            0
        ) AS pct_b
FROM prices
WINDOW w AS (
    PARTITION BY symbol ORDER BY trade_date
    ROWS BETWEEN 19 PRECEDING AND CURRENT ROW
);
