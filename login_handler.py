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

    # Step 1: Send api_secret as a query parameter (NOT header)
    url1 = API_STEP1.format(api_token=api_token)
    params1 = {"api_secret": api_secret}
    resp1 = requests.get(url1, params=params1)
    data1 = resp1.json()
    if "otp_token" not in data1:
        st.error(f"Login Step 1 failed: {data1}")
        return None

    otp_token = data1["otp_token"]
    st.info(f"OTP sent to your registered mobile/email.")

    otp_code = st.text_input("Enter OTP (from SMS/Email):", type="password")
    if not otp_code:
        return None

    if st.button("Submit OTP"):
        # Step 2: Send OTP and token in POST body
        payload2 = {"otp_token": otp_token, "otp": otp_code}
        resp2 = requests.post(API_STEP2, json=payload2)
        data2 = resp2.json()
        api_session_key = data2.get("api_session_key", "")
        ws_session_key = data2.get("susertoken", "")

        if not api_session_key or not ws_session_key:
            st.error(f"Login Step 2 failed: {data2}")
            return None

        st.success("Login successful! Copy the below block into your .streamlit/secrets.toml file:")
        st.code(f'''
integrate_api_token = "{api_token}"
integrate_api_secret = "{api_secret}"
integrate_api_session_key = "{api_session_key}"
integrate_ws_session_key = "{ws_session_key}"
''', language="toml")
        return api_session_key

    return None
