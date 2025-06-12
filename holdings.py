import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta
from utils import integrate_get, integrate_post

def get_ltp(exchange, token, session_key):
    url = f"https://integrate.definedgesecurities.com/dart/v1/quotes/{exchange}/{token}"
    headers = {"Authorization": session_key}
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            return float(data.get('ltp', 0) or 0)
    except Exception as e:
        print(f"LTP fetch error: {e}")
    return 0.0

def get_prev_close(exchange, token, session_key):
    # Fetches previous 2 days closes and returns the 2nd last (previous close)
    headers = {"Authorization": session_key}
    dt = datetime.now()
    date_str = dt.strftime('%d%m%Y')
    from_time = f"{date_str}0000"
    to_time = f"{date_str}1530"
    url = f"https://data.definedgesecurities.com/sds/history/{exchange}/{token}/day/{from_time}/{to_time}"
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            lines = [x for x in resp.text.strip().splitlines() if x]
            closes = [float(line.split(',')[4]) for line in lines if len(line.split(',')) > 4]
            if len(closes) >= 2:
                return closes[-2]
    except Exception as e:
        print(f"Prev close fetch error: {e}")
    return 0.0

def place_squareoff_order(exchange, tsym, qty, session_key):
    # Use data= not json= for requests
    order_data = {
        "exchange": exchange,
        "order_type": "SELL",
        "price": 0,
        "price_type": "MARKET",
        "product_type": "CNC",
        "quantity": int(qty),
        "tradingsymbol": tsym
    }
    try:
        resp = integrate_post("/orders", data=order_data, session_key=session_key)
        return resp
    except Exception as e:
        return f"Order error: {e}"

def show():
    st.header("=========== Holdings ===========")
    session_key = st.secrets["integrate_api_session_key"]
    data = integrate_get("/holdings")
    holdings = data.get("data", [])
    if not holdings:
        st.info("No holdings found.")
        return

    rows = []
    total_today_pnl = 0
    total_overall_pnl = 0
    total_invested = 0
    total_current = 0

    for idx, h in enumerate(holdings):
        ts = h.get("tradingsymbol")
        if isinstance(ts, list) and ts and isinstance(ts[0], dict):
            tsym = ts[0].get("tradingsymbol", "N/A")
            exch = ts[0].get("exchange", "NSE")
            isin = ts[0].get("isin", "")
            token = ts[0].get("token", "")
        else:
            tsym = ts if isinstance(ts, str) else "N/A"
            exch = h.get("exchange", "NSE")
            isin = h.get("isin", "")
            token = h.get("token", "")
        qty = float(h.get("dp_qty", 0) or 0)
        avg_buy = float(h.get("avg_buy_price", 0) or 0)
        invested = qty * avg_buy

        ltp = get_ltp(exch, token, session_key)
        prev_close = get_prev_close(exch, token, session_key)
        current = qty * ltp

        today_pnl = (ltp - prev_close) * qty if prev_close else 0
        overall_pnl = (ltp - avg_buy) * qty if avg_buy else 0
        pct_chg = ((ltp - prev_close) / prev_close * 100) if prev_close else 0
        pct_chg_avg = ((ltp - avg_buy) / avg_buy * 100) if avg_buy else 0

        row = {
            "Symbol": tsym,
            "LTP": round(ltp, 2),
            "Avg Buy": round(avg_buy, 2),
            "Qty": int(qty),
            "P.Close": round(prev_close, 2),
            "%Chg": round(pct_chg, 2),
            "Today P&L": round(today_pnl, 2),
            "Overall P&L": round(overall_pnl, 2),
            "%Chg Avg": round(pct_chg_avg, 2),
            "Invested": round(invested, 2),
            "Current": round(current, 2),
            "Exchange": exch,
            "ISIN": isin,
            "T1": h.get("t1_qty", 0),
            "Haircut": h.get("haircut", 0),
            "Coll Qty": h.get("collateral_qty", 0),
            "Sell Amt": h.get("sell_amt", 0),
            "Trade Qty": h.get("trade_qty", 0)
        }
        rows.append(row)

        # Square Off button for each row
        col1, col2 = st.columns([9, 1])
        with col1:
            st.write(f"{tsym} | Qty: {int(qty)} | LTP: {round(ltp,2)} | Overall P&L: {round(overall_pnl,2)}")
        with col2:
            if st.button(f"Square Off {tsym}", key=f"squareoff_{idx}_{tsym}"):
                if qty > 0:
                    resp = place_squareoff_order(exch, tsym, qty, session_key)
                    st.success(f"Square off order placed for {tsym}: {resp}")
                else:
                    st.warning("No holding quantity to square off.")

        total_today_pnl += today_pnl
        total_overall_pnl += overall_pnl
        total_invested += invested
        total_current += current

    df = pd.DataFrame(rows)
    st.markdown("""
**Summary**
|            | Amount   | Total Invested value | Total current value |
|------------|----------|---------------------|--------------------|
| Today P&L  | {:.2f}   | {:.2f}              | {:.2f}             |
| Overall P&L| {:.2f}   |                     |                    |
""".format(total_today_pnl, total_invested, total_current, total_overall_pnl)
    )

    st.markdown(f"**Total NSE Holdings: {len(df)}**")
    st.dataframe(df, use_container_width=True)
