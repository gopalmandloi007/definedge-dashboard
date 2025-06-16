import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objs as go
import io
from utils import integrate_get

@st.cache_data
def load_master():
    # Supports both 14 and 15 column master.csv automatically
    df = pd.read_csv("master.csv", sep="\t", header=None)
    if df.shape[1] == 15:
        df.columns = [
            "segment", "token", "symbol", "symbol_series", "series", "unknown1",
            "unknown2", "unknown3", "series2", "unknown4", "unknown5", "unknown6",
            "isin", "unknown7", "company"
        ]
        return df[["segment", "token", "symbol", "symbol_series", "series"]]
    else:  # legacy 14-column
        df.columns = [
            "segment", "token", "symbol", "instrument", "series", "isin1",
            "facevalue", "lot", "something", "zero1", "two1", "one1", "isin", "one2"
        ]
        return df[["segment", "token", "symbol", "instrument", "series"]]

def get_token(symbol, segment, master_df):
    symbol = symbol.strip().upper()
    segment = segment.strip().upper()
    # Try symbol
    row = master_df[(master_df['symbol'].str.upper() == symbol) & (master_df['segment'].str.upper() == segment)]
    if not row.empty:
        return row.iloc[0]['token']
    # Try symbol_series (for 15-col), or instrument (for 14-col)
    if "symbol_series" in master_df.columns:
        row2 = master_df[(master_df['symbol_series'].str.upper() == symbol) & (master_df['segment'].str.upper() == segment)]
        if not row2.empty:
            return row2.iloc[0]['token']
    if "instrument" in master_df.columns:
        row3 = master_df[(master_df['instrument'].str.upper() == symbol) & (master_df['segment'].str.upper() == segment)]
        if not row3.empty:
            return row3.iloc[0]['token']
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
        to = now
    frm = to - timedelta(days=days)
    return frm.strftime("%d%m%Y%H%M"), to.strftime("%d%m%Y%H%M")

def highlight_pnl(val):
    try:
        val = float(val)
        if val > 0:
            return 'color: green'
        elif val < 0:
            return 'color: red'
    except:
        pass
    return 'color: black'

def show():
    st.header("=========== Positions Dashboard Pro ===========")
    api_session_key = st.secrets.get("integrate_api_session_key", "")
    master_df = load_master()

    try:
        data = integrate_get("/positions")
        positions = data.get("data", [])
        if not positions:
            st.info("No positions found.")
            return

        # Prepare symbols/segments for chart dropdown
        active_positions = []
        symbol_segment_dict = {}
        for pos in positions:
            qty = 0.0
            ts = pos.get("tradingsymbol")
            exch = pos.get("exchange", "NSE")
            # Some APIs send 'quantity', some send 'netqty'
            qty = float(pos.get("netqty", pos.get("quantity", 0)))
            if qty != 0:  # Only active (open) positions
                active_positions.append((ts, exch))
                symbol_segment_dict[ts] = exch

        if not active_positions:
            st.info("No active positions for chart.")
            return

        # Chart section
        st.subheader("📈 Chart: See Candlestick for your Positions")
        position_symbols = list(symbol_segment_dict.keys())
        selected_symbol = st.selectbox("Select Position Symbol for Chart", sorted(position_symbols))
        segment = symbol_segment_dict[selected_symbol]
        token = get_token(selected_symbol, segment, master_df)
        if token:
            show_ema20 = st.checkbox("Show 20 EMA", value=True, key="ema20_chart")
            show_ema50 = st.checkbox("Show 50 EMA", value=True, key="ema50_chart")
            from_dt, to_dt = get_time_range(120)
            try:
                chart_df = fetch_candles_definedge(segment, token, from_dt, to_dt, api_key=api_session_key)
                chart_df = chart_df.sort_values("Date")
                chart_df = chart_df.tail(60).copy()
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
                    title=f"{selected_symbol} Daily Candlestick Chart",
                    xaxis=dict(type="category")
                )
                st.plotly_chart(fig, use_container_width=True)
                st.dataframe(chart_df[["Date", "Open", "High", "Low", "Close"]].tail(15))
            except Exception as e:
                st.error(f"Error fetching chart data: {e}")
        else:
            st.warning("Symbol-token mapping not found in master file for chart.")

    except Exception as e:
        st.error(f"Error loading positions: {e}")

if __name__ == "__main__":
    show()
