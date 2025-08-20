import streamlit as st
import importlib

# Import session_utils for login/session management
import session_utils

st.set_page_config(page_title="Gopal Mandloi_Dashboard", layout="wide")

PAGES = {
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

# Add Login option at the top of sidebar
st.sidebar.title("Menu")
menu_options = ["Login"] + list(PAGES.keys())
page = st.sidebar.radio("Go to", menu_options)
 
if page == "Login":
    # Show the login/session refresh UI from session_utils
    session_utils.show()
else:
    # Check if session keys exist before showing main pages
    required_keys = [
        "INTEGRATE_UID",
        "INTEGRATE_ACTID",
        "INTEGRATE_API_SESSION_KEY",
        "INTEGRATE_WS_SESSION_KEY",
    ]
    if all(k in st.session_state for k in required_keys):
        modulename = PAGES[page]
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
    else:
        st.warning("Please login first using the 'Login' option in the sidebar to access this feature.")
