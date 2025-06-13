import streamlit as st
import pandas as pd
import numpy as np
import requests
import io
from datetime import datetime, timedelta
import plotly.graph_objs as go

@st.cache_data
def load_master():
    df = pd.read_csv("master.csv", sep="\t", header=None)
    df.columns = [
        "segment", "token", "symbol", "instrument", "series", "isin1",
        "facevalue", "lot", "something", "zero1", "two1", "one1", "isin", "one2"
    ]
    return df[["segment", "token", "symbol", "instrument"]]

def get_token(symbol, segment, master_df):
    symbol = symbol.strip().upper()
    segment = segment.strip().upper()
    row = master_df[(master_df['symbol'] == symbol) & (master_df['segment'] == segment)]
    if not row.empty:
        return row.iloc[0]['token']
    row2 = master_df[(master_df['instrument'] == symbol) & (master_df['segment'] == segment)]
    if not row2.empty:
        return row2.iloc[0]['token']
    return None

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
    try:
        to = to.replace(hour=int(endtime[:2]), minute=int(endtime[2:]), second=0, microsecond=0)
    except Exception:
        pass
    frm = to - timedelta(days=days)
    return frm.strftime("%d%m%Y%H%M"), to.strftime("%d%m%Y%H%M")

def display_metric(label, value):
    st.metric(label, "N/A" if pd.isna(value) else f"{value:.2f}")

def plot_candlestick(df, ema20=None, ema50=None, ema200=None, title="Daily Candlestick Chart"):
    fig = go.Figure()
    fig.add_trace(go.Candlestick(
        x=df['Date'],
        open=df['Open'],
        high=df['High'],
        low=df['Low'],
        close=df['Close'],
        name='Candlestick'
    ))
    if ema20 is not None:
        fig.add_trace(go.Scatter(
            x=df['Date'], y=ema20,
            mode='lines', name='EMA 20',
            line=dict(width=1, color='blue')
        ))
    if ema50 is not None:
        fig.add_trace(go.Scatter(
            x=df['Date'], y=ema50,
            mode='lines', name='EMA 50',
            line=dict(width=1, color='orange')
        ))
    if ema200 is not None:
        fig.add_trace(go.Scatter(
            x=df['Date'], y=ema200,
            mode='lines', name='EMA 200',
            line=dict(width=1, color='green')
        ))
    fig.update_layout(
        xaxis_rangeslider_visible=False,
        title=title,
        height=500,
        margin=dict(l=10, r=10, t=30, b=10)
    )
    return fig

def plot_rsi(df, title="RSI"):
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df['Date'], y=df['RSI'],
        mode='lines', name='RSI',
        line=dict(width=1.5, color='purple')
    ))
    fig.add_hline(y=70, line=dict(dash='dash', color='red'), annotation_text="Overbought", annotation_position="top right")
    fig.add_hline(y=30, line=dict(dash='dash', color='green'), annotation_text="Oversold", annotation_position="bottom right")
    fig.update_layout(
        title=title,
        height=250,
        yaxis=dict(range=[0, 100]),
        margin=dict(l=10, r=10, t=30, b=10)
    )
    return fig

def show():
    st.header("Symbol Technical Details (Definedge)")

    api_key = st.secrets.get("integrate_api_session_key", "")
    if not api_key:
        st.error("API key not found. Please add integrate_api_session_key in Streamlit secrets.")
        return

    try:
        master_df = load_master()
    except Exception as e:
        st.error(f"Error loading master.csv: {e}")
        return

    col1, col2, col3 = st.columns(3)
    with col1:
        segment = st.selectbox("Segment", sorted(master_df["segment"].str.upper().unique()), index=0)
    with col2:
        symbol = st.text_input("Symbol (e.g. RELIANCE-EQ)", value="RELIANCE-EQ").strip().upper()
    with col3:
        st.caption("EMAs/RSI are for daily timeframe.")

    token = get_token(symbol, segment, master_df)
    if not token:
        st.warning("Symbol-token mapping not found in master file. Try exact symbol or instrument code.")
        return

    try:
        from_dt, to_dt = get_time_range(420)
        daily = fetch_candles_definedge(segment, token, "day", from_dt, to_dt, api_key)
        week_df = daily.copy().set_index("Date").resample("W").agg({"Open":"first","High":"max","Low":"min","Close":"last","Volume":"sum"}).dropna().reset_index()
        month_df = daily.copy().set_index("Date").resample("M").agg({"Open":"first","High":"max","Low":"min","Close":"last","Volume":"sum"}).dropna().reset_index()
    except Exception as e:
        st.error(f"Error fetching candles: {e}")
        return

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

    rsi_daily = daily["RSI"].dropna().iloc[-1] if daily["RSI"].notna().any() else np.nan
    rsi_weekly = week_df["RSI"].dropna().iloc[-1] if week_df["RSI"].notna().any() else np.nan
    rsi_monthly = month_df["RSI"].dropna().iloc[-1] if month_df["RSI"].notna().any() else np.nan

    ema20_ltp = ema20 / ltp if ltp else np.nan
    ema50_ema20 = ema50 / ema20 if ema20 else np.nan
    updays = count_updays(daily, 15)
    downdays = count_downdays(daily, 15)

    colm = st.columns(3)
    with colm[0]:
        display_metric("Monthly RSI", rsi_monthly)
        st.metric("LTP", f"{ltp:.2f}")
        st.metric("20 EMA", f"{ema20:.2f}")
        st.metric("Updays (15d)", updays)
    with colm[1]:
        display_metric("Weekly RSI", rsi_weekly)
        st.metric("50 EMA", f"{ema50:.2f}")
        st.metric("50 EMA / 20 EMA", f"{ema50_ema20:.4f}")
        st.metric("Downdays (15d)", downdays)
    with colm[2]:
        display_metric("Daily RSI", rsi_daily)
        st.metric("200 EMA", f"{ema200:.2f}")
        st.metric("20 EMA / LTP", f"{ema20_ltp:.4f}")

    st.markdown("#### Daily Candlestick Chart")
    st.plotly_chart(
        plot_candlestick(
            daily.tail(60),
            ema20=daily["EMA20"].tail(60),
            ema50=daily["EMA50"].tail(60),
            ema200=daily["EMA200"].tail(60)
        ),
        use_container_width=True
    )

    st.markdown("#### Daily RSI Chart")
    st.plotly_chart(plot_rsi(daily.tail(90)), use_container_width=True)

    st.markdown("#### Recent Daily Candles")
    st.dataframe(daily.tail(15)[["Date", "Open", "High", "Low", "Close", "EMA20", "EMA50", "EMA200", "RSI"]])

    st.info("All data is fetched from Definedge Historical Data API using your master file.")

    # Optionally: CSV Download
    csv = daily.to_csv(index=False)
    st.download_button("Download Daily Data as CSV", csv, "daily_data.csv")
