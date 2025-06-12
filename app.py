import streamlit as st

st.set_page_config(page_title="Definedge Dashboard", layout="wide")
st.title("Definedge Dashboard")

PAGES = {
    "Holdings/Positions": "holdings",
    # Add other modules as needed
}

page = st.sidebar.selectbox("Go to", list(PAGES.keys()))

if page == "Holdings/Positions":
    import holdings
    holdings.show()
# Add more elif blocks for other modules
