import streamlit as st
import importlib

st.set_page_config(page_title="Definedge Dashboard", layout="wide")
st.title("Definedge Dashboard")

# List all page files (without .py extension)
PAGES = {
    "Holdings / Positions": "holdings",
    "Order Book": "orderbook",
    "Orders (Manage)": "orders",
    "Trade Book": "tradebook",
    "GTT & OCO": "gtt",
    "Limits / Product Conversion": "limits",
    "Margins / Span": "margin",
    "Quotes & Security Info": "quotes",
    "WebSocket Live Data": "websocket_help",
}

page = st.sidebar.radio("Go to", list(PAGES.keys()))

# Try importing the selected page module
page_module_name = PAGES[page]

try:
    page_module = importlib.import_module(page_module_name)
    if hasattr(page_module, 'show'):
        page_module.show()
    else:
        st.error(f"Module `{page_module_name}` found but missing a `show()` function.")
except ModuleNotFoundError:
    st.error(f"Module `{page_module_name}.py` not found. Please create this file in your project directory.")
except Exception as e:
    st.error(f"Error loading `{page_module_name}`: {e}")
