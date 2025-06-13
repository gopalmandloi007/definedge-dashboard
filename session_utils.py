import streamlit as st
import os
import time
from dotenv import load_dotenv, set_key
from integrate import ConnectToIntegrate, IntegrateOrders

dotenv_file = '.env'
load_dotenv(dotenv_file)

def update_env_session_keys(uid, actid, api_session_key, ws_session_key):
    os.environ["INTEGRATE_UID"] = uid
    os.environ["INTEGRATE_ACTID"] = actid
    os.environ["INTEGRATE_API_SESSION_KEY"] = api_session_key
    os.environ["INTEGRATE_WS_SESSION_KEY"] = ws_session_key
    set_key(dotenv_file, "INTEGRATE_UID", uid)
    set_key(dotenv_file, "INTEGRATE_ACTID", actid)
    set_key(dotenv_file, "INTEGRATE_API_SESSION_KEY", api_session_key)
    set_key(dotenv_file, "INTEGRATE_WS_SESSION_KEY", ws_session_key)

def ensure_active_session(conn):
    try:
        io = IntegrateOrders(conn)
        test = io.holdings()
        if (
            isinstance(test, dict)
            and str(test.get("status", "")).upper() in ["FAILED", "FAIL", "ERROR"]
            and "session" in str(test.get("message", "")).lower()
        ):
            st.warning("Session expired, re-logging in.")
            raise Exception("Session expired")
        return io
    except Exception:
        api_token = os.environ["INTEGRATE_API_TOKEN"]
        api_secret = os.environ["INTEGRATE_API_SECRET"]
        conn.login(api_token=api_token, api_secret=api_secret)
        uid, actid, api_session_key, ws_session_key = conn.get_session_keys()
        update_env_session_keys(uid, actid, api_session_key, ws_session_key)
        st.info("Session refreshed successfully.")
        return IntegrateOrders(conn)

def show():
    st.header("Login & Session Key (SDK Mode)")
    # This is called once at app load, or you can make a button for manual refresh
    api_token = os.environ.get("INTEGRATE_API_TOKEN", "")
    api_secret = os.environ.get("INTEGRATE_API_SECRET", "")
    if not api_token or not api_secret:
        st.error("Please set INTEGRATE_API_TOKEN and INTEGRATE_API_SECRET in your .env file.")
        return

    conn = ConnectToIntegrate()
    try:
        uid = os.environ["INTEGRATE_UID"]
        actid = os.environ["INTEGRATE_ACTID"]
        api_session_key = os.environ["INTEGRATE_API_SESSION_KEY"]
        ws_session_key = os.environ["INTEGRATE_WS_SESSION_KEY"]
        conn.set_session_keys(uid, actid, api_session_key, ws_session_key)
    except KeyError:
        st.warning("No previous session found. Logging in...")
        conn.login(api_token=api_token, api_secret=api_secret)
        uid, actid, api_session_key, ws_session_key = conn.get_session_keys()
        update_env_session_keys(uid, actid, api_session_key, ws_session_key)
        st.info("Session created and keys saved.")

    if st.button("Force Refresh Session"):
        conn.login(api_token=api_token, api_secret=api_secret)
        uid, actid, api_session_key, ws_session_key = conn.get_session_keys()
        update_env_session_keys(uid, actid, api_session_key, ws_session_key)
        st.success("Session forcibly refreshed!")
    
    st.info(f"Current session key: {os.environ.get('INTEGRATE_API_SESSION_KEY','')[:8]}... (hidden for security)")
    st.caption(f"Actid: {os.environ.get('INTEGRATE_ACTID','')}")
