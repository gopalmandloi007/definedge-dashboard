import streamlit as st
from utils import integrate_post, integrate_put, integrate_delete

def show():
    st.header("Place / Modify / Cancel Order")
    st.subheader("Place Order")
    with st.form("place_order"):
        tradingsymbol = st.text_input("Trading Symbol")
        exchange = st.selectbox("Exchange", ["NSE", "BSE", "NFO", "BFO", "CDS", "MCX"])
        order_type = st.selectbox("Order Type", ["BUY", "SELL"])
        quantity = st.number_input("Quantity", step=1)
        price = st.number_input("Price", value=0.0)
        price_type = st.selectbox("Price Type", ["LIMIT", "MARKET", "SL-LIMIT", "SL-MARKET"])
        product_type = st.selectbox("Product Type", ["CNC", "INTRADAY", "NORMAL"])
        trigger_price = st.number_input("Trigger Price", value=0.0)
        remarks = st.text_input("Remarks (optional)")
        submit = st.form_submit_button("Place Order")
        if submit:
            data = {
                "tradingsymbol": tradingsymbol,
                "exchange": exchange,
                "order_type": order_type,
                "quantity": quantity,
                "price": price,
                "price_type": price_type,
                "product_type": product_type,
                "trigger_price": trigger_price,
                "remarks": remarks
            }
            resp = integrate_post("/orders", data)
            st.write(resp)

    st.subheader("Modify / Cancel Order")
    order_id = st.text_input("Order ID (for modify/cancel)")
    mod_cancel = st.radio("Action", ["Modify", "Cancel"])
    if mod_cancel == "Modify":
        with st.form("modify_order"):
            new_price = st.number_input("New Price", value=0.0, key="mod_price")
            new_qty = st.number_input("New Qty", step=1, key="mod_qty")
            mod_submit = st.form_submit_button("Modify Order")
            if mod_submit and order_id:
                data = {"price": new_price, "quantity": new_qty}
                resp = integrate_put(f"/orders/{order_id}", data)
                st.write(resp)
    elif mod_cancel == "Cancel" and order_id:
        if st.button("Cancel Order Now"):
            resp = integrate_delete(f"/orders/{order_id}")
            st.write(resp)
