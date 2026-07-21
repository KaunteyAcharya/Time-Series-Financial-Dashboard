-- Refresh strategy: run after each data ingestion.
-- CONCURRENTLY allows reads during refresh (requires unique index).
REFRESH MATERIALIZED VIEW CONCURRENTLY mv_rolling_volatility;
REFRESH MATERIALIZED VIEW CONCURRENTLY mv_moving_averages;
REFRESH MATERIALIZED VIEW CONCURRENTLY mv_bollinger_bands;
