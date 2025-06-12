import streamlit as st
import pandas as pd
from utils import definedge_get

def show():
    st.header("💼 Holdings & Positions")

    # Holdings
    with st.expander("Holdings", expanded=True):
        data = definedge_get("/holdings")
        df = pd.DataFrame(data.get("data", []))
        st.dataframe(df)

    # Positions
    with st.expander("Positions"):
        data = definedge_get("/positions")
        df = pd.DataFrame(data.get("positions", []))
        st.dataframe(df)
