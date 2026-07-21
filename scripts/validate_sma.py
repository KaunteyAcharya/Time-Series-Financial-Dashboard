"""Cross-validate SQL SMA-20 against pandas rolling(20).mean()."""

import os
import pandas as pd
import psycopg2

DB_DSN = os.getenv(
    "DATABASE_URL",
    "dbname=timeseries user=ts_user password=ts_pass host=localhost port=5432",
)

SYMBOL = "AAPL"
TOLERANCE = 1e-4


def main():
    conn = psycopg2.connect(DB_DSN)

    prices = pd.read_sql(
        "SELECT trade_date, close FROM prices WHERE symbol = %s ORDER BY trade_date",
        conn,
        params=(SYMBOL,),
    )
    prices["pandas_sma_20"] = prices["close"].rolling(20).mean()

    sql_sma = pd.read_sql(
        "SELECT trade_date, sma_20 FROM v_moving_averages WHERE symbol = %s ORDER BY trade_date",
        conn,
        params=(SYMBOL,),
    )

    merged = prices.merge(sql_sma, on="trade_date")
    merged = merged.dropna(subset=["pandas_sma_20", "sma_20"])
    merged["diff"] = (merged["pandas_sma_20"] - merged["sma_20"]).abs()

    max_diff = merged["diff"].max()
    mismatches = merged[merged["diff"] > TOLERANCE]

    print(f"Symbol: {SYMBOL}")
    print(f"Rows compared: {len(merged)}")
    print(f"Max absolute difference: {max_diff:.8f}")
    print(f"Mismatches (tolerance {TOLERANCE}): {len(mismatches)}")

    if len(mismatches) == 0:
        print("PASS: SQL SMA-20 matches pandas exactly.")
    else:
        print("FAIL: Mismatches found:")
        print(mismatches.head(10).to_string(index=False))

    conn.close()


if __name__ == "__main__":
    main()
