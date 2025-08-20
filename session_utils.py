import streamlit as st
from integrate import ConnectToIntegrate

def update_session_secrets(uid, actid, api_session_key, ws_session_key):
    st.secrets["integrate_uid"] = uid
    st.secrets["integrate_actid"] = actid
    st.secrets["integrate_api_session_key"] = api_session_key
    st.secrets["integrate_ws_session_key"] = ws_session_key

def ensure_active_session():
    required_keys = [
        "integrate_uid", "integrate_actid",
        "integrate_api_session_key", "integrate_ws_session_key"
    ]
    if not all(k in st.secrets for k in required_keys):
        st.warning("You are not logged in! Please login with OTP from the sidebar.")
        return None

    conn = ConnectToIntegrate()
    conn.set_session_keys(
        st.secrets["integrate_uid"],
        st.secrets["integrate_actid"],
        st.secrets["integrate_api_session_key"],
        st.secrets["integrate_ws_session_key"],
    )
    return conn
