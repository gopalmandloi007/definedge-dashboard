import streamlit as st
from utils import integrate_get, integrate_post

def squareoff_hold_form(holding, qty, tradingsymbols):
    # ... (form code yahan rahe)
    pass  # <-- apna actual form code yahan likhein

def show():
    st.title("⚡ Definedge Integrate Dashboard")
    st.subheader("💼 Square Off Positions & Holdings")
    st.markdown("---")
    st.header("📦 Holdings")
    data = integrate_get("/holdings")
    holdings = data.get("data", [])
    user_holdings = []
    for h in holdings:
        qty = int(float(h.get("dp_qty", 0)))
        tradingsymbols = h.get("tradingsymbol", [])
        if qty > 0 and tradingsymbols and isinstance(tradingsymbols, list):
            user_holdings.append((h, qty, tradingsymbols))
    if not user_holdings:
        st.info("No holdings to square off.")
    else:
        for holding, qty, tradingsymbols in user_holdings:
            with st.expander(f"{tradingsymbols[0]['tradingsymbol']} | Qty: {qty}", expanded=False):
                squareoff_hold_form(holding, qty, tradingsymbols)
