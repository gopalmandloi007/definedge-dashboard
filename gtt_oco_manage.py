import streamlit as st
from utils import integrate_get, integrate_post
import requests

def gtt_modify_form(order):
    unique_id = f"gtt_{order.get('alert_id', '')}"
    st.markdown("---")
    st.subheader(f"Modify GTT: {order.get('tradingsymbol', '')} ({order.get('alert_id', '')})")
    with st.form(f"gtt_mod_form_{unique_id}"):
        condition = st.radio(
            "Condition",
            ["LTP_ABOVE", "LTP_BELOW"],
            horizontal=True,
            index=0 if order.get('condition', 'LTP_ABOVE') == "LTP_ABOVE" else 1,
            key=f"gtt_cond_{unique_id}"
        )
        alert_price = st.number_input("Alert Price", value=float(order.get('alert_price', 0)), key=f"gtt_ap_{unique_id}")
        price = st.number_input("Order Price", value=float(order.get('price', 0)), key=f"gtt_op_{unique_id}")
        quantity = st.number_input("Quantity", value=int(order.get('quantity', 1)), step=1, key=f"gtt_qty_{unique_id}")
        product_type = st.radio(
            "Product Type",
            ["CNC", "INTRADAY", "NORMAL"],
            horizontal=True,
            index=0 if order.get('product_type', 'CNC') == "CNC" else (1 if order.get('product_type', 'CNC') == "INTRADAY" else 2),
            key=f"gtt_pt_{unique_id}"
        )
        submit_mod = st.form_submit_button("Confirm Modify")
        if submit_mod:
            payload = {
                "exchange": order.get('exchange', ''),
                "alert_id": order.get('alert_id', ''),
                "tradingsymbol": order.get('tradingsymbol', ''),
                "condition": condition,
                "alert_price": str(alert_price),
                "order_type": order.get('order_type', ''),
                "quantity": str(quantity),
                "price": str(price),
                "product_type": product_type
            }
            resp = integrate_post("/gttmodify", payload)
            status = resp.get('status') or resp.get('message') or resp
            if resp.get("status") == "ERROR":
                st.error(f"Modify Failed: {resp.get('message','Error')}")
            else:
                st.success(f"Modify Response: {status}")
            st.session_state["gtt_mod_id"] = None
            st.rerun()

def oco_modify_form(order):
    unique_id = f"oco_{order.get('alert_id', '')}"
    st.markdown("---")
    st.subheader(f"Modify OCO: {order.get('tradingsymbol', '')} ({order.get('alert_id', '')})")
    with st.form(f"oco_mod_form_{unique_id}"):
        target_price = st.number_input(
            "Target Price", value=float(order.get('target_price', 0)), key=f"oco_tg_{unique_id}"
        )
        stoploss_price = st.number_input(
            "Stoploss Price", value=float(order.get('stoploss_price', 0)), key=f"oco_sl_{unique_id}"
        )
        target_qty = st.number_input(
            "Target Quantity", value=int(order.get('target_quantity', 1)), step=1, key=f"oco_tq_{unique_id}"
        )
        stoploss_qty = st.number_input(
            "Stoploss Quantity", value=int(order.get('stoploss_quantity', 1)), step=1, key=f"oco_sq_{unique_id}"
        )
        product_type = st.radio(
            "Product Type",
            ["CNC", "INTRADAY", "NORMAL"],
            horizontal=True,
            index=0 if order.get('product_type', 'CNC') == "CNC" else (1 if order.get('product_type', 'CNC') == "INTRADAY" else 2),
            key=f"oco_pt_{unique_id}"
        )
        remarks = st.text_input("Remarks", value=order.get('remarks', ''), key=f"oco_rem_{unique_id}")
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
                "alert_id": order.get('alert_id', ''),
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

