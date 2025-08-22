import streamlit as st
from integrate import ConnectToIntegrate, IntegrateOrders

def update_session_keys(conn):
    """Login and fetch fresh session keys from broker for this machine."""
    api_token = st.secrets["INTEGRATE_API_TOKEN"]
    api_secret = st.secrets["INTEGRATE_API_SECRET"]
    conn.login(api_token=api_token, api_secret=api_secret)
    uid, actid, api_session_key, ws_session_key = conn.get_session_keys()
    conn.set_session_keys(uid, actid, api_session_key, ws_session_key)
    return uid, actid, api_session_key, ws_session_key

def ensure_active_session(conn):
    """Checks session validity, refreshes if needed."""
    try:
        io = IntegrateOrders(conn)
        test = io.holdings()
        # If session expired, re-login
        if (
            isinstance(test, dict)
            and str(test.get("status", "")).upper() in ["FAILED", "FAIL", "ERROR"]
            and "session" in str(test.get("message", "")).lower()
        ):
            st.warning("Session expired, re-logging in.")
            raise Exception("Session expired")
        return io
    except Exception:
        # Always login from THIS app, never copy-paste session keys!
        uid, actid, api_session_key, ws_session_key = update_session_keys(conn)
        st.info("Session refreshed successfully.")
        return IntegrateOrders(conn)

def show():
    st.header("Login & Session Key (SDK Mode)")
    api_token = st.secrets.get("INTEGRATE_API_TOKEN", "")
    api_secret = st.secrets.get("INTEGRATE_API_SECRET", "")
    if not api_token or not api_secret:
        st.error("Please set INTEGRATE_API_TOKEN and INTEGRATE_API_SECRET in your secrets.toml file.")
        return

    conn = ConnectToIntegrate()
    try:
        # Try to get valid session keys by logging in
        uid, actid, api_session_key, ws_session_key = update_session_keys(conn)
    except Exception as e:
        st.error(f"Login failed: {e}")
        return

    if st.button("Force Refresh Session"):
        uid, actid, api_session_key, ws_session_key = update_session_keys(conn)
        st.success("Session forcibly refreshed!")
    
    st.info(f"Current session key: {api_session_key[:8]}... (hidden for security)")
    st.caption(f"Actid: {actid}")
