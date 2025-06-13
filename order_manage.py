import streamlit as st
from utils import integrate_get

def show():
    st.header("Orders Book & Manage")
    data = integrate_get("/orders")

    st.subheader("Raw API Response")
    st.json(data)

    orderlist = data.get("orders", []) or data.get("orderBookDetail", []) or data.get("data", []) or []
    st.write(f"Orders found: {len(orderlist)}")
    if not orderlist:
        st.info("No orders array found in API response.")
        return

    # Print one order to find the status key
    st.write("First order object:", orderlist[0])

    # Try all possible status keys (update after you check above)
    def get_status(o):
        return o.get("order_status", "").upper()   # CHANGE THIS LINE after inspecting the real data

    statuses = set([get_status(o) for o in orderlist])
    st.write("Statuses found in orders:", statuses)

    open_statuses = {"OPEN", "PARTIALLY FILLED", "PARTIALLY_FILLED"}  # Adjust as needed

    open_orders = [o for o in orderlist if get_status(o) in open_statuses]
    st.write(f"Open/Partial orders found: {len(open_orders)}")
    for order in open_orders:
        st.json(order)

    if not open_orders:
        st.info("No open/partial orders found after filtering. Adjust filter as needed.")
