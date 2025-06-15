import streamlit as st
import pandas as pd
import requests
import io
from datetime import datetime, timedelta
import plotly.graph_objs as go

@st.cache_data
def load_master():
    df = pd.read_csv("master.csv", sep="\t", header=None)
    df.columns = [
        "segment", "token", "symbol", "symbol_series", "series", "unknown1",
        "unknown2", "unknown3", "series2", "unknown4", "unknown5", "unknown6",
        "isin", "unknown7", "company"
    ]
    return df[["segment", "token", "symbol", "symbol_series", "series", "company"]]

def get_token(symbol, segment, series, master_df):
    # Try to match on symbol, symbol_series, segment, and series (case insensitive)
    candidates = master_df[
        (master_df['segment'].str.upper() == segment.upper()) &
        ((master_df['symbol'].str.upper() == symbol.upper()) | (master_df['symbol_series'].str.upper() == symbol.upper()))
    ]
    if not candidates.empty:
        # Prefer exact series match if present
        row = candidates[candidates['series'].str.upper() == series.upper()]
        if not row.empty:
            return row.iloc[0]['token']
        # Fallback: return first candidate
        return candidates.iloc[0]['token']
    return None

def fetch_candles_definedge(segment, token, from_dt, to_dt, api_key):
    url = f"https://data.definedgesecurities.com/sds/history/{segment}/{token}/day/{from_dt}/{to_dt}"
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
    df = df[df["Date"] <= pd.Timestamp.now()]
    for col in ["Open", "High", "Low", "Close", "Volume"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df

def get_time_range(days, endtime="1530"):
    now = datetime.now()
    to = now.replace(hour=15, minute=30, second=0, microsecond=0)
    if to > now:
        to = now  # In case running before market close
    frm = to - timedelta(days=days)
    return frm.strftime("%d%m%Y%H%M"), to.strftime("%d%m%Y%H%M")

def show():
    st.header("Definedge Simple Candlestick Chart Demo (Daily, Live)")

    api_key = st.secrets.get("integrate_api_session_key", "")
    master_df = load_master()

    segment_options = sorted(master_df["segment"].str.upper().unique())
    segment = st.selectbox("Segment", segment_options, index=0)

    # Show all unique symbol+series display names for this segment
    df_segment = master_df[master_df["segment"].str.upper() == segment]
    # Compose display names: symbol (series) for clarity
    df_segment["display_name"] = df_segment.apply(
        lambda r: f"{r['symbol']} ({r['series']})" if pd.notnull(r['series']) else r['symbol'], axis=1
    )
    # Only show each symbol+series combo once
    df_segment = df_segment.drop_duplicates(subset=["symbol", "series"])
    symbol_display_list = df_segment["display_name"].tolist()
    symbol_idx = 0
    symbol_display = st.selectbox("Symbol", symbol_display_list, index=symbol_idx)

    # Get selected row for this display name
    selected_row = df_segment[df_segment["display_name"] == symbol_display].iloc[0]
    symbol = selected_row["symbol"]
    # For stocks, allow EQ/BE, for indices force IDX
    possible_series = df_segment[df_segment["symbol"] == symbol]["series"].unique()
    if len(possible_series) == 1:
        series = possible_series[0]
    else:
        # Let user pick if multiple (e.g. EQ/BE for stocks)
        series = st.selectbox("Series", possible_series, index=0)

    st.write("Selected:", segment, symbol, series)

    col3, col4 = st.columns(2)
    with col3:
        show_ema20 = st.checkbox("Show 20 EMA", value=True)
    with col4:
        show_ema50 = st.checkbox("Show 50 EMA", value=True)

    token = get_token(symbol, segment, series, master_df)
    if not token:
        st.error("Symbol-token mapping not found in master file. Try another symbol/series.")
        return

    from_dt, to_dt = get_time_range(120)
    try:
        df = fetch_candles_definedge(segment, token, from_dt, to_dt, api_key)
    except Exception as e:
        st.error(f"Error fetching candles: {e}")
        return

    if df.empty:
        st.warning("No data fetched for this symbol.")
        return

    df = df.sort_values("Date")
    chart_df = df.tail(60).copy()

    if show_ema20:
        chart_df['EMA20'] = chart_df['Close'].ewm(span=20, adjust=False).mean()
    if show_ema50:
        chart_df['EMA50'] = chart_df['Close'].ewm(span=50, adjust=False).mean()

    fig = go.Figure()
    fig.add_trace(go.Candlestick(
        x=chart_df["Date"].dt.strftime("%Y-%m-%d"),
        open=chart_df["Open"],
        high=chart_df["High"],
        low=chart_df["Low"],
        close=chart_df["Close"],
        name="Candles"
    ))
    if show_ema20:
        fig.add_trace(go.Scatter(
            x=chart_df["Date"].dt.strftime("%Y-%m-%d"),
            y=chart_df["EMA20"],
            mode="lines",
            name="20 EMA",
            line=dict(color="blue", width=1.5)
        ))
    if show_ema50:
        fig.add_trace(go.Scatter(
            x=chart_df["Date"].dt.strftime("%Y-%m-%d"),
            y=chart_df["EMA50"],
            mode="lines",
            name="50 EMA",
            line=dict(color="orange", width=1.5)
        ))

    fig.update_layout(
        height=400,
        margin=dict(l=10, r=10, t=30, b=10),
        xaxis_rangeslider_visible=False,
        title=f"{symbol} ({series}) Daily Candlestick Chart",
        xaxis=dict(type="category")
    )
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(chart_df[["Date", "Open", "High", "Low", "Close"]].tail(15))

    st.info("This chart shows daily candles including the latest available data from Definedge API. Toggle 20/50 EMA above.")

if __name__ == "__main__":
    show()
