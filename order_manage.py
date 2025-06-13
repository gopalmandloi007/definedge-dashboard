import streamlit as st
from utils import integrate_get

def show():
    st.header("Orders Book & Manage")
    data = integrate_get("/orders")  # or your actual endpoint

    st.subheader("Raw API Response")
    st.json(data)

    # Try all possible keys
    orderlist = data.get("orders", []) or data.get("orderBookDetail", []) or data.get("data", []) or []
    st.write(f"Orders found: {len(orderlist)}")
    if not orderlist:
        st.info("No orders array found in API response.")
        return

    # Show all unique statuses
    statuses = set([o.get("status", "").upper() for o in orderlist])
    st.write("Statuses found in orders:", statuses)

    open_statuses = {"OPEN", "PARTIALLY FILLED", "PARTIALLY_FILLED"}  # Update this after you see correct values

    open_orders = [o for o in orderlist if o.get("status", "").upper() in open_statuses]
    st.write(f"Open/Partial orders found: {len(open_orders)}")
    for order in open_orders:
        st.json(order)

    if not open_orders:
        st.info("No open/partial orders found after filtering. Adjust filter as needed.")
