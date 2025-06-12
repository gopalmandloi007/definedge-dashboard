import streamlit as st
import pandas as pd
from utils import integrate_get

def show():
    st.header("Positions Book")
    data = integrate_get("/positions")
    positions = data.get("positions", [])
    if not positions:
        st.info("No positions found.")
        return
    df = pd.DataFrame(positions)
    st.dataframe(df)
    try:
        st.write("**Total Realized P&L:**", df["realized_pnl"].astype(float).sum())
        st.write("**Total Unrealized P&L:**", df["unrealized_pnl"].astype(float).sum())
    except Exception:
        pass
