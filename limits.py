import streamlit as st
from utils import integrate_get, integrate_post

def show():
    st.header("Limits & Product Conversion")
    st.subheader("Limits")
    data = integrate_get("/limits")
    st.json(data)

    st.subheader("Product Conversion")
    with st.form("prod_conv"):
        tradingsymbol = st.text_input("Trading Symbol")
        exchange = st.selectbox("Exchange", ["NSE", "NFO", "BSE", "MCX"])
        quantity = st.number_input("Quantity", step=1)
        previous_product = st.selectbox("Previous Product", ["CNC", "INTRADAY", "NORMAL"])
        new_product = st.selectbox("New Product", ["CNC", "INTRADAY", "NORMAL"])
        order_type = st.selectbox("Order Type", ["BUY", "SELL"])
        position_type = st.selectbox("Position Type", ["DAY", "CARRYFORWARD"])
        submit = st.form_submit_button("Convert Product")
        if submit:
            data = {
                "tradingsymbol": tradingsymbol,
                "exchange": exchange,
                "quantity": quantity,
                "previous_product": previous_product,
                "product_type": new_product,
                "order_type": order_type,
                "position_type": position_type
            }
            resp = integrate_post("/positions/convert", data)
            st.write(resp)
