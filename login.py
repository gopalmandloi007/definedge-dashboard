import streamlit as st
from integrate import ConnectToIntegrate

def show():
    st.header("Definedge Login (Colab-style)")

    # Get API creds from secrets.toml
    try:
        api_token = st.secrets["integrate_api_token"]
        api_secret = st.secrets["integrate_api_secret"]
    except Exception:
        st.error("Please set your API token and secret in .streamlit/secrets.toml")
        st.stop()

    # Step 1: User clicks to generate OTP
    if "otp_sent" not in st.session_state:
        st.session_state.otp_sent = False

    if not st.session_state.otp_sent:
        if st.button("Send OTP to Mobile/Email"):
            # Initiate login to trigger OTP (most brokers require a dummy/fake login to send OTP)
            try:
                # This will fail but send OTP, so we catch the error
                conn = ConnectToIntegrate()
                conn.login(api_token=api_token, api_secret=api_secret, totp="000000")
            except Exception:
                pass  # Ignore error: Purpose is to trigger OTP only
            st.session_state.otp_sent = True
            st.success("OTP sent! Please check your mobile/email.")
        st.stop()

    # Step 2: User enters OTP received on mobile
    otp = st.text_input("Enter OTP you received on mobile/email", type="password")
    if st.button("Login"):
        if not otp:
            st.error("Please enter the OTP.")
            return
        conn = ConnectToIntegrate()
        try:
            conn.login(api_token=api_token, api_secret=api_secret, totp=otp)
            # get_session_keys method (if available), else fallback to attribute names
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
        except Exception as e:
            st.error(f"Login failed: {e}")
            st.session_state.otp_sent = False  # Allow retry
