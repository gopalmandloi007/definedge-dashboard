import streamlit as st
import pandas as pd
from utils import get_integrate_client

def show():
    st.header("Order Book")
    conn, io = get_integrate_client()

    orders = io.get_order_book()
    if not orders:
        st.info("No orders found.")
        return
    df = pd.DataFrame(orders)
    show_cols = ["order_id", "tradingsymbol", "order_type", "quantity", "price_type", "price", "order_status", "order_entry_time"]
    st.dataframe(df[show_cols], use_container_width=True)
    idx = st.selectbox("Select order to modify/cancel", options=list(range(len(df))), format_func=lambda x: f"{df.iloc[x]['tradingsymbol']} ({df.iloc[x]['order_id']})" if len(df) else "")
    selected = df.iloc[idx]
    st.write(selected)

    st.subheader("Modify Order")
    with st.form("modify_order_form"):
        side = st.selectbox("Side", ["BUY", "SELL"], index=0 if selected["order_type"]=="BUY" else 1)
        qty = st.number_input("Quantity", min_value=1, value=int(selected["quantity"]))
        price_type = st.selectbox("Order Type", ["LIMIT", "MARKET"], index=0 if selected["price_type"].startswith("L") else 1)
        price = st.number_input("Price", min_value=0.0, value=float(selected["price"]))
        submitted = st.form_submit_button("Modify Order")
        if submitted:
            try:
                resp = io.modify_order(
                    order_id=selected["order_id"],
                    tradingsymbol=selected["tradingsymbol"],
                    order_type=side,
                    quantity=int(qty),
                    price_type=price_type,
                    price=float(price),
                    exchange=selected["exchange"],
                    product_type=selected.get("product_type", conn.PRODUCT_TYPE_CNC)
                )
                st.success(f"Order Modified: {resp}")
            except Exception as e:
                st.error(f"Failed: {e}")

    if st.button("Cancel This Order"):
        try:
            resp = io.cancel_order(order_id=selected["order_id"])
            st.success(f"Order Cancelled: {resp}")
        except Exception as e:
            st.error(f"Cancel failed: {e}")
