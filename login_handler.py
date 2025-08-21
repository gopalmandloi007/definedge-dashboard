import streamlit as st
import requests

API_STEP1 = "https://signin.definedgesecurities.com/auth/realms/debroking/dsbpkc/login/{api_token}"
API_STEP2 = "https://signin.definedgesecurities.com/auth/realms/debroking/dsbpkc/token"

def do_login():
    api_token = st.secrets.get("integrate_api_token")
    api_secret = st.secrets.get("integrate_api_secret")
    st.write(f"api_token: {repr(api_token)}")
    st.write(f"api_secret: {repr(api_secret)}")

    if not api_token or not api_secret:
        st.error("Please add integrate_api_token and integrate_api_secret in Streamlit secrets.")
        return None

    # Step 1 → Get otp_token
    url = API_STEP1.format(api_token=api_token)
    st.write(f"Step 1 URL: {url}")
    try:
        resp = requests.get(url, headers={"api_secret": api_secret})
        st.write("Raw response text:", resp.text)
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
            st.write("Step 2 Raw response:", resp2.text)
            data2 = resp2.json()
        except Exception as e:
            st.error(f"Network error: {e}")
            return None

        if "api_session_key" not in data2:
            st.error(f"Login Step 2 failed: {data2}")
            return None

        st.session_state["integrate_api_session_key"] = data2["api_session_key"]
        st.session_state["susertoken"] = data2.get("susertoken", "")

        st.success("Login successful! Session key stored in memory.")
        st.markdown("### Copy this session key and paste in your `.streamlit/secrets.toml` under `integrate_api_session_key`:")
        st.code(data2["api_session_key"], language="text")
        st.markdown("> **Note:** You can use this session key for 24 hours in your secrets file.")

        return data2["api_session_key"]

    return None
