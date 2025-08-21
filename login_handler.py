import streamlit as st
import requests

API_STEP1 = "https://signin.definedgesecurities.com/auth/realms/debroking/dsbpkc/login/{api_token}"
API_STEP2 = "https://signin.definedgesecurities.com/auth/realms/debroking/dsbpkc/token"

def do_login():
    api_token = st.secrets.get("integrate_api_token")
    api_secret = st.secrets.get("integrate_api_secret")

    if not api_token or not api_secret:
        st.error("Please add integrate_api_token and integrate_api_secret in Streamlit secrets.")
        return None

    # Step 1 → Get otp_token
    try:
        resp = requests.get(API_STEP1.format(api_token=api_token), headers={"api_secret": api_secret})
        data = resp.json()
    except Exception as e:
        st.error(f"Network error: {e}")
        return None

    if "otp_token" not in data:
        st.error(f"Login Step 1 failed: {data}")
        return None

    otp_token = data["otp_token"]
    st.info(f"OTP sent to your registered mobile/email.")

    # Step 2 → Enter OTP in Streamlit
    otp_code = st.text_input("Enter OTP (from SMS/Email):", type="password")
    if not otp_code:
        return None

    if st.button("Submit OTP"):
        payload = {"otp_token": otp_token, "otp": otp_code}
        try:
            resp2 = requests.post(API_STEP2, json=payload)
            data2 = resp2.json()
        except Exception as e:
            st.error(f"Network error: {e}")
            return None

        # Extract API session key and websocket session key
        api_session_key = data2.get("api_session_key", "")
        ws_session_key = data2.get("susertoken", "")

        if not api_session_key or not ws_session_key:
            st.error(f"Login Step 2 failed: {data2}")
            return None

        st.session_state["integrate_api_session_key"] = api_session_key
        st.session_state["integrate_ws_session_key"] = ws_session_key

        st.success("Login successful! Copy the keys below and paste into your `.streamlit/secrets.toml` file:")

        st.markdown("#### Paste in `.streamlit/secrets.toml` (replace old values):")
        st.code(f'''
integrate_api_session_key = "{api_session_key}"
integrate_ws_session_key = "{ws_session_key}"
''', language="toml")
        st.markdown("> **Note:** These keys are valid for ~24 hours. Update them again after expiry.")

        return api_session_key

    return None
