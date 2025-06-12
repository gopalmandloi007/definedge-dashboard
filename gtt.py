import streamlit as st
from utils import integrate_get, integrate_post

def show():
    st.header("GTT Orders")
    st.write("View and place GTT orders.")

    # Book Section (compact)
    st.subheader("GTT Book")
    data = integrate_get("/gttorders")
    gttlist = data.get("pendingGTTOrderBook", [])
    if gttlist:
        st.dataframe(gttlist, use_container_width=True)
    else:
        st.info("No pending GTT orders.")

    # Place Order Section (super compact, radio buttons, GTT type select, confirm flow)
    st.subheader("Place GTT Order")
    with st.form("gtt_place", clear_on_submit=False):
        st.markdown("#### 🔔 Quick GTT (with OCO/Single option)")
        gtt_type = st.radio("GTT Type", ["Single GTT", "OCO GTT"], horizontal=True, key="gtt_type")
        tradingsymbol = st.text_input("Trading Symbol", key="gtt_ts")
        exchange = st.radio("Exchange", ["NSE", "BSE", "NFO", "BFO", "CDS", "MCX"], horizontal=True, key="gtt_exch")
        order_type = st.radio("Order Type", ["BUY", "SELL"], horizontal=True, key="gtt_ot")

        if gtt_type == "Single GTT":
            condition = st.radio("Condition", ["LTP_ABOVE", "LTP_BELOW"], horizontal=True, key="gtt_cond")
            alert_price = st.number_input("Alert Price", min_value=0.0, step=0.05, key="gtt_alert")
            price = st.number_input("Order Price", min_value=0.0, step=0.05, key="gtt_price")
            quantity = st.number_input("Quantity", min_value=1, step=1, key="gtt_qty")
        else:  # OCO GTT
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

        remarks = st.text_input("Remarks (optional)", key="gtt_remarks")
        confirm = st.radio("Confirm GTT Order?", ["Yes", "No"], horizontal=True, key="gtt_confirm")
        submit = st.form_submit_button("Submit GTT Order")

        if submit:
            if confirm == "Yes":
                if gtt_type == "Single GTT":
                    data = {
                        "exchange": exchange,
                        "tradingsymbol": tradingsymbol,
                        "condition": condition,
                        "alert_price": str(alert_price),
                        "order_type": order_type,
                        "price": str(price),
                        "quantity": str(quantity),
                    }
                    if remarks:
                        data["remarks"] = remarks
                else:
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
                            },
                            {
                                "condition": cond2,
                                "alert_price": str(alert2),
                                "order_type": order_type,
                                "price": str(price2),
                                "quantity": str(qty2),
                            }
                        ]
                    }
                    if remarks:
                        data["remarks"] = remarks
                resp = integrate_post("/gttplaceorder", data)
                st.success("GTT Order submitted!")
                st.json(resp)
            else:
                st.warning("Order Not Confirmed.")
                if gtt_type == "Single GTT":
                    modify_field = st.radio("What do you want to modify?", 
                        ["Quantity", "Price", "Condition", "Alert Price", "Order Type"], horizontal=True, key="gtt_mod_single")
                else:
                    modify_field = st.radio("What do you want to modify? (OCO leg)", 
                        ["First Leg", "Second Leg", "Both"], horizontal=True, key="gtt_mod_oco")
                st.info(f"Modify {modify_field} above and re-submit!")
