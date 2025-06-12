import streamlit as st
from utils import get_integrate_client

def show():
    st.header("Holdings & Positions (Live)")
    try:
        conn, io = get_integrate_client()
    except Exception as e:
        st.error(f"API client error: {e}")
        st.stop()

    # Correct function call:
    try:
        holdings = io.holdings()  # NOT io.get_holdings()
    except Exception as e:
        st.error(f"Failed to retrieve holdings: {e}")
        return

    st.write(holdings)
