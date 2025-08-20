import streamlit as st
from integrate import ConnectToIntegrate

st.header("Definedge Manual Login (Copy Session Keys Output)")

try:
    api_token = st.secrets["integrate_api_token"]
    api_secret = st.secrets["integrate_api_secret"]
except Exception:
    st.error("Please set your API token and secret in Streamlit secrets.")
    st.stop()

otp = st.text_input("Enter OTP (from SMS/App)", type="password")

if st.button("Login"):
    if otp:
        conn = ConnectToIntegrate()
        try:
            # Try both attribute and method for session keys
            login_result = conn.login(api_token=api_token, api_secret=api_secret, totp=otp)
            # Try .get_session_keys() first, fallback to attributes
            try:
                uid, actid, api_session_key, ws_session_key = conn.get_session_keys()
            except Exception:
                # Fallback to common attribute names
                d = conn.__dict__
                st.write("DEBUG: Login attributes", d)
                uid = d.get("uid") or d.get("user_id") or ""
                actid = d.get("actid") or d.get("account_id") or ""
                api_session_key = d.get("api_session_key") or d.get("session_key") or ""
                ws_session_key = d.get("ws_session_key") or d.get("ws_key") or ""
            # Output for secrets.toml
            st.success("✅ Login successful! Copy below for your .streamlit/secrets.toml 👇")
            st.code(f"""integrate_uid = "{uid}"
integrate_actid = "{actid}"
integrate_api_session_key = "{api_session_key}"
integrate_ws_session_key = "{ws_session_key}" """, language="toml")
            st.info("Copy these 4 lines into your .streamlit/secrets.toml file and rerun the app.")
        except Exception as e:
            st.error(f"Login failed: {e}")
    else:
        st.error("Please enter the OTP.")
