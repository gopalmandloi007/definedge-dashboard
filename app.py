import streamlit as st

st.set_page_config(page_title="Definedge Dashboard", layout="wide")
st.title("Definedge Dashboard")

PAGES = {
    "Holdings/Positions": "holdings",
    "Order Book": "order_book",
    "Place Order": "place_order",
    "GTT Orders": "gtt"
}

page = st.sidebar.selectbox("Go to", list(PAGES.keys()))

if page == "Holdings/Positions":
    import holdings
    holdings.show()
elif page == "Order Book":
    import order_book
    order_book.show()
elif page == "Place Order":
    import place_order
    place_order.show()
elif page == "GTT Orders":
    import gtt
    gtt.show()
