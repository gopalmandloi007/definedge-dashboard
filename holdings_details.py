import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from utils import integrate_get
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
import requests
import io

st.set_page_config(layout="wide")

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

def compute_rsi(data, window=14):
    delta = data['Close'].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window=window).mean()
    avg_loss = loss.rolling(window=window).mean()
    avg_loss = avg_loss.replace(0, 1e-10)
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def compute_macd(data, slow=26, fast=12, signal=9):
    ema_slow = data['Close'].ewm(span=slow, adjust=False).mean()
    ema_fast = data['Close'].ewm(span=fast, adjust=False).mean()
    macd = ema_fast - ema_slow
    signal_line = macd.ewm(span=signal, adjust=False).mean()
    return macd, signal_line

def minervini_sell_signals(df, lookback_days=15):
    if len(df) < lookback_days:
        return {"error": "Insufficient data for analysis"}
    recent = df.tail(lookback_days).copy()
    recent['change'] = recent['Close'].pct_change() * 100
    recent['spread'] = recent['High'] - recent['Low']
    signals = {
        'up_days': 0,
        'down_days': 0,
        'up_day_percent': 0,
        'largest_up_day': 0,
        'largest_spread': 0,
        'exhaustion_gap': False,
        'high_volume_reversal': False,
        'churning': False,
        'heavy_volume_down': False,
        'warnings': []
    }
    for i in range(1, len(recent)):
        if recent['Close'].iloc[i] > recent['Close'].iloc[i-1]:
            signals['up_days'] += 1
        elif recent['Close'].iloc[i] < recent['Close'].iloc[i-1]:
            signals['down_days'] += 1
    signals['up_day_percent'] = (signals['up_days'] / lookback_days) * 100
    signals['largest_up_day'] = recent['change'].max()
    signals['largest_spread'] = recent['spread'].max()
    recent['gap_up'] = recent['Open'] > recent['High'].shift(1)
    recent['gap_down'] = recent['Open'] < recent['Low'].shift(1)
    recent['gap_filled'] = False
    for i in range(1, len(recent)):
        if recent['gap_up'].iloc[i]:
            if recent['Low'].iloc[i] <= recent['High'].shift(1).iloc[i]:
                recent.at[recent.index[i], 'gap_filled'] = True
                signals['exhaustion_gap'] = True
    avg_volume = recent['Volume'].mean()
    for i in range(1, len(recent)):
        if recent['Volume'].iloc[i] > avg_volume * 1.5:
            range_ = recent['High'].iloc[i] - recent['Low'].iloc[i]
            if (recent['High'].iloc[i] > recent['High'].iloc[i-1] and
                (recent['Close'].iloc[i] - recent['Low'].iloc[i]) < range_ * 0.25):
                signals['high_volume_reversal'] = True
                break
    if recent['Volume'].iloc[-1] > avg_volume * 1.8:
        price_change = abs(recent['Close'].iloc[-1] - recent['Open'].iloc[-1])
        if price_change < recent['spread'].iloc[-1] * 0.15:
            signals['churning'] = True
    if recent['Volume'].iloc[-1] > avg_volume * 1.5 and recent['change'].iloc[-1] < -3:
        signals['heavy_volume_down'] = True
    if signals['up_day_percent'] >= 70:
        signals['warnings'].append(
            f"⚠️ {signals['up_day_percent']:.0f}% up days ({signals['up_days']}/{lookback_days}) - Consider selling into strength"
        )
    if signals['largest_up_day'] > 5:
        signals['warnings'].append(
            f"⚠️ Largest up day: {signals['largest_up_day']:.2f}% - Potential climax run"
        )
    if signals['exhaustion_gap']:
        signals['warnings'].append("⚠️ Exhaustion gap detected - Potential reversal signal")
    if signals['high_volume_reversal']:
        signals['warnings'].append("⚠️ High-volume reversal - Institutional selling")
    if signals['churning']:
        signals['warnings'].append("⚠️ Churning detected (high volume, low progress) - Distribution likely")
    if signals['heavy_volume_down']:
        signals['warnings'].append("⚠️ Heavy volume down day - Consider exiting position")
    return signals

