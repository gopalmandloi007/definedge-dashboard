import streamlit as st

st.set_page_config(page_title="Definedge Dashboard", layout="wide")
st.title("Definedge Dashboard")

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

if page == "Holdings / Positions":
    import holdings
    holdings.show()
elif page == "Order Book":
    import orderbook
    orderbook.show()
elif page == "Orders (Manage)":
    import orders
    orders.show()
elif page == "Trade Book":
    import tradebook
    tradebook.show()
elif page == "GTT & OCO":
    import gtt
    gtt.show()
elif page == "Limits / Product Conversion":
    import limits
    limits.show()
elif page == "Margins / Span":
    import margin
    margin.show()
elif page == "Quotes & Security Info":
    import quotes
    quotes.show()
elif page == "WebSocket Live Data":
    import websocket_help
    websocket_help.show()
