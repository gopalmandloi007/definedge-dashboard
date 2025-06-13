import streamlit as st
import pandas as pd
import numpy as np

# ---- Yahan apne backend/API call lagaye ----
def fetch_candles_definedge(symbol, interval, lookback=220):
    """
    Yahan aapko apne definedge API se data fetch karna hai.
    symbol: e.g. "RELIANCE-EQ"
    interval: "D" (daily), "W" (weekly), "M" (monthly)
    return: DataFrame with columns ["Date", "Open", "High", "Low", "Close", "Volume"]
    """
    # Example stub, replace with actual API call:
    # df = pd.read_json(requests.get(...).text)
    raise NotImplementedError("fetch_candles_definedge ko apne API se connect karein.")

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

def show():
    st.header("Symbol Technical Details")

    symbol = st.text_input("Enter Symbol (e.g. RELIANCE-EQ):", value="RELIANCE-EQ")
    if not symbol:
        st.info("Please enter symbol above.")
        return

    # --- Data Fetch & Calculation ---
    try:
        with st.spinner("Fetching daily candles..."):
            df_daily = fetch_candles_definedge(symbol, "D", lookback=220)
        with st.spinner("Fetching weekly candles..."):
            df_weekly = fetch_candles_definedge(symbol, "W", lookback=60)
        with st.spinner("Fetching monthly candles..."):
            df_monthly = fetch_candles_definedge(symbol, "M", lookback=24)
    except NotImplementedError:
        st.warning("fetch_candles_definedge() ko apne Definedge API se connect karein.")
        return

    # --- Indicators ---
    df_daily["EMA20"] = compute_ema(df_daily["Close"], 20)
    df_daily["EMA50"] = compute_ema(df_daily["Close"], 50)
    df_daily["EMA200"] = compute_ema(df_daily["Close"], 200)
    df_daily["RSI"] = compute_rsi(df_daily["Close"], 14)
    df_weekly["RSI"] = compute_rsi(df_weekly["Close"], 14)
    df_monthly["RSI"] = compute_rsi(df_monthly["Close"], 14)

    # --- Latest Values ---
    ltp = df_daily["Close"].iloc[-1]
    ema20 = df_daily["EMA20"].iloc[-1]
    ema50 = df_daily["EMA50"].iloc[-1]
    ema200 = df_daily["EMA200"].iloc[-1]
    rsi_daily = df_daily["RSI"].iloc[-1]
    rsi_weekly = df_weekly["RSI"].iloc[-1]
    rsi_monthly = df_monthly["RSI"].iloc[-1]
    ema20_ltp = ema20 / ltp if ltp else np.nan
    ema50_ema20 = ema50 / ema20 if ema20 else np.nan
    updays = count_updays(df_daily, 15)
    downdays = count_downdays(df_daily, 15)

    # --- Display Panel ---
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
    st.dataframe(df_daily.tail(15)[["Date", "Open", "High", "Low", "Close", "EMA20", "EMA50", "EMA200", "RSI"]])

    st.info("Note: Yeh page aapke Definedge backend/API candles se kaam karega. fetch_candles_definedge() ko implement karein.")
