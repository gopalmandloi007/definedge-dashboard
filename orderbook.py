import streamlit as st
import pandas as pd
from utils import integrate_get

def show():
    st.header("Order Book & Trade Book")
    st.subheader("Order Book")
    data = integrate_get("/orders")
    orders = data.get("orders", [])
    if orders:
        st.dataframe(pd.DataFrame(orders))
    else:
        st.info("No orders found.")
    st.subheader("Trade Book")
    data = integrate_get("/trades")
    trades = data.get("trades", [])
    if trades:
        st.dataframe(pd.DataFrame(trades))
    else:
        st.info("No trades found.")
