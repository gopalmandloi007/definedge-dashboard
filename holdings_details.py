import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta
from utils import integrate_get
import plotly.express as px

# ========== Master Loader & Token Lookup ==========

@st.cache_data
def load_master():
    df = pd.read_csv("master.csv", sep="\t", header=None)
    df.columns = [
        "segment", "token", "symbol", "instrument", "series", "isin1",
        "facevalue", "lot", "something", "zero1", "two1", "one1", "isin", "one2"
    ]
    return df[["segment", "token", "symbol", "instrument"]]

def get_token(symbol, segment, master_df):
    symbol = str(symbol).strip().upper()
    segment = str(segment).strip().upper()
    row = master_df[(master_df['symbol'] == symbol) & (master_df['segment'] == segment)]
    if not row.empty:
        return row.iloc[0]['token']
    row2 = master_df[(master_df['instrument'] == symbol) & (master_df['segment'] == segment)]
    if not row2.empty:
        return row2.iloc[0]['token']
    return None

def safe_float(val):
    try:
        return float(val)
    except Exception:
        return 0.0

# ========== LTP Fetcher ==========

def get_ltp(exchange, token, api_session_key):
    if not exchange or not token:
        return None
    url = f"https://integrate.definedgesecurities.com/dart/v1/quotes/{exchange}/{token}"
    headers = {"Authorization": api_session_key}
    try:
        resp = requests.get(url, headers=headers, timeout=5)
        if resp.status_code == 200:
            ltp = resp.json().get("ltp", None)
            return safe_float(ltp)
        else:
            return None
    except Exception:
        return None

def get_prev_close(exchange, token, api_session_key):
    today = datetime.now()
    for i in range(1, 5):
        prev_day = today - timedelta(days=i)
        if prev_day.weekday() < 5:
            break
    else:
        prev_day = today - timedelta(days=1)
    from_str = prev_day.strftime("%d%m%Y0000")
    to_str = today.strftime("%d%m%Y1530")
    url = f"https://data.definedgesecurities.com/sds/history/{exchange}/{token}/day/{from_str}/{to_str}"
    headers = {"Authorization": api_session_key}
    try:
        resp = requests.get(url, headers=headers, timeout=5)
        if resp.status_code == 200:
            rows = resp.text.strip().split("\n")
            if len(rows) >= 2:
                prev_row = rows[-2]
                prev_close = safe_float(prev_row.split(",")[4])
                return prev_close
            elif len(rows) == 1:
                prev_close = safe_float(rows[0].split(",")[4])
                return prev_close
    except Exception:
        pass
    return None

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

# ========== MAIN DASHBOARD ==========

