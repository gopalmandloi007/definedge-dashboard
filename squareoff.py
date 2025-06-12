import streamlit as st
from utils import integrate_get, integrate_post

def squareoff_hold_form(holding, quantity):
    st.write(f"**Holding:** {holding.get('tradingsymbol', '')}")

    qty_option = st.radio(
        "Quantity to Square Off",
        ["Full", "Partial"],
        horizontal=True,
        key=f"qty_option_{holding.get('tradingsymbol', '')}_holding"
    )
    if qty_option == "Partial":
        squareoff_qty = st.number_input(
            "Enter quantity to square off",
            min_value=1,
            max_value=quantity,
            value=quantity,
            key=f"qty_input_{holding.get('tradingsymbol', '')}_holding"
        )
    else:
        squareoff_qty = quantity

    price_option = st.radio(
        "Square Off At",
        ["Market Price", "Limit Price"],
        horizontal=True,
        key=f"price_option_{holding.get('tradingsymbol', '')}_holding"
    )
    if price_option == "Limit Price":
        default_price = float(holding.get("avg_buy_price") or 0)
        squareoff_price = st.number_input(
            "Limit Price",
            min_value=0.0,
            value=default_price,
            key=f"price_input_{holding.get('tradingsymbol', '')}_holding"
        )
        price_type = "LIMIT"
    else:
        squareoff_price = 0.0
        price_type = "MARKET"

    submit = st.form_submit_button("Confirm Square Off")
    if submit:
        payload = {
            "exchange": holding.get("exchange", ""),
            "tradingsymbol": holding.get("tradingsymbol", ""),
            "quantity": str(squareoff_qty),
            "order_type": "SELL",
            "price": str(squareoff_price),
            "price_type": price_type,
            "product_type": "CNC",  # Usually for holdings
        }
        resp = integrate_post("/squareoff", payload)  # Change endpoint if needed
        st.success("Square Off Response:")
        st.json(resp)

def squareoff_position_form(position, quantity):
    st.write(f"**Position:** {position.get('tradingsymbol', '')}")

    qty_option = st.radio(
        "Quantity to Square Off",
        ["Full", "Partial"],
        horizontal=True,
        key=f"qty_option_{position.get('tradingsymbol', '')}_position"
    )
    if qty_option == "Partial":
        squareoff_qty = st.number_input(
            "Enter quantity to square off",
            min_value=1,
            max_value=quantity,
            value=quantity,
            key=f"qty_input_{position.get('tradingsymbol', '')}_position"
        )
    else:
        squareoff_qty = quantity

    price_option = st.radio(
        "Square Off At",
        ["Market Price", "Limit Price"],
        horizontal=True,
        key=f"price_option_{position.get('tradingsymbol', '')}_position"
    )
    if price_option == "Limit Price":
        default_price = float(position.get("avg_price") or position.get("last_price") or 0)
        squareoff_price = st.number_input(
            "Limit Price",
            min_value=0.0,
            value=default_price,
            key=f"price_input_{position.get('tradingsymbol', '')}_position"
        )
        price_type = "LIMIT"
    else:
        squareoff_price = 0.0
        price_type = "MARKET"

    submit = st.form_submit_button("Confirm Square Off")
    if submit:
        side = "SELL" if position.get("buy_or_sell", "BUY") == "BUY" else "BUY"
        payload = {
            "exchange": position.get("exchange", ""),
            "tradingsymbol": position.get("tradingsymbol", ""),
            "quantity": str(squareoff_qty),
            "order_type": side,
            "price": str(squareoff_price),
            "price_type": price_type,
            "product_type": position.get("product_type", "INTRADAY"),
        }
        resp = integrate_post("/squareoff", payload)  # Change endpoint if needed
        st.success("Square Off Response:")
        st.json(resp)

def show():
    st.header("Square Off Positions & Holdings")

    # ========== Holdings Section ==========
    st.subheader("Holdings")
    data = integrate_get("/holdings")
    holdings = data.get("data", [])
    # Apply same filtering as in your holdings.py
    active_holdings = []
    for h in holdings:
        qty = 0.0
        ts = h.get("tradingsymbol")
        if isinstance(ts, list) and len(ts) > 0 and isinstance(ts[0], dict):
            qty = float(ts[0].get("dp_qty", h.get("dp_qty", 0)))
        else:
            qty = float(h.get("dp_qty", 0))
        if qty > 0:
            active_holdings.append((h, int(qty)))

    if not active_holdings:
        st.info("No holdings to square off.")
    else:
        for hold, qty in active_holdings:
            with st.expander(f"{hold.get('tradingsymbol', '')} | Qty: {qty}"):
                st.json(hold)
                with st.form(key=f"squareoff_hold_form_{hold.get('tradingsymbol', '')}"):
                    squareoff_hold_form(hold, qty)

    # ========== Positions Section ==========
    st.subheader("Positions")
    pos_data = integrate_get("/positions")
    positions = pos_data.get("positions", [])
    active_positions = []
    for p in positions:
        qty = int(float(p.get("quantity", 0)))
        if qty > 0:
            active_positions.append((p, qty))

    if not active_positions:
        st.info("No positions to square off.")
    else:
        for pos, qty in active_positions:
            with st.expander(f"{pos.get('tradingsymbol', '')} | Qty: {qty} | Side: {pos.get('buy_or_sell', '')}"):
                st.json(pos)
                with st.form(key=f"squareoff_pos_form_{pos.get('tradingsymbol', '')}"):
                    squareoff_position_form(pos, qty)
