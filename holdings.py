import streamlit as st
import pandas as pd
from utils import integrate_get

import requests

def get_live_ltp_and_prev_close(exchange, token, session_key):
    url = f"https://integrate.definedgesecurities.com/dart/v1/quotes/{exchange}/{token}"
    headers = {"Authorization": session_key}
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            ltp = float(data.get('ltp', 0) or 0)
            prev_close = float(data.get('prev_close', 0) or 0)
            return ltp, prev_close
    except Exception as e:
        print(f"Error fetching quote for {exchange}/{token}: {e}")
    return 0, 0

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

    for h in holdings:
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

        # Always get live LTP and Prev Close for each holding
        ltp, prev_close = get_live_ltp_and_prev_close(exch, token, session_key)
        current = qty * ltp

        today_pnl = (ltp - prev_close) * qty if prev_close else 0
        overall_pnl = (ltp - avg_buy) * qty if avg_buy else 0
        pct_chg = ((ltp - prev_close) / prev_close * 100) if prev_close else 0
        pct_chg_avg = ((ltp - avg_buy) / avg_buy * 100) if avg_buy else 0

        # For debug:
        st.write(f"{tsym}: LTP={ltp}, PrevClose={prev_close}, Qty={qty}, TodayPnL={today_pnl}")

        rows.append({
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
        })

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
