import streamlit as st
from utils import integrate_get, integrate_post
import requests

# ---- Modify Forms ----
def gtt_modify_form(order):
    unique_id = f"gtt_{order.get('alert_id', '')}"
    st.markdown("---")
    st.subheader(f"Modify GTT: {order.get('tradingsymbol', '')} ({order.get('alert_id', '')})")
    with st.form(f"gtt_mod_form_{unique_id}"):
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            condition = st.radio("Condition", ["LTP_ABOVE", "LTP_BELOW"], horizontal=True,
                                 index=0 if order.get('condition', 'LTP_ABOVE') == "LTP_ABOVE" else 1)
            order_type = st.radio("Order Type", ["BUY", "SELL"], horizontal=True,
                                  index=0 if order.get('order_type', 'BUY') == "BUY" else 1)
        with col2:
            alert_price = st.number_input("Alert Price", value=float(order.get('alert_price', 0)))
            price = st.number_input("Order Price", value=float(order.get('price', 0)))
        with col3:
            quantity = st.number_input("Quantity", value=int(order.get('quantity', 1)), step=1)
            product_type = st.radio("Product Type", ["CNC", "INTRADAY", "NORMAL"], horizontal=True,
                                    index=0 if order.get('product_type', 'CNC') == "CNC" else (1 if order.get('product_type', 'CNC') == "INTRADAY" else 2))
        with col4:
            remarks = st.text_input("Remarks", value=order.get('remarks', ''))
        submit_mod = st.form_submit_button("Confirm Modify")
        if submit_mod:
            payload = {
                "exchange": order.get('exchange', ''),
                "alert_id": order.get('alert_id', ''),
                "tradingsymbol": order.get('tradingsymbol', ''),
                "condition": condition,
                "alert_price": str(alert_price),
                "order_type": order_type,
                "quantity": str(quantity),
                "price": str(price),
                "product_type": product_type
            }
            if remarks:
                payload["remarks"] = remarks
            resp = integrate_post("/gttmodify", payload)
            status = resp.get('status') or resp.get('message') or resp
            if resp.get("status") == "ERROR":
                st.error(f"Modify Failed: {resp.get('message','Error')}")
            else:
                st.success(f"Modify Response: {status}")
            st.session_state["gtt_mod_id"] = None
            st.rerun()

