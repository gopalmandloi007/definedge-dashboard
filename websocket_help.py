import streamlit as st

def show():
    st.header("🌐 WebSocket API Help")
    st.markdown("""
- One connection at a time, 500 tokens max per WS.
- Use wss://trade.definedgesecurities.com/NorenWSTRTP/
- Send JSON for connect, subscribe (touchline/depth), order update, and heartbeats as per API docs.
- See [API Docs](#) or ask the developer for ready-to-use Python code snippets!
- **Note:** Streamlit cannot do native WebSocket feeds, but you can run a background process and push data to Streamlit via files/database.
    """)