def show():
    st.title("Holdings Details Dashboard")

    api_session_key = st.secrets.get("integrate_api_session_key", "")
    master_df = load_master()

    # --- Fetch holdings data ---
    data = integrate_get("/holdings")
    holdings = data.get("data", [])
    if not holdings:
        st.warning("No holdings found.")
        return

    # Filter only ACTIVE holdings (qty > 0)
    active_holdings = []
    for h in holdings:
        qty = safe_float(h.get("dp_qty", 0))
        if qty > 0:
            active_holdings.append(h)

    rows = []
    total_invested = 0.0
    total_current = 0.0
    total_open_risk = 0.0

    for h in active_holdings:
        # Symbol, Exchange, ISIN etc.
        ts = h.get("tradingsymbol")
        exch = h.get("exchange", "NSE")
        segment = exch # If you have segment separately, use that
        isin = h.get("isin", "")
        product = h.get("product", "")
        qty = safe_float(h.get("dp_qty", 0))
        entry = safe_float(h.get("avg_buy_price", 0))
        invested = entry * qty

        # --- Token from master ---
        token = get_token(ts, segment, master_df)
        ltp = get_ltp(exch, token, api_session_key) if token else None
        if not ltp or ltp == 0:
            ltp = get_prev_close(exch, token, api_session_key) if token else None

        # --- Current Value & P&L ---
        if ltp and ltp > 0:
            current_value = ltp * qty
            pnl = current_value - invested
            change_pct = ((ltp - entry) / entry * 100) if entry else 0
        else:
            current_value = None
            pnl = None
            change_pct = None

        # --- Trailing Stop Loss Logic ---
        initial_sl = round(entry * 0.97, 2)
        status = "Initial SL"
        trailing_sl = initial_sl

        if ltp and ltp > 0:
            if change_pct >= 30:
                trailing_sl = round(entry * 1.20, 2)
                status = "Excellent Profit (SL at Entry +20%)"
            elif change_pct >= 20:
                trailing_sl = round(entry * 1.10, 2)
                status = "Good Profit (SL at Entry +10%)"
            elif change_pct >= 10:
                trailing_sl = round(entry, 2)
                status = "Safe (Breakeven SL)"

        open_risk = (trailing_sl - entry) * qty

        # --- Accumulate Totals ---
        total_invested += invested
        total_current += current_value if current_value else 0
        total_open_risk += open_risk

        rows.append({
            "Symbol": ts,
            "Exchange": exch,
            "ISIN": isin,
            "Product": product,
            "Qty": qty,
            "Entry": entry,
            "Invested": invested,
            "Current Price": ltp if ltp else "N/A",
            "Current Value": current_value if current_value else "N/A",
            "P&L": pnl if pnl is not None else "N/A",
            "Change %": round(change_pct, 2) if change_pct is not None else "N/A",
            "Status": status,
            "Stop Loss": trailing_sl,
            "Open Risk": open_risk,
            "DP Free Qty": h.get("dp_free_qty", ""),
            "Pledge Qty": h.get("pledge_qty", ""),
            "Collateral Qty": h.get("collateral_qty", ""),
            "T1 Qty": h.get("t1_qty", ""),
        })

    df = pd.DataFrame(rows)
    if df.empty:
        st.warning("No active holdings with quantity > 0.")
        return

    # --- Capital Management ---
    TOTAL_CAPITAL = 650000.0
    cash_in_hand = max(TOTAL_CAPITAL - total_invested, 0)
    allocation_percent = (total_invested / TOTAL_CAPITAL * 100) if TOTAL_CAPITAL else 0

    st.subheader("💰 Capital Management")
    colA, colB, colC = st.columns(3)
    colA.metric("Total Capital", f"₹{TOTAL_CAPITAL:,.0f}")
    colB.metric("Invested", f"₹{total_invested:,.0f}", f"{allocation_percent:.1f}%")
    colC.metric("Cash in Hand", f"₹{cash_in_hand:,.0f}")

    # --- Pie Chart: Allocation (with Cash in Hand) ---
    df_pie = df[["Symbol", "Invested"]].copy()
    df_pie = pd.concat([
        df_pie,
        pd.DataFrame([{"Symbol": "Cash in Hand", "Invested": cash_in_hand}])
    ], ignore_index=True)

    st.subheader("Portfolio Allocation Pie (with Cash)")
    fig = px.pie(
        df_pie,
        names="Symbol",
        values="Invested",
        title="Allocation by Stock & Cash",
        hole=0.3
    )
    fig.update_traces(textinfo='label+percent')
    st.plotly_chart(fig, use_container_width=True)

    # --- Main Holdings Table with all columns and P&L color ---
    st.subheader("Holdings Details Table (with Trailing SL & Open Risk)")
    st.dataframe(
        df.style.applymap(
            highlight_pnl,
            subset=["P&L", "Open Risk"]
        ),
        use_container_width=True,
    )

    # --- Totals Summary ---
    st.subheader("Summary")
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Total Invested", f"₹{total_invested:,.0f}")
    col2.metric("Total Current Value", f"₹{total_current:,.0f}")
    col3.metric("Total P&L", f"₹{(total_current-total_invested):,.0f}")
    col4.metric("Total Qty", f"{df['Qty'].sum():,.0f}")
    col5.metric("Total Open Risk", f"₹{total_open_risk:,.0f}")

    st.info(
        "Trailing Stop Loss logic: "
        "Initial SL = Entry - 3%. "
        "If gain >10%, SL moves to Entry (Safe). "
        "If gain >20%, SL = Entry +10% (Good Profit). "
        "If gain >30%, SL = Entry +20% (Excellent Profit)."
    )
