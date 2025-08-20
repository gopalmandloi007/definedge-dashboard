import streamlit as st
import importlib

st.set_page_config(page_title="Gopal Mandloi_Dashboard", layout="wide")

PAGES = {
    "Login": "login",  # Add login page
    "Holdings": "holdings",
    "Holdings Details": "holdings_details",
    "Positions": "positions",
    "Order Book": "orderbook",
    "Orders": "orders",
    "Order Manage": "order_manage",
    "Limits": "limits",
    "Margin": "margin",
    "Quotes": "quotes",
    "GTT order manage": "gtt",
    "GTT Order Place": "gtt_oco_manage",
    "Square Off": "squareoff",
    "Symbol Technical Details": "symbol_technical_details",
    "Batch Symbol Scanner": "definedge_batch_scan",
    "Candlestick Demo": "simple_chart_demo",
    "Websocket Help": "websocket_help",
}

st.title("Gopal Mandloi Integrate Dashboard")

page = st.sidebar.radio("Go to", list(PAGES.keys()))
modulename = PAGES[page]

# For all non-login pages, check session is active
if page != "Login":
    required_keys = [
        "INTEGRATE_UID",
        "INTEGRATE_ACTID",
        "INTEGRATE_API_SESSION_KEY",
        "INTEGRATE_WS_SESSION_KEY",
    ]
    if not all(k in st.session_state for k in required_keys):
        st.warning("Please login first using the 'Login' option in the sidebar to access this feature.")
        # Optionally: auto-switch to login page (advanced)
        st.stop()

try:
    module = importlib.import_module(modulename)
    if hasattr(module, "show") and callable(getattr(module, "show")):
        module.show()
    else:
        st.error(f"Module `{modulename}` is missing a callable `show()` function.")
except ModuleNotFoundError:
    st.error(f"Module `{modulename}.py` not found.")
except Exception as e:
    st.error(f"Error loading `{modulename}`: {e}")
