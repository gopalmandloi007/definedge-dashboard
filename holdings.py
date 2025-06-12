import streamlit as st
import pandas as pd
from utils import get_integrate_client

def show():
    st.header("💼 Holdings & Positions (Live)")

    try:
        conn, io = get_integrate_client()
    except Exception as e:
        st.error(f"API client error: {e}")
        st.stop()

    # Fetch holdings
    try:
        holdings_data = io.holdings()
        data = holdings_data.get("data", [])
    except Exception as e:
        st.error(f"Failed to retrieve holdings: {e}")
        return

    if not data:
        st.info("No holdings found.")
    else:
        st.subheader("📊 Holdings Overview")
        table = []
        for h in data:
            # Use only NSE for this summary
            for ts in h.get("tradingsymbol", []):
                if ts.get("exchange") != "NSE":
                    continue
                qty = float(h.get("dp_qty", 0) or 0)
                avg_buy = float(h.get("avg_buy_price", 0) or 0)
                symbol = ts.get("tradingsymbol", "N/A")
                invested = qty * avg_buy
                # LTP not available directly: mark as N/A, or integrate get_definedge_ltp_and_yclose if needed
                ltp = None
                current = ltp * qty if ltp is not None else None
                pnl = (ltp - avg_buy) * qty if ltp is not None else None
                pct = 100 * pnl / invested if ltp is not None and invested else None
                table.append({
                    "Symbol": symbol,
                    "Qty": int(qty),
                    "Avg Buy": avg_buy,
                    "Invested": invested,
                    "LTP": ltp if ltp is not None else "N/A",
                    "Current": current if current is not None else "N/A",
                    "P&L": pnl if pnl is not None else "N/A",
                    "% Change": f"{pct:.2f}%" if pct is not None else "N/A",
                    "Exchange": ts.get("exchange", ""),
                    "ISIN": ts.get("isin", ""),
                })
        df = pd.DataFrame(table)
        # Attractively format
        if not df.empty:
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Invested", f"₹{df['Invested'].sum():,.0f}")
            if df['Current'].dtype != object:
                col2.metric("Current Value", f"₹{df['Current'].sum():,.0f}")
                total_pnl = df['P&L'].sum()
            else:
                col2.metric("Current Value", "N/A")
                total_pnl = "N/A"
            col3.metric("Overall P&L", f"₹{total_pnl:,.0f}" if total_pnl != "N/A" else "N/A")
            # Color formatting
            def highlight_pnl(val):
                if isinstance(val, (int, float)):
                    color = "green" if val > 0 else "red" if val < 0 else "black"
                    return f"color: {color}; font-weight: bold"
                return ""
            st.dataframe(
                df.style.applymap(highlight_pnl, subset=["P&L"]).format({"Avg Buy": "₹{:.2f}", "Invested": "₹{:.2f}", "Current": "₹{:.2f}", "P&L": "₹{:.2f}"}),
                use_container_width=True,
            )
        else:
            st.info("No NSE holdings found.")

    # Fetch positions
    try:
        positions_data = io.positions()
        positions = positions_data.get("positions", [])
    except Exception as e:
        st.error(f"Failed to retrieve positions: {e}")
        return

    st.subheader("📈 Positions")
    if not positions:
        st.info("No positions found.")
    else:
        pos_table = []
        for p in positions:
            pos_table.append({
                "Symbol": p.get("tradingsymbol", ""),
                "Qty": p.get("net_quantity", ""),
                "Avg Price": p.get("net_averageprice", ""),
                "Last Price": p.get("lastPrice", ""),
                "Unrealised P&L": p.get("unrealized_pnl", ""),
                "Realised P&L": p.get("realized_pnl", ""),
                "Product": p.get("product_type", ""),
            })
        df_pos = pd.DataFrame(pos_table)
        st.dataframe(df_pos.style.format({"Avg Price": "₹{:.2f}", "Last Price": "₹{:.2f}", "Unrealised P&L": "₹{:.2f}", "Realised P&L": "₹{:.2f}"}), use_container_width=True)
