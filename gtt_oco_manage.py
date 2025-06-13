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
    st.header("GTT / OCO Orders")

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
    # Try /ocoorders first. If 404 or empty, fallback to main /orders endpoint and filter for OCOs.
    ocolist = []
    oco_mod_id = st.session_state.get("oco_mod_id", None)
    oco_error = None
    try:
        data = integrate_get("/ocoorders")
        ocolist = data.get("pendingOCOOrderBook", [])
    except Exception as e:
        oco_error = e
        ocolist = []

    # If ocolist is empty, fallback to /orders and filter for OCO type
    if not ocolist:
        try:
            data = integrate_get("/orders")
            all_orders = data.get("orders", [])
            # Adjust the filter as per your order field that marks OCO orders!
            ocolist = [o for o in all_orders if o.get("order_type", "").upper() == "OCO" or o.get("oco_flag") or o.get("oco_leg1") or o.get("oco_leg2")]
        except Exception as e:
            oco_error = e
            ocolist = []

    if ocolist:
        oco_labels = ["Symbol", "Type", "Target Price", "Stoploss Price", "Target Qty", "Stoploss Qty", "Product", "Modify", "Cancel"]
        cols = st.columns([1.5, 1.2, 1.2, 1.2, 1, 1, 1.2, 1.2, 1.2])
        for i, l in enumerate(oco_labels):
            cols[i].markdown(f"**{l}**")

        for idx, order in enumerate(ocolist):
            cols = st.columns([1.5, 1.2, 1.2, 1.2, 1, 1, 1.2, 1.2, 1.2])
            cols[0].write(order.get('tradingsymbol', ''))
            cols[1].write(order.get('order_type', ''))
            cols[2].write(order.get('target_price', order.get('price', '')))
            cols[3].write(order.get('stoploss_price', ''))
            cols[4].write(order.get('target_quantity', order.get('quantity', '')))
            cols[5].write(order.get('stoploss_quantity', ''))
            cols[6].write(order.get('product_type', ''))

            if cols[7].button("Modify", key=f"oco_mod_btn_{order.get('alert_id', order.get('order_id', idx))}"):
                st.session_state["oco_mod_id"] = order.get('alert_id', order.get('order_id', idx))
                st.rerun()
            if cols[8].button("Cancel", key=f"oco_cancel_btn_{order.get('alert_id', order.get('order_id', idx))}"):
                api_session_key = st.secrets.get("integrate_api_session_key", "")
                alert_id = order.get('alert_id', order.get('order_id', idx))
                url = f"https://integrate.definedgesecurities.com/dart/v1/ococancel/{alert_id}"
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
            if oco_mod_id == order.get('alert_id', order.get('order_id', idx)):
                oco_modify_form(order)
                # Do not reset session_state here! Only after submit.
    else:
        if oco_error:
            st.error(f"Could not fetch OCO orders: {oco_error}")
        else:
            st.info("No pending OCO orders.")

    st.markdown("---")

    # Order type selection (Single GTT, OCO GTT, OCO Order)
    st.subheader("Place GTT / OCO Order")
    order_mode = st.radio("Order Mode", ["Single GTT", "OCO GTT", "OCO Order"], horizontal=True, key="gtt_oco_mode")

    with st.form("gtt_oco_place", clear_on_submit=False):
        tradingsymbol = st.text_input("Trading Symbol", key="gtt_ts")
        exchange = st.radio("Exchange", ["NSE", "BSE", "NFO", "BFO", "CDS", "MCX"], horizontal=True, key="gtt_exch")
        order_type = st.radio("Order Type", ["BUY", "SELL"], horizontal=True, key="gtt_ot")
        product_type = st.radio("Product Type", ["CNC", "INTRADAY", "NORMAL"], horizontal=True, key="gtt_pt")

        if order_mode == "Single GTT":
            condition = st.radio("Condition", ["LTP_ABOVE", "LTP_BELOW"], horizontal=True, key="gtt_cond")
            alert_price = st.number_input("Alert Price", min_value=0.0, step=0.05, key="gtt_alert")
            price = st.number_input("Order Price", min_value=0.0, step=0.05, key="gtt_price")
            quantity = st.number_input("Quantity", min_value=1, step=1, key="gtt_qty")
            remarks = st.text_input("Order Remarks (optional)", key="gtt_remarks")
        elif order_mode == "OCO GTT":
            st.markdown("##### OCO Trigger 1")
            cond1 = st.radio("Condition 1", ["LTP_ABOVE", "LTP_BELOW"], horizontal=True, key="gtt_cond1")
            alert1 = st.number_input("Alert Price 1", min_value=0.0, step=0.05, key="gtt_alert1")
            price1 = st.number_input("Order Price 1", min_value=0.0, step=0.05, key="gtt_price1")
            qty1 = st.number_input("Quantity 1", min_value=1, step=1, key="gtt_qty1")
            st.markdown("##### OCO Trigger 2")
            cond2 = st.radio("Condition 2", ["LTP_ABOVE", "LTP_BELOW"], horizontal=True, key="gtt_cond2")
            alert2 = st.number_input("Alert Price 2", min_value=0.0, step=0.05, key="gtt_alert2")
            price2 = st.number_input("Order Price 2", min_value=0.0, step=0.05, key="gtt_price2")
            qty2 = st.number_input("Quantity 2", min_value=1, step=1, key="gtt_qty2")
            remarks = st.text_input("Order Remarks (optional)", key="gtt_remarks2")
        else:  # OCO Order
            st.markdown("##### OCO Target & Stoploss (Order)")
            target_price = st.number_input("Target Price", min_value=0.0, step=0.05, key="oco_target_price")
            stoploss_price = st.number_input("Stoploss Price", min_value=0.0, step=0.05, key="oco_stoploss_price")
            target_qty = st.number_input("Target Quantity", min_value=1, step=1, key="oco_target_qty")
            stoploss_qty = st.number_input("Stoploss Quantity", min_value=1, step=1, key="oco_stoploss_qty")
            remarks = st.text_input("Order Remarks (optional)", key="oco_remarks")

        confirm = st.radio("Confirm Order?", ["Yes", "No"], horizontal=True, key="gtt_oco_confirm")
        submit = st.form_submit_button("Submit Order")

        if submit:
            if confirm == "Yes":
                if order_mode == "Single GTT":
                    data = {
                        "exchange": exchange,
                        "tradingsymbol": tradingsymbol,
                        "condition": condition,
                        "alert_price": str(alert_price),
                        "order_type": order_type,
                        "price": str(price),
                        "quantity": str(quantity),
                        "product_type": product_type
                    }
                    if remarks:
                        data["remarks"] = remarks
                    resp = integrate_post("/gttplaceorder", data)
                    st.success("Single GTT Order submitted!")
                    st.json(resp)
                elif order_mode == "OCO GTT":
                    data = {
                        "exchange": exchange,
                        "tradingsymbol": tradingsymbol,
                        "oco": [
                            {
                                "condition": cond1,
                                "alert_price": str(alert1),
                                "order_type": order_type,
                                "price": str(price1),
                                "quantity": str(qty1),
                                "product_type": product_type
                            },
                            {
                                "condition": cond2,
                                "alert_price": str(alert2),
                                "order_type": order_type,
                                "price": str(price2),
                                "quantity": str(qty2),
                                "product_type": product_type
                            }
                        ]
                    }
                    if remarks:
                        data["remarks"] = remarks
                    resp = integrate_post("/gttplaceorder", data)
                    st.success("OCO GTT Order submitted!")
                    st.json(resp)
                else:  # OCO Order (target/stoploss)
                    data = {
                        "tradingsymbol": tradingsymbol,
                        "exchange": exchange,
                        "order_type": order_type,
                        "target_quantity": int(target_qty),
                        "stoploss_quantity": int(stoploss_qty),
                        "target_price": str(target_price),
                        "stoploss_price": str(stoploss_price),
                        "product_type": product_type
                    }
                    if remarks:
                        data["remarks"] = remarks
                    resp = integrate_post("/ocoplaceorder", data)
                    st.success("OCO Order (target/stoploss) submitted!")
                    st.json(resp)
            else:
                st.warning("Order Not Confirmed.")
                st.info("Modify your values above and re-submit!")
