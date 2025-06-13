import streamlit as st
from utils import integrate_get, integrate_post
import requests

def show():
    st.header("GTT / OCO Orders Book & Manage")

    # --- GTT Order Book Section ---
    st.subheader("GTT Order Book")
    data = integrate_get("/gttorders")
    gttlist = data.get("pendingGTTOrderBook", [])
    if gttlist:
        for order in gttlist:
            st.markdown(f"**GTT:** {order.get('tradingsymbol', '')} ({order.get('alert_id', '')}) | {order.get('order_type', '')} @ {order.get('alert_price', 0)} | Qty: {order.get('quantity', 1)}")
    else:
        st.info("No pending GTT orders.")

    st.markdown("---")

    # --- OCO Order Book Section ---
    st.subheader("OCO Order Book")
    # Try /ocoorders first. If 404 or empty, fallback to main /orders endpoint and filter for OCOs.
    ocolist = []
    oco_error = None
    try:
        data = integrate_get("/ocoorders")
        ocolist = data.get("pendingOCOOrderBook", [])
    except Exception as e:
        oco_error = e
        ocolist = []

    # Fallback to /orders if ocolist is empty
    if not ocolist:
        try:
            data = integrate_get("/orders")
            st.write("All Orders Response:", data)  # <-- REMOVE after identifying structure!
            all_orders = data.get("orders", [])
            # Adjust this filter as per your actual OCO fields!
            ocolist = [
                o for o in all_orders
                if str(o.get("order_type", "")).upper() == "OCO"
                or o.get("oco_flag") is True
                or o.get("oco_leg1") is not None
                or o.get("oco_leg2") is not None
            ]
        except Exception as e:
            oco_error = e
            ocolist = []

    if ocolist:
        for order in ocolist:
            st.markdown(f"**OCO:** {order.get('tradingsymbol', '')} ({order.get('alert_id', order.get('order_id', ''))}) | {order.get('order_type', '')}")
            st.json(order)
    else:
        if oco_error:
            st.error(f"Could not fetch OCO orders: {oco_error}")
        else:
            st.info("No pending OCO orders.")
