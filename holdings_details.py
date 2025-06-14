import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from utils import integrate_get
import requests
import io

st.set_page_config(layout="wide")

def safe_float(val):
    try:
        return float(val)
    except Exception:
        return 0.0

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

def get_ltp(exchange, token, api_session_key):
    if not exchange or not token:
        return 0.0
    url = f"https://integrate.definedgesecurities.com/dart/v1/quotes/{exchange}/{token}"
    headers = {"Authorization": api_session_key}
    try:
        resp = requests.get(url, headers=headers, timeout=5)
        if resp.status_code == 200:
            return safe_float(resp.json().get("ltp", 0))
        else:
            return None
    except Exception:
        return None

def show():
    st.header("Holdings Details & Stop Loss Management")
    api_session_key = st.secrets.get("integrate_api_session_key", "")
    master_df = load_master()

    # --- Total capital setup ---
    if 'total_capital' not in st.session_state:
        st.session_state.total_capital = 657000.0  # You can set your default here

    st.sidebar.subheader("💰 Capital Management")
    total_capital = st.sidebar.number_input(
        "Total Capital (Cash + Invested)",
        min_value=0.0,
        value=st.session_state.total_capital,
        step=10000.0,
        key="total_capital_input"
    )
    st.session_state.total_capital = total_capital

    data = integrate_get("/holdings")
    holdings = data.get("data", [])
    holding_symbols = []
    symbol_exchange = {}
    avg_buys = {}
    qtys = {}
    tokens = {}

    for h in holdings:
        ts = h.get("tradingsymbol")
        exch = h.get("exchange", "NSE")
        if isinstance(ts, list) and len(ts) > 0 and isinstance(ts[0], dict):
            tsym = ts[0].get("tradingsymbol", "N/A")
            exch = ts[0].get("exchange", exch)
            qty = safe_float(ts[0].get("dp_qty", h.get("dp_qty", 0)))
            avg_buy = safe_float(ts[0].get("avg_buy_price", h.get("avg_buy_price", 0)))
            token = ts[0].get("token")
        else:
            tsym = ts if isinstance(ts, str) else "N/A"
            qty = safe_float(h.get("dp_qty", 0))
            avg_buy = safe_float(h.get("avg_buy_price", 0))
            token = h.get("token")
        holding_symbols.append(tsym)
        symbol_exchange[tsym] = exch
        avg_buys[tsym] = avg_buy
        qtys[tsym] = qty
        tokens[tsym] = token

    selected_symbol = st.selectbox("Select Holding", sorted(holding_symbols))
    segment = symbol_exchange[selected_symbol]
    avg_buy = avg_buys[selected_symbol]
    qty = qtys[selected_symbol]
    token = tokens[selected_symbol]

    # --- Stop loss state management per stock ---
    if 'stop_losses' not in st.session_state:
        st.session_state.stop_losses = {}
    default_stop_loss = round(avg_buy * 0.98, 2)
    stop_loss = st.session_state.stop_losses.get(selected_symbol, default_stop_loss)

    st.subheader(f"Stop Loss for {selected_symbol}")
    stop_loss_input = st.number_input(
        "Stop Loss Price", min_value=0.0, value=stop_loss, step=0.1, key=f"stop_loss_{selected_symbol}"
    )

    if st.button("Update Stop Loss"):
        st.session_state.stop_losses[selected_symbol] = stop_loss_input
        st.success(f"Stop loss updated for {selected_symbol}")

    # --- Calculate open risk ---
    ltp = get_ltp(segment, token, api_session_key)
    open_risk = (ltp - stop_loss_input) * qty if ltp and qty else 0.0

    st.write(f"**Entry Price:** ₹{avg_buy:,.2f}")
    st.write(f"**Current LTP:** ₹{ltp:,.2f}" if ltp else "**Current LTP:** N/A")
    st.write(f"**Quantity:** {qty}")
    st.write(f"**Selected Stop Loss:** ₹{stop_loss_input:,.2f}")
    st.write(f"### 🛑 Open Risk: ₹{open_risk:,.2f}")

    # --- Capital Allocation Summary ---
    invested = avg_buy * qty
    cash_balance = st.session_state.total_capital - invested
    allocation_percent = invested / st.session_state.total_capital * 100 if st.session_state.total_capital else 0

    st.subheader("Capital Allocation Metrics")
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Capital", f"₹{st.session_state.total_capital:,.0f}")
    col2.metric("Invested (this stock)", f"₹{invested:,.0f}")
    col3.metric("Allocation %", f"{allocation_percent:.2f}%")

    st.info(f"Editable capital reflects your cash + invested. Adjust as your demat balance changes.")

if __name__ == "__main__":
    show()
