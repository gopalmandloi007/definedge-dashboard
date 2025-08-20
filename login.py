import streamlit as st
from integrate import ConnectToIntegrate

def show():
    st.header("Definedge Login (Colab-style, Proper OTP Flow)")

    # Get API creds from secrets.toml
    try:
        api_token = st.secrets["integrate_api_token"]
        api_secret = st.secrets["integrate_api_secret"]
    except Exception:
        st.error("Please set your API token and secret in .streamlit/secrets.toml")
        st.stop()

    if "otp_sent" not in st.session_state:
        st.session_state.otp_sent = False

    if not st.session_state.otp_sent:
        if st.button("Send OTP to Mobile/Email"):
            try:
                # Most brokers: dummy login with wrong OTP triggers OTP send
                conn = ConnectToIntegrate()
                try:
                    conn.login(api_token=api_token, api_secret=api_secret, totp="000000")
                except Exception:
                    pass  # Ignore - intent is just to send OTP
                st.session_state.otp_sent = True
                st.success("OTP sent! Please check your mobile/email.")
                st.experimental_rerun()
            except Exception as e:
                st.error(f"OTP send failed: {e}")
        st.stop()
    else:
        otp = st.text_input("Enter OTP received on mobile/email", type="password")
        if st.button("Login"):
            if not otp:
                st.error("Please enter the OTP.")
                return
            conn = ConnectToIntegrate()
            try:
                conn.login(api_token=api_token, api_secret=api_secret, totp=otp)
                # Try get_session_keys method, fallback to attributes
                try:
                    uid, actid, api_session_key, ws_session_key = conn.get_session_keys()
                except Exception:
                    d = conn.__dict__
                    uid = d.get("uid") or d.get("user_id") or ""
                    actid = d.get("actid") or d.get("account_id") or ""
                    api_session_key = d.get("api_session_key") or d.get("session_key") or ""
                    ws_session_key = d.get("ws_session_key") or d.get("ws_key") or ""
                st.success("✅ Login successful! Copy these lines to your .streamlit/secrets.toml:")
                st.code(f"""integrate_uid = "{uid}"
integrate_actid = "{actid}"
integrate_api_session_key = "{api_session_key}"
integrate_ws_session_key = "{ws_session_key}" """, language="toml")
                st.info("Paste above lines into your .streamlit/secrets.toml and rerun the app.")
                st.session_state.otp_sent = False  # Reset for next time
            except Exception as e:
                st.error(f"Login failed: {e}")
                st.session_state.otp_sent = False  # Allow retry
