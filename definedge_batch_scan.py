import streamlit as st
import pandas as pd
import numpy as np
import requests
import io
from datetime import datetime, timedelta
import plotly.graph_objs as go

# --- Helper functions copied from your working code ---

@st.cache_data
def load_master():
    df = pd.read_csv("master.csv", sep="\t", header=None)
    df.columns = [
        "segment", "token", "symbol", "instrument", "series", "isin1",
        "facevalue", "lot", "something", "zero1", "two1", "one1", "isin", "one2"
    ]
    return df[["segment", "token", "symbol", "instrument"]]

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
    for col in ["Open", "High", "Low", "Close", "Volume"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df

def compute_ema(series, period):
    return series.ewm(span=period, adjust=False).mean()

def count_updays(df, window=15):
    highs = df["High"].values
    count = 0
    for i in range(-window, 0):
        if i - 1 < -len(highs):
            continue
        if highs[i] > highs[i-1]:
            count += 1
    return count

def count_downdays(df, window=15):
    lows = df["Low"].values
    count = 0
    for i in range(-window, 0):
        if i - 1 < -len(lows):
            continue
        if lows[i] < lows[i-1]:
            count += 1
    return count

def get_time_range(days, endtime="1530"):
    to = datetime.now()
    to = to.replace(hour=int(endtime[:2]), minute=int(endtime[2:]), second=0, microsecond=0)
    frm = to - timedelta(days=days)
    return frm.strftime("%d%m%Y%H%M"), to.strftime("%d%m%Y%H%M")

# --- Main scan and plotting functions as previously given ---

def scan_symbols(master_df, api_key, updown_window=15, days=120, ema_ltp_thr=0.95, ema_ratio_thr=0.95):
    result = []
    for idx, row in master_df.iterrows():
        segment, token, symbol, instrument = row['segment'], row['token'], row['symbol'], row['instrument']
        try:
            from_dt, to_dt = get_time_range(days)
            df = fetch_candles_definedge(segment, token, "day", from_dt, to_dt, api_key)
            if len(df) < 20:
                continue
            df["EMA20"] = compute_ema(df["Close"], 20)
            df["EMA50"] = compute_ema(df["Close"], 50)
            ltp = df["Close"].iloc[-1]
            ema20 = df["EMA20"].iloc[-1]
            ema50 = df["EMA50"].iloc[-1]
            updays = count_updays(df, updown_window)
            downdays = count_downdays(df, updown_window)
            ema20_ltp = ema20 / ltp if ltp else np.nan
            ema50_ema20 = ema50 / ema20 if ema20 else np.nan

            if (
                (updays > downdays) and
                (ema20_ltp > ema_ltp_thr) and
                (ema50_ema20 > ema_ratio_thr)
            ):
                result.append({
                    "Symbol": symbol,
                    "Updays": updays,
                    "Downdays": downdays,
                    "20EMA/LTP": round(ema20_ltp, 4),
                    "50EMA/20EMA": round(ema50_ema20, 4),
                    "LTP": ltp,
                    "segment": segment,
                    "token": token
                })
        except Exception:
            continue
    return pd.DataFrame(result)

def plot_candlestick(df):
    fig = go.Figure(data=[go.Candlestick(
        x=df['Date'],
        open=df['Open'],
        high=df['High'],
        low=df['Low'],
        close=df['Close'],
        name='Candlestick'
    )])
    fig.update_layout(xaxis_rangeslider_visible=False)
    return fig

def show():
    st.header("Definedge Batch Symbol Scanner")

    api_key = st.secrets.get("integrate_api_session_key", "")
    master_df = load_master()

    st.sidebar.title("Scan filters")
    ema_ltp_thr = st.sidebar.number_input("20EMA / LTP threshold", min_value=0.8, max_value=1.5, value=0.95, step=0.01)
    ema_ratio_thr = st.sidebar.number_input("50EMA / 20EMA threshold", min_value=0.8, max_value=1.5, value=0.95, step=0.01)
    updown_window = st.sidebar.number_input("Updays/Downdays Window (days)", min_value=5, max_value=40, value=15, step=1)
    days = st.sidebar.number_input("Lookback Days", min_value=50, max_value=600, value=120, step=10)

    if st.button("Run Symbol Scan"):
        st.info("Scanning symbols, please wait...")
        scan_df = scan_symbols(master_df, api_key, updown_window, days, ema_ltp_thr, ema_ratio_thr)
        if scan_df.empty:
            st.warning("No symbols matched the criteria.")
            return
        st.dataframe(scan_df)
        symbol_sel = st.selectbox("See candlestick for symbol:", scan_df["Symbol"])
        row = scan_df[scan_df["Symbol"] == symbol_sel].iloc[0]
        segment, token = row["segment"], row["token"]
        from_dt, to_dt = get_time_range(days)
        df = fetch_candles_definedge(segment, token, "day", from_dt, to_dt, api_key)
        st.plotly_chart(plot_candlestick(df), use_container_width=True)

    st.info("Adjust the filters and click 'Run Symbol Scan' to find matching symbols and visualize price action.")
