import streamlit as st
from utils import integrate_post, integrate_get

def show():
    st.header("GTT / OCO Orders")

    # Existing GTTs dikhao (compact)
    st.subheader("GTT Order Book")
    data = integrate_get("/gttorders")
    gttlist = data.get("pendingGTTOrderBook", [])
    if gttlist:
        st.dataframe(gttlist, use_container_width=True)
    else:
        st.info("No pending GTT orders.")

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
        else:  # OCO Order
            st.markdown("##### OCO Target & Stoploss (Order)")
            target_price = st.number_input("Target Price", min_value=0.0, step=0.05, key="oco_target_price")
            stoploss_price = st.number_input("Stoploss Price", min_value=0.0, step=0.05, key="oco_stoploss_price")
            target_qty = st.number_input("Target Quantity", min_value=1, step=1, key="oco_target_qty")
            stoploss_qty = st.number_input("Stoploss Quantity", min_value=1, step=1, key="oco_stoploss_qty")
            remarks = st.text_input("Order Remarks (optional)", key="oco_remarks")

        if order_mode != "OCO Order":
            remarks = st.text_input("Order Remarks (optional)", key="gtt_remarks")

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
                if order_mode == "OCO Order":
                    modify_field = st.radio("What do you want to modify?", 
                        ["Target Price", "Stoploss Price", "Target Qty", "Stoploss Qty", "Order Type"], horizontal=True, key="oco_mod")
                elif order_mode == "OCO GTT":
                    modify_field = st.radio("What do you want to modify? (OCO leg)", 
                        ["First Leg", "Second Leg", "Both"], horizontal=True, key="gtt_mod_oco")
                else:
                    modify_field = st.radio("What do you want to modify?",
                        ["Quantity", "Price", "Condition", "Alert Price", "Order Type"], horizontal=True, key="gtt_mod_single")
                st.info(f"Modify {modify_field} above and re-submit!")