def show():
    st.header("📈 Holdings Details & Technicals")
    api_session_key = st.secrets.get("integrate_api_session_key", "")
    master_df = load_master()

    # Get holdings data
    data = integrate_get("/holdings")
    holdings = data.get("data", [])
    holding_symbols = []
    symbol_exchange = {}
    for h in holdings:
        ts = h.get("tradingsymbol")
        exch = h.get("exchange", "NSE")
        if isinstance(ts, list) and len(ts) > 0 and isinstance(ts[0], dict):
            tsym = ts[0].get("tradingsymbol", "N/A")
            exch = ts[0].get("exchange", exch)
        else:
            tsym = ts if isinstance(ts, str) else "N/A"
        holding_symbols.append(tsym)
        symbol_exchange[tsym] = exch

    selected_symbol = st.selectbox("Select Holding", sorted(holding_symbols))
    segment = symbol_exchange[selected_symbol]
    token = get_token(selected_symbol, segment, master_df)

    show_ema = st.checkbox("Show Moving Averages", value=True)
    show_rsi = st.checkbox("Show RSI", value=True)
    show_macd = st.checkbox("Show MACD", value=True)
    days_back = st.slider("Days to Show", 30, 365, 90)

    if token:
        from_dt, to_dt = get_time_range(days_back)
        chart_df = fetch_candles_definedge(segment, token, from_dt, to_dt, api_key=api_session_key)
        chart_df = chart_df.sort_values("Date")
        if show_ema:
            chart_df['EMA20'] = chart_df['Close'].ewm(span=20, adjust=False).mean()
            chart_df['EMA50'] = chart_df['Close'].ewm(span=50, adjust=False).mean()
        if show_rsi:
            chart_df['RSI'] = compute_rsi(chart_df)
        if show_macd:
            macd, signal = compute_macd(chart_df)
            chart_df['MACD'] = macd
            chart_df['Signal'] = signal

        # Plot chart
        rows = 1
        row_heights = [1.0]
        specs = [[{"secondary_y": True}]]
        if show_rsi and show_macd:
            rows = 3
            row_heights = [0.6, 0.2, 0.2]
            specs = [[{"secondary_y": True}], [{}], [{}]]
        elif show_rsi or show_macd:
            rows = 2
            row_heights = [0.7, 0.3]
            specs = [[{"secondary_y": True}], [{}]]

        fig = make_subplots(
            rows=rows, 
            cols=1,
            shared_xaxes=True,
            vertical_spacing=0.05,
            row_heights=row_heights,
            specs=specs
        )
        fig.add_trace(
            go.Candlestick(
                x=chart_df["Date"],
                open=chart_df["Open"],
                high=chart_df["High"],
                low=chart_df["Low"],
                close=chart_df["Close"],
                name="Price"
            ),
            row=1, col=1
        )
        if show_ema:
            fig.add_trace(
                go.Scatter(
                    x=chart_df["Date"],
                    y=chart_df["EMA20"],
                    mode="lines",
                    name="20 EMA",
                    line=dict(color="blue", width=1.5)
                ),
                row=1, col=1
            )
            fig.add_trace(
                go.Scatter(
                    x=chart_df["Date"],
                    y=chart_df["EMA50"],
                    mode="lines",
                    name="50 EMA",
                    line=dict(color="orange", width=1.5)
                ),
                row=1, col=1
            )
        if show_rsi:
            rsi_row = 2 if not show_macd else 2
            fig.add_trace(
                go.Scatter(
                    x=chart_df["Date"],
                    y=chart_df["RSI"],
                    mode="lines",
                    name="RSI",
                    line=dict(color="purple", width=1.5)
                ),
                row=rsi_row, col=1
            )
            fig.add_hline(
                y=30, line_dash="dash", line_color="green",
                row=rsi_row, col=1
            )
            fig.add_hline(
                y=70, line_dash="dash", line_color="red",
                row=rsi_row, col=1
            )
        if show_macd:
            macd_row = 2 if not show_rsi else 3
            fig.add_trace(
                go.Bar(
                    x=chart_df["Date"],
                    y=chart_df["MACD"],
                    name="MACD",
                    marker_color=np.where(chart_df['MACD'] > 0, 'green', 'red')
                ),
                row=macd_row, col=1
            )
            fig.add_trace(
                go.Scatter(
                    x=chart_df["Date"],
                    y=chart_df["Signal"],
                    mode="lines",
                    name="Signal",
                    line=dict(color="blue", width=1.5)
                ),
                row=macd_row, col=1
            )
        fig.update_layout(
            height=600,
            title=f"{selected_symbol} Technical Analysis",
            showlegend=True,
            xaxis_rangeslider_visible=False
        )
        st.plotly_chart(fig, use_container_width=True)

        # Minervini signals
        st.subheader("🔔 Minervini Sell Signals Analysis")
        minervini_lookback = st.slider("Analysis Lookback (days)", 7, 30, 15)
        signals = minervini_sell_signals(chart_df, minervini_lookback)
        if signals.get('error'):
            st.warning(signals['error'])
        else:
            st.write(signals)
            if signals['warnings']:
                st.error("## Sell Signals Detected")
                for warning in signals['warnings']:
                    st.error(warning)
            else:
                st.success("No strong sell signals detected")
    else:
        st.warning("Token not found for selected symbol")

if __name__ == "__main__":
    show()
