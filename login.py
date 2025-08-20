import streamlit as st
from integrate import ConnectToIntegrate

def show():
    st.header("Login (OTP Manual)")

    try:
        api_token = st.secrets["integrate_api_token"]
        api_secret = st.secrets["integrate_api_secret"]
    except Exception:
        st.error("Please set your API token and secret in Streamlit secrets.")
        return

    otp = st.text_input("Enter OTP (from app/SMS/Email)", type="password", key="login_otp")

    if st.button("Login"):
        if otp:
            conn = ConnectToIntegrate()
            try:
                conn.login(api_token=api_token, api_secret=api_secret, totp=otp)
                uid = getattr(conn, "uid", "")
                actid = getattr(conn, "actid", "")
                api_session_key = getattr(conn, "api_session_key", "")
                ws_session_key = getattr(conn, "ws_session_key", "")
                st.success("Login successful!")
                st.code(f"""
integrate_uid = "{uid}"
integrate_actid = "{actid}"
integrate_api_session_key = "{api_session_key}"
integrate_ws_session_key = "{ws_session_key}"
                """, language="toml")
                st.info("Copy-paste these lines into your .streamlit/secrets.toml file for all legacy code to work.")
            except Exception as e:
                st.error(f"Login failed: {e}")
        else:
            st.error("Please enter the OTP.")
