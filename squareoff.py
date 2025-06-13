import streamlit as st
from utils import integrate_get, integrate_post

def squareoff_form(item, qty, ts_info, is_position=False):
    # item: holding or position dict, qty: int, ts_info: dict with tradingsymbol, exchange
    st.markdown("---")
    label = "Position" if is_position else "Holding"
    st.subheader(f"Square Off {label}: {ts_info['tradingsymbol']} ({qty} Qty)")

    with st.form(f"squareoff_form_{label}_{ts_info['tradingsymbol']}"):
        col1, col2, col3 = st.columns(3)
        with col1:
            exch = st.selectbox("Exchange", [ts_info['exchange']], disabled=True)
            tradingsymbol = ts_info["tradingsymbol"]
            st.write(f"**ISIN:** {ts_info.get('isin', '')}")
        with col2:
            qty_option = st.radio("Quantity to Square Off", ["Full", "Partial"], horizontal=True, key=f"qtyopt_{tradingsymbol}")
            if qty_option == "Partial":
                squareoff_qty = st.number_input(
                    "Enter quantity", min_value=1, max_value=int(qty), value=1, key=f"squareoffqty_{tradingsymbol}")
            else:
                squareoff_qty = int(qty)
        with col3:
            price_option = st.radio("Order Type", ["Market Order", "Limit Order"], horizontal=True, key=f"pricetype_{tradingsymbol}")
            if price_option == "Limit Order":
                default_price = float(item.get("avg_buy_price") or item.get("average_price") or 0)
                squareoff_price = st.number_input(
                    "Limit Price (₹)", min_value=0.01, value=round(default_price,2), key=f"price_{tradingsymbol}")
                price_type = "LIMIT"
            else:
                squareoff_price = 0.0
                price_type = "MARKET"

        validity = st.selectbox("Order Validity", ["DAY", "IOC", "EOS"], index=0, key=f"validity_{tradingsymbol}")
        remarks = st.text_input("Remarks (optional)", key=f"remarks_{tradingsymbol}")

        disclose = st.checkbox("Disclose Partial Quantity?", key=f"disclose_{tradingsymbol}")
        if disclose:
            disclosed_quantity = st.number_input(
                "Disclosed Quantity (optional)", min_value=1, max_value=int(squareoff_qty), value=1, key=f"discloseqty_{tradingsymbol}")
        else:
            disclosed_quantity = None

        st.markdown("---")
        submitted = st.form_submit_button("🟢 Place Square Off Order")
        if submitted:
            payload = {
                "exchange": exch,
                "tradingsymbol": tradingsymbol,
                "order_type": "SELL",
                "quantity": str(squareoff_qty),
                "price": str(squareoff_price),
                "price_type": price_type,
                "product_type": "CNC",
                "validity": validity,
            }
            if remarks:
                payload["remarks"] = remarks
            if disclosed_quantity:
                payload["disclosed_quantity"] = str(disclosed_quantity)
            with st.spinner("Placing order..."):
                resp = integrate_post("/placeorder", payload)
            status = resp.get('status') or resp.get('message') or resp
            if resp.get("status") == "ERROR":
                st.error(f"Order Failed: {resp.get('message','Error')}")
            else:
                st.success(f"Order Response: {status}")

def show():
    st.title("⚡ Definedge Integrate Dashboard")
    st.subheader("💼 Square Off Positions & Holdings")
    st.markdown("---")
    # --- Holdings Table ---
    st.header("📦 Holdings")
    data = integrate_get("/holdings")
    holdings = data.get("data", [])
    # Table columns
    hold_cols = ["tradingsymbol", "exchange", "isin", "dp_qty", "t1_qty", "avg_buy_price", "haircut"]
    col_labels = ["Symbol", "Exch", "ISIN", "DP Qty", "T1 Qty", "Avg Price", "Haircut"]
    st.markdown("#### Holdings List")
    columns = st.columns([1.5, 1.2, 1.5, 1.1, 1.1, 1.2, 1.1, 1.2])
    for i, label in enumerate(col_labels):
        columns[i].markdown(f"**{label}**")
    columns[-1].markdown("**Square Off**")

    user_holdings = []
    for h in holdings:
        qty = int(float(h.get("dp_qty", 0)))
        tradingsymbols = h.get("tradingsymbol", [])
        if qty > 0 and tradingsymbols and isinstance(tradingsymbols, list):
            user_holdings.append((h, qty, tradingsymbols))
    if not user_holdings:
        st.info("No holdings to square off.")
    else:
        sq_id = st.session_state.get("sq_id", None)
        for idx, (holding, qty, tradingsymbols) in enumerate(user_holdings):
            ts_info = tradingsymbols[0]
            columns = st.columns([1.5, 1.2, 1.5, 1.1, 1.1, 1.2, 1.1, 1.2])
            for i, key in enumerate(hold_cols):
                val = ts_info.get(key) if key in ts_info else holding.get(key)
                columns[i].write(val)
            if columns[-1].button("Square Off", key=f"squareoff_btn_{ts_info['tradingsymbol']}"):
                st.session_state["sq_id"] = f"HOLD_{idx}"
                st.rerun()
            # Show form below table if this row is selected
            if sq_id == f"HOLD_{idx}":
                squareoff_form(holding, qty, ts_info, is_position=False)
                st.session_state["sq_id"] = None

    # --- Positions Table ---
    st.header("📝 Positions")
    pdata = integrate_get("/positions")
    positions = pdata.get("data", [])
    # Table columns
    pos_cols = ["tradingsymbol", "exchange", "product_type", "quantity", "buy_avg_price", "sell_avg_price", "net_qty", "pnl"]
    pos_labels = ["Symbol", "Exch", "Product", "Qty", "Buy Avg", "Sell Avg", "Net Qty", "PnL"]
    st.markdown("#### Positions List")
    columns = st.columns([1.5, 1.2, 1.2, 1, 1.2, 1.2, 1, 1.3, 1.2])
    for i, label in enumerate(pos_labels):
        columns[i].markdown(f"**{label}**")
    columns[-1].markdown("**Square Off**")

    user_positions = []
    for p in positions:
        qty = int(float(p.get("quantity", 0)))
        if abs(qty) > 0:
            user_positions.append(p)
    if not user_positions:
        st.info("No open positions to square off.")
    else:
        sqp_id = st.session_state.get("sqp_id", None)
        for idx, pos in enumerate(user_positions):
            columns = st.columns([1.5, 1.2, 1.2, 1, 1.2, 1.2, 1, 1.3, 1.2])
            for i, key in enumerate(pos_cols):
                columns[i].write(pos.get(key, ""))
            if columns[-1].button("Square Off", key=f"squareoff_btn_pos_{pos['tradingsymbol']}_{idx}"):
                st.session_state["sqp_id"] = f"POS_{idx}"
                st.rerun()
            # Show form below table if this row is selected
            if sqp_id == f"POS_{idx}":
                # Fake ts_info for positions (for UI consistency)
                ts_info = {
                    "tradingsymbol": pos.get("tradingsymbol"),
                    "exchange": pos.get("exchange"),
                    "isin": pos.get("isin", ""),
                }
                qty = abs(int(float(pos.get("quantity", 0))))
                squareoff_form(pos, qty, ts_info, is_position=True)
                st.session_state["sqp_id"] = None
