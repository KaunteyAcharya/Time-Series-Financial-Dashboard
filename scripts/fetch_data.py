"""Fetch OHLCV history from Yahoo Finance and load into Postgres."""

import os
import time
import logging
from io import StringIO

import pandas as pd
import psycopg2
import yfinance as yf

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

DB_DSN = os.getenv(
    "DATABASE_URL",
    "dbname=timeseries user=ts_user password=ts_pass host=localhost port=5432",
)

SYMBOLS = {
    "AAPL":    ("Apple Inc.", "equity", "NASDAQ"),
    "MSFT":    ("Microsoft Corp.", "equity", "NASDAQ"),
    "GOOGL":   ("Alphabet Inc.", "equity", "NASDAQ"),
    "AMZN":    ("Amazon.com Inc.", "equity", "NASDAQ"),
    "TSLA":    ("Tesla Inc.", "equity", "NASDAQ"),
    "SPY":     ("SPDR S&P 500 ETF", "etf", "ARCA"),
    "BTC-USD": ("Bitcoin USD", "crypto", None),
    "ETH-USD": ("Ethereum USD", "crypto", None),
}

HISTORY_PERIOD = "10y"
RATE_LIMIT_SLEEP = 1.5


def get_connection():
    return psycopg2.connect(DB_DSN)


def upsert_symbol(cur, symbol, name, asset_type, exchange):
    cur.execute(
        """
        INSERT INTO symbols (symbol, name, asset_type, exchange)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (symbol) DO UPDATE
            SET name = EXCLUDED.name,
                asset_type = EXCLUDED.asset_type,
                exchange = EXCLUDED.exchange
        """,
        (symbol, name, asset_type, exchange),
    )


def load_prices(cur, symbol: str, df: pd.DataFrame) -> int:
    if df.empty:
        log.warning("No data for %s, skipping", symbol)
        return 0

    df = df.copy()
    df.columns = [c.lower().replace(" ", "_") for c in df.columns]

    if "adj_close" not in df.columns and "adj close" in df.columns:
        df.rename(columns={"adj close": "adj_close"}, inplace=True)
    if "adj_close" not in df.columns:
        df["adj_close"] = df["close"]

    df = df.dropna(subset=["open", "high", "low", "close"])
    df = df[df["high"] >= df["low"]]
    df = df[df["close"] > 0]

    buf = StringIO()
    for date_val, row in df.iterrows():
        trade_date = pd.Timestamp(date_val).strftime("%Y-%m-%d")
        line = "\t".join([
            symbol,
            trade_date,
            f"{row['open']:.6f}",
            f"{row['high']:.6f}",
            f"{row['low']:.6f}",
            f"{row['close']:.6f}",
            f"{row['adj_close']:.6f}",
            str(int(row.get("volume", 0))),
        ])
        buf.write(line + "\n")

    buf.seek(0)

    tmp_table = f"tmp_prices_{symbol.replace('-', '_').lower()}"
    cur.execute(f"""
        CREATE TEMP TABLE {tmp_table} (LIKE prices INCLUDING DEFAULTS)
        ON COMMIT DROP
    """)
    cur.copy_from(buf, tmp_table, columns=[
        "symbol", "trade_date", "open", "high", "low", "close", "adj_close", "volume"
    ])
    cur.execute(f"""
        INSERT INTO prices (symbol, trade_date, open, high, low, close, adj_close, volume)
        SELECT symbol, trade_date, open, high, low, close, adj_close, volume
        FROM {tmp_table}
        ON CONFLICT (symbol, trade_date) DO UPDATE
            SET open      = EXCLUDED.open,
                high      = EXCLUDED.high,
                low       = EXCLUDED.low,
                close     = EXCLUDED.close,
                adj_close = EXCLUDED.adj_close,
                volume    = EXCLUDED.volume
    """)
    return cur.rowcount


def validate_counts(cur, symbol: str, asset_type: str):
    cur.execute("SELECT COUNT(*) FROM prices WHERE symbol = %s", (symbol,))
    actual = cur.fetchone()[0]
    days_per_year = 365 if asset_type == "crypto" else 250
    years = int(HISTORY_PERIOD.replace("y", ""))
    expected_min = int(days_per_year * years * 0.8)

    if actual < expected_min:
        log.warning("%s: %d rows (expected >= %d)", symbol, actual, expected_min)
    else:
        log.info("%s: %d rows loaded", symbol, actual)
    return actual


def main():
    conn = get_connection()
    conn.autocommit = False

    for symbol, (name, asset_type, exchange) in SYMBOLS.items():
        log.info("Fetching %s (%s)...", symbol, name)
        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(period=HISTORY_PERIOD, auto_adjust=False)
        except Exception as e:
            log.error("Failed to fetch %s: %s", symbol, e)
            continue

        try:
            with conn:
                cur = conn.cursor()
                upsert_symbol(cur, symbol, name, asset_type, exchange)
                rows = load_prices(cur, symbol, df)
                log.info("Upserted %d rows for %s", rows, symbol)
                validate_counts(cur, symbol, asset_type)
        except Exception as e:
            log.error("DB error for %s: %s", symbol, e)
            conn.rollback()

        time.sleep(RATE_LIMIT_SLEEP)

    conn.close()
    log.info("Done.")


if __name__ == "__main__":
    main()
