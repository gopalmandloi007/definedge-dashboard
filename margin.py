import streamlit as st
from utils import integrate_post

def show():
    st.header("Basket Margin Calculator")
    st.write("Calculate required margin for a basket of orders.")
    with st.form("basket_margin"):
        basket_str = st.text_area("Basket Orders JSON (list)", value='[{"tradingsymbol":"SBIN-EQ","exchange":"NSE","order_type":"BUY","price":0,"price_type":"MARKET","product_type":"CNC","quantity":1}]')
        submit = st.form_submit_button("Calculate Margin")
        if submit:
            try:
                import json
                basket = json.loads(basket_str)
                data = {"basketlists": basket}
                resp = integrate_post("/margin", data)
                st.write(resp)
            except Exception as e:
                st.error(str(e))
