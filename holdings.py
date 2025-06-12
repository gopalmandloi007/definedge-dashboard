import streamlit as st
import pandas as pd
from utils import integrate_get  # aapka existing function

import requests
from datetime import datetime, timedelta

def get_ltp(exchange, token, api_session_key):
    url = f"https://integrate.definedgesecurities.com/dart/v1/quotes/{exchange}/{token}"
    headers = {"Authorization": api_session_key}
    resp = requests.get(url, headers=headers)
    if resp.status_code == 200:
        return resp.json().get("ltp", 0)
    return 0

def get_prev_close(exchange, token, api_session_key):
    # previous trading day calculate karo
    to_date = datetime.now()
    from_date = to_date - timedelta(days=2)  # 2 din peechhe tak le lo, weekends handle karne ke liye
    from_str = from_date.strftime("%d%m%Y0000")
    to_str = to_date.strftime("%d%m%Y1530")
    url = f"https://data.definedgesecurities.com/sds/history/{exchange}/{token}/day/{from_str}/{to_str}"
    headers = {"Authorization": api_session_key}
    resp = requests.get(url, headers=headers)
    if resp.status_code == 200:
        rows = resp.text.strip().split("\n")
        if len(rows) >= 2:
            # Last but one row ka close price (previous day ka close)
            prev_row = rows[-2]
            prev_close = float(prev_row.split(",")[4])
            return prev_close
        elif len(rows) == 1:
            # Sirf ek row hai (matlab aaj ka hi data hai)
            prev_close = float(rows[0].split(",")[4])
            return prev_close
    return 0

def show():
    st.header("=========== Holdings ===========")

    api_session_key = st.secrets["integrate_api_session_key"]
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
        # Extract symbol, exchange, token
        ts = h.get("tradingsymbol")
        exch = h.get("exchange", "NSE")
        token = None
        isin = ""
        if isinstance(ts, list) and len(ts) > 0 and isinstance(ts[0], dict):
            tsym = ts[0].get("tradingsymbol", "N/A")
            exch = ts[0].get("exchange", "NSE")
            token = ts[0].get("token")
            isin = ts[0].get("isin", "")
        else:
            tsym = ts if isinstance(ts, str) else "N/A"
            token = h.get("token")
            isin = h.get("isin", "")

        avg_buy = float(h.get("avg_buy_price", 0) or 0)
        qty = float(h.get("dp_qty", 0) or 0)

        # Get LTP and Prev Close using new APIs
        ltp = get_ltp(exch, token, api_session_key) if token else 0
        prev_close = get_prev_close(exch, token, api_session_key) if token else 0

        t1_qty = h.get("t1_qty", 0)
        haircut = h.get("haircut", 0)
        collateral_qty = h.get("collateral_qty", 0)
        sell_amt = float(h.get("sell_amt", 0) or 0)
        trade_qty = float(h.get("trade_qty", 0) or 0)

        invested = avg_buy * qty
        current = ltp * qty

        today_pnl = (ltp - prev_close) * qty if prev_close else 0
        overall_pnl = (ltp - avg_buy) * qty if avg_buy else 0
        pct_chg = ((ltp - prev_close) / prev_close * 100) if prev_close else 0
        pct_chg_avg = ((ltp - avg_buy) / avg_buy * 100) if avg_buy else 0
        realized_pnl = 0

        total_today_pnl += today_pnl
        total_overall_pnl += overall_pnl
        total_invested += invested
        total_current += current

        rows.append([
            tsym,
            round(ltp, 2),
            round(avg_buy, 2),
            int(qty),
            round(prev_close, 2),
            round(pct_chg, 2),
            round(today_pnl, 2),
            round(overall_pnl, 2),
            round(realized_pnl, 2) if realized_pnl else "",
            round(pct_chg_avg, 2),
            round(invested, 2),
            round(current, 2),
            exch,
            isin,
            t1_qty,
            haircut,
            collateral_qty,
            round(sell_amt, 2),
            int(trade_qty)
        ])

    headers = [
        "Symbol", "LTP", "Avg Buy", "Qty", "P.Close", "%Chg", "Today P&L", "Overall P&L",
        "Realized P&L", "%Chg Avg", "Invested", "Current", "Exchange", "ISIN", "T1", "Haircut",
        "Coll Qty", "Sell Amt", "Trade Qty"
    ]

    df = pd.DataFrame(rows, columns=headers)

    st.markdown("""
| Summary         | Amount        | Total Invested value | Total current value |
|-----------------|--------------|----------------------|---------------------|
| Today P&L       | {:.2f}        | {:.2f}               | {:.2f}              |
| Overall P&L     | {:.2f}        |                      |                     |
    """.format(total_today_pnl, total_invested, total_current, total_overall_pnl)
    )

    st.markdown(f"**Total NSE Holdings: {len(df)}**")

    st.dataframe(df, use_container_width=True)
