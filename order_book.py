import streamlit as st
import pandas as pd
from utils import definedge_get

def show():
    st.header("📚 Order Book")
    data = definedge_get("/orders")
    df = pd.DataFrame(data.get("orders", []))
    st.dataframe(df)
