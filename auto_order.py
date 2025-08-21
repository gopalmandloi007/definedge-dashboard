import streamlit as st
from utils import integrate_get, integrate_post

def extract_first_valid(d, keys, default=""):
    for k in keys:
        v = d.get(k)
        if v not in (None, "", [], {}, "null"):
            return v
    return default

def extract_qty(pos):
    for k in ['netqty', 'net_quantity', 'net_qty', 'quantity', 'Qty']:
        v = pos.get(k)
        if v is not None and v != "":
            try:
                return int(float(v))
            except Exception:
                continue
    return 0

def auto_orders_for_item(item, qty, ts_info, entry_price, product_type="CNC", is_position=False):
    symbol = ts_info['tradingsymbol']
    exchange = ts_info['exchange']
    unique_id = f"{symbol}_{exchange}_{product_type}"

    # Default calculations
    stop_loss_price = round(entry_price * 0.98, 2)
    target1_price = round(entry_price * 1.12, 2)
    target2_price = round(entry_price * 1.25, 2)
    half_qty = qty // 2
    rem_qty = qty - half_qty

    # Session state for confirmation
    if "auto_orders" not in st.session_state:
        st.session_state["auto_orders"] = {}

    # Only show if not already confirmed
    if st.session_state["auto_orders"].get(unique_id) != "done":
        st.markdown(f"### {symbol} ({exchange}) — {product_type}")
        st.write(f"Entry Price: ₹{entry_price:.2f}, Quantity: {qty}")
        with st.form(f"auto_order_form_{unique_id}"):
            st.subheader("Stop Loss (SL-LIMIT) — 100% Qty")
            sl_price = st.number_input("Stop Loss Price (2% below Entry)", min_value=0.01, value=stop_loss_price, key=f"sl_price_{unique_id}")
            sl_qty = st.number_input("SL Quantity", min_value=1, max_value=qty, value=qty, key=f"sl_qty_{unique_id}")
            sl_type = st.selectbox("SL Type", ["SL-LIMIT", "SL-MARKET"], index=0, key=f"sl_type_{unique_id}")

            st.subheader("Target 1 (LIMIT) — Half Qty")
            t1_price = st.number_input("Target 1 Price (12% above Entry)", min_value=entry_price, value=target1_price, key=f"t1_price_{unique_id}")
            t1_qty = st.number_input("Target 1 Qty", min_value=1, max_value=qty, value=half_qty, key=f"t1_qty_{unique_id}")

            st.subheader("Target 2 (LIMIT) — Remaining Qty")
            t2_price = st.number_input("Target 2 Price (25% above Entry)", min_value=entry_price, value=target2_price, key=f"t2_price_{unique_id}")
            t2_qty = st.number_input("Target 2 Qty", min_value=1, max_value=qty, value=rem_qty, key=f"t2_qty_{unique_id}")

            validity = st.selectbox("Order Validity", ["DAY", "IOC", "EOS"], index=0, key=f"validity_{unique_id}")

            confirm = st.form_submit_button("✓ Place Orders")
            cancel = st.form_submit_button("✗ Cancel")

            if confirm:
                # SL Order (SELL, SL-LIMIT or SL-MARKET)
                sl_payload = {
                    "exchange": exchange,
                    "tradingsymbol": symbol,
                    "order_type": "SELL",
                    "quantity": str(sl_qty),
                    "price": str(sl_price),
                    "price_type": sl_type,
                    "product_type": product_type,
                    "validity": validity,
                }
                resp_sl = integrate_post("/placeorder", sl_payload)

                # Target 1 Order (SELL, LIMIT)
                t1_payload = {
                    "exchange": exchange,
                    "tradingsymbol": symbol,
                    "order_type": "SELL",
                    "quantity": str(t1_qty),
                    "price": str(t1_price),
                    "price_type": "LIMIT",
                    "product_type": product_type,
                    "validity": validity,
                }
                resp_t1 = integrate_post("/placeorder", t1_payload)

                # Target 2 Order (SELL, LIMIT)
                t2_payload = {
                    "exchange": exchange,
                    "tradingsymbol": symbol,
                    "order_type": "SELL",
                    "quantity": str(t2_qty),
                    "price": str(t2_price),
                    "price_type": "LIMIT",
                    "product_type": product_type,
                    "validity": validity,
                }
                resp_t2 = integrate_post("/placeorder", t2_payload)

                st.success(f"SL Order Response: {resp_sl.get('message', resp_sl)}")
                st.success(f"Target 1 Order Response: {resp_t1.get('message', resp_t1)}")
                st.success(f"Target 2 Order Response: {resp_t2.get('message', resp_t2)}")

                st.session_state["auto_orders"][unique_id] = "done"
                st.rerun()

            if cancel:
                st.session_state["auto_orders"][unique_id] = "cancelled"
                st.rerun()

def show():
    st.title("🚀 Auto Order (SL & Targets) for Holdings and Positions")

    st.header("Holdings")
    hdata = integrate_get("/holdings")
    holdings = hdata.get("data", [])

    for h in holdings:
        qty = int(float(h.get("dp_qty", 0) or 0))
        tradingsymbols = h.get("tradingsymbol", [])
        if qty > 0 and tradingsymbols and isinstance(tradingsymbols, list):
            ts_info = tradingsymbols[0]
            entry_price = float(extract_first_valid(ts_info, ["avg_buy_price", "average_price", "buy_avg_price"], 0))
            if entry_price > 0:
                auto_orders_for_item(h, qty, ts_info, entry_price, product_type="CNC", is_position=False)

    st.header("Positions")
    pdata = integrate_get("/positions")
    positions = pdata.get("positions") or pdata.get("data") or []

    for pos in positions:
        net_qty = extract_qty(pos)
        if net_qty > 0:
            ts_info = {
                "tradingsymbol": extract_first_valid(pos, ["tradingsymbol", "symbol"]),
                "exchange": extract_first_valid(pos, ["exchange"]),
                "isin": extract_first_valid(pos, ["isin"], ""),
            }
            entry_price = float(extract_first_valid(pos, ["day_buy_avg", "total_buy_avg"], 0))
            product_type = extract_first_valid(pos, ["product_type", "productType", "Product"], "INTRADAY")
            if entry_price > 0:
                auto_orders_for_item(pos, net_qty, ts_info, entry_price, product_type=product_type, is_position=True)

if __name__ == "__main__":
    show()
