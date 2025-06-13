import streamlit as st
import importlib
import os
import sys
import os

# Fix sys.path if first entry is 'app.py', replace with current directory
if sys.path[0].endswith("app.py"):
    sys.path[0] = os.path.dirname(os.path.abspath(__file__))
st.set_page_config(page_title="Definedge Integrate Dashboard", layout="wide")  # <-- MUST be first
import sys
st.write("Python sys.path:", sys.path)
# Debug: print files in repo root
st.write("Files in repo root:", os.listdir("."))

try:
    import simple_chart_demo
    st.write("Direct import of simple_chart_demo: SUCCESS")
except Exception as e:
    st.write(f"Direct import of simple_chart_demo failed: {e}")

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
    "GTT order manage": "gtt",
    "GTT Order Place": "gtt_oco_manage",
    "Square Off": "squareoff",
    "Symbol Technical Details": "symbol_technical_details",
    "Definedge Batch Symbol Scanner": "definedge_batch_scan",
    "Candlestick Demo": "simple_chart_demo",
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
