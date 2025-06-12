import streamlit as st
from utils import definedge_get, definedge_post

def show():
    st.header("💸 Limits / Product Conversion")
    st.subheader("Limits")
    data = definedge_get("/limits")
    st.json(data)

    st.subheader("Product Conversion")
    with st.form("prod_conv"):
        exch = st.selectbox("Exchange", ["NSE", "NFO", "BSE", "MCX"])
        tradingsymbol = st.text_input("Trading Symbol")
        qty = st.number_input("Quantity", step=1)
        prev_prod = st.selectbox("Previous Product", ["CNC", "INTRADAY", "NORMAL"])
        new_prod = st.selectbox("New Product", ["CNC", "INTRADAY", "NORMAL"])
        order_type = st.selectbox("Order Type", ["BUY", "SELL"])
        pos_type = st.text_input("Position Type", value="DAY")
        submit = st.form_submit_button("Convert Product")
        if submit:
            data = {
                "exchange": exch,
                "tradingsymbol": tradingsymbol,
                "quantity": qty,
                "previous_product": prev_prod,
                "order_type": order_type,
                "product_type": new_prod,
                "position_type": pos_type,
            }
            resp = definedge_post("/productconversion", data)
            st.write(resp)
