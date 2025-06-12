import streamlit as st
from utils import integrate_get, integrate_post

def squareoff_hold_form(holding, qty, tradingsymbols):
    st.markdown(f"### {tradingsymbols[0]['tradingsymbol']} ({qty} Qty)")
    st.write(f"**ISIN:** {tradingsymbols[0].get('isin', '')}")
    st.write(f"**Exchanges:** " + " / ".join([x['exchange'] for x in tradingsymbols]))
    st.write(f"**Avg Buy Price:** ₹{holding.get('avg_buy_price','-')}")
    st.write(f"**DP Quantity:** {holding.get('dp_qty','-')}")
    st.write(f"**T1 Quantity:** {holding.get('t1_qty','-')}")
    st.write(f"**Haircut:** {holding.get('haircut','-')}")

    with st.form(key=f"squareoff_hold_form_{tradingsymbols[0]['tradingsymbol']}"):
        exch_names = [x['exchange'] for x in tradingsymbols]
        exch = st.selectbox("Select Exchange", exch_names)
        ts_info = next(x for x in tradingsymbols if x['exchange'] == exch)
        tradingsymbol = ts_info["tradingsymbol"]
        token = ts_info["token"]

        col1, col2 = st.columns(2)
        with col1:
            qty_option = st.radio("Quantity to Square Off", ["Full", "Partial"], horizontal=True)
            if qty_option == "Partial":
                squareoff_qty = st.number_input(
                    "Enter quantity to square off", min_value=1, max_value=int(qty), value=int(qty)
                )
            else:
                squareoff_qty = int(qty)
        with col2:
            price_option = st.radio("Square Off At", ["Market Price", "Limit Price"], horizontal=True)
            if price_option == "Limit Price":
                default_price = float(holding.get("avg_buy_price") or 0)
                squareoff_price = st.number_input(
                    "Limit Price (₹)", min_value=0.01, value=round(default_price,2)
                )
                price_type = "LIMIT"
            else:
                squareoff_price = 0.0
                price_type = "MARKET"

        st.markdown("---")
        submitted = st.form_submit_button("🟢 Confirm Square Off")
        if submitted:
            payload = {
                "exchange": exch,
                "tradingsymbol": tradingsymbol,
                "token": token,
                "quantity": str(squareoff_qty),
                "order_type": "SELL",
                "price": str(squareoff_price),
                "price_type": price_type,
                "product_type": "CNC",
            }
            with st.spinner("Placing square off order..."):
                resp = integrate_post("/squareoff", payload)
            st.success("Order placed!")
            st.json(resp)

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
