import streamlit as st
import pandas as pd
from utils import get_integrate_client

def show():
    st.header("Holdings & Positions (Live)")
    conn, io = get_integrate_client()

    # Holdings
    st.subheader("Holdings")
    holdings = io.get_holdings()
    if not holdings:
        st.info("No holdings found.")
    else:
        df = pd.DataFrame(holdings)
        show_cols = ["tradingsymbol", "exchange", "quantity", "avg_buy_price", "current_price", "pnl_today", "pnl_overall", "current_value", "invested_value"]
        # Calculate extra columns if not present
        df["current_value"] = df["quantity"] * df["current_price"]
        df["invested_value"] = df["quantity"] * df["avg_buy_price"]
        df["pnl_overall"] = df["current_value"] - df["invested_value"]
        df["%change"] = 100 * df["pnl_overall"] / df["invested_value"]
        st.dataframe(df[show_cols + ["%change"]], use_container_width=True)
        idx = st.selectbox("Select holding to square off", options=list(range(len(df))), format_func=lambda x: f"{df.iloc[x]['tradingsymbol']} ({df.iloc[x]['quantity']})" if len(df) else "")
        if st.button("Square Off Selected Holding (Market)"):
            row = df.iloc[idx]
            try:
                resp = io.place_order(
                    tradingsymbol=row["tradingsymbol"],
                    exchange=row["exchange"],
                    order_type=conn.ORDER_TYPE_SELL,
                    quantity=int(row["quantity"]),
                    price=0,
                    price_type=conn.PRICE_TYPE_MARKET,
                    product_type=conn.PRODUCT_TYPE_CNC
                )
                st.success(f"Square off order placed: {resp}")
            except Exception as e:
                st.error(f"Failed to square off: {e}")

    # Positions
    st.subheader("Positions")
    positions = io.get_positions()
    if not positions:
        st.info("No positions found.")
    else:
        df = pd.DataFrame(positions)
        show_cols = ["tradingsymbol", "exchange", "net_quantity", "net_avg_price", "ltp", "pnl_today", "realized_pnl", "unrealized_pnl"]
        st.dataframe(df[show_cols], use_container_width=True)
        idx = st.selectbox("Select position to square off", options=list(range(len(df))), format_func=lambda x: f"{df.iloc[x]['tradingsymbol']} ({df.iloc[x]['net_quantity']})" if len(df) else "", key="pos_sqoff")
        if st.button("Square Off Selected Position (Market)"):
            row = df.iloc[idx]
            try:
                resp = io.place_order(
                    tradingsymbol=row["tradingsymbol"],
                    exchange=row["exchange"],
                    order_type=conn.ORDER_TYPE_SELL if row["net_quantity"] > 0 else conn.ORDER_TYPE_BUY,
                    quantity=abs(int(row["net_quantity"])),
                    price=0,
                    price_type=conn.PRICE_TYPE_MARKET,
                    product_type=row.get("product_type", conn.PRODUCT_TYPE_CNC)
                )
                st.success(f"Square off order placed: {resp}")
            except Exception as e:
                st.error(f"Failed to square off: {e}")
