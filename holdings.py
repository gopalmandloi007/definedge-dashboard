import streamlit as st
from integrate import ConnectToIntegrate, IntegrateOrders

def show():
    st.header("Holdings")
    try:
        conn = ConnectToIntegrate()
        conn.login("", "")
        conn.set_session_keys("", "", "", "")
        io = IntegrateOrders(conn)
        holdings_book = io.holdings()
        st.write("DEBUG: holdings_book", holdings_book)
        if not holdings_book.get("data"):
            st.info("No holdings found or API returned: " + str(holdings_book))
        else:
            st.write("Holdings data found!")
            st.write(holdings_book["data"])
    except Exception as e:
        st.error(f"Failed to get holdings: {e}")