def oco_modify_form(order):
    unique_id = f"oco_{order.get('order_id', order.get('alert_id', ''))}"
    st.markdown("---")
    st.subheader(f"Modify OCO: {order.get('tradingsymbol', '')} ({unique_id})")
    with st.form(f"oco_mod_form_{unique_id}"):
        col1, col2, col3 = st.columns(3)
        with col1:
            target_price = st.number_input("Target Price", value=float(order.get('target_price', order.get('price', 0))))
            stoploss_price = st.number_input("Stoploss Price", value=float(order.get('stoploss_price', 0)))
        with col2:
            target_qty = st.number_input("Target Qty", value=int(order.get('target_quantity', order.get('quantity', 1))), step=1)
            stoploss_qty = st.number_input("Stoploss Qty", value=int(order.get('stoploss_quantity', 1)), step=1)
        with col3:
            product_type = st.radio("Product", ["CNC", "INTRADAY", "NORMAL"], horizontal=True,
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

def show():
    st.title("⚡ Definedge Integrate Dashboard")
    st.header("GTT / OCO Orders Book & Manage")

    # -------- GTT Order Book --------
    st.subheader("GTT Order Book")
    data = integrate_get("/gttorders")
    gttlist = data.get("pendingGTTOrderBook", [])
    gtt_mod_id = st.session_state.get("gtt_mod_id", None)
    if gttlist:
        gtt_labels = ["Symbol", "Type", "Cond", "Alert", "Order Price", "Qty", "Product", "Remarks", "Modify", "Cancel"]
        cols = st.columns([1.3, 1.1, 1.1, 1.2, 1.2, 0.8, 0.9, 1.2, 1, 1])
        for i, l in enumerate(gtt_labels):
            cols[i].markdown(f"**{l}**")
        for idx, order in enumerate(gttlist):
            cols = st.columns([1.3, 1.1, 1.1, 1.2, 1.2, 0.8, 0.9, 1.2, 1, 1])
            cols[0].write(order.get('tradingsymbol', ''))
            cols[1].write(order.get('order_type', ''))
            cols[2].write(order.get('condition', ''))
            cols[3].write(order.get('alert_price', ''))
            cols[4].write(order.get('price', ''))
            cols[5].write(order.get('quantity', ''))
            cols[6].write(order.get('product_type', ''))
            cols[7].write(order.get('remarks', ''))
            if cols[8].button("Modify", key=f"gtt_mod_btn_{order.get('alert_id', '')}"):
                st.session_state["gtt_mod_id"] = order.get('alert_id', '')
                st.rerun()
            if cols[9].button("Cancel", key=f"gtt_cancel_btn_{order.get('alert_id', '')}"):
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
            if gtt_mod_id == order.get('alert_id', ''):
                gtt_modify_form(order)
    else:
        st.info("No pending GTT orders.")

    # -------- OCO Order Book --------
    st.subheader("OCO Order Book")
    oco_mod_id = st.session_state.get("oco_mod_id", None)
    data = integrate_get("/orders")
    all_orders = data.get("orders", [])
    ocolist = [
        o for o in all_orders
        if str(o.get("order_type", "")).upper() == "OCO"
        or o.get("oco_flag")
        or (o.get("target_price") and o.get("stoploss_price"))
    ]
    if ocolist:
        oco_labels = ["Symbol", "Type", "Target", "Stoploss", "Target Qty", "Stoploss Qty", "Product", "Remarks", "Modify", "Cancel"]
        cols = st.columns([1.3, 1.1, 1.1, 1.1, 1, 1, 1.1, 1.2, 1, 1])
        for i, l in enumerate(oco_labels):
            cols[i].markdown(f"**{l}**")
        for idx, order in enumerate(ocolist):
            cols = st.columns([1.3, 1.1, 1.1, 1.1, 1, 1, 1.1, 1.2, 1, 1])
            cols[0].write(order.get('tradingsymbol', ''))
            cols[1].write(order.get('order_type', ''))
            cols[2].write(order.get('target_price', order.get('price', '')))
            cols[3].write(order.get('stoploss_price', ''))
            cols[4].write(order.get('target_quantity', order.get('quantity', '')))
            cols[5].write(order.get('stoploss_quantity', ''))
            cols[6].write(order.get('product_type', ''))
            cols[7].write(order.get('remarks', ''))
            this_oid = order.get('order_id', order.get('alert_id', idx))
            if cols[8].button("Modify", key=f"oco_mod_btn_{this_oid}"):
                st.session_state["oco_mod_id"] = this_oid
                st.rerun()
            if cols[9].button("Cancel", key=f"oco_cancel_btn_{this_oid}"):
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

    # -------- Place New GTT / OCO Order (Compact Columns) --------
    st.markdown("---")
    st.subheader("Place GTT / OCO Order")
    order_mode = st.radio("Order Mode", ["Single GTT", "OCO GTT", "OCO Order"], horizontal=True, key="gtt_oco_mode")
    with st.form("gtt_oco_place", clear_on_submit=False):
        # Responsive columns for compact form
        if order_mode == "Single GTT":
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                tradingsymbol = st.text_input("Trading Symbol")
                exchange = st.radio("Exchange", ["NSE", "BSE", "NFO", "BFO", "CDS", "MCX"], horizontal=True)
            with col2:
                order_type = st.radio("Order Type", ["BUY", "SELL"], horizontal=True)
                product_type = st.radio("Product Type", ["CNC", "INTRADAY", "NORMAL"], horizontal=True)
            with col3:
                condition = st.radio("Condition", ["LTP_ABOVE", "LTP_BELOW"], horizontal=True)
                alert_price = st.number_input("Alert Price", min_value=0.0, step=0.05)
                price = st.number_input("Order Price", min_value=0.0, step=0.05)
            with col4:
                quantity = st.number_input("Quantity", min_value=1, step=1)
                remarks = st.text_input("Remarks (optional)")
        elif order_mode == "OCO GTT":
            st.markdown("###### OCO Trigger 1")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                tradingsymbol = st.text_input("Trading Symbol")
                exchange = st.radio("Exchange", ["NSE", "BSE", "NFO", "BFO", "CDS", "MCX"], horizontal=True)
            with col2:
                order_type = st.radio("Order Type", ["BUY", "SELL"], horizontal=True)
                product_type = st.radio("Product Type", ["CNC", "INTRADAY", "NORMAL"], horizontal=True)
            with col3:
                cond1 = st.radio("Condition 1", ["LTP_ABOVE", "LTP_BELOW"], horizontal=True)
                alert1 = st.number_input("Alert Price 1", min_value=0.0, step=0.05)
                price1 = st.number_input("Order Price 1", min_value=0.0, step=0.05)
            with col4:
                qty1 = st.number_input("Quantity 1", min_value=1, step=1)
                remarks = st.text_input("Remarks (optional)")
            st.markdown("###### OCO Trigger 2")
            col5, col6 = st.columns(2)
            with col5:
                cond2 = st.radio("Condition 2", ["LTP_ABOVE", "LTP_BELOW"], horizontal=True)
                alert2 = st.number_input("Alert Price 2", min_value=0.0, step=0.05)
                price2 = st.number_input("Order Price 2", min_value=0.0, step=0.05)
            with col6:
                qty2 = st.number_input("Quantity 2", min_value=1, step=1)
        else:  # OCO Order
            col1, col2, col3 = st.columns(3)
            with col1:
                tradingsymbol = st.text_input("Trading Symbol")
                exchange = st.radio("Exchange", ["NSE", "BSE", "NFO", "BFO", "CDS", "MCX"], horizontal=True)
                remarks = st.text_input("Remarks (optional)")
            with col2:
                order_type = st.radio("Order Type", ["BUY", "SELL"], horizontal=True)
                product_type = st.radio("Product Type", ["CNC", "INTRADAY", "NORMAL"], horizontal=True)
            with col3:
                target_price = st.number_input("Target Price", min_value=0.0, step=0.05)
                stoploss_price = st.number_input("Stoploss Price", min_value=0.0, step=0.05)
                target_qty = st.number_input("Target Quantity", min_value=1, step=1)
                stoploss_qty = st.number_input("Stoploss Quantity", min_value=1, step=1)
        confirm = st.radio("Confirm Order?", ["Yes", "No"], horizontal=True)
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
import streamlit as st
from utils import integrate_get, integrate_post
import requests

def gtt_modify_form(order):
    unique_id = f"gtt_{order.get('alert_id', '')}"
    st.markdown("---")
    st.subheader(f"Modify GTT: {order.get('tradingsymbol', '')} ({order.get('alert_id', '')})")
    with st.form(f"gtt_mod_form_{unique_id}"):
        condition = st.radio("Condition", ["LTP_ABOVE", "LTP_BELOW"], horizontal=True,
                             index=0 if order.get('condition', 'LTP_ABOVE') == "LTP_ABOVE" else 1)
        alert_price = st.number_input("Alert Price", value=float(order.get('alert_price', 0)))
        price = st.number_input("Order Price", value=float(order.get('price', 0)))
        quantity = st.number_input("Quantity", value=int(order.get('quantity', 1)), step=1)
        product_type = st.radio("Product Type", ["CNC", "INTRADAY", "NORMAL"], horizontal=True,
                                index=0 if order.get('product_type', 'CNC') == "CNC" else (1 if order.get('product_type', 'CNC') == "INTRADAY" else 2))
        remarks = st.text_input("Remarks", value=order.get('remarks', ''))
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
            if remarks:
                payload["remarks"] = remarks
            resp = integrate_post("/gttmodify", payload)
            status = resp.get('status') or resp.get('message') or resp
            if resp.get("status") == "ERROR":
                st.error(f"Modify Failed: {resp.get('message','Error')}")
            else:
                st.success(f"Modify Response: {status}")
            st.session_state["gtt_mod_id"] = None
            st.rerun()

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

def show():
    st.header("GTT / OCO Orders Book & Manage")

    # --- GTT Order Book ---
    st.subheader("GTT Order Book")
    data = integrate_get("/gttorders")
    gttlist = data.get("pendingGTTOrderBook", [])
    gtt_mod_id = st.session_state.get("gtt_mod_id", None)

    if gttlist:
        gtt_labels = ["Symbol", "Type", "Cond", "Alert Price", "Order Price", "Qty", "Product", "Remarks", "Modify", "Cancel"]
        cols = st.columns([1.3, 1.1, 1.1, 1.1, 1.1, 0.8, 1.1, 1.2, 1, 1])
        for i, l in enumerate(gtt_labels):
            cols[i].markdown(f"**{l}**")
        for idx, order in enumerate(gttlist):
            cols = st.columns([1.3, 1.1, 1.1, 1.1, 1.1, 0.8, 1.1, 1.2, 1, 1])
            cols[0].write(order.get('tradingsymbol', ''))
            cols[1].write(order.get('order_type', ''))
            cols[2].write(order.get('condition', ''))
            cols[3].write(order.get('alert_price', ''))
            cols[4].write(order.get('price', ''))
            cols[5].write(order.get('quantity', ''))
            cols[6].write(order.get('product_type', ''))
            cols[7].write(order.get('remarks', ''))
            if cols[8].button("Modify", key=f"gtt_mod_btn_{order.get('alert_id', '')}"):
                st.session_state["gtt_mod_id"] = order.get('alert_id', '')
                st.rerun()
            if cols[9].button("Cancel", key=f"gtt_cancel_btn_{order.get('alert_id', '')}"):
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
            if gtt_mod_id == order.get('alert_id', ''):
                gtt_modify_form(order)
    else:
        st.info("No pending GTT orders.")

    # --- OCO Order Book ---
    st.subheader("OCO Order Book")
    oco_mod_id = st.session_state.get("oco_mod_id", None)
    # Always use /orders, since /ocoorders does not exist or is empty/404
    data = integrate_get("/orders")
    all_orders = data.get("orders", [])
    # Filter for OCO orders: adjust this filter as per your real order fields if needed!
    ocolist = [
        o for o in all_orders
        if str(o.get("order_type", "")).upper() == "OCO"
        or o.get("oco_flag")
        or (o.get("target_price") and o.get("stoploss_price"))
    ]
    if ocolist:
        oco_labels = ["Symbol", "Type", "Target Price", "Stoploss Price", "Target Qty", "Stoploss Qty", "Product", "Remarks", "Modify", "Cancel"]
        cols = st.columns([1.3, 1.1, 1.1, 1.1, 1, 1, 1.1, 1.2, 1, 1])
        for i, l in enumerate(oco_labels):
            cols[i].markdown(f"**{l}**")
        for idx, order in enumerate(ocolist):
            cols = st.columns([1.3, 1.1, 1.1, 1.1, 1, 1, 1.1, 1.2, 1, 1])
            cols[0].write(order.get('tradingsymbol', ''))
            cols[1].write(order.get('order_type', ''))
            cols[2].write(order.get('target_price', order.get('price', '')))
            cols[3].write(order.get('stoploss_price', ''))
            cols[4].write(order.get('target_quantity', order.get('quantity', '')))
            cols[5].write(order.get('stoploss_quantity', ''))
            cols[6].write(order.get('product_type', ''))
            cols[7].write(order.get('remarks', ''))
            this_oid = order.get('order_id', order.get('alert_id', idx))
            if cols[8].button("Modify", key=f"oco_mod_btn_{this_oid}"):
                st.session_state["oco_mod_id"] = this_oid
                st.rerun()
            if cols[9].button("Cancel", key=f"oco_cancel_btn_{this_oid}"):
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
