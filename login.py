import streamlit as st
from integrate import ConnectToIntegrate

def update_session_state(uid, actid, api_session_key, ws_session_key):
    st.session_state["INTEGRATE_UID"] = uid
    st.session_state["INTEGRATE_ACTID"] = actid
    st.session_state["INTEGRATE_API_SESSION_KEY"] = api_session_key
    st.session_state["INTEGRATE_WS_SESSION_KEY"] = ws_session_key

def show():
    st.header("Login (OTP Required)")
    try:
        creds = st.secrets["integrate"]
        api_token = creds["api_token"]
        api_secret = creds["api_secret"]
    except Exception:
        st.error("Please set your API token and secret in Streamlit secrets.")
        return

    # Agar already session hai toh message dikhao
    if all(k in st.session_state for k in [
        "INTEGRATE_UID", "INTEGRATE_ACTID", "INTEGRATE_API_SESSION_KEY", "INTEGRATE_WS_SESSION_KEY"
    ]):
        st.success("Session is active! You can use other features.")
        st.info(f"Current session key: {str(st.session_state.get('INTEGRATE_API_SESSION_KEY',''))[:8]}... (hidden)")
        st.caption(f"Actid: {str(st.session_state.get('INTEGRATE_ACTID',''))}")
        if st.button("Force Refresh Session (OTP required)"):
            otp = st.text_input("Enter OTP (from app/SMS)", type="password", key="refresh_otp")
            if otp:
                conn = ConnectToIntegrate()
                try:
                    conn.login(api_token=api_token, api_secret=api_secret, totp=otp)
                    uid, actid, api_session_key, ws_session_key = conn.get_session_keys()
                    update_session_state(uid, actid, api_session_key, ws_session_key)
                    st.success("Session forcibly refreshed!")
                except Exception as e:
                    st.error(f"Login failed: {e}")
    else:
        st.warning("No active session found. Please login with OTP.")
        otp = st.text_input("Enter OTP (from app/SMS)", type="password", key="login_otp")
        if st.button("Login"):
            if otp:
                conn = ConnectToIntegrate()
                try:
                    conn.login(api_token=api_token, api_secret=api_secret, totp=otp)
                    uid, actid, api_session_key, ws_session_key = conn.get_session_keys()
                    update_session_state(uid, actid, api_session_key, ws_session_key)
                    st.success("Session created successfully!")
                except Exception as e:
                    st.error(f"Login failed: {e}")
            else:
                st.error("Please enter the OTP.")
