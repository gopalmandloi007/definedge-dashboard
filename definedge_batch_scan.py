import streamlit as st
import pandas as pd
import numpy as np
import requests
import io
from datetime import datetime, timedelta
import plotly.graph_objs as go

from master_loader import load_watchlist

WATCHLIST_FILES = [
    "master.csv",
    "watchlist_1.csv",
    "watchlist_2.csv",
    "watchlist_3.csv",
    "watchlist_5.csv",
    "watchlist_6.csv",
    "watchlist_7.csv",
]

NIFTY500_SYMBOL = "nifty 500"

def fetch_candles_definedge(segment, token, timeframe, from_dt, to_dt, api_key):
    url = f"https://data.definedgesecurities.com/sds/history/{segment}/{token}/{timeframe}/{from_dt}/{to_dt}"
    headers = {"Authorization": api_key}
    resp = requests.get(url, headers=headers)
    if resp.status_code != 200:
        raise Exception(f"API error: {resp.status_code} {resp.text}")
    cols = ["Dateandtime", "Open", "High", "Low", "Close", "Volume", "OI"]
    df = pd.read_csv(io.StringIO(resp.text), header=None, names=cols)
    df = df[df["Dateandtime"].notnull()]
    df = df[df["Dateandtime"].astype(str).str.strip() != ""]
    df["Date"] = pd.to_datetime(df["Dateandtime"], format="%d%m%Y%H%M", errors="coerce")
    df = df.dropna(subset=["Date"])
    df = df[df['Date'] <= pd.Timestamp.today()]
    for col in ["Open", "High", "Low", "Close", "Volume"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df

def get_nifty500_row(master_df):
    for idx, row in master_df.iterrows():
        symbol = str(row.get('symbol', '')).strip().lower()
        if symbol == NIFTY500_SYMBOL:
            return row
    return None

# ... rest of your code unchanged ...

def show():
    st.header("Definedge Batch Symbol Scanner")

    api_key = st.secrets.get("integrate_api_session_key", "")
    if not api_key:
        st.error("API key not found in Streamlit secrets! Please add integrate_api_session_key.")
        return

    st.sidebar.title("Watchlist & Scan filters")
    selected_watchlist = st.sidebar.selectbox("Select Watchlist CSV", WATCHLIST_FILES)

    # Always load master.csv for Nifty 500 (for RS and chart)
    try:
        master_for_nifty = load_watchlist("master.csv")
    except Exception as e:
        st.error(f"Error loading master.csv for Nifty 500: {e}")
        return

    # Load selected watchlist for scanning
    try:
        master_df = load_watchlist(selected_watchlist)
    except Exception as e:
        st.error(f"Error loading {selected_watchlist}: {e}")
        return

    # ... (sidebar controls unchanged) ...

    # --- Fetch Nifty 500 data ONCE robustly, always from master.csv ---
    nifty500_row = get_nifty500_row(master_for_nifty)
    nifty_df = None
    nifty500_error = ""
    if nifty500_row is not None:
        nseg, ntok = nifty500_row['segment'], nifty500_row['token']
        from_dt, to_dt = get_time_range(days)
        try:
            nifty_df = fetch_candles_definedge(nseg, ntok, "day", from_dt, to_dt, api_key)
            if nifty_df.empty:
                nifty500_error = "Nifty 500 candle data empty."
        except Exception as e:
            nifty500_error = str(e)
    else:
        nifty500_error = "'Nifty 500' symbol not found in master.csv."

    if st.button("Run Symbol Scan"):
        st.info("Scanning symbols, please wait...")
        scan_df = scan_symbols(
            master_df, api_key, updown_window, days, ema_ltp_thr, ema_ratio_thr,
            rsi_enabled, rsi_threshold, rsi_direction,
            ema_scan_enabled, ema_condition, show_rs,
            nifty_df=nifty_df
        )
        if scan_df.empty:
            st.warning("No symbols matched the criteria.")
            return
        st.dataframe(scan_df)

        cols = st.columns(2)
        with cols[0]:
            st.subheader("Nifty 500 Chart")
            if nifty_df is not None and not nifty_df.empty:
                st.plotly_chart(plot_candlestick(nifty_df), use_container_width=True)
            else:
                st.warning(f"Nifty 500 chart data not available. {nifty500_error}")

        with cols[1]:
            symbol_sel = st.selectbox("See candlestick for symbol:", scan_df["Symbol"])
            row = scan_df[scan_df["Symbol"] == symbol_sel].iloc[0]
            segment, token = row["segment"], row["token"]
            from_dt, to_dt = get_time_range(days)
            try:
                df = fetch_candles_definedge(segment, token, "day", from_dt, to_dt, api_key)
                st.subheader(f"{symbol_sel} Chart")
                st.plotly_chart(plot_candlestick(df), use_container_width=True)
            except Exception as e:
                st.error(f"Error fetching candle data: {e}")

    st.info("Select watchlist and filters, then click 'Run Symbol Scan' to find matching symbols and visualize price action.")

if __name__ == "__main__":
    show()
