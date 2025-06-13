import streamlit as st
import importlib

st.set_page_config(page_title="Definedge Integrate Dashboard", layout="wide")
st.title("Definedge Integrate Dashboard")

PAGES = {
    "Holdings": "holdings",
    "Positions": "positions",
    "Order Book": "orderbook",
    "Orders": "orders",
    "Order Manage": "order_manage",
    "Limits": "limits",
    "Margin": "margin",
    "Quotes": "quotes",
    "GTT": "gtt",
    "GTT/OCO Manage": "gtt_oco_manage",
    "Square Off": "squareoff",  # <-- Yeh line add karein
    "Login": "session_utils",
    "Websocket Help": "websocket_help",
}

page = st.sidebar.radio("Go to", list(PAGES.keys()))
modulename = PAGES[page]
try:
    module = importlib.import_module(modulename)
    if hasattr(module, "show"):
        module.show()
    else:
        st.error(f"Module `{modulename}` missing `show()` function.")
except ModuleNotFoundError:
    st.error(f"Module `{modulename}.py` not found.")
except Exception as e:
    st.error(f"Error loading `{modulename}`: {e}")
