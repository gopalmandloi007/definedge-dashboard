import streamlit as st
import pandas as pd
from utils import integrate_get

def show():
    st.title("Holdings Details")

    # Fetch holdings data
    data = integrate_get("/holdings")
    holdings = data.get("data", [])
    if not holdings:
        st.warning("No holdings found.")
        return

    # Prepare rows for DataFrame
    rows = []
    for h in holdings:
        ts = h.get("tradingsymbol")
        exch = h.get("exchange", "NSE")
        qty = float(h.get("dp_qty", 0) or 0)
        avg_buy = float(h.get("avg_buy_price", 0) or 0)
        ltp = float(h.get("ltp", h.get("current_price", 0)) or 0)
        invested = avg_buy * qty
        current_value = ltp * qty
        pnl = current_value - invested

        rows.append({
            "Symbol": ts,
            "Exchange": exch,
            "Qty": qty,
            "Avg Buy": avg_buy,
            "Current Price": ltp,
            "Invested": invested,
            "Current Value": current_value,
            "P&L": pnl
        })

    df = pd.DataFrame(rows)
    if df.empty:
        st.warning("No active holdings with quantity > 0.")
        return

    # Show dataframe
    st.dataframe(
        df.style.applymap(
            lambda x: "background-color:#c6f5c6" if isinstance(x, (int, float)) and x > 0 else ("background-color:#ffcccc" if isinstance(x, (int, float)) and x < 0 else ""),
            subset=["P&L"]
        ),
        use_container_width=True,
    )

    # Total summary
    st.subheader("Summary")
    col1, col2 = st.columns(2)
    col1.metric("Total Invested", f"₹{df['Invested'].sum():,.0f}")
    col2.metric("Total P&L", f"₹{df['P&L'].sum():,.0f}")

    st.info("This page shows your holdings with live P&L and current value. P&L is Current Value minus Invested.")
