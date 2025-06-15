import streamlit as st
from utils import integrate_get

def show():
    st.header("Get Quotes / Security Info")
    exchange = st.text_input("Exchange", value="NSE")
    token = st.text_input("Token", value="22")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Get Quotes"):
            try:
                data = integrate_get(f"/quotes/{exchange}/{token}")
                st.json(data)
            except Exception as e:
                st.error(f"Error fetching quotes: {e}")
    with col2:
        if st.button("Get Security Info"):
            try:
                data = integrate_get(f"/securityinfo/{exchange}/{token}")
                st.json(data)
            except Exception as e:
                st.error(f"Error fetching security info: {e}")
