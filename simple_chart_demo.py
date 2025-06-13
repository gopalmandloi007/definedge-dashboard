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
    # Parse date, only keep rows with valid dates
    df["Date"] = pd.to_datetime(df["Dateandtime"], format="%d%m%Y%H%M", errors="coerce")
    df = df.dropna(subset=["Date"])
    # Only keep dates up to today (no future dates!)
    df = df[df["Date"] <= pd.Timestamp.now()]
    for col in ["Open", "High", "Low", "Close", "Volume"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df

def get_time_range(days, endtime="1530"):
    # Always end at today (Indian market close time)
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

    col1, col2 = st.columns(2)
    with col1:
        segment = st.selectbox("Segment", sorted(master_df["segment"].str.upper().unique()), index=0)
    with col2:
        symbol_list = master_df[master_df["segment"] == segment]["symbol"].unique()
        symbol = st.selectbox("Symbol", sorted(symbol_list), index=0)
    st.write("Selected:", segment, symbol)

    token = get_token(symbol, segment, master_df)
    if not token:
        st.error("Symbol-token mapping not found in master file. Try another symbol.")
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
    chart_df = df.tail(60)
    fig = go.Figure(data=[go.Candlestick(
        x=chart_df["Date"],
        open=chart_df["Open"],
        high=chart_df["High"],
        low=chart_df["Low"],
        close=chart_df["Close"],
        name="Candles"
    )])
    fig.update_layout(
        height=400,
        margin=dict(l=10, r=10, t=30, b=10),
        xaxis_rangeslider_visible=False,
        title=f"{symbol} Daily Candlestick Chart"
    )
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(chart_df[["Date", "Open", "High", "Low", "Close"]].tail(15))

    st.info("This chart shows daily candles including the latest available data from Definedge API.")

if __name__ == "__main__":
    show()
