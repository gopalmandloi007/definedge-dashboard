import streamlit as st
import pandas as pd
from utils import integrate_get

def show():
    st.header("=========== Holdings ===========")

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
        # Handle both string and list for tradingsymbol
        ts = h.get("tradingsymbol")
        if isinstance(ts, list) and len(ts) > 0 and isinstance(ts[0], dict):
            tsym = ts[0].get("tradingsymbol", "N/A")
            exch = ts[0].get("exchange", "N/A")
            isin = ts[0].get("isin", "")
        else:
            tsym = ts if isinstance(ts, str) else "N/A"
            exch = h.get("exchange", "NSE")
            isin = h.get("isin", "")

        ltp = float(h.get("ltp", 0) or 0)
        avg_buy = float(h.get("avg_buy_price", 0) or 0)
        qty = float(h.get("dp_qty", 0) or 0)
        prev_close = float(h.get("prev_close", 0) or 0)
        t1_qty = h.get("t1_qty", 0)
        haircut = h.get("haircut", 0)
        collateral_qty = h.get("collateral_qty", 0)
        sell_amt = float(h.get("sell_amt", 0) or 0)
        trade_qty = float(h.get("trade_qty", 0) or 0)

        invested = avg_buy * qty
        current = ltp * qty

        # Today P&L
        today_pnl = (ltp - prev_close) * qty if prev_close else 0
        overall_pnl = (ltp - avg_buy) * qty if avg_buy else 0

        # Percent changes
        pct_chg = ((ltp - prev_close) / prev_close * 100) if prev_close else 0
        pct_chg_avg = ((ltp - avg_buy) / avg_buy * 100) if avg_buy else 0

        # Realized P&L (if any, for exited qty)
        realized_pnl = 0  # Can be calculated if API provides exited qty and sell avg price

        # Totals
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
