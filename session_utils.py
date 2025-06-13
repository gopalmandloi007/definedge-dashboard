import requests
import streamlit as st

def generate_session_key():
    client_code = st.secrets["CLIENT_CODE"]
    password = st.secrets["PASSWORD"]
    api_url = "https://api.definedge.com/session"  # Update if your endpoint differs

    payload = {
        "clientcode": client_code,
        "password": password
    }
    try:
        response = requests.post(api_url, json=payload, timeout=10)
        data = response.json()
        if data.get("status") == "SUCCESS" and "session_key" in data:
            st.session_state["session_key"] = data["session_key"]
            return data["session_key"]
        else:
            st.error(f"Login failed: {data.get('message', 'Unknown error')}")
            return None
    except Exception as e:
        st.error(f"Session key generation error: {e}")
        return None

def get_session_key():
    if "session_key" in st.session_state:
        return st.session_state["session_key"]
    return generate_session_key()
