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

NIFTY500_SYMBOL = "Nifty 500"  # Case-insensitive match

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
    up = delta.clip(lower=0)
    down = -1 * delta.clip(upper=0)
    ma_up = up.rolling(window=period, min_periods=period).mean()
    ma_down = down.rolling(window=period, min_periods=period).mean()
    rs = ma_up / (ma_down + 1e-10)
    rsi = 100 - (100 / (1 + rs))
    return rsi

def get_time_range(days, endtime="1530"):
    to = datetime.now()
    try:
        to = to.replace(hour=int(endtime[:2]), minute=int(endtime[2:]), second=0, microsecond=0)
    except Exception:
        pass
    frm = to - timedelta(days=days)
    return frm.strftime("%d%m%Y%H%M"), to.strftime("%d%m%Y%H%M")

def scan_symbols(
    master_df, api_key, updown_window=15, days=120, ema_ltp_thr=0.95, ema_ratio_thr=0.95,
    rsi_enabled=False, rsi_threshold=None, rsi_direction="Above",
    ema_scan_enabled=False, ema_condition="Price above 20EMA", show_rs=True
):
    result = []
    # Get Nifty 500 data for RS calculation if needed
    nifty_row = master_df[master_df["symbol"].str.lower() == NIFTY500_SYMBOL.lower()]
    nifty_df = None
    if show_rs and not nifty_row.empty:
        nseg, ntok = nifty_row.iloc[0][["segment", "token"]]
        from_dt, to_dt = get_time_range(days)
        try:
            nifty_df = fetch_candles_definedge(nseg, ntok, "day", from_dt, to_dt, api_key)
            if len(nifty_df) < 2:
                nifty_df = None
        except Exception:
            nifty_df = None

    for idx, row in master_df.iterrows():
        segment = row['segment']
        token = row['token']
        symbol = row['symbol']
        instrument = row['instrument']
        company = row['company'] if "company" in row else ""
        if symbol.lower() == NIFTY500_SYMBOL.lower():
            continue  # Skip Nifty 500 itself
        try:
            from_dt, to_dt = get_time_range(days)
            df = fetch_candles_definedge(segment, token, "day", from_dt, to_dt, api_key)
            if len(df) < 50:  # Need at least 50 for EMA/RSI
                continue
            df["EMA20"] = compute_ema(df["Close"], 20)
            df["EMA50"] = compute_ema(df["Close"], 50)
            df["RSI14"] = compute_rsi(df["Close"], 14)
            ltp = df["Close"].iloc[-1]
            ema20 = df["EMA20"].iloc[-1]
            ema50 = df["EMA50"].iloc[-1]
            rsi14 = df["RSI14"].iloc[-1]

            # RSI condition
            rsi_status = ""
            if rsi_enabled and rsi_threshold is not None:
                if rsi_direction == "Above" and rsi14 > rsi_threshold:
                    rsi_status = f"RSI {rsi14:.1f} > {rsi_threshold}"
                elif rsi_direction == "Below" and rsi14 < rsi_threshold:
                    rsi_status = f"RSI {rsi14:.1f} < {rsi_threshold}"
                else:
                    continue  # Skip if not matching

            # EMA scan
            ema_status = ""
            if ema_scan_enabled:
                if ema_condition == "Price above 20EMA" and ltp > ema20:
                    ema_status = "LTP > 20EMA"
                elif ema_condition == "Price below 20EMA" and ltp < ema20:
                    ema_status = "LTP < 20EMA"
                elif ema_condition == "20EMA above 50EMA" and ema20 > ema50:
                    ema_status = "20EMA > 50EMA"
                elif ema_condition == "20EMA below 50EMA" and ema20 < ema50:
                    ema_status = "20EMA < 50EMA"
                else:
                    continue  # Skip if not matching

            # Relative Strength (RS) vs Nifty 500 (robust version)
            rs_score, rs_flag = np.nan, ""
            if show_rs and nifty_df is not None:
                merged = pd.merge(
                    df[["Date", "Close"]],
                    nifty_df[["Date", "Close"]].rename(columns={"Close": "NiftyClose"}),
                    on="Date",
                    how="inner"
                )
                if len(merged) >= 2:
                    stock_return = merged["Close"].iloc[-1] / merged["Close"].iloc[0]
                    nifty_return = merged["NiftyClose"].iloc[-1] / merged["NiftyClose"].iloc[0]
                    if nifty_return != 0:
                        rs_score = stock_return / nifty_return
                        rs_flag = "Outperform" if rs_score > 1 else "Underperform"

            # Main scan logic
            ema20_ltp = ema20 / ltp if ltp else np.nan
            ema50_ema20 = ema50 / ema20 if ema20 else np.nan
            if (
                (ema20_ltp > ema_ltp_thr) and
                (ema50_ema20 > ema_ratio_thr)
            ):
                result.append({
                    "Symbol": symbol,
                    "Company": company,
                    "LTP": ltp,
                    "20EMA": round(ema20, 2),
                    "50EMA": round(ema50, 2),
                    "RSI14": round(rsi14, 2),
                    "RS_Score": round(rs_score, 3) if show_rs and not np.isnan(rs_score) else "",
                    "RS_Flag": rs_flag if show_rs else "",
                    "EMA_Scan": ema_status,
                    "RSI_Scan": rsi_status,
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
    if not api_key:
        st.error("API key not found in Streamlit secrets! Please add integrate_api_session_key.")
        return

    st.sidebar.title("Watchlist & Scan filters")
    selected_watchlist = st.sidebar.selectbox("Select Watchlist CSV", WATCHLIST_FILES)
    try:
        master_df = load_watchlist(selected_watchlist)
    except Exception as e:
        st.error(f"Error loading {selected_watchlist}: {e}")
        return

    ema_ltp_thr = st.sidebar.number_input("20EMA / LTP threshold", min_value=0.8, max_value=1.5, value=0.95, step=0.01)
    ema_ratio_thr = st.sidebar.number_input("50EMA / 20EMA threshold", min_value=0.8, max_value=1.5, value=0.95, step=0.01)
    updown_window = st.sidebar.number_input("Updays/Downdays Window (days)", min_value=5, max_value=40, value=15, step=1)
    days = st.sidebar.number_input("Lookback Days", min_value=50, max_value=600, value=120, step=10)

    st.sidebar.markdown("---")
    st.sidebar.subheader("RSI Scanner")
    rsi_enabled = st.sidebar.checkbox("Enable RSI Scan", value=False)
    rsi_threshold = None
    rsi_direction = "Above"
    if rsi_enabled:
        rsi_threshold = st.sidebar.number_input("RSI threshold", min_value=0, max_value=100, value=60)
        rsi_direction = st.sidebar.selectbox("RSI Condition", ["Above", "Below"])

    st.sidebar.markdown("---")
    st.sidebar.subheader("EMA Scanner")
    ema_scan_enabled = st.sidebar.checkbox("Enable EMA Scan", value=False)
    ema_condition = "Price above 20EMA"
    if ema_scan_enabled:
        ema_condition = st.sidebar.selectbox("EMA Condition", [
            "Price above 20EMA",
            "Price below 20EMA",
            "20EMA above 50EMA",
            "20EMA below 50EMA"
        ])

    st.sidebar.markdown("---")
    show_rs = st.sidebar.checkbox("Show Relative Strength vs Nifty 500", value=True)

    if st.button("Run Symbol Scan"):
        st.info("Scanning symbols, please wait...")
        scan_df = scan_symbols(
            master_df, api_key, updown_window, days, ema_ltp_thr, ema_ratio_thr,
            rsi_enabled, rsi_threshold, rsi_direction,
            ema_scan_enabled, ema_condition, show_rs
        )
        if scan_df.empty:
            st.warning("No symbols matched the criteria.")
            return
        st.dataframe(scan_df)
        symbol_sel = st.selectbox("See candlestick for symbol:", scan_df["Symbol"])
        row = scan_df[scan_df["Symbol"] == symbol_sel].iloc[0]
        segment, token = row["segment"], row["token"]
        from_dt, to_dt = get_time_range(days)
        try:
            df = fetch_candles_definedge(segment, token, "day", from_dt, to_dt, api_key)
            st.plotly_chart(plot_candlestick(df), use_container_width=True)
        except Exception as e:
            st.error(f"Error fetching candle data: {e}")

    st.info("Select watchlist and filters, then click 'Run Symbol Scan' to find matching symbols and visualize price action.")

if __name__ == "__main__":
    show()
