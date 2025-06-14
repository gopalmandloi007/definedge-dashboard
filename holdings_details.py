import streamlit as st
import pandas as pd
import plotly.express as px
from utils import integrate_get

def show():
    st.title("Holdings Details Dashboard")

    # --- Fetch holdings data ---
    data = integrate_get("/holdings")
    holdings = data.get("data", [])
    if not holdings:
        st.warning("No holdings found.")
        return

    # --- Prepare DataFrame with all details ---
    rows = []
    for h in holdings:
        # --- Robust symbol extraction ---
        ts = h.get("tradingsymbol")
        if isinstance(ts, list):
            if ts:
                if isinstance(ts[0], dict):
                    tsym = ts[0].get("tradingsymbol", "N/A")
                else:
                    tsym = str(ts[0])
            else:
                tsym = "N/A"
        elif isinstance(ts, dict):
            tsym = ts.get("tradingsymbol", "N/A")
        else:
            tsym = str(ts) if ts is not None else "N/A"

        exch = h.get("exchange", "NSE")
        isin = h.get("isin", "")
        product = h.get("product", "")
        qty = float(h.get("dp_qty", 0) or 0)
        avg_buy = float(h.get("avg_buy_price", 0) or 0)
        invested = avg_buy * qty

        # Try to get last traded price (LTP), fallback to current_price or 0
        ltp = float(h.get("ltp", h.get("current_price", 0)) or 0)
        current_value = ltp * qty
        pnl = current_value - invested

        rows.append({
            "Symbol": tsym,
            "Exchange": exch,
            "ISIN": isin,
            "Product": product,
            "Qty": qty,
            "Avg Buy": avg_buy,
            "Invested": invested,
            "Current Price": ltp,
            "Current Value": current_value,
            "P&L": pnl,
            "DP Free Qty": h.get("dp_free_qty", ""),
            "Pledge Qty": h.get("pledge_qty", ""),
            "Collateral Qty": h.get("collateral_qty", ""),
            "T1 Qty": h.get("t1_qty", ""),
        })

    df = pd.DataFrame(rows)
    if df.empty:
        st.warning("No active holdings with quantity > 0.")
        return

    # --- Capital Management (Top section, fixed capital) ---
    TOTAL_CAPITAL = 650000.0
    total_invested = df["Invested"].sum()
    cash_in_hand = max(TOTAL_CAPITAL - total_invested, 0)
    allocation_percent = (total_invested / TOTAL_CAPITAL * 100) if TOTAL_CAPITAL else 0

    st.subheader("💰 Capital Management")
    colA, colB, colC = st.columns(3)
    colA.metric("Total Capital", f"₹{TOTAL_CAPITAL:,.0f}")
    colB.metric("Invested", f"₹{total_invested:,.0f}", f"{allocation_percent:.1f}%")
    colC.metric("Cash in Hand", f"₹{cash_in_hand:,.0f}")

    # --- Pie Chart: Allocation ---
    st.subheader("Portfolio Allocation Pie")
    fig = px.pie(
        df,
        names="Symbol",
        values="Invested",
        title="Allocation by Stock",
        hole=0.3
    )
    fig.update_traces(textinfo='label+percent')
    st.plotly_chart(fig, use_container_width=True)

    # --- Main Holdings Table with all columns and P&L color ---
    st.subheader("Holdings Details Table")
    st.dataframe(
        df.style.applymap(
            lambda x: "background-color:#c6f5c6" if isinstance(x, (int, float)) and x > 0 else ("background-color:#ffcccc" if isinstance(x, (int, float)) and x < 0 else ""),
            subset=["P&L"]
        ),
        use_container_width=True,
    )

    # --- Totals Summary ---
    st.subheader("Summary")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Invested", f"₹{df['Invested'].sum():,.0f}")
    col2.metric("Total Current Value", f"₹{df['Current Value'].sum():,.0f}")
    col3.metric("Total P&L", f"₹{df['P&L'].sum():,.0f}")
    col4.metric("Total Qty", f"{df['Qty'].sum():,.0f}")

    st.info("Saare symbol ab clearly dikhenge. Agar fir bhi object aaye toh API data format bhejein.")
