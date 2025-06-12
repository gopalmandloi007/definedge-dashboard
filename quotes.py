import streamlit as st
from utils import integrate_get

def show():
    st.header("Get Quotes / Security Info")
    exchange = st.text_input("Exchange", value="NSE")
    token = st.text_input("Token", value="22")
    if st.button("Get Quotes"):
        data = integrate_get(f"/quotes/{exchange}/{token}")
        st.json(data)
    if st.button("Get Security Info"):
        data = integrate_get(f"/securityinfo/{exchange}/{token}")
        st.json(data)
