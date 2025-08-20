import streamlit as st
from integrate import ConnectToIntegrate

# Optional: For automatic TOTP if you have the TOTP secret
try:
    import pyotp
except ImportError:
    pyotp = None

def update_session_state(uid, actid, api_session_key, ws_session_key):
    st.session_state["INTEGRATE_UID"] = uid
    st.session_state["INTEGRATE_ACTID"] = actid
    st.session_state["INTEGRATE_API_SESSION_KEY"] = api_session_key
    st.session_state["INTEGRATE_WS_SESSION_KEY"] = ws_session_key

def show():
    st.header("Login (OTP Required)")
    try:
        api_token = st.secrets["integrate_api_token"]
        api_secret = st.secrets["integrate_api_secret"]
    except Exception:
        st.error("Please set your API token and secret in Streamlit secrets.")
        return

    # Check if TOTP (auto OTP) is available
    auto_otp = False
    otp_value = None
    if "integrate_totp_secret" in st.secrets and pyotp is not None:
        auto_otp = True
        otp_value = pyotp.TOTP(st.secrets["integrate_totp_secret"]).now()

    session_exists = all(
        k in st.session_state for k in [
            "INTEGRATE_UID", "INTEGRATE_ACTID", "INTEGRATE_API_SESSION_KEY", "INTEGRATE_WS_SESSION_KEY"
        ]
    )
    if session_exists:
        st.success("Session is active! You can use other features.")
        st.info(f"Current session key: {str(st.session_state.get('INTEGRATE_API_SESSION_KEY',''))[:8]}... (hidden)")
        st.caption(f"Actid: {str(st.session_state.get('INTEGRATE_ACTID',''))}")

        with st.expander("Force Refresh Session (OTP required)"):
            if auto_otp:
                otp = otp_value
                st.info(f"Auto OTP generated: {otp}")
            else:
                otp = st.text_input("Enter OTP (from app/SMS)", type="password", key="refresh_otp")
            if st.button("Refresh Session"):
                if otp:
                    conn = ConnectToIntegrate()
                    try:
                        conn.login(api_token=api_token, api_secret=api_secret, totp=otp)
                        uid = getattr(conn, "uid", None)
                        actid = getattr(conn, "actid", None)
                        api_session_key = getattr(conn, "api_session_key", None)
                        ws_session_key = getattr(conn, "ws_session_key", None)
                        update_session_state(uid, actid, api_session_key, ws_session_key)
                        st.success("Session forcibly refreshed!")
                    except Exception as e:
                        st.error(f"Login failed: {e}")
                else:
                    st.error("Please enter the OTP.")
    else:
        st.warning("No active session found. Please login with OTP.")
        if auto_otp:
            otp = otp_value
            st.info(f"Auto OTP generated: {otp}")
        else:
            otp = st.text_input("Enter OTP (from app/SMS)", type="password", key="login_otp")
        if st.button("Login"):
            if otp:
                conn = ConnectToIntegrate()
                try:
                    conn.login(api_token=api_token, api_secret=api_secret, totp=otp)
                    uid = getattr(conn, "uid", None)
                    actid = getattr(conn, "actid", None)
                    api_session_key = getattr(conn, "api_session_key", None)
                    ws_session_key = getattr(conn, "ws_session_key", None)
                    update_session_state(uid, actid, api_session_key, ws_session_key)
                    st.success("Session created successfully!")
                except Exception as e:
                    st.error(f"Login failed: {e}")
            else:
                st.error("Please enter the OTP.")
