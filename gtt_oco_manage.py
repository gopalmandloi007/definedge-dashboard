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
            with st.expander(f"GTT: {order['tradingsymbol']} ({order['alert_id']}) | {order['order_type']} @ {order['alert_price']} | Qty: {order['quantity']}"):
                st.json(order)
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Modify", key=f"gtt_mod_{order['alert_id']}"):
                        with st.form(f"gtt_mod_form_{order['alert_id']}"):
                            condition = st.radio(
                                "Condition",
                                ["LTP_ABOVE", "LTP_BELOW"],
                                horizontal=True,
                                index=0 if order['condition'] == "LTP_ABOVE" else 1
                            )
                            alert_price = st.number_input("Alert Price", value=float(order['alert_price']))
                            price = st.number_input("Order Price", value=float(order.get('price', 0)))
                            quantity = st.number_input("Quantity", value=int(order['quantity']), step=1)
                            product_type = st.radio(
                                "Product Type",
                                ["CNC", "INTRADAY", "NORMAL"],
                                horizontal=True,
                                index=0 if order.get('product_type', 'CNC') == "CNC" else (1 if order.get('product_type', 'CNC') == "INTRADAY" else 2)
                            )
                            submit_mod = st.form_submit_button("Confirm Modify")
                            if submit_mod:
                                payload = {
                                    "exchange": order['exchange'],
                                    "alert_id": order['alert_id'],
                                    "tradingsymbol": order['tradingsymbol'],
                                    "condition": condition,
                                    "alert_price": str(alert_price),
                                    "order_type": order['order_type'],
                                    "quantity": str(quantity),
                                    "price": str(price),
                                    "product_type": product_type
                                }
                                resp = integrate_post("/gttmodify", payload)
                                st.success("Modify response:")
                                st.json(resp)
                with col2:
                    if st.button("Cancel", key=f"gtt_cancel_{order['alert_id']}"):
                        api_session_key = st.secrets.get("integrate_api_session_key", "")
                        url = f"https://integrate.definedgesecurities.com/dart/v1/gttcancel/{order['alert_id']}"
                        headers = {"Authorization": api_session_key}
                        resp = requests.get(url, headers=headers)
                        st.success("Cancel response:")
                        st.json(resp.json())
    else:
        st.info("No pending GTT orders.")

    # --- OCO Order Book Section ---
    st.subheader("OCO Order Book")
    # NOTE: Your backend should provide /ocoorders and pendingOCOOrderBook for this to work.
    data = integrate_get("/ocoorders")
    ocolist = data.get("pendingOCOOrderBook", [])
    if ocolist:
        for order in ocolist:
            with st.expander(f"OCO: {order['tradingsymbol']} ({order['alert_id']}) | {order['order_type']}"):
                st.json(order)
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Modify", key=f"oco_mod_{order['alert_id']}"):
                        with st.form(f"oco_mod_form_{order['alert_id']}"):
                            target_price = st.number_input("Target Price", value=float(order.get('target_price', 0)), key=f"oco_tg_{order['alert_id']}")
                            stoploss_price = st.number_input("Stoploss Price", value=float(order.get('stoploss_price', 0)), key=f"oco_sl_{order['alert_id']}")
                            target_qty = st.number_input("Target Quantity", value=int(order.get('target_quantity', 1)), step=1, key=f"oco_tq_{order['alert_id']}")
                            stoploss_qty = st.number_input("Stoploss Quantity", value=int(order.get('stoploss_quantity', 1)), step=1, key=f"oco_sq_{order['alert_id']}")
                            product_type = st.radio(
                                "Product Type",
                                ["CNC", "INTRADAY", "NORMAL"],
                                horizontal=True,
                                index=0 if order.get('product_type', 'CNC') == "CNC" else (1 if order.get('product_type', 'CNC') == "INTRADAY" else 2)
                            )
                            remarks = st.text_input("Remarks", value=order.get('remarks', ''), key=f"oco_rem_{order['alert_id']}")
                            submit_mod = st.form_submit_button("Confirm Modify")
                            if submit_mod:
                                payload = {
                                    "remarks": remarks,
                                    "tradingsymbol": order['tradingsymbol'],
                                    "exchange": order['exchange'],
                                    "order_type": order['order_type'],
                                    "target_quantity": str(target_qty),
                                    "stoploss_quantity": str(stoploss_qty),
                                    "target_price": str(target_price),
                                    "stoploss_price": str(stoploss_price),
                                    "alert_id": order['alert_id'],
                                    "product_type": product_type
                                }
                                resp = integrate_post("/ocomodify", payload)
                                st.success("Modify response:")
                                st.json(resp)
                with col2:
                    if st.button("Cancel", key=f"oco_cancel_{order['alert_id']}"):
                        api_session_key = st.secrets.get("integrate_api_session_key", "")
                        url = f"https://integrate.definedgesecurities.com/dart/v1/ococancel/{order['alert_id']}"
                        headers = {"Authorization": api_session_key}
                        resp = requests.get(url, headers=headers)
                        st.success("Cancel response:")
                        st.json(resp.json())
    else:
        st.info("No pending OCO orders.")
