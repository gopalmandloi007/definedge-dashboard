import streamlit as st
import requests

@st.cache_resource(show_spinner=False)
def get_api_session_key():
    return st.secrets["integrate_api_session_key"]

def definedge_get(relative_url, params=None):
    url = f"https://trade.definedgesecurities.com{relative_url}"
    headers = {"Authorization": get_api_session_key()}
    try:
        resp = requests.get(url, params=params, headers=headers, timeout=10)
        resp.raise_for_status()
        if "application/json" in resp.headers.get("Content-Type", ""):
            try:
                return resp.json()
            except Exception as e:
                st.error(f"Invalid JSON response: {resp.text[:300]}")
                return {}
        else:
            st.error(f"Non-JSON response received: {resp.text[:300]}")
            return {}
    except requests.exceptions.HTTPError as e:
        st.error(f"HTTP {resp.status_code}: {resp.text[:300]}")
        return {}
    except Exception as e:
        st.error(f"Request error: {str(e)}")
        return {}

def definedge_post(relative_url, data=None):
    url = f"https://trade.definedgesecurities.com{relative_url}"
    headers = {
        "Authorization": get_api_session_key(),
        "Content-Type": "application/json",
    }
    try:
        resp = requests.post(url, json=data, headers=headers, timeout=10)
        resp.raise_for_status()
        if "application/json" in resp.headers.get("Content-Type", ""):
            try:
                return resp.json()
            except Exception as e:
                st.error(f"Invalid JSON response: {resp.text[:300]}")
                return {}
        else:
            st.error(f"Non-JSON response received: {resp.text[:300]}")
            return {}
    except requests.exceptions.HTTPError as e:
        st.error(f"HTTP {resp.status_code}: {resp.text[:300]}")
        return {}
    except Exception as e:
        st.error(f"Request error: {str(e)}")
        return {}
