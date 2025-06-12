import streamlit as st
import pandas as pd
from utils import integrate_get

def show():
    st.header("Holdings Book (Live P&L with Prev Close)")
    data = integrate_get("/holdings")
    holdings = data.get("data", [])
    if not holdings:
        st.info("No holdings found.")
        return
    rows = []
    for h in holdings:
        ts = h.get("tradingsymbol", "N/A")
        exch = h.get("exchange", "NSE")
        qty = float(h.get("dp_qty", 0) or 0)
        avg_buy = float(h.get("avg_buy_price", 0) or 0)
        invested = qty * avg_buy
        ltp = float(h.get("ltp", 0) or 0)
        prev_close = float(h.get("prev_close", 0) or 0)
        curr_val = qty * ltp
        today_pnl = (ltp - prev_close) * qty if prev_close else 0
        pct_change = ((ltp - prev_close) / prev_close * 100) if prev_close else 0
        overall_pnl = (ltp - avg_buy) * qty if avg_buy else 0
        pct_change_avg = ((ltp - avg_buy) / avg_buy * 100) if avg_buy else 0
        rows.append({
            "Symbol": ts,
            "Qty": qty,
            "Avg Buy": avg_buy,
            "Invested": invested,
            "LTP": ltp,
            "Prev Close": prev_close,
            "Today P&L": today_pnl,
            "%Change": pct_change,
            "Overall P&L": overall_pnl,
            "%Change Avg": pct_change_avg,
            "Current": curr_val,
            "Exchange": exch,
            "ISIN": h.get("isin", "")
        })
    if not rows:
        st.info("No holdings with valid qty.")
        return
    df = pd.DataFrame(rows)
    totals = {
        "Invested": df["Invested"].sum(),
        "Current": df["Current"].sum(),
        "Today P&L": df["Today P&L"].sum(),
        "Overall P&L": df["Overall P&L"].sum()
    }
    st.write("**Summary**")
    st.json(totals)
    st.dataframe(df)
