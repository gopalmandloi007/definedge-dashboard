import streamlit as st
from integrate import ConnectToIntegrate, IntegrateOrders

def update_session_state(uid, actid, api_session_key, ws_session_key):
    st.session_state["INTEGRATE_UID"] = uid
    st.session_state["INTEGRATE_ACTID"] = actid
    st.session_state["INTEGRATE_API_SESSION_KEY"] = api_session_key
    st.session_state["INTEGRATE_WS_SESSION_KEY"] = ws_session_key

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
        creds = st.secrets["integrate"]
        api_token = creds["api_token"]
        api_secret = creds["api_secret"]
        conn.login(api_token=api_token, api_secret=api_secret)
        uid, actid, api_session_key, ws_session_key = conn.get_session_keys()
        update_session_state(uid, actid, api_session_key, ws_session_key)
        st.info("Session refreshed successfully.")
        return IntegrateOrders(conn)

def show():
    st.header("Login & Session Key (SDK Mode)")
    try:
        creds = st.secrets["integrate"]
        api_token = creds["api_token"]
        api_secret = creds["api_secret"]
    except Exception:
        st.error("Please set your API token and secret in Streamlit secrets.")
        return

    # Try to restore previous session from session_state
    if all(k in st.session_state for k in [
        "INTEGRATE_UID", "INTEGRATE_ACTID", "INTEGRATE_API_SESSION_KEY", "INTEGRATE_WS_SESSION_KEY"
    ]):
        conn = ConnectToIntegrate()
        conn.set_session_keys(
            st.session_state["INTEGRATE_UID"],
            st.session_state["INTEGRATE_ACTID"],
            st.session_state["INTEGRATE_API_SESSION_KEY"],
            st.session_state["INTEGRATE_WS_SESSION_KEY"],
        )
    else:
        st.warning("No previous session found or session expired. Logging in...")
        conn = ConnectToIntegrate()
        conn.login(api_token=api_token, api_secret=api_secret)
        uid, actid, api_session_key, ws_session_key = conn.get_session_keys()
        update_session_state(uid, actid, api_session_key, ws_session_key)
        st.info("Session created and keys saved in memory.")

    if st.button("Force Refresh Session"):
        conn.login(api_token=api_token, api_secret=api_secret)
        uid, actid, api_session_key, ws_session_key = conn.get_session_keys()
        update_session_state(uid, actid, api_session_key, ws_session_key)
        st.success("Session forcibly refreshed!")

    st.info(f"Current session key: {str(st.session_state.get('INTEGRATE_API_SESSION_KEY',''))[:8]}... (hidden for security)")
    st.caption(f"Actid: {str(st.session_state.get('INTEGRATE_ACTID',''))}")
