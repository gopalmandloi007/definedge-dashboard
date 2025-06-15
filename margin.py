import streamlit as st
from utils import integrate_post
import json

def show():
    st.header("Basket Margin Calculator")
    st.write("Calculate required margin for a basket of orders.")
    with st.form("basket_margin"):
        example = '[{"tradingsymbol":"SBIN-EQ","exchange":"NSE","order_type":"BUY","price":0,"price_type":"MARKET","product_type":"CNC","quantity":1}]'
        basket_str = st.text_area("Basket Orders JSON (list)", value=example, height=150)
        submit = st.form_submit_button("Calculate Margin")
        if submit:
            try:
                basket = json.loads(basket_str)
                if not isinstance(basket, list):
                    raise ValueError("Input must be a list of order dicts.")
                data = {"basketlists": basket}
                resp = integrate_post("/margin", data)
                st.json(resp)
            except json.JSONDecodeError:
                st.error("Invalid JSON format. Please check your input.")
            except Exception as e:
                st.error(f"Error: {e}")