def show():
    st.header("GTT / OCO Orders Book & Manage")

    # --- GTT Order Book Section ---
    st.subheader("GTT Order Book")
    data = integrate_get("/gttorders")
    gttlist = data.get("pendingGTTOrderBook", [])
    gtt_mod_id = st.session_state.get("gtt_mod_id", None)

    if gttlist:
        # Table header
        gtt_labels = ["Symbol", "Type", "Cond", "Alert Price", "Order Price", "Qty", "Product", "Modify", "Cancel"]
        cols = st.columns([1.5, 1.2, 1.2, 1.2, 1.2, 1, 1.2, 1.2, 1.2])
        for i, l in enumerate(gtt_labels):
            cols[i].markdown(f"**{l}**")

        for idx, order in enumerate(gttlist):
            cols = st.columns([1.5, 1.2, 1.2, 1.2, 1.2, 1, 1.2, 1.2, 1.2])
            cols[0].write(order.get('tradingsymbol', ''))
            cols[1].write(order.get('order_type', ''))
            cols[2].write(order.get('condition', ''))
            cols[3].write(order.get('alert_price', ''))
            cols[4].write(order.get('price', ''))
            cols[5].write(order.get('quantity', ''))
            cols[6].write(order.get('product_type', ''))

            if cols[7].button("Modify", key=f"gtt_mod_btn_{order.get('alert_id', '')}"):
                st.session_state["gtt_mod_id"] = order.get('alert_id', '')
                st.rerun()
            if cols[8].button("Cancel", key=f"gtt_cancel_btn_{order.get('alert_id', '')}"):
                api_session_key = st.secrets.get("integrate_api_session_key", "")
                url = f"https://integrate.definedgesecurities.com/dart/v1/gttcancel/{order.get('alert_id', '')}"
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
            # Show modify form below table if this row is selected
            if gtt_mod_id == order.get('alert_id', ''):
                gtt_modify_form(order)
                # Do not reset session_state here! Only after submit.

    else:
        st.info("No pending GTT orders.")

    # --- OCO Order Book Section ---
    st.subheader("OCO Order Book")
    data = integrate_get("/ocoorders")
    ocolist = data.get("pendingOCOOrderBook", [])
    oco_mod_id = st.session_state.get("oco_mod_id", None)

    if ocolist:
        # Table header
        oco_labels = ["Symbol", "Type", "Target Price", "Stoploss Price", "Target Qty", "Stoploss Qty", "Product", "Modify", "Cancel"]
        cols = st.columns([1.5, 1.2, 1.2, 1.2, 1, 1, 1.2, 1.2, 1.2])
        for i, l in enumerate(oco_labels):
            cols[i].markdown(f"**{l}**")

        for idx, order in enumerate(ocolist):
            cols = st.columns([1.5, 1.2, 1.2, 1.2, 1, 1, 1.2, 1.2, 1.2])
            cols[0].write(order.get('tradingsymbol', ''))
            cols[1].write(order.get('order_type', ''))
            cols[2].write(order.get('target_price', ''))
            cols[3].write(order.get('stoploss_price', ''))
            cols[4].write(order.get('target_quantity', ''))
            cols[5].write(order.get('stoploss_quantity', ''))
            cols[6].write(order.get('product_type', ''))

            if cols[7].button("Modify", key=f"oco_mod_btn_{order.get('alert_id', '')}"):
                st.session_state["oco_mod_id"] = order.get('alert_id', '')
                st.rerun()
            if cols[8].button("Cancel", key=f"oco_cancel_btn_{order.get('alert_id', '')}"):
                api_session_key = st.secrets.get("integrate_api_session_key", "")
                url = f"https://integrate.definedgesecurities.com/dart/v1/ococancel/{order.get('alert_id', '')}"
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
            # Show modify form below table if this row is selected
            if oco_mod_id == order.get('alert_id', ''):
                oco_modify_form(order)
                # Do not reset session_state here! Only after submit.
    else:
        st.info("No pending OCO orders.")
