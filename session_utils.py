import streamlit as st
from integrate import ConnectToIntegrate, IntegrateOrders

def update_session_state(uid, actid, api_session_key, ws_session_key):
    st.session_state["INTEGRATE_UID"] = uid
    st.session_state["INTEGRATE_ACTID"] = actid
    st.session_state["INTEGRATE_API_SESSION_KEY"] = api_session_key
    st.session_state["INTEGRATE_WS_SESSION_KEY"] = ws_session_key

def login_with_otp(api_token, api_secret):
    otp = st.text_input("Enter OTP (from app/SMS)", type="password")
    login_btn = st.button("Login / Refresh Session")
    if login_btn and otp:
        conn = ConnectToIntegrate()
        try:
            conn.login(api_token=api_token, api_secret=api_secret, totp=otp)
            uid, actid, api_session_key, ws_session_key = conn.get_session_keys()
            update_session_state(uid, actid, api_session_key, ws_session_key)
            st.success("Session created/refreshed successfully!")
            return conn
        except Exception as e:
            st.error(f"Login failed: {e}")
            return None
    return None

def ensure_active_session(conn):
    try:
        io = IntegrateOrders(conn)
        test = io.holdings()
        if (
            isinstance(test, dict)
            and str(test.get("status", "")).upper() in ["FAILED", "FAIL", "ERROR"]
            and "session" in str(test.get("message", "")).lower()
        ):
            st.warning("Session expired, please login again with OTP.")
            raise Exception("Session expired")
        return io
    except Exception:
        st.warning("Session expired. Please login again with OTP from the Login page.")
        # Let the main app handle login UI
        return None

def show():
    st.header("Login & Session Key (SDK Mode)")
    try:
        creds = st.secrets["integrate"]
        api_token = creds["api_token"]
        api_secret = creds["api_secret"]
    except Exception:
        st.error("Please set your API token and secret in Streamlit secrets.")
        return

    # Check if session exists
    if all(k in st.session_state for k in [
        "INTEGRATE_UID", "INTEGRATE_ACTID", "INTEGRATE_API_SESSION_KEY", "INTEGRATE_WS_SESSION_KEY"
    ]):
        st.success("Session is active! You can use other features.")
        st.info(f"Current session key: {str(st.session_state.get('INTEGRATE_API_SESSION_KEY',''))[:8]}... (hidden)")
        st.caption(f"Actid: {str(st.session_state.get('INTEGRATE_ACTID',''))}")
        if st.checkbox("Force Refresh Session (OTP required)"):
            login_with_otp(api_token, api_secret)
    else:
        st.warning("No active session found. Please login with OTP.")
        login_with_otp(api_token, api_secret)
