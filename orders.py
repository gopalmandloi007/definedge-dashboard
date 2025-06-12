import streamlit as st
from utils import definedge_get, definedge_post

def show():
    st.header("📝 Order Management")
    # Place Order
    st.subheader("Place New Order")
    with st.form("place_order"):
        exch = st.selectbox("Exchange", ["NSE", "BSE", "NFO", "BFO", "CDS", "MCX"])
        order_type = st.selectbox("Order Type", ["BUY", "SELL"])
        price_type = st.selectbox("Price Type", ["LIMIT", "MARKET", "SL-LIMIT", "SL-MARKET"])
        prod_type = st.selectbox("Product Type", ["CNC", "INTRADAY", "NORMAL"])
        tradingsymbol = st.text_input("Trading Symbol")
        price = st.number_input("Price", value=0.0)
        qty = st.number_input("Quantity", step=1)
        trigger_price = st.number_input("Trigger Price", value=0.0)
        submit = st.form_submit_button("Place Order")
        if submit:
            data = {
                "exchange": exch,
                "order_type": order_type,
                "price_type": price_type,
                "product_type": prod_type,
                "tradingsymbol": tradingsymbol,
                "price": price,
                "quantity": qty,
                "trigger_price": trigger_price,
            }
            resp = definedge_post("/placeorder", data)
            st.write(resp)

    st.subheader("Modify/Cancel Order (Use Order ID)")
    order_id = st.text_input("Order ID")
    mod_cancel = st.radio("Action", ["Modify", "Cancel"])
    if mod_cancel == "Modify":
        # Provide fields to modify
        with st.form("modify_order"):
            new_price = st.number_input("New Price", value=0.0, key="mod_price")
            new_qty = st.number_input("New Qty", step=1, key="mod_qty")
            mod_submit = st.form_submit_button("Modify Order")
            if mod_submit and order_id:
                data = {"order_id": order_id, "price": new_price, "quantity": new_qty}
                resp = definedge_post("/modify", data)
                st.write(resp)
    elif mod_cancel == "Cancel" and order_id:
        if st.button("Cancel Order Now"):
            resp = definedge_get(f"/cancel/{order_id}")
            st.write(resp)
