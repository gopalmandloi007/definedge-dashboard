import streamlit as st
from integrate import ConnectToIntegrate, IntegrateOrders

def update_session_state(uid, actid, api_session_key, ws_session_key):
    st.session_state["INTEGRATE_UID"] = uid
    st.session_state["INTEGRATE_ACTID"] = actid
    st.session_state["INTEGRATE_API_SESSION_KEY"] = api_session_key
    st.session_state["INTEGRATE_WS_SESSION_KEY"] = ws_session_key

def ensure_active_session():
    required_keys = ["INTEGRATE_UID", "INTEGRATE_ACTID", "INTEGRATE_API_SESSION_KEY", "INTEGRATE_WS_SESSION_KEY"]
    if not all(k in st.session_state for k in required_keys):
        st.warning("You are not logged in! Please login with OTP from the sidebar.")
        return None

    conn = ConnectToIntegrate()
    conn.set_session_keys(
        st.session_state["INTEGRATE_UID"],
        st.session_state["INTEGRATE_ACTID"],
        st.session_state["INTEGRATE_API_SESSION_KEY"],
        st.session_state["INTEGRATE_WS_SESSION_KEY"],
    )
    try:
        io = IntegrateOrders(conn)
        test = io.holdings()
        if (
            isinstance(test, dict)
            and str(test.get("status", "")).upper() in ["FAILED", "FAIL", "ERROR"]
            and "session" in str(test.get("message", "")).lower()
        ):
            st.error("Session expired! Please go to Login page and refresh with OTP.")
            return None
        return conn
    except Exception:
        st.error("Session error! Please login again from Login page.")
        return None
