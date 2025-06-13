import streamlit as st
from utils import integrate_get, integrate_post
import requests

def oco_modify_form(order):
    unique_id = f"oco_{order.get('order_id', order.get('alert_id', ''))}"
    st.markdown("---")
    st.subheader(f"Modify OCO: {order.get('tradingsymbol', '')} ({unique_id})")
    with st.form(f"oco_mod_form_{unique_id}"):
        target_price = st.number_input("Target Price", value=float(order.get('target_price', order.get('price', 0))))
        stoploss_price = st.number_input("Stoploss Price", value=float(order.get('stoploss_price', 0)))
        target_qty = st.number_input("Target Quantity", value=int(order.get('target_quantity', order.get('quantity', 1))), step=1)
        stoploss_qty = st.number_input("Stoploss Quantity", value=int(order.get('stoploss_quantity', 1)), step=1)
        product_type = st.radio("Product Type", ["CNC", "INTRADAY", "NORMAL"], horizontal=True,
                                index=0 if order.get('product_type', 'CNC') == "CNC" else (1 if order.get('product_type', 'CNC') == "INTRADAY" else 2))
        remarks = st.text_input("Remarks", value=order.get('remarks', ''))
        submit_mod = st.form_submit_button("Confirm Modify")
        if submit_mod:
            payload = {
                "remarks": remarks,
                "tradingsymbol": order.get('tradingsymbol', ''),
                "exchange": order.get('exchange', ''),
                "order_type": order.get('order_type', ''),
                "target_quantity": str(target_qty),
                "stoploss_quantity": str(stoploss_qty),
                "target_price": str(target_price),
                "stoploss_price": str(stoploss_price),
                "alert_id": order.get('alert_id', order.get('order_id', '')),
                "product_type": product_type
            }
            resp = integrate_post("/ocomodify", payload)
            status = resp.get('status') or resp.get('message') or resp
            if resp.get("status") == "ERROR":
                st.error(f"Modify Failed: {resp.get('message','Error')}")
            else:
                st.success(f"Modify Response: {status}")
            st.session_state["oco_mod_id"] = None
            st.rerun()

def show_oco_orders():
    st.subheader("OCO Order Book")
    oco_mod_id = st.session_state.get("oco_mod_id", None)
    # Fetch all orders
    data = integrate_get("/orders")
    all_orders = data.get("orders", [])
    # Filter for OCO orders (adjust this filter if you find a better flag/field in your data)
    oco_orders = [
        o for o in all_orders
        if str(o.get("order_type", "")).upper() == "OCO"
        or o.get("oco_flag")
        or o.get("target_price")  # Many OCOs have target/stoploss fields
    ]
    if oco_orders:
        oco_labels = ["Symbol", "Type", "Target Price", "Stoploss Price", "Target Qty", "Stoploss Qty", "Product", "Modify", "Cancel"]
        cols = st.columns([1.5, 1.2, 1.2, 1.2, 1, 1, 1.2, 1.2, 1.2])
        for i, l in enumerate(oco_labels):
            cols[i].markdown(f"**{l}**")
        for idx, order in enumerate(oco_orders):
            cols = st.columns([1.5, 1.2, 1.2, 1.2, 1, 1, 1.2, 1.2, 1.2])
            cols[0].write(order.get('tradingsymbol', ''))
            cols[1].write(order.get('order_type', ''))
            cols[2].write(order.get('target_price', order.get('price', '')))
            cols[3].write(order.get('stoploss_price', ''))
            cols[4].write(order.get('target_quantity', order.get('quantity', '')))
            cols[5].write(order.get('stoploss_quantity', ''))
            cols[6].write(order.get('product_type', ''))
            this_oid = order.get('order_id', order.get('alert_id', idx))
            if cols[7].button("Modify", key=f"oco_mod_btn_{this_oid}"):
                st.session_state["oco_mod_id"] = this_oid
                st.rerun()
            if cols[8].button("Cancel", key=f"oco_cancel_btn_{this_oid}"):
                api_session_key = st.secrets.get("integrate_api_session_key", "")
                url = f"https://integrate.definedgesecurities.com/dart/v1/ococancel/{this_oid}"
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
                st.rerun()
            if oco_mod_id == this_oid:
                oco_modify_form(order)
    else:
        st.info("No pending OCO orders.")

# In your main show() function, call show_oco_orders() where you want to show the OCO Order Book
