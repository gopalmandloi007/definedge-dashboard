import streamlit as st
from utils import integrate_post

def show():
    st.header("Place / Modify / Cancel Order")
    st.subheader("Place Order")
    with st.form("place_order"):
        tradingsymbol = st.text_input("Trading Symbol")
        exchange = st.selectbox("Exchange", ["NSE", "BSE", "NFO", "BFO", "CDS", "MCX"])
        order_type = st.selectbox("Order Type", ["BUY", "SELL"])
        quantity = st.number_input("Quantity", step=1)
        price_type = st.selectbox("Price Type", ["LIMIT", "MARKET", "SL-LIMIT", "SL-MARKET"])
        price = st.number_input("Price", value=0.0)
        product_type = st.selectbox("Product Type", ["CNC", "INTRADAY", "NORMAL"])
        trigger_price = st.number_input("Trigger Price", value=0.0)
        remarks = st.text_input("Remarks (optional)")
        validity = st.selectbox("Validity", ["DAY", "EOS", "IOC"], index=0)
        disclosed_quantity = st.number_input("Disclosed Quantity", value=0, step=1)
        amo = st.checkbox("After Market Order (AMO)?")
        submit = st.form_submit_button("Place Order")
        if submit:
            data = {
                "tradingsymbol": tradingsymbol,
                "exchange": exchange,
                "order_type": order_type,
                "quantity": int(quantity),
                "price_type": price_type,
                "price": float(price),
                "product_type": product_type,
                "validity": validity
            }
            if trigger_price:
                data["trigger_price"] = float(trigger_price)
            if remarks:
                data["remarks"] = remarks
            if disclosed_quantity:
                data["disclosed_quantity"] = int(disclosed_quantity)
            if amo:
                data["amo"] = "Yes"
            resp = integrate_post("/placeorder", data)
            st.json(resp)
