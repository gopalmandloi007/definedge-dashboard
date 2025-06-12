import streamlit as st
import requests

@st.cache_resource(show_spinner=False)
def get_api_session_key():
    # Load from streamlit secrets (you must set these in .streamlit/secrets.toml)
    return st.secrets["integrate_api_session_key"]

def definedge_get(relative_url, params=None):
    url = f"https://trade.definedgesecurities.com{relative_url}"
    headers = {"Authorization": get_api_session_key()}
    return requests.get(url, params=params, headers=headers).json()

def definedge_post(relative_url, data=None):
    url = f"https://trade.definedgesecurities.com{relative_url}"
    headers = {
        "Authorization": get_api_session_key(),
        "Content-Type": "application/json",
    }
    return requests.post(url, json=data, headers=headers).json()

def definedge_csv(relative_url):
    url = f"https://data.definedgesecurities.com{relative_url}"
    headers = {"Authorization": get_api_session_key()}
    return requests.get(url, headers=headers).text
