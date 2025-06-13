import streamlit as st
import pandas as pd
import numpy as np
import requests
from datetime import datetime, timedelta

# ---- Load your master file (symbol <-> token) ----
# You should cache this for performance!
@st.cache_data
def load_master():
    # Adjust path/columns as per your master file
    # Example: columns=["token", "symbol", "segment"]
    # Place master.csv in your project folder or provide full path
    df = pd.read_csv("master.csv", dtype=str)
    df.columns = [c.lower() for c in df.columns]
    return df

def get_token(symbol, segment, master_df):
    symbol = symbol.strip().upper()
    segment = segment.strip().upper()
    row = master_df[(master_df['symbol'] == symbol) & (master_df['segment'] == segment)]
    if not row.empty:
        return row.iloc[0]['token']
    return None

def fetch_candles_definedge(segment, token, timeframe, from_dt, to_dt, api_key):
    url = f"https://data.definedgesecurities.com/sds/history/{segment}/{token}/{timeframe}/{from_dt}/{to_dt}"
    headers = {"Authorization": api_key}
    resp = requests.get(url, headers=headers)
    if resp.status_code != 200:
        raise Exception(f"API error: {resp.status_code} {resp.text}")
    # For day/minute: Dateandtime, Open, High, Low, Close, Volume, OI
    cols = ["Dateandtime", "Open", "High", "Low", "Close", "Volume", "OI"]
    df = pd.read_csv(pd.compat.StringIO(resp.text), header=None, names=cols)
    # Parse datetime
    df["Date"] = pd.to_datetime(df["Dateandtime"], format="%d-%m-%Y %H:%M")
    return df

def compute_ema(series, period):
    return series.ewm(span=period, adjust=False).mean()

def compute_rsi(series, period=14):
    delta = series.diff()
    gain = np.where(delta > 0, delta, 0)
    loss = np.where(delta < 0, -delta, 0)
    avg_gain = pd.Series(gain).rolling(window=period, min_periods=period).mean()
    avg_loss = pd.Series(loss).rolling(window=period, min_periods=period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return pd.Series(rsi, index=series.index)

def count_updays(df, window=15):
    highs = df["High"].values
    count = 0
    for i in range(-window, 0):
        if i-1 < -len(highs):
            continue
        if highs[i] > highs[i-1]:
            count += 1
    return count

def count_downdays(df, window=15):
    lows = df["Low"].values
    count = 0
    for i in range(-window, 0):
        if i-1 < -len(lows):
            continue
        if lows[i] < lows[i-1]:
            count += 1
    return count

def get_time_range(days, endtime="1530"):
    # Returns (from_dt, to_dt) in ddMMyyyyHHmm
    to = datetime.now()
    to = to.replace(hour=int(endtime[:2]), minute=int(endtime[2:]), second=0, microsecond=0)
    frm = to - timedelta(days=days)
    return frm.strftime("%d%m%Y%H%M"), to.strftime("%d%m%Y%H%M")

def show():
    st.header("Symbol Technical Details (Definedge)")

    api_key = st.secrets.get("integrate_api_session_key", "")
    master_df = load_master()

    col1, col2, col3 = st.columns(3)
    with col1:
        segment = st.selectbox("Segment", sorted(master_df["segment"].str.upper().unique()), index=0)
    with col2:
        symbol = st.text_input("Symbol (e.g. RELIANCE-EQ)", value="RELIANCE-EQ").strip().upper()
    with col3:
        default_tf = st.selectbox("Show LTP and EMAs for", ["day", "minute"], index=0)

    token = get_token(symbol, segment, master_df)
    if not token:
        st.warning("Symbol-token mapping not found in master file.")
        return

    try:
        # Daily candles: ~220 for 200 EMA + margin
        from_dt, to_dt = get_time_range(220)
        daily = fetch_candles_definedge(segment, token, "day", from_dt, to_dt, api_key)
        # Weekly/monthly RSI: use 'day' data and resample
        week_df = daily.copy().set_index("Date").resample("W").agg({"Open":"first","High":"max","Low":"min","Close":"last","Volume":"sum"}).dropna().reset_index()
        month_df = daily.copy().set_index("Date").resample("M").agg({"Open":"first","High":"max","Low":"min","Close":"last","Volume":"sum"}).dropna().reset_index()
    except Exception as e:
        st.error(f"Error fetching candles: {e}")
        return

    # --- Indicators ---
    daily["EMA20"] = compute_ema(daily["Close"], 20)
    daily["EMA50"] = compute_ema(daily["Close"], 50)
    daily["EMA200"] = compute_ema(daily["Close"], 200)
    daily["RSI"] = compute_rsi(daily["Close"], 14)
    week_df["RSI"] = compute_rsi(week_df["Close"], 14)
    month_df["RSI"] = compute_rsi(month_df["Close"], 14)

    ltp = daily["Close"].iloc[-1]
    ema20 = daily["EMA20"].iloc[-1]
    ema50 = daily["EMA50"].iloc[-1]
    ema200 = daily["EMA200"].iloc[-1]
    rsi_daily = daily["RSI"].iloc[-1]
    rsi_weekly = week_df["RSI"].iloc[-1]
    rsi_monthly = month_df["RSI"].iloc[-1]
    ema20_ltp = ema20 / ltp if ltp else np.nan
    ema50_ema20 = ema50 / ema20 if ema20 else np.nan
    updays = count_updays(daily, 15)
    downdays = count_downdays(daily, 15)

    colm = st.columns(3)
    with colm[0]:
        st.metric("Monthly RSI", f"{rsi_monthly:.2f}")
        st.metric("LTP", f"{ltp:.2f}")
        st.metric("20 EMA", f"{ema20:.2f}")
        st.metric("Updays (15d)", updays)
    with colm[1]:
        st.metric("Weekly RSI", f"{rsi_weekly:.2f}")
        st.metric("50 EMA", f"{ema50:.2f}")
        st.metric("50 EMA / 20 EMA", f"{ema50_ema20:.4f}")
        st.metric("Downdays (15d)", downdays)
    with colm[2]:
        st.metric("Daily RSI", f"{rsi_daily:.2f}")
        st.metric("200 EMA", f"{ema200:.2f}")
        st.metric("20 EMA / LTP", f"{ema20_ltp:.4f}")

    st.markdown("#### Recent Daily Candles")
    st.dataframe(daily.tail(15)[["Date", "Open", "High", "Low", "Close", "EMA20", "EMA50", "EMA200", "RSI"]])

    st.info("All data is fetched from Definedge Historical Data API using your master file.")
