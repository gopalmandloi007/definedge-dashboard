import streamlit as st
from utils import definedge_get

def show():
    st.header("💹 Quotes & Security Info")
    exch = st.text_input("Exchange", value="NSE")
    token = st.text_input("Token", value="22")
    if st.button("Get Quotes"):
        data = definedge_get(f"/quotes/{exch}/{token}")
        st.json(data)
    if st.button("Get Security Info"):
        data = definedge_get(f"/securityinfo/{exch}/{token}")
        st.json(data)
