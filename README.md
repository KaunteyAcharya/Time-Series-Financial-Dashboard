# Time-Series Financial Dashboard

SQL-driven analytical dashboard for OHLCV financial data. Uses PostgreSQL window functions for technical indicators and Streamlit + Plotly for interactive visualization.

## Schema

```
┌──────────────────────┐       ┌──────────────────────────────────────┐
│       symbols        │       │              prices                  │
├──────────────────────┤       ├──────────────────────────────────────┤
│ symbol    PK VARCHAR │◄──────│ symbol    PK,FK VARCHAR             │
│ name      VARCHAR    │       │ trade_date PK  DATE                 │
│ asset_type VARCHAR   │       │ open           NUMERIC(18,6)        │
│ exchange   VARCHAR   │       │ high           NUMERIC(18,6)        │
│ created_at TIMESTAMPTZ│      │ low            NUMERIC(18,6)        │
└──────────────────────┘       │ close          NUMERIC(18,6)        │
                               │ adj_close      NUMERIC(18,6)        │
                               │ volume         BIGINT               │
                               ├──────────────────────────────────────┤
                               │ CHECK: high >= low                  │
                               │ CHECK: all prices > 0               │
                               │ INDEX: (symbol, trade_date DESC)    │
                               └──────────────────────────────────────┘
```

## Analytical Views

| View | Description | Key Window Function |
|------|-------------|-------------------|
| `v_daily_returns` | Log and simple daily returns | `LAG()` |
| `v_moving_averages` | SMA-20/50/200 with golden/death cross signal | `AVG() OVER ROWS BETWEEN` |
| `v_rolling_volatility` | 20-day rolling vol, annualized | `STDDEV() OVER ROWS BETWEEN` |
| `v_bollinger_bands` | Upper/lower bands, %B indicator | `AVG() + STDDEV()` window |
| `v_drawdowns` | Running max and drawdown percentage | `MAX() OVER UNBOUNDED PRECEDING` |
| `v_calendar_gapfill` | Continuous calendar with forward-fill | `generate_series` + `FIRST_VALUE()` |

## Quick Start

### 1. Start Postgres

```bash
docker-compose up -d
```

### 2. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 3. Create views

```bash
psql -h localhost -U ts_user -d timeseries -f sql/views/apply_views.sql
```

### 4. Fetch data

```bash
python scripts/fetch_data.py
```

### 5. Run validation

```bash
psql -h localhost -U ts_user -d timeseries -f sql/queries/sanity_checks.sql
python scripts/validate_sma.py
```

### 6. Launch dashboard

```bash
streamlit run scripts/dashboard.py
```

### 7. (Optional) Create materialized views for performance

```bash
psql -h localhost -U ts_user -d timeseries -f sql/queries/benchmark.sql
```

Refresh after each data load:

```bash
psql -h localhost -U ts_user -d timeseries -f sql/queries/refresh_materialized.sql
```

## Symbols Included

| Symbol | Name | Type |
|--------|------|------|
| AAPL | Apple Inc. | Equity |
| MSFT | Microsoft Corp. | Equity |
| GOOGL | Alphabet Inc. | Equity |
| AMZN | Amazon.com Inc. | Equity |
| TSLA | Tesla Inc. | Equity |
| SPY | SPDR S&P 500 ETF | ETF |
| BTC-USD | Bitcoin USD | Crypto |
| ETH-USD | Ethereum USD | Crypto |

## Project Structure

```
├── docker-compose.yml
├── requirements.txt
├── sql/
│   ├── schema/
│   │   └── 001_create_tables.sql
│   ├── views/
│   │   ├── apply_views.sql
│   │   ├── v_daily_returns.sql
│   │   ├── v_moving_averages.sql
│   │   ├── v_rolling_volatility.sql
│   │   ├── v_bollinger_bands.sql
│   │   ├── v_drawdowns.sql
│   │   └── v_calendar_gapfill.sql
│   └── queries/
│       ├── sanity_checks.sql
│       ├── benchmark.sql
│       └── refresh_materialized.sql
├── scripts/
│   ├── fetch_data.py
│   ├── validate_sma.py
│   └── dashboard.py
└── docs/
```
