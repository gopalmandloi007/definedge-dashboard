import streamlit as st
from utils import integrate_get, integrate_post
import requests

def show():
    st.header("Orders Book & Manage")

    # --- Orders Book Section ---
    st.subheader("Order Book (Open/Partially Filled)")
    # Your API endpoint may differ, adjust if needed
    data = integrate_get("/orderbook")
    orderlist = data.get("orderBookDetail", [])
    if orderlist:
        for order in orderlist:
            order_status = order.get("status", "").upper()
            if order_status not in ["OPEN", "PARTIALLY FILLED", "PARTIALLY_FILLED"]:
                continue

            with st.expander(
                f"Order: {order.get('tradingsymbol', '')} ({order.get('order_id', '')}) | "
                f"{order.get('order_type', '')} @ {order.get('price', 0)} | Qty: {order.get('quantity', 1)} | Status: {order_status}"
            ):
                st.json(order)
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Modify", key=f"ord_mod_{order.get('order_id', '')}"):
                        with st.form(f"ord_mod_form_{order.get('order_id', '')}"):
                            price_type = st.radio(
                                "Price Type",
                                ["LIMIT", "MARKET", "SL-LIMIT", "SL-MARKET"],
                                horizontal=True,
                                index=["LIMIT", "MARKET", "SL-LIMIT", "SL-MARKET"].index(order.get('price_type', 'LIMIT').upper())
                                if order.get('price_type', 'LIMIT').upper() in ["LIMIT", "MARKET", "SL-LIMIT", "SL-MARKET"] else 0
                            )
                            price = st.number_input("Price", value=float(order.get('price', 0)))
                            quantity = st.number_input("Quantity", value=int(order.get('quantity', 1)), step=1)
                            disclosed_quantity = st.number_input("Disclosed Quantity", value=int(order.get('disclosed_quantity', 0)), step=1)
                            trigger_price = st.number_input("Trigger Price", value=float(order.get('trigger_price', 0)))
                            product_type = st.radio(
                                "Product Type",
                                ["CNC", "INTRADAY", "NORMAL"],
                                horizontal=True,
                                index=0 if order.get('product_type', 'CNC') == "CNC" else (1 if order.get('product_type', 'CNC') == "INTRADAY" else 2)
                            )
                            validity = st.radio(
                                "Validity",
                                ["DAY", "EOS", "IOC"],
                                horizontal=True,
                                index=["DAY", "EOS", "IOC"].index(order.get('validity', 'DAY')) if order.get('validity', 'DAY') in ["DAY", "EOS", "IOC"] else 0
                            )
                            remarks = st.text_input("Remarks", value=order.get('remarks', ''))
                            market_protection = st.number_input("Market Protection (%)", value=float(order.get('market_protection', 0)))
                            submit_mod = st.form_submit_button("Confirm Modify")
                            if submit_mod:
                                payload = {
                                    "exchange": order.get('exchange', ''),
                                    "order_id": order.get('order_id', ''),
                                    "tradingsymbol": order.get('tradingsymbol', ''),
                                    "quantity": str(quantity),
                                    "price": str(price),
                                    "product_type": product_type,
                                    "order_type": order.get('order_type', ''),
                                    "price_type": price_type,
                                }
                                # Optional fields
                                if disclosed_quantity:
                                    payload["disclosed_quantity"] = str(disclosed_quantity)
                                if trigger_price:
                                    payload["trigger_price"] = str(trigger_price)
                                if remarks:
                                    payload["remarks"] = remarks
                                if validity:
                                    payload["validity"] = validity
                                if market_protection:
                                    payload["market_protection"] = str(market_protection)
                                resp = integrate_post("/modify", payload)
                                st.success("Modify response:")
                                st.json(resp)
                with col2:
                    if st.button("Cancel", key=f"ord_cancel_{order.get('order_id', '')}"):
                        api_session_key = st.secrets.get("integrate_api_session_key", "")
                        url = f"https://integrate.definedgesecurities.com/dart/v1/cancel/{order.get('order_id', '')}"
                        headers = {"Authorization": api_session_key}
                        resp = requests.get(url, headers=headers)
                        st.success("Cancel response:")
                        st.json(resp.json())
    else:
        st.info("No open/partial orders found.")
