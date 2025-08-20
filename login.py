import streamlit as st
from integrate import ConnectToIntegrate

def show():
    st.header("Definedge Manual Login (Copy Session Keys Output)")

    try:
        api_token = st.secrets["integrate_api_token"]
        api_secret = st.secrets["integrate_api_secret"]
    except Exception:
        st.error("Please set your API token and secret in Streamlit secrets.")
        st.stop()

    otp = st.text_input("Enter OTP (from SMS/App)", type="password")

    if st.button("Login"):
        if not otp:
            st.error("Please enter the OTP.")
            return

        conn = ConnectToIntegrate()
        try:
            conn.login(api_token=api_token, api_secret=api_secret, totp=otp)
            # Try to get all possible attribute names
            uid = getattr(conn, "uid", "") or getattr(conn, "user_id", "")
            actid = getattr(conn, "actid", "") or getattr(conn, "account_id", "")
            api_session_key = getattr(conn, "api_session_key", "") or getattr(conn, "session_key", "")
            ws_session_key = getattr(conn, "ws_session_key", "") or getattr(conn, "ws_key", "")
            # If all are blank, show debug info
            if not any([uid, actid, api_session_key, ws_session_key]):
                st.error("Session keys not found! Debug info below:")
                st.write(conn.__dict__)
                return
            st.success("✅ Login successful! Copy below for your .streamlit/secrets.toml 👇")
            st.code(f"""integrate_uid = "{uid}"
integrate_actid = "{actid}"
integrate_api_session_key = "{api_session_key}"
integrate_ws_session_key = "{ws_session_key}" """, language="toml")
            st.info("Copy these 4 lines into your .streamlit/secrets.toml file and rerun the app.")
        except Exception as e:
            st.error(f"Login failed: {e}")
