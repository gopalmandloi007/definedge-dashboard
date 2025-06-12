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

        qty_option = st.radio("Quantity to Square Off", ["Full", "Partial"], horizontal=True)
        if qty_option == "Partial":
            squareoff_qty = st.number_input(
                "Enter quantity to square off", min_value=1, max_value=int(qty), value=int(qty)
            )
        else:
            squareoff_qty = int(qty)

        price_option = st.radio("Order Type", ["Market Order", "Limit Order"], horizontal=True)
        if price_option == "Limit Order":
            default_price = float(holding.get("avg_buy_price") or 0)
            price = st.number_input("Limit Price (₹)", min_value=0.01, value=round(default_price,2))
            price_type = "LIMIT"
        else:
            price = 0.0
            price_type = "MARKET"

        product_type = "CNC"
        order_type = "SELL"
        validity = st.selectbox("Order Validity", ["DAY", "IOC", "EOS"], index=0)
        remarks = st.text_input("Remarks (optional)")
        disclosed_quantity = st.number_input(
            "Disclosed Quantity (optional)", min_value=0, max_value=squareoff_qty, value=0
        ) if st.checkbox("Disclose Partial Quantity?") else None

        st.markdown("---")
        submitted = st.form_submit_button("🟢 Place Square Off Order")
        if submitted:
            payload = {
                "exchange": exch,
                "tradingsymbol": tradingsymbol,
                "order_type": order_type,
                "quantity": str(squareoff_qty),
                "price": str(price),
                "price_type": price_type,
                "product_type": product_type,
                "validity": validity,
            }
            if remarks:
                payload["remarks"] = remarks
            if disclosed_quantity and disclosed_quantity > 0:
                payload["disclosed_quantity"] = str(disclosed_quantity)
            with st.spinner("Placing order..."):
                resp = integrate_post("/placeorder", payload)
            status = resp.get('status') or resp.get('message') or resp
            st.success(f"Order Response: {status}")
            st.json(resp)

def squareoff_position_form(pos, qty):
    st.markdown(f"### {pos.get('tradingsymbol','')} ({qty} Qty)")
    st.write(f"**Exchange:** {pos.get('exchange','')}")
    st.write(f"**Product:** {pos.get('product_type','')}")
    st.write(f"**Avg Price:** ₹{pos.get('avg_price','-')}")
    st.write(f"**Last Price:** ₹{pos.get('last_price','-')}")
    st.write(f"**Side:** {pos.get('buy_or_sell','')}")

    with st.form(key=f"squareoff_pos_form_{pos.get('tradingsymbol', '')}"):
        qty_option = st.radio("Quantity to Square Off", ["Full", "Partial"], horizontal=True)
        if qty_option == "Partial":
            squareoff_qty = st.number_input(
                "Enter quantity to square off", min_value=1, max_value=int(qty), value=int(qty)
            )
        else:
            squareoff_qty = int(qty)

        price_option = st.radio("Order Type", ["Market Order", "Limit Order"], horizontal=True)
        if price_option == "Limit Order":
            default_price = float(pos.get("avg_price") or pos.get("last_price") or 0)
            price = st.number_input("Limit Price (₹)", min_value=0.01, value=round(default_price,2))
            price_type = "LIMIT"
        else:
            price = 0.0
            price_type = "MARKET"

        # BUY position ko SELL se squareoff karna hai, SELL position ko BUY se
        order_type = "SELL" if pos.get('buy_or_sell', 'BUY') == "BUY" else "BUY"
        product_type = pos.get("product_type", "INTRADAY")
        validity = st.selectbox("Order Validity", ["DAY", "IOC", "EOS"], index=0)
        remarks = st.text_input("Remarks (optional)")
        disclosed_quantity = st.number_input(
            "Disclosed Quantity (optional)", min_value=0, max_value=squareoff_qty, value=0
        ) if st.checkbox("Disclose Partial Quantity?") else None

        st.markdown("---")
        submitted = st.form_submit_button("🟢 Place Square Off Order")
        if submitted:
            payload = {
                "exchange": pos.get("exchange", ""),
                "tradingsymbol": pos.get("tradingsymbol", ""),
                "order_type": order_type,
                "quantity": str(squareoff_qty),
                "price": str(price),
                "price_type": price_type,
                "product_type": product_type,
                "validity": validity,
            }
            if remarks:
                payload["remarks"] = remarks
            if disclosed_quantity and disclosed_quantity > 0:
                payload["disclosed_quantity"] = str(disclosed_quantity)
            with st.spinner("Placing order..."):
                resp = integrate_post("/placeorder", payload)
            status = resp.get('status') or resp.get('message') or resp
            st.success(f"Order Response: {status}")
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

    st.markdown("---")
    st.header("📝 Positions")
    pos_data = integrate_get("/positions")
    positions = pos_data.get("positions", [])
    positions = [p for p in positions if int(float(p.get("quantity", 0))) > 0]
    if not positions:
        st.info("No positions to square off.")
    else:
        for pos in positions:
            qty = int(float(pos.get("quantity", 0)))
            with st.expander(f"{pos.get('tradingsymbol', '')} | Qty: {qty} | Side: {pos.get('buy_or_sell', '')}"):
                squareoff_position_form(pos, qty)
