import streamlit as st
from utils import integrate_get

def show_oco_orders():
    st.subheader("OCO Order Book")
    # Fetch all orders from /orders
    data = integrate_get("/orders")
    all_orders = data.get("orders", [])
    # Filter for OCO orders (adjust filter as per your API response)
    oco_orders = [
        o for o in all_orders
        if str(o.get("order_type", "")).upper() == "OCO"
        or o.get("target_price")  # many OCOs have target/stoploss fields
        or o.get("oco_flag")
    ]
    if oco_orders:
        for order in oco_orders:
            st.write(
                f"OCO: {order.get('tradingsymbol', '')} | "
                f"Target: {order.get('target_price', '')} | "
                f"Stoploss: {order.get('stoploss_price', '')} | "
                f"Order ID: {order.get('order_id', '')}"
            )
    else:
        st.info("No pending OCO orders.")

# Call show_oco_orders() in your Streamlit app where needed
