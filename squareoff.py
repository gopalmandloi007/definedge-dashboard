import streamlit as st
from utils import integrate_get, integrate_post

def squareoff_form(item, item_type):
    st.write(f"**{item_type}:** {item.get('tradingsymbol', '')}")

    # Default qty field
    full_qty = int(item.get("quantity", item.get("netqty", 0)))
    if full_qty == 0:
        st.info("No quantity available to square off.")
        return

    qty_option = st.radio("Quantity to Square Off", ["Full", "Partial"], horizontal=True, key=f"qty_option_{item.get('tradingsymbol', '')}_{item_type}")
    if qty_option == "Partial":
        squareoff_qty = st.number_input("Enter quantity to square off", min_value=1, max_value=full_qty, value=full_qty, key=f"qty_input_{item.get('tradingsymbol', '')}_{item_type}")
    else:
        squareoff_qty = full_qty

    price_option = st.radio("Square Off At", ["Market Price", "Limit Price"], horizontal=True, key=f"price_option_{item.get('tradingsymbol', '')}_{item_type}")
    if price_option == "Limit Price":
        squareoff_price = st.number_input("Limit Price", min_value=0.0, value=float(item.get("last_price", 0)), key=f"price_input_{item.get('tradingsymbol', '')}_{item_type}")
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
            "order_type": "SELL" if item.get("buy_or_sell", "BUY") == "BUY" else "BUY",
            "price": str(squareoff_price),
            "price_type": price_type,
            "product_type": item.get("product_type", "INTRADAY"),
        }
        # You can add more fields from item if your API needs it
        # Choose the correct endpoint as per your API docs:
        resp = integrate_post("/squareoff", payload)  # Change '/squareoff' to your backend endpoint if needed
        st.success("Square Off Response:")
        st.json(resp)

def show():
    st.header("Square Off Positions & Holdings")

    # --- Positions Section ---
    st.subheader("Positions")
    positions_data = integrate_get("/positions")
    positions = positions_data.get("positions", [])  # Adjust key if your response is different

    if not positions:
        st.info("No open positions to square off.")
    else:
        for pos in positions:
            with st.expander(f"{pos.get('tradingsymbol', '')} | Qty: {pos.get('quantity', 0)} | Side: {pos.get('buy_or_sell', '')}"):
                st.json(pos)
                with st.form(key=f"squareoff_pos_form_{pos.get('tradingsymbol', '')}"):
                    squareoff_form(pos, "Position")

    # --- Holdings Section ---
    st.subheader("Holdings")
    holdings_data = integrate_get("/holdings")
    holdings = holdings_data.get("holdings", [])  # Adjust key if your response is different

    if not holdings:
        st.info("No holdings to square off.")
    else:
        for hold in holdings:
            qty = int(hold.get("quantity", hold.get("netqty", 0)))
            if qty == 0:
                continue
            with st.expander(f"{hold.get('tradingsymbol', '')} | Qty: {qty}"):
                st.json(hold)
                with st.form(key=f"squareoff_hold_form_{hold.get('tradingsymbol', '')}"):
                    squareoff_form(hold, "Holding")
