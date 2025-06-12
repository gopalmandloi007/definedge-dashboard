import streamlit as st
import requests

BASE_URL = "https://integrate.definedgesecurities.com/dart/v1"

@st.cache_resource(show_spinner=False)
def get_api_session_key():
    return st.secrets["integrate_api_session_key"]

def integrate_get(endpoint, params=None):
    url = BASE_URL + endpoint
    headers = {"Authorization": get_api_session_key()}
    try:
        resp = requests.get(url, headers=headers, params=params, timeout=10)
        resp.raise_for_status()
        if "application/json" in resp.headers.get("Content-Type", ""):
            return resp.json()
        else:
            st.error(f"Non-JSON response: {resp.text[:200]}")
            return {}
    except Exception as e:
        st.error(f"GET {url} failed: {e}")
        return {}

def integrate_post(endpoint, data=None):
    url = BASE_URL + endpoint
    headers = {"Authorization": get_api_session_key(), "Content-Type": "application/json"}
    try:
        resp = requests.post(url, headers=headers, json=data, timeout=10)
        resp.raise_for_status()
        if "application/json" in resp.headers.get("Content-Type", ""):
            return resp.json()
        else:
            st.error(f"Non-JSON response: {resp.text[:200]}")
            return {}
    except Exception as e:
        st.error(f"POST {url} failed: {e}")
        return {}

def integrate_put(endpoint, data=None):
    url = BASE_URL + endpoint
    headers = {"Authorization": get_api_session_key(), "Content-Type": "application/json"}
    try:
        resp = requests.put(url, headers=headers, json=data, timeout=10)
        resp.raise_for_status()
        if "application/json" in resp.headers.get("Content-Type", ""):
            return resp.json()
        else:
            st.error(f"Non-JSON response: {resp.text[:200]}")
            return {}
    except Exception as e:
        st.error(f"PUT {url} failed: {e}")
        return {}

def integrate_delete(endpoint, params=None):
    url = BASE_URL + endpoint
    headers = {"Authorization": get_api_session_key()}
    try:
        resp = requests.delete(url, headers=headers, params=params, timeout=10)
        resp.raise_for_status()
        if "application/json" in resp.headers.get("Content-Type", ""):
            return resp.json()
        else:
            st.error(f"Non-JSON response: {resp.text[:200]}")
            return {}
    except Exception as e:
        st.error(f"DELETE {url} failed: {e}")
        return {}
