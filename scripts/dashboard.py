"""Streamlit dashboard querying Postgres analytical views."""

import os
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from sqlalchemy import create_engine

DB_URL = os.getenv(
    "DATABASE_URL_ALCHEMY",
    "postgresql://ts_user:ts_pass@localhost:5432/timeseries",
)

engine = create_engine(DB_URL)

st.set_page_config(page_title="Time-Series Financial Dashboard", layout="wide")
st.title("Time-Series Financial Dashboard")


@st.cache_data(ttl=300)
def get_symbols():
    return pd.read_sql("SELECT symbol, name, asset_type FROM symbols ORDER BY symbol", engine)


@st.cache_data(ttl=300)
def query_view(view: str, symbol: str, start: str, end: str) -> pd.DataFrame:
    date_col = "cal_date" if "gapfill" in view else "trade_date"
    df = pd.read_sql(
        f"SELECT * FROM {view} WHERE symbol = %(sym)s AND {date_col} BETWEEN %(s)s AND %(e)s ORDER BY {date_col}",
        engine,
        params={"sym": symbol, "s": start, "e": end},
    )
    if date_col in df.columns:
        df[date_col] = pd.to_datetime(df[date_col])
    return df


symbols_df = get_symbols()
if symbols_df.empty:
    st.warning("No symbols found. Run `python scripts/fetch_data.py` first.")
    st.stop()

col1, col2, col3 = st.columns([2, 2, 2])
with col1:
    symbol = st.selectbox("Symbol", symbols_df["symbol"].tolist())
with col2:
    start_date = st.date_input("Start date", value=pd.Timestamp.now() - pd.DateOffset(years=2))
with col3:
    end_date = st.date_input("End date", value=pd.Timestamp.now())

start_str = str(start_date)
end_str = str(end_date)

tab_price, tab_bb, tab_vol, tab_dd, tab_returns = st.tabs([
    "Price & Moving Averages", "Bollinger Bands", "Volatility", "Drawdowns", "Returns"
])

# --- Tab 1: Price + Moving Averages ---
with tab_price:
    ma = query_view("v_moving_averages", symbol, start_str, end_str)
    if ma.empty:
        st.info("No data for selected range.")
    else:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=ma["trade_date"], y=ma["close"], name="Close", line=dict(color="#636EFA")))
        fig.add_trace(go.Scatter(x=ma["trade_date"], y=ma["sma_20"], name="SMA 20", line=dict(dash="dot")))
        fig.add_trace(go.Scatter(x=ma["trade_date"], y=ma["sma_50"], name="SMA 50", line=dict(dash="dash")))
        fig.add_trace(go.Scatter(x=ma["trade_date"], y=ma["sma_200"], name="SMA 200", line=dict(dash="longdash")))
        fig.update_layout(title=f"{symbol} — Price & Moving Averages", xaxis_title="Date", yaxis_title="Price", height=500)
        st.plotly_chart(fig, use_container_width=True)

        golden = ma[ma["ma_signal"] == "golden_cross"].iloc[-1:] if "golden_cross" in ma["ma_signal"].values else pd.DataFrame()
        if not golden.empty:
            st.success(f"Current signal: Golden Cross (SMA-50 > SMA-200) as of {golden.iloc[0]['trade_date'].date()}")
        else:
            st.warning("Current signal: Death Cross (SMA-50 < SMA-200)")

# --- Tab 2: Bollinger Bands ---
with tab_bb:
    bb = query_view("v_bollinger_bands", symbol, start_str, end_str)
    if bb.empty:
        st.info("No data for selected range.")
    else:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=bb["trade_date"], y=bb["upper_band"], name="Upper Band", line=dict(color="rgba(255,0,0,0.3)")))
        fig.add_trace(go.Scatter(x=bb["trade_date"], y=bb["lower_band"], name="Lower Band", line=dict(color="rgba(0,128,0,0.3)"), fill="tonexty", fillcolor="rgba(200,200,200,0.2)"))
        fig.add_trace(go.Scatter(x=bb["trade_date"], y=bb["sma_20"], name="SMA 20", line=dict(dash="dot", color="orange")))
        fig.add_trace(go.Scatter(x=bb["trade_date"], y=bb["close"], name="Close", line=dict(color="#636EFA")))
        fig.update_layout(title=f"{symbol} — Bollinger Bands", height=500)
        st.plotly_chart(fig, use_container_width=True)

        latest = bb.iloc[-1]
        st.metric("Latest %B", f"{latest['pct_b']:.2f}", delta=latest['bb_signal'])

