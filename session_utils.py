import requests
import streamlit as st
import time

SESSION_KEY_VALIDITY_SECONDS = 3000  # 50 minutes

def generate_session_key():
    client_code = st.secrets["CLIENT_CODE"]
    password = st.secrets["PASSWORD"]
    api_url = "https://api.definedge.com/session"  # Update if different

    payload = {
        "clientcode": client_code,
        "password": password
    }
    try:
        response = requests.post(api_url, json=payload, timeout=10)
        data = response.json()
        if data.get("status") == "SUCCESS" and "session_key" in data:
            st.session_state["session_key"] = data["session_key"]
            st.session_state["session_key_time"] = time.time()
            return data["session_key"]
        else:
            st.error(f"Login failed: {data.get('message', 'Unknown error')}")
            return None
    except Exception as e:
        st.error(f"Session key generation error: {e}")
        return None

def get_session_key(force_refresh=False):
    if force_refresh:
        return generate_session_key()
    key = st.session_state.get("session_key")
    key_time = st.session_state.get("session_key_time")
    if key and key_time:
        if time.time() - key_time < SESSION_KEY_VALIDITY_SECONDS:
            return key
    return generate_session_key()

def api_call_with_auto_refresh(url, payload=None, headers=None, method="GET"):
    session_key = get_session_key()
    if headers is None:
        headers = {}
    headers["Authorization"] = f"Bearer {session_key}"

    def make_request():
        if method == "POST":
            resp = requests.post(url, json=payload, headers=headers, timeout=10)
        else:
            resp = requests.get(url, params=payload, headers=headers, timeout=10)
        return resp

    resp = make_request()
    try:
        data = resp.json()
    except Exception:
        st.error("Invalid response from API.")
        return None

    if isinstance(data, dict) and "status" in data and "Session Expired" in str(data.get("message", "")):
        session_key = get_session_key(force_refresh=True)
        headers["Authorization"] = f"Bearer {session_key}"
        resp = make_request()
        try:
            data = resp.json()
        except Exception:
            st.error("Invalid response from API after re-login.")
            return None
    return data
