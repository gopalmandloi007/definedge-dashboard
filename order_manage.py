import streamlit as st
from utils import integrate_get, integrate_post
import requests

def show():
    st.header("Orders Book & Manage")

    # Use the correct endpoint (try '/orders' if '/orderbook' gives 404)
    try:
        data = integrate_get("/orders")  # <-- Change here!
    except Exception as e:
        st.error(f"Failed to fetch order book: {e}")
        return

    orderlist = data.get("orderBookDetail", []) or data.get("orders", []) or data.get("data", []) or []
    refreshed = st.button("🔄 Refresh Orders", use_container_width=True)
    if refreshed:
        st.rerun()  # <-- Change here!

    if orderlist:
        open_orders = [
            order for order in orderlist
            if order.get("status", "").upper() in ["OPEN", "PARTIALLY FILLED", "PARTIALLY_FILLED"]
        ]
        if not open_orders:
            st.info("No open/partial orders found.")
            return

        for order in open_orders:
            order_id = order.get("order_id", "")
            symbol = order.get('tradingsymbol', '')
            order_type = order.get('order_type', '')
            price = order.get('price', 0)
            qty = order.get('quantity', 1)
            status = order.get('status', '').upper()

            with st.expander(
                f"{symbol} ({order_id}) | {order_type} @ {price} | Qty: {qty} | Status: {status}"
            ):
                st.json(order)
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("#### Modify Order")
                    with st.form(f"ord_mod_form_{order_id}", clear_on_submit=True):
                        price_type = st.radio(
                            "Price Type",
                            ["LIMIT", "MARKET", "SL-LIMIT", "SL-MARKET"],
                            horizontal=True,
                            index=["LIMIT", "MARKET", "SL-LIMIT", "SL-MARKET"].index(order.get('price_type', 'LIMIT').upper())
                            if order.get('price_type', 'LIMIT').upper() in ["LIMIT", "MARKET", "SL-LIMIT", "SL-MARKET"] else 0
                        )
                        price = st.number_input("Price", value=float(order.get('price', 0)), min_value=0.0)
                        quantity = st.number_input("Quantity", value=int(order.get('quantity', 1)), step=1, min_value=1)
                        disclosed_quantity = st.number_input("Disclosed Quantity", value=int(order.get('disclosed_quantity', 0)), step=1, min_value=0)
                        trigger_price = st.number_input("Trigger Price", value=float(order.get('trigger_price', 0)), min_value=0.0)
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
                        market_protection = st.number_input("Market Protection (%)", value=float(order.get('market_protection', 0)), min_value=0.0)
                        submit_mod = st.form_submit_button("Confirm Modify")
                        if submit_mod:
                            payload = {
                                "exchange": order.get('exchange', ''),
                                "order_id": order_id,
                                "tradingsymbol": symbol,
                                "quantity": str(quantity),
                                "price": str(price),
                                "product_type": product_type,
                                "order_type": order_type,
                                "price_type": price_type,
                            }
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
                            if resp.get("status") == "ERROR":
                                st.error(f"Modify Failed: {resp.get('message','Error')}")
                            else:
                                st.success("Order modification submitted!")
                                st.json(resp)
                            st.rerun()
                with col2:
                    st.markdown("#### Cancel Order")
                    if st.button("Cancel", key=f"ord_cancel_{order_id}"):
                        api_session_key = st.secrets.get("integrate_api_session_key", "")
                        url = f"https://integrate.definedgesecurities.com/dart/v1/cancel/{order_id}"
                        headers = {"Authorization": api_session_key}
                        resp = requests.get(url, headers=headers)
                        try:
                            result = resp.json()
                        except Exception:
                            result = {"status": "ERROR", "message": "Invalid API response"}
                        if result.get("status") == "ERROR":
                            st.error(f"Cancel Failed: {result.get('message','Error')}")
                        else:
                            st.success("Order cancelled!")
                            st.json(result)
                        st.rerun()
    else:
        st.info("No open/partial orders found.")
