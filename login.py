import streamlit as st
from integrate import ConnectToIntegrate

def update_session_secrets(uid, actid, api_session_key, ws_session_key):
    # Update runtime secrets so legacy code works everywhere
    st.secrets["integrate_uid"] = uid
    st.secrets["integrate_actid"] = actid
    st.secrets["integrate_api_session_key"] = api_session_key
    st.secrets["integrate_ws_session_key"] = ws_session_key

def show():
    st.header("Login (OTP Required)")

    try:
        api_token = st.secrets["integrate_api_token"]
        api_secret = st.secrets["integrate_api_secret"]
    except Exception:
        st.error("Please set your API token and secret in Streamlit secrets.")
        return

    session_exists = all(
        k in st.secrets for k in [
            "integrate_uid", "integrate_actid", "integrate_api_session_key", "integrate_ws_session_key"
        ]
    )
    if session_exists:
        st.success("Session is active! You can use other features.")
        st.info(f"Current session key: {str(st.secrets.get('integrate_api_session_key',''))[:8]}... (hidden)")
        st.caption(f"Actid: {str(st.secrets.get('integrate_actid',''))}")

        with st.expander("Force Refresh Session (OTP required)"):
            otp = st.text_input("Enter OTP (from app/SMS/Email)", type="password", key="refresh_otp")
            if st.button("Refresh Session"):
                if otp:
                    conn = ConnectToIntegrate()
                    try:
                        conn.login(api_token=api_token, api_secret=api_secret, totp=otp)
                        uid = getattr(conn, "uid", None)
                        actid = getattr(conn, "actid", None)
                        api_session_key = getattr(conn, "api_session_key", None)
                        ws_session_key = getattr(conn, "ws_session_key", None)
                        update_session_secrets(uid, actid, api_session_key, ws_session_key)
                        st.success("Session forcibly refreshed!")
                    except Exception as e:
                        st.error(f"Login failed: {e}")
                else:
                    st.error("Please enter the OTP.")
    else:
        st.warning("No active session found. Please login with OTP.")
        otp = st.text_input("Enter OTP (from app/SMS/Email)", type="password", key="login_otp")
        if st.button("Login"):
            if otp:
                conn = ConnectToIntegrate()
                try:
                    conn.login(api_token=api_token, api_secret=api_secret, totp=otp)
                    uid = getattr(conn, "uid", None)
                    actid = getattr(conn, "actid", None)
                    api_session_key = getattr(conn, "api_session_key", None)
                    ws_session_key = getattr(conn, "ws_session_key", None)
                    update_session_secrets(uid, actid, api_session_key, ws_session_key)
                    st.success("Session created successfully!")
                except Exception as e:
                    st.error(f"Login failed: {e}")
            else:
                st.error("Please enter the OTP.")
