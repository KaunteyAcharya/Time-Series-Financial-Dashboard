-- Calendar gap-fill: generate a continuous date series per symbol, then
-- LEFT JOIN prices and forward-fill NULLs with the last known close.
-- Useful for aligning equity (weekday-only) with crypto (daily) series.
CREATE OR REPLACE VIEW v_calendar_gapfill AS
WITH date_bounds AS (
    SELECT
        symbol,
        MIN(trade_date) AS first_date,
        MAX(trade_date) AS last_date
    FROM prices
    GROUP BY symbol
),
calendar AS (
    SELECT
        db.symbol,
        d::date AS cal_date
    FROM date_bounds db
    CROSS JOIN LATERAL generate_series(
        db.first_date, db.last_date, INTERVAL '1 day'
    ) AS d
),
joined AS (
    SELECT
        c.symbol,
        c.cal_date,
        p.close,
        p.volume,
        p.open,
        p.high,
        p.low,
        COUNT(p.close) OVER (
            PARTITION BY c.symbol ORDER BY c.cal_date
        ) AS grp
    FROM calendar c
    LEFT JOIN prices p
        ON c.symbol = p.symbol AND c.cal_date = p.trade_date
)
SELECT
    symbol,
    cal_date,
    FIRST_VALUE(close)  OVER w AS close_filled,
    FIRST_VALUE(open)   OVER w AS open_filled,
    FIRST_VALUE(high)   OVER w AS high_filled,
    FIRST_VALUE(low)    OVER w AS low_filled,
    FIRST_VALUE(volume) OVER w AS volume_filled,
    CASE WHEN close IS NULL THEN TRUE ELSE FALSE END AS is_filled
FROM joined
WINDOW w AS (
    PARTITION BY symbol, grp ORDER BY cal_date
    ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
);
