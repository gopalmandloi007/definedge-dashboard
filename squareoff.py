import streamlit as st
from utils import integrate_get, integrate_post

def squareoff_form(item, item_type, avail_qty):
    st.write(f"**{item_type}:** {item.get('tradingsymbol', '')}")

    if avail_qty == 0:
        st.info("No quantity available to square off.")
        return

    qty_option = st.radio(
        "Quantity to Square Off",
        ["Full", "Partial"],
        horizontal=True,
        key=f"qty_option_{item.get('tradingsymbol', '')}_{item_type}"
    )
    if qty_option == "Partial":
        squareoff_qty = st.number_input(
            "Enter quantity to square off",
            min_value=1,
            max_value=avail_qty,
            value=avail_qty,
            key=f"qty_input_{item.get('tradingsymbol', '')}_{item_type}"
        )
    else:
        squareoff_qty = avail_qty

    price_option = st.radio(
        "Square Off At",
        ["Market Price", "Limit Price"],
        horizontal=True,
        key=f"price_option_{item.get('tradingsymbol', '')}_{item_type}"
    )
    if price_option == "Limit Price":
        default_price = float(item.get("last_price") or item.get("avg_buy_price") or 0)
        squareoff_price = st.number_input(
            "Limit Price",
            min_value=0.0,
            value=default_price,
            key=f"price_input_{item.get('tradingsymbol', '')}_{item_type}"
        )
        price_type = "LIMIT"
    else:
        squareoff_price = 0.0
        price_type = "MARKET"

    submit = st.form_submit_button("Confirm Square Off")
    if submit:
        payload = {
            "exchange": item.get("exchange", ""),
            "tradingsymbol": item.get("tradingsymbol", ""),
            "quantity": str(squareoff_qty),
            "order_type": "SELL" if item_type == "Holding" or item.get("buy_or_sell", "BUY") == "BUY" else "BUY",
            "price": str(squareoff_price),
            "price_type": price_type,
            "product_type": item.get("product_type", "INTRADAY" if item_type == "Position" else "CNC"),
        }
        resp = integrate_post("/squareoff", payload)  # Change endpoint as per backend if needed.
        st.success("Square Off Response:")
        st.json(resp)

def show():
    st.header("Square Off Positions & Holdings")

    # --- Positions Section ---
    st.subheader("Positions")
    positions_data = integrate_get("/positions")
    positions = positions_data.get("positions", []) if isinstance(positions_data, dict) else []
    if not positions:
        st.info("No open positions to square off.")
    else:
        for pos in positions:
            qty = int(pos.get("quantity", 0))
            if qty == 0:
                continue
            with st.expander(f"{pos.get('tradingsymbol', '')} | Qty: {qty} | Side: {pos.get('buy_or_sell', '')}"):
                st.json(pos)
                with st.form(key=f"squareoff_pos_form_{pos.get('tradingsymbol', '')}"):
                    squareoff_form(pos, "Position", qty)

    # --- Holdings Section ---
    st.subheader("Holdings")
    holdings_data = integrate_get("/holdings")
    # Try to find the list of holdings in response
    if isinstance(holdings_data, dict) and "holdings" in holdings_data:
        holdings = holdings_data.get("holdings", [])
    elif isinstance(holdings_data, dict) and "data" in holdings_data and "holdings" in holdings_data["data"]:
        holdings = holdings_data["data"].get("holdings", [])
    elif isinstance(holdings_data, list):
        holdings = holdings_data
    else:
        holdings = []

    holding_found = False
    for hold in holdings:
        # Calculate available quantity for squareoff: dp_qty + t1_qty (add more fields if needed)
        dp_qty = int(hold.get("dp_qty", 0))
        t1_qty = int(hold.get("t1_qty", 0))
        avail_qty = dp_qty + t1_qty
        if avail_qty == 0:
            continue
        holding_found = True
        with st.expander(f"{hold.get('tradingsymbol', '')} | Qty: {avail_qty}"):
            st.json(hold)
            with st.form(key=f"squareoff_hold_form_{hold.get('tradingsymbol', '')}"):
                squareoff_form(hold, "Holding", avail_qty)

    if not holding_found:
        st.info("No holdings to square off.")
