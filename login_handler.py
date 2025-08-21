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
    resp = requests.get(API_STEP1.format(api_token=api_token), headers={"api_secret": api_secret})
    data = resp.json()
    if "otp_token" not in data:
        st.error(f"Login Step 1 failed: {data}")
        return None
    otp_token = data["otp_token"]
    st.info(f"OTP sent to your registered mobile/email.")

    # Step 2 → Enter OTP in Streamlit
    otp_code = st.text_input("Enter OTP:", type="password")
    if not otp_code:
        return None

    if st.button("Submit OTP"):
        payload = {"otp_token": otp_token, "otp": otp_code}
        resp2 = requests.post(API_STEP2, json=payload)
        data2 = resp2.json()
        if "api_session_key" not in data2:
            st.error(f"Login Step 2 failed: {data2}")
            return None

        # Save in secrets (runtime only)
        st.session_state["integrate_api_session_key"] = data2["api_session_key"]
        st.session_state["susertoken"] = data2["susertoken"]

        st.success("Login successful! Session key stored.")
        return data2["api_session_key"]

    return None
