import streamlit as st
from integrate import ConnectToIntegrate, IntegrateOrders

def ensure_active_session(conn):
    try:
        io = IntegrateOrders(conn)
        test = io.holdings()
        if (
            isinstance(test, dict)
            and str(test.get("status", "")).upper() in ["FAILED", "FAIL", "ERROR"]
            and "session" in str(test.get("message", "")).lower()
        ):
            st.warning("Session expired, re-logging in.")
            raise Exception("Session expired")
        return io
    except Exception:
        api_token = st.secrets["INTEGRATE_API_TOKEN"]
        api_secret = st.secrets["INTEGRATE_API_SECRET"]
        conn.login(api_token=api_token, api_secret=api_secret)
        uid, actid, api_session_key, ws_session_key = conn.get_session_keys()
        # Optionally update Streamlit secrets if needed, but usually not required
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
        uid = st.secrets["INTEGRATE_UID"]
        actid = st.secrets["INTEGRATE_ACTID"]
        api_session_key = st.secrets["INTEGRATE_API_SESSION_KEY"]
        ws_session_key = st.secrets["INTEGRATE_WS_SESSION_KEY"]
        conn.set_session_keys(uid, actid, api_session_key, ws_session_key)
    except KeyError:
        st.warning("No previous session found. Logging in...")
        conn.login(api_token=api_token, api_secret=api_secret)
        uid, actid, api_session_key, ws_session_key = conn.get_session_keys()
        # Optionally update Streamlit secrets if needed, but usually not required
        st.info("Session created and keys saved.")

    if st.button("Force Refresh Session"):
        conn.login(api_token=api_token, api_secret=api_secret)
        uid, actid, api_session_key, ws_session_key = conn.get_session_keys()
        # Optionally update Streamlit secrets if needed, but usually not required
        st.success("Session forcibly refreshed!")
    
    st.info(f"Current session key: {api_session_key[:8]}... (hidden for security)")
    st.caption(f"Actid: {actid}")
