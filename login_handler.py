import streamlit as st
import requests

API_STEP1 = "https://signin.definedgesecurities.com/auth/realms/debroking/dsbpkc/login/{api_token}"
API_STEP2 = "https://signin.definedgesecurities.com/auth/realms/debroking/dsbpkc/token"

def do_login():
    api_token = st.secrets.get("integrate_api_token")
    api_secret = st.secrets.get("integrate_api_secret")
    integrate_uid = st.secrets.get("integrate_uid", "")
    integrate_actid = st.secrets.get("integrate_actid", "")

    if not api_token or not api_secret:
        st.error("Please add integrate_api_token and integrate_api_secret in Streamlit secrets.")
        return None

    # Step 1 → Get otp_token
    url = API_STEP1.format(api_token=api_token)
    resp = requests.get(url, params={"api_secret": api_secret})
    data = resp.json()

    if "otp_token" not in data:
        st.error(f"Login Step 1 failed: {data}")
        return None

    otp_token = data["otp_token"]
    st.info(f"OTP sent to your registered mobile/email.")

    # OTP entry
    otp_code = st.text_input("Enter OTP (from SMS/Email):", type="password")
    if not otp_code:
        return None

    if st.button("Submit OTP"):
        payload = {"otp_token": otp_token, "otp": otp_code}
        resp2 = requests.post(API_STEP2, json=payload)
        data2 = resp2.json()

        # Extract keys
        api_session_key = data2.get("api_session_key", "")
        ws_session_key = data2.get("susertoken", "")
        uid = data2.get("uid", integrate_uid)
        actid = data2.get("actid", integrate_actid)

        if not api_session_key or not ws_session_key:
            st.error(f"Login Step 2 failed: {data2}")
            return None

        st.session_state["integrate_api_session_key"] = api_session_key
        st.session_state["integrate_ws_session_key"] = ws_session_key
        st.session_state["integrate_uid"] = uid
        st.session_state["integrate_actid"] = actid

        st.success("Login successful! Copy the below block into your .streamlit/secrets.toml file:")

        st.code(f'''
integrate_api_token = "{api_token}"
integrate_api_secret = "{api_secret}"
integrate_uid = "{uid}"
integrate_actid = "{actid}"
integrate_api_session_key = "{api_session_key}"
integrate_ws_session_key = "{ws_session_key}"
''', language="toml")

        st.markdown("> **Note:** Update these values in `.streamlit/secrets.toml` after every fresh login/OTP. File is already in `.gitignore` so safe.")

        return api_session_key

    return None
