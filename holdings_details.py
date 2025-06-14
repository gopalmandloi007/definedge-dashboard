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
        # Extract symbol robustly
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
        entry = float(h.get("avg_buy_price", 0) or 0)
        invested = entry * qty

        ltp = h.get("ltp", None)
        try:
            ltp = float(ltp) if ltp is not None else None
        except:
            ltp = None

        # Calculate P&L only if LTP is available and >0
        if ltp and ltp > 0:
            current_value = ltp * qty
            pnl = current_value - invested
        else:
            current_value = ""
            pnl = ""

        # --- TRAILING STOP LOSS LOGIC ---
        # Initial SL
        initial_sl = round(entry * 0.97, 2)
        status = "Initial SL"
        trailing_sl = initial_sl

        if ltp and ltp > 0:
            change_pct = 100 * (ltp - entry) / entry if entry else 0
            # Trailing SL steps
            if change_pct >= 30:
                trailing_sl = round(entry * 1.20, 2)
                status = "Excellent Profit (SL at Entry +20%)"
            elif change_pct >= 20:
                trailing_sl = round(entry * 1.10, 2)
                status = "Good Profit (SL at Entry +10%)"
            elif change_pct >= 10:
                trailing_sl = round(entry, 2)
                status = "Safe (Breakeven SL)"
        else:
            change_pct = ""

        # Open Risk
        open_risk = (trailing_sl - entry) * qty

        rows.append({
            "Symbol": tsym,
            "Exchange": exch,
            "ISIN": isin,
            "Product": product,
            "Qty": qty,
            "Entry": entry,
            "Invested": invested,
            "Current Price": ltp if ltp and ltp > 0 else "",
            "Current Value": current_value,
            "P&L": pnl,
            "Change %": round(change_pct, 2) if change_pct != "" else "",
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
    total_invested = df["Invested"].sum()
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
            lambda x: "background-color:#c6f5c6" if isinstance(x, (int, float)) and x > 0 else ("background-color:#ffcccc" if isinstance(x, (int, float)) and x < 0 else ""),
            subset=["P&L", "Open Risk"]
        ),
        use_container_width=True,
    )

    # --- Totals Summary ---
    st.subheader("Summary")
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Total Invested", f"₹{df['Invested'].sum():,.0f}")
    col2.metric("Total Current Value", f"₹{df['Current Value'].replace('', 0).sum():,.0f}")
    col3.metric("Total P&L", f"₹{df['P&L'].replace('', 0).sum():,.0f}")
    col4.metric("Total Qty", f"{df['Qty'].sum():,.0f}")
    col5.metric("Total Open Risk", f"₹{df['Open Risk'].sum():,.0f}")

    st.info(
        "Trailing Stop Loss logic: "
        "Initial SL = Entry - 3%. "
        "If gain >10%, SL moves to Entry (Safe). "
        "If gain >20%, SL = Entry +10% (Good Profit). "
        "If gain >30%, SL = Entry +20% (Excellent Profit)."
    )