# --- Tab 3: Rolling Volatility ---
with tab_vol:
    vol = query_view("v_rolling_volatility", symbol, start_str, end_str)
    if vol.empty:
        st.info("No data for selected range.")
    else:
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.08,
                            subplot_titles=("Close Price", "20-Day Annualized Volatility"))
        fig.add_trace(go.Scatter(x=vol["trade_date"], y=vol["close"], name="Close"), row=1, col=1)
        fig.add_trace(go.Scatter(x=vol["trade_date"], y=vol["vol_20d_annualized"], name="Vol (ann.)", line=dict(color="red")), row=2, col=1)
        fig.update_layout(height=600, title=f"{symbol} — Rolling Volatility")
        st.plotly_chart(fig, use_container_width=True)

        latest_vol = vol["vol_20d_annualized"].iloc[-1]
        avg_vol = vol["vol_20d_annualized"].mean()
        st.metric("Current Annualized Vol", f"{latest_vol:.2%}", delta=f"{(latest_vol - avg_vol):.2%} vs avg")

# --- Tab 4: Drawdowns ---
with tab_dd:
    dd = query_view("v_drawdowns", symbol, start_str, end_str)
    if dd.empty:
        st.info("No data for selected range.")
    else:
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.08,
                            subplot_titles=("Close vs Running Max", "Drawdown %"))
        fig.add_trace(go.Scatter(x=dd["trade_date"], y=dd["close"], name="Close"), row=1, col=1)
        fig.add_trace(go.Scatter(x=dd["trade_date"], y=dd["running_max"], name="Running Max", line=dict(dash="dot", color="green")), row=1, col=1)
        fig.add_trace(go.Scatter(x=dd["trade_date"], y=dd["drawdown_pct"], name="Drawdown", fill="tozeroy", line=dict(color="red")), row=2, col=1)
        fig.update_layout(height=600, title=f"{symbol} — Drawdowns")
        fig.update_yaxes(tickformat=".0%", row=2, col=1)
        st.plotly_chart(fig, use_container_width=True)

        max_dd = dd["drawdown_pct"].min()
        max_dd_date = dd.loc[dd["drawdown_pct"].idxmin(), "trade_date"]
        st.metric("Max Drawdown", f"{max_dd:.2%}", delta=str(max_dd_date.date()))

# --- Tab 5: Returns Distribution ---
with tab_returns:
    ret = query_view("v_daily_returns", symbol, start_str, end_str)
    ret = ret.dropna(subset=["log_return"])
    if ret.empty:
        st.info("No data for selected range.")
    else:
        col_a, col_b = st.columns(2)
        with col_a:
            fig = go.Figure(data=[go.Histogram(x=ret["log_return"], nbinsx=100, name="Log Returns")])
            fig.update_layout(title="Daily Log Return Distribution", height=400)
            st.plotly_chart(fig, use_container_width=True)
        with col_b:
            fig = go.Figure(data=[go.Scatter(x=ret["trade_date"], y=ret["log_return"].cumsum(), name="Cumulative Log Return", fill="tozeroy")])
            fig.update_layout(title="Cumulative Log Return", height=400)
            st.plotly_chart(fig, use_container_width=True)

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Mean Daily Return", f"{ret['log_return'].mean():.4%}")
        c2.metric("Std Dev", f"{ret['log_return'].std():.4%}")
        c3.metric("Skewness", f"{ret['log_return'].skew():.3f}")
        c4.metric("Kurtosis", f"{ret['log_return'].kurtosis():.3f}")
