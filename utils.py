import streamlit as st
from integrate import ConnectToIntegrate, IntegrateOrders

@st.cache_resource(show_spinner=False)
def get_integrate_client():
    # Set these as Streamlit secrets!
    api_token = st.secrets["integrate_api_token"]
    api_secret = st.secrets["integrate_api_secret"]
    uid = st.secrets["integrate_uid"]
    actid = st.secrets["integrate_actid"]
    api_session_key = st.secrets["integrate_api_session_key"]
    ws_session_key = st.secrets["integrate_ws_session_key"]

    conn = ConnectToIntegrate()
    conn.login(api_token, api_secret)
    conn.set_session_keys(uid, actid, api_session_key, ws_session_key)
    io = IntegrateOrders(conn)
    return conn, io
